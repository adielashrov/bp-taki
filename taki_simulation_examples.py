#!/usr/bin/env python3
"""
Simple example of running Taki game simulations.

This script demonstrates basic usage of the simulation module.
"""

from taki_simulation import run_simulation, save_results


def example_basic_simulation():
    """Run a basic simulation with 50 games."""
    print("Example 1: Basic simulation (50 games)")
    print("=" * 60)
    
    stats = run_simulation(
        num_games=50,
        start_seed=0,
        player_0_strategy="taki_and_super_taki",
        player_1_strategy="basic",
        silent=True
    )
    
    print("\n" + stats.summary())
    save_results(stats, "example_basic_simulation.json")


def example_strategy_comparison():
    """Compare different strategies."""
    print("\n\nExample 2: Strategy Comparison")
    print("=" * 60)
    
    configurations = [
        ("basic", "basic", "Basic vs Basic"),
        ("taki", "basic", "Taki vs Basic"),
        ("taki_and_super_taki", "basic", "Taki+SuperTaki vs Basic"),
        ("taki_and_super_taki", "taki", "Taki+SuperTaki vs Taki"),
    ]
    
    results = []
    
    for p0_strat, p1_strat, label in configurations:
        print(f"\n{label}")
        print("-" * 60)
        
        stats = run_simulation(
            num_games=30,
            start_seed=1000,  # Use consistent seeds for fair comparison
            player_0_strategy=p0_strat,
            player_1_strategy=p1_strat,
            silent=True,
            progress_interval=15
        )
        
        print(stats.summary())
        results.append((label, stats))
    
    # Print comparison table
    print("\n\nSTRATEGY COMPARISON SUMMARY")
    print("=" * 60)
    print(f"{'Configuration':<35} {'P0 Wins':>10} {'P1 Wins':>10}")
    print("-" * 60)
    
    for label, stats in results:
        print(f"{label:<35} {stats.player_0_wins:>10} {stats.player_1_wins:>10}")


def example_large_simulation():
    """Run a larger simulation for more robust statistics."""
    print("\n\nExample 3: Large Simulation (200 games)")
    print("=" * 60)
    
    stats = run_simulation(
        num_games=200,
        start_seed=42,
        player_0_strategy="taki_and_super_taki",
        player_1_strategy="taki",
        silent=True,
        progress_interval=25
    )
    
    print("\n" + stats.summary())
    
    # Show some detailed statistics
    print("\nDetailed Statistics:")
    print("-" * 60)
    print(f"Shortest game: {min(r.event_count for r in stats.results)} events")
    print(f"Longest game:  {max(r.event_count for r in stats.results)} events")
    print(f"Average game:  {stats.average_events_per_game:.1f} events")
    
    save_results(stats, "example_large_simulation.json")


def example_seed_exploration():
    """Explore how different seed ranges affect outcomes."""
    print("\n\nExample 4: Seed Range Exploration")
    print("=" * 60)
    
    seed_ranges = [
        (0, "Seeds 0-29"),
        (100, "Seeds 100-129"),
        (500, "Seeds 500-529"),
        (1000, "Seeds 1000-1029"),
    ]
    
    print(f"\n{'Seed Range':<20} {'P0 Wins':>10} {'P1 Wins':>10} {'P0 Win %':>12}")
    print("-" * 60)
    
    for start_seed, label in seed_ranges:
        stats = run_simulation(
            num_games=30,
            start_seed=start_seed,
            player_0_strategy="taki_and_super_taki",
            player_1_strategy="basic",
            silent=True,
            progress_interval=30
        )
        
        print(f"{label:<20} {stats.player_0_wins:>10} {stats.player_1_wins:>10} "
              f"{stats.win_rate(0):>11.1f}%")


def example_block_super_taki_strategy():
    """Compare performance with and without the block_super_taki strategy."""
    print("\n\nExample 5: Block Super TAKI Strategy")
    print("=" * 60)
    print("\nThis example tests the strategy_block_super_taki_during_regular_taki b-thread")
    print("which blocks Super TAKI from being played during regular TAKI sequences.")
    print()
    
    configurations = [
        {
            "label": "Baseline: Taki+SuperTaki vs Basic",
            "p0_strategy": "taki_and_super_taki",
            "p1_strategy": "basic",
            "p0_block": False,
            "p1_block": False
        },
        {
            "label": "P0 blocks Super TAKI during regular TAKI",
            "p0_strategy": "taki_and_super_taki",
            "p1_strategy": "basic",
            "p0_block": True,
            "p1_block": False
        },
        {
            "label": "Both players: Taki strategy with blocking",
            "p0_strategy": "taki",
            "p1_strategy": "taki",
            "p0_block": True,
            "p1_block": True
        },
        {
            "label": "P0: Full strategy + block, P1: Basic",
            "p0_strategy": "taki_and_super_taki",
            "p1_strategy": "basic",
            "p0_block": True,
            "p1_block": False
        }
    ]
    
    print(f"{'Configuration':<45} {'P0 Wins':>10} {'P1 Wins':>10} {'P0 %':>8}")
    print("-" * 75)
    
    for config in configurations:
        stats = run_simulation(
            num_games=50,
            start_seed=2000,  # Use consistent seeds
            player_0_strategy=config["p0_strategy"],
            player_1_strategy=config["p1_strategy"],
            player_0_block_super_taki=config["p0_block"],
            player_1_block_super_taki=config["p1_block"],
            silent=True,
            progress_interval=50
        )
        
        print(f"{config['label']:<45} {stats.player_0_wins:>10} {stats.player_1_wins:>10} "
              f"{stats.win_rate(0):>7.1f}%")
    
    print("\nNote: The blocking strategy prevents Super TAKI from being used during")
    print("regular TAKI sequences, forcing more strategic play of TAKI cards.")


if __name__ == "__main__":
    # Run all examples
    # Uncomment the ones you want to run
    
    example_basic_simulation()
    
    # example_strategy_comparison()
    
    # example_large_simulation()
    
    # example_seed_exploration()
    
    # example_block_super_taki_strategy()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)