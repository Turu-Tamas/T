from tensordict import TensorClass
import numpy as np
import torch
import pyspiel.hungarian_tarokk as T
from .constants import MAX_ANNOUNCEMENTS_LENGTH, MAX_NUM_TRICKS, MAX_HAND_SIZE, NUM_BID_SLOTS, CARDS_PER_TRICK

class InputAnnouncement(TensorClass["tensor_only"]):
    actions: torch.Tensor
    players: torch.Tensor

    @classmethod
    def empty(cls, batch_size: list[int] = []) -> "InputAnnouncement":
        shape = [*batch_size, MAX_ANNOUNCEMENTS_LENGTH]
        return cls(
            actions=torch.empty(shape, dtype=torch.int8),
            players=torch.empty(shape, dtype=torch.int8),
            batch_size=shape,
        )

    def write_(self, announcement_history: T.HungarianTarokkCallArrays, index=...) -> None:
        self.actions[index] = torch.from_numpy(announcement_history.actions)
        self.players[index] = torch.from_numpy(announcement_history.players)

    @classmethod
    def new(cls, announcement_history: T.HungarianTarokkCallArrays) -> "InputAnnouncement":
        result = cls.empty()
        result.write_(announcement_history)
        return result

class InputTrick(TensorClass["tensor_only"]):
    leaders: torch.Tensor
    winners: torch.Tensor
    cards: torch.Tensor

    @classmethod
    def empty(cls, batch_size: list[int] = []) -> "InputTrick":
        return cls(
            leaders=torch.empty([*batch_size, MAX_NUM_TRICKS], dtype=torch.int8),
            winners=torch.empty([*batch_size, MAX_NUM_TRICKS], dtype=torch.int8),
            cards=torch.empty([*batch_size, MAX_NUM_TRICKS, CARDS_PER_TRICK], dtype=torch.int8),
            batch_size=[*batch_size, MAX_NUM_TRICKS],
        )

    def write_(self, trick_history: T.HungarianTarokkTrickArrays, current_trick: np.typing.NDArray[np.int32], index=...) -> None:
        self.leaders[index] = torch.from_numpy(trick_history.leaders)
        self.winners[index] = torch.from_numpy(trick_history.winners)
        self.cards[index] = torch.from_numpy(trick_history.cards)

    @classmethod
    def new(cls, trick_history: T.HungarianTarokkTrickArrays, current_trick: np.typing.NDArray[np.int32]) -> "InputTrick":
        result = cls.empty()
        result.write_(trick_history, current_trick)
        return result


class InputTensorClass(TensorClass["tensor_only"]):
    hand: torch.Tensor
    bid_slots: torch.Tensor
    current_players: torch.Tensor
    phase: torch.Tensor
    action_mask: torch.BoolTensor

    announcements: InputAnnouncement
    tricks: InputTrick

    def to_int(self) -> "InputTensorClass":
        return self.apply(
            lambda tensor: tensor.to(torch.int) if tensor.dtype == torch.int8 else tensor
        )

    @classmethod
    def empty(cls, batch_size: list[int] = []) -> "InputTensorClass":
        """Allocate an uninitialized buffer, e.g. `InputTensorClass.empty([n_envs])`,
        to be filled in place per-row via `write_` instead of building and stacking
        one instance per state."""
        return cls(
            hand=torch.empty([*batch_size, MAX_HAND_SIZE], dtype=torch.int8),
            bid_slots=torch.empty([*batch_size, NUM_BID_SLOTS], dtype=torch.int8),
            current_players=torch.empty(batch_size, dtype=torch.int8),
            phase=torch.empty(batch_size, dtype=torch.int8),
            action_mask=torch.empty([*batch_size, T.NUM_DISTINCT_ACTIONS], dtype=torch.bool),
            announcements=InputAnnouncement.empty(batch_size),
            tricks=InputTrick.empty(batch_size),
            batch_size=batch_size,
        )

    def write_(self, state: T.HungarianTarokkState, index=...) -> None:
        """Fill row `index` of a buffer (or the whole instance, for a non-batched
        one) from `state`, without allocating a new InputTensorClass."""
        obs = state.to_observation_arrays(
            announcement_history_length=MAX_ANNOUNCEMENTS_LENGTH,
            player=state.current_player(),
            trick_history_length=9
        )

        self.hand[index] = torch.from_numpy(obs.hand)
        self.bid_slots[index] = torch.from_numpy(obs.bid_slots)
        self.current_players[index] = obs.current_player
        self.phase[index] = int(state.current_phase())

        self.action_mask[index] = torch.from_numpy(obs.legal_actions_mask)

        self.announcements.write_(obs.announcement_history, index=index)
        self.tricks.write_(obs.trick_history, obs.current_trick, index=index)

def get_input(state: T.HungarianTarokkState) -> InputTensorClass:
    result = InputTensorClass.empty()
    result.write_(state)
    return result
