"""
Diagnostic script for seed=3 loss.
Patches strategic_taki_color_scores to print card_events
at the exact moment of each change_color decision.
"""
import sys
sys.path.insert(0, ".")

# ── import project modules ────────────────────────────────────────────────────
import bp_taki
import taki_simulation
from taki_simulation import create_simulation_bprogram, SimulationListener

# ── patch the color scoring function ─────────────────────────────────────────
original_build_change_color = bp_taki.build_strategic_change_color_requests
call_count = [0]

def patched_build_change_color_requests(card_events):
    call_count[0] += 1
    print(f"\n[PATCH] change_color selection #{call_count[0]}")
    print(f"[PATCH] card_events at decision time:")
    for e in card_events:
        print(f"         {e.name} (priority={e.priority})")
    scores = bp_taki.strategic_taki_color_scores(card_events)
    print(f"[PATCH] color scores: {scores}")
    order = bp_taki.strategic_taki_color_order(card_events)
    print(f"[PATCH] color order (best→worst): {order}")
    result = original_build_change_color(card_events)
    print(f"[PATCH] requests built:")
    for e in result:
        print(f"         {e.name} (priority={e.priority})")
    return result

bp_taki.build_strategic_change_color_requests = patched_build_change_color_requests

# ── run the game ──────────────────────────────────────────────────────────────
seed = 3
listener = SimulationListener()
b_program, starting_player = create_simulation_bprogram(
    seed=seed,
    listener=listener,
    player_0_strategy="basic",
    player_1_strategy="strategic",
    starting_player=-1,
)

try:
    b_program.run()
except AssertionError:
    if not (listener.get_deadlock() or listener.get_draw()):
        raise

print(f"\n[RESULT] winner={listener.get_winner()} | starting_player={starting_player} | events={listener.get_event_count()}")