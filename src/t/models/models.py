import torch
import torch.nn as nn
from .hand_encoder import HandEncoder
from .bidding_encoder import BiddingEncoder
from .announcements_encoder import AnnouncementsEncoder, ANNOUNCEMENTS_NUM_ACTIONS
from .sequence_resampler import SequenceResampler
from .tricks_encoder import TricksEncoder, SingleTrickEncoder
from .multisequence import MultiSequenceCrossAttention
import pyspiel.hungarian_tarokk as T
from .input_struct import InputTensorClass

_PHASE_ACTION_SPACES = {
    phase: T.phase_actions(phase)
    for phase in [
        T.HungarianTarokkPhase.BIDDING,
        T.HungarianTarokkPhase.PLAYING,
        T.HungarianTarokkPhase.ANNOUNCEMENTS,
        T.HungarianTarokkPhase.TALON_EXCHANGE
    ]
}
_PHASE_ACTION_COUNTS = {
    phase: len(actions)
    for phase, actions in _PHASE_ACTION_SPACES.items()
}

_ENCODER_BUILDERS = {
    "hand": lambda config: HandEncoder(**config["hand_encoder"]),
    "bidding": lambda config: BiddingEncoder(**config["bidding_encoder"]),
    "announcements": lambda config: AnnouncementsEncoder(**config["announcements_encoder"]),
    "tricks": lambda config: TricksEncoder(
        SingleTrickEncoder(**config["single_trick_encoder"]), **config["tricks_encoder"]
    ),
}

_ENCODER_FORWARD = {
    "hand": lambda encoder, inputs: encoder(inputs.hand),
    "bidding": lambda encoder, inputs: encoder(inputs.bid_slots, inputs.current_players),
    "announcements": lambda encoder, inputs: encoder(
        inputs.announcements.actions, inputs.announcements.players, inputs.current_players
    ),
    "tricks": lambda encoder, inputs: encoder(
        inputs.tricks.leaders, inputs.tricks.winners, inputs.tricks.cards
    ),
}

_PHASE_COMPONENTS = {
    T.HungarianTarokkPhase.BIDDING: ("hand", "bidding"),
    T.HungarianTarokkPhase.TALON_EXCHANGE: ("hand", "bidding"),
    T.HungarianTarokkPhase.ANNOUNCEMENTS: ("hand", "bidding", "announcements"),
    T.HungarianTarokkPhase.PLAYING: ("hand", "bidding", "announcements", "tricks"),
}


class PhaseModel(nn.Module):
    def __init__(self, config, phase: T.HungarianTarokkPhase):
        super().__init__()
        self.components = _PHASE_COMPONENTS[phase]
        self.encoders = nn.ModuleDict({
            name: _ENCODER_BUILDERS[name](config) for name in self.components
        })

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceCrossAttention(num_sequences=len(self.components), **layer_config)
            for _ in range(config["multisequence"]["num_layers"])
        ])

        self.generic_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                batch_first=True,
                **{k: v for k, v in config["transformer"].items() if k != "num_layers"}
            ),
            num_layers=config["transformer"]["num_layers"]
        )
        self.downsampler = SequenceResampler(**config["downsampler"])

        downsampled_len = config["downsampler"]["output_dim"] * config["downsampler"]["output_seq_len"]
        hidden_dim = config["head"]["hidden_dim"]

        head_layers = [nn.Linear(downsampled_len, hidden_dim), nn.ReLU()]
        for _ in range(config["head"]["num_layers"]):
            head_layers.append(nn.Linear(hidden_dim, hidden_dim))
            head_layers.append(nn.ReLU())
        head_layers.append(nn.Linear(hidden_dim, _PHASE_ACTION_COUNTS[phase]))
        self.head = nn.Sequential(*head_layers)

    def forward(self, inputs: InputTensorClass):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d_i]
        embeddings = tuple(
            _ENCODER_FORWARD[name](self.encoders[name], inputs) for name in self.components
        )

        x = self.multisequence(embeddings)
        x = torch.cat(x, dim=1)
        x = self.generic_transformer(x) # [B, N, d]

        x = self.downsampler(x)
        x = torch.flatten(x, 1, 2)
        x = self.head(x)

        return x


class TarokkModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        module_dict = {
            T.HungarianTarokkPhase.BIDDING: PhaseModel(config["bidding"], T.HungarianTarokkPhase.BIDDING),
            T.HungarianTarokkPhase.PLAYING: PhaseModel(config["play"], T.HungarianTarokkPhase.PLAYING),
            T.HungarianTarokkPhase.ANNOUNCEMENTS: PhaseModel(config["announcement"], T.HungarianTarokkPhase.ANNOUNCEMENTS),
            T.HungarianTarokkPhase.TALON_EXCHANGE: PhaseModel(config["discards"], T.HungarianTarokkPhase.TALON_EXCHANGE)
        }
        self.phase_models = nn.ModuleDict({
            str(int(k)): v
            for k, v in module_dict.items()
        })

    def forward(self, x: InputTensorClass):
        outputs = torch.full([*x.batch_size, T.NUM_DISTINCT_ACTIONS], -torch.inf)
        def _add_output(phase: T.HungarianTarokkPhase):
            length = _PHASE_ACTION_COUNTS[phase]
            mask = torch.eq(x.phase, int(phase))
            masked_input = x[mask]
            if masked_input.size(0) == 0:
                return
            output = self.phase_models[str(int(phase))](masked_input.to_int())
            actions = _PHASE_ACTION_SPACES[phase]
            outputs[mask, actions] = output

        _add_output(T.HungarianTarokkPhase.BIDDING)
        _add_output(T.HungarianTarokkPhase.TALON_EXCHANGE)
        _add_output(T.HungarianTarokkPhase.ANNOUNCEMENTS)
        _add_output(T.HungarianTarokkPhase.PLAYING)

        outputs[~x.action_mask] = -torch.inf
        return outputs


class AnnouncementsStubModel(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x: InputTensorClass):
        result = torch.zeros([*x.batch_size, 59], device=x.device)
        result[..., T.AnnouncementActions.PASS - T.AnnouncementActions.CALL_ACTION_BASE] = 1e20 # overriden in parent forward() if illegal
        return result

class TarokkModelNoAnnouncements(nn.Module):
    def __init__(self, config):
        super().__init__()
        module_dict = {
            T.HungarianTarokkPhase.BIDDING: PhaseModel(config["bidding"], T.HungarianTarokkPhase.BIDDING),
            T.HungarianTarokkPhase.PLAYING: PhaseModel(config["play"], T.HungarianTarokkPhase.PLAYING),
            T.HungarianTarokkPhase.ANNOUNCEMENTS: AnnouncementsStubModel(),
            T.HungarianTarokkPhase.TALON_EXCHANGE: PhaseModel(config["discards"], T.HungarianTarokkPhase.TALON_EXCHANGE)
        }
        self.phase_models = nn.ModuleDict({
            str(int(k)): v
            for k, v in module_dict.items()
        })

    def forward(self, x: InputTensorClass):
        x_exp = x.unsqueeze(0) if x.ndim == 0 else x
        outputs = torch.full([*x_exp.batch_size, T.NUM_DISTINCT_ACTIONS], -torch.inf, device=x.device)
        def _add_output(phase: T.HungarianTarokkPhase):
            mask = torch.eq(x_exp.phase, int(phase))
            masked_input = x_exp[mask]
            if masked_input.size(0) == 0:
                return
            output = self.phase_models[str(int(phase))](masked_input.to_int())
            actions = _PHASE_ACTION_SPACES[phase]
            rows = mask.nonzero(as_tuple=True)[0]
            outputs[rows[:, None], actions] = output

        _add_output(T.HungarianTarokkPhase.BIDDING)
        _add_output(T.HungarianTarokkPhase.TALON_EXCHANGE)
        _add_output(T.HungarianTarokkPhase.ANNOUNCEMENTS)
        _add_output(T.HungarianTarokkPhase.PLAYING)

        outputs[~x_exp.action_mask] = -torch.inf
        if x.ndim == 0:
            return outputs.squeeze(0)
        else:
            return outputs
