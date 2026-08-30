import numpy as np
import torch
import pyspiel.hungarian_tarokk as T
import pyspiel
from tensordict import TensorClass
from .memory import *
from tqdm import trange, tqdm
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from os import cpu_count


class Trajectory(TensorClass["tensor_only"]):
    taken_actions: torch.Tensor
    sampling_probs: torch.Tensor
    target_probs: torch.Tensor
    players: torch.Tensor

    @classmethod
    def empty(cls, batch_size: list[int] = []) -> "Trajectory":
        return cls(
            taken_actions=torch.empty(batch_size, dtype=torch.long),
            sampling_probs=torch.empty(batch_size, dtype=torch.float64),
            target_probs=torch.empty([*batch_size, T.NUM_DISTINCT_ACTIONS], dtype=torch.float64),
            players=torch.empty(batch_size, dtype=torch.int8),
            batch_size=batch_size,
        )

    def write_(self, action, sampling_prob, target_prob, player, index=...) -> None:
        self.taken_actions[index] = action
        self.sampling_probs[index] = sampling_prob
        self.target_probs[index] = torch.as_tensor(target_prob)
        self.players[index] = player

class TrajectoryCursor(TensorClass["tensor_only"]):
    num_steps: torch.LongTensor
    num_inputs: torch.LongTensor

def calculate_regrets(trajectory: Trajectory, returns: np.ndarray):
    sampling_probs = trajectory.sampling_probs.numpy()
    target_probs = trajectory.target_probs.numpy()
    actions = trajectory.taken_actions.numpy()
    players = trajectory.players.numpy()
    returns = np.asarray(returns)

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
TRAJECTORY_INITIAL_SIZE = 150

class EnvWorker:
    def __init__(
        self,
        start,
        stop,
        inputs_buffer: InputTensorClass,
        trajectory_buffer: Trajectory,
        trajectory_inputs_buffer: InputTensorClass,
        inputs_mask: torch.BoolTensor,
        cursors: TrajectoryCursor,
        actions: torch.LongTensor
    ):
        self._game = pyspiel.load_game("hungarian_tarokk")
        self._in_flight = [
            (slot, self._game.new_initial_state())
            for slot in range(start, stop)
        ]
        self._inputs_buffer = inputs_buffer
        self._trajectory_buffer = trajectory_buffer
        self._trajectory_inputs_buffer = trajectory_inputs_buffer
        self._inputs_mask = inputs_mask
        self._cursors = cursors
        self._actions = actions

    def step_chance_nodes(self):
        for slot, state in self._in_flight:
            while state.is_chance_node():
                actions, probs = zip(*state.chance_outcomes())
                probs = np.asarray(probs); actions = np.asarray(actions)
                action = np.random.choice(actions, p=probs)

                state.apply_action(action)

                prob = probs[actions == action][0]
                probs_full = np.zeros([T.NUM_DISTINCT_ACTIONS], dtype=np.float32)
                probs_full[actions] = probs

                cursor = self._cursors[slot]
                self._trajectory_buffer.write_(
                    int(action), prob, probs_full, int(pyspiel.PlayerId.CHANCE),
                    index=(slot, cursor.num_steps),
                )
                cursor.num_steps += 1
            self._inputs_mask[slot] = False

    def step_non_chance_nodes(self):
        non_chance = []
        for slot, state in self._in_flight:
            if state.is_chance_node() or state.is_terminal():
                continue
            self._inputs_buffer.write_(state, slot)
            non_chance.append((slot, state))
            self._inputs_mask[slot] = True

        n_envs = len(non_chance)
        if n_envs == 0:
            return

        slots = torch.tensor([slot for slot, _ in non_chance], dtype=torch.long)
        inputs = self._inputs_buffer[slots]

        input_steps = torch.tensor([cursor.num_inputs for _, _, cursor in non_chance], dtype=torch.long)
        self._trajectory_inputs_buffer[slots, input_steps] = inputs

        traj_steps = torch.tensor([cursor.num_steps for _, _, cursor in non_chance], dtype=torch.long)
        self._trajectory_buffer[slots, traj_steps].update_(Trajectory(
            taken_actions=torch.from_numpy(self._actions),
            players=torch.tensor([state.current_player() for _, state, _ in non_chance], dtype=torch.int8),
            batch_size=[n_envs],
        ))

        for (slot, state) in zip(non_chance):
            cursor = self._cursors[slot]
            cursor.num_steps += 1
            cursor.num_inputs += 1

            try:
                state.apply_action(self._actions[slot])
            except pyspiel.SpielError:
                history = self._trajectory_buffer.taken_actions[slot, :self.cursor[slot].num_steps]
                print(self._actions[slot], state.legal_actions(), history)
                raise

    def handle_terminal_envs(self):
        new_in_flight = []
        terminated = []
        for slot, state in self._in_flight:
            if not state.is_terminal():
                new_in_flight.append((slot, state))
                continue

            terminated.append((slot, state.returns()))

            new_in_flight.append((
                slot,
                self._game.new_initial_state(),
            ))

        self._in_flight = new_in_flight
        print("sub", len(terminated))
        return terminated

    def step_envs(self):
        self.step_chance_nodes()
        self.step_non_chance_nodes()
        return self.handle_terminal_envs()


def env_worker_main(
    start,
    stop,
    inputs_buffer: InputTensorClass,
    trajectory_buffer: Trajectory,
    trajectory_inputs_buffer: InputTensorClass,
    inputs_mask: torch.BoolTensor,
    cursors: TrajectoryCursor,
    actions: torch.LongTensor,
    input_queue: mp.Queue,
    output_queue: mp.Queue
    ):
    worker = EnvWorker(start, stop, inputs_buffer, trajectory_buffer, trajectory_inputs_buffer, inputs_mask, cursors, actions)

    msg = input_queue.get()
    while msg != "stop":
        print("\nworker", start, msg)
        terminated = worker.step_envs()
        print("putting in queue")
        output_queue.put(terminated)
        print("\nworker", start, "put")
        msg = input_queue.get()

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
        self._trajectory_inputs_buffer = InputTensorClass.empty([batch_size, TRAJECTORY_INPUTS_INITIAL_SIZE])
        self._trajectory_buffer = Trajectory.empty([batch_size, TRAJECTORY_INITIAL_SIZE])
        self._inputs_mask = torch.zeros([batch_size], dtype=torch.bool)
        self.cursors = TrajectoryCursor(
            torch.zeros([batch_size], dtype=torch.long),
            torch.zeros([batch_size], dtype=torch.long),
            batch_size=[batch_size]
        )
        self.actions = torch.full([batch_size], -1, dtype=torch.long)

        self._inputs_buffer.share_memory_()
        self._inputs_buffer.unlock_()
        self._trajectory_inputs_buffer.share_memory_()
        self._trajectory_inputs_buffer.unlock_()
        self._trajectory_buffer.share_memory_()
        self._trajectory_buffer.unlock_()
        self._inputs_mask.share_memory_()
        self.cursors.share_memory_()
        self.cursors.unlock_()
        self.actions.share_memory_()

        self.num_processes = 1
        envs_per_process = batch_size // self.num_processes
        self._message_queues = [mp.Queue() for _ in range(self.num_processes)]
        self._output_queue = mp.Queue()
        self._processes = [
            mp.Process(target=env_worker_main, kwargs={
                "start": idx * envs_per_process,
                "stop": (idx + 1) * envs_per_process,
                "inputs_buffer": self._inputs_buffer,
                "trajectory_buffer": self._trajectory_buffer,
                "trajectory_inputs_buffer": self._trajectory_inputs_buffer,
                "inputs_mask": self._inputs_mask,
                "cursors": self.cursors,
                "actions": self.actions,
                "input_queue": self._message_queues[idx],
                "output_queue": self._output_queue
            })
            for idx in range(self.num_processes)
        ]
        for p in self._processes:
            p.start()

    def _ensure_trajectory_capacity(self, max_step):
        buffer_size = self._trajectory_buffer.size(1)
        if max_step >= buffer_size:
            new_buffer = Trajectory.empty([self._batch_size, int(buffer_size * 1.5)])
            new_buffer[:, :buffer_size] = self._trajectory_buffer
            self._trajectory_buffer = new_buffer

    def _ensure_inputs_buffer_capacity(self, max_step):
        buffer_size = self._trajectory_inputs_buffer.size(1)
        if max_step >= buffer_size:
            new_buffer = InputTensorClass.empty([self._batch_size, int(buffer_size * 1.5)])
            new_buffer[:, :buffer_size] = self._trajectory_inputs_buffer
            self._trajectory_inputs_buffer = new_buffer

    def _add_memory(self, target_probs, inputs, regrets, iteration):
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

    def process_terminated(self, terminated, iteration):
        trajectories: list[Trajectory] = []
        input_indices = []
        regrets = []
        for slot, returns in terminated:
            trajectory = self._trajectory_buffer[slot, :self.cursors[slot].num_steps]
            regret = calculate_regrets(trajectory, returns)
            trajectories.append(trajectory)
            input_indices.append((slot, slice(self.cursor[slot].num_inputs)))
            regrets.append(regret)
            self.cursors[slot].num_steps = 0
            self.cursors[slot].num_inputs = 0
            self._num_finished += 1

        if len(regrets) > 0:
            target_probs = torch.cat([traj.target_probs[traj.players >= 0] for traj in trajectories])
            inputs = torch.cat([self._trajectory_inputs_buffer[*idx] for idx in input_indices])
            regrets = torch.from_numpy(np.concatenate(regrets, axis=0))
            self._add_memory(target_probs, inputs, regrets, iteration)

    def evaluate_policies(self, policies):
        inputs = self._inputs_buffer[self._inputs_mask]
        n_envs = inputs.size(0)
        if n_envs == 0:
            return np.full([self._batch_size], -1, dtype=np.long)

        with torch.inference_mode():
            probs_sampling, probs_target = policies(inputs.to(self.device, non_blocking=True))

        actions = torch.multinomial(
            torch.from_numpy(probs_sampling),
            num_samples=1,
        ).squeeze(1).numpy()
        taken_probs = probs_sampling[np.arange(n_envs), actions]

        input_steps = self.cursors[self._inputs_mask].num_inputs
        self._ensure_inputs_buffer_capacity(input_steps.max())
        indices = self._inputs_mask.nonzero(as_tuple=True)[0]
        self._trajectory_inputs_buffer[indices, input_steps] = inputs

        traj_steps = self.cursors[self._inputs_mask].num_steps
        indices = self._inputs_mask.nonzero(as_tuple=True)[0]
        self._trajectory_buffer.update_at_(
            Trajectory(
                sampling_probs=torch.from_numpy(taken_probs).double(),
                target_probs=torch.from_numpy(np.asarray(probs_target)).double(),
            ),
            idx=(indices, traj_steps)
        )
        self.actions[self._inputs_mask] = actions

    def step_envs(self, policies, iteration):
        self.evaluate_policies(policies)
        self._ensure_trajectory_capacity(self.cursors.num_steps.max())
        for q in self._message_queues:
            q.put("go")
        terminated = [
            self._output_queue.get()
            for _ in range(self.num_processes)
        ]
        print("parent", terminated)
        self.process_terminated(terminated, iteration)

    def run_traversals(self, iteration: int, policies):
        self._num_finished = 0

        with tqdm(total=self._num_traversals, smoothing=0.01) as pbar:
            prev = self._num_finished
            while self._num_finished < self._num_traversals:
                self.step_envs(policies, iteration)
                pbar.update(self._num_finished - prev)
                prev = self._num_finished

    def join_processes(self):
        for q in self._message_queues:
            q.put("stop")
        for p in self._processes:
            p.join()
