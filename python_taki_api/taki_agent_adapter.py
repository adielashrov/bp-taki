from dataclasses import dataclass
from typing import List, Optional, Tuple

from .taki_agent import TakiAgent
from .taki_game import TakiGame
from .taki_types import Action, GameObservation, GameState


@dataclass(frozen=True)
class AgentStepResult:
    player_index: int
    observation: GameObservation
    action_name: str
    action: Action
    next_state: GameState


def choose_action(game: TakiGame, agent: TakiAgent, state: GameState) -> Tuple[GameObservation, str, Action]:
    player_index = state.current_player
    observation = game.observe(state, player_index)
    action_name = agent.get_action(observation)
    if action_name is None:
        raise ValueError(f"Agent returned no action for player {player_index}")
    action = game.resolve_action_name(state, action_name)
    return observation, action_name, action


def step_agent(game: TakiGame, agent: TakiAgent, state: GameState) -> AgentStepResult:
    observation, action_name, action = choose_action(game, agent, state)
    next_state = game.step(state, action)
    return AgentStepResult(
        player_index=state.current_player,
        observation=observation,
        action_name=action_name,
        action=action,
        next_state=next_state,
    )


def run_agent_episode(
    game: TakiGame,
    agent: TakiAgent,
    seed: Optional[int] = None,
    num_players: int = 2,
    hand_size: int = 8,
    max_steps: int = 100,
) -> Tuple[GameState, List[AgentStepResult]]:
    state = game.reset(seed=seed, num_players=num_players, hand_size=hand_size)
    agent.reset(game.observe(state, state.current_player))

    history: List[AgentStepResult] = []
    while not game.is_terminal(state):
        if len(history) >= max_steps:
            raise RuntimeError(f"Episode exceeded max_steps={max_steps}")
        step_result = step_agent(game, agent, state)
        history.append(step_result)
        state = step_result.next_state

    return state, history
