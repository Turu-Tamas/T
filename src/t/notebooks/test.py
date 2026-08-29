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

#%%
%load_ext autoreload
%autoreload 2
%aimport -torch -numpy -hydra

#%%
from t.deep_cfr.sampling import GameSampler
import pyspiel
import numpy as np
import pyspiel.hungarian_tarokk as T

def input_fn(state: T.HungarianTarokkState):
    if state.current_phase() == T.HungarianTarokkPhase.ANNOUNCEMENTS and T.AnnouncementActions.PASS in state.legal_actions():
        return [T.AnnouncementActions.PASS]
    return state.legal_actions()

sampler = GameSampler(input_fn, pyspiel.load_game("hungarian_tarokk"), 10, 10, 1)

#%%
def sampling_policy(legal_actions):
    result = np.zeros([T.NUM_DISTINCT_ACTIONS], dtype=np.float32)
    result[legal_actions] = 1. / len(legal_actions)
    return result
def target_policy(legal_actions):
    result = np.zeros([T.NUM_DISTINCT_ACTIONS], dtype=np.float32)
    result[legal_actions] = np.abs(np.random.randn(len(legal_actions)))
    result = result / result.sum()
    return result
#%%
import matplotlib.pyplot as plt
trajectory = sampler._sample_trajectory(sampling_policy, target_policy)
player = 0
regrets = sampler._calculate_regrets(trajectory)
plt.hist(np.abs(np.unique(regrets)))
#%%
trajectories = [
    sampler._sample_trajectory(sampling_policy, target_policy)
    for _ in range(10000)
]
regrets = [
    np.unique(sampler._calculate_regrets(traj))
    for traj in trajectories
]
regrets = np.concat(regrets)
#%%
plt.hist(np.log10(np.abs(regrets)[regrets != 0]), log=True)

#%%
outputs = torch.tensor([   -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
         0.1920, -0.1890, -0.0444,  0.0836, -0.0239, -0.0411,  0.0841, -0.0641,
        -0.1656, -0.1279,  0.0492,  0.0782,  0.0169, -0.1679,  0.1538, -0.1449,
        -0.0425, -0.0881,  0.1412, -0.1561,  0.1338, -0.0472,  0.0718, -0.2059,
        -0.1660, -0.0235, -0.0696,  0.0063, -0.0196,  0.0636,  0.1705,  0.0085,
         0.1625,  0.0694, -0.0055,  0.1157,  0.0282,  0.0790,  0.1064, -0.1410,
        -0.0719, -0.0935,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf,
           -inf,    -inf,    -inf,    -inf,    -inf,    -inf,    -inf])
mask = torch.tensor([False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
         True,  True, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False])
torch.arange(outputs.size(0))[outputs != -inf]
torch.arange(outputs.size(0))[mask]

#%%
import torch
from torch import inf
mask = torch.tensor([False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False,  True,  True, False, False,  True, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False,
        False])

torch.arange(151 )[mask]
#%%
from t.models.models import _PHASE_ACTION_SPACES
print(_PHASE_ACTION_SPACES)