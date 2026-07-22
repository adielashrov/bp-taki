"""Replication check: does the ~2.5pp drop seen when boosting dominant/minority
color priority (sweep_prefer_popular_color_priority.py) hold on a disjoint seed
block with more games, or does it look like PRNG-perturbation noise from
EventPrioritySelectionStrategy.select() consuming the shared `random` stream?
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sweep_prefer_popular_color_priority import sweep, sweep_inverse

if __name__ == "__main__":
    print("=== Dominant-boost replication (seed block 50000+, N=5000) ===")
    sweep([10.0, 8.0], num_games=5000, start_seed=50000)

    print()
    print("=== Minority-boost replication (seed block 50000+, N=5000) ===")
    sweep_inverse([10.0, 8.0], num_games=5000, start_seed=50000)
