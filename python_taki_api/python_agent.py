from typing import Optional

from .taki_agent import TakiAgent
from .taki_agent_adapter import run_agent_episode
from .taki_game import TakiGame
from .taki_types import GameObservation


class PythonAgent(TakiAgent):
    def __init__(self, game: Optional[TakiGame] = None):
        self.last_observation: Optional[GameObservation] = None
        if game is None:
            from .rule_based_taki_game_adapter import RuleBasedTakiGameAdapter

            game = RuleBasedTakiGameAdapter()
        self.game = game

    def reset(self, initial_observation: Optional[GameObservation] = None) -> None:
        self.last_observation = initial_observation

    def get_action(self, observation: GameObservation) -> Optional[str]:
        self.last_observation = observation

        legal_action_names = self.game.legal_action_names_from_observation(observation)
        if not legal_action_names:
            return None
        return legal_action_names[0]


def run_dummy_session(max_steps: int = 20):
    from .rule_based_taki_game_adapter import RuleBasedTakiGameAdapter

    game = RuleBasedTakiGameAdapter()
    agent = PythonAgent(game=game)
    return run_agent_episode(game=game, agent=agent, max_steps=max_steps)
