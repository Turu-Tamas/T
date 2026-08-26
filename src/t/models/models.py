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

_phase_action_counts = {
    T.HungarianTarokkPhase.BIDDING: 6,
    T.HungarianTarokkPhase.PLAYING: T.NUM_CARDS,
    T.HungarianTarokkPhase.ANNOUNCEMENTS: ANNOUNCEMENTS_NUM_ACTIONS,
    T.HungarianTarokkPhase.TALON_EXCHANGE: T.NUM_CARDS
}
_phase_action_starts = {
    T.HungarianTarokkPhase.BIDDING: 42,
    T.HungarianTarokkPhase.PLAYING: 0,
    T.HungarianTarokkPhase.ANNOUNCEMENTS: 92,
    T.HungarianTarokkPhase.TALON_EXCHANGE: 48
}

class BiddingModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceCrossAttention(num_sequences=2, **layer_config)            
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
        head_layers.append(nn.Linear(hidden_dim, _phase_action_counts[T.HungarianTarokkPhase.BIDDING]))
        self.head = nn.Sequential(*head_layers)

    def forward(self, inputs: InputTensorClass):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d_i]
        hand_embeddings = self.hand_encoder(inputs.hand)
        bidding_embeddings = self.bidding_encoder(inputs.bid_slots, inputs.current_players)

        x = self.multisequence((hand_embeddings, bidding_embeddings))
        x = torch.cat(x, dim=1)
        x = self.generic_transformer(x) # [B, N, d]

        x = self.downsampler(x)
        x = torch.flatten(x, 1, 2)
        x = self.head(x)

        return x


class DiscardsModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceCrossAttention(num_sequences=2, **layer_config)            
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
        head_layers.append(nn.Linear(hidden_dim, _phase_action_counts[T.HungarianTarokkPhase.TALON_EXCHANGE]))
        self.head = nn.Sequential(*head_layers)

    def forward(self, inputs: InputTensorClass):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d_i]
        hand_embeddings = self.hand_encoder(inputs.hand)    
        bidding_embeddings = self.bidding_encoder(inputs.bid_slots, inputs.current_players)

        x = self.multisequence((hand_embeddings, bidding_embeddings))
        x = torch.cat(x, dim=1)
        x = self.generic_transformer(x) # [B, N, d]

        x = self.downsampler(x)
        x = torch.flatten(x, 1, 2)
        x = self.head(x)        

        return x


class AnnouncementsModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])
        self.announcements_encoder = AnnouncementsEncoder(**config["announcements_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceCrossAttention(num_sequences=3, **layer_config)            
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
        head_layers.append(nn.Linear(hidden_dim, _phase_action_counts[T.HungarianTarokkPhase.ANNOUNCEMENTS]))
        self.head = nn.Sequential(*head_layers)

    def forward(self, inputs: InputTensorClass):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d]
        hand_embeddings = self.hand_encoder(inputs.hand)    
        bidding_embeddings = self.bidding_encoder(inputs.bid_slots, inputs.current_players)
        announcements_embeddings = self.announcements_encoder(inputs.announcements.actions, inputs.announcements.players, inputs.current_players)

        x = self.multisequence((hand_embeddings, bidding_embeddings, announcements_embeddings))
        x = torch.cat(x, dim=1)
        x = self.generic_transformer(x) # [B, N, d]

        x = self.downsampler(x)
        x = torch.flatten(x, 1, 2)
        x = self.head(x)        

        return x


class PlayModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])
        self.announcements_encoder = AnnouncementsEncoder(**config["announcements_encoder"])
        single_trick_encoder = SingleTrickEncoder(**config["single_trick_encoder"])
        self.tricks_encoder = TricksEncoder(single_trick_encoder, **config["tricks_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceCrossAttention(num_sequences=4, **layer_config)            
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
        head_layers.append(nn.Linear(hidden_dim, _phase_action_counts[T.HungarianTarokkPhase.PLAYING]))
        self.head = nn.Sequential(*head_layers)

    def forward(self, inputs: InputTensorClass):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d]
        hand_embeddings = self.hand_encoder(inputs.hand)
        bidding_embeddings = self.bidding_encoder(inputs.bid_slots, inputs.current_players)
        announcements_embeddings = self.announcements_encoder(inputs.announcements.actions, inputs.announcements.players, inputs.current_players)
        tricks_embeddings = self.tricks_encoder(inputs.tricks.leaders, inputs.tricks.winners, inputs.tricks.cards)

        x = self.multisequence((hand_embeddings, bidding_embeddings, announcements_embeddings, tricks_embeddings))
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
            T.HungarianTarokkPhase.BIDDING: BiddingModel(config["bidding"]),
            T.HungarianTarokkPhase.PLAYING: PlayModel(config["play"]),
            T.HungarianTarokkPhase.ANNOUNCEMENTS: AnnouncementsModel(config["announcement"]),
            T.HungarianTarokkPhase.TALON_EXCHANGE: DiscardsModel(config["discards"])
        }
        self.phase_models = nn.ModuleDict({
            str(int(k)): v
            for k, v in module_dict.items()
        })

    def forward(self, x: InputTensorClass):
        outputs = torch.full([*x.batch_size, T.NUM_DISTINCT_ACTIONS], -torch.inf)
        def _add_output(phase: T.HungarianTarokkPhase):
            length = _phase_action_counts[phase]
            start = _phase_action_starts[phase]
            mask = torch.eq(x.phase, int(phase))
            masked_input = x[mask]
            if masked_input.size(0) == 0:
                return
            output = self.phase_models[str(int(phase))](masked_input.to_int())
            outputs[mask, start:start + length] = output

        _add_output(T.HungarianTarokkPhase.BIDDING)
        _add_output(T.HungarianTarokkPhase.TALON_EXCHANGE)
        _add_output(T.HungarianTarokkPhase.ANNOUNCEMENTS)
        _add_output(T.HungarianTarokkPhase.PLAYING)

        outputs[~x.action_mask] = -torch.inf
        return outputs
