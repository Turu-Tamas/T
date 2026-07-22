from __future__ import annotations
import collections.abc
import typing
__all__: list[str] = ['FenchelYoungOptimizer', 'Optimizer', 'SoftCondorcetOptimizer']
class FenchelYoungOptimizer(Optimizer):
    def __init__(self, votes: collections.abc.Sequence[tuple[typing.SupportsInt | typing.SupportsIndex, collections.abc.Sequence[str]]], rating_lower_bound: typing.SupportsFloat | typing.SupportsIndex, rating_upper_bound: typing.SupportsFloat | typing.SupportsIndex, batch_size: typing.SupportsInt | typing.SupportsIndex, rng_seed: typing.SupportsInt | typing.SupportsIndex = 0, compute_norm_freq: typing.SupportsInt | typing.SupportsIndex = 1000, initial_param_noise: typing.SupportsFloat | typing.SupportsIndex = 0.0, sigma: typing.SupportsFloat | typing.SupportsIndex = 100.0, alternative_names: collections.abc.Sequence[str] = []) -> None:
        ...
    def ratings(self) -> dict[str, float]:
        ...
    def run_solver(self, iterations: typing.SupportsInt | typing.SupportsIndex, learning_rate: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
class Optimizer:
    pass
class SoftCondorcetOptimizer(Optimizer):
    def __init__(self, votes: collections.abc.Sequence[tuple[typing.SupportsInt | typing.SupportsIndex, collections.abc.Sequence[str]]], rating_lower_bound: typing.SupportsFloat | typing.SupportsIndex, rating_upper_bound: typing.SupportsFloat | typing.SupportsIndex, batch_size: typing.SupportsInt | typing.SupportsIndex, temperature: typing.SupportsFloat | typing.SupportsIndex = 1, rng_seed: typing.SupportsInt | typing.SupportsIndex = 0, compute_norm_freq: typing.SupportsInt | typing.SupportsIndex = 1000, initial_param_noise: typing.SupportsFloat | typing.SupportsIndex = 0.0, alternative_names: collections.abc.Sequence[str] = []) -> None:
        ...
    def ratings(self) -> dict[str, float]:
        ...
    def run_solver(self, iterations: typing.SupportsInt | typing.SupportsIndex, learning_rate: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
