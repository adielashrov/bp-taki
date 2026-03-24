from abc import ABC, abstractmethod
from typing import Optional

from .taki_types import GameObservation


class TakiAgent(ABC):
    """
    Abstract interface for a TAKI-playing agent.

    Expected call lifecycle:
        agent.reset(initial_observation)  # called once at the start of each episode
        while not terminal:
            action_name = agent.get_action(observation)  # called on every turn
    """

    @abstractmethod
    def reset(self, initial_observation: Optional[GameObservation] = None) -> None:
        """
        Called once at the start of each episode, before the first get_action call.

        Agents that maintain internal state (e.g. tracking which cards have
        been played) should initialise that state here.
        Stateless agents may ignore this argument.
        """
        raise NotImplementedError

    @abstractmethod
    def get_action(self, observation: GameObservation) -> Optional[str]:
        """
        Choose and return a legal action name for the current turn.

        The returned string must be a valid action name for the current player
        in the current game state.  The game runner will raise an error if an
        illegal action is returned.

        ``observation.hand`` contains the player's cards as action-name strings.
        The agent must determine which cards are legal to play and which
        non-card actions are available using the observation fields:

        - ``phase``: determines which non-card actions exist this turn:
            - ``TURN``          → ``p_{i}_draw_card`` is available
            - ``TAKI_SEQUENCE`` → ``p_{i}_closed_taki`` is available
            - ``CHANGE_COLOR``  → ``selected_{color}`` for each color
        - ``top_card``: the top card as a player-prefix-free descriptor
          (e.g. ``card_4_blue``, ``stop_red``) — compare against cards in
          ``hand`` by ignoring the ``p_{i}_`` prefix on hand entries
        - ``active_color``, ``rule_mode``: determine which cards in hand
          are legal to play on a normal turn
        - ``taki_color``: constrains which cards are legal during a TAKI
          sequence (cards must match this color, except SUPER_TAKI)

        Action name format (``{i}`` is the player's zero-based index,
        ``{color}`` is one of ``red``, ``blue``, ``green``):

        Card plays:

            Number card : ``p_{i}_card_{number}_{color}``   e.g. ``p_0_card_4_blue``
            Stop card   : ``p_{i}_stop_{color}``            e.g. ``p_1_stop_green``
            TAKI card   : ``p_{i}_taki_{color}``            e.g. ``p_0_taki_red``
            Super TAKI  : ``p_{i}_super_taki``
            Change color: ``p_{i}_change_color``

        Non-card actions:

            Draw card   : ``p_{i}_draw_card``
            Close TAKI  : ``p_{i}_closed_taki``
            Select color: ``selected_{color}``              e.g. ``selected_red``
                (no player prefix — color selection is a global game event)
        """
        raise NotImplementedError
