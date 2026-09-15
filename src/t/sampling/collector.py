import torch
from torchrl.data import ReplayBuffer
import torch.multiprocessing as mp
import traceback
import tqdm
from time import sleep
from .env import InferenceBuffers, TarokkEnvs
import queue

INFERENCE_STOP = "stop"
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

    @torch.inference_mode()
    def run(self):
        cmd = None
        while cmd != INFERENCE_STOP:
            cmd, worker_idx = self.in_queue.get()
            if cmd == ENV_OBS_READY:
                inputs = self.buffers.obs[worker_idx].to(self.device)
                logits = self.network(inputs)
                actions = torch.multinomial(logits.softmax(-1), 1)
                self.buffers.actions[worker_idx] = actions.cpu().squeeze(-1)
                self.env_queues[worker_idx].put(ENV_ACTIONS_READY)

    @staticmethod
    def run_process(err_queue, *args, **kwargs):
        try:
            inner = InferenceProcess(*args, **kwargs)
            inner.run()
        except Exception as e:
            err_queue.put((e, traceback.format_exc()))
            raise

class EnvProcess:
    def __init__(self, num_envs, idx, in_queue: mp.Queue, inference_queue: mp.Queue, inference_buffers: InferenceBuffers, replay_buffer: ReplayBuffer, trajectory_counter):
        self.envs = TarokkEnvs(num_envs, inference_buffers, replay_buffer, trajectory_counter)
        self.in_queue = in_queue
        self.inference_queue = inference_queue
        self.idx = idx

    def run(self):
        self.inference_queue.put((ENV_OBS_READY, self.idx))
        msg = None
        while msg != ENV_STOP:
            msg = self.in_queue.get()
            if msg == ENV_ACTIONS_READY:
                self.envs.step()
                self.inference_queue.put((ENV_OBS_READY, self.idx))

    @staticmethod
    def run_process(err_queue, *args, **kwargs):
        try:
            inner = EnvProcess(*args, **kwargs)
            inner.run()
        except Exception as e:
            err_queue.put((e, traceback.format_exc()))
            raise

class TarokkCollector:
    def __init__(self, num_workers, envs_per_worker, replay_buffer: ReplayBuffer, network, device):
        self.inference_queue = mp.Queue()
        self.err_queue = mp.Queue()
        self.env_queues = [mp.Queue() for _ in range(num_workers)]
        self.trajectory_counter = mp.Value("i", 0)

        self.replay_buffer = replay_buffer
        self.replay_buffer.share()
        self.network = network
        self.envs_per_worker = envs_per_worker
        self.device = device
        self.num_workers = num_workers

        self.inference_buffers = InferenceBuffers.new([num_workers, envs_per_worker])
        self.inference_buffers.share_memory_()
        self.inference_buffers.unlock_()

    def create_processes(self):
        self.inference_process = mp.Process(
            target=InferenceProcess.run_process,
            kwargs={
                "buffers": self.inference_buffers,
                "in_queue": self.inference_queue,
                "env_queues": self.env_queues,
                "err_queue": self.err_queue,
                "device": self.device,
                "network": self.network,
            }
        )

        self.env_processes = [
            mp.Process(
                target=EnvProcess.run_process,
                kwargs={
                    "num_envs": self.envs_per_worker,
                    "idx": idx,
                    "in_queue": self.env_queues[idx],
                    "inference_queue": self.inference_queue,
                    "inference_buffers": self.inference_buffers[idx],
                    "replay_buffer": self.replay_buffer,
                    "err_queue": self.err_queue,
                    "trajectory_counter": self.trajectory_counter
                }
            )
            for idx in range(self.num_workers)
        ]

    def stop(self):
        for queue in self.env_queues:
            queue.put(ENV_STOP)

        self.inference_queue.put((INFERENCE_STOP, None))

        for proc in self.env_processes:
            proc.join()

        self.inference_process.join()

    def handle_errors(self):
        try:
            err, trace = self.err_queue.get_nowait()
        except queue.Empty:
            return

        self.stop()
        raise RuntimeError(
            f"Worker process failed:\n{trace}"
        ) from err

    def collect(self, num_steps=None, num_trajs=None):
        if num_steps and num_trajs:
            raise ValueError("arguments num_steps and num_trajs are mutually exclusive")

        self.trajectory_counter.value = 0
        self.create_processes()
        for proc in self.env_processes:
            proc.start()
        self.inference_process.start()

        initial_progress = self.replay_buffer.write_count if num_steps else 0
        last_progress = initial_progress
        total_progress = lambda: self.replay_buffer.write_count if num_steps else self.trajectory_counter.value

        with tqdm.tqdm(range(num_steps or num_trajs), smoothing=0.0) as pbar:
            current_progress = total_progress()
            while current_progress - initial_progress < (num_steps or num_trajs):
                self.handle_errors()
                sleep(1.0)
                current_progress = total_progress()
                if current_progress > 0:
                    pbar.update(current_progress - last_progress)
                else:
                    # ensure the display is updated every second
                    pbar.display()
                last_progress = current_progress

        self.stop()
