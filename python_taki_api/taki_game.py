from abc import ABC, abstractmethod
from typing import List, Optional

from .taki_types import Action, GameObservation, GameState


class TakiGame(ABC):
    """
    Abstract contract for a standalone Python TAKI engine.

    A concrete implementation is expected to own the full game rules and state
    transitions independently of the BP program.

    Expected call lifecycle:
        state = game.reset()                          # start a new episode
        while not game.is_terminal(state):
            obs = game.observe(state, current_player) # build player observation
            action = agent.get_action(obs)            # agent picks an action
            action = game.resolve_action_name(state, action)
            state = game.step(state, action)          # advance the state

    Action name format
    ------------------
    Action names are strings that uniquely identify a player's action in the
    shared event namespace (required for behavioural-programming integration,
    where all player events live in the same global space).

    Card names follow the pattern ``p_{player_index}_{card_descriptor}``:

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

    Where ``{color}`` is one of ``red``, ``blue``, ``green`` and ``{i}`` is the
    zero-based player index.
    """

    @abstractmethod
    def reset(
        self,
        seed: Optional[int] = None,
        num_players: int = 2,
        hand_size: int = 8,
    ) -> GameState:
        """
        Initialize and return a fresh game state.
        """
        raise NotImplementedError

    @abstractmethod
    def observe(self, state: GameState, player_index: int) -> GameObservation:
        """
        Build the player-facing observation for the requested player.
        """
        raise NotImplementedError

    @abstractmethod
    def legal_actions(self, state: GameState) -> List[Action]:
        """
        Return the legal actions for the current player in the given state.
        """
        raise NotImplementedError

    @abstractmethod
    def legal_action_names_from_observation(self, observation: GameObservation) -> List[str]:
        """
        Return the legal external action names for a player-facing observation.
        """
        raise NotImplementedError

    @abstractmethod
    def action_to_name(self, player_index: int, action: Action) -> str:
        """
        Convert a domain Action into the external action-name representation.

        ``player_index`` is required because action names are player-scoped:
        two players performing the same action (e.g. both drawing a card) must
        produce distinct names so that the behavioural-programming event bus can
        tell them apart.  See the class docstring for the full name format.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_action_name(self, state: GameState, action_name: str) -> Action:
        """
        Resolve an agent-returned action name into a concrete domain Action.

        The name must be one of the strings produced by action_to_name for the
        current player and state (i.e. it should appear in
        GameObservation.candidate_actions).  See the class docstring for the
        full name format.
        """
        raise NotImplementedError

    @abstractmethod
    def step(self, state: GameState, action: Action) -> GameState:
        """
        Apply one action and return the next game state.
        """
        raise NotImplementedError

    @abstractmethod
    def is_terminal(self, state: GameState) -> bool:
        """
        Return True when the state is terminal.
        """
        raise NotImplementedError
