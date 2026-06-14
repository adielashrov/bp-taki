"""
Tests for prefer_stop_over_regular_cards_strategy.

These tests cover only the behavior guaranteed by the current implementation:
- prefer stop over same-color regular cards when both are legal
- allow same-color regular cards when the stop is not legal yet
- stay inactive when no stop card of that color is in hand
- avoid interfering with regular cards of other colors
"""

import unittest

import bppy as bp
from bppy.model.b_priority_event import BPEvent

from bp_taki import prefer_stop_over_regular_cards_strategy, run_bp_program
from tests.helpers.fixed_alternating_dealer import fixed_alternating_dealer
from tests.helpers.make_test_bprogram import make_test_bprogram
from tests.helpers.trace_listener import TraceListener
from tests.helpers.trace_utils import write_trace_to_file


def run_bp_with_trace(test_name, bp_program, listener):
    """Run the b-program and surface any exception as a rich AssertionError."""
    try:
        run_bp_program(bp_program, configure_logger=False)
    except Exception as exc:
        trace_path = write_trace_to_file(test_name, listener.events)
        raise AssertionError(
            f"BP run failed with {type(exc).__name__}: {exc}\n"
            f"Trace written to: {trace_path}\n"
            f"Trace tail: {listener.tail(50)}"
        ) from exc


def p0_played_cards(events):
    """Return P0 card-play events, excluding draw_card / no_more_cards / closed_taki."""
    return [
        event_name
        for event_name in events
        if event_name.startswith("p_0_")
        and not event_name.endswith("_draw_card")
        and not event_name.endswith("_no_more_cards")
        and not event_name.endswith("_closed_taki")
    ]


@bp.thread
def end_game_after_p0_plays(target_count):
    """Terminate the test run once P0 has played the requested number of cards."""
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    played = 0
    while played < target_count:
        event = yield bp.sync(waitFor=bp.All())
        if (
            event.name.startswith("p_0_")
            and not event.name.endswith("_draw_card")
            and not event.name.endswith("_no_more_cards")
            and not event.name.endswith("_closed_taki")
        ):
            played += 1

    yield bp.sync(request=BPEvent("end_game", priority=10.0))


class TestPreferStopStrategy(unittest.TestCase):
    def test_prefers_stop_over_regular_card_when_both_legal(self):
        """
        When P0 holds both stop_red and card_4_red, and the leading card is
        card_5_red (red playable), the strategy must force stop_red out first.
        """
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp_program = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_stop_red", "p_card_4_red"],
                ["p_card_1_red", "p_card_1_green"],
                "p_card_5_red",
            ),
            listener=listener,
            num_cards=2,
            extra_bthreads=[
                prefer_stop_over_regular_cards_strategy(0, "red"),
                end_game_after_p0_plays(2),
            ],
        )

        run_bp_with_trace(test_name, bp_program, listener)

        p0_moves = p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertEqual(
            p0_moves,
            ["p_0_stop_red", "p_0_card_4_red"],
            msg=(
                f"Strategy should force stop_red before card_4_red.\n"
                f"Trace written to: {trace_path}\n"
                f"Actual P0 moves: {p0_moves}"
            ),
        )

    def test_regular_card_allowed_when_no_stop_in_hand(self):
        """
        When P0 does not hold a stop_red card, the strategy should be inactive
        and P0 can freely play regular red cards.
        """
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp_program = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_card_4_red", "p_card_1_red"],
                ["p_card_1_red", "p_card_3_blue"],
                "p_card_4_blue",
            ),
            listener=listener,
            num_cards=2,
            extra_bthreads=[
                prefer_stop_over_regular_cards_strategy(0, "red"),
                end_game_after_p0_plays(2),
            ],
        )

        run_bp_with_trace(test_name, bp_program, listener)

        p0_moves = p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertEqual(
            p0_moves,
            ["p_0_card_4_red", "p_0_card_1_red"],
            msg=(
                "With no stop card, P0 should play regular red cards without interference.\n"
                f"Trace written to: {trace_path}\n"
                f"Actual P0 moves: {p0_moves}"
            ),
        )

    def test_regular_card_allowed_when_stop_is_not_legal(self):
        """
        When P0 holds stop_red and card_4_red, but the leading card is
        card_4_blue, card_4_red is legal by number while stop_red is not legal.
        """
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp_program = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_stop_red", "p_card_4_red"],
                ["p_card_1_red", "p_card_1_green"],
                "p_card_4_blue",
            ),
            listener=listener,
            num_cards=2,
            extra_bthreads=[
                prefer_stop_over_regular_cards_strategy(0, "red"),
                end_game_after_p0_plays(1),
            ],
        )

        run_bp_with_trace(test_name, bp_program, listener)

        p0_moves = p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertGreater(
            len(p0_moves),
            0,
            msg=(
                "P0 should be able to play at least one card.\n"
                f"Trace written to: {trace_path}\n"
                f"Actual P0 moves: {p0_moves}"
            ),
        )
        self.assertEqual(
            p0_moves[0],
            "p_0_card_4_red",
            msg=(
                "card_4_red should be the first P0 move when stop_red is not legal.\n"
                f"Trace written to: {trace_path}\n"
                f"Actual P0 moves: {p0_moves}"
            ),
        )

    def test_strategy_does_not_affect_other_colors(self):
        """
        The strategy targets only the specified color. P0 must remain free to
        play regular cards of other colors even while holding stop_red.
        """
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp_program = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_stop_red", "p_card_4_blue"],
                ["p_card_1_red", "p_card_1_green"],
                "p_card_5_blue",
            ),
            listener=listener,
            num_cards=2,
            extra_bthreads=[
                prefer_stop_over_regular_cards_strategy(0, "red"),
                end_game_after_p0_plays(1),
            ],
        )

        run_bp_with_trace(test_name, bp_program, listener)

        p0_moves = p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertIn(
            "p_0_card_4_blue",
            p0_moves,
            msg=(
                f"card_4_blue must be playable even while stop_red is in hand.\n"
                f"Trace written to: {trace_path}\n"
                f"Actual P0 moves: {p0_moves}"
            ),
        )
        self.assertNotIn(
            "p_0_stop_red",
            p0_moves,
            msg=(
                f"stop_red should never be played when the leading card is blue.\n"
                f"Trace written to: {trace_path}\n"
                f"Actual P0 moves: {p0_moves}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
