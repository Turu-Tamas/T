import numpy as np
import torch
import pyspiel.hungarian_tarokk as T
import pyspiel
from tensordict import TensorClass
from .memory import *
from tqdm import trange, tqdm
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import torch.multiprocessing as mp
import traceback
from os import cpu_count


class WorkerError(RuntimeError):
    """Raised in the parent process when an env worker process crashes."""


@dataclass
class _WorkerFailure:
    traceback: str


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

TRAJECTORY_INPUTS_INITIAL_SIZE = 10
TRAJECTORY_INITIAL_SIZE = 10
MAX_CONSECUTIVE_CHANCE_NDOES = 42

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

    def _step_chance_nodes(self):
        for slot, state in self._in_flight:
            while state.is_chance_node():
                actions, probs = zip(*state.chance_outcomes())
                probs = np.asarray(probs); actions = np.asarray(actions)
                action = np.random.choice(actions, p=probs)

                state.apply_action(action)

                prob = probs[actions == action][0]
                probs_full = np.zeros([T.NUM_DISTINCT_ACTIONS], dtype=np.float32)
                probs_full[actions] = probs

                self._trajectory_buffer.write_(
                    int(action), prob, probs_full, int(pyspiel.PlayerId.CHANCE),
                    index=(slot, self._cursors[slot].num_steps),
                )
                self._cursors[slot].num_steps += 1
            self._inputs_mask[slot] = state.is_player_node()

    def write_inputs(self):
        for slot, state in self._in_flight:
            if state.is_chance_node() or state.is_terminal():
                continue
            self._inputs_buffer.write_(state, slot)

    def _step_non_chance_nodes(self):
        non_chance = []
        for slot, state in self._in_flight:
            if state.is_player_node():
                non_chance.append((slot, state))
        n_envs = len(non_chance)

        if n_envs == 0:
            return

        slots = torch.tensor([slot for slot, _ in non_chance], dtype=torch.long)
        inputs = self._inputs_buffer[slots]

        input_steps = self._cursors[slots].num_inputs
        self._trajectory_inputs_buffer[slots, input_steps] = inputs

        traj_steps = self._cursors[slots].num_steps
        players = torch.tensor([state.current_player() for _, state in non_chance], dtype=torch.int8)
        self._trajectory_buffer.taken_actions[slots, traj_steps] = self._actions[slots]
        self._trajectory_buffer.players[slots, traj_steps] = players

        for (slot, state) in non_chance:
            self._cursors.num_steps[slot] += 1
            self._cursors.num_inputs[slot] += 1

            try:
                state.apply_action(self._actions[slot])
                self._inputs_mask[slot] = state.is_player_node()
            except pyspiel.SpielError as e:
                history = self._trajectory_buffer.taken_actions[slot, :self._cursors[slot].num_steps]
                e.add_note(f"{self._actions[slot]}, {history}")
                raise

    def _reset_envs(self):
        new_in_flight = []
        for slot, state in self._in_flight:
            if not state.is_terminal():
                new_in_flight.append((slot, state))
                continue

            new_state = self._game.new_initial_state()
            new_in_flight.append((
                slot,
                new_state,
            ))
            self._inputs_mask[slot] = new_state.is_player_node()
            self._cursors.num_inputs[slot] = 0
            self._cursors.num_steps [slot]= 0

        self._in_flight = new_in_flight

    def get_terminal_envs(self):
        terminated = []
        for slot, state in self._in_flight:
            if not state.is_terminal():
                continue
            terminated.append((slot, state.returns()))

        return terminated

    def step_nodes(self):
        self._reset_envs()
        self._step_non_chance_nodes()
        self._step_chance_nodes()

    def update_buffers(self, traj_buf: Trajectory, traj_inputs_buf: InputTensorClass):
        self._trajectory_buffer = traj_buf
        self._trajectory_inputs_buffer = traj_inputs_buf

WORKER_STEP = "step-nodes"
WORKER_GET_TERMINALS = "get-terminals"
WORKER_WRITE_INPUTS = "write-inputs"
WORKER_UPDATE_BUFFERS = "update-buffers"

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
    output_queue: mp.Queue,
    error_queue: mp.Queue
    ):
    worker = EnvWorker(start, stop, inputs_buffer, trajectory_buffer, trajectory_inputs_buffer, inputs_mask, cursors, actions)

    msg = input_queue.get()
    while msg != "stop":
        try:
            if msg == WORKER_STEP:
                worker.step_nodes()
                output_queue.put("finished")
            elif msg == WORKER_WRITE_INPUTS:
                worker.write_inputs()
                output_queue.put("finished")
            elif msg == WORKER_GET_TERMINALS:
                terminated = worker.get_terminal_envs()
                output_queue.put(terminated)
            elif isinstance(msg, tuple) and msg[0] == WORKER_UPDATE_BUFFERS:
                worker.update_buffers(*msg[1])
                output_queue.put("finished")
        except Exception:
            error_queue.put(_WorkerFailure(traceback.format_exc()))
            raise
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

        self.num_processes = 16
        envs_per_process = batch_size // self.num_processes
        self._message_queues = [mp.Queue() for _ in range(self.num_processes)]
        self._output_queue = mp.Queue()
        self._error_queue = mp.Queue()
        self.subprocess_args = [
            {
                "start": idx * envs_per_process,
                "stop": (idx + 1) * envs_per_process,
                "inputs_buffer": self._inputs_buffer,
                "trajectory_buffer": self._trajectory_buffer,
                "trajectory_inputs_buffer": self._trajectory_inputs_buffer,
                "inputs_mask": self._inputs_mask,
                "cursors": self.cursors,
                "actions": self.actions,
                "input_queue": self._message_queues[idx],
                "output_queue": self._output_queue,
                "error_queue": self._error_queue
            }
            for idx in range(self.num_processes)
        ]

    def _ensure_trajectory_capacity(self, min_size):
        buffer_size = self._trajectory_buffer.size(1)
        if min_size > buffer_size:
            new_buffer = Trajectory.empty([self._batch_size, max(min_size, int(buffer_size * 1.5))])
            new_buffer[:, :buffer_size] = self._trajectory_buffer
            new_buffer.share_memory_()
            new_buffer.unlock_()
            self._trajectory_buffer = new_buffer
            self._send_messages((WORKER_UPDATE_BUFFERS, (self._trajectory_buffer, self._trajectory_inputs_buffer)))
            self._get_results()

    def _ensure_inputs_buffer_capacity(self, min_size):
        buffer_size = self._trajectory_inputs_buffer.size(1)
        if min_size > buffer_size:
            new_buffer = InputTensorClass.empty([self._batch_size, max(min_size, int(buffer_size * 1.5))])
            new_buffer[:, :buffer_size] = self._trajectory_inputs_buffer
            new_buffer.share_memory_()
            new_buffer.unlock_()
            self._trajectory_inputs_buffer = new_buffer
            self._send_messages((WORKER_UPDATE_BUFFERS, (self._trajectory_buffer, self._trajectory_inputs_buffer)))
            self._get_results()

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
            trajectory = self._trajectory_buffer[slot, :self.cursors.num_steps[slot]]
            regret = calculate_regrets(trajectory, returns)
            trajectories.append(trajectory)
            input_indices.append((slot, slice(self.cursors[slot].num_inputs)))
            regrets.append(regret)

            # warning: cursor is updated here, child sees the wrong number until this point
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

        traj_steps = self.cursors[self._inputs_mask].num_steps
        indices = self._inputs_mask.nonzero(as_tuple=True)[0]
        self._trajectory_buffer.sampling_probs[indices, traj_steps] = torch.from_numpy(taken_probs).double()
        self._trajectory_buffer.target_probs[indices, traj_steps] = torch.from_numpy(np.asarray(probs_target)).double()
        self.actions[self._inputs_mask] = torch.from_numpy(actions)

    def _send_messages(self, msg):
        for q in self._message_queues:
            q.put(msg)

    def _get_results(self):
        if not self._error_queue.empty():
            raise self._error_queue.get_nowait()
        return [
            self._output_queue.get()
            for _ in range(self.num_processes)
        ]

    def step_envs(self, policies, iteration):
        # +1 is the non-chance step
        self._ensure_trajectory_capacity(self.cursors.num_steps.max() + 1 + MAX_CONSECUTIVE_CHANCE_NDOES) 
        self._ensure_inputs_buffer_capacity(self.cursors.num_inputs.max() + 1)

        self._send_messages(WORKER_WRITE_INPUTS)
        self._get_results()
        self.evaluate_policies(policies)

        self._send_messages(WORKER_STEP)
        self._get_results()

        self._send_messages(WORKER_GET_TERMINALS)
        terminals = self._get_results()
        self.process_terminated([x for xs in terminals for x in xs], iteration)

    def run_traversals(self, iteration: int, policies):
        self._num_finished = 0
        self._processes = [
            mp.Process(target=env_worker_main, kwargs=self.subprocess_args[idx])
            for idx in range(self.num_processes)
        ]
        for p in self._processes:
            p.start()

        with tqdm(total=self._num_traversals, smoothing=0.01) as pbar:
            prev = self._num_finished
            while self._num_finished < self._num_traversals:
                try:
                    self.step_envs(policies, iteration)
                except:
                    self.join_processes()
                    pbar.clear()
                    raise
                pbar.update(self._num_finished - prev)
                prev = self._num_finished

        self.join_processes()

    def join_processes(self):
        for q in self._message_queues:
            q.put("stop")
        for p in self._processes:
            p.join()

    def clear_queues(self):
        for q in self._message_queues + [self._output_queue]:
            while not q.empty():
                q.get()
