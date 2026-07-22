"""
Sweep `prefer_popular_color_boost_probability` on the actual shipped
prefer_popular_color_regular_cards_strategy_original (bp_taki.py:1107),
via taki_simulation.run_simulation / PlayerStrategyConfig — no parameterized
copies, this exercises the real production code path.

boost_probability=0.0 should reproduce the no-op baseline (~50%).
boost_probability=1.0 should reproduce the fully-deterministic result
measured earlier (~47.8% on seeds 0-4999).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from taki_simulation import run_simulation, PlayerStrategyConfig, SimulationStats


def sweep(probabilities, num_games=2000, start_seed=0):
    print(f"Sweeping {len(probabilities)} boost_probability candidates over {num_games} games each.")
    print("-" * 70)

    rows = []
    for p in probabilities:
        player_0_config = PlayerStrategyConfig(base_strategy="basic")
        player_1_config = PlayerStrategyConfig(
            base_strategy="basic",
            prefer_popular_color_regular_cards=True,
            prefer_popular_color_boost_probability=p,
        )

        stats = run_simulation(
            num_games=num_games,
            start_seed=start_seed,
            starting_player=-1,
            balanced_starting_players=True,
            player_0_config=player_0_config,
            player_1_config=player_1_config,
            silent=True,
            progress_interval=10**9,  # suppress progress prints
        )

        ci_lo, ci_hi = SimulationStats.wilson_ci(stats.player_1_wins, stats.total_completed)
        rows.append((p, stats.player_1_wins, stats.player_0_wins, stats.deadlocks, stats.draws))
        print(
            f"boost_probability={p:4.2f} | "
            f"P1 wins: {stats.player_1_wins:4d}/{stats.total_completed} "
            f"({stats.win_rate(1):5.1f}%) [{ci_lo*100:5.1f}%, {ci_hi*100:5.1f}%] | "
            f"P0 wins: {stats.player_0_wins:4d} | deadlocks: {stats.deadlocks} | draws: {stats.draws}"
        )

    return rows


if __name__ == "__main__":
    probabilities = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    sweep(probabilities, num_games=2000, start_seed=0)
