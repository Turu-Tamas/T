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

def input_fn(state: pyspiel.State):
    return state.legal_actions()
def policy(inputs):
    result = np.zeros([T.NUM_DISTINCT_ACTIONS], dtype=np.float32)
    result[inputs] = 1. / len(inputs)
    return result

sampler = GameSampler(input_fn, pyspiel.load_game("hungarian_tarokk"), 10, 10, 1)

#%%
inputs, actions, probs, returns = sampler.sample_trajectory(policy)
#%%
actions_taken = players.size
# [N, 4]
other_players_mask = players[:, None] == np.arange(NUM_PLAYERS)[None, :]
logged_probs = np.log(probs)
counterfactual_probs_up_to = \
    np.cumsum(probs[other_players_mask], axis=0)


#%%
import pyspiel.hungarian_tarokk as T

T.AnnouncementActions.__dict__


