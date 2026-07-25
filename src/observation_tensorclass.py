import pyspiel
from pyspiel.hungarian_tarokk import *
from tensordict import TensorClass
import torch
from typing import cast

_NUM_PLAYERS = 4
_NUM_CARDS = 42
_NUM_TAROKKS = 22
_NUM_BIDS = 4
_NUM_BONUSES = 6

class ObservationTensor(TensorClass):
    phase: torch.Tensor  # onehot, 6
    current_player: torch.Tensor  # onehot, 4 (all-zero if nobody's turn)
    hand: torch.Tensor  # multihot, 42

    declarer: torch.Tensor  # onehot, 5 (4 players + 1 for none)
    # 0 = three, 1 = two, 2 = one, 3 = solo, 4 = none
    winning_bid: torch.Tensor  # onehot, 5

    # 0 = none, 1 = XIX, 2 = XVIII, 3 = XX
    obligatory_called_card: torch.Tensor  # onehot, 4

    # for each of the 7 possible bid-slots (3, 2, hold@2, 1, hold@1, solo,
    # hold@solo), the player who last reached it, relative to the observer
    # (0 = self)
    bid_slot_to_player: torch.Tensor  # -1..3, 7 (-1 = nobody bid at that level)

    called_card: torch.Tensor  # onehot, 23 (0..21 = tarokk index, 22 = none)
    # 0 = declarer, 1 = defender, 2 = unknown
    public_sides: torch.Tensor  # onehot, 4x3

    # the tarokk count declared by each player: 0 = none, 1 = 8, 2 = 9
    declared_tarokks: torch.Tensor  # onehot, 4x3
    # the player (relative to the observer) who kontra'd by office, if any
    hivatalbol_kontra: torch.Tensor  # onehot, 5 (4 players + 1 for none)

    # wether the bonus was announced by each side (0 = declarer, 1 = defender)
    bonus_announced: torch.Tensor  # bool, 6x2
    # how many times the announcement was kontra'd
    bonus_kontra_count: torch.Tensor  # integer, 6x2
    game_kontra_level: torch.Tensor  # integer, 1

    discarded_tarokk_counts: torch.Tensor  # integer, 4
    declarer_shown_tarokks: torch.Tensor  # multihot, 42

    current_trick: torch.Tensor  # onehot per player, 4x43 (0..41 cards, 42 = none)
    trick_leader: torch.Tensor  # onehot, 4
    last_trick: torch.Tensor  # onehot per player, 4x43 (0..41 cards, 42 = none)


def observation_tensor_to_tensorclass(
    observation: torch.Tensor
) -> ObservationTensor:
    pos = 0

    def take(size: int) -> torch.Tensor:
        nonlocal pos
        chunk = observation[pos : pos + size]
        pos += size
        return chunk

    phase = take(6).bool()
    current_player = take(_NUM_PLAYERS).bool()
    hand = take(_NUM_CARDS).bool()

    declarer = take(_NUM_PLAYERS + 1).bool()
    winning_bid = take(_NUM_BIDS + 1).bool()
    obligatory_called_card = take(4).bool()

    bid_slot_to_player = take(2 * _NUM_BIDS - 1).to(torch.int64)

    called_card = take(_NUM_TAROKKS + 1).bool()
    public_sides = take(_NUM_PLAYERS * 3).bool().view(_NUM_PLAYERS, 3)
    declared_tarokks = take(_NUM_PLAYERS * 3).bool().view(_NUM_PLAYERS, 3)
    hivatalbol_kontra = take(_NUM_PLAYERS + 1).bool()

    bonus_announced = take(_NUM_BONUSES * 2).bool().view(_NUM_BONUSES, 2)
    bonus_kontra_count = take(_NUM_BONUSES * 2).to(torch.int64).view(_NUM_BONUSES, 2)
    game_kontra_level = take(1).to(torch.int64)

    discarded_tarokk_counts = take(_NUM_PLAYERS).to(torch.int64)
    declarer_shown_tarokks = take(_NUM_CARDS).bool()

    current_trick = (
        take(_NUM_PLAYERS * (_NUM_CARDS + 1))
        .bool()
        .view(_NUM_PLAYERS, _NUM_CARDS + 1)
    )
    trick_leader = take(_NUM_PLAYERS).bool()
    last_trick = (
        take(_NUM_PLAYERS * (_NUM_CARDS + 1))
        .bool()
        .view(_NUM_PLAYERS, _NUM_CARDS + 1)
    )

    assert pos == observation.numel()

    return ObservationTensor(
        phase=phase,
        current_player=current_player,
        hand=hand,
        declarer=declarer,
        winning_bid=winning_bid,
        obligatory_called_card=obligatory_called_card,
        bid_slot_to_player=bid_slot_to_player,
        called_card=called_card,
        public_sides=public_sides,
        declared_tarokks=declared_tarokks,
        hivatalbol_kontra=hivatalbol_kontra,
        bonus_announced=bonus_announced,
        bonus_kontra_count=bonus_kontra_count,
        game_kontra_level=game_kontra_level,
        discarded_tarokk_counts=discarded_tarokk_counts,
        declarer_shown_tarokks=declarer_shown_tarokks,
        current_trick=current_trick,
        trick_leader=trick_leader,
        last_trick=last_trick,
    )
