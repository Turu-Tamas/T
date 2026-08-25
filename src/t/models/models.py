import torch
import torch.nn as nn
from .hand_encoder import HandEncoder
from .bidding_encoder import BiddingEncoder
from .announcements_encoder import AnnouncementsEncoder, ANNOUNCEMENTS_NUM_ACTIONS
from .sequence_resampler import SequenceResampler
from .tricks_encoder import TricksEncoder, SingleTrickEncoder
from .multisequence import MultiSequenceSelfAttentionLayer
import pyspiel.hungarian_tarokk as T
from tensordict import TensorClass


class BiddingModel(nn.Module):
    def __init__(self, config):
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceSelfAttentionLayer(n_sequences=2, **layer_config)            
            for _ in range(config["multiseqence"]["num_layers"])
        ])

        self.generic_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
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
        head_layers.append(nn.Linear(hidden_dim, 6))
        self.head = nn.Sequential(*head_layers)

    def forward(self, hand, bid_slots, current_players):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d_i]
        hand_embeddings = self.hand_encoder(hand)
        bidding_embeddings = self.bidding_encoder(bid_slots, current_players)

        x = self.multisequence(hand_embeddings, bidding_embeddings)
        x = self.generic_transformer(x) # [B, N, d]

        x = torch.flatten(x, 1, 2)
        x = self.head(x)

        return x


class DiscardsModel(nn.Module):
    def __init__(self, config):
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceSelfAttentionLayer(n_sequences=2, **layer_config)            
            for _ in range(config["multiseqence"]["num_layers"])
        ])

        self.generic_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
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
        head_layers.append(nn.Linear(hidden_dim, T.NUM_CARDS))
        self.head = nn.Sequential(*head_layers)

    def forward(self, hand, bid_slots, current_players):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d_i]
        hand_embeddings = self.hand_encoder(hand)    
        bidding_embeddings = self.bidding_encoder(bid_slots, current_players)

        x = self.multisequence(hand_embeddings, bidding_embeddings)
        x = self.generic_transformer(x) # [B, N, d]

        x = torch.flatten(x, 1, 2)
        x = self.head(x)        

        return x


class AnnouncementsModel(nn.Module):
    def __init__(self, config):
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])
        self.announcements_encoder = AnnouncementsEncoder(**config["announcements_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceSelfAttentionLayer(n_sequences=3, **layer_config)            
            for _ in range(config["multiseqence"]["num_layers"])
        ])

        self.generic_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
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
        head_layers.append(nn.Linear(hidden_dim, ANNOUNCEMENTS_NUM_ACTIONS))
        self.head = nn.Sequential(*head_layers)

    def forward(self, hand, bid_slots, announcements_actions, announcements_players, current_players):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d]
        hand_embeddings = self.hand_encoder(hand)    
        bidding_embeddings = self.bidding_encoder(bid_slots, current_players)
        announcements_embeddings = self.announcements_encoder(announcements_actions, announcements_players, current_players)

        x = self.multisequence(hand_embeddings, bidding_embeddings, announcements_embeddings)
        x = self.generic_transformer(x) # [B, N, d]

        x = torch.flatten(x, 1, 2)
        x = self.head(x)        

        return x


class PlayModel(nn.Module):
    def __init__(self, config):
        self.hand_encoder = HandEncoder(**config["hand_encoder"])
        self.bidding_encoder = BiddingEncoder(**config["bidding_encoder"])
        self.announcements_encoder = AnnouncementsEncoder(**config["announcements_encoder"])
        single_trick_encoder = SingleTrickEncoder(**config["single_trick_encoder"])
        self.tricks_encoder = TricksEncoder(single_trick_encoder, **config["tricks_encoder"])

        layer_config = {k: v for k, v in config["multisequence"].items() if k != "num_layers"}
        self.multisequence = nn.Sequential(*[
            MultiSequenceSelfAttentionLayer(n_sequences=4, **layer_config)            
            for _ in range(config["multiseqence"]["num_layers"])
        ])

        self.generic_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
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
        head_layers.append(nn.Linear(hidden_dim, ANNOUNCEMENTS_NUM_ACTIONS))
        self.head = nn.Sequential(*head_layers)

    def forward(self, hand, bid_slots, announcements_actions, announcements_players, current_players, trick_leaders, trick_winners, trick_cards):
        # hand: [B, N]
        # bid_slots: [B, N]
        # current_players: [B]

        # [B, N_i, d]
        hand_embeddings = self.hand_encoder(hand)    
        bidding_embeddings = self.bidding_encoder(bid_slots, current_players)
        announcements_embeddings = self.announcements_encoder(announcements_actions, announcements_players, current_players)
        tricks_embeddings = self.tricks_encoder(trick_leaders, trick_winners, trick_cards)

        x = self.multisequence(hand_embeddings, bidding_embeddings, announcements_embeddings, tricks_embeddings)
        x = self.generic_transformer(x) # [B, N, d]

        x = torch.flatten(x, 1, 2)
        x = self.head(x)        

        return x

class TarokkModel(nn.Module):
    class ObservationStruc(TensorClass):
        hand: torch.ShortTensor
        bid_slots: torch.ShortTensor
        announcements_actions: torch.ShortTensor
        announcements_players: torch.ShortTensor
        current_players: torch.ShortTensor
        trick_leaders: torch.ShortTensor
        trick_winners: torch.ShortTensor
        trick_cards: torch.ShortTensor

    @classmethod
    def get_observation_struct(cls, state: T.HungarianTarokkState):
        pass

    def __init__(self, config):
        super().__init__()
        self.bidding = BiddingModel(**config["bidding"])
        self.discard = DiscardsModel(**config["discards"])
        self.announcement = AnnouncementsModel(**config["announcement"])
        self.play = PlayModel(**config["play"])

    def forward(self, obs):
        pass