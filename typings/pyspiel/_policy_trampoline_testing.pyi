"""
Internal test functions for calling policy member functions.
"""
from __future__ import annotations
import pyspiel
import typing
__all__: list[str] = ['call_action_probabilities', 'call_get_state_policy', 'call_get_state_policy_as_parallel_vectors', 'call_serialize']
@typing.overload
def call_action_probabilities(arg0: pyspiel.Policy, arg1: pyspiel.State) -> dict[int, float]:
    ...
@typing.overload
def call_action_probabilities(arg0: pyspiel.Policy, arg1: str) -> dict[int, float]:
    ...
@typing.overload
def call_get_state_policy(arg0: pyspiel.Policy, arg1: pyspiel.State) -> list[tuple[int, float]]:
    ...
@typing.overload
def call_get_state_policy(arg0: pyspiel.Policy, arg1: pyspiel.State, arg2: typing.SupportsInt | typing.SupportsIndex) -> list[tuple[int, float]]:
    ...
@typing.overload
def call_get_state_policy(arg0: pyspiel.Policy, arg1: str) -> list[tuple[int, float]]:
    ...
@typing.overload
def call_get_state_policy_as_parallel_vectors(arg0: pyspiel.Policy, arg1: pyspiel.State) -> tuple[list[int], list[float]]:
    ...
@typing.overload
def call_get_state_policy_as_parallel_vectors(arg0: pyspiel.Policy, arg1: str) -> tuple[list[int], list[float]]:
    ...
def call_serialize(arg0: pyspiel.Policy, arg1: typing.SupportsInt | typing.SupportsIndex, arg2: str) -> str:
    ...
