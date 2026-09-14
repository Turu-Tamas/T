from t.models.input_struct import InputTensorClass
from tensordict import TensorClass
import pyspiel
import torch
import numpy as np
from torchrl.data import ReplayBuffer

class InferenceBuffers(TensorClass["tensor_only"]):
    obs: InputTensorClass
    actions: torch.LongTensor

    @staticmethod
    def new(shape):
        return InferenceBuffers(
            obs=InputTensorClass.empty(shape),
            actions=torch.empty(shape, dtype=torch.long),
            batch_size=shape
        )

class TrajectoryFrames(TensorClass):
    observations: InputTensorClass
    actions: torch.CharTensor

class TrajectoryBuffer(TensorClass):
    frames: TrajectoryFrames
    indices: torch.LongTensor

    @staticmethod
    def new(num_envs, buffer_size):
        return TrajectoryBuffer(
            frames=TrajectoryFrames(
                observations=InputTensorClass.empty([num_envs, buffer_size]),
                actions=torch.empty([num_envs, buffer_size], dtype=torch.uint8),
                batch_size=[num_envs, buffer_size]
            ),
            indices=torch.zeros([num_envs], dtype=torch.long),
            batch_size=[num_envs]
        )

    def realloc(self):
        old_size = self.frames.shape[1]
        num_envs = self.shape[0]
        new_buffer = self.new(num_envs, int(old_size * 1.5))
        new_buffer.indices = self.indices
        new_buffer.frames[:, :old_size] = self.frames
        return new_buffer

    def capacity(self):
        return self.frames.shape[1]

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
    def __init__(self, num_envs: int, buffers: InferenceBuffers, replay_buffer: ReplayBuffer, trajectory_counter):
        self.game = pyspiel.load_game("hungarian_tarokk")
        self.states = [self.game.new_initial_state() for _ in range(num_envs)]

        self.inference_buffers = buffers
        self.num_envs = num_envs
        self.replay_buffer = replay_buffer
        self.trajectory_counter = trajectory_counter

        # holds unfinished trajectories indexed as [env, frame]
        self.trajectory_buffer = TrajectoryBuffer.new(num_envs, self.INITIAL_TRAJECTORY_BUFFER_SIZE)
        # holds the frames of finished trajectories before writing them to the replay buffer in a single batch
        self.finished_trajectories = ReplayFrames.empty([self.REPLAY_EXTEND_BATCH_SIZE + 400])
        self.finished_cursor = 0

        self.step_to_player_nodes()
        self.write_obs()

    def write_finished_trajectory(self, env_idx):
        traj_len = self.trajectory_buffer.indices[env_idx]
        if traj_len == 0:
            return
        observations = self.trajectory_buffer.frames.observations[env_idx, :traj_len]
        actions = self.trajectory_buffer.frames.actions[env_idx, :traj_len]
        returns = torch.as_tensor(self.states[env_idx].returns()).expand([traj_len, 4])
        frames = ReplayFrames(
            observations=observations,
            returns=returns,
            actions=actions,
            batch_size=[traj_len],
        )
        self.finished_trajectories[self.finished_cursor : self.finished_cursor + traj_len] = frames

        self.finished_cursor += traj_len
        if self.finished_cursor > self.REPLAY_EXTEND_BATCH_SIZE:
            self.replay_buffer.extend(self.finished_trajectories[:self.finished_cursor])
            self.finished_cursor = 0

    def reset_env(self, idx):
        self.states[idx] = self.game.new_initial_state()
        self.trajectory_buffer.indices[idx] = 0
        return self.states[idx]

    def step_to_player_nodes(self):
        for idx, state in enumerate(self.states):
            while not state.is_player_node():
                if state.is_chance_node():
                    actions, probs = zip(*state.chance_outcomes())
                    action = np.random.choice(actions, p=probs)
                    state.apply_action(action)
                elif state.is_terminal():
                    self.write_finished_trajectory(idx)
                    state = self.reset_env(idx)
                    with self.trajectory_counter.get_lock():
                        self.trajectory_counter.value += 1

    def maybe_grow_traj_buffer(self):
        traj_buf = self.trajectory_buffer
        if traj_buf.indices.max() + 1 >= traj_buf.capacity():
            self.trajectory_buffer = traj_buf.realloc()

    def write_obs(self):
        for idx, state in enumerate(self.states):
            self.inference_buffers.obs.write_(state, idx)

        self.maybe_grow_traj_buffer()
        traj_buf = self.trajectory_buffer

        indices = (torch.arange(self.num_envs), traj_buf.indices)
        traj_buf.frames.actions[*indices] = self.inference_buffers.actions.to(torch.uint8)
        traj_buf.frames.observations[*indices] = self.inference_buffers.obs
        traj_buf.indices += 1

    def apply_actions(self):
        for idx, state in enumerate(self.states):
            state.apply_action(self.inference_buffers.actions[idx])

    def step(self):
        self.apply_actions()
        # step to player nodes first so that we have an observation to write
        self.step_to_player_nodes()
        self.write_obs()
