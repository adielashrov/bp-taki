"""
Comprehensive 4-Game Symmetry Test

This experiment tests ALL sources of bias by varying:
1. Which player starts (P0 or P1)
2. Which hands players receive (A or B)

Protocol:
  Game 1: P0 starts, P0 has Hand A, P1 has Hand B
  Game 2: P0 starts, P0 has Hand B, P1 has Hand A (swap hands)
  Game 3: P1 starts, P0 has Hand A, P1 has Hand B (swap starting)
  Game 4: P1 starts, P0 has Hand B, P1 has Hand A (swap both)

Symmetry Checks:
  1. Starting player symmetry: Does starting player win regardless of identity?
  2. Hand quality symmetry: Does same hand quality win regardless of who holds it?
  3. Position symmetry: No inherent P0 vs P1 advantage
  4. Diagonal symmetry: Complete role reversal yields same pattern
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
1
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
    print(f"  {game_label}...", end=" ", flush=True)
    try:
        b_program.run()
        winner = listener.winner
        print(f"Winner: P{winner} ({listener.events_count} events)")
        return winner
    except Exception as e:
        print(f"ERROR: {e}")
        return None


# ============================================================================
# 4-Game Symmetry Test
# ============================================================================

def run_four_game_symmetry_test():
    """
    Run all 4 game combinations and check for symmetry.
    """
    
    print("\n" + "=" * 70)
    print("COMPREHENSIVE 4-GAME SYMMETRY TEST")
    print("=" * 70)
    print()
    print("This experiment tests ALL sources of bias:")
    print("  • Player position (P0 vs P1 identity)")
    print("  • Starting player (who goes first)")
    print("  • Hand quality (which cards you have)")
    print()
    print("Protocol: Run 4 games varying starting player and hand assignment")
    print("=" * 70)
    
    # Setup
    setup_logger()
    logger.setLevel(logging.CRITICAL)
    
    # Create fixed cards
    print("\nSetting up fixed cards...")
    fixed_cards = FixedCardsEvents()
    
    print("\n" + "-" * 70)
    print("Hand A:")
    for card in fixed_cards.hand_A:
        print(f"  • {card.name}")
    
    print("\nHand B:")
    for card in fixed_cards.hand_B:
        print(f"  • {card.name}")
    
    print(f"\nLeading card: {fixed_cards.leading_card.name}")
    print("-" * 70)
    
    # Store results
    results = {}
    
    input("\nPress Enter to run the 4 games...")
    
    print("\n" + "=" * 70)
    print("RUNNING GAMES")
    print("=" * 70)
    
    # ========================================================================
    # GAME 1: P0 starts, P0 has Hand A, P1 has Hand B
    # ========================================================================
    
    print("\nGame 1: P0 starts, P0 has Hand A, P1 has Hand B")
    print("-" * 70)
    
    config1 = fixed_cards.get_game_config(p0_gets_hand_A=True)
    winner1 = run_single_game(
        **config1,
        starting_player=0,
        game_label="  Running",
        silent=True
    )
    results['game1'] = {
        'starting_player': 0,
        'p0_hand': 'A',
        'p1_hand': 'B',
        'winner': winner1
    }
    
    # ========================================================================
    # GAME 2: P0 starts, P0 has Hand B, P1 has Hand A (swap hands)
    # ========================================================================
    
    print("\nGame 2: P0 starts, P0 has Hand B, P1 has Hand A (hands swapped)")
    print("-" * 70)
    
    config2 = fixed_cards.get_game_config(p0_gets_hand_A=False)
    winner2 = run_single_game(
        **config2,
        starting_player=0,
        game_label="  Running",
        silent=True
    )
    results['game2'] = {
        'starting_player': 0,
        'p0_hand': 'B',
        'p1_hand': 'A',
        'winner': winner2
    }
    
    # ========================================================================
    # GAME 3: P1 starts, P0 has Hand A, P1 has Hand B (swap starting player)
    # ========================================================================
    
    print("\nGame 3: P1 starts, P0 has Hand A, P1 has Hand B (P1 starts)")
    print("-" * 70)
    
    config3 = fixed_cards.get_game_config(p0_gets_hand_A=True)
    winner3 = run_single_game(
        **config3,
        starting_player=1,  # P1 starts!
        game_label="  Running",
        silent=True
    )
    results['game3'] = {
        'starting_player': 1,
        'p0_hand': 'A',
        'p1_hand': 'B',
        'winner': winner3
    }
    
    # ========================================================================
    # GAME 4: P1 starts, P0 has Hand B, P1 has Hand A (swap both)
    # ========================================================================
    
    print("\nGame 4: P1 starts, P0 has Hand B, P1 has Hand A (both swapped)")
    print("-" * 70)
    
    config4 = fixed_cards.get_game_config(p0_gets_hand_A=False)
    winner4 = run_single_game(
        **config4,
        starting_player=1,  # P1 starts!
        game_label="  Running",
        silent=True
    )
    results['game4'] = {
        'starting_player': 1,
        'p0_hand': 'B',
        'p1_hand': 'A',
        'winner': winner4
    }
    
    # ========================================================================
    # ANALYSIS: Check All Symmetries
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    # Create results table
    print("\n┌────────┬──────────────┬──────────┬──────────┬─────────┐")
    print("│ Game   │ Starting     │ P0 Hand  │ P1 Hand  │ Winner  │")
    print("├────────┼──────────────┼──────────┼──────────┼─────────┤")
    print(f"│ Game 1 │ P{results['game1']['starting_player']}           │ {results['game1']['p0_hand']:8s} │ {results['game1']['p1_hand']:8s} │ P{results['game1']['winner']}      │")
    print(f"│ Game 2 │ P{results['game2']['starting_player']}           │ {results['game2']['p0_hand']:8s} │ {results['game2']['p1_hand']:8s} │ P{results['game2']['winner']}      │")
    print(f"│ Game 3 │ P{results['game3']['starting_player']}           │ {results['game3']['p0_hand']:8s} │ {results['game3']['p1_hand']:8s} │ P{results['game3']['winner']}      │")
    print(f"│ Game 4 │ P{results['game4']['starting_player']}           │ {results['game4']['p0_hand']:8s} │ {results['game4']['p1_hand']:8s} │ P{results['game4']['winner']}      │")
    print("└────────┴──────────────┴──────────┴──────────┴─────────┘")
    
    # ========================================================================
    # SYMMETRY CHECKS
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("SYMMETRY ANALYSIS")
    print("=" * 70)
    
    symmetry_passed = 0
    symmetry_total = 0
    
    # ------------------------------------------------------------------------
    # CHECK 1: Hand Quality Symmetry (when P0 starts)
    # ------------------------------------------------------------------------
    print("\n[CHECK 1] Hand Quality Symmetry (when P0 starts)")
    print("-" * 70)
    print("Question: Does the player with Hand B win when P0 starts?")
    print()
    print(f"  Game 1: P0 starts, P0 has A, P1 has B → P{winner1} wins")
    print(f"  Game 2: P0 starts, P0 has B, P1 has A → P{winner2} wins")
    print()
    
    # Who has Hand B in each game?
    game1_hand_b_holder = 1  # P1 has Hand B
    game2_hand_b_holder = 0  # P0 has Hand B
    
    symmetry_total += 1
    if winner1 == game1_hand_b_holder and winner2 == game2_hand_b_holder:
        print("  ✅ SYMMETRIC: Player with Hand B won both times")
        print("     → Hand quality matters more than player position")
        symmetry_passed += 1
    elif winner1 == winner2:
        print(f"  ❌ POSITION BIAS: P{winner1} won both times despite different hands")
        print(f"     → Player {winner1} has systematic advantage when P0 starts")
    else:
        print("  ⚠️  MIXED RESULT: Different hands won")
        print("     → May indicate randomness or complex interaction")
    
    # ------------------------------------------------------------------------
    # CHECK 2: Hand Quality Symmetry (when P1 starts)
    # ------------------------------------------------------------------------
    print("\n[CHECK 2] Hand Quality Symmetry (when P1 starts)")
    print("-" * 70)
    print("Question: Does the player with Hand B win when P1 starts?")
    print()
    print(f"  Game 3: P1 starts, P0 has A, P1 has B → P{winner3} wins")
    print(f"  Game 4: P1 starts, P0 has B, P1 has A → P{winner4} wins")
    print()
    
    game3_hand_b_holder = 1  # P1 has Hand B
    game4_hand_b_holder = 0  # P0 has Hand B
    
    symmetry_total += 1
    if winner3 == game3_hand_b_holder and winner4 == game4_hand_b_holder:
        print("  ✅ SYMMETRIC: Player with Hand B won both times")
        print("     → Hand quality matters more than player position")
        symmetry_passed += 1
    elif winner3 == winner4:
        print(f"  ❌ POSITION BIAS: P{winner3} won both times despite different hands")
        print(f"     → Player {winner3} has systematic advantage when P1 starts")
    else:
        print("  ⚠️  MIXED RESULT: Different hands won")
        print("     → May indicate randomness or complex interaction")
    
    # ------------------------------------------------------------------------
    # CHECK 3: Starting Player Symmetry (with Hand A)
    # ------------------------------------------------------------------------
    print("\n[CHECK 3] Starting Player Symmetry (with Hand A)")
    print("-" * 70)
    print("Question: Does the starting player win when they have Hand A?")
    print()
    print(f"  Game 1: P0 starts, P0 has A → P{winner1} wins")
    print(f"  Game 3: P1 starts, P1 has A → P{winner3} wins")
    print()
    
    symmetry_total += 1
    if winner1 == 0 and winner3 == 1:
        print("  ✅ SYMMETRIC: Starting player won in both cases")
        print("     → Starting player has advantage (first-mover advantage)")
        symmetry_passed += 1
    elif winner1 == 1 and winner3 == 0:
        print("  ✅ SYMMETRIC: Non-starting player won in both cases")
        print("     → Second player has advantage (counter-player advantage)")
        symmetry_passed += 1
    elif winner1 == winner3:
        print(f"  ❌ POSITION BIAS: P{winner1} won both times")
        print(f"     → Player {winner1} has systematic advantage regardless of starting")
    else:
        print("  ⚠️  MIXED RESULT: No clear pattern")
    
    # ------------------------------------------------------------------------
    # CHECK 4: Starting Player Symmetry (with Hand B)
    # ------------------------------------------------------------------------
    print("\n[CHECK 4] Starting Player Symmetry (with Hand B)")
    print("-" * 70)
    print("Question: Does the starting player win when they have Hand B?")
    print()
    print(f"  Game 2: P0 starts, P0 has B → P{winner2} wins")
    print(f"  Game 4: P1 starts, P1 has B → P{winner4} wins")
    print()
    
    symmetry_total += 1
    if winner2 == 0 and winner4 == 1:
        print("  ✅ SYMMETRIC: Starting player won in both cases")
        print("     → Starting player has advantage")
        symmetry_passed += 1
    elif winner2 == 1 and winner4 == 0:
        print("  ✅ SYMMETRIC: Non-starting player won in both cases")
        print("     → Second player has advantage")
        symmetry_passed += 1
    elif winner2 == winner4:
        print(f"  ❌ POSITION BIAS: P{winner2} won both times")
        print(f"     → Player {winner2} has systematic advantage regardless of starting")
    else:
        print("  ⚠️  MIXED RESULT: No clear pattern")
    
    # ------------------------------------------------------------------------
    # CHECK 5: Diagonal Symmetry (complete role reversal)
    # ------------------------------------------------------------------------
    print("\n[CHECK 5] Diagonal Symmetry (complete role reversal)")
    print("-" * 70)
    print("Question: Does complete role reversal produce same winner?")
    print()
    print(f"  Game 1: P0 starts, P0 has A, P1 has B → P{winner1} wins")
    print(f"  Game 4: P1 starts, P0 has B, P1 has A → P{winner4} wins")
    print("          └─────────────────────────────────┘")
    print("          Complete reversal: P0↔P1, A↔B, starter↔second")
    print()
    
    symmetry_total += 1
    if winner1 == winner4:
        print(f"  ✅ SYMMETRIC: P{winner1} won in both cases")
        print("     → System exhibits perfect rotational symmetry")
        symmetry_passed += 1
    else:
        print(f"  ❌ ASYMMETRIC: P{winner1} won Game 1, P{winner4} won Game 4")
        print("     → System breaks under complete role reversal")
    
    # ------------------------------------------------------------------------
    # CHECK 6: Cross-diagonal Symmetry
    # ------------------------------------------------------------------------
    print("\n[CHECK 6] Cross-Diagonal Symmetry")
    print("-" * 70)
    print("Question: Does the other diagonal show consistency?")
    print()
    print(f"  Game 2: P0 starts, P0 has B, P1 has A → P{winner2} wins")
    print(f"  Game 3: P1 starts, P0 has A, P1 has B → P{winner3} wins")
    print()
    
    symmetry_total += 1
    if winner2 == winner3:
        print(f"  ✅ CONSISTENT: P{winner2} won in both cases")
        symmetry_passed += 1
    else:
        print(f"  ❌ INCONSISTENT: P{winner2} won Game 2, P{winner3} won Game 3")
    
    # ========================================================================
    # OVERALL ASSESSMENT
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("OVERALL ASSESSMENT")
    print("=" * 70)
    
    symmetry_score = symmetry_passed / symmetry_total * 100
    
    print(f"\nSymmetry checks passed: {symmetry_passed}/{symmetry_total} ({symmetry_score:.1f}%)")
    print()
    
    if symmetry_score >= 80:
        print("✅ SYSTEM IS HIGHLY SYMMETRIC")
        print()
        print("The BP implementation appears fair and unbiased.")
        print("Outcomes are determined by:")
        print("  • Hand quality (which cards you have)")
        print("  • Starting player advantage (first-mover or counter-player)")
        print("  • NOT by player identity (P0 vs P1)")
    elif symmetry_score >= 50:
        print("⚠️  PARTIAL SYMMETRY DETECTED")
        print()
        print("Some symmetries hold but others are broken.")
        print("The system may have subtle biases.")
        print("Recommendation: Run multiple trials to confirm patterns.")
    else:
        print("❌ SYSTEM SHOWS SIGNIFICANT ASYMMETRY")
        print()
        print("Multiple symmetry checks failed.")
        print("The system likely has implementation bias.")
        print("Recommendation:")
        print("  1. Check b-thread registration order")
        print("  2. Try DeterministicEventPrioritySelectionStrategy")
        print("  3. Run multiple trials to confirm")
    
    print("=" * 70)
    
    return results


# ============================================================================
# Multiple Trials Version
# ============================================================================

def run_multiple_four_game_trials(num_trials=10):
    """
    Run multiple sets of 4-game trials for statistical confidence.
    """
    print("\n" + "=" * 70)
    print(f"MULTIPLE 4-GAME TRIALS ({num_trials} sets)")
    print("=" * 70)
    print()
    print("Running multiple complete 4-game sets to detect patterns...")
    print()
    
    # Setup
    setup_logger()
    logger.setLevel(logging.CRITICAL)
    
    fixed_cards = FixedCardsEvents()
    
    # Track all results
    all_results = []
    
    print(f"Running {num_trials} complete 4-game sets...")
    print("-" * 70)
    
    for trial in range(1, num_trials + 1):
        print(f"\nTrial {trial}/{num_trials}:")
        
        trial_results = {}
        
        # Game 1: P0 starts, P0 has A
        config1 = fixed_cards.get_game_config(p0_gets_hand_A=True)
        w1 = run_single_game(**config1, starting_player=0, game_label=f"  G1", silent=True)
        trial_results['g1'] = w1
        
        # Game 2: P0 starts, P0 has B
        config2 = fixed_cards.get_game_config(p0_gets_hand_A=False)
        w2 = run_single_game(**config2, starting_player=0, game_label=f"  G2", silent=True)
        trial_results['g2'] = w2
        
        # Game 3: P1 starts, P0 has A
        config3 = fixed_cards.get_game_config(p0_gets_hand_A=True)
        w3 = run_single_game(**config3, starting_player=1, game_label=f"  G3", silent=True)
        trial_results['g3'] = w3
        
        # Game 4: P1 starts, P0 has B
        config4 = fixed_cards.get_game_config(p0_gets_hand_A=False)
        w4 = run_single_game(**config4, starting_player=1, game_label=f"  G4", silent=True)
        trial_results['g4'] = w4
        
        all_results.append(trial_results)
        
        # Quick pattern check
        hand_b_wins = sum([
            w1 == 1,  # P1 has B in G1
            w2 == 0,  # P0 has B in G2
            w3 == 1,  # P1 has B in G3
            w4 == 0   # P0 has B in G4
        ])
        
        print(f"    Hand B won {hand_b_wins}/4 games", end="")
        if hand_b_wins == 4:
            print(" ✅ Perfect hand symmetry")
        elif hand_b_wins == 0:
            print(" ❌ Hand A always wins?!")
        else:
            print()
    
    # Statistical analysis
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS")
    print("=" * 70)
    
    # Count how often Hand B holder wins
    hand_b_win_counts = [
        sum([r['g1'] == 1, r['g2'] == 0, r['g3'] == 1, r['g4'] == 0])
        for r in all_results
    ]
    
    avg_hand_b_wins = sum(hand_b_win_counts) / len(hand_b_win_counts)
    
    print(f"\nAverage games where Hand B holder won: {avg_hand_b_wins:.2f}/4")
    print(f"Expected if hand quality matters: 4.00/4")
    print(f"Expected if random: 2.00/4")
    
    if avg_hand_b_wins >= 3.5:
        print("\n✅ Hand B is systematically stronger")
        print("   System appears fair - hand quality determines outcomes")
    elif avg_hand_b_wins <= 0.5:
        print("\n❌ Hand A is systematically stronger (unexpected!)")
    else:
        print("\n⚠️  Mixed results - may indicate bias or randomness")
    
    print("=" * 70)


# ============================================================================
# Main Menu
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║         COMPREHENSIVE 4-GAME SYMMETRY TEST                        ║
    ║                                                                   ║
    ║  Tests all combinations of starting player and hand assignment   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print("Choose experiment type:")
    print("  1. Single 4-game set (detailed analysis)")
    print("  2. Multiple trials (10 sets = 40 games)")
    print("  3. Extended trials (50 sets = 200 games)")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        run_four_game_symmetry_test()
    elif choice == "2":
        run_multiple_four_game_trials(num_trials=10)
    elif choice == "3":
        run_multiple_four_game_trials(num_trials=50)
    else:
        print("Invalid choice. Running single 4-game set...")
        run_four_game_symmetry_test()
    
    input("\nPress Enter to exit...")