from t.models.input_struct import InputTensorClass
from tensordict import TensorClass
import pyspiel
import pyspiel.hungarian_tarokk as T
import torch
import numpy as np
from torchrl.data import ReplayBuffer
import torch.multiprocessing as mp
import traceback
import tqdm
from time import sleep
from torch.distributions import Categorical

class InferenceBuffers(TensorClass):
    obs: InputTensorClass
    actions: torch.LongTensor

    @staticmethod
    def new(shape):
        return InferenceBuffers(
            obs=InputTensorClass.empty(shape),
            actions=torch.empty(shape, dtype=torch.long),
            batch_size=shape
        )

class TrajectoryBuffer(TensorClass):
    observations: InputTensorClass
    indices: torch.LongTensor
    actions: torch.CharTensor

    @staticmethod
    def new(num_envs, buffer_size):
        return TrajectoryBuffer(
            observations=InputTensorClass.empty([num_envs, buffer_size]),
            indices=torch.zeros([num_envs], dtype=torch.long),
            actions=torch.empty([num_envs, buffer_size], dtype=torch.uint8),
            batch_size=[num_envs]
        )

class ReplayFrames(TensorClass):
    observations: InputTensorClass
    returns: torch.FloatTensor
    actions: torch.CharTensor

    @staticmethod
    def empty(shape):
        return ReplayFrames(
            observations=InputTensorClass.empty(shape),
            returns=torch.empty([*shape, 4], dtype=torch.float),
            actions=torch.empty(shape, dtype=torch.uint8),
            batch_size=shape,
        )

class TarokkEnvs:
    INITIAL_TRAJECTORY_BUFFER_SIZE = 50
    REPLAY_EXTEND_BATCH_SIZE = 2048
    def __init__(self, num_envs: int, buffers: InferenceBuffers, replay_buffer: ReplayBuffer):
        self.game = pyspiel.load_game("hungarian_tarokk")
        self.states = [self.game.new_initial_state() for _ in range(num_envs)]

        self.inference_buffers = buffers
        self.num_envs = num_envs
        self.replay_buffer = replay_buffer

        self.trajectory_buffer = TrajectoryBuffer.new(num_envs, self.INITIAL_TRAJECTORY_BUFFER_SIZE)
        self.finished_trajectories = ReplayFrames.empty([self.REPLAY_EXTEND_BATCH_SIZE + 400])
        self.finished_cursor = 0

        self.step_to_player_node()
        self.write_obs()

    def write_frames(self, idx):
        traj_len = self.trajectory_buffer.indices[idx]
        if traj_len == 0:
            return
        observations = self.trajectory_buffer.observations[idx, :traj_len]
        actions = self.trajectory_buffer.actions[idx, :traj_len]
        frames = ReplayFrames(
            observations=observations,
            returns=self.states[idx].returns(),
            actions=actions,
            batch_size=[],
        )
        self.finished_trajectories[self.finished_cursor : self.finished_cursor + traj_len] = frames

        self.finished_cursor += traj_len
        if self.finished_cursor > self.REPLAY_EXTEND_BATCH_SIZE:
            self.replay_buffer.extend(self.finished_trajectories[:self.finished_trajectories])
            self.finished_cursor = 0

    def reset_env(self, idx):
        self.states[idx] = self.game.new_initial_state()
        self.trajectory_buffer.indices[idx] = 0
        return self.states[idx]

    def step_to_player_node(self):
        for idx, state in enumerate(self.states):
            while not state.is_player_node():
                if state.is_chance_node():
                    actions, probs = zip(*state.chance_outcomes())
                    action = np.random.choice(actions, p=probs)
                    state.apply_action(action)
                elif state.is_terminal():
                    self.write_frames(idx)
                    state = self.reset_env(idx)

    def maybe_grow_traj_buffer(self):
        traj_buf = self.trajectory_buffer
        old_size = traj_buf.shape[0]
        if traj_buf.indices.max() + 1 >= old_size:
            new_buffer = TrajectoryBuffer.new(self.num_envs, int(old_size * 1.5))
            new_buffer[:, :old_size] = traj_buf
            self.trajectory_buffer = new_buffer

    def write_obs(self):
        for idx, state in enumerate(self.states):
            self.inference_buffers.obs[idx].write_(state)

        self.maybe_grow_traj_buffer()
        traj_buf = self.trajectory_buffer

        indices = (torch.arange(self.num_envs), traj_buf.indices)
        traj_buf.actions[*indices] = self.inference_buffers.actions.to(torch.uint8)
        traj_buf.observations[*indices] = self.inference_buffers.obs
        traj_buf.indices += 1

    def apply_actions(self):
        for idx, state in enumerate(self.states):
            state.apply_action(self.inference_buffers.actions[idx])

    def step(self):
        self.apply_actions()
        self.step_to_player_node()
        self.write_obs()


INFERENCE_STOP = "stop"
INFERENCE_EVAL = "eval"
ENV_OBS_READY = "obs"
ENV_ACTIONS_READY = "actions"
ENV_STOP = "stop"

class InferenceProcess:
    def __init__(self, buffers: InferenceBuffers, in_queue: mp.Queue, env_queues: list[mp.Queue], network, device):
        self.buffers = buffers
        self.in_queue = in_queue
        self.network = network
        self.device = device
        self.env_queues = env_queues

    def _run(self):
        cmd = None
        while cmd != INFERENCE_STOP:
            cmd, val = self.in_queue.get()
            if cmd == ENV_OBS_READY:
                inputs = self.buffers.obs[val].to(self.device)
                logits = self.network(inputs).cpu()
                self.buffers.actions[val] = Categorical(logits=logits).sample().cpu()
                self.env_queues[val].put(ENV_ACTIONS_READY)

    @staticmethod
    def run(buffers: InferenceBuffers, in_queue: mp.Queue, env_queues: list[mp.Queue], network, device, err_queue: mp.Queue):
        try:
            inner = InferenceProcess(buffers, in_queue, env_queues, network, device)
            inner._run()
        except Exception as e:
            err_queue.put((e, traceback.format_exc()))
            raise

class EnvProcess:
    def __init__(self, num_envs, idx, in_queue: mp.Queue, inference_queue: mp.Queue, inference_buffers: InferenceBuffers, replay_buffer: ReplayBuffer):
        self.envs = TarokkEnvs(num_envs, inference_buffers, replay_buffer)
        self.in_queue = in_queue
        self.inference_queue = inference_queue
        self.idx = idx

    def _run(self):
        self.inference_queue.put((ENV_OBS_READY, self.idx))
        msg = None
        while msg != ENV_STOP:
            msg = self.in_queue.get()
            if msg == ENV_ACTIONS_READY:
                self.envs.step()
                self.inference_queue.put((ENV_OBS_READY, self.idx))

    @staticmethod
    def run(num_envs, idx, in_queue: mp.Queue, inference_queue: mp.Queue, inference_buffers: InferenceBuffers, replay_buffer: ReplayBuffer, err_queue: mp.Queue):
        try:
            inner = EnvProcess(num_envs, idx, in_queue, inference_queue, inference_buffers, replay_buffer)
            inner._run()
        except Exception as e:
            err_queue.put((e, traceback.format_exc()))
            raise
            
class TarokkCollector:
    def __init__(self, num_workers, envs_per_worker, replay_buffer: ReplayBuffer, network):
        self.inference_queue = mp.Queue()
        self.err_queue = mp.Queue()
        self.env_queues = [mp.Queue() for _ in range(num_workers)]
        self.inference_buffers = InferenceBuffers.new([num_workers, envs_per_worker])
        self.replay_buffer = replay_buffer.share()
        self.network = network
        self.inference_buffers.share_memory_()
        self.inference_buffers.unlock_()
        self.inference_process = mp.Process(
            target=InferenceProcess.run,
            kwargs={
                "buffers": self.inference_buffers,
                "in_queue": self.inference_queue,
                "env_queues": self.env_queues,
                "err_queue": self.err_queue,
                "device": "cuda",
                "network": network,
            }
        )
        self.env_processes = [
            mp.Process(
                target=EnvProcess.run,
                kwargs={
                    "num_envs": envs_per_worker,
                    "idx": idx,
                    "in_queue": self.env_queues[idx],
                    "inference_queue": self.inference_queue,
                    "inference_buffers": self.inference_buffers[idx],
                    "replay_buffer": replay_buffer,
                    "err_queue": self.err_queue,
                }
            )
            for idx in range(num_workers)
        ]

    def handle_errors(self):
        if not self.err_queue.empty():
            err: Exception
            err, trace = self.err_queue.get()
            print(trace)
            print(type(err))
            raise RuntimeError

    def collect(self, num_steps):
        for proc in self.env_processes:
            proc.start()
        self.inference_process.start()
    
        initial_write_count = self.replay_buffer.write_count
        last_count = self.replay_buffer.write_count
        with tqdm.tqdm(range(num_steps), smoothing=0.0) as pbar:
            current_count = self.replay_buffer.write_count
            while current_count - initial_write_count < num_steps:
                self.handle_errors()
                sleep(1.0)
                current_count = self.replay_buffer.write_count
                pbar.update(current_count - last_count)
                last_count = current_count

        for q in self.env_queues:
            q.put(ENV_STOP)
        self.inference_queue.put((INFERENCE_STOP, None))

        for proc in self.env_processes:
            proc.join()
        self.inference_process.join()
