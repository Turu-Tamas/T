#%%
import pyspiel
from typing import cast
from pyspiel.hungarian_tarokk import *
import random
import torch
from t.env_utils.observation_tensorclass import build_observation_tensorclass

game = pyspiel.load_game("hungarian_tarokk")
state = cast(HungarianTarokkState, game.new_initial_state())

while state.current_phase() == HungarianTarokkPhase.DEALING:
    legals = state.legal_actions()
    action = random.choice(legals)
    state.apply_action(action)

obs = torch.tensor(state.observation_tensor())
legals = torch.tensor(state.legal_actions())
obs_tc = build_observation_tensorclass(obs, legals)

#%%
hand = [Card(idx) for idx in obs_tc.hand.argwhere()]
print([str(card) for card in hand])

#%%
import torch.nn as nn
import torch
encoder_layer = nn.TransformerEncoderLayer(
    d_model=8,
    nhead=4,
    dim_feedforward=4,
    batch_first=True,
)

encoder = nn.TransformerEncoder(
    encoder_layer,
    num_layers=2,
)

encoder(torch.randn([0, 2, 8]), src_key_padding_mask=torch.randn([0,2]) > 0)