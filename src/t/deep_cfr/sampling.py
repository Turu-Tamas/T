import torch
import numpy as np
import pyspiel.hungarian_tarokk as T
import pyspiel
from .memory import *

def _chance_node_sample_action(state: T.HungarianTarokkState):
    outcome, prob = zip(*state.chance_outcomes())
    action = np.random.choice(outcome, p=prob)
    return action


class GameSampler:
    def __init__(self, input_fn, game: pyspiel.Game, advantage_capacity, strategy_capacity, num_traversals):
        self.advantage_memory = ReservoirBuffer(advantage_capacity)
        self.strategy_memory = ReservoirBuffer(strategy_capacity)
        self._input_fn = input_fn
        self._game = game
        self._traversal = 0
        self._num_actions = game.num_distinct_actions()
        self._num_traversals = num_traversals

    def set_advantage_network(self, networks):
        self.network = networks

    def _sample_action_from_advantage(self, inputs, legal_actions):
        legals = np.array(legal_actions)
        with torch.no_grad():
            raw_advantages = (
                self.network(inputs).cpu().numpy()
            )
        advantages = np.maximum(raw_advantages, 0)
        matched_regrets = np.zeros([self._num_actions])
        cumulative_regret = advantages[legals].sum()
        if cumulative_regret > 1e-6:
            matched_regrets[legals] = advantages[legals] / cumulative_regret
        else:
            matched_regrets[legals[np.argmax(raw_advantages[legals])]] = 1
        return matched_regrets

    def _traverse_player_node(self, player: pyspiel.PlayerId, state: T.HungarianTarokkState, iteration: int):
        inputs = self._input_fn(state)
        legal_actions = state.legal_actions(player)
        probs = self._sample_action_from_advantage(inputs, legal_actions)

        expected_payoff = np.zeros([self._num_actions], dtype=np.float32)
        expected_payoff[legal_actions] = [
            self._traverse_tree(player, state.child(action))
            for action in legal_actions
        ]

        counter_factual_value = 0
        for action in legal_actions:
            counter_factual_value += probs[action] * expected_payoff[action]

        sampled_regret_arr = np.zeros([self._num_actions], dtype=np.float32)
        sampled_regret_arr[legal_actions] = expected_payoff[legal_actions] - counter_factual_value

        data = AdvantageMemory(
            inputs=self._input_fn(state),
            iteration=torch.tensor(iteration, dtype=torch.float32),
            advantage=torch.from_numpy(sampled_regret_arr),
        )

        self.advantage_memory.append(data)
        return counter_factual_value

    def _traverse_opponent_node(self, player: pyspiel.PlayerId, state: T.HungarianTarokkState, iteration: int):
        other_player = state.current_player()
        inputs = self._input_fn(state)
        legal_actions = state.legal_actions(other_player)
        probs = self._sample_action_from_advantage(inputs, legal_actions)
        sampled_action = np.random.choice(self._num_actions, p=probs)

        data = StrategyMemory(
            inputs=self._input_fn(state),
            iteration=torch.tensor(iteration, dtype=torch.float32),
            strategy_action_probs=torch.from_numpy(probs).to(torch.float32)
        )
        self.strategy_memory.append(data)

        return self._traverse_tree(player, state.child(sampled_action))

    def _traverse_tree(self, player: pyspiel.PlayerId, state: pyspiel.State, iteration: int):
        if state.is_terminal():
            return state.returns()[player]
        if state.is_chance_node():
            next_state = state.child(_chance_node_sample_action(state))
            return self._traverse_tree(player, next_state)

        if state.current_player() == player:
            return self._traverse_player_node(player, state)
        else:
            return self._traverse_opponent_node(player, state)

    def run_traversals(self, player, iteration: int, state: pyspiel.State=None):
        if state is None:
            state = self._game.new_initial_state()
        for _ in range(self._num_traversals):
            self._traversal += 1
            self._traverse_tree(player, state, iteration)
