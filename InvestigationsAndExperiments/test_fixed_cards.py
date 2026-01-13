"""
Step-by-Step Test: Verify Fixed Card Dealing

This script tests that:
1. Player 0 receives exactly Hand A
2. Player 1 receives exactly Hand B
3. The leading card is correct
4. The game runs successfully
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import from your existing modules
from bp_taki import (
    setup_logger,
    game_manager,
    player_behavior,
    enforce_turns,
    enforce_card_placement_rules,
    identify_deadlock,
    identify_livelock,
    verify_turn_alternation,
    NUM_OF_CARDS,
    logger
)

# Import BPpy
import bppy as bp
from bppy.model.b_priority_event import BPEvent
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy
from log_b_program_runner_listener import LogBProgramRunnerListener

# Import fixed cards
from fixed_cards_dealing import FixedCardsEvents, deal_fixed_cards

# ============================================================================
# STEP 1: Create a Custom Listener to Track What Cards Players Receive
# ============================================================================

class CardTrackingListener:
    """
    Listener that tracks which cards each player receives.
    """
    
    def __init__(self):
        self.p0_cards = []
        self.p1_cards = []
        self.leading_card = None
        self.winner = None
        self.game_started = False
        self.cards_dealt = False
        
    def starting(self, b_program):
        print("[LISTENER] BP program starting...")
    
    def started(self, b_program):
        print("[LISTENER] BP program started")
    
    def event_selected(self, b_program, event):
        """Track each event that occurs."""
        event_name = event.name
        
        # Track which player is currently being dealt to (BEFORE card dealing)
        if event_name == "deal_cards_to_player_0":
            self.current_dealing_player = 0
            print("[LISTENER] Now dealing to Player 0...")
        elif event_name == "deal_cards_to_player_1":
            self.current_dealing_player = 1
            print("[LISTENER] Now dealing to Player 1...")
        
        # Track when dealing is complete (BEFORE game starts)
        elif event_name == "finished_dealing_cards_to_players":
            self.cards_dealt = True
            self.current_dealing_player = None  # Stop tracking cards after initial deal
            print("[LISTENER] Initial card dealing complete!")
        
        # Track card dealing events (ONLY during initial dealing, not during game)
        elif not self.cards_dealt and (event_name.startswith("deal_p_card_") or 
                                       event_name.startswith("deal_p_stop") or 
                                       event_name.startswith("deal_p_taki") or 
                                       event_name.startswith("deal_p_change")):
            # Extract the card name (remove "deal_p_" prefix)
            card_name = event_name.replace("deal_p_", "")
            
            # Determine which player received it based on context
            # We need to track the last "deal_cards_to_player_X" event
            if hasattr(self, 'current_dealing_player') and self.current_dealing_player is not None:
                if self.current_dealing_player == 0:
                    self.p0_cards.append(card_name)
                    print(f"[LISTENER] P0 received: {card_name}")
                elif self.current_dealing_player == 1:
                    self.p1_cards.append(card_name)
                    print(f"[LISTENER] P1 received: {card_name}")
        
        # Track leading card
        elif event_name.startswith("leading_deal_p_"):
            card_name = event_name.replace("leading_deal_p_", "")
            self.leading_card = card_name
            print(f"[LISTENER] Leading card: {card_name}")
        
        # Track game start
        elif event_name == "start_game":
            self.game_started = True
            print("[LISTENER] Game started!")
        
        # Track winner
        elif event_name == "p_0_no_more_cards":
            self.winner = 0
            print("[LISTENER] Player 0 wins!")
        elif event_name == "p_1_no_more_cards":
            self.winner = 1
            print("[LISTENER] Player 1 wins!")
        
        elif event_name == "end_game":
            print("[LISTENER] Game ended")
    
    def ended(self, b_program):
        print("[LISTENER] BP program ended")
    
    def halted(self, b_program):
        print("[LISTENER] BP program halted")
    
    def assertion_failed(self, b_program):
        print("[LISTENER] Assertion failed!")
    
    def super_step_done(self, b_program):
        pass  # Too verbose for this test
    
    def print_summary(self):
        """Print what cards each player received."""
        print("\n" + "=" * 70)
        print("CARD DEALING SUMMARY")
        print("=" * 70)
        print(f"Player 0 received {len(self.p0_cards)} cards:")
        for i, card in enumerate(self.p0_cards, 1):
            print(f"  {i}. {card}")
        print()
        print(f"Player 1 received {len(self.p1_cards)} cards:")
        for i, card in enumerate(self.p1_cards, 1):
            print(f"  {i}. {card}")
        print()
        print(f"Leading card: {self.leading_card}")
        print()
        print(f"Winner: Player {self.winner}")
        print("=" * 70)


# ============================================================================
# STEP 2: Create the Test Function
# ============================================================================

def test_fixed_card_dealing():
    """
    Test that fixed cards are dealt correctly.
    
    This test verifies:
    1. P0 receives Hand A (4 specific cards)
    2. P1 receives Hand B (4 specific cards)
    3. The leading card is placed correctly
    4. The game runs to completion
    """
    
    print("\n" + "=" * 70)
    print("TEST: FIXED CARD DEALING VERIFICATION")
    print("=" * 70)
    
    # Step 2.1: Create the fixed cards configuration
    print("\nStep 1: Creating fixed cards configuration...")
    fixed_cards = FixedCardsEvents()
    
    # Step 2.2: Print what we EXPECT to happen
    print("\nStep 2: Expected card distribution:")
    print("\n  Hand A (for P0):")
    for card in fixed_cards.hand_A:
        print(f"    - {card.name}")
    
    print("\n  Hand B (for P1):")
    for card in fixed_cards.hand_B:
        print(f"    - {card.name}")
    
    print(f"\n  Leading card: {fixed_cards.leading_card.name}")
    
    # Step 2.3: Validate the configuration
    print("\nStep 3: Validating configuration...")
    if not fixed_cards.validate():
        print("ERROR: Configuration invalid!")
        return False
    print("  OK: Configuration is valid")
    
    # Step 2.4: Get the configuration for Game 1 (P0 gets Hand A)
    print("\nStep 4: Getting Game 1 configuration (P0 gets Hand A)...")
    config = fixed_cards.get_game_config(p0_gets_hand_A=True)
    
    # Step 2.5: Create the listener to track cards
    print("\nStep 5: Creating card tracking listener...")
    card_listener = CardTrackingListener()
    
    # Step 2.6: Create the BProgram
    print("\nStep 6: Creating BProgram with fixed cards...")
    num_cards = len(config['p0_cards'])
    
    bthreads = [
        game_manager(),
        deal_fixed_cards(
            config['p0_cards'],      # positional arg 1
            config['p1_cards'],      # positional arg 2
            config['leading_card'],  # positional arg 3
            config['remaining_deck'] # positional arg 4
        ),
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        enforce_turns(2, 0),  # num_of_players=2, starting_player=0
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation()
    ]
    
    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=card_listener
    )
    
    # Step 2.7: Setup logger (optional - set to False for less output)
    print("\nStep 7: Configuring logger...")
    setup_logger()
    logger.setLevel(logging.WARNING)  # Reduce log noise for this test
    
    # Step 2.8: Run the game!
    print("\nStep 8: Running the game...")
    print("-" * 70)
    
    try:
        b_program.run()
        print("-" * 70)
        print("OK: Game completed successfully")
    except Exception as e:
        print("-" * 70)
        print(f"ERROR: Game failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2.9: Print what actually happened
    card_listener.print_summary()
    
    # Step 2.10: Verify the cards match expectations
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    expected_p0 = [card.name for card in fixed_cards.hand_A]
    expected_p1 = [card.name for card in fixed_cards.hand_B]
    expected_leading = fixed_cards.leading_card.name
    
    actual_p0 = card_listener.p0_cards
    actual_p1 = card_listener.p1_cards
    actual_leading = card_listener.leading_card
    
    all_correct = True
    
    # Check P0's cards
    print("\nPlayer 0 cards:")
    if sorted(actual_p0) == sorted(expected_p0):
        print("  OK: P0 received correct cards")
    else:
        print("  ERROR: P0 received wrong cards!")
        print(f"    Expected: {expected_p0}")
        print(f"    Got:      {actual_p0}")
        all_correct = False
    
    # Check P1's cards
    print("\nPlayer 1 cards:")
    if sorted(actual_p1) == sorted(expected_p1):
        print("  OK: P1 received correct cards")
    else:
        print("  ERROR: P1 received wrong cards!")
        print(f"    Expected: {expected_p1}")
        print(f"    Got:      {actual_p1}")
        all_correct = False
    
    # Check leading card
    print("\nLeading card:")
    if actual_leading == expected_leading:
        print("  OK: Leading card is correct")
    else:
        print("  ERROR: Leading card is wrong!")
        print(f"    Expected: {expected_leading}")
        print(f"    Got:      {actual_leading}")
        all_correct = False
    
    # Final result
    print("\n" + "=" * 70)
    if all_correct:
        print("SUCCESS: All cards dealt correctly!")
        print("=" * 70)
        return True
    else:
        print("FAILURE: Some cards were incorrect")
        print("=" * 70)
        return False


# ============================================================================
# STEP 3: Run the Test
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║           FIXED CARD DEALING TEST                                 ║
    ║                                                                   ║
    ║  This test verifies that deal_fixed_cards correctly delivers     ║
    ║  predetermined hands to each player.                             ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to run the test...")
    
    success = test_fixed_card_dealing()
    
    if success:
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("Now that you've verified the basic dealing works, you can:")
        print("1. Run the card-swap test (Game 1 vs Game 2)")
        print("2. Test with different starting players")
        print("3. Run multiple trials for statistical confidence")
        print("=" * 70)
    else:
        print("\nPlease fix the issues before proceeding to the card-swap test.")
    
    input("\nPress Enter to exit...")