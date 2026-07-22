from __future__ import annotations
import collections.abc
import pyspiel
import typing
__all__: list[str] = ['GoGame', 'GoState', 'GoStateStruct', 'load_games_from_sgf_file', 'load_games_from_sgf_string']
class GoGame(pyspiel.Game):
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
    def board_size(self) -> int:
        ...
    def handicap(self) -> int:
        ...
    def komi(self) -> float:
        ...
class GoState(pyspiel.State):
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
class GoStateStruct(pyspiel.StateStruct):
    current_player: str
    is_terminal: bool
    previous_move_a1: str
    winner: str
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: str) -> None:
        ...
    @property
    def board_grid(self) -> list[list[dict[str, str]]]:
        ...
    @board_grid.setter
    def board_grid(self, arg0: collections.abc.Sequence[collections.abc.Sequence[collections.abc.Mapping[str, str]]]) -> None:
        ...
    @property
    def board_size(self) -> int:
        ...
    @board_size.setter
    def board_size(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def komi(self) -> float:
        ...
    @komi.setter
    def komi(self, arg0: typing.SupportsFloat | typing.SupportsIndex) -> None:
        ...
    @property
    def move_number(self) -> int:
        ...
    @move_number.setter
    def move_number(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
def load_games_from_sgf_file(arg0: str) -> list[tuple[pyspiel.Game, pyspiel.State]]:
    """
    Load games from an SGF file.
    """
def load_games_from_sgf_string(arg0: str) -> list[tuple[pyspiel.Game, pyspiel.State]]:
    """
    Load games from an SGF string.
    """
