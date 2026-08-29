import numpy as np
import pyspiel.hungarian_tarokk as T
import pyspiel
from .memory import *
from tqdm import trange, tqdm
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor


@dataclass
class Trajectory:
    inputs: list
    taken_actions: list[int]
    sampling_probs: list
    target_probs: list
    returns: list
    players: list

    @classmethod
    def new_empty(cls):
        return cls(
            inputs=[],
            taken_actions=[],
            sampling_probs=[],
            target_probs=[],
            returns=[],
            players=[]
        )

def calculate_regrets(trajectory: Trajectory):
    sampling_probs = np.array(trajectory.sampling_probs, dtype=np.float64)
    target_probs = np.array(trajectory.target_probs, dtype=np.float64)
    actions = np.array(trajectory.taken_actions)
    players = np.array(trajectory.players)
    returns = np.array(trajectory.returns)

    target_probs = target_probs[np.arange(target_probs.shape[0]), actions]

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

class GameSampler:
    def __init__(self, input_fn, game: pyspiel.Game, advantage_capacity, strategy_capacity, num_traversals, batch_size):
        self.advantage_memory = ReservoirBuffer(advantage_capacity)
        self.strategy_memory = ReservoirBuffer(strategy_capacity)
        self._input_fn = input_fn
        self._game = game
        self._num_actions = game.num_distinct_actions()
        self._num_traversals = num_traversals
        self._batch_size = batch_size

    def _add_memory(self, trajectory: Trajectory, regrets: np.ndarray, iteration):
        players_mask = np.array(trajectory.players) >= 0
        target_probs = np.array(trajectory.target_probs)[players_mask]
        inputs = torch.stack([inpt for inpt in trajectory.inputs if inpt is not None])

        for inpt, regret, probs in zip(inputs, regrets, target_probs):
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

    def step_chance_nodes(self):
        for state, trajectory in self._in_flight:
            while state.is_chance_node():
                trajectory.inputs.append(None)
                actions, probs = zip(*state.chance_outcomes())
                probs = np.array(probs); actions = np.array(actions)
                action = np.random.choice(actions, p=probs)

                state.apply_action(action)
                trajectory.taken_actions.append(int(action))

                prob = probs[actions == action][0]
                probs_full = np.zeros([T.NUM_DISTINCT_ACTIONS], dtype=np.float32)
                probs_full[actions] = probs
                trajectory.sampling_probs.append(prob)
                trajectory.target_probs.append(probs_full)
                trajectory.players.append(int(pyspiel.PlayerId.CHANCE))

    def step_non_chance_nodes(self, policies):
        inputs = []
        non_chance_states: list[tuple[pyspiel.State, Trajectory]] = []
        for idx, (state, trajectory) in enumerate(self._in_flight):
            if state.is_chance_node() or state.is_terminal():
                continue
            inputs.append(self._input_fn(state))
            non_chance_states.append((state, trajectory))

        if len(inputs) == 0:
            return
        n_envs = len(inputs)
        inputs = torch.stack(inputs)
        probs_sampling, probs_target = policies(inputs)
        actions = [
            np.random.choice(self._num_actions, p=probs)
            for probs in probs_sampling
        ]
        taken_probs = probs_sampling[np.arange(n_envs), actions]
        for inpt, action, taken_prob, target_prob, (state, trajectory) in zip(inputs, actions, taken_probs, probs_target, non_chance_states):
            trajectory.inputs.append(inpt)
            trajectory.taken_actions.append(action)
            trajectory.sampling_probs.append(taken_prob)
            trajectory.target_probs.append(target_prob)
            trajectory.players.append(state.current_player())

            state.apply_action(action)

    def handle_terminal_envs(self, iteration):
        for idx, (state, trajectory) in enumerate(self._in_flight):
            if not state.is_terminal():
                continue
            trajectory.returns = np.array(state.returns())
            regret = calculate_regrets(trajectory)
            self._add_memory(trajectory, regret, iteration)

            self._num_finished += 1
            if self._num_finished + len(self._in_flight) < self._num_traversals:
                self._in_flight[idx] = self._game.new_initial_state(), Trajectory.new_empty()
            else:
                self._in_flight.pop(idx)

    def step_envs(self, policies, iteration):
        self.step_chance_nodes()
        self.step_non_chance_nodes(policies)
        self.handle_terminal_envs(iteration)

    def run_traversals(self, iteration: int, policies):
        self._in_flight = [
            (self._game.new_initial_state(), Trajectory.new_empty())
            for _ in range(self._batch_size)
        ]
        self._num_finished = 0
        with tqdm(total=self._num_traversals, smoothing=0) as pbar:
            prev = self._num_finished
            while self._num_finished < self._num_traversals:
                self.step_envs(policies, iteration)
                pbar.update(self._num_finished - prev)
                prev = self._num_finished
            pbar.clear()
