"""
Test the color dominance strategy
"""
from taki_simulation import run_simulation

if __name__ == "__main__":
    print("Testing Color Dominance Strategy")
    print("=" * 60)
    
    # Test 1: Color dominance vs basic
    print("\nTest 1: Color Dominance (P0) vs Basic (P1)")
    print("-" * 60)
    stats1 = run_simulation(
        num_games=1000,
        start_seed=0,
        starting_player=-1,
        player_0_strategy="color_dominance",
        player_1_strategy="basic",
        silent=False,
        progress_interval=10
    )
    
    summary1 = stats1.summary(
        player_0_strategy="color_dominance",
        player_1_strategy="basic"
    )
    print("\n" + summary1)
    
    # Test 2: Color dominance vs TAKI strategy
    print("\n\nTest 2: Color Dominance (P0) vs TAKI Strategy (P1)")
    print("-" * 60)
    stats2 = run_simulation(
        num_games=1000,
        start_seed=100,
        starting_player=-1,
        player_0_strategy="color_dominance",
        player_1_strategy="taki_and_super_taki",
        silent=False,
        progress_interval=10
    )
    
    summary2 = stats2.summary(
        player_0_strategy="color_dominance",
        player_1_strategy="taki_and_super_taki"
    )
    print("\n" + summary2)
    
    # Test 3: Both players using color dominance
    print("\n\nTest 3: Color Dominance (P0) vs Color Dominance (P1)")
    print("-" * 60)
    stats3 = run_simulation(
        num_games=1000,
        start_seed=200,
        starting_player=-1,
        player_0_strategy="color_dominance",
        player_1_strategy="color_dominance",
        silent=False,
        progress_interval=10
    )
    
    summary3 = stats3.summary(
        player_0_strategy="color_dominance",
        player_1_strategy="color_dominance"
    )
    print("\n" + summary3)
