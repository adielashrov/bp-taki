from typing import List, Optional

from .taki_game import TakiGame
from .taki_types import Action, ActionType, Card, CardKind, Color, GameObservation, GameState, Phase


class DummyTakiGame(TakiGame):
    """
    Minimal reference implementation of the TakiGame contract.

    This is intentionally not a full TAKI rules engine. Its purpose is to:
    - demonstrate how a concrete game class satisfies the abstract contract
    - provide a simple object a Python agent can be exercised against
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
