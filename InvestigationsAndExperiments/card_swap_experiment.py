"""
Card-Swap Symmetry Experiment

This experiment tests for player-position bias by running paired games
with swapped hands.

Protocol:
  Game 1: P0 gets Hand A, P1 gets Hand B → Record winner
  Game 2: P0 gets Hand B, P1 gets Hand A (SWAPPED) → Record winner

Expected Results:
  - FAIR SYSTEM: Different players win (hand quality determines outcome)
  - BIASED SYSTEM: Same player wins both (player position determines outcome)
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import from existing modules
from bp_taki import (
    setup_logger,
    game_manager,
    player_behavior,
    enforce_turns,
    enforce_card_placement_rules,
    identify_deadlock,
    identify_livelock,
    verify_turn_alternation,
    logger
)

# Import BPpy
import bppy as bp
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy

# Import fixed cards
from fixed_cards_dealing import FixedCardsEvents, deal_fixed_cards


# ============================================================================
# Simple Listener to Track Winner
# ============================================================================

class WinnerTrackingListener:
    """Minimal listener that only tracks the winner."""
    
    def __init__(self):
        self.winner = None
        self.events_count = 0
    
    def starting(self, b_program): pass
    def started(self, b_program): pass
    def super_step_done(self, b_program): pass
    def ended(self, b_program): pass
    def assertion_failed(self, b_program): pass
    def halted(self, b_program): pass
    
    def event_selected(self, b_program, event):
        """Track winner events only."""
        self.events_count += 1
        
        if event.name == "p_0_no_more_cards":
            self.winner = 0
        elif event.name == "p_1_no_more_cards":
            self.winner = 1


# ============================================================================
# Run a Single Game
# ============================================================================

def run_single_game(p0_cards, p1_cards, leading_card, remaining_deck, 
                   starting_player=0, game_label="Game", silent=True):
    """
    Run a single game with fixed cards and return the winner.
    
    Parameters
    ----------
    p0_cards : list[BPEvent]
        Cards for player 0
    p1_cards : list[BPEvent]
        Cards for player 1
    leading_card : BPEvent
        The leading card
    remaining_deck : list[BPEvent]
        Remaining cards for draws
    starting_player : int
        Which player goes first (0 or 1)
    game_label : str
        Label for logging (e.g., "Game 1", "Game 2")
    silent : bool
        If True, suppress detailed logging
    
    Returns
    -------
    int or None
        Winner (0 or 1) or None if draw/deadlock
    """
    # Setup logging
    if silent:
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.WARNING)
    
    # Create listener
    listener = WinnerTrackingListener()
    
    # Create BProgram
    num_cards = len(p0_cards)
    bthreads = [
        game_manager(),
        deal_fixed_cards(p0_cards, p1_cards, leading_card, remaining_deck),
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        enforce_turns(2, starting_player),
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation()
    ]
    
    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=listener
    )
    
    # Run the game
    print(f"  Running {game_label}...", end=" ", flush=True)
    try:
        b_program.run()
        winner = listener.winner
        print(f"Player {winner} wins ({listener.events_count} events)")
        return winner
    except Exception as e:
        print(f"ERROR: {e}")
        return None


# ============================================================================
# Card-Swap Experiment
# ============================================================================

def run_card_swap_experiment():
    """
    Main experiment: Run two games with swapped hands.
    """
    
    print("\n" + "=" * 70)
    print("CARD-SWAP SYMMETRY EXPERIMENT")
    print("=" * 70)
    print()
    print("This experiment tests for player-position bias.")
    print()
    print("Protocol:")
    print("  Game 1: P0 gets Hand A, P1 gets Hand B")
    print("  Game 2: P0 gets Hand B, P1 gets Hand A (SWAPPED)")
    print()
    print("Expected results:")
    print("  FAIR:   Different players win (hand quality matters)")
    print("  BIASED: Same player wins both (player position matters)")
    print()
    print("=" * 70)
    
    # Setup
    setup_logger()
    logger.setLevel(logging.CRITICAL)  # Quiet during games
    
    # Create fixed cards
    print("\nSetting up fixed cards...")
    fixed_cards = FixedCardsEvents()
    
    print("\n" + "-" * 70)
    print("Hand A (stronger with TAKI + change_color):")
    for card in fixed_cards.hand_A:
        print(f"  • {card.name}")
    
    print("\nHand B (regular cards):")
    for card in fixed_cards.hand_B:
        print(f"  • {card.name}")
    
    print(f"\nLeading card: {fixed_cards.leading_card.name}")
    print("-" * 70)
    
    input("\nPress Enter to run Game 1...")
    
    # ========================================================================
    # GAME 1: P0 gets Hand A, P1 gets Hand B
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("GAME 1: P0 gets Hand A, P1 gets Hand B")
    print("=" * 70)
    
    config1 = fixed_cards.get_game_config(p0_gets_hand_A=True)
    
    print("\nP0's hand:")
    for card in config1['p0_cards']:
        print(f"  • {card.name}")
    
    print("\nP1's hand:")
    for card in config1['p1_cards']:
        print(f"  • {card.name}")
    
    print()
    winner1 = run_single_game(
        **config1,
        starting_player=0,  # P0 always starts
        game_label="Game 1",
        silent=True
    )
    
    print(f"\n→ Game 1 Result: Player {winner1} wins")
    
    input("\nPress Enter to run Game 2 (with swapped hands)...")
    
    # ========================================================================
    # GAME 2: P0 gets Hand B, P1 gets Hand A (SWAPPED)
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("GAME 2: P0 gets Hand B, P1 gets Hand A (SWAPPED)")
    print("=" * 70)
    
    config2 = fixed_cards.get_game_config(p0_gets_hand_A=False)
    
    print("\nP0's hand (was P1's in Game 1):")
    for card in config2['p0_cards']:
        print(f"  • {card.name}")
    
    print("\nP1's hand (was P0's in Game 1):")
    for card in config2['p1_cards']:
        print(f"  • {card.name}")
    
    print()
    winner2 = run_single_game(
        **config2,
        starting_player=0,  # P0 always starts
        game_label="Game 2",
        silent=True
    )
    
    print(f"\n→ Game 2 Result: Player {winner2} wins")
    
    # ========================================================================
    # ANALYSIS
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    print("\nResults:")
    print(f"  Game 1 (P0 had Hand A): Player {winner1} won")
    print(f"  Game 2 (P0 had Hand B): Player {winner2} won")
    
    print("\n" + "-" * 70)
    
    if winner1 is None or winner2 is None:
        print("⚠️  INCONCLUSIVE")
        print()
        print("One or both games ended without a clear winner (draw/deadlock).")
        print("Try running the experiment again.")
    
    elif winner1 != winner2:
        print("✅ SYMMETRIC RESULT - System appears FAIR")
        print()
        print("Different players won when hands were swapped.")
        print()
        print("Interpretation:")
        print("  • Hand quality determines the winner")
        print("  • No systematic bias based on player position")
        print("  • The BP system treats P0 and P1 fairly")
        print()
        print("Note: This is just ONE trial. For statistical confidence,")
        print("      you should run multiple trials (10-100 pairs).")
    
    else:
        print("⚠️  ASYMMETRIC RESULT - BIAS DETECTED!")
        print()
        print(f"Player {winner1} won BOTH games despite having different hands.")
        print()
        print("Interpretation:")
        print("  • Player position creates systematic advantage")
        print(f"  • Player {winner1} has an inherent advantage in the system")
        print("  • Hand quality matters less than player position")
        print()
        print("Likely causes:")
        print("  1. B-thread registration order bias")
        print("  2. Event selection tiebreaking favors one player")
        print("  3. Some other implementation asymmetry")
        print()
        print("Recommended next steps:")
        print("  • Investigate b-thread registration order")
        print("  • Check EventPrioritySelectionStrategy tiebreaking")
        print("  • Try DeterministicEventPrioritySelectionStrategy")
        print("  • Run multiple trials to confirm pattern")
    
    print("=" * 70)
    
    return winner1, winner2


# ============================================================================
# Multiple Trials for Statistical Confidence
# ============================================================================

def run_multiple_trials(num_trials=10):
    """
    Run multiple card-swap pairs for statistical confidence.
    """
    print("\n" + "=" * 70)
    print(f"MULTIPLE TRIALS EXPERIMENT ({num_trials} pairs)")
    print("=" * 70)
    print()
    print("Running multiple card-swap pairs to detect systematic bias...")
    print()
    
    # Setup
    setup_logger()
    logger.setLevel(logging.CRITICAL)
    
    fixed_cards = FixedCardsEvents()
    
    # Track results
    results = {
        'symmetric': 0,      # Different winners
        'p0_bias': 0,       # P0 won both
        'p1_bias': 0,       # P1 won both
        'inconclusive': 0   # Draw/deadlock
    }
    
    print(f"Running {num_trials} pairs of games...")
    print("-" * 70)
    
    for trial in range(1, num_trials + 1):
        print(f"\nTrial {trial}/{num_trials}:")
        
        # Game A: P0 gets Hand A
        config_a = fixed_cards.get_game_config(p0_gets_hand_A=True)
        winner_a = run_single_game(
            **config_a,
            starting_player=0,
            game_label=f"  Game A",
            silent=True
        )
        
        # Game B: P0 gets Hand B (swapped)
        config_b = fixed_cards.get_game_config(p0_gets_hand_A=False)
        winner_b = run_single_game(
            **config_b,
            starting_player=0,
            game_label=f"  Game B",
            silent=True
        )
        
        # Classify result
        if winner_a is None or winner_b is None:
            results['inconclusive'] += 1
            print(f"  → Inconclusive (draw/deadlock)")
        elif winner_a != winner_b:
            results['symmetric'] += 1
            print(f"  → Symmetric (different winners)")
        elif winner_a == 0 and winner_b == 0:
            results['p0_bias'] += 1
            print(f"  → P0 won both (P0 bias)")
        else:
            results['p1_bias'] += 1
            print(f"  → P1 won both (P1 bias)")
    
    # Analysis
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS")
    print("=" * 70)
    
    completed = num_trials - results['inconclusive']
    
    print(f"\nCompleted trials: {completed}/{num_trials}")
    print()
    print(f"Symmetric outcomes:   {results['symmetric']:3d} ({results['symmetric']/completed*100:5.1f}%)")
    print(f"P0 won both games:    {results['p0_bias']:3d} ({results['p0_bias']/completed*100:5.1f}%)")
    print(f"P1 won both games:    {results['p1_bias']:3d} ({results['p1_bias']/completed*100:5.1f}%)")
    print(f"Inconclusive:         {results['inconclusive']:3d}")
    
    print("\n" + "-" * 70)
    print("INTERPRETATION:")
    print("-" * 70)
    
    # Calculate bias score
    bias_score = (results['p0_bias'] + results['p1_bias']) / completed * 100
    
    if bias_score < 10:
        print("\n✅ SYSTEM APPEARS FAIR")
        print(f"   Only {bias_score:.1f}% of trials showed position bias")
        print("   Hand quality appears to determine outcomes")
    elif bias_score < 30:
        print("\n⚠️  WEAK BIAS DETECTED")
        print(f"   {bias_score:.1f}% of trials showed position bias")
        print("   May need more trials to confirm pattern")
    else:
        print("\n❌ STRONG BIAS DETECTED")
        print(f"   {bias_score:.1f}% of trials showed position bias")
        print("   Player position significantly affects outcomes")
        
        if results['p0_bias'] > results['p1_bias']:
            print(f"\n   Player 0 has systematic advantage")
            print(f"   P0 won both games in {results['p0_bias']/completed*100:.1f}% of trials")
        else:
            print(f"\n   Player 1 has systematic advantage")
            print(f"   P1 won both games in {results['p1_bias']/completed*100:.1f}% of trials")
    
    print("=" * 70)
    
    return results


# ============================================================================
# Main Menu
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║            CARD-SWAP SYMMETRY EXPERIMENT                          ║
    ║                                                                   ║
    ║  Test for player-position bias in the BP Taki implementation     ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print("Choose experiment type:")
    print("  1. Single pair (2 games - quick test)")
    print("  2. Multiple trials (10 pairs - more confidence)")
    print("  3. Extended trials (50 pairs - statistical analysis)")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        run_card_swap_experiment()
    elif choice == "2":
        run_multiple_trials(num_trials=10)
    elif choice == "3":
        run_multiple_trials(num_trials=50)
    else:
        print("Invalid choice. Running single pair...")
        run_card_swap_experiment()
    
    input("\nPress Enter to exit...")