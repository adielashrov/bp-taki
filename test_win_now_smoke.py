"""
Step 4: Controlled smoke tests for strategy_win_now_color_selection.

Tests:
  A. Unit tests for _find_win_now_color with explicit hands.
  B. Integration test: run seed 6 with DEBUG logging and verify
     the [WIN_NOW] message appears and the right color is selected.
"""

import logging
import sys
import io

sys.path.insert(0, ".")

from bp_taki import _find_win_now_color


# ── minimal BPEvent stand-in ──────────────────────────────────────────────────

class E:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"E({self.name})"


# ── Part A: unit tests for _find_win_now_color ────────────────────────────────

def test_basic_win_now():
    """All cards same color + TAKI of that color → return color."""
    hand = [E("p_1_taki_red"), E("p_1_card_3_red"), E("p_1_card_1_red")]
    assert _find_win_now_color(hand) == "red", "Should detect red win-now"
    print("PASS  test_basic_win_now")


def test_no_taki_no_win_now():
    """Same color but no TAKI → not a win-now (can't open chain)."""
    hand = [E("p_1_card_3_red"), E("p_1_card_1_red")]
    assert _find_win_now_color(hand) is None, "No TAKI → no win-now"
    print("PASS  test_no_taki_no_win_now")


def test_mixed_colors_no_win_now():
    """Cards of two colors → no win-now regardless of TAKI."""
    hand = [E("p_1_taki_red"), E("p_1_card_3_red"), E("p_1_card_1_blue")]
    assert _find_win_now_color(hand) is None, "Mixed colors → no win-now"
    print("PASS  test_mixed_colors_no_win_now")


def test_wild_cards_ignored():
    """SUPER_TAKI and CHANGE_COLOR are wildcards and should be ignored."""
    hand = [E("p_1_taki_green"), E("p_1_card_3_green"), E("p_1_super_taki")]
    assert _find_win_now_color(hand) == "green", "Wildcards ignored → green win-now"
    print("PASS  test_wild_cards_ignored")


def test_closed_taki_skipped():
    """_closed_taki is a virtual event; should be skipped by the checker."""
    hand = [E("p_1_taki_blue"), E("p_1_card_2_blue"), E("p_1_closed_taki")]
    assert _find_win_now_color(hand) == "blue", "_closed_taki skipped → blue win-now"
    print("PASS  test_closed_taki_skipped")


def test_single_taki_only():
    """Hand is just a TAKI card → win-now (it can chain immediately)."""
    hand = [E("p_1_taki_green")]
    assert _find_win_now_color(hand) == "green", "Single TAKI → win-now"
    print("PASS  test_single_taki_only")


def test_stop_card_same_color():
    """STOP card of the same color is a regular colored card — counts."""
    hand = [E("p_1_taki_red"), E("p_1_stop_red")]
    assert _find_win_now_color(hand) == "red", "STOP same color → win-now"
    print("PASS  test_stop_card_same_color")


def test_stop_card_different_color():
    """STOP card of different color blocks win-now."""
    hand = [E("p_1_taki_red"), E("p_1_stop_blue")]
    assert _find_win_now_color(hand) is None, "STOP different color → no win-now"
    print("PASS  test_stop_card_different_color")


# ── Part B: integration test on seed 6 ───────────────────────────────────────

def test_seed_6_win_now_logged():
    """
    Seed 6 is a known game where player 1 plays change_color with hand
    [p_1_card_3_blue, p_1_card_1_blue, p_1_taki_blue].
    Run with DEBUG logging captured and verify [WIN_NOW] appears and
    selected_blue is chosen.
    """
    import taki_simulation as sim

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)

    bp_logger = logging.getLogger("TakiGame")
    original_level = bp_logger.level
    bp_logger.setLevel(logging.DEBUG)
    bp_logger.addHandler(handler)

    try:
        listener = sim.SimulationListener()
        b_program, _ = sim.create_simulation_bprogram(
            seed=6,
            listener=listener,
            player_0_strategy="basic",
            player_1_strategy="strategic",
            player_0_block_super_taki=False,
            player_1_block_super_taki=False,
            player_1_win_now=True,
            starting_player=-1,
        )
        try:
            b_program.run()
        except AssertionError:
            if not (listener.get_deadlock() or listener.get_draw()):
                raise
    finally:
        bp_logger.removeHandler(handler)
        bp_logger.setLevel(original_level)

    log_output = log_stream.getvalue()

    assert "[WIN_NOW]" in log_output, (
        "Expected [WIN_NOW] log message — b-thread did not fire.\n"
        f"Log output:\n{log_output[-2000:]}"
    )
    assert "requesting selected_blue" in log_output, (
        "Expected win-now to request selected_blue.\n"
        f"Relevant log:\n{log_output[-2000:]}"
    )

    events = listener.get_events() if hasattr(listener, "get_events") else []
    print("PASS  test_seed_6_win_now_logged")
    print(f"      [WIN_NOW] log found: "
          + next(l for l in log_output.splitlines() if "[WIN_NOW]" in l))


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Part A: unit tests for _find_win_now_color ===\n")
    test_basic_win_now()
    test_no_taki_no_win_now()
    test_mixed_colors_no_win_now()
    test_wild_cards_ignored()
    test_closed_taki_skipped()
    test_single_taki_only()
    test_stop_card_same_color()
    test_stop_card_different_color()

    print("\n=== Part B: integration test on seed 6 ===\n")
    test_seed_6_win_now_logged()

    print("\nAll tests passed.")
