import torch
import numpy as np
from typing import NamedTuple
from tensordict import TensorClass
from ..models.input_struct import InputTensorClass
from torch.utils.data import Dataset


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

class AdvantageMemory(TensorClass):
    inputs: InputTensorClass
    iteration: torch.Tensor
    advantage: torch.Tensor

class StrategyMemory(TensorClass):
    inputs: InputTensorClass
    iteration: torch.Tensor
    action_probs: torch.Tensor
    

class ReservoirBuffer(Dataset):
    def __init__(
        self, capacity: int
    ) -> None:
        self.capacity = capacity
        self.experience = None
        self.add_calls = 0

    def __len__(self) -> int:
        return min(self.add_calls, self.capacity)

    def __getitem__(self, idx):
        return self.experience[idx]

    def _maybe_initialize_buffer(self, experience):
        if self.experience is None:
            self.experience = experience.apply(
                lambda leaf: torch.empty([self.capacity, *leaf.shape], dtype=leaf.dtype),
                batch_size=[self.capacity])

    def extend(self, experience: AdvantageMemory | StrategyMemory):
        assert experience.ndim == 1
        self._maybe_initialize_buffer(experience[0])
        experience = experience.cpu()

        to_copy = min(self.capacity - len(self), experience.size(0))
        if to_copy > 0:
            self.experience[len(self):len(self) + to_copy] = experience[:to_copy]
            self.add_calls += to_copy

            experience = experience[to_copy:]
            if experience.size(0) == 0:
                return

        probs = self.add_calls + 1 + torch.arange(experience.size(0))
        probs = self.capacity / probs
        add_mask = torch.rand(experience.batch_size) < probs
        to_add = experience[add_mask]
        indices = torch.randint(0, self.capacity, to_add.shape)
        indices, sort = torch.sort(indices)
        to_add = to_add[sort]
        if indices.size(0) == 0:
            return

        keep = torch.empty([indices.size(0)], dtype=torch.bool)
        keep[-1] = True
        keep[:-1] = indices[:-1] != indices[1:]
        indices = indices[keep]
        to_add = to_add[keep]

        self.add_calls += experience.size(0)
        self.experience[indices].update_(to_add)

    def append(
        self,
        experience: AdvantageMemory | StrategyMemory,
    ) -> None:
        assert experience.batch_dims == 0
        self._maybe_initialize_buffer(experience)

        if self.add_calls < self.capacity:
            write_idx = self.add_calls
        else:
            idx = np.random.randint(0, self.add_calls + 1)
            if idx >= self.capacity:
                self.add_calls += 1
                return
            write_idx = idx

        self.experience[write_idx].update_(experience.cpu())
        self.add_calls += 1

    def sample(self, num_samples: int) -> AdvantageMemory | StrategyMemory:
        max_size = len(self)
        if max_size < num_samples:
          raise ValueError(
              f"{num_samples} elements could not be sampled from size {max_size}"
          )

        indices = np.random.choice(max_size, size=(num_samples,), replace=False)
        return self.experience[indices]

    def shuffle(self) -> None:
        permutation = np.random.permutation(len(self))
        self.experience[:len(self)] = self.experience[:len(self)][permutation]

    def clear(self) -> None:
        self.add_calls = 0
