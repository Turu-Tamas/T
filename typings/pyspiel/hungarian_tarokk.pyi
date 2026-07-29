from __future__ import annotations
import collections.abc
import pyspiel
import typing
__all__: list[str] = ['AnnouncementActions', 'BiddingActions', 'Card', 'HungarianTarokkBid', 'HungarianTarokkBonus', 'HungarianTarokkBonusAnnouncement', 'HungarianTarokkCalledCard', 'HungarianTarokkGame', 'HungarianTarokkObservationStruct', 'HungarianTarokkPhase', 'HungarianTarokkSide', 'HungarianTarokkState', 'NUM_CARDS', 'NUM_DISTINCT_ACTIONS', 'NUM_TAROKKS', 'Suit', 'SuitRank', 'TalonActions']
class AnnouncementActions:
    ANNOUNCE_BONUS_BASE: typing.ClassVar[int] = 114
    CALL_ACTION_BASE: typing.ClassVar[int] = 92
    DECLARE_EIGHT: typing.ClassVar[int] = 148
    DECLARE_NINE: typing.ClassVar[int] = 149
    GAME_KONTRA_ITEM: typing.ClassVar[int] = 0
    KONTRA_ACTION_BASE: typing.ClassVar[int] = 120
    MAX_KONTRA: typing.ClassVar[int] = 4
    NUM_KONTRA_ACTIONS: typing.ClassVar[int] = 28
    NUM_KONTRA_ITEMS: typing.ClassVar[int] = 13
    NUM_KONTRA_TARGETS: typing.ClassVar[int] = 7
    PASS: typing.ClassVar[int] = 150
    @staticmethod
    def announce_bonus_action(bonus: HungarianTarokkBonus) -> int:
        ...
    @staticmethod
    def call_action_for_tarokk(tarokk: Card) -> int:
        ...
    @staticmethod
    def kontra_claim_action(bonus: HungarianTarokkBonus, level: typing.SupportsInt | typing.SupportsIndex) -> int:
        ...
    @staticmethod
    def kontra_game_action(level: typing.SupportsInt | typing.SupportsIndex) -> int:
        ...
class BiddingActions:
    ACTION_BASE: typing.ClassVar[int] = 42
    BID_ONE: typing.ClassVar[int] = 45
    BID_SOLO: typing.ClassVar[int] = 46
    BID_THREE: typing.ClassVar[int] = 43
    BID_TWO: typing.ClassVar[int] = 44
    HOLD: typing.ClassVar[int] = 47
    NUM_ACTIONS: typing.ClassVar[int] = 6
    PASS: typing.ClassVar[int] = 42
    @staticmethod
    def bid_to_action(bid: HungarianTarokkBid) -> int:
        ...
class Card:
    @staticmethod
    def new_suit(suit: Suit, rank: SuitRank) -> Card:
        ...
    @staticmethod
    def new_tarokk(numeral: typing.SupportsInt | typing.SupportsIndex) -> Card:
        ...
    def __eq__(self, arg0: Card) -> bool:
        ...
    def __hash__(self) -> int:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, index: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __str__(self) -> str:
        ...
    def is_tarokk(self) -> bool:
        ...
    def points(self) -> int:
        ...
    def suit(self) -> int:
        ...
    @property
    def index(self) -> int:
        ...
    @index.setter
    def index(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
class HungarianTarokkBid:
    """
    Members:
    
      THREE
    
      TWO
    
      ONE
    
      SOLO
    """
    ONE: typing.ClassVar[HungarianTarokkBid]  # value = <HungarianTarokkBid.ONE: 2>
    SOLO: typing.ClassVar[HungarianTarokkBid]  # value = <HungarianTarokkBid.SOLO: 3>
    THREE: typing.ClassVar[HungarianTarokkBid]  # value = <HungarianTarokkBid.THREE: 0>
    TWO: typing.ClassVar[HungarianTarokkBid]  # value = <HungarianTarokkBid.TWO: 1>
    __members__: typing.ClassVar[dict[str, HungarianTarokkBid]]  # value = {'THREE': <HungarianTarokkBid.THREE: 0>, 'TWO': <HungarianTarokkBid.TWO: 1>, 'ONE': <HungarianTarokkBid.ONE: 2>, 'SOLO': <HungarianTarokkBid.SOLO: 3>}
    @typing.overload
    def __eq__(self, other: HungarianTarokkBid) -> bool:
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
    def __ne__(self, other: HungarianTarokkBid) -> bool:
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
class HungarianTarokkBonus:
    """
    Members:
    
      TRULL
    
      FOUR_KINGS
    
      PAGAT_ULTI
    
      XXI_CATCH
    
      DOUBLE_GAME
    
      VOLAT
    """
    DOUBLE_GAME: typing.ClassVar[HungarianTarokkBonus]  # value = <HungarianTarokkBonus.DOUBLE_GAME: 4>
    FOUR_KINGS: typing.ClassVar[HungarianTarokkBonus]  # value = <HungarianTarokkBonus.FOUR_KINGS: 1>
    PAGAT_ULTI: typing.ClassVar[HungarianTarokkBonus]  # value = <HungarianTarokkBonus.PAGAT_ULTI: 2>
    TRULL: typing.ClassVar[HungarianTarokkBonus]  # value = <HungarianTarokkBonus.TRULL: 0>
    VOLAT: typing.ClassVar[HungarianTarokkBonus]  # value = <HungarianTarokkBonus.VOLAT: 5>
    XXI_CATCH: typing.ClassVar[HungarianTarokkBonus]  # value = <HungarianTarokkBonus.XXI_CATCH: 3>
    __members__: typing.ClassVar[dict[str, HungarianTarokkBonus]]  # value = {'TRULL': <HungarianTarokkBonus.TRULL: 0>, 'FOUR_KINGS': <HungarianTarokkBonus.FOUR_KINGS: 1>, 'PAGAT_ULTI': <HungarianTarokkBonus.PAGAT_ULTI: 2>, 'XXI_CATCH': <HungarianTarokkBonus.XXI_CATCH: 3>, 'DOUBLE_GAME': <HungarianTarokkBonus.DOUBLE_GAME: 4>, 'VOLAT': <HungarianTarokkBonus.VOLAT: 5>}
    @typing.overload
    def __eq__(self, other: HungarianTarokkBonus) -> bool:
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
    def __ne__(self, other: HungarianTarokkBonus) -> bool:
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
class HungarianTarokkBonusAnnouncement:
    def __init__(self) -> None:
        ...
    @property
    def bonus(self) -> int:
        ...
    @bonus.setter
    def bonus(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def kontra_level(self) -> int:
        ...
    @kontra_level.setter
    def kontra_level(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def side(self) -> int:
        ...
    @side.setter
    def side(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
class HungarianTarokkCalledCard:
    """
    Members:
    
      NONE
    
      XIX
    
      XVIII
    
      XX
    """
    NONE: typing.ClassVar[HungarianTarokkCalledCard]  # value = <HungarianTarokkCalledCard.NONE: 0>
    XIX: typing.ClassVar[HungarianTarokkCalledCard]  # value = <HungarianTarokkCalledCard.XIX: 1>
    XVIII: typing.ClassVar[HungarianTarokkCalledCard]  # value = <HungarianTarokkCalledCard.XVIII: 2>
    XX: typing.ClassVar[HungarianTarokkCalledCard]  # value = <HungarianTarokkCalledCard.XX: 3>
    __members__: typing.ClassVar[dict[str, HungarianTarokkCalledCard]]  # value = {'NONE': <HungarianTarokkCalledCard.NONE: 0>, 'XIX': <HungarianTarokkCalledCard.XIX: 1>, 'XVIII': <HungarianTarokkCalledCard.XVIII: 2>, 'XX': <HungarianTarokkCalledCard.XX: 3>}
    @typing.overload
    def __eq__(self, other: HungarianTarokkCalledCard) -> bool:
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
    def __ne__(self, other: HungarianTarokkCalledCard) -> bool:
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
class HungarianTarokkGame(pyspiel.Game):
    ObservationStruct = HungarianTarokkObservationStruct
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
class HungarianTarokkObservationStruct(pyspiel.ObservationStruct):
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
    def bid(self) -> int:
        ...
    @bid.setter
    def bid(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def bid_slots(self) -> list[int]:
        ...
    @bid_slots.setter
    def bid_slots(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def bonus_announcements(self) -> list[HungarianTarokkBonusAnnouncement]:
        ...
    @bonus_announcements.setter
    def bonus_announcements(self, arg0: collections.abc.Sequence[HungarianTarokkBonusAnnouncement]) -> None:
        ...
    @property
    def called_tarokk(self) -> int:
        ...
    @called_tarokk.setter
    def called_tarokk(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def current_player(self) -> int:
        ...
    @current_player.setter
    def current_player(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def current_trick(self) -> list[int]:
        ...
    @current_trick.setter
    def current_trick(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def current_trick_leader(self) -> int:
        ...
    @current_trick_leader.setter
    def current_trick_leader(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def declared_tarokks(self) -> list[int]:
        ...
    @declared_tarokks.setter
    def declared_tarokks(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def declarer(self) -> int:
        ...
    @declarer.setter
    def declarer(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def declarer_shown_tarokks(self) -> list[int]:
        ...
    @declarer_shown_tarokks.setter
    def declarer_shown_tarokks(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def discard_tarokk_counts(self) -> list[int]:
        ...
    @discard_tarokk_counts.setter
    def discard_tarokk_counts(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def game_kontra(self) -> int:
        ...
    @game_kontra.setter
    def game_kontra(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def hand(self) -> list[int]:
        ...
    @hand.setter
    def hand(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def hivatalbol_kontra(self) -> int:
        ...
    @hivatalbol_kontra.setter
    def hivatalbol_kontra(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def last_trick(self) -> list[int]:
        ...
    @last_trick.setter
    def last_trick(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
    @property
    def obligatory_call(self) -> int:
        ...
    @obligatory_call.setter
    def obligatory_call(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def observing_player(self) -> int:
        ...
    @observing_player.setter
    def observing_player(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def phase(self) -> int:
        ...
    @phase.setter
    def phase(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> None:
        ...
    @property
    def sides(self) -> list[int]:
        ...
    @sides.setter
    def sides(self, arg0: collections.abc.Sequence[typing.SupportsInt | typing.SupportsIndex]) -> None:
        ...
class HungarianTarokkPhase:
    """
    Members:
    
      DEALING
    
      BIDDING
    
      TALON_EXCHANGE
    
      ANNOUNCEMENTS
    
      PLAYING
    
      FINISHED
    """
    ANNOUNCEMENTS: typing.ClassVar[HungarianTarokkPhase]  # value = <HungarianTarokkPhase.ANNOUNCEMENTS: 3>
    BIDDING: typing.ClassVar[HungarianTarokkPhase]  # value = <HungarianTarokkPhase.BIDDING: 1>
    DEALING: typing.ClassVar[HungarianTarokkPhase]  # value = <HungarianTarokkPhase.DEALING: 0>
    FINISHED: typing.ClassVar[HungarianTarokkPhase]  # value = <HungarianTarokkPhase.FINISHED: 5>
    PLAYING: typing.ClassVar[HungarianTarokkPhase]  # value = <HungarianTarokkPhase.PLAYING: 4>
    TALON_EXCHANGE: typing.ClassVar[HungarianTarokkPhase]  # value = <HungarianTarokkPhase.TALON_EXCHANGE: 2>
    __members__: typing.ClassVar[dict[str, HungarianTarokkPhase]]  # value = {'DEALING': <HungarianTarokkPhase.DEALING: 0>, 'BIDDING': <HungarianTarokkPhase.BIDDING: 1>, 'TALON_EXCHANGE': <HungarianTarokkPhase.TALON_EXCHANGE: 2>, 'ANNOUNCEMENTS': <HungarianTarokkPhase.ANNOUNCEMENTS: 3>, 'PLAYING': <HungarianTarokkPhase.PLAYING: 4>, 'FINISHED': <HungarianTarokkPhase.FINISHED: 5>}
    @typing.overload
    def __eq__(self, other: HungarianTarokkPhase) -> bool:
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
    def __ne__(self, other: HungarianTarokkPhase) -> bool:
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
class HungarianTarokkSide:
    """
    Members:
    
      DECLARERS
    
      DEFENDERS
    """
    DECLARERS: typing.ClassVar[HungarianTarokkSide]  # value = <HungarianTarokkSide.DECLARERS: 0>
    DEFENDERS: typing.ClassVar[HungarianTarokkSide]  # value = <HungarianTarokkSide.DEFENDERS: 1>
    __members__: typing.ClassVar[dict[str, HungarianTarokkSide]]  # value = {'DECLARERS': <HungarianTarokkSide.DECLARERS: 0>, 'DEFENDERS': <HungarianTarokkSide.DEFENDERS: 1>}
    @typing.overload
    def __eq__(self, other: HungarianTarokkSide) -> bool:
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
    def __ne__(self, other: HungarianTarokkSide) -> bool:
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
class HungarianTarokkState(pyspiel.State):
    def __getstate__(self) -> str:
        ...
    def __setstate__(self, arg0: str) -> None:
        ...
    def current_phase(self) -> HungarianTarokkPhase:
        ...
    def declarer(self) -> int:
        ...
    def is_annulled(self) -> bool:
        ...
    def partner(self) -> int:
        ...
    def player_cards(self, player: typing.SupportsInt | typing.SupportsIndex) -> list[Card]:
        ...
    def talon(self) -> list[Card]:
        ...
    def winning_bid(self) -> HungarianTarokkBid:
        ...
class Suit:
    """
    Members:
    
      HEARTS
    
      CLUBS
    
      SPADES
    
      DIAMONDS
    """
    CLUBS: typing.ClassVar[Suit]  # value = <Suit.CLUBS: 2>
    DIAMONDS: typing.ClassVar[Suit]  # value = <Suit.DIAMONDS: 1>
    HEARTS: typing.ClassVar[Suit]  # value = <Suit.HEARTS: 0>
    SPADES: typing.ClassVar[Suit]  # value = <Suit.SPADES: 3>
    __members__: typing.ClassVar[dict[str, Suit]]  # value = {'HEARTS': <Suit.HEARTS: 0>, 'CLUBS': <Suit.CLUBS: 2>, 'SPADES': <Suit.SPADES: 3>, 'DIAMONDS': <Suit.DIAMONDS: 1>}
    @typing.overload
    def __eq__(self, other: Suit) -> bool:
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
    def __ne__(self, other: Suit) -> bool:
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
class SuitRank:
    """
    Members:
    
      ACE
    
      JACK
    
      RIDER
    
      QUEEN
    
      KING
    """
    ACE: typing.ClassVar[SuitRank]  # value = <SuitRank.ACE: 0>
    JACK: typing.ClassVar[SuitRank]  # value = <SuitRank.JACK: 1>
    KING: typing.ClassVar[SuitRank]  # value = <SuitRank.KING: 4>
    QUEEN: typing.ClassVar[SuitRank]  # value = <SuitRank.QUEEN: 3>
    RIDER: typing.ClassVar[SuitRank]  # value = <SuitRank.RIDER: 2>
    __members__: typing.ClassVar[dict[str, SuitRank]]  # value = {'ACE': <SuitRank.ACE: 0>, 'JACK': <SuitRank.JACK: 1>, 'RIDER': <SuitRank.RIDER: 2>, 'QUEEN': <SuitRank.QUEEN: 3>, 'KING': <SuitRank.KING: 4>}
    @typing.overload
    def __eq__(self, other: SuitRank) -> bool:
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
    def __ne__(self, other: SuitRank) -> bool:
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
class TalonActions:
    ANNUL: typing.ClassVar[int] = 90
    DECLINE_ANNUL: typing.ClassVar[int] = 91
    DISCARD_ACTION_BASE: typing.ClassVar[int] = 48
    @staticmethod
    def discard_action_for_card(card: Card) -> int:
        ...
NUM_CARDS: int = 42
NUM_DISTINCT_ACTIONS: int = 151
NUM_TAROKKS: int = 22
