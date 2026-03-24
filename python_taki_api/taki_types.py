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


class RuleMode(str, Enum):
    """Controls how card legality is determined on a normal TURN.

    MATCH_COLOR_OR_TYPE: a card is legal if it matches the active color,
        the top card's number (for NUMBER cards), or the top card's kind.
        This is the standard TAKI rule.
    COLOR_ONLY: a card is legal only if it matches the active color.
        Used when the engine enforces a stricter color-matching variant.
    """

    MATCH_COLOR_OR_TYPE = "match_color_or_type"
    COLOR_ONLY = "color_only"


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
    """Full internal game state. Not exposed directly to agents; use GameObservation instead.

    Fields:
        hands: One list of cards per player, indexed by player index.
        draw_pile: Cards remaining to draw, top of pile at the end of the list.
        discard_pile: Cards already played, most recent at the end of the list.
        current_player: Index of the player whose turn it is.
        top_card: The card on top of the discard pile (None at game start).
        active_color: The color that must be matched to play a card on the current
            turn. None only during the CHANGE_COLOR phase (while waiting for a
            SELECT_COLOR action). Set by the last played card's color or by a
            SELECT_COLOR action.
        phase: Current game phase (see Phase).
        taki_color: Non-None only during a TAKI_SEQUENCE phase. Records the color
            of the TAKI card that opened the sequence; cards played within the
            sequence must match this color (SUPER_TAKI is always allowed).
            Always equals active_color while the sequence is open.
        winner: Index of the winning player once the game is terminal, else None.
    """

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
    """Player-facing view of the game. Contains only information visible to the agent.

    Fields:
        player_index: The index of the player this observation is built for.
        phase: Current game phase (see Phase).
        hand: The player's own cards as action-name strings
            (see TakiGame docstring for the action-name format).
            Contains only the cards the player holds — not non-card actions
            such as draw_card or close_taki.  The agent is responsible for
            determining which cards are legal to play and which non-card
            actions (draw_card, close_taki, selected_color) are available,
            using the other observation fields (phase, top_card, active_color,
            rule_mode, taki_color).
        top_card: The card on top of the discard pile as a card descriptor
            string, or None if the discard pile is empty.  Uses a
            player-prefix-free format: ``card_{number}_{color}``,
            ``stop_{color}``, ``taki_{color}``, ``super_taki``,
            ``change_color``.  This is purely informational — the agent uses
            it to determine which cards in hand are legal to play, but never
            returns it as an action.
        active_color: The color that must be matched this turn, or None during
            the CHANGE_COLOR phase.
        rule_mode: Determines card legality on a normal TURN (see RuleMode).
        taki_color: Non-None only during TAKI_SEQUENCE. The color of the open
            TAKI card; cards played within the sequence must match this color.
            Always equals active_color while the sequence is open.
    """

    player_index: int
    phase: Phase
    hand: List[str]
    top_card: Optional[str]
    active_color: Optional[str]
    rule_mode: RuleMode
    taki_color: Optional[str]

    def to_dict(self):
        return asdict(self)
