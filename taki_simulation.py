"""
Taki Game Simulation Module

This module provides functionality to run multiple simulations of the Taki game
with different random seeds and track statistics about player wins.
"""

import random
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json

import bppy as bp
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy

# Import from bp_taki
from bp_taki import (
    game_manager,
    deal_cards,
    player_behavior,
    basic_strategy_taki,
    basic_strategy_taki_and_super_taki,
    strategy_block_super_taki_during_regular_taki,
    enforce_turns,
    enforce_card_placement_rules,
    identify_deadlock,
    verify_turn_alternation,
    NUM_OF_CARDS
)


@dataclass
class GameResult:
    """Represents the result of a single game."""
    game_number: int
    seed: int
    winner: int  # 0 or 1
    event_count: int
    duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'game_number': self.game_number,
            'seed': self.seed,
            'winner': self.winner,
            'event_count': self.event_count,
            'duration_seconds': self.duration_seconds
        }


@dataclass
class SimulationStats:
    """Tracks statistics across multiple games."""
    total_games: int = 0
    player_0_wins: int = 0
    player_1_wins: int = 0
    errors: int = 0
    average_events_per_game: float = 0.0
    results: List[GameResult] = field(default_factory=list)
    
    def add_result(self, result: GameResult):
        """Add a game result and update statistics."""
        self.results.append(result)
        self.total_games += 1
        
        if result.winner == 0:
            self.player_0_wins += 1
        elif result.winner == 1:
            self.player_1_wins += 1
        
        # Update average events
        total_events = sum(r.event_count for r in self.results)
        self.average_events_per_game = total_events / self.total_games if self.total_games > 0 else 0
    
    def record_error(self):
        """Record a game that ended in error."""
        self.errors += 1
    
    def win_rate(self, player: int) -> float:
        """Calculate win rate for a specific player."""
        if self.total_games == 0:
            return 0.0
        
        wins = self.player_0_wins if player == 0 else self.player_1_wins
        return (wins / self.total_games) * 100
    
    def summary(self) -> str:
        """Generate a summary string of the statistics."""
        lines = [
            "=" * 60,
            "TAKI GAME SIMULATION RESULTS",
            "=" * 60,
            f"Total Games Played: {self.total_games}",
            f"Errors/Incomplete: {self.errors}",
            "",
            "Player 0 Wins: {:4d} ({:5.1f}%)".format(
                self.player_0_wins, self.win_rate(0)
            ),
            "Player 1 Wins: {:4d} ({:5.1f}%)".format(
                self.player_1_wins, self.win_rate(1)
            ),
            "",
            f"Average Events per Game: {self.average_events_per_game:.1f}",
            "=" * 60
        ]
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_games': self.total_games,
            'player_0_wins': self.player_0_wins,
            'player_1_wins': self.player_1_wins,
            'player_0_win_rate': self.win_rate(0),
            'player_1_win_rate': self.win_rate(1),
            'errors': self.errors,
            'average_events_per_game': self.average_events_per_game,
            'results': [r.to_dict() for r in self.results]
        }


class SimulationListener:
    """Listener that tracks game events and determines the winner."""
    
    def __init__(self):
        self.events = []
        self.winner = None
        
    def starting(self, b_program): pass
    def started(self, b_program): pass
    def super_step_done(self, b_program): pass
    def ended(self, b_program): pass
    def assertion_failed(self, b_program): pass
    def halted(self, b_program): pass
    
    def event_selected(self, b_program, event):
        """Record each selected event."""
        self.events.append(event.name)
        
        # Check if this is a winning event
        if event.name == "p_0_no_more_cards":
            self.winner = 0
        elif event.name == "p_1_no_more_cards":
            self.winner = 1
    
    def get_winner(self) -> Optional[int]:
        """Return the winner (0 or 1) or None if no winner yet."""
        return self.winner
    
    def get_event_count(self) -> int:
        """Return the total number of events that occurred."""
        return len(self.events)


def create_simulation_bprogram(
    seed: int,
    listener: SimulationListener,
    num_cards: int = NUM_OF_CARDS,
    player_0_strategy: str = "taki_and_super_taki",
    player_1_strategy: str = "basic",
    player_0_block_super_taki: bool = False,
    player_1_block_super_taki: bool = False,
    starting_player: int = 0
) -> bp.BProgram:
    """
    Create a BProgram configured for simulation.
    
    Parameters
    ----------
    seed : int
        Random seed for this game
    listener : SimulationListener
        Listener to track game events
    num_cards : int
        Number of cards to deal to each player
    player_0_strategy : str
        Strategy for player 0: "basic", "taki", "taki_and_super_taki"
    player_1_strategy : str
        Strategy for player 1: "basic", "taki", "taki_and_super_taki"
    player_0_block_super_taki : bool
        If True, add strategy_block_super_taki_during_regular_taki for player 0
    player_1_block_super_taki : bool
        If True, add strategy_block_super_taki_during_regular_taki for player 1
    starting_player : int
        Which player goes first (0 or 1). Use -1 for random selection based on seed.
        NOTE: Current bp_taki.py implementation always starts with player 0.
        This parameter is included for future compatibility but doesn't change behavior yet.
    
    Returns
    -------
    bp.BProgram
        Configured behavioral program
    
    Notes
    -----
    WARNING: The current implementation of bp_taki.py has a first-player advantage bug.
    Player 0 always goes first (hardcoded in enforce_turns), which gives them
    a significant advantage (~70% win rate with equal strategies).
    
    The starting_player parameter is a placeholder for when this is fixed in bp_taki.py.
    """
    # Set the random seed
    random.seed(seed)
    
    # Determine starting player (currently not used - see docstring warning)
    if starting_player == -1:
        # Random selection based on seed
        actual_starting_player = random.randint(0, 1)
    else:
        actual_starting_player = starting_player
    
    # NOTE: actual_starting_player is computed but not used yet
    # because enforce_turns() doesn't accept this parameter
    
    # Start with core b-threads that are always present
    bthreads = [
        game_manager(),
        deal_cards(2, num_cards),
        player_behavior(0, num_cards),  # Always include base player behavior
        player_behavior(1, num_cards),  # Always include base player behavior
        enforce_turns(),  # TODO: Pass starting_player when bp_taki.py supports it
        enforce_card_placement_rules(),
        identify_deadlock(),
        verify_turn_alternation()
    ]
    
    # Add strategy b-threads for player 0 if not basic
    if player_0_strategy == "taki":
        bthreads.append(basic_strategy_taki(0, num_cards))
    elif player_0_strategy == "taki_and_super_taki":
        bthreads.append(basic_strategy_taki_and_super_taki(0, num_cards))
    elif player_0_strategy != "basic":
        raise ValueError(f"Unknown strategy for player 0: {player_0_strategy}")
    
    # Add blocking strategy for player 0 if requested
    if player_0_block_super_taki:
        bthreads.append(strategy_block_super_taki_during_regular_taki(0))
    
    # Add strategy b-threads for player 1 if not basic
    if player_1_strategy == "taki":
        bthreads.append(basic_strategy_taki(1, num_cards))
    elif player_1_strategy == "taki_and_super_taki":
        bthreads.append(basic_strategy_taki_and_super_taki(1, num_cards))
    elif player_1_strategy != "basic":
        raise ValueError(f"Unknown strategy for player 1: {player_1_strategy}")
    
    # Add blocking strategy for player 1 if requested
    if player_1_block_super_taki:
        bthreads.append(strategy_block_super_taki_during_regular_taki(1))
    
    # Create and return the BProgram
    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=listener
    )
    
    return b_program


def run_single_game(
    game_number: int,
    seed: int,
    num_cards: int = NUM_OF_CARDS,
    player_0_strategy: str = "taki_and_super_taki",
    player_1_strategy: str = "basic",
    player_0_block_super_taki: bool = False,
    player_1_block_super_taki: bool = False,
    silent: bool = True
) -> Optional[GameResult]:
    """
    Run a single game with the given seed.
    
    Parameters
    ----------
    game_number : int
        The game number in the simulation
    seed : int
        Random seed for reproducibility
    num_cards : int
        Number of cards per player
    player_0_strategy : str
        Strategy for player 0
    player_1_strategy : str
        Strategy for player 1
    player_0_block_super_taki : bool
        If True, add strategy_block_super_taki_during_regular_taki for player 0
    player_1_block_super_taki : bool
        If True, add strategy_block_super_taki_during_regular_taki for player 1
    silent : bool
        If True, suppress logging output
    
    Returns
    -------
    GameResult or None
        Result of the game, or None if an error occurred
    """
    # Temporarily adjust logging if silent mode
    if silent:
        original_level = logging.getLogger("TakiGame").level
        logging.getLogger("TakiGame").setLevel(logging.CRITICAL)
    
    try:
        # Create listener
        listener = SimulationListener()
        
        # Create and run the b-program
        start_time = datetime.now()
        b_program = create_simulation_bprogram(
            seed=seed,
            listener=listener,
            num_cards=num_cards,
            player_0_strategy=player_0_strategy,
            player_1_strategy=player_1_strategy,
            player_0_block_super_taki=player_0_block_super_taki,
            player_1_block_super_taki=player_1_block_super_taki
        )
        b_program.run()
        end_time = datetime.now()
        
        # Get the winner
        winner = listener.get_winner()
        
        if winner is None:
            print(f"Warning: Game {game_number} (seed={seed}) ended without a winner")
            return None
        
        # Create result
        duration = (end_time - start_time).total_seconds()
        result = GameResult(
            game_number=game_number,
            seed=seed,
            winner=winner,
            event_count=listener.get_event_count(),
            duration_seconds=duration
        )
        
        return result
        
    except Exception as e:
        print(f"Error in game {game_number} (seed={seed}): {type(e).__name__}: {e}")
        return None
        
    finally:
        if silent:
            logging.getLogger("TakiGame").setLevel(original_level)


def run_simulation(
    num_games: int,
    start_seed: int = 0,
    num_cards: int = NUM_OF_CARDS,
    player_0_strategy: str = "basic",
    player_1_strategy: str = "basic",
    player_0_block_super_taki: bool = False,
    player_1_block_super_taki: bool = False,
    silent: bool = True,
    progress_interval: int = 10
) -> SimulationStats:
    """
    Run multiple games and collect statistics.
    
    Parameters
    ----------
    num_games : int
        Number of games to simulate
    start_seed : int
        Starting random seed (each game increments by 1)
    num_cards : int
        Number of cards per player
    player_0_strategy : str
        Strategy for player 0
    player_1_strategy : str
        Strategy for player 1
    player_0_block_super_taki : bool
        If True, add strategy_block_super_taki_during_regular_taki for player 0
    player_1_block_super_taki : bool
        If True, add strategy_block_super_taki_during_regular_taki for player 1
    silent : bool
        If True, suppress game logging
    progress_interval : int
        Print progress every N games
    
    Returns
    -------
    SimulationStats
        Statistics about all games
    """
    print(f"Starting simulation of {num_games} games...")
    print(f"Player 0 strategy: {player_0_strategy}" + 
          (" + block_super_taki" if player_0_block_super_taki else ""))
    print(f"Player 1 strategy: {player_1_strategy}" +
          (" + block_super_taki" if player_1_block_super_taki else ""))
    print(f"Cards per player: {num_cards}")
    print(f"Starting seed: {start_seed}")
    print("-" * 60)
    
    stats = SimulationStats()
    
    for i in range(num_games):
        game_number = i + 1
        seed = start_seed + i
        
        # Print progress
        if game_number % progress_interval == 0 or game_number == 1:
            print(f"Running game {game_number}/{num_games} (seed={seed})...")
        
        # Run the game
        result = run_single_game(
            game_number=game_number,
            seed=seed,
            num_cards=num_cards,
            player_0_strategy=player_0_strategy,
            player_1_strategy=player_1_strategy,
            player_0_block_super_taki=player_0_block_super_taki,
            player_1_block_super_taki=player_1_block_super_taki,
            silent=silent
        )
        
        # Record result
        if result is not None:
            stats.add_result(result)
        else:
            stats.record_error()
    
    return stats


def save_results(stats: SimulationStats, filename: str = None):
    """
    Save simulation results to a JSON file.
    
    Parameters
    ----------
    stats : SimulationStats
        Statistics to save
    filename : str, optional
        Output filename. If None, generates a timestamped name.
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"taki_simulation_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(stats.to_dict(), f, indent=2)
    
    print(f"\nResults saved to: {filename}")


if __name__ == "__main__":
    # Example: Run 100 games
    stats = run_simulation(
        num_games=10,
        start_seed=0,
        player_0_strategy="basic",
        player_1_strategy="basic",
        silent=True,
        progress_interval=10
    )
    
    # Print summary
    print("\n" + stats.summary())
    
    # Save results
    save_results(stats)