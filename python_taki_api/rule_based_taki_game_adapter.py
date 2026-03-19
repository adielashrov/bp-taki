import re
from typing import List, Optional

from .taki_game import TakiGame
from .taki_types import Action, ActionType, Card, CardKind, Color, GameObservation, GameState, Phase


class RuleBasedTakiGameAdapter(TakiGame):
    """
    Minimal rule-based adapter over the TakiGame contract.

    This is intentionally not a full TAKI rules engine. Its purpose is to:
    - demonstrate how a concrete game class satisfies the abstract contract
    - provide legality filtering and action-name resolution for the Python agent
    - keep the real TAKI implementation for a separate session
    """

    def reset(
        self,
        seed: Optional[int] = None,
        num_players: int = 2,
        hand_size: int = 8,
    ) -> GameState:
        hands = [
            [
                Card(kind=CardKind.NUMBER, color=Color.BLUE, number=4),
                Card(kind=CardKind.CHANGE_COLOR),
                Card(kind=CardKind.TAKI, color=Color.RED),
            ],
            [
                Card(kind=CardKind.NUMBER, color=Color.RED, number=4),
                Card(kind=CardKind.TAKI, color=Color.BLUE),
                Card(kind=CardKind.STOP, color=Color.GREEN),
            ],
        ]

        return GameState(
            hands=hands[:num_players],
            draw_pile=[],
            discard_pile=[Card(kind=CardKind.NUMBER, color=Color.BLUE, number=3)],
            current_player=0,
            top_card=Card(kind=CardKind.NUMBER, color=Color.BLUE, number=3),
            active_color=Color.BLUE,
            phase=Phase.TURN,
            taki_color=None,
            winner=None,
        )

    def observe(self, state: GameState, player_index: int) -> GameObservation:
        candidate_actions = [self.action_to_name(player_index, action) for action in self.legal_actions(state)]
        hand = [self.card_to_name(player_index, card) for card in state.hands[player_index]]

        return GameObservation(
            player_index=player_index,
            phase=state.phase.value,
            hand=hand,
            candidate_actions=candidate_actions,
            top_card=self.card_to_name(player_index, state.top_card) if state.top_card else None,
            active_color=state.active_color.value if state.active_color else None,
            rule_mode="match_color_or_type",
            taki_color=state.taki_color.value if state.taki_color else None,
        )

    def legal_actions(self, state: GameState) -> List[Action]:
        if state.winner is not None or state.phase == Phase.TERMINAL:
            return []

        if state.phase == Phase.CHANGE_COLOR:
            return [Action(type=ActionType.SELECT_COLOR, color=color) for color in Color]

        actions = [Action(type=ActionType.PLAY_CARD, card=card) for card in state.hands[state.current_player]]

        if state.phase == Phase.TAKI_SEQUENCE:
            actions.append(Action(type=ActionType.CLOSE_TAKI))
        else:
            actions.append(Action(type=ActionType.DRAW_CARD))

        return actions

    def legal_action_names_from_observation(self, observation: GameObservation) -> List[str]:
        return [
            action_name
            for action_name in observation.candidate_actions
            if self._is_legal_action_name(action_name, observation)
        ]

    def step(self, state: GameState, action: Action) -> GameState:
        next_state = GameState(
            hands=[hand.copy() for hand in state.hands],
            draw_pile=state.draw_pile.copy(),
            discard_pile=state.discard_pile.copy(),
            current_player=state.current_player,
            top_card=state.top_card,
            active_color=state.active_color,
            phase=state.phase,
            taki_color=state.taki_color,
            winner=state.winner,
        )

        player_index = next_state.current_player

        if action.type == ActionType.DRAW_CARD:
            next_state.current_player = (player_index + 1) % len(next_state.hands)
            return next_state

        if action.type == ActionType.SELECT_COLOR:
            next_state.active_color = action.color
            next_state.phase = Phase.TURN
            next_state.taki_color = None
            next_state.current_player = (player_index + 1) % len(next_state.hands)
            return next_state

        if action.type == ActionType.CLOSE_TAKI:
            next_state.phase = Phase.TURN
            next_state.taki_color = None
            next_state.current_player = (player_index + 1) % len(next_state.hands)
            return next_state

        if action.type != ActionType.PLAY_CARD or action.card is None:
            raise ValueError(f"Unsupported action: {action}")

        next_state.hands[player_index].remove(action.card)
        next_state.discard_pile.append(action.card)
        next_state.top_card = action.card

        if action.card.kind == CardKind.CHANGE_COLOR:
            next_state.phase = Phase.CHANGE_COLOR
            next_state.active_color = None
            next_state.taki_color = None
            return next_state

        if action.card.kind == CardKind.TAKI:
            next_state.phase = Phase.TAKI_SEQUENCE
            next_state.active_color = action.card.color
            next_state.taki_color = action.card.color
            return next_state

        next_state.phase = Phase.TURN
        next_state.active_color = action.card.color
        next_state.taki_color = None

        if not next_state.hands[player_index]:
            next_state.winner = player_index
            next_state.phase = Phase.TERMINAL
            return next_state

        next_state.current_player = (player_index + 1) % len(next_state.hands)
        return next_state

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or state.phase == Phase.TERMINAL

    def card_to_name(self, player_index: int, card: Optional[Card]) -> Optional[str]:
        if card is None:
            return None

        prefix = f"p_{player_index}_"
        if card.kind == CardKind.NUMBER and card.color is not None and card.number is not None:
            return f"{prefix}card_{card.number}_{card.color.value}"
        if card.kind == CardKind.STOP and card.color is not None:
            return f"{prefix}stop_{card.color.value}"
        if card.kind == CardKind.CHANGE_COLOR:
            return f"{prefix}change_color"
        if card.kind == CardKind.TAKI and card.color is not None:
            return f"{prefix}taki_{card.color.value}"
        if card.kind == CardKind.SUPER_TAKI:
            return f"{prefix}super_taki"
        raise ValueError(f"Unsupported card: {card}")

    def action_to_name(self, player_index: int, action: Action) -> str:
        if action.type == ActionType.DRAW_CARD:
            return f"p_{player_index}_draw_card"
        if action.type == ActionType.CLOSE_TAKI:
            return f"p_{player_index}_closed_taki"
        if action.type == ActionType.SELECT_COLOR and action.color is not None:
            return f"selected_{action.color.value}"
        if action.type == ActionType.PLAY_CARD and action.card is not None:
            return self.card_to_name(player_index, action.card)
        raise ValueError(f"Unsupported action: {action}")

    def resolve_action_name(self, state: GameState, action_name: str) -> Action:
        player_index = state.current_player
        for action in self.legal_actions(state):
            if self.action_to_name(player_index, action) == action_name:
                return action
        raise ValueError(
            f"Unknown action '{action_name}' for player {player_index}. "
            f"Known actions={[self.action_to_name(player_index, action) for action in self.legal_actions(state)]}"
        )

    def _is_legal_action_name(self, action_name: str, observation: GameObservation) -> bool:
        action = self._action_name_to_action(action_name)
        if action is None:
            return False

        phase = observation.phase
        top_card = self._card_from_event_name(observation.top_card)
        active_color = self._color_from_string(observation.active_color)
        taki_color = self._color_from_string(observation.taki_color)

        if phase == Phase.CHANGE_COLOR.value:
            return action.type == ActionType.SELECT_COLOR

        if phase == Phase.TAKI_SEQUENCE.value:
            if action.type == ActionType.CLOSE_TAKI:
                return True
            if action.type != ActionType.PLAY_CARD or action.card is None:
                return False
            if action.card.kind == CardKind.CHANGE_COLOR:
                return False
            if action.card.kind == CardKind.SUPER_TAKI:
                return True
            return action.card.color == taki_color

        if action.type == ActionType.DRAW_CARD:
            return True
        if action.type != ActionType.PLAY_CARD or action.card is None:
            return False
        if action.card.kind in (CardKind.CHANGE_COLOR, CardKind.SUPER_TAKI):
            return True

        if observation.rule_mode == "color_only":
            return action.card.color == active_color

        if top_card is None:
            return True

        if top_card.kind == CardKind.TAKI and action.card.kind == CardKind.TAKI:
            return True

        return self._matches_top_card(action.card, top_card)

    def _action_name_to_action(self, action_name: Optional[str]) -> Optional[Action]:
        if action_name is None:
            return None

        if action_name.endswith("_draw_card"):
            return Action(type=ActionType.DRAW_CARD)

        if action_name.endswith("_closed_taki"):
            return Action(type=ActionType.CLOSE_TAKI)

        if action_name.startswith("selected_"):
            color = self._color_from_string(action_name.replace("selected_", "", 1))
            if color is None:
                return None
            return Action(type=ActionType.SELECT_COLOR, color=color)

        card = self._card_from_event_name(action_name)
        if card is None:
            return None
        return Action(type=ActionType.PLAY_CARD, card=card)

    def _card_from_event_name(self, event_name: Optional[str]) -> Optional[Card]:
        if not event_name:
            return None

        stripped_name = event_name
        while True:
            next_name = re.sub(r"^(deal_|leading_)", "", stripped_name)
            if next_name == stripped_name:
                break
            stripped_name = next_name

        stripped_name = re.sub(r"^p_\d+_", "", stripped_name)
        stripped_name = re.sub(r"^p_", "", stripped_name)

        card_match = re.match(r"^card_(\d+)_(red|blue|green)$", stripped_name)
        if card_match:
            return Card(
                kind=CardKind.NUMBER,
                color=self._color_from_string(card_match.group(2)),
                number=int(card_match.group(1)),
            )

        stop_match = re.match(r"^stop_(red|blue|green)$", stripped_name)
        if stop_match:
            return Card(kind=CardKind.STOP, color=self._color_from_string(stop_match.group(1)))

        taki_match = re.match(r"^taki_(red|blue|green)$", stripped_name)
        if taki_match:
            return Card(kind=CardKind.TAKI, color=self._color_from_string(taki_match.group(1)))

        if stripped_name == "change_color":
            return Card(kind=CardKind.CHANGE_COLOR)

        if stripped_name == "super_taki":
            return Card(kind=CardKind.SUPER_TAKI)

        return None

    def _matches_top_card(self, card: Card, top_card: Card) -> bool:
        if card.color is not None and top_card.color is not None and card.color == top_card.color:
            return True

        if card.kind == CardKind.NUMBER and top_card.kind == CardKind.NUMBER:
            return card.number == top_card.number

        return card.kind == top_card.kind

    def _color_from_string(self, color_value: Optional[str]) -> Optional[Color]:
        if color_value is None:
            return None
        try:
            return Color(color_value)
        except ValueError:
            return None
