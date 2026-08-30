from tensordict import TensorClass
import torch
import pyspiel.hungarian_tarokk as T
from typing import cast
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

    def write_(self, announcement_history: list[T.HungarianTarokkCall], index=...) -> None:
        # exclude the partner calling action (idx 0)
        start = max(1, len(announcement_history) - MAX_ANNOUNCEMENTS_LENGTH)
        truncated = announcement_history[start:]
        n = len(truncated)

        actions = self.actions[index]
        players = self.players[index]
        if n > 0:
            actions[:n] = torch.tensor([ann.action - T.AnnouncementActions.CALL_ACTION_BASE for ann in truncated], dtype=torch.int8)
            assert actions.max() < T.AnnouncementActions.NUM_ACTIONS
            players[:n] = torch.tensor([ann.player for ann in truncated], dtype=torch.int8)
        actions[n:] = -1
        players[n:] = -1

    @classmethod
    def new(cls, announcement_history: list[T.HungarianTarokkCall]) -> "InputAnnouncement":
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

    def write_(self, trick_history: list[T.HungarianTarokkTrick], current_trick_cards: list[int], index=...) -> None:
        current_trick = T.HungarianTarokkTrick()
        current_trick.cards = current_trick_cards + [-1] * (CARDS_PER_TRICK - len(current_trick_cards))
        current_trick.leader = trick_history[-1].winner if len(trick_history) > 0 else 0
        current_trick.winner = -1
        all_tricks = trick_history + [current_trick]
        n = len(all_tricks)

        leaders = self.leaders[index]
        winners = self.winners[index]
        cards = self.cards[index]

        leaders[:n] = torch.tensor([trick.leader for trick in all_tricks], dtype=torch.int8)
        winners[:n] = torch.tensor([trick.winner for trick in all_tricks], dtype=torch.int8)
        cards[:n] = torch.tensor([trick.cards for trick in all_tricks], dtype=torch.int8)
        leaders[n:] = -1
        winners[n:] = -1
        cards[n:] = -1

    @classmethod
    def new(cls, trick_history: list[T.HungarianTarokkTrick], current_trick_cards: list[int]) -> "InputTrick":
        result = cls.empty()
        result.write_(trick_history, current_trick_cards)
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
        obs = cast(T.HungarianTarokkObservationStruct, state.to_observation_struct())

        hand = self.hand[index]
        n = len(obs.hand)
        hand[:n] = torch.tensor(obs.hand, dtype=torch.int8)
        hand[n:] = -1

        self.bid_slots[index] = torch.tensor(obs.bid_slots, dtype=torch.int8)
        self.current_players[index] = obs.current_player
        self.phase[index] = int(state.current_phase())

        mask = self.action_mask[index]
        mask[:] = False
        mask[state.legal_actions()] = True

        self.announcements.write_(obs.announcement_history, index=index)
        self.tricks.write_(obs.trick_history, obs.current_trick, index=index)

def get_input(state: T.HungarianTarokkState) -> InputTensorClass:
    result = InputTensorClass.empty()
    result.write_(state)
    return result
