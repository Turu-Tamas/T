import torch
import torch.nn as nn


class SequenceResampler(nn.Module):
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        output_seq_len: int,
        num_heads: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()

        self.output_seq_len = output_seq_len
        self.output_dim = output_dim

        # Project input embeddings into the attention dimension.
        self.input_projection = nn.Linear(input_dim, output_dim)

        # One learned query for each output position.
        self.queries = nn.Parameter(
            torch.randn(output_seq_len, output_dim) * 0.02
        )
        self.norm1 = nn.LayerNorm(output_dim)
        self.norm2 = nn.LayerNorm(output_dim)

        # Cross-attention: queries attend to the input sequence.
        self.attention = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )

        self.ffn = nn.Sequential(
            nn.Linear(output_dim, 4 * output_dim),
            nn.GELU(),
            nn.Linear(4 * output_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, input_seq_len, input_dim]
        batch_size = x.shape[0]

        # Change embedding dimension.
        x = self.input_projection(x)

        # Expand learned queries across the batch.
        queries = self.queries.unsqueeze(0).expand(batch_size, -1, -1)

        # Each output position attends to the entire input sequence.
        attended, _ = self.attention(
            query=queries,
            key=x,
            value=x,
        )

        out = self.norm1(queries + attended)
        out = self.norm2(out + self.ffn(out))

        return out
