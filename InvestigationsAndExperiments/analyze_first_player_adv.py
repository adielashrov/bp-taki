#!/usr/bin/env python3
"""
Example: Analyzing First-Player Advantage

This script demonstrates how starting player information is tracked
and analyzed in simulation results.
"""

from pathlib import Path
import sys
1
# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from taki_simulation import run_simulation, save_results


def example_first_player_advantage_tracking():
    """
    Demonstrate that starting player is tracked in results.
    
    Currently, all games start with Player 0 (bp_taki.py limitation),
    but this tracking will be useful once the bug is fixed.
    """
    print("=" * 70)
    print("FIRST-PLAYER ADVANTAGE TRACKING DEMONSTRATION")
    print("=" * 70)
    print()
    print("Running 100 games with both players using basic strategy...")
    print("We'll track who started each game and analyze the advantage.")
    print()
    
    stats = run_simulation(
        num_games=10,
        start_seed=42,
        player_0_strategy="basic",
        player_1_strategy="basic",
        starting_player=0,  # Currently always 0 (bug in bp_taki.py)
        silent=True,
        progress_interval=25
    )
    
    print("\n" + stats.summary())
    
    # Detailed analysis
    print("\n" + "=" * 70)
    print("DETAILED STARTING PLAYER ANALYSIS")
    print("=" * 70)
    
    adv = stats.starting_player_advantage()
    
    print(f"\nGames where Player 0 started: {adv['starting_player_0_count']}")
    print(f"Games where Player 1 started: {adv['starting_player_1_count']}")
    print(f"\nStarting player won: {adv['wins_when_starting']} games")
    print(f"Starting player win rate: {adv['starter_win_rate']:.1f}%")
    
    if adv['starting_player_0_count'] == stats.total_games:
        print("\n⚠️  ALERT: Player 0 started ALL games!")
        print("This confirms the first-player advantage bug in bp_taki.py")
        print(f"Player 0 won {stats.player_0_wins} games ({stats.win_rate(0):.1f}%)")
        print(f"Expected with fair game: ~50 games (~50%)")
        print(f"Advantage: ~{stats.win_rate(0) - 50:.1f} percentage points")
    
    # Show sample of individual game results
    print("\n" + "=" * 70)
    print("SAMPLE GAME RESULTS (first 10 games)")
    print("=" * 70)
    print(f"{'Game':<6} {'Seed':<8} {'Starter':<8} {'Winner':<8} {'Events':<8}")
    print("-" * 70)
    
    for result in stats.results[:10]:
        print(f"{result.game_number:<6} {result.seed:<8} "
              f"P{result.starting_player:<7} P{result.winner:<7} "
              f"{result.event_count:<8}")
    
    print("\nNote: 'Starter' column shows who went first (currently always P0)")
    
    # Save results with starting player data
    save_results(stats, "first_player_tracking_demo.json")
    print("\n✓ Results saved to first_player_tracking_demo.json")
    print("  (includes 'starting_player' field for each game)")


def example_after_fix():
    """
    This is what the output WILL look like after bp_taki.py is fixed
    to support randomized starting player.
    """
    print("\n\n" + "=" * 70)
    print("EXAMPLE: WHAT RESULTS WILL LOOK LIKE AFTER FIX")
    print("=" * 70)
    print("""
When bp_taki.py is fixed and starting_player=-1 is used:

============================================================
TAKI GAME SIMULATION RESULTS
============================================================
Total Games Played: 100
Errors/Incomplete: 0

Player 0 Wins:   51 ( 51.0%)
Player 1 Wins:   49 ( 49.0%)

Average Events per Game: 85.3

Starting Player Analysis:
  Games where P0 started: 48
  Games where P1 started: 52
  Starting player won: 71/100 (71.0%)
============================================================

This would show:
- Fair win distribution (51% vs 49%)
- Randomized starting player (48 vs 52 games)
- Quantified first-player advantage (~71% win rate for starter)
""")


if __name__ == "__main__":
    example_first_player_advantage_tracking()
    example_after_fix()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Starting player is now tracked in every GameResult!

Fields tracked:
- game_number: Sequential game ID
- seed: Random seed used
- winner: Which player won (0 or 1)
- starting_player: Which player went first (0 or 1)  ← NEW!
- event_count: Number of events in game
- duration_seconds: How long the game took

This data enables:
✓ Detecting first-player advantage bugs
✓ Quantifying starting position impact
✓ Analyzing strategy effectiveness independent of position
✓ Research validation and reproducibility

Next step: Fix bp_taki.py to support starting_player parameter!
""")