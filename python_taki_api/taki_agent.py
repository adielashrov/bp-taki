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
        raise NotImplementedError

    @abstractmethod
    def get_action(self, observation: GameObservation) -> Optional[str]:
        raise NotImplementedError
