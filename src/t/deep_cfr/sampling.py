import torch
import numpy as np
import pyspiel.hungarian_tarokk as T
import pyspiel
from .memory import *
from tqdm import trange

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

    def sample_trajectory(self, policy):
        state = self._game.new_initial_state()
        inputs = []
        taken_actions = []
        taken_probs = []
        while not state.is_terminal():
            if state.is_chance_node():
                actions, prob = zip(*state.chance_outcomes())
                action = np.random.choice(actions, p=prob)
            inputs.append(self._input_fn(state))
            action_probs = policy(inputs[-1])
            action = np.random.choice(range(self._num_actions), p=action_probs)
            prob = action_probs[action]
            taken_actions.append(action)
            taken_probs.append(prob)
        return inputs, taken_actions, taken_probs

    def run_traversals(self, player, iteration: int, policy):
        if state is None:
            state = self._game.new_initial_state()
        for _ in trange(self._num_traversals):
            self._traversal += 1
            self._traverse_tree(player, state, iteration)
