import torch
import torch.nn as nn
from .constants import NUM_PLAYERS, NUM_BID_SLOTS

class BiddingEncoder(nn.Module):
    def __init__(self, d_model=32, nhead=4, n_layers=2):
        super().__init__()

        # no padding index because unbid slots carry information
        self.player_embedding = nn.Embedding(NUM_PLAYERS + 1, d_model)
        self.relative_pos_embedding = nn.Embedding(NUM_PLAYERS + 1, d_model)
        self.slot_embedding = nn.Embedding(NUM_BID_SLOTS, d_model)

        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=4 * d_model,
            batch_first=True,
        )

        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)

    def forward(self, bid_slot_to_player, current_player):
        # [B, 7]
        bidders = bid_slot_to_player + 1

        # [B, 7, D]
        x = self.player_embedding(bidders)

        x = x + self.slot_embedding.weight.unsqueeze(0)
        relative_positions = torch.where(bid_slot_to_player >= 0, (bid_slot_to_player - current_player) % NUM_PLAYERS, NUM_PLAYERS)
        x = x + self.relative_pos_embedding(relative_positions)

        # [B, 7, D]
        x = self.transformer(x)

        return x
