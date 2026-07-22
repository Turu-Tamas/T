from __future__ import annotations
import collections.abc
import typing
__all__: list[str] = ['DEFAULT_CONVERGENCE_DELTA', 'DEFAULT_MAX_ITERATIONS', 'DEFAULT_MINIMUM_RATING', 'DEFAULT_SMOOTHING_FACTOR', 'DRAW', 'EloOptions', 'FIRST_PLAYER_LOSS', 'FIRST_PLAYER_WIN', 'MatchOutcome', 'MatchRecord', 'STANDARD_SCALE_FACTOR', 'compute_ratings_from_match_records', 'compute_ratings_from_matrices', 'default_elo_options']
class EloOptions:
    @property
    def convergence_delta(self) -> float:
        ...
    @convergence_delta.setter
    def convergence_delta(self, arg0: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
    @property
    def max_iterations(self) -> int:
        ...
    @max_iterations.setter
    def max_iterations(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def minimum_rating(self) -> float:
        ...
    @minimum_rating.setter
    def minimum_rating(self, arg0: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
    @property
    def scale_factor(self) -> float:
        ...
    @scale_factor.setter
    def scale_factor(self, arg0: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
    @property
    def smoothing_factor(self) -> float:
        ...
    @smoothing_factor.setter
    def smoothing_factor(self, arg0: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
class MatchOutcome:
    """
    Members:
    
      FIRST_PLAYER_WIN
    
      FIRST_PLAYER_LOSS
    
      DRAW
    """
    DRAW: typing.ClassVar[MatchOutcome]  # value = <MatchOutcome.DRAW: 2>
    FIRST_PLAYER_LOSS: typing.ClassVar[MatchOutcome]  # value = <MatchOutcome.FIRST_PLAYER_LOSS: 1>
    FIRST_PLAYER_WIN: typing.ClassVar[MatchOutcome]  # value = <MatchOutcome.FIRST_PLAYER_WIN: 0>
    __members__: typing.ClassVar[dict[str, MatchOutcome]]  # value = {'FIRST_PLAYER_WIN': <MatchOutcome.FIRST_PLAYER_WIN: 0>, 'FIRST_PLAYER_LOSS': <MatchOutcome.FIRST_PLAYER_LOSS: 1>, 'DRAW': <MatchOutcome.DRAW: 2>}
    @typing.overload
    def __eq__(self, other: MatchOutcome) -> bool:
        ...
    @typing.overload
    def __eq__(self, other: typing.SupportsInt | typing.SupportsIndex) -> bool:
        ...
    @typing.overload
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    def __int__(self) -> int:
        ...
    @typing.overload
    def __ne__(self, other: MatchOutcome) -> bool:
        ...
    @typing.overload
    def __ne__(self, other: typing.SupportsInt | typing.SupportsIndex) -> bool:
        ...
    @typing.overload
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class MatchRecord:
    first_player_name: str
    outcome: MatchOutcome
    second_player_name: str
    def __init__(self, first_player_name: str, second_player_name: str, outcome: MatchOutcome = ...) -> None:
        ...
def compute_ratings_from_match_records(match_records: collections.abc.Sequence[MatchRecord], options: EloOptions = ...) -> dict[str, float]:
    """
    Compute Elo ratings from a list of match records.
    """
def compute_ratings_from_matrices(win_matrix: collections.abc.Sequence[collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]], draw_matrix: collections.abc.Sequence[collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]] = [], options: EloOptions = ...) -> list[float]:
    """
    Compute Elo ratings from a win matrix and a draw matrix.
    """
def default_elo_options() -> EloOptions:
    """
    Return default EloOptions (see elo.h for values).
    """
DEFAULT_CONVERGENCE_DELTA: float = 1e-10
DEFAULT_MAX_ITERATIONS: int = 2000
DEFAULT_MINIMUM_RATING: float = 0.0
DEFAULT_SMOOTHING_FACTOR: float = 0.01
DRAW: MatchOutcome  # value = <MatchOutcome.DRAW: 2>
FIRST_PLAYER_LOSS: MatchOutcome  # value = <MatchOutcome.FIRST_PLAYER_LOSS: 1>
FIRST_PLAYER_WIN: MatchOutcome  # value = <MatchOutcome.FIRST_PLAYER_WIN: 0>
STANDARD_SCALE_FACTOR: float = 400.0
