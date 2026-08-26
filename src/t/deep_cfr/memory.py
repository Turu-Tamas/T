import torch
import numpy as np
from typing import NamedTuple
import tree as np_tree
from tensordict import TensorClass
from ..models.input_struct import InputTensorClass

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
    strategy_action_probs: torch.Tensor
    

class ReservoirBuffer:
    def __init__(
        self, capacity: int, experience: AdvantageMemory | StrategyMemory
    ) -> None:
        self.capacity = capacity
        self.experience = experience
        self.add_calls = 0

    def __len__(self) -> int:
        return min(self.add_calls.item(), self.capacity.item())

    def __getitem__(self, idx):
        return np_tree.map_structure(lambda data: data[idx], self.experience)

    @classmethod
    def init(
        cls, capacity: int, experience: AdvantageMemory | StrategyMemory
    ) -> "ReservoirBuffer":
        # Initialize buffer by replicating the structure of the experience
        experience_ = np_tree.map_structure(
            lambda x: np.empty((capacity, *x.shape), dtype=x.dtype), experience
        )
        return cls(np.array(capacity), experience_)

    def append(
        self,
        experience: AdvantageMemory | StrategyMemory,
    ) -> None:
        # Determine the insertion index
        # Note: count + 1 because the current item is the (count+1)-th item
        idx = np.random.randint(0, self.add_calls + 1)

        # 2. Logic:
        # If buffer is not full, we always add at 'count'.
        # If buffer is full, we replace at 'idx' ONLY IF idx < capacity.
        is_full = self.add_calls >= self.capacity
        write_idx = idx if is_full else self.add_calls
        should_update = write_idx < self.capacity

        if should_update:
            self.experience[write_idx].update_(experience)
        self.add_calls += 1

    def sample(self, num_samples: int) -> AdvantageMemory | StrategyMemory:
        max_size = len(self)
        if max_size < num_samples:
          raise ValueError(
              f"{num_samples} elements could not be sampled from size {max_size}"
          )

        indices = np.random.choice(max_size, size=(num_samples,), replace=False)

        return np_tree.map_structure(lambda data: data[indices], self.experience)

    def shuffle(self) -> None:
        permutation = np.random.permutation(len(self))
        self.experience[:len(self)] = self.experience[:len(self)][permutation]


    def clear(self) -> None:
        self.add_calls = 0
