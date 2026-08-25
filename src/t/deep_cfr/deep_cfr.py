import lightning.pytorch as L
import torch
import torch.nn as nn
import numpy as np
import pyspiel.hungarian_tarokk as T
import pyspiel
import collections
from .memory import *

def _chance_node_sample_action(state: T.HungarianTarokkState):
    outcome, prob = zip(*state.chance_outcomes())
    action = np.random.choice(outcome, p=prob)
    return action


class GameDataCollector:
    def __init__(self):
        pass

    def _sample_action_from_advantage(self, state: T.HungarianTarokkState, player: pyspiel.PlayerId):
        info_state = state.information_state_tensor(player)
        legal_actions = state.legal_actions(player)
        with torch.no_grad():
            state_tensor = torch.FloatTensor(
                np.expand_dims(info_state, axis=0), device=self._device
            )
            raw_advantages = (
                self._advantage_networks[player](state_tensor)[0].cpu().numpy()
            )
        advantages = [max(0., advantage) for advantage in raw_advantages]
        cumulative_regret = np.sum([advantages[action] for action in legal_actions])
        matched_regrets = np.array([0.] * self._num_actions)
        if cumulative_regret > 0.:
            for action in legal_actions:
                matched_regrets[action] = advantages[action] / cumulative_regret
        else:
            matched_regrets[max(legal_actions, key=lambda a: raw_advantages[a])] = 1
        return advantages, matched_regrets

    def _get_buffer_init(
        self, capacity: int, data: AdvantageMemory | StrategyMemory
    ) -> ReservoirBuffer:
        return ReservoirBuffer.init(capacity, data)

    def _append_to_advantage_buffer(self, player: int, data: AdvantageMemory):
        if self._advantage_memories[player] is None:
            self._advantage_memories[player] = self._get_buffer_init(
                self._memory_capacity, data
            )
        self._advantage_memories[player].append(data)

    def _append_to_stategy_buffer(self, player: int, data: AdvantageMemory):
        if self._strategy_memories is None:
            self._strategy_memories = self._get_buffer_init(
                self._memory_capacity, data
            )
        self._strategy_memories.append(data)

    def _traverse_player_node(self, state: T.HungarianTarokkState, player: pyspiel.PlayerId):
        expected_payoff = collections.defaultdict(float)
        sampled_regret = collections.defaultdict(float)
        probs = self._sample_action_from_advantage(state, player)

        for action in state.legal_actions():
            expected_payoff[action] = self.traverse_tree(
                state.child(action), player)

        counter_factual_value = 0
        for action in state.legal_actions():
            counter_factual_value += probs[action] * expected_payoff[action]
        for action in state.legal_actions():
            sampled_regret[action] = expected_payoff[action]
            sampled_regret[action] -= counter_factual_value

        sampled_regret_arr = [0] * self._num_actions
        for action in sampled_regret:
            sampled_regret_arr[action] = sampled_regret[action]

        data = AdvantageMemory(
            np.array(state.information_state_tensor(), dtype=np.float32),
            np.array(self._iteration, dtype=int).reshape(
                1,
            ),
            np.array(sampled_regret_arr, dtype=np.float32),
        )

        self._append_to_advantage_buffer(player, data)
        return counter_factual_value

    def _traverse_opponent_node(self, state: T.HungarianTarokkState, player: pyspiel.PlayerId):
        other_player = state.current_player()
        probs = self._sample_action_from_advantage(state, other_player)
        # Recompute distribution for numerical errors.
        probs = np.array(probs)
        probs /= probs.sum()
        sampled_action = np.random.choice(range(self._num_actions), p=probs)

        data = StrategyMemory(
            np.array(
                state.information_state_tensor(other_player), dtype=np.float32
            ),
            np.array(self._iteration, dtype=int).reshape(
                1,
            ),
            np.array(probs, dtype=np.float32),
        )
        self._append_to_stategy_buffer(data)

        return self._traverse_game_tree(state.child(sampled_action), player)

    def traverse_tree(self, state: T.HungarianTarokkState, player: pyspiel.PlayerId):
        if state.is_terminal():
            return state.returns()[player]
        if state.is_chance_node():
            next_state = state.child(_chance_node_sample_action(state))
            return self.traverse_tree(next_state, player)

        if state.current_player() == player:
            return self._traverse_player_node(state, player)
        else:
            return self._traverse_opponent_node(state, player)
