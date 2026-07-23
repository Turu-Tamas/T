import pyspiel
from pyspiel.hungarian_tarokk import HungarianTarokkState, HungarianTarokkObservationStruct
from tensordict import TensorClass
import torch
from typing import cast

class ObservationTensor(TensorClass):
    phase: torch.Tensor # onehot, 6
    current_player: torch.Tensor # onehot, 4
    hand: torch.Tensor # multihot, 42

    declarer: torch.Tensor # onehot, 5 (4 players + 1 for none)
    # 0 = three, 1 = two, 2 = one, 3 = solo, 4 = none
    winning_bid: torch.Tensor # onehot, 5

    # 0 = none, 1 = XIX, 2 = XVIII, 3 = XX
    obligatory_called_card: torch.Tensor # onehot, 4

    # maps each possible bid (initial bids and holds) to a player
    # 7 = 3, 2 hold@2, 1, hold@1, solo, hold@solo
    bid_slot_to_player: torch.Tensor # 0..4, 7 (4 is if no player has that bid)

    called_card: torch.Tensor # onehot, 43 (42 = none)
    public_sides: torch.Tensor # onehot, 4x3 (0 = declarer, 1 = defender1, 2 = unknown)

    # the tarokk count declared by each player, 0 = none, 1 = 8, 2 = 9
    declared_tarokks: torch.Tensor # onehot, 4x3
    # 0 or 1, wether the bonus was announced by each side (0 = declarer, 1 = defender)
    bonus_announced: torch.Tensor # onehot, 6x2
    # how many times the announcement was kontra'd
    bonus_kontra_count: torch.Tensor # 6x2
    game_contra_level: torch.Tensor # integer, 1

    discarded_tarokk_counts: torch.Tensor # integer, 4
    declarer_discarded_tarokks: torch.Tensor # multihot, 42
    
    

class HungarianTarokkStateWrapper(HungarianTarokkState):
    def observation_tensorclass(self):
        observation = cast(HungarianTarokkObservationStruct, self.to_observation_struct())
        return ObservationTensor(
                
        )
