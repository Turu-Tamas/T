import torch
import torch.nn as nn
from pyspiel import hungarian_tarokk as T
from .constants import NUM_PLAYERS, ANNOUNCEMENTS_NUM_ACTIONS


class AnnouncementsEncoder(nn.Module):
    def __init__(self, d_model, nhead, n_layers):
        super().__init__()

        self.position_embedding = nn.Embedding(NUM_PLAYERS + 1, d_model, padding_idx=0)
        self.relative_pos_embedding = nn.Embedding(NUM_PLAYERS + 1, d_model, padding_idx=0)
        self.action_embedding = nn.Embedding(ANNOUNCEMENTS_NUM_ACTIONS + 1, d_model, padding_idx=0)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=4 * d_model,
            batch_first=True,
        )

        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)

    def forward(self, actions, players, current_player):
        x = self.position_embedding(players + 1)
        positions = (players - current_player.reshape(-1, 1)) % NUM_PLAYERS
        relative_positions = torch.where(players < 0, -1, positions)
        x = x + self.relative_pos_embedding(relative_positions + 1)

        if actions.max() >= ANNOUNCEMENTS_NUM_ACTIONS or actions.min() < -1:
            print(actions)
        x = x + self.action_embedding(actions + 1)

        x = self.transformer(x,
                             src_key_padding_mask=actions < 0)
        return x
