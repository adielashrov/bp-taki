"""
Integration Guide: Using deal_fixed_cards for Card-Swap Testing

This guide shows you how to integrate the fixed card dealing system
into your existing bp_taki.py code.
"""

# ============================================================================
# STEP 1: Import the fixed cards module
# ============================================================================

from fixed_cards_dealing import (
    FixedCardsEvents,
    deal_fixed_cards,
    create_fixed_deal_bprogram
)


# ============================================================================
# STEP 2: Create a simple test function
# ============================================================================

def run_single_fixed_game(p0_cards, p1_cards, leading_card, remaining_deck, starting_player=0):
    """
    Run a single game with fixed cards and return the winner.
    
    Returns
    -------
    int or None
        Winner (0 or 1) or None if draw/deadlock
    """
    from bp_taki import setup_logger
    import logging
    
    # Setup logger
    setup_logger()
    logger = logging.getLogger("TakiGame")
    
    # Create BProgram
    bp_program = create_fixed_deal_bprogram(
        p0_cards=p0_cards,
        p1_cards=p1_cards,
        leading_card=leading_card,
        remaining_deck=remaining_deck,
        starting_player=starting_player,
        num_cards=len(p0_cards),  # Important: tell player_behavior how many cards
        player_0_strategy="basic",
        player_1_strategy="basic"
    )
    
    # Create a listener to track the winner
    from taki_simulation import SimulationListener
    listener = SimulationListener()
    
    # Replace the listener
    bp_program.listener = listener
    
    # Run the game
    logger.info("=" * 70)
    logger.info("STARTING FIXED-CARD GAME")
    logger.info("=" * 70)
    bp_program.run()
    
    # Get the winner
    winner = listener.get_winner()
    logger.info("=" * 70)
    logger.info(f"GAME ENDED - Winner: Player {winner}")
    logger.info("=" * 70)
    
    return winner


# ============================================================================
# STEP 3: Run the card-swap symmetry test
# ============================================================================

def test_card_swap_symmetry():
    """
    Main test function: Run paired games with swapped cards.
    """
    print("\n" + "=" * 70)
    print("CARD-SWAP SYMMETRY TEST")
    print("=" * 70)
    print()
    print("This test checks if the system has bias based on player position.")
    print()
    print("Protocol:")
    print("  Game 1: P0 gets Hand A, P1 gets Hand B")
    print("  Game 2: P0 gets Hand B, P1 gets Hand A (swapped)")
    print()
    print("Expected result (fair system):")
    print("  - Different players win the two games")
    print("  - Hand quality determines winner, not player identity")
    print()
    print("Bias indicator:")
    print("  - Same player wins both games")
    print("  - Player position matters more than cards")
    print()
    input("Press Enter to continue...")
    
    # Create fixed cards
    fixed_cards = FixedCardsEvents()
    
    # Validate
    print("\n" + "=" * 70)
    print("VALIDATING CARD CONFIGURATION")
    print("=" * 70)
    fixed_cards.print_summary()
    
    if not fixed_cards.validate():
        print("\nERROR: Invalid card configuration!")
        return
    
    print("\nOK: Configuration is valid")
    input("\nPress Enter to run Game 1...")
    
    # Game 1: P0 gets hand A
    print("\n" + "=" * 70)
    print("GAME 1: P0 gets Hand A, P1 gets Hand B")
    print("=" * 70)
    print("P0's hand:")
    for card in fixed_cards.hand_A:
        print(f"  - {card.name}")
    print("P1's hand:")
    for card in fixed_cards.hand_B:
        print(f"  - {card.name}")
    print()
    
    config1 = fixed_cards.get_game_config(p0_gets_hand_A=True)
    winner1 = run_single_fixed_game(
        **config1,
        starting_player=0  # Both games start with P0
    )
    
    print(f"\nGame 1 Result: Player {winner1} wins")
    input("\nPress Enter to run Game 2...")
    
    # Game 2: P0 gets hand B (swapped)
    print("\n" + "=" * 70)
    print("GAME 2: P0 gets Hand B, P1 gets Hand A (SWAPPED)")
    print("=" * 70)
    print("P0's hand (was P1's in Game 1):")
    for card in fixed_cards.hand_B:
        print(f"  - {card.name}")
    print("P1's hand (was P0's in Game 1):")
    for card in fixed_cards.hand_A:
        print(f"  - {card.name}")
    print()
    
    config2 = fixed_cards.get_game_config(p0_gets_hand_A=False)
    winner2 = run_single_fixed_game(
        **config2,
        starting_player=0  # Both games start with P0
    )
    
    print(f"\nGame 2 Result: Player {winner2} wins")
    
    # Analyze results
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print(f"Game 1: P0 had Hand A → Player {winner1} won")
    print(f"Game 2: P0 had Hand B → Player {winner2} won")
    print()
    
    if winner1 is None or winner2 is None:
        print("WARNING: One or both games ended without a clear winner (draw/deadlock)")
        print("Result: INCONCLUSIVE")
    elif winner1 != winner2:
        print("OK: SYMMETRIC RESULT")
        print()
        print("Different players won when hands were swapped.")
        print("This suggests:")
        print("  - Hand quality determines the winner")
        print("  - No systematic bias based on player position")
        print("  - The system treats P0 and P1 fairly")
    else:
        print("WARNING: ASYMMETRIC RESULT - BIAS DETECTED!")
        print()
        print(f"Player {winner1} won BOTH games despite having different hands.")
        print("This suggests:")
        print("  - Player position creates systematic advantage")
        print("  - Likely causes:")
        print("    * B-thread registration order bias")
        print("    * Event selection tiebreaking favors one player")
        print("    * Some other implementation asymmetry")
        print()
        print("RECOMMENDATION:")
        print("  - Investigate b-thread registration order")
        print("  - Check EventPrioritySelectionStrategy tiebreaking")
        print("  - Consider using DeterministicEventPrioritySelectionStrategy")
    
    print("=" * 70)


# ============================================================================
# STEP 4: Advanced test with multiple starting positions
# ============================================================================

def test_card_swap_with_both_starting_positions():
    """
    More comprehensive test: Try both starting positions.
    
    This tests 4 combinations:
    1. P0 starts, P0 has hand A
    2. P0 starts, P0 has hand B
    3. P1 starts, P0 has hand A
    4. P1 starts, P0 has hand B
    """
    fixed_cards = FixedCardsEvents()
    
    print("\n" + "=" * 70)
    print("COMPREHENSIVE CARD-SWAP TEST")
    print("=" * 70)
    print("Testing all combinations of:")
    print("  - Hand assignment (A→P0 or B→P0)")
    print("  - Starting player (P0 or P1)")
    print("=" * 70)
    
    results = {}
    
    for starting_player in [0, 1]:
        for p0_gets_A in [True, False]:
            config = fixed_cards.get_game_config(p0_gets_hand_A=p0_gets_A)
            
            hand_label = "A" if p0_gets_A else "B"
            print(f"\nRunning: P{starting_player} starts, P0 has hand {hand_label}")
            
            winner = run_single_fixed_game(
                **config,
                starting_player=starting_player
            )
            
            key = (starting_player, p0_gets_A)
            results[key] = winner
            print(f"  Result: Player {winner} wins")
    
    # Analyze results
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ANALYSIS")
    print("=" * 70)
    print("\nResults table:")
    print()
    print("                    | P0 has Hand A | P0 has Hand B")
    print("--------------------+---------------+---------------")
    print(f"P0 starts          | P{results[(0, True)]} wins       | P{results[(0, False)]} wins")
    print(f"P1 starts          | P{results[(1, True)]} wins       | P{results[(1, False)]} wins")
    print()
    
    # Check for symmetry
    # When hands are swapped, winners should flip (if fair)
    p0_starts_A = results[(0, True)]
    p0_starts_B = results[(0, False)]
    p1_starts_A = results[(1, True)]
    p1_starts_B = results[(1, False)]
    
    print("Checking symmetry patterns:")
    print()
    
    # Pattern 1: When P0 starts, swapping hands should flip winner
    if p0_starts_A is not None and p0_starts_B is not None:
        if p0_starts_A != p0_starts_B:
            print("OK: When P0 starts, different winners with swapped hands")
        else:
            print("WARNING: When P0 starts, same player wins regardless of hands!")
    
    # Pattern 2: When P1 starts, swapping hands should flip winner
    if p1_starts_A is not None and p1_starts_B is not None:
        if p1_starts_A != p1_starts_B:
            print("OK: When P1 starts, different winners with swapped hands")
        else:
            print("WARNING: When P1 starts, same player wins regardless of hands!")
    
    # Pattern 3: Check if starting player always wins
    starting_player_wins = [
        results[(0, True)] == 0,   # P0 starts, P0 wins?
        results[(0, False)] == 0,  # P0 starts, P0 wins?
        results[(1, True)] == 1,   # P1 starts, P1 wins?
        results[(1, False)] == 1   # P1 starts, P1 wins?
    ]
    
    if all(starting_player_wins):
        print()
        print("PATTERN: Starting player ALWAYS wins")
        print("  This indicates strong first-mover advantage")
    
    print("=" * 70)


# ============================================================================
# STEP 5: Quick usage example
# ============================================================================

if __name__ == "__main__":
    print("""
    Card-Swap Symmetry Test
    =======================
    
    Choose a test:
    1. Simple test (2 games, P0 always starts)
    2. Comprehensive test (4 games, all combinations)
    """)
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_card_swap_symmetry()
    elif choice == "2":
        test_card_swap_with_both_starting_positions()
    else:
        print("Invalid choice. Running simple test...")
        test_card_swap_symmetry()