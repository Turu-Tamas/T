#%%
from hydra import initialize, compose

with initialize(version_base=None, config_path="conf"):
    cfg = compose(
        config_name="config",
    )

#%%
%load_ext autoreload
%autoreload 2
%aimport -torch -numpy -hydra

#%%
from t.models.models import TarokkModel

model = TarokkModel(cfg["model"])

#%%
import pyspiel.hungarian_tarokk as T
import pyspiel
from typing import cast
import numpy as np
#%%
from t.models.models import *
from t.models.input_struct import get_input

game = pyspiel.load_game("hungarian_tarokk")
state = cast(T.HungarianTarokkState, game.new_initial_state())

while not state.is_terminal():
    if not state.is_chance_node():
        x = get_input(state)
        model(x.unsqueeze(0))
    legals = state.legal_actions()
    state.apply_action(np.random.choice(legals))

# %%
