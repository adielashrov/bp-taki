from abc import ABC, abstractmethod
from typing import Optional

from .taki_types import GameObservation


class TakiAgent(ABC):
    @abstractmethod
    def reset(self, initial_observation: Optional[GameObservation] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_action(self, observation: GameObservation) -> Optional[str]:
        raise NotImplementedError
