from dataclasses import asdict, dataclass
from enum import Enum
from typing import List, Optional


class Color(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"


class Phase(str, Enum):
    TURN = "turn"
    TAKI_SEQUENCE = "taki_sequence"
    CHANGE_COLOR = "change_color"
    TERMINAL = "terminal"


class CardKind(str, Enum):
    NUMBER = "number"
    STOP = "stop"
    CHANGE_COLOR = "change_color"
    TAKI = "taki"
    SUPER_TAKI = "super_taki"


class ActionType(str, Enum):
    PLAY_CARD = "play_card"
    DRAW_CARD = "draw_card"
    CLOSE_TAKI = "close_taki"
    SELECT_COLOR = "select_color"


@dataclass(frozen=True)
class Card:
    kind: CardKind
    color: Optional[Color] = None
    number: Optional[int] = None


@dataclass(frozen=True)
class Action:
    type: ActionType
    card: Optional[Card] = None
    color: Optional[Color] = None


@dataclass
class GameState:
    hands: List[List[Card]]
    draw_pile: List[Card]
    discard_pile: List[Card]
    current_player: int
    top_card: Optional[Card]
    active_color: Optional[Color]
    phase: Phase = Phase.TURN
    taki_color: Optional[Color] = None
    winner: Optional[int] = None


@dataclass(frozen=True)
class GameObservation:
    player_index: int
    phase: Phase
    hand: List[str]
    candidate_actions: List[str]
    top_card: Optional[str]
    active_color: Optional[str]
    rule_mode: str
    taki_color: Optional[str]

    def to_dict(self):
        return asdict(self)
