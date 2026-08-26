import torch
import torch.nn as nn
import pyspiel.hungarian_tarokk as T
from .constants import NUM_PLAYERS, CARDS_PER_TRICK, MAX_NUM_TRICKS

# trick token, winner, leader, one per card played
_ROLE_TOKENS_PER_TRICK = 3 + CARDS_PER_TRICK

class SingleTrickEncoder(nn.Module):
    def __init__(self, d_model, nhead, dim_feedforward, num_layers):
        super().__init__()

        self.embedding = nn.Embedding(T.NUM_CARDS + 1, d_model, padding_idx=0)
        self.role_embedding = nn.Parameter(
            torch.zeros(_ROLE_TOKENS_PER_TRICK, d_model)
        )
        nn.init.normal_(self.role_embedding, std=0.02)
        self.leader_embedding = nn.Embedding(NUM_PLAYERS + 1, d_model, padding_idx=0)
        self.winner_embedding = nn.Embedding(NUM_PLAYERS + 1, d_model, padding_idx=0)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            batch_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

    def forward(self, cards, leaders, winners):
        # cards: [batch, num_tricks, CARDS_PER_TRICK]
        # leaders: [B, N]
        # winners: [B, N]
        b, n, k = cards.shape
        assert k == CARDS_PER_TRICK

        # +1 for -1 padding values
        emb_leaders = self.leader_embedding(leaders + 1).unsqueeze(2) # [B, N, 1, D]
        emb_winners = self.winner_embedding(winners + 1).unsqueeze(2) # [B, N, 1, D]
        x = self.embedding(cards + 1)              # [B, N, CARDS_PER_TRICK, D]
        x = torch.cat([torch.zeros_like(emb_winners), emb_winners, emb_leaders, x], dim=2) # [B, N, ROLE_TOKENS, D]
        x = x + self.role_embedding        # [B, N, ROLE_TOKENS, D]

        x = x.reshape(b * n, _ROLE_TOKENS_PER_TRICK, -1)             # [B*N, ROLE_TOKENS, D]
        trick_padding = winners < 0
        padding_mask = trick_padding.reshape(b * n, 1).expand(-1, _ROLE_TOKENS_PER_TRICK)
        x = self.encoder(x, src_key_padding_mask=padding_mask) # [B*N, ROLE_TOKENS, D]
        x = x[:, 0, :]                       # [B*N, D]

        x = x.masked_fill(
            trick_padding.unsqueeze(-1),
            0.0,
        )

        return x.reshape(b, n, -1)              # [B, N, D]


class TricksEncoder(nn.Module):
    def __init__(
        self,
        trick_encoder: SingleTrickEncoder,
        nhead,
        dim_feedforward,
        num_layers,
    ):
        super().__init__()

        d_model = trick_encoder.embedding.embedding_dim

        self.cards_encoder = trick_encoder
        self.trick_position_embedding = nn.Parameter(torch.zeros(MAX_NUM_TRICKS, d_model))
        nn.init.normal_(self.trick_position_embedding, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            batch_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

    def forward(self, leaders, winners, cards):
        # leaders: [B, N]
        # winners: [B, N]
        # cards:   [B, N, CARDS_PER_TRICK]

        x = self.cards_encoder(cards, leaders, winners)          # [B, N, D]
        x = x + self.trick_position_embedding[:x.size(1)]

        padding_mask = winners < 0
        x = self.encoder(x, src_key_padding_mask=padding_mask)
        x = x.masked_fill(padding_mask.unsqueeze(-1), 0.0)
        assert x.size(1) <= MAX_NUM_TRICKS

        return x
