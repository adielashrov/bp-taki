"""
Trace Comparison Experiment

Tests if swapping player identities produces identical traces.

Protocol:
  Game A: P0 starts with Hand A, P1 has Hand B, seed=X
  Game B: P1 starts with Hand A, P0 has Hand B, seed=X
          └─────────────────────────────────────────┘
          Complete identity swap
          
Expected: Identical event sequences (with P0↔P1 labels swapped)
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
# Trace Recording Listener
# ============================================================================

class TraceRecordingListener:
    """Records complete event trace."""
    
    def __init__(self):
        self.trace = []
        self.winner = None
    
    def starting(self, b_program): pass
    def started(self, b_program): pass
    def super_step_done(self, b_program): pass
    def ended(self, b_program): pass
    def assertion_failed(self, b_program): pass
    def halted(self, b_program): pass
    
    def event_selected(self, b_program, event):
        """Record each event."""
        self.trace.append(event.name)
        
        if event.name == "p_0_no_more_cards":
            self.winner = 0
        elif event.name == "p_1_no_more_cards":
            self.winner = 1
    
    def get_trace(self):
        """Return the complete trace."""
        return self.trace
    
    def get_winner(self):
        """Return the winner."""
        return self.winner


# ============================================================================
# Run Game and Record Trace
# ============================================================================

def run_game_with_trace(p0_cards, p1_cards, leading_card, remaining_deck,
                        starting_player, seed, label="Game"):
    """
    Run a game and return the complete event trace.
    """
    import random
    
    # Set random seed
    random.seed(seed)
    
    # Setup logging (quiet)
    logger.setLevel(logging.CRITICAL)
    
    # Create listener
    listener = TraceRecordingListener()
    
    # Create BProgram
    num_cards = len(p0_cards)
    bthreads = [
        game_manager(),
        deal_fixed_cards(p0_cards, p1_cards, leading_card, remaining_deck, 2, starting_player),  # Positional args
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
    print(f"  Running {label}...", end=" ", flush=True)
    try:
        b_program.run()
        trace = listener.get_trace()
        winner = listener.get_winner()
        print(f"Complete. Winner: P{winner}, Events: {len(trace)}")
        return trace, winner
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None


# ============================================================================
# Swap Player Labels in Trace
# ============================================================================

def swap_player_labels(trace):
    """
    Swap P0 ↔ P1 in all event names.
    
    Example:
      "p_0_card_5_red" → "p_1_card_5_red"
      "p_1_draw_card" → "p_0_draw_card"
      "deal_cards_to_player_0" → "deal_cards_to_player_1"
    """
    swapped = []
    for event in trace:
        # Swap p_0 ↔ p_1 and deal_cards_to_player_0 ↔ deal_cards_to_player_1
        if "p_0" in event or "player_0" in event:
            # Replace p_0 → p_X, p_1 → p_0, p_X → p_1 (three-way swap)
            swapped_event = event.replace("p_0", "p_X").replace("player_0", "player_X")
            swapped_event = swapped_event.replace("p_1", "p_0").replace("player_1", "player_0")
            swapped_event = swapped_event.replace("p_X", "p_1").replace("player_X", "player_1")
            swapped.append(swapped_event)
        elif "p_1" in event or "player_1" in event:
            # Just p_1 → p_0, player_1 → player_0
            swapped_event = event.replace("p_1", "p_0").replace("player_1", "player_0")
            swapped.append(swapped_event)
        else:
            # No player labels
            swapped.append(event)
    
    return swapped


# ============================================================================
# Compare Traces
# ============================================================================

def compare_traces(trace_a, trace_b_swapped, label_a="Game A", label_b="Game B"):
    """
    Compare two traces element by element.
    """
    print("\n" + "=" * 70)
    print("TRACE COMPARISON")
    print("=" * 70)
    
    print(f"\n{label_a}: {len(trace_a)} events")
    print(f"{label_b} (swapped): {len(trace_b_swapped)} events")
    
    if len(trace_a) != len(trace_b_swapped):
        print("\n❌ TRACES HAVE DIFFERENT LENGTHS")
        print(f"   {label_a}: {len(trace_a)} events")
        print(f"   {label_b}: {len(trace_b_swapped)} events")
        print("\n   The system is NOT symmetric!")
        return False
    
    # Compare element by element
    differences = []
    for i, (event_a, event_b) in enumerate(zip(trace_a, trace_b_swapped)):
        if event_a != event_b:
            differences.append((i, event_a, event_b))
    
    if not differences:
        print("\n✅ TRACES ARE IDENTICAL (after swapping player labels)")
        print("   The system exhibits PERFECT SYMMETRY!")
        return True
    else:
        print(f"\n❌ TRACES DIFFER at {len(differences)} positions")
        print("\n   First 10 differences:")
        for i, (pos, event_a, event_b) in enumerate(differences[:10]):
            print(f"   Position {pos}:")
            print(f"     {label_a}: {event_a}")
            print(f"     {label_b}: {event_b}")
        
        if len(differences) > 10:
            print(f"\n   ... and {len(differences) - 10} more differences")
        
        print("\n   The system is NOT perfectly symmetric!")
        return False


# ============================================================================
# Main Experiment
# ============================================================================

def run_trace_comparison_experiment():
    """
    Run the trace comparison experiment.
    """
    print("\n" + "=" * 70)
    print("TRACE COMPARISON EXPERIMENT")
    print("=" * 70)
    print()
    print("Testing if swapping player identities produces identical traces.")
    print()
    print("Protocol:")
    print("  Game A: P0 starts with Hand A, P1 has Hand B, seed=X")
    print("  Game B: P1 starts with Hand A, P0 has Hand B, seed=X")
    print("          (Complete identity swap)")
    print()
    print("Expected: Identical event sequences (with P0↔P1 swapped)")
    print("=" * 70)
    
    # Setup
    setup_logger()
    
    # Create fixed cards
    print("\nSetting up fixed cards...")
    fixed_cards = FixedCardsEvents()
    
    # Choose a seed
    seed = 42
    print(f"Using random seed: {seed}")
    
    input("\nPress Enter to run Game A...")
    
    # ========================================================================
    # GAME A: P0 starts with Hand A
    # ========================================================================
    
    print("\n" + "-" * 70)
    print("GAME A: P0 starts with Hand A, P1 has Hand B")
    print("-" * 70)
    
    config_a = fixed_cards.get_game_config(p0_gets_hand_A=True)
    trace_a, winner_a = run_game_with_trace(
        **config_a,
        starting_player=0,
        seed=seed,
        label="Game A"
    )
    
    print(f"Game A Result: P{winner_a} wins")
    
    input("\nPress Enter to run Game B...")
    
    # ========================================================================
    # GAME B: P1 starts with Hand A (identity swapped)
    # ========================================================================
    
    print("\n" + "-" * 70)
    print("GAME B: P1 starts with Hand A, P0 has Hand B (identity swapped)")
    print("-" * 70)
    
    # To swap identities, we need:
    # - P1 to have Hand A (so p0_gets_hand_A=False)
    # - P1 to start (starting_player=1)
    config_b = fixed_cards.get_game_config(p0_gets_hand_A=False)
    trace_b, winner_b = run_game_with_trace(
        **config_b,
        starting_player=1,
        seed=seed,
        label="Game B"
    )
    
    print(f"Game B Result: P{winner_b} wins")
    
    # ========================================================================
    # COMPARE TRACES
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("ORIGINAL TRACES (without swapping)")
    print("=" * 70)
    print("\nShowing the actual event names from each game:")
    print(f"\n{'Pos':<5} {'Game A (P0 starts)':<40} {'Game B (P1 starts)':<40}")
    print("-" * 90)
    for i in range(min(len(trace_a), len(trace_b))):
        event_a = trace_a[i] if i < len(trace_a) else "---"
        event_b = trace_b[i] if i < len(trace_b) else "---"
        print(f"{i:<5} {event_a:<40} {event_b:<40}")
    
    print("\n" + "=" * 70)
    print("SWAPPING PLAYER LABELS IN GAME B")
    print("=" * 70)
    print("\nConverting Game B trace to have same player perspective as Game A...")
    
    trace_b_swapped = swap_player_labels(trace_b)
    
    print("\nFirst 10 events:")
    print(f"\n{'Position':<10} {'Game A':<30} {'Game B (swapped)':<30}")
    print("-" * 70)
    for i in range(min(10, len(trace_a))):
        event_a = trace_a[i] if i < len(trace_a) else "---"
        event_b = trace_b_swapped[i] if i < len(trace_b_swapped) else "---"
        match = "✓" if event_a == event_b else "✗"
        print(f"{i:<10} {event_a:<30} {event_b:<30} {match}")
    
    # Print complete traces
    print("\n" + "=" * 70)
    print("COMPLETE TRACE COMPARISON")
    print("=" * 70)
    
    print(f"\nFull trace ({len(trace_a)} events):")
    print(f"\n{'Pos':<5} {'Game A':<40} {'Game B (swapped)':<40} {'Match':<5}")
    print("-" * 95)
    for i, (event_a, event_b) in enumerate(zip(trace_a, trace_b_swapped)):
        match = "✓" if event_a == event_b else "✗"
        print(f"{i:<5} {event_a:<40} {event_b:<40} {match:<5}")
    
    # Compare
    identical = compare_traces(trace_a, trace_b_swapped, "Game A", "Game B")
    
    # ========================================================================
    # WINNER ANALYSIS
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("WINNER ANALYSIS")
    print("=" * 70)
    
    print(f"\nGame A: P{winner_a} wins")
    print(f"Game B: P{winner_b} wins")
    
    # Expected: winner identities should be swapped
    if winner_a == 0 and winner_b == 1:
        print("\n✅ Winners are swapped (P0 → P1)")
        print("   This is expected for perfect symmetry!")
    elif winner_a == 1 and winner_b == 0:
        print("\n✅ Winners are swapped (P1 → P0)")
        print("   This is expected for perfect symmetry!")
    elif winner_a == winner_b:
        print(f"\n❌ Same player won both games (P{winner_a})")
        print("   This suggests asymmetry!")
    
    # ========================================================================
    # FINAL VERDICT
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    
    if identical and ((winner_a == 0 and winner_b == 1) or (winner_a == 1 and winner_b == 0)):
        print("\n✅ PERFECT SYMMETRY ACHIEVED")
        print()
        print("The system is truly symmetric:")
        print("  • Event traces are identical (with swapped labels)")
        print("  • Winner identities are swapped as expected")
        print("  • No hidden P0 vs P1 bias detected")
        print()
        print("This confirms your BP implementation treats P0 and P1 equally!")
    else:
        print("\n⚠️  ASYMMETRY DETECTED")
        print()
        if not identical:
            print("Event traces differ - the system behaves differently")
            print("based on player identity, not just starting position.")
        if winner_a == winner_b:
            print(f"Same player won both games - P{winner_a} has systematic advantage")
        print()
        print("Possible causes:")
        print("  • B-thread registration order creates bias")
        print("  • Event selection tiebreaking favors one player")
        print("  • Random seed affects players differently")
    
    print("=" * 70)


# ============================================================================
# Run Multiple Seeds
# ============================================================================

def run_multiple_seeds(num_seeds=10):
    """
    Test trace symmetry across multiple random seeds.
    """
    print("\n" + "=" * 70)
    print(f"MULTI-SEED TRACE COMPARISON ({num_seeds} seeds)")
    print("=" * 70)
    
    setup_logger()
    logger.setLevel(logging.CRITICAL)
    
    fixed_cards = FixedCardsEvents()
    
    results = []
    
    print(f"\nTesting {num_seeds} different random seeds...")
    print("-" * 70)
    
    for i in range(num_seeds):
        seed = i * 100  # Use spread-out seeds
        
        # Game A: P0 starts with Hand A
        config_a = fixed_cards.get_game_config(p0_gets_hand_A=True)
        trace_a, winner_a = run_game_with_trace(
            **config_a, starting_player=0, seed=seed, label=f"Seed {seed} A"
        )
        
        # Game B: P1 starts with Hand A
        config_b = fixed_cards.get_game_config(p0_gets_hand_A=False)
        trace_b, winner_b = run_game_with_trace(
            **config_b, starting_player=1, seed=seed, label=f"Seed {seed} B"
        )
        
        # Swap labels and compare
        trace_b_swapped = swap_player_labels(trace_b)
        identical = (trace_a == trace_b_swapped)
        winner_swapped = ((winner_a == 0 and winner_b == 1) or 
                         (winner_a == 1 and winner_b == 0))
        
        results.append({
            'seed': seed,
            'identical': identical,
            'winner_swapped': winner_swapped,
            'trace_len_a': len(trace_a),
            'trace_len_b': len(trace_b)
        })
        
        status = "✅" if (identical and winner_swapped) else "❌"
        print(f"  Seed {seed:3d}: {status} Traces {'match' if identical else 'differ':6s}, "
              f"Winners {'swapped' if winner_swapped else 'same':8s}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    perfect_symmetry = sum(1 for r in results if r['identical'] and r['winner_swapped'])
    
    print(f"\nPerfect symmetry: {perfect_symmetry}/{num_seeds} seeds ({perfect_symmetry/num_seeds*100:.1f}%)")
    
    if perfect_symmetry == num_seeds:
        print("\n✅ PERFECT SYMMETRY across all seeds!")
        print("   Your system is truly symmetric!")
    elif perfect_symmetry >= num_seeds * 0.9:
        print("\n⚠️  Mostly symmetric, but some edge cases fail")
    else:
        print("\n❌ System shows significant asymmetry")
    
    print("=" * 70)


# ============================================================================
# Main Menu
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║           TRACE COMPARISON EXPERIMENT                             ║
    ║                                                                   ║
    ║  Test if swapping player identities produces identical traces    ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print("Choose test:")
    print("  1. Single seed comparison (detailed analysis)")
    print("  2. Multiple seeds (10 comparisons)")
    print()
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        run_trace_comparison_experiment()
    elif choice == "2":
        run_multiple_seeds(num_seeds=10)
    else:
        print("Invalid choice. Running single seed test...")
        run_trace_comparison_experiment()
    
    input("\nPress Enter to exit...")