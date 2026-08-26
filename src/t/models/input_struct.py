from tensordict import TensorClass
import torch
import pyspiel.hungarian_tarokk as T
from typing import cast
import torch.nn.functional as F
from .constants import MAX_ANNOUNCEMENTS_LENGTH, MAX_NUM_TRICKS, MAX_HAND_SIZE, CARDS_PER_TRICK

class InputAnnouncement(TensorClass["tensor_only"]):
    actions: torch.Tensor
    players: torch.Tensor

    @classmethod
    def new(cls, announcement_history: list[T.HungarianTarokkCall]):
        start = max(1, len(announcement_history) - MAX_ANNOUNCEMENTS_LENGTH)
        truncated = announcement_history[start:]
        actions = [ann.action for ann in truncated]
        players = [ann.player for ann in truncated]
        actions = torch.tensor(actions) - T.AnnouncementActions.CALL_ACTION_BASE
        unpadded = cls(
            actions=actions.to(torch.int8),
            players=torch.tensor(players, dtype=torch.int8),
            batch_size=[]
        )
        # exclude the partner calling action (idx 0)
        padding = (0, MAX_ANNOUNCEMENTS_LENGTH - len(truncated))
        padded = unpadded.apply(lambda tensor: F.pad(tensor, padding, value=-1))
        padded.batch_size = [MAX_ANNOUNCEMENTS_LENGTH]
        return padded

class InputTrick(TensorClass["tensor_only"]):
    leaders: torch.Tensor
    winners: torch.Tensor
    cards: torch.Tensor

    @classmethod
    def new(cls, trick_history: list[T.HungarianTarokkTrick], current_trick_cards: list[int]):
        current_trick = T.HungarianTarokkTrick()
        current_trick.cards = current_trick_cards + [-1] * (CARDS_PER_TRICK - len(current_trick_cards))
        current_trick.leader = trick_history[-1].winner if len(trick_history) > 0 else 0
        current_trick.winner = -1
        all_tricks = trick_history + [current_trick]
        leaders = torch.tensor([trick.leader for trick in all_tricks], dtype=torch.int8)
        winners = torch.tensor([trick.winner for trick in all_tricks], dtype=torch.int8)
        cards = torch.tensor([trick.cards for trick in all_tricks], dtype=torch.int8)
        padding = (0, MAX_NUM_TRICKS - len(all_tricks))
        return cls(
            leaders=F.pad(leaders, padding, value=-1),
            winners=F.pad(winners, padding, value=-1),
            cards=F.pad(cards, (0, 0, *padding), value=-1),

            batch_size=[MAX_NUM_TRICKS]
        )


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

def get_input(state: T.HungarianTarokkState) -> InputTensorClass:
    obs = cast(T.HungarianTarokkObservationStruct, state.to_observation_struct())
    obs.trick_history
    action_mask = torch.full([T.NUM_DISTINCT_ACTIONS], False)
    action_mask[state.legal_actions()] = True
    padded_hand = obs.hand + [-1] * (MAX_HAND_SIZE - len(obs.hand))
    return InputTensorClass(
        hand=torch.tensor(padded_hand, dtype=torch.int8),
        bid_slots=torch.tensor(obs.bid_slots, dtype=torch.int8),
        current_players=torch.tensor(obs.current_player, dtype=torch.int8),
        phase=torch.tensor(int(state.current_phase()), dtype=torch.int8),
        action_mask=action_mask,
        announcements=InputAnnouncement.new(obs.announcement_history), 
        tricks=InputTrick.new(obs.trick_history, obs.current_trick),

        batch_size=[]
    )
