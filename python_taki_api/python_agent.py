from typing import Optional

from .taki_agent import TakiAgent
from .taki_agent_adapter import run_agent_episode
from .taki_types import GameObservation


class PythonAgent(TakiAgent):
    def __init__(self):
        self.last_observation: Optional[GameObservation] = None

    def reset(self, initial_observation: Optional[GameObservation] = None) -> None:
        self.last_observation = initial_observation

    def get_action(self, observation: GameObservation) -> Optional[str]:
        self.last_observation = observation

        if not observation.candidate_actions:
            return None

        # Placeholder policy until a concrete standalone TakiGame
        # implementation is provided in a separate session.
        return observation.candidate_actions[0]


def run_dummy_session(max_steps: int = 20):
    from .dummy_taki_game import DummyTakiGame

    game = DummyTakiGame()
    agent = PythonAgent()
    return run_agent_episode(game=game, agent=agent, max_steps=max_steps)
