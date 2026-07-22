from __future__ import annotations
import collections.abc
import pyspiel
import typing
__all__: list[str] = ['CROSS', 'CellState', 'EMPTY', 'NOUGHT', 'NUM_CELLS', 'NUM_COLS', 'NUM_ROWS', 'TicTacToeActionStruct', 'TicTacToeGame', 'TicTacToeObservationStruct', 'TicTacToeState', 'TicTacToeStateStruct', 'cellstate_to_string', 'player_to_cellstate']
class CellState:
    """
    Members:
    
      EMPTY
    
      NOUGHT
    
      CROSS
    """
    CROSS: typing.ClassVar[CellState]  # value = <CellState.CROSS: 2>
    EMPTY: typing.ClassVar[CellState]  # value = <CellState.EMPTY: 0>
    NOUGHT: typing.ClassVar[CellState]  # value = <CellState.NOUGHT: 1>
    __members__: typing.ClassVar[dict[str, CellState]]  # value = {'EMPTY': <CellState.EMPTY: 0>, 'NOUGHT': <CellState.NOUGHT: 1>, 'CROSS': <CellState.CROSS: 2>}
    @typing.overload
    def __eq__(self, other: CellState) -> bool:
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
    def __ne__(self, other: CellState) -> bool:
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
class TicTacToeActionStruct(pyspiel.ActionStruct):
    @staticmethod
    @typing.overload
    def __init__(*args, **kwargs) -> None:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: str) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @property
    def col(self) -> int:
        ...
    @col.setter
    def col(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def row(self) -> int:
        ...
    @row.setter
    def row(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
class TicTacToeGame(pyspiel.Game):
    ActionStruct = TicTacToeActionStruct
    ObservationStruct = TicTacToeObservationStruct
    StateStruct = TicTacToeStateStruct
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
class TicTacToeObservationStruct(pyspiel.ObservationStruct):
    current_player: str
    @staticmethod
    @typing.overload
    def __init__(*args, **kwargs) -> None:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: str) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @property
    def board(self) -> list[str]:
        ...
    @board.setter
    def board(self, arg0: collections.abc.Sequence[str]) -> None:
        ...
class TicTacToeState(pyspiel.State):
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
    def board(self) -> list[CellState]:
        """
        Returns the board as a list of CellStates.
        """
    def board_at(self, row: typing.SupportsInt | typing.SupportsIndex, col: typing.SupportsInt | typing.SupportsIndex) -> CellState:
        """
        Returns the CellState at row, col coordinates.
        """
class TicTacToeStateStruct(pyspiel.StateStruct):
    current_player: str
    @staticmethod
    @typing.overload
    def __init__(*args, **kwargs) -> None:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: str) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @property
    def board(self) -> list[str]:
        ...
    @board.setter
    def board(self, arg0: collections.abc.Sequence[str]) -> None:
        ...
def cellstate_to_string(arg0: ...) -> str:
    ...
def player_to_cellstate(arg0: typing.SupportsInt | typing.SupportsIndex) -> ...:
    ...
CROSS: CellState  # value = <CellState.CROSS: 2>
EMPTY: CellState  # value = <CellState.EMPTY: 0>
NOUGHT: CellState  # value = <CellState.NOUGHT: 1>
NUM_CELLS: int = 9
NUM_COLS: int = 3
NUM_ROWS: int = 3
