import torch
import torch.nn as nn
from pyspiel.hungarian_tarokk import NUM_CARDS

CARD_PAD_TOKEN = -1
MAX_HAND_SIZE = 12

class HandEncoder(nn.Module):
    def __init__(self, d_model, nhead, dim_feedforward, num_layers):
        super().__init__()

        self.embedding = nn.Embedding(
            num_embeddings=NUM_CARDS,
            embedding_dim=d_model,
            padding_idx=CARD_PAD_TOKEN,
        )

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

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        # [batch, seq_len, d_model]
        x = self.embedding(tokens)

        # Treat padding tokens as attention-masked
        padding_mask = tokens.eq(CARD_PAD_TOKEN)

        # [batch, seq_len, d_model]
        x = self.encoder(
            x,
            src_key_padding_mask=padding_mask,
        )

        return x
