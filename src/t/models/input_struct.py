from tensordict import TensorClass
import torch
import pyspiel.hungarian_tarokk as T
from typing import cast


class InputAnnouncement(TensorClass["tensor_only"]):
    actions: torch.ByteTensor
    players: torch.ByteTensor

    @classmethod
    def new(cls, announcement_history: list[T.HungarianTarokkCall]):
        actions = map(lambda ann: ann.action, announcement_history)
        players = map(lambda ann: ann.player, announcement_history)
        return cls(
            actions=torch.tensor(actions, dtype=torch.uint8),
            players=torch.tensor(players, dtype=torch.uint8),

            batch_size=[len(announcement_history)]
        )

class InputTrick(TensorClass["tensor_only"]):
    leaders: torch.ByteTensor
    winners: torch.ByteTensor
    cards: torch.ByteTensor

    @classmethod
    def new(cls, trick_history: list[T.HungarianTarokkTrick]):
        leaders = map(lambda trick: trick.leader, trick_history)
        winners = map(lambda trick: trick.winner, trick_history)
        cards = map(lambda trick: trick.cards, trick_history)
        return cls(
            leaders=torch.tensor(leaders, dtype=torch.uint8),
            winners=torch.tensor(winners, dtype=torch.uint8),
            cards=torch.tensor(cards, dtype=torch.uint8),

            batch_size=[len(trick_history)]
        )

class InputTensorClass(TensorClass["tensor_only"]):
    hand: torch.ByteTensor
    bid_slots: torch.ByteTensor
    current_players: torch.ByteTensor
    phase: torch.ByteTensor

    announcements: InputAnnouncement
    tricks: InputTrick

def get_input(state: T.HungarianTarokkState) -> InputTensorClass:
    obs = cast(T.HungarianTarokkObservationStruct, state.to_observation_struct())
    obs.trick_history
    return InputTensorClass(
        hand=torch.tensor(obs.hand, dtype=torch.uint8),
        bid_slots=torch.tensor(obs.bid_slots, dtype=torch.uint8),
        current_players=torch.tensor(obs.current_player, dtype=torch.uint8),
        phase=torch.tensor(state.current_phase, dtype=torch.uint8),
        announcements=InputAnnouncement.new(obs.announcement_history),
        tricks=InputTrick.new(obs.trick_history)
    )
