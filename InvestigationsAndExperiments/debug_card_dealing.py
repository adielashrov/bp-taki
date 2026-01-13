"""
Debug script to verify card dealing alternation between players.
Tracks the exact order of card distribution.
"""

import sys
import bppy as bp
import random
import logging
from pathlib import Path

# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy

from bp_taki import (
    game_manager,
    deal_cards,
    player_behavior,
    enforce_turns,
    enforce_card_placement_rules,
    identify_deadlock,
    identify_livelock,
    verify_turn_alternation,
    NUM_OF_CARDS
)


class CardDealingDebugListener:
    """Listener that tracks the exact order of card dealing."""
    
    def __init__(self):
        self.events = []
        self.dealing_sequence = []
        self.player_0_cards = []
        self.player_1_cards = []
        self.currently_dealing_to = None
        
    def starting(self, b_program): pass
    def started(self, b_program): pass
    def super_step_done(self, b_program): pass
    def ended(self, b_program): pass
    def assertion_failed(self, b_program): pass
    def halted(self, b_program): pass
    
    def event_selected(self, b_program, event):
        """Record each selected event."""
        self.events.append(event.name)
        
        # Track which player is about to receive a card
        if event.name == "deal_cards_to_player_0":
            self.currently_dealing_to = 0
            self.dealing_sequence.append(("signal", 0))
        elif event.name == "deal_cards_to_player_1":
            self.currently_dealing_to = 1
            self.dealing_sequence.append(("signal", 1))
        
        # Track the actual card being dealt
        elif event.name.startswith("deal_p_") and self.currently_dealing_to is not None:
            card_name = event.name.replace("deal_p_", "")
            self.dealing_sequence.append(("card", self.currently_dealing_to, card_name))
            
            if self.currently_dealing_to == 0:
                self.player_0_cards.append(card_name)
            else:
                self.player_1_cards.append(card_name)
        
        # Stop tracking when dealing is finished
        elif event.name == "finished_dealing_cards_to_players":
            self.currently_dealing_to = None
    
    def print_dealing_report(self):
        """Print a detailed report of the dealing sequence."""
        print("\n" + "=" * 70)
        print("CARD DEALING DEBUG REPORT")
        print("=" * 70)
        
        print("\n📋 DEALING SEQUENCE (in order):")
        print("-" * 70)
        
        for i, entry in enumerate(self.dealing_sequence, 1):
            if entry[0] == "signal":
                player = entry[1]
                print(f"  {i:2d}. 🔔 Signal: deal_cards_to_player_{player}")
            elif entry[0] == "card":
                player = entry[1]
                card = entry[2]
                print(f"  {i:2d}. 🃏 Card dealt to Player {player}: {card}")
        
        print("\n" + "-" * 70)
        print(f"\n👤 PLAYER 0 RECEIVED {len(self.player_0_cards)} CARDS:")
        for i, card in enumerate(self.player_0_cards, 1):
            print(f"  {i}. {card}")
        
        print(f"\n👤 PLAYER 1 RECEIVED {len(self.player_1_cards)} CARDS:")
        for i, card in enumerate(self.player_1_cards, 1):
            print(f"  {i}. {card}")
        
        # Analyze alternation pattern
        print("\n🔍 ALTERNATION ANALYSIS:")
        print("-" * 70)
        
        card_sequence = [entry for entry in self.dealing_sequence if entry[0] == "card"]
        
        if len(card_sequence) >= 2:
            alternates = True
            for i in range(len(card_sequence) - 1):
                current_player = card_sequence[i][1]
                next_player = card_sequence[i + 1][1]
                
                if current_player == next_player:
                    alternates = False
                    print(f"  ❌ Cards {i+1} and {i+2} both went to Player {current_player}")
                    print(f"     Card {i+1}: {card_sequence[i][2]}")
                    print(f"     Card {i+2}: {card_sequence[i+1][2]}")
            
            if alternates:
                print("  ✅ PERFECT ALTERNATION! Cards alternate between players.")
            else:
                print("  ❌ FAILED: Some consecutive cards went to the same player.")
        
        # Check signal pattern
        print("\n🔔 SIGNAL PATTERN:")
        print("-" * 70)
        signal_sequence = [entry for entry in self.dealing_sequence if entry[0] == "signal"]
        
        signal_pattern = [entry[1] for entry in signal_sequence]
        print(f"  Pattern: {' -> '.join(map(str, signal_pattern))}")
        
        # Expected pattern for fair dealing: 0,1,0,1,0,1...
        expected_pattern = []
        for i in range(NUM_OF_CARDS):
            expected_pattern.extend([0, 1])
        
        if signal_pattern == expected_pattern:
            print("  ✅ Signal pattern matches expected alternation!")
        else:
            print("  ❌ Signal pattern does NOT match expected alternation.")
            print(f"  Expected: {' -> '.join(map(str, expected_pattern))}")
        
        print("\n" + "=" * 70)


def run_debug_game(seed=42, num_cards=NUM_OF_CARDS):
    """Run a single game with detailed card dealing tracking."""
    
    print(f"\n🎲 Starting debug game with seed={seed}, num_cards={num_cards}")
    
    # Set random seed
    random.seed(seed)
    
    # Configure logging to see dealing events
    logging.basicConfig(level=logging.WARNING)  # Keep other logs quiet
    
    # Create debug listener
    listener = CardDealingDebugListener()
    
    # Create b-threads
    bthreads = [
        game_manager(),
        deal_cards(2, num_cards),
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        enforce_turns(2, 0),
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation()
    ]
    
    # Create and run the BProgram
    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=listener
    )
    
    try:
        print("🎮 Running game (this may take a moment)...\n")
        b_program.run()
        print("✅ Game completed successfully!")
    except Exception as e:
        print(f"❌ Error during game execution: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Print the detailed report
    listener.print_dealing_report()


if __name__ == "__main__":
    # Run with different seeds to verify consistency
    print("\n" + "🧪 TESTING CARD DEALING ALTERNATION " + "🧪")
    print("=" * 70)
    
    # Test with a couple different seeds
    for seed in [42, 100, 999]:
        run_debug_game(seed=seed, num_cards=NUM_OF_CARDS)
        print("\n")
