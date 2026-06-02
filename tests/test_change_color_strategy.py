import unittest

from bp_taki import change_color_strategy, run_bp_program
from tests.helpers.fixed_alternating_dealer import fixed_alternating_dealer
from tests.helpers.make_test_bprogram import make_test_bprogram
from tests.helpers.trace_listener import TraceListener
from tests.helpers.trace_utils import write_trace_to_file


class TestChangeColorStrategy(unittest.TestCase):
    def run_bp_with_trace(self, test_name, bp, listener):
        try:
            run_bp_program(bp, configure_logger=False)
        except Exception as exc:
            trace_path = write_trace_to_file(test_name, listener.events)
            raise AssertionError(
                f"BP run failed with {type(exc).__name__}: {exc}\n"
                f"Trace written to: {trace_path}\n"
                f"Trace tail: {listener.tail(50)}"
            ) from exc

    @staticmethod
    def p0_played_cards(events):
        return [
            event
            for event in events
            if event.startswith("p_0_")
            and not event.endswith("_draw_card")
            and not event.endswith("_no_more_cards")
            and not event.endswith("_closed_taki")
        ]

    def test_prefers_regular_card_over_change_color_when_legal(self):
        """Verify combined behavior of player_behavior and change_color_strategy.

        player_behavior executes the moves, while change_color_strategy adds
        lower-priority change_color requests. This test asserts the emergent
        P0 play order produced by both b-threads together.
        """
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_change_color", "p_card_4_blue"],
                ["p_card_4_red", "p_card_1_green"],
                "p_card_5_blue",
            ),
            listener=listener,
            num_cards=2,
            extra_bthreads=[change_color_strategy(0, 2)],
        )

        self.run_bp_with_trace(test_name, bp, listener)

        p0_moves = self.p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertEqual(
            p0_moves,
            ["p_0_card_4_blue", "p_0_change_color"],
            msg=f"Unexpected P0 move sequence. Trace written to: {trace_path}",
        )

    def test_uses_change_color_when_it_is_only_legal_move(self):
        """Verify combined behavior of player_behavior and change_color_strategy.

        player_behavior executes the moves, while change_color_strategy adds
        lower-priority change_color requests. This test asserts that the resulting 
        P0 move sequence is exactly [change_color] when no other legal play exists.
        """
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_change_color"],
                ["p_card_1_green"],
                "p_card_5_blue",
            ),
            listener=listener,
            num_cards=1,
            extra_bthreads=[change_color_strategy(0, 1)],
        )

        self.run_bp_with_trace(test_name, bp, listener)

        p0_moves = self.p0_played_cards(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertEqual(
            p0_moves,
            ["p_0_change_color"],
            msg=f"change_color should be the only P0 move. Trace written to: {trace_path}",
        )
