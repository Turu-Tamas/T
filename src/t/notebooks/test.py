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
%%timeit -n 1000
sampler._calculate_regrets(sampler._sample_trajectory(sampling_policy, target_policy))