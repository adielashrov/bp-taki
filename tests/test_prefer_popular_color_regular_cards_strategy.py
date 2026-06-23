import unittest

import bppy as bp
from bppy.model.b_priority_event import BPEvent

from bp_taki import prefer_popular_color_regular_cards_strategy, run_bp_program
from tests.helpers.fixed_alternating_dealer import fixed_alternating_dealer
from tests.helpers.make_test_bprogram import make_test_bprogram
from tests.helpers.trace_listener import TraceListener
from tests.helpers.trace_utils import write_trace_to_file


def run_bp_with_trace(test_name, bp_program, listener):
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


class TestPreferPopularColorRegularCardsStrategy(unittest.TestCase):
    def test_legal_stop_beats_same_color_regular(self):
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp_program = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_stop_red", "p_card_4_red", "p_card_1_red"],
                ["p_card_1_green", "p_card_3_blue", "p_card_5_green"],
                "p_card_5_red",
            ),
            listener=listener,
            num_cards=3,
            extra_bthreads=[
                prefer_popular_color_regular_cards_strategy(0, 3),
                end_game_after_p0_plays(2),
            ],
        )

        run_bp_with_trace(test_name, bp_program, listener)

        p0_moves = p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)
        self.assertGreater(len(p0_moves), 0, msg=f"Trace written to: {trace_path}")
        self.assertEqual("p_0_stop_red", p0_moves[0], msg=f"Actual P0 moves: {p0_moves}")

    def test_regular_card_prefers_color_with_more_follow_up_value(self):
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp_program = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_card_4_red", "p_card_4_blue", "p_card_1_blue"],
                ["p_card_1_green", "p_card_3_blue", "p_card_5_green"],
                "p_card_4_green",
            ),
            listener=listener,
            num_cards=3,
            extra_bthreads=[
                prefer_popular_color_regular_cards_strategy(0, 3),
                end_game_after_p0_plays(2),
            ],
        )

        run_bp_with_trace(test_name, bp_program, listener)

        p0_moves = p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)
        self.assertGreater(len(p0_moves), 0, msg=f"Trace written to: {trace_path}")
        self.assertEqual("p_0_card_4_blue", p0_moves[0], msg=f"Actual P0 moves: {p0_moves}")


if __name__ == "__main__":
    unittest.main()
