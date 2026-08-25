import torch
import numpy as np
from typing import NamedTuple
import tree as np_tree

def set_seed(seed):
  np.random.seed(seed)
  torch.manual_seed(seed)
  if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class AdvantageMemory(NamedTuple):
  """Advantage network memory buffer."""

  info_state: np.ndarray
  iteration: np.ndarray
  advantage: np.ndarray


class StrategyMemory(NamedTuple):
  """Stratefy network memory buffer."""

  info_state: np.ndarray
  iteration: np.ndarray
  strategy_action_probs: np.ndarray


class ReservoirBuffer:
  """Allows uniform sampling over a stream of data.

  See https://en.wikipedia.org/wiki/Reservoir_sampling for more details.
  """

  def __init__(
      self, capacity: np.ndarray, experience: AdvantageMemory | StrategyMemory
  ) -> None:
    self.capacity = capacity
    self.experience = experience
    self.add_calls = np.array(0)

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
    """Potentially adds `experience` to the reservoir buffer.

    Args:
      experience: data to be added to the reservoir buffer.

    Returns:
      None as the method updated the buffer in-place
    """
    # Determine the insertion index
    # Note: count + 1 because the current item is the (count+1)-th item
    idx = np.random.randint(0, self.add_calls + 1)

    # 2. Logic:
    # If buffer is not full, we always add at 'count'.
    # If buffer is full, we replace at 'idx' ONLY IF idx < capacity.
    is_full = self.add_calls >= self.capacity
    write_idx = np.where(is_full, idx, self.add_calls)
    should_update = write_idx < self.capacity

    def _inplace(arr, idx, val):
      arr[idx] = val

    if should_update:
      np_tree.map_structure(
          lambda buf_leaf, exp_leaf: _inplace(buf_leaf, write_idx, exp_leaf),
          self.experience,
          experience,
      )
    self.add_calls += 1

  def sample(self, num_samples: int) -> AdvantageMemory | StrategyMemory:
    """Returns `num_samples` uniformly sampled from the buffer.

    Args:
      num_samples: `int`, number of samples to draw.

    Returns:
      An iterable over `num_samples` random elements of the buffer.
    Raises:
      ValueError: If there are less than `num_samples` elements in the buffer
    """
    max_size = len(self)
    if max_size < num_samples:
      raise ValueError(
          f"{num_samples} elements could not be sampled from size {max_size}"
      )

    indices = np.random.choice(max_size, size=(num_samples,), replace=False)

    return np_tree.map_structure(lambda data: data[indices], self.experience)

  def shuffle(self) -> None:
    """Shuffling the reservoir buffer along the batch axis."""
    np_tree.map_structure(
        lambda x: np.random.shuffle(x[: len(self)]), self.experience
    )

  def clear(self) -> None:
    """Clears the reservoir buffer."""
    self.add_calls = np.array(0)