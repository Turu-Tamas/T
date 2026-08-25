import torch.nn as nn
from pyspiel import hungarian_tarokk as T

_FIRST_ACTION = T.AnnouncementActions.CALL_ACTION_BASE
_LAST_ACTION = T.AnnouncementActions.LAST_ACTION
ANNOUNCEMENTS_NUM_ACTIONS = _LAST_ACTION - _FIRST_ACTION

class AnnouncementsEncoder(nn.Module):
    def __init__(self, d_model, nhead, n_layers):
        super().__init__()

        self.position_embedding = nn.Embedding(4, d_model)
        self.relative_pos_embedding = nn.Embedding(4, d_model)
        self.action_embedding = nn.Embedding(ANNOUNCEMENTS_NUM_ACTIONS, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=4 * d_model,
            batch_first=True,
        )

        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)

    def forward(self, actions, players, current_player):
        x = self.position_embedding(players)
        x = x + self.relative_pos_embedding((players - current_player) % 4)

        x = x + self.action_embedding(actions - _FIRST_ACTION)

        x = self.transformer(x,
                             src_key_padding_mask=actions < 0)
        return x
