from __future__ import annotations
import collections.abc
import pyspiel
import typing
__all__: list[str] = ['ConnectFourActionStruct', 'ConnectFourGame', 'ConnectFourGameParams', 'ConnectFourObservationStruct', 'ConnectFourState', 'ConnectFourStateStruct']
class ConnectFourActionStruct(pyspiel.ActionStruct):
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
    def column(self) -> int:
        ...
    @column.setter
    def column(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
class ConnectFourGame(pyspiel.Game):
    ActionStruct = ConnectFourActionStruct
    GameParametersStruct = ConnectFourGameParams
    ObservationStruct = ConnectFourObservationStruct
    StateStruct = ConnectFourStateStruct
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
class ConnectFourGameParams(pyspiel.GameParametersStruct):
    egocentric_obs_tensor: bool
    game_name: str
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
    def columns(self) -> int:
        ...
    @columns.setter
    def columns(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def rows(self) -> int:
        ...
    @rows.setter
    def rows(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def x_in_row(self) -> int:
        ...
    @x_in_row.setter
    def x_in_row(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
class ConnectFourObservationStruct(pyspiel.ObservationStruct):
    current_player: str
    is_terminal: bool
    winner: str
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
    def board(self) -> list[list[str]]:
        ...
    @board.setter
    def board(self, arg0: collections.abc.Sequence[collections.abc.Sequence[str]]) -> None:
        ...
class ConnectFourState(pyspiel.State):
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
class ConnectFourStateStruct(pyspiel.StateStruct):
    current_player: str
    is_terminal: bool
    winner: str
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
    def board(self) -> list[list[str]]:
        ...
    @board.setter
    def board(self, arg0: collections.abc.Sequence[collections.abc.Sequence[str]]) -> None:
        ...
