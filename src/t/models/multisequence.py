import math
import torch
import torch.nn as nn


class MultiSequenceSelfAttentionHead(nn.Module):
    def __init__(self, n_sequences, d_model, d_head, d_query):
        super().__init__()

        self.d_model = d_model
        self.d_head = d_head
        self.d_query = d_query

        self.query = nn.ModuleList([
            nn.Linear(d_model, d_query)
            for _ in range(n_sequences)
        ])

        self.key = nn.ModuleList([
            nn.Linear(d_model, d_query)
            for _ in range(n_sequences)
        ])

        self.value = nn.ModuleList([
            nn.Linear(d_model, d_head)
            for _ in range(n_sequences)
        ])

    def forward(self, *sequences):
        # Each sequence: [B, N_i, D]

        queries = torch.cat([
            query(seq)
            for query, seq in zip(self.query, sequences)
        ], dim=1)  # [B, N, d_query]

        keys = torch.cat([
            key(seq)
            for key, seq in zip(self.key, sequences)
        ], dim=1)  # [B, N, d_query]

        values = torch.cat([
            value(seq)
            for value, seq in zip(self.value, sequences)
        ], dim=1)  # [B, N, d_head]

        attention_scores = queries @ keys.transpose(-2, -1)
        attention_scores = attention_scores / math.sqrt(self.d_query)

        attention_weights = torch.softmax(
            attention_scores,
            dim=-1,
        )

        x = attention_weights @ values
        # [B, N, d_head]

        return x


class MultiSequenceSelfAttentionLayer(nn.Module):
    def __init__(
        self,
        n_heads,
        n_sequences,
        d_model,
        d_query=None,
        d_ff=None,
        dropout=0.0,
    ):
        super().__init__()

        assert d_model % n_heads == 0, \
            "d_model must be divisible by n_heads"

        self.n_heads = n_heads
        self.d_model = d_model
        self.d_head = d_model // n_heads

        if d_query is None:
            d_query = self.d_head

        if d_ff is None:
            d_ff = 4 * d_model

        self.d_query = d_query

        self.heads = nn.ModuleList([
            MultiSequenceSelfAttentionHead(
                n_sequences=n_sequences,
                d_model=d_model,
                d_head=self.d_head,
                d_query=d_query,
            )
            for _ in range(n_heads)
        ])

        # Multi-head attention output projection
        self.output_projection = nn.Linear(
            d_model,
            d_model,
        )

        # Feedforward block
        self.feedforward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

        # Pre-normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, *sequences):
        # Each sequence: [B, N_i, D]
        x = torch.cat(sequences, dim=1)
        # [B, N, D]

        normed_sequences = tuple(
            self.norm1(seq)
            for seq in sequences
        )

        head_outputs = [
            head(*normed_sequences)
            for head in self.heads
        ]

        # Each head: [B, N, d_head]
        attention_output = torch.cat(
            head_outputs,
            dim=-1,
        )
        # [B, N, d_model]

        attention_output = self.output_projection(
            attention_output
        )

        x = x + attention_output
        # Residual 1
        # [B, N, d_model]

        x = x + self.feedforward(
            self.norm2(x)
        )
        # Residual 2
        # [B, N, d_model]

        return x
