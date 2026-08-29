import numpy as np
import pyspiel.hungarian_tarokk as T
import pyspiel
from .memory import *
from tqdm import trange
from ..models.constants import NUM_PLAYERS
from dataclasses import dataclass


class GameSampler:
    @dataclass
    class _Trajectory:
        inputs: list
        taken_actions: list[int]
        sampling_probs: np.ndarray
        target_probs: np.ndarray
        returns: np.ndarray
        players: np.ndarray

    def __init__(self, input_fn, game: pyspiel.Game, advantage_capacity, strategy_capacity, num_traversals):
        self.advantage_memory = ReservoirBuffer(advantage_capacity)
        self.strategy_memory = ReservoirBuffer(strategy_capacity)
        self._input_fn = input_fn
        self._game = game
        self._traversal = 0
        self._num_actions = game.num_distinct_actions()
        self._num_traversals = num_traversals

    def _sample_trajectory(self, policies):
        state = self._game.new_initial_state()
        inputs = []
        taken_actions = []
        sampling_probs = []
        target_probs = []
        players = []
        while not state.is_terminal():
            players.append(state.current_player())

            if state.is_chance_node():
                inputs.append(None)
                actions, probs = zip(*state.chance_outcomes())
                probs = np.array(probs); actions = np.array(actions)
                action = np.random.choice(actions, p=probs)
                prob = probs[actions == action][0]
                target_probs.append(prob)
            else:
                inputs.append(self._input_fn(state))
                probs_sampling, probs_target = policies(inputs[-1])
                action = np.random.choice(self._num_actions, p=probs_sampling)
                prob = probs_sampling[action]
                target_probs.append(probs_target[action])

            state.apply_action(action)
            taken_actions.append(int(action))
            sampling_probs.append(prob)

        return self._Trajectory(
            inputs=inputs,
            taken_actions=np.array(taken_actions),
            sampling_probs=np.array(sampling_probs, np.float64),
            target_probs=np.array(target_probs, np.float64),
            returns=np.array(state.returns()),
            players=np.array(players)
        )

    def _calculate_regrets(self, trajectory: _Trajectory):
        sampling_probs = np.array(trajectory.sampling_probs, np.float64)
        target_probs = np.array(trajectory.target_probs, np.float64)
        actions = np.array(trajectory.taken_actions)
        players = np.array(trajectory.players)
        returns = np.array(trajectory.returns)

        not_chance_mask = players >= 0
        n_steps = not_chance_mask.sum()
        traj_prob = np.prod(sampling_probs)
        suffix_prob = np.flip(np.cumprod(np.flip(target_probs)))[not_chance_mask]

        cf_reach = np.empty([4, len(actions)])
        for player in range(4):
            player_mask = players == player
            player_excluded_probs = np.where(player_mask, 1, target_probs)

            cf_reach[player] = np.cumprod(player_excluded_probs, axis=0)
        cf_reach = cf_reach[:, not_chance_mask]

        acting_players = players[not_chance_mask]
        cf_reach_active = cf_reach[acting_players, np.arange(n_steps)]

        regrets = np.empty([n_steps, T.NUM_DISTINCT_ACTIONS])
        W = returns[acting_players] * cf_reach_active / traj_prob # [N_actions]
        regrets = (-W * suffix_prob).reshape(-1, 1).repeat(T.NUM_DISTINCT_ACTIONS, axis=1)
        regrets[
            np.arange(n_steps - 1),
            actions[not_chance_mask][:-1]
        ] = W[:-1] * (suffix_prob[1:] - suffix_prob[:-1])

        return regrets

    def _add_memory(self, trajectory: _Trajectory, regrets: np.ndarray, iteration):
        players_mask = trajectory.players >= 0
        inputs = torch.stack([inpt for inpt in trajectory.inputs if inpt is not None])

        for inpt, regret, probs in zip(inputs, regrets, trajectory.target_probs[players_mask]):
            self.advantage_memory.append(AdvantageMemory(
                inputs=inpt,
                advantage=torch.tensor(regret),
                iteration=torch.tensor(iteration)
            ))
            self.strategy_memory.append(StrategyMemory(
                inputs=inpt,
                action_probs=torch.tensor(probs),
                iteration=torch.tensor(iteration)
            ))

    def run_traversals(self, player, iteration: int, policies):
        for _ in trange(self._num_traversals):
            self._traversal += 1
            sample = self._sample_trajectory(player, policies)
            regrets = self._calculate_regrets(sample)
            self._add_memory(sample, regrets, iteration)
