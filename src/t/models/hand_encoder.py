import torch
import torch.nn as nn
from pyspiel.hungarian_tarokk import NUM_CARDS

class HandEncoder(nn.Module):
    def __init__(self, d_model, nhead, dim_feedforward, num_layers):
        super().__init__()

        self.embedding = nn.Embedding(
            num_embeddings=NUM_CARDS + 1, # +1 for padding
            embedding_dim=d_model,
            padding_idx=0,
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
        x = self.embedding(tokens + 1)

        # Treat padding tokens as attention-masked
        padding_mask = tokens.eq(-1)

        # [batch, seq_len, d_model]
        x = self.encoder(
            x,
            src_key_padding_mask=padding_mask,
        )

        return x
