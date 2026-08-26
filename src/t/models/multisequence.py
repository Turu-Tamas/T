import torch
import torch.nn as nn


class MultiSequenceCrossAttention(nn.Module):
    def __init__(
        self,
        dim: int,
        num_heads: int,
        num_sequences: int,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
        bias: bool = True,
    ):
        super().__init__()

        self.dim = dim
        self.num_heads = num_heads
        self.num_sequences = num_sequences

        assert dim % num_heads == 0

        self.sequence_embedding = nn.Parameter(torch.randn((num_sequences, dim)) * 0.02)
        # Separate Q/K/V projection for every sequence.
        self.q_proj = nn.ModuleList([
            nn.Linear(dim, dim, bias=bias)
            for _ in range(num_sequences)
        ])
        self.k_proj = nn.ModuleList([
            nn.Linear(dim, dim, bias=bias)
            for _ in range(num_sequences)
        ])
        self.v_proj = nn.ModuleList([
            nn.Linear(dim, dim, bias=bias)
            for _ in range(num_sequences)
        ])
        self.out_proj = nn.ModuleList([
            nn.Linear(dim, dim, bias=bias)
            for _ in range(num_sequences)
        ])

        # Pre-normalization.
        self.norm_attn = nn.ModuleList([
            nn.LayerNorm(dim)
            for _ in range(num_sequences)
        ])
        self.norm_ff = nn.ModuleList([
            nn.LayerNorm(dim)
            for _ in range(num_sequences)
        ])

        hidden_dim = int(dim * mlp_ratio)
        self.ff = nn.ModuleList([
            nn.Sequential(
                nn.Linear(dim, hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, dim),
                nn.Dropout(dropout),
            )
            for _ in range(num_sequences)
        ])

        self.dropout = nn.Dropout(dropout)

    def forward(self, sequences):
        if len(sequences) != self.num_sequences:
            raise ValueError(
                f"Expected {self.num_sequences} sequences, "
                f"got {len(sequences)}."
            )

        x = [
            self.norm_attn[i](seq + self.sequence_embedding[i])
            for i, seq in enumerate(sequences)
        ]
        queries = [
            self.q_proj[i](x[i])
            for i in range(self.num_sequences)
        ]
        keys = [
            self.k_proj[i](x[i])
            for i in range(self.num_sequences)
        ]
        values = [
            self.v_proj[i](x[i])
            for i in range(self.num_sequences)
        ]

        outputs = []
        for i in range(self.num_sequences):
            # Don't include sequence i in its own K/V memory.
            other_keys = torch.cat(
                [
                    keys[j]
                    for j in range(self.num_sequences)
                    if j != i
                ],
                dim=1,
            )
            other_values = torch.cat(
                [
                    values[j]
                    for j in range(self.num_sequences)
                    if j != i
                ],
                dim=1,
            )

            q = queries[i]
            # (B, L_i, D) @ (B, D, L_other)
            scores = torch.matmul(
                q,
                other_keys.transpose(-2, -1),
            )
            scores = scores / (self.dim ** 0.5)
            attn = torch.softmax(scores, dim=-1)
            attn = self.dropout(attn)

            # (B, L_i, L_other) @ (B, L_other, D)
            attended = torch.matmul(attn, other_values)
            attended = self.out_proj[i](attended)

            # Residual connection
            outputs.append(
                sequences[i] + attended
            )

        outputs = [
            outputs[i] + self.ff[i](self.norm_ff[i](outputs[i]))
            for i in range(self.num_sequences)
        ]

        return tuple(outputs)
