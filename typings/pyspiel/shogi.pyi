from __future__ import annotations
import typing
__all__: list[str] = ['BISHOP', 'BISHOPP', 'BLACK', 'Color', 'EMPTY', 'GOLD', 'KING', 'KNIGHT', 'KNIGHTP', 'LANCE', 'LANCEP', 'Move', 'PAWN', 'PAWNP', 'Piece', 'PieceType', 'ROOK', 'ROOKP', 'SILVER', 'SILVERP', 'ShogiBoard', 'Square', 'WHITE', 'action_to_move', 'move_to_action']
class Color:
    """
    Members:
    
      BLACK
    
      WHITE
    
      EMPTY
    """
    BLACK: typing.ClassVar[Color]  # value = <Color.BLACK: 0>
    EMPTY: typing.ClassVar[Color]  # value = <Color.EMPTY: 2>
    WHITE: typing.ClassVar[Color]  # value = <Color.WHITE: 1>
    __members__: typing.ClassVar[dict[str, Color]]  # value = {'BLACK': <Color.BLACK: 0>, 'WHITE': <Color.WHITE: 1>, 'EMPTY': <Color.EMPTY: 2>}
    @typing.overload
    def __eq__(self, other: Color) -> bool:
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
    def __ne__(self, other: Color) -> bool:
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
class Move:
    def __init__(self) -> None:
        ...
    def to_string(self) -> str:
        ...
    @property
    def drop(self) -> bool:
        ...
    @property
    def from_square(self) -> Square:
        ...
    @property
    def piece(self) -> Piece:
        ...
    @property
    def promote(self) -> bool:
        ...
    @property
    def to_square(self) -> Square:
        ...
class Piece:
    def __init__(self) -> None:
        ...
    @property
    def color(self) -> Color:
        ...
    @property
    def type(self) -> PieceType:
        ...
class PieceType:
    """
    Members:
    
      EMPTY
    
      KING
    
      LANCE
    
      KNIGHT
    
      SILVER
    
      GOLD
    
      ROOK
    
      BISHOP
    
      PAWN
    
      LANCEP
    
      KNIGHTP
    
      SILVERP
    
      ROOKP
    
      BISHOPP
    
      PAWNP
    """
    BISHOP: typing.ClassVar[PieceType]  # value = <PieceType.BISHOP: 7>
    BISHOPP: typing.ClassVar[PieceType]  # value = <PieceType.BISHOPP: 13>
    EMPTY: typing.ClassVar[PieceType]  # value = <PieceType.EMPTY: 0>
    GOLD: typing.ClassVar[PieceType]  # value = <PieceType.GOLD: 5>
    KING: typing.ClassVar[PieceType]  # value = <PieceType.KING: 1>
    KNIGHT: typing.ClassVar[PieceType]  # value = <PieceType.KNIGHT: 3>
    KNIGHTP: typing.ClassVar[PieceType]  # value = <PieceType.KNIGHTP: 10>
    LANCE: typing.ClassVar[PieceType]  # value = <PieceType.LANCE: 2>
    LANCEP: typing.ClassVar[PieceType]  # value = <PieceType.LANCEP: 9>
    PAWN: typing.ClassVar[PieceType]  # value = <PieceType.PAWN: 6>
    PAWNP: typing.ClassVar[PieceType]  # value = <PieceType.PAWNP: 12>
    ROOK: typing.ClassVar[PieceType]  # value = <PieceType.ROOK: 8>
    ROOKP: typing.ClassVar[PieceType]  # value = <PieceType.ROOKP: 14>
    SILVER: typing.ClassVar[PieceType]  # value = <PieceType.SILVER: 4>
    SILVERP: typing.ClassVar[PieceType]  # value = <PieceType.SILVERP: 11>
    __members__: typing.ClassVar[dict[str, PieceType]]  # value = {'EMPTY': <PieceType.EMPTY: 0>, 'KING': <PieceType.KING: 1>, 'LANCE': <PieceType.LANCE: 2>, 'KNIGHT': <PieceType.KNIGHT: 3>, 'SILVER': <PieceType.SILVER: 4>, 'GOLD': <PieceType.GOLD: 5>, 'ROOK': <PieceType.ROOK: 8>, 'BISHOP': <PieceType.BISHOP: 7>, 'PAWN': <PieceType.PAWN: 6>, 'LANCEP': <PieceType.LANCEP: 9>, 'KNIGHTP': <PieceType.KNIGHTP: 10>, 'SILVERP': <PieceType.SILVERP: 11>, 'ROOKP': <PieceType.ROOKP: 14>, 'BISHOPP': <PieceType.BISHOPP: 13>, 'PAWNP': <PieceType.PAWNP: 12>}
    @typing.overload
    def __eq__(self, other: PieceType) -> bool:
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
    def __ne__(self, other: PieceType) -> bool:
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
class ShogiBoard:
    def debug_string(self, arg0: bool) -> str:
        ...
    def has_legal_moves(self, arg0: bool) -> bool:
        ...
    def to_sfen(self) -> str:
        ...
class Square:
    def __init__(self) -> None:
        ...
    @property
    def x(self) -> int:
        ...
    @property
    def y(self) -> int:
        ...
def action_to_move(action: typing.SupportsInt | typing.SupportsIndex, board: ShogiBoard) -> Move:
    ...
def move_to_action(move: Move) -> int:
    ...
BISHOP: PieceType  # value = <PieceType.BISHOP: 7>
BISHOPP: PieceType  # value = <PieceType.BISHOPP: 13>
BLACK: Color  # value = <Color.BLACK: 0>
EMPTY: PieceType  # value = <PieceType.EMPTY: 0>
GOLD: PieceType  # value = <PieceType.GOLD: 5>
KING: PieceType  # value = <PieceType.KING: 1>
KNIGHT: PieceType  # value = <PieceType.KNIGHT: 3>
KNIGHTP: PieceType  # value = <PieceType.KNIGHTP: 10>
LANCE: PieceType  # value = <PieceType.LANCE: 2>
LANCEP: PieceType  # value = <PieceType.LANCEP: 9>
PAWN: PieceType  # value = <PieceType.PAWN: 6>
PAWNP: PieceType  # value = <PieceType.PAWNP: 12>
ROOK: PieceType  # value = <PieceType.ROOK: 8>
ROOKP: PieceType  # value = <PieceType.ROOKP: 14>
SILVER: PieceType  # value = <PieceType.SILVER: 4>
SILVERP: PieceType  # value = <PieceType.SILVERP: 11>
WHITE: Color  # value = <Color.WHITE: 1>
