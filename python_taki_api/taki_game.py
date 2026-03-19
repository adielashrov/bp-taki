from abc import ABC, abstractmethod
from typing import List, Optional

from .taki_types import Action, GameObservation, GameState


class TakiGame(ABC):
    """
    Abstract contract for a standalone Python TAKI engine.

    A concrete implementation is expected to own the full game rules and state
    transitions independently of the BP program.
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
    def action_to_name(self, player_index: int, action: Action) -> str:
        """
        Convert a domain Action into the external action-name representation.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_action_name(self, state: GameState, action_name: str) -> Action:
        """
        Resolve an agent-returned action name into a concrete domain Action.
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
