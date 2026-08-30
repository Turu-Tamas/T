import numpy as np
import pyspiel.hungarian_tarokk as T
import pyspiel
from .memory import *
from tqdm import trange, tqdm
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import time


@dataclass
class Trajectory:
    taken_actions: list[int]
    sampling_probs: list
    target_probs: list
    returns: list
    players: list
    num_inputs: int = 0

    @classmethod
    def new_empty(cls):
        return cls(
            taken_actions=[],
            sampling_probs=[],
            target_probs=[],
            returns=[],
            players=[]
        )

    def __len__(self):
        return len(self.players)

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

TRAJECTORY_INPUTS_INITIAL_SIZE = 70

class GameSampler:
    def __init__(self, advantage_capacity, strategy_capacity, num_traversals, batch_size, device):
        self.advantage_memory = ReservoirBuffer(advantage_capacity)
        self.strategy_memory = ReservoirBuffer(strategy_capacity)
        self._game = pyspiel.load_game("hungarian_tarokk")
        self._num_actions = self._game.num_distinct_actions()
        self._num_traversals = num_traversals
        self._batch_size = batch_size
        self.device = device
        self._inputs_buffer = InputTensorClass.empty([batch_size]).pin_memory()
        self._inputs_buffer.share_memory_()
        self._trajectory_inputs_buffer = InputTensorClass.empty([batch_size, TRAJECTORY_INPUTS_INITIAL_SIZE])

    def _add_memory(self, trajectory: Trajectory, inputs, regrets: np.ndarray, iteration):
        players_mask = np.array(trajectory.players) >= 0
        target_probs = torch.from_numpy(np.array(trajectory.target_probs))[players_mask]

        regrets = torch.from_numpy(regrets)
        iteration = torch.full(inputs.shape, iteration)
        self.advantage_memory.extend(AdvantageMemory(
            inputs=inputs,
            advantage=regrets,
            iteration=iteration,
            batch_size=inputs.shape
        ))
        self.strategy_memory.extend(StrategyMemory(
            inputs=inputs,
            action_probs=target_probs,
            iteration=iteration,
            batch_size=inputs.shape
        ))

    def step_chance_nodes(self):
        for _slot, state, trajectory in self._in_flight:
            while state.is_chance_node():
                actions, probs = zip(*state.chance_outcomes())
                probs = np.asarray(probs); actions = np.asarray(actions)
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
        non_chance = []
        for slot, state, trajectory in self._in_flight:
            if state.is_chance_node() or state.is_terminal():
                continue
            self._inputs_buffer.write_(state, slot)
            non_chance.append((slot, state, trajectory))

        n_envs = len(non_chance)
        if n_envs == 0:
            return

        slots = torch.tensor([slot for slot, _, _ in non_chance], dtype=torch.long)
        inputs = self._inputs_buffer[slots]

        with torch.inference_mode():
            probs_sampling, probs_target = policies(inputs.to(self.device, non_blocking=True))

        actions = torch.multinomial(
            torch.from_numpy(probs_sampling),
            num_samples=1,
        ).squeeze(1).numpy()
        taken_probs = probs_sampling[np.arange(n_envs), actions]

        steps = torch.tensor([trajectory.num_inputs for _, _, trajectory in non_chance], dtype=torch.long)
        buffer_size = self._trajectory_inputs_buffer.size(1)
        if steps.max() >= buffer_size:
            new_buffer = InputTensorClass.empty([self._batch_size, int(buffer_size * 1.5)])
            new_buffer[:, :buffer_size] = self._trajectory_inputs_buffer
            self._trajectory_inputs_buffer = new_buffer

        self._trajectory_inputs_buffer[slots, steps] = inputs

        for (slot, state, trajectory), action, taken_prob, target_prob in zip(
            non_chance, actions, taken_probs, probs_target
        ):
            trajectory.taken_actions.append(action)
            trajectory.sampling_probs.append(taken_prob)
            trajectory.target_probs.append(target_prob)
            trajectory.players.append(state.current_player())
            trajectory.num_inputs += 1

            try:
                state.apply_action(action)
            except pyspiel.SpielError:
                print(action, state.legal_actions(), trajectory.taken_actions)
                raise

    def handle_terminal_envs(self, iteration):
        remaining = len(self._in_flight)
        new_in_flight = []
        for slot, state, trajectory in self._in_flight:
            if not state.is_terminal():
                new_in_flight.append((slot, state, trajectory))
                continue

            trajectory.returns = np.array(state.returns())
            regret = calculate_regrets(trajectory)
            inputs = self._trajectory_inputs_buffer[slot, :trajectory.num_inputs]
            self._add_memory(trajectory, inputs, regret, iteration)
            self._num_finished += 1

            if self._num_finished + remaining > self._num_traversals:
                remaining -= 1
            else:
                new_in_flight.append((
                    slot,
                    self._game.new_initial_state(),
                    Trajectory.new_empty(),
                ))

        self._in_flight = new_in_flight

    def step_envs(self, policies, iteration):
        self.step_chance_nodes()
        self.step_non_chance_nodes(policies)
        self.handle_terminal_envs(iteration)

    def run_traversals(self, iteration: int, policies):
        self._in_flight = [
            (slot, self._game.new_initial_state(), Trajectory.new_empty())
            for slot in range(self._batch_size)
        ]
        self._num_finished = 0

        with tqdm(total=self._num_traversals, smoothing=0.01) as pbar:
            prev = self._num_finished
            while self._num_finished < self._num_traversals:
                self.step_envs(policies, iteration)
                pbar.update(self._num_finished - prev)
                prev = self._num_finished
