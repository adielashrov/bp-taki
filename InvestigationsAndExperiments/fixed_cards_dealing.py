"""
Fixed Card Dealing Implementation for Taki Card-Swap Test

This module provides functionality to deal predetermined hands to players
for testing symmetry and identifying sources of bias in the BP system.
"""


import bppy as bp
from bppy.model.b_priority_event import BPEvent
import logging
import sys
from pathlib import Path

# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


logger = logging.getLogger("TakiGame")

# Constants from bp_taki.py
COLORS = ["red", "blue", "green"]


class FixedCardsEvents:
    """
    Fixed card configuration for symmetry testing.
    
    This class defines specific hands for testing whether the BP system
    exhibits bias based on player position (P0 vs P1) independent of cards.
    
    Test protocol:
    - Game 1: P0 gets hand_A, P1 gets hand_B
    - Game 2: P0 gets hand_B, P1 gets hand_A (swapped)
    
    Expected result (fair system): Different players win each game
    Bias indicator: Same player wins both games
    """
    
    def __init__(self):
        # Hand A: Balanced mix of regular cards and one action card
        self.hand_A = [
            BPEvent(name="card_5_red", priority=10.0),
            BPEvent(name="card_3_blue", priority=10.0),
            BPEvent(name="card_3_green", priority=10.0),
            BPEvent(name="stop_red", priority=10.0),
        ]
        
        # Hand B: Balanced mix including TAKI and change_color
        self.hand_B = [
            BPEvent(name="card_5_green", priority=10.0),
            BPEvent(name="stop_green", priority=10.0),
            BPEvent(name="taki_blue", priority=10.0),
            BPEvent(name="change_color", priority=10.0),
        ]
        
        # Leading card: 5 of blue (both hands can play on this)
        self.leading_card = BPEvent(name="card_5_blue", priority=10.0)
        
        # Remaining deck (excluding dealt cards)
        self.remaining_deck = self._create_remaining_deck()
    
    def _create_full_deck(self):
        """Create the complete Taki deck with all duplicates."""
        cards = []
        colors = COLORS
        numbers = ["1", "3", "4", "5"]
        
        # Regular numbered cards - 1 of each
        for color in colors:
            for number in numbers:
                cards.append(BPEvent(name=f"card_{number}_{color}", priority=10.0))
        
        # Stop cards - 2 of each color
        for color in colors:
            for _ in range(2):
                cards.append(BPEvent(name=f"stop_{color}", priority=10.0))
        
        # Change color - 2 total
        for _ in range(2):
            cards.append(BPEvent(name="change_color", priority=10.0))
        
        # Regular TAKI - 2 of each color
        for color in colors:
            for _ in range(2):
                cards.append(BPEvent(name=f"taki_{color}", priority=10.0))
        
        # Super TAKI - 2 total
        for _ in range(2):
            cards.append(BPEvent(name="super_taki", priority=10.0))
        
        return cards
    
    def _create_remaining_deck(self):
        """Create deck with all cards EXCEPT those already dealt."""
        all_cards = self._create_full_deck()
        dealt_cards = self.hand_A + self.hand_B + [self.leading_card]
        
        # Remove dealt cards from deck
        remaining = all_cards.copy()
        for dealt_card in dealt_cards:
            for i, deck_card in enumerate(remaining):
                if deck_card.name == dealt_card.name:
                    remaining.pop(i)
                    break  # Remove only one copy
        
        return remaining
    
    def get_game_config(self, p0_gets_hand_A: bool):
        """
        Get card configuration for a specific game.
        
        Parameters
        ----------
        p0_gets_hand_A : bool
            If True, P0 gets hand_A and P1 gets hand_B
            If False, P0 gets hand_B and P1 gets hand_A (swapped)
        
        Returns
        -------
        dict
            Configuration with keys: 'p0_cards', 'p1_cards', 'leading_card', 'remaining_deck'
        """
        if p0_gets_hand_A:
            return {
                'p0_cards': self.hand_A,
                'p1_cards': self.hand_B,
                'leading_card': self.leading_card,
                'remaining_deck': self.remaining_deck
            }
        else:
            return {
                'p0_cards': self.hand_B,  # Swapped!
                'p1_cards': self.hand_A,  # Swapped!
                'leading_card': self.leading_card,
                'remaining_deck': self.remaining_deck
            }
    
    def validate(self):
        """Validate that the deck is consistent and complete."""
        # Check no card appears more than expected
        all_dealt = self.hand_A + self.hand_B + [self.leading_card] + self.remaining_deck
        
        card_counts = {}
        for card in all_dealt:
            card_counts[card.name] = card_counts.get(card.name, 0) + 1
        
        errors = []
        warnings = []
        
        # Check regular cards (should be 1 each)
        for color in COLORS:
            for number in ["1", "3", "4", "5"]:
                card_name = f"card_{number}_{color}"
                count = card_counts.get(card_name, 0)
                if count != 1:
                    errors.append(f"{card_name}: expected 1, got {count}")
        
        # Check stop cards (should be 2 of each color)
        for color in COLORS:
            card_name = f"stop_{color}"
            count = card_counts.get(card_name, 0)
            if count != 2:
                errors.append(f"{card_name}: expected 2, got {count}")
        
        # Check change_color (should be 2)
        count = card_counts.get("change_color", 0)
        if count != 2:
            errors.append(f"change_color: expected 2, got {count}")
        
        # Check taki cards (should be 2 of each color)
        for color in COLORS:
            card_name = f"taki_{color}"
            count = card_counts.get(card_name, 0)
            if count != 2:
                errors.append(f"{card_name}: expected 2, got {count}")
        
        # Check super_taki (should be 2)
        count = card_counts.get("super_taki", 0)
        if count != 2:
            errors.append(f"super_taki: expected 2, got {count}")
        
        if errors:
            print("ERROR: Deck validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("OK: Deck validation passed")
            return True
    
    def print_summary(self):
        """Print a summary of the card configuration."""
        print("=" * 60)
        print("FIXED CARDS CONFIGURATION")
        print("=" * 60)
        print(f"Hand A ({len(self.hand_A)} cards):")
        for card in self.hand_A:
            print(f"  - {card.name}")
        print()
        print(f"Hand B ({len(self.hand_B)} cards):")
        for card in self.hand_B:
            print(f"  - {card.name}")
        print()
        print(f"Leading card: {self.leading_card.name}")
        print()
        print(f"Remaining deck: {len(self.remaining_deck)} cards")
        print("=" * 60)


@bp.thread
def deal_fixed_cards(p0_cards, p1_cards, leading_card, remaining_deck, num_of_players=2, starting_player=0):
    """
    Deal predetermined cards to players for symmetry testing.
    
    This b-thread replaces the normal deal_cards b-thread to provide
    complete control over which cards each player receives.
    
    IMPORTANT: Cards are dealt in STARTING-PLAYER ORDER to ensure symmetry
    when swapping player identities. This is critical for trace comparison.
    
    Parameters
    ----------
    p0_cards : list[BPEvent]
        Cards to deal to player 0
    p1_cards : list[BPEvent]
        Cards to deal to player 1
    leading_card : BPEvent
        The card to place on the discard pile
    remaining_deck : list[BPEvent]
        Cards available for drawing during the game
    num_of_players : int, optional
        Number of players (default: 2)
    starting_player : int, optional
        Which player goes first (0 or 1). Default is 0.
        Cards are dealt to starting player FIRST for symmetry.
    
    Notes
    -----
    The dealing follows the same protocol as the normal deal_cards b-thread:
    1. Wait for "start_dealing_cards_to_players"
    2. Deal cards to STARTING PLAYER first, then other player
    3. Signal "finished_dealing_cards_to_players"
    4. Wait for "deal_leading_card"
    5. Deal the leading card
    6. Handle subsequent draw requests from remaining deck
    """
    logger.info(f"[FIXED_DEAL] Starting fixed card dealing (starting_player={starting_player})")
    logger.info(f"[FIXED_DEAL] P0 will receive {len(p0_cards)} cards")
    logger.info(f"[FIXED_DEAL] P1 will receive {len(p1_cards)} cards")
    logger.info(f"[FIXED_DEAL] Leading card: {leading_card.name}")
    logger.info(f"[FIXED_DEAL] Remaining deck: {len(remaining_deck)} cards")
    
    # Wait for the game to request card dealing
    yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))
    logger.info("[FIXED_DEAL] Received request to start dealing")
    
    # Determine dealing order based on starting player
    if starting_player == 0:
        # P0 starts: deal to P0 first, then P1
        first_player = 0
        second_player = 1
        first_cards = p0_cards
        second_cards = p1_cards
    else:
        # P1 starts: deal to P1 first, then P0
        first_player = 1
        second_player = 0
        first_cards = p1_cards
        second_cards = p0_cards
    
    logger.info(f"[FIXED_DEAL] Dealing order: P{first_player} first (starting), then P{second_player}")
    
    # Deal to first player (starting player)
    yield bp.sync(request=BPEvent(f"deal_cards_to_player_{first_player}", priority=10.0))
    logger.info(f"[FIXED_DEAL] Dealing {len(first_cards)} cards to Player {first_player}:")
    for i, card in enumerate(first_cards):
        deal_event = BPEvent(f"deal_p_{card.name}", priority=card.priority)
        logger.info(f"[FIXED_DEAL]   {i+1}. {card.name}")
        yield bp.sync(request=deal_event)
    
    # Deal to second player (non-starting player)
    yield bp.sync(request=BPEvent(f"deal_cards_to_player_{second_player}", priority=10.0))
    logger.info(f"[FIXED_DEAL] Dealing {len(second_cards)} cards to Player {second_player}:")
    for i, card in enumerate(second_cards):
        deal_event = BPEvent(f"deal_p_{card.name}", priority=card.priority)
        logger.info(f"[FIXED_DEAL]   {i+1}. {card.name}")
        yield bp.sync(request=deal_event)
    
    # Signal that initial dealing is complete
    yield bp.sync(request=BPEvent("finished_dealing_cards_to_players", priority=10.0))
    logger.info("[FIXED_DEAL] Finished dealing initial hands")
    
    # Deal the leading card
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    logger.info(f"[FIXED_DEAL] Dealing leading card: {leading_card.name}")
    deal_event = BPEvent(f"deal_p_{leading_card.name}", priority=leading_card.priority)
    yield bp.sync(request=deal_event)
    yield bp.sync(request=BPEvent(f"leading_deal_p_{leading_card.name}", priority=10.0))
    yield bp.sync(request=BPEvent("finished_leading_card", priority=10.0))
    logger.info("[FIXED_DEAL] Leading card placed")
    
    # Handle draw requests during the game
    deal_cards_events = [BPEvent(f"deal_p_{c.name}", priority=c.priority) for c in remaining_deck]
    original_deck_size = len(deal_cards_events)
    
    logger.info(f"[FIXED_DEAL] Ready to handle draws from {original_deck_size}-card deck")
    
    draw_count = 0
    while True:
        # Wait for a player to request a card
        last_event = yield bp.sync(waitFor=[BPEvent("p_0_draw_card"), BPEvent("p_1_draw_card")])
        player_id = "0" if "p_0" in last_event.name else "1"
        draw_count += 1
        
        logger.info(f"[FIXED_DEAL] Player {player_id} requests card #{draw_count}. Deck size: {len(deal_cards_events)}")
        
        # Refill deck if empty (infinite deck simulation)
        if not deal_cards_events:
            logger.warning("=" * 70)
            logger.warning("[FIXED_DEAL] DECK EMPTY -> REFILLING DECK")
            logger.warning("=" * 70)
            deal_cards_events = [BPEvent(f"deal_p_{c.name}", priority=c.priority) for c in remaining_deck]
            logger.warning(f"[FIXED_DEAL] Deck refilled! New size = {len(deal_cards_events)} cards")
            logger.warning(f"[FIXED_DEAL] Available cards in new deck:")
            for i, card in enumerate(deal_cards_events[:5], 1):
                logger.warning(f"[FIXED_DEAL]   {i}. {card.name.replace('deal_p_', '')}")
            if len(deal_cards_events) > 5:
                logger.warning(f"[FIXED_DEAL]   ... and {len(deal_cards_events) - 5} more cards")
            logger.warning("=" * 70)
        
        # Deal the card
        last_event = yield bp.sync(request=deal_cards_events)
        card_dealt = last_event.name.replace("deal_p_", "")
        logger.info(f"[FIXED_DEAL] Player {player_id} receives: {card_dealt}. Deck now: {len(deal_cards_events)-1} cards")
        deal_cards_events.remove(last_event)


def create_fixed_deal_bprogram(
    p0_cards,
    p1_cards,
    leading_card,
    remaining_deck,
    starting_player=0,
    num_cards=4,
    player_0_strategy="basic",
    player_1_strategy="basic"
):
    """
    Create a BProgram with fixed card dealing for symmetry testing.
    
    This function creates a complete BProgram but replaces the normal
    deal_cards b-thread with deal_fixed_cards to control the exact
    cards each player receives.
    
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
    starting_player : int, optional
        Which player goes first (0 or 1)
    num_cards : int, optional
        Number of cards each player receives (for player_behavior initialization)
    player_0_strategy : str, optional
        Strategy for player 0: "basic", "taki", "taki_and_super_taki"
    player_1_strategy : str, optional
        Strategy for player 1: "basic", "taki", "taki_and_super_taki"
    
    Returns
    -------
    bp.BProgram
        Configured behavioral program with fixed card dealing
    
    Notes
    -----
    This function assumes the following imports and functions are available:
    - game_manager, player_behavior, enforce_turns, enforce_card_placement_rules
    - identify_deadlock, identify_livelock, verify_turn_alternation
    - EventPrioritySelectionStrategy
    - LogBProgramRunnerListener (or other listener)
    """
    from bp_taki import (
        game_manager,
        player_behavior,
        enforce_turns,
        enforce_card_placement_rules,
        identify_deadlock,
        identify_livelock,
        verify_turn_alternation,
        basic_strategy_taki,
        basic_strategy_taki_and_super_taki,
    )
    from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy
    from log_b_program_runner_listener import LogBProgramRunnerListener
    
    logger.info("=" * 70)
    logger.info("[FIXED_DEAL_BPROGRAM] Creating BProgram with fixed cards")
    logger.info(f"[FIXED_DEAL_BPROGRAM] Starting player: Player {starting_player}")
    logger.info(f"[FIXED_DEAL_BPROGRAM] P0 strategy: {player_0_strategy}")
    logger.info(f"[FIXED_DEAL_BPROGRAM] P1 strategy: {player_1_strategy}")
    logger.info("=" * 70)
    
    # Start with core b-threads
    bthreads = [
        game_manager(),
        deal_fixed_cards(p0_cards, p1_cards, leading_card, remaining_deck, 2, starting_player),  # ← Positional args
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        enforce_turns(2, starting_player),
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation()
    ]
    
    # Add strategy b-threads if not basic
    if player_0_strategy == "taki":
        bthreads.append(basic_strategy_taki(0, num_cards))
    elif player_0_strategy == "taki_and_super_taki":
        bthreads.append(basic_strategy_taki_and_super_taki(0, num_cards))
    elif player_0_strategy != "basic":
        raise ValueError(f"Unknown strategy for player 0: {player_0_strategy}")
    
    if player_1_strategy == "taki":
        bthreads.append(basic_strategy_taki(1, num_cards))
    elif player_1_strategy == "taki_and_super_taki":
        bthreads.append(basic_strategy_taki_and_super_taki(1, num_cards))
    elif player_1_strategy != "basic":
        raise ValueError(f"Unknown strategy for player 1: {player_1_strategy}")
    
    # Create BProgram
    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=LogBProgramRunnerListener(logger=logger)
    )
    
    return b_program


# ============================================================================
# Example Usage and Testing
# ============================================================================

def run_card_swap_test_example():
    """
    Example of how to run the card swap symmetry test.
    """
    print("\n" + "=" * 70)
    print("CARD SWAP SYMMETRY TEST")
    print("=" * 70)
    
    # Create fixed cards configuration
    fixed_cards = FixedCardsEvents()
    
    # Validate the configuration
    fixed_cards.print_summary()
    if not fixed_cards.validate():
        print("ERROR: Card configuration is invalid!")
        return
    
    print("\n" + "=" * 70)
    print("TEST PROTOCOL")
    print("=" * 70)
    print("Game 1: P0 gets Hand A, P1 gets Hand B")
    print("Game 2: P0 gets Hand B, P1 gets Hand A (swapped)")
    print()
    print("Expected (if system is fair):")
    print("  - Different players should win the two games")
    print("  - Advantage should flip when hands are swapped")
    print()
    print("Bias indicator:")
    print("  - Same player wins both games despite swapped hands")
    print("=" * 70)
    
    # Game 1: P0 gets hand A
    print("\n" + "=" * 70)
    print("GAME 1: P0 gets Hand A, P1 gets Hand B")
    print("=" * 70)
    config1 = fixed_cards.get_game_config(p0_gets_hand_A=True)
    
    # Create and run BProgram (you'll need to implement result tracking)
    # bp1 = create_fixed_deal_bprogram(**config1, starting_player=0)
    # bp1.run()
    # result1 = get_winner(bp1)  # You need to implement this
    
    print("(Implementation needed: create and run BProgram)")
    result1_winner = None  # Placeholder
    
    # Game 2: P0 gets hand B (swapped)
    print("\n" + "=" * 70)
    print("GAME 2: P0 gets Hand B, P1 gets Hand A (SWAPPED)")
    print("=" * 70)
    config2 = fixed_cards.get_game_config(p0_gets_hand_A=False)
    
    # Create and run BProgram
    # bp2 = create_fixed_deal_bprogram(**config2, starting_player=0)
    # bp2.run()
    # result2 = get_winner(bp2)  # You need to implement this
    
    print("(Implementation needed: create and run BProgram)")
    result2_winner = None  # Placeholder
    
    # Compare results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Game 1 winner: Player {result1_winner}")
    print(f"Game 2 winner: Player {result2_winner}")
    print()
    
    if result1_winner is not None and result2_winner is not None:
        if result1_winner != result2_winner:
            print("OK: SYMMETRIC - Different players won with swapped hands")
            print("     This suggests the system is fair!")
        else:
            print("WARNING: ASYMMETRIC - Same player won both games")
            print("         This indicates a bias based on player position!")
    else:
        print("(Awaiting implementation of game execution)")


if __name__ == "__main__":
    # Run example test
    run_card_swap_test_example()