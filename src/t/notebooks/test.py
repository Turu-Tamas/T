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