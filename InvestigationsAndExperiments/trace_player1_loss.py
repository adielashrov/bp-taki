"""Trace a specific seed from run_players_simulation() to see why Player 1 lost.

Usage: python InvestigationsAndExperiments/trace_player1_loss.py <seed> <starting_player>
"""
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from taki_simulation import (
    create_simulation_bprogram,
    SimulationListener,
    PlayerStrategyConfig,
)

logging.getLogger("TakiGame").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format="%(message)s", stream=sys.stdout)


class TraceListener(SimulationListener):
    def event_selected(self, b_program, event):
        super().event_selected(b_program, event)
        idx = len(self.events)
        print(f"  [{idx:>4}] {event.name}  (pri={getattr(event, 'priority', '?')})")


def run(seed: int, starting_player: int):
    listener = TraceListener()

    player_0_config = PlayerStrategyConfig(base_strategy="basic")
    player_1_config = PlayerStrategyConfig(base_strategy="basic", prefer_popular_color_regular_cards=True)

    b_program, actual_starting_player = create_simulation_bprogram(
        seed=seed,
        listener=listener,
        starting_player=starting_player,
        player_0_config=player_0_config,
        player_1_config=player_1_config,
    )

    print(f"seed={seed} actual_starting_player={actual_starting_player}")
    try:
        b_program.run()
    except AssertionError:
        if not (listener.get_deadlock() or listener.get_draw()):
            raise

    print("\n" + "=" * 60)
    if listener.get_winner() is not None:
        print(f"RESULT: Player {listener.get_winner()} wins!")
    elif listener.get_deadlock():
        print("RESULT: DEADLOCK")
    elif listener.get_draw():
        print("RESULT: DRAW")
    print(f"Total events: {len(listener.events)}")


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    starting_player = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    run(seed, starting_player)
