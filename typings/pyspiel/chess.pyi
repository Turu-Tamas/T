from __future__ import annotations
import typing
__all__: list[str] = ['BISHOP', 'BLACK', 'ChessBoard', 'Color', 'EMPTY', 'KING', 'KNIGHT', 'Move', 'PAWN', 'Piece', 'PieceType', 'QUEEN', 'ROOK', 'Square', 'WHITE', 'action_to_move', 'move_to_action']
class ChessBoard:
    def at(self, arg0: Square) -> Piece:
        ...
    def debug_string(self, shredder_fen: bool = False) -> str:
        ...
    def has_legal_moves(self) -> bool:
        ...
    def to_fen(self, shredder: bool = False) -> str:
        ...
    def to_unicode_string(self) -> str:
        ...
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
    def is_castling(self) -> bool:
        ...
    def to_lan(self, chess960: bool = False, board: ... = None) -> str:
        ...
    def to_san(self, arg0: ...) -> str:
        ...
    def to_string(self) -> str:
        ...
    @property
    def from_square(self) -> Square:
        ...
    @property
    def piece(self) -> Piece:
        ...
    @property
    def promotion_type(self) -> PieceType:
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
    
      QUEEN
    
      ROOK
    
      BISHOP
    
      KNIGHT
    
      PAWN
    """
    BISHOP: typing.ClassVar[PieceType]  # value = <PieceType.BISHOP: 4>
    EMPTY: typing.ClassVar[PieceType]  # value = <PieceType.EMPTY: 0>
    KING: typing.ClassVar[PieceType]  # value = <PieceType.KING: 1>
    KNIGHT: typing.ClassVar[PieceType]  # value = <PieceType.KNIGHT: 5>
    PAWN: typing.ClassVar[PieceType]  # value = <PieceType.PAWN: 6>
    QUEEN: typing.ClassVar[PieceType]  # value = <PieceType.QUEEN: 2>
    ROOK: typing.ClassVar[PieceType]  # value = <PieceType.ROOK: 3>
    __members__: typing.ClassVar[dict[str, PieceType]]  # value = {'EMPTY': <PieceType.EMPTY: 0>, 'KING': <PieceType.KING: 1>, 'QUEEN': <PieceType.QUEEN: 2>, 'ROOK': <PieceType.ROOK: 3>, 'BISHOP': <PieceType.BISHOP: 4>, 'KNIGHT': <PieceType.KNIGHT: 5>, 'PAWN': <PieceType.PAWN: 6>}
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
class Square:
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: typing.SupportsInt | typing.SupportsIndex, arg1: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def x(self) -> int:
        ...
    @property
    def y(self) -> int:
        ...
def action_to_move(action: typing.SupportsInt | typing.SupportsIndex, board: ChessBoard) -> Move:
    ...
def move_to_action(move: Move, board_size: typing.SupportsInt | typing.SupportsIndex = 8) -> int:
    ...
BISHOP: PieceType  # value = <PieceType.BISHOP: 4>
BLACK: Color  # value = <Color.BLACK: 0>
EMPTY: PieceType  # value = <PieceType.EMPTY: 0>
KING: PieceType  # value = <PieceType.KING: 1>
KNIGHT: PieceType  # value = <PieceType.KNIGHT: 5>
PAWN: PieceType  # value = <PieceType.PAWN: 6>
QUEEN: PieceType  # value = <PieceType.QUEEN: 2>
ROOK: PieceType  # value = <PieceType.ROOK: 3>
WHITE: Color  # value = <Color.WHITE: 1>
