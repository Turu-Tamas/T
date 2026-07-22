from __future__ import annotations
import typing
__all__: list[str] = ['BISHOP', 'BISHOPP', 'BLACK', 'Color', 'CrazyhouseBoard', 'EMPTY', 'KING', 'KNIGHT', 'KNIGHTP', 'Move', 'PAWN', 'Piece', 'PieceType', 'QUEEN', 'QUEENP', 'ROOK', 'ROOKP', 'Square', 'WHITE', 'action_to_move', 'move_to_action']
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
class CrazyhouseBoard:
    def debug_string(self, shredder_fen: bool = False) -> str:
        ...
    def has_legal_moves(self) -> bool:
        ...
    def to_fen(self, shredder: bool = False) -> str:
        ...
    def to_unicode_string(self) -> str:
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
    
      QUEENP
    
      ROOKP
    
      BISHOPP
    
      KNIGHTP
    """
    BISHOP: typing.ClassVar[PieceType]  # value = <PieceType.BISHOP: 4>
    BISHOPP: typing.ClassVar[PieceType]  # value = <PieceType.BISHOPP: 9>
    EMPTY: typing.ClassVar[PieceType]  # value = <PieceType.EMPTY: 0>
    KING: typing.ClassVar[PieceType]  # value = <PieceType.KING: 1>
    KNIGHT: typing.ClassVar[PieceType]  # value = <PieceType.KNIGHT: 5>
    KNIGHTP: typing.ClassVar[PieceType]  # value = <PieceType.KNIGHTP: 10>
    PAWN: typing.ClassVar[PieceType]  # value = <PieceType.PAWN: 6>
    QUEEN: typing.ClassVar[PieceType]  # value = <PieceType.QUEEN: 2>
    QUEENP: typing.ClassVar[PieceType]  # value = <PieceType.QUEENP: 7>
    ROOK: typing.ClassVar[PieceType]  # value = <PieceType.ROOK: 3>
    ROOKP: typing.ClassVar[PieceType]  # value = <PieceType.ROOKP: 8>
    __members__: typing.ClassVar[dict[str, PieceType]]  # value = {'EMPTY': <PieceType.EMPTY: 0>, 'KING': <PieceType.KING: 1>, 'QUEEN': <PieceType.QUEEN: 2>, 'ROOK': <PieceType.ROOK: 3>, 'BISHOP': <PieceType.BISHOP: 4>, 'KNIGHT': <PieceType.KNIGHT: 5>, 'PAWN': <PieceType.PAWN: 6>, 'QUEENP': <PieceType.QUEENP: 7>, 'ROOKP': <PieceType.ROOKP: 8>, 'BISHOPP': <PieceType.BISHOPP: 9>, 'KNIGHTP': <PieceType.KNIGHTP: 10>}
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
    def __init__(self) -> None:
        ...
    @property
    def x(self) -> int:
        ...
    @property
    def y(self) -> int:
        ...
def action_to_move(action: typing.SupportsInt | typing.SupportsIndex, board: CrazyhouseBoard) -> Move:
    ...
def move_to_action(move: Move, board_size: typing.SupportsInt | typing.SupportsIndex = 8) -> int:
    ...
BISHOP: PieceType  # value = <PieceType.BISHOP: 4>
BISHOPP: PieceType  # value = <PieceType.BISHOPP: 9>
BLACK: Color  # value = <Color.BLACK: 0>
EMPTY: PieceType  # value = <PieceType.EMPTY: 0>
KING: PieceType  # value = <PieceType.KING: 1>
KNIGHT: PieceType  # value = <PieceType.KNIGHT: 5>
KNIGHTP: PieceType  # value = <PieceType.KNIGHTP: 10>
PAWN: PieceType  # value = <PieceType.PAWN: 6>
QUEEN: PieceType  # value = <PieceType.QUEEN: 2>
QUEENP: PieceType  # value = <PieceType.QUEENP: 7>
ROOK: PieceType  # value = <PieceType.ROOK: 3>
ROOKP: PieceType  # value = <PieceType.ROOKP: 8>
WHITE: Color  # value = <Color.WHITE: 1>
