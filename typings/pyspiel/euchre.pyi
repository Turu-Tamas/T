from __future__ import annotations
import pyspiel
import typing
__all__: list[str] = ['BIDDING', 'CLUBS', 'CLUBS_TRUMP_ACTION', 'DEAL', 'DEALER_SELECTION', 'DIAMONDS', 'DIAMONDS_TRUMP_ACTION', 'DISCARD', 'EuchreState', 'FULL_HAND_SIZE', 'GAME_OVER', 'GO_ALONE', 'GO_ALONE_ACTION', 'HEARTS', 'HEARTS_TRUMP_ACTION', 'INVALID_SUIT', 'JACK_RANK', 'MAX_BIDS', 'NUM_CARDS', 'NUM_CARDS_PER_SUIT', 'NUM_SUITS', 'NUM_TRICKS', 'PASS_ACTION', 'PLAY', 'PLAY_WITH_PARTNER_ACTION', 'Phase', 'SPADES', 'SPADES_TRUMP_ACTION', 'Suit', 'card_rank', 'card_string', 'card_suit']
class EuchreState(pyspiel.State):
    class Trick:
        def cards(self) -> list[int]:
            ...
        def leader(self) -> int:
            ...
        def led_suit(self) -> Suit:
            ...
        def trump_played(self) -> bool:
            ...
        def trump_suit(self) -> Suit:
            ...
        def winner(self) -> int:
            ...
        def winning_card(self) -> int:
            ...
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
    def active_players(self) -> list[bool]:
        ...
    def card_holder(self) -> typing.Annotated[list[int | None], "FixedSize(24)"]:
        ...
    def current_phase(self) -> Phase:
        ...
    def current_trick(self) -> ...:
        ...
    def current_trick_index(self) -> int:
        ...
    def dealer(self) -> int:
        ...
    def declarer(self) -> int:
        ...
    def declarer_go_alone(self) -> bool | None:
        ...
    def declarer_partner(self) -> int:
        ...
    def discard(self) -> int:
        ...
    def first_defender(self) -> int:
        ...
    def left_bower(self) -> int:
        ...
    def lone_defender(self) -> int:
        ...
    def num_cards_dealt(self) -> int:
        ...
    def num_cards_played(self) -> int:
        ...
    def num_passes(self) -> int:
        ...
    def right_bower(self) -> int:
        ...
    def second_defender(self) -> int:
        ...
    def tricks(self) -> list[...]:
        ...
    def trump_suit(self) -> int:
        ...
    def upcard(self) -> int:
        ...
class Phase:
    """
    Members:
    
      DEALER_SELECTION
    
      DEAL
    
      BIDDING
    
      DISCARD
    
      GO_ALONE
    
      PLAY
    
      GAME_OVER
    """
    BIDDING: typing.ClassVar[Phase]  # value = <Phase.BIDDING: 2>
    DEAL: typing.ClassVar[Phase]  # value = <Phase.DEAL: 1>
    DEALER_SELECTION: typing.ClassVar[Phase]  # value = <Phase.DEALER_SELECTION: 0>
    DISCARD: typing.ClassVar[Phase]  # value = <Phase.DISCARD: 3>
    GAME_OVER: typing.ClassVar[Phase]  # value = <Phase.GAME_OVER: 6>
    GO_ALONE: typing.ClassVar[Phase]  # value = <Phase.GO_ALONE: 4>
    PLAY: typing.ClassVar[Phase]  # value = <Phase.PLAY: 5>
    __members__: typing.ClassVar[dict[str, Phase]]  # value = {'DEALER_SELECTION': <Phase.DEALER_SELECTION: 0>, 'DEAL': <Phase.DEAL: 1>, 'BIDDING': <Phase.BIDDING: 2>, 'DISCARD': <Phase.DISCARD: 3>, 'GO_ALONE': <Phase.GO_ALONE: 4>, 'PLAY': <Phase.PLAY: 5>, 'GAME_OVER': <Phase.GAME_OVER: 6>}
    @typing.overload
    def __eq__(self, other: Phase) -> bool:
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
    def __ne__(self, other: Phase) -> bool:
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
class Suit:
    """
    Members:
    
      INVALID_SUIT
    
      CLUBS
    
      DIAMONDS
    
      HEARTS
    
      SPADES
    """
    CLUBS: typing.ClassVar[Suit]  # value = <Suit.CLUBS: 0>
    DIAMONDS: typing.ClassVar[Suit]  # value = <Suit.DIAMONDS: 1>
    HEARTS: typing.ClassVar[Suit]  # value = <Suit.HEARTS: 2>
    INVALID_SUIT: typing.ClassVar[Suit]  # value = <Suit.INVALID_SUIT: -1>
    SPADES: typing.ClassVar[Suit]  # value = <Suit.SPADES: 3>
    __members__: typing.ClassVar[dict[str, Suit]]  # value = {'INVALID_SUIT': <Suit.INVALID_SUIT: -1>, 'CLUBS': <Suit.CLUBS: 0>, 'DIAMONDS': <Suit.DIAMONDS: 1>, 'HEARTS': <Suit.HEARTS: 2>, 'SPADES': <Suit.SPADES: 3>}
    @typing.overload
    def __eq__(self, other: Suit) -> bool:
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
    def __ne__(self, other: Suit) -> bool:
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
@typing.overload
def card_rank(arg0: typing.SupportsInt | typing.SupportsIndex) -> int:
    ...
@typing.overload
def card_rank(arg0: typing.SupportsInt | typing.SupportsIndex, arg1: ...) -> int:
    ...
def card_string(arg0: typing.SupportsInt | typing.SupportsIndex) -> str:
    ...
@typing.overload
def card_suit(arg0: typing.SupportsInt | typing.SupportsIndex) -> ...:
    ...
@typing.overload
def card_suit(arg0: typing.SupportsInt | typing.SupportsIndex, arg1: ...) -> ...:
    ...
BIDDING: Phase  # value = <Phase.BIDDING: 2>
CLUBS: Suit  # value = <Suit.CLUBS: 0>
CLUBS_TRUMP_ACTION: int = 25
DEAL: Phase  # value = <Phase.DEAL: 1>
DEALER_SELECTION: Phase  # value = <Phase.DEALER_SELECTION: 0>
DIAMONDS: Suit  # value = <Suit.DIAMONDS: 1>
DIAMONDS_TRUMP_ACTION: int = 26
DISCARD: Phase  # value = <Phase.DISCARD: 3>
FULL_HAND_SIZE: int = 5
GAME_OVER: Phase  # value = <Phase.GAME_OVER: 6>
GO_ALONE: Phase  # value = <Phase.GO_ALONE: 4>
GO_ALONE_ACTION: int = 29
HEARTS: Suit  # value = <Suit.HEARTS: 2>
HEARTS_TRUMP_ACTION: int = 27
INVALID_SUIT: Suit  # value = <Suit.INVALID_SUIT: -1>
JACK_RANK: int = 2
MAX_BIDS: int = 8
NUM_CARDS: int = 24
NUM_CARDS_PER_SUIT: int = 6
NUM_SUITS: int = 4
NUM_TRICKS: int = 5
PASS_ACTION: int = 24
PLAY: Phase  # value = <Phase.PLAY: 5>
PLAY_WITH_PARTNER_ACTION: int = 30
SPADES: Suit  # value = <Suit.SPADES: 3>
SPADES_TRUMP_ACTION: int = 28
