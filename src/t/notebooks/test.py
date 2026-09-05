#%%
from t.models.models import TarokkModelNoAnnouncements
from t.models.input_struct import get_input
import pyspiel.hungarian_tarokk as T
import pyspiel
import numpy as np
from typing import cast
import torch

game = pyspiel.load_game("hungarian_tarokk")
state = cast(T.HungarianTarokkState, game.new_initial_state())

states: list[T.HungarianTarokkState] = []
while not state.is_terminal():
    legals = state.legal_actions()
    if state.current_phase() == T.HungarianTarokkPhase.ANNOUNCEMENTS and T.AnnouncementActions.PASS in legals:
        states.append(state.child(T.AnnouncementActions.PASS))
        state.apply_action(T.AnnouncementActions.PASS)
    else:
        action = np.random.choice(legals)
        states.append(state.child(action))
        state.apply_action(action)

inputs = torch.stack([get_input(state) for state in states if state.current_player() >= 0])

# %%
from hydra import initialize, compose

with initialize(version_base=None, config_path="src/t/deep_cfr/conf"):
    cfg = compose(
        config_name="config",
    )
model = TarokkModelNoAnnouncements(cfg["model"])
# %%
import matplotlib.pyplot as plt
model.reset()
outputs = model(inputs).detach().numpy()
phases = [state.current_phase() for state in states if state.current_player() >= 0]
extremes = [(arr.max(), arr[arr > -np.inf].min()) for arr in outputs]
list(zip(extremes, phases))