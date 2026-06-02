import unittest

from bp_taki import most_popular_color_selection_strategy, run_bp_program
from tests.helpers.fixed_alternating_dealer import fixed_alternating_dealer
from tests.helpers.make_test_bprogram import make_test_bprogram
from tests.helpers.trace_listener import TraceListener
from tests.helpers.trace_utils import write_trace_to_file


class TestMostPopularColorSelectionStrategy(unittest.TestCase):
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
    def selected_colors(events):
        return [event for event in events if event.startswith("selected_")]

    def test_selects_most_common_remaining_color(self):
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_change_color", "p_card_1_green", "p_card_7_green"],
                ["p_card_1_green", "p_card_7_green", "p_card_4_red"],
                "p_card_5_blue",
            ),
            listener=listener,
            num_cards=3,
            extra_bthreads=[most_popular_color_selection_strategy(0, 3)],
        )

        self.run_bp_with_trace(test_name, bp, listener)

        selected = self.selected_colors(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertGreater(
            len(selected),
            0,
            msg=f"Expected a selected_<color> event. Trace written to: {trace_path}",
        )
        self.assertEqual(
            selected[0],
            "selected_green",
            msg=f"Expected green to be selected from remaining hand. Trace written to: {trace_path}",
        )

    def test_tie_breaks_by_colors_order(self):
        test_name = self.id().split(".")[-1]
        listener = TraceListener()

        bp = make_test_bprogram(
            dealer_bthread=fixed_alternating_dealer(
                ["p_change_color", "p_card_1_red", "p_card_7_green"],
                ["p_card_1_red", "p_card_7_red", "p_card_4_blue"],
                "p_card_5_blue",
            ),
            listener=listener,
            num_cards=3,
            extra_bthreads=[most_popular_color_selection_strategy(0, 3)],
        )

        self.run_bp_with_trace(test_name, bp, listener)

        selected = self.selected_colors(listener.events)
        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertGreater(
            len(selected),
            0,
            msg=f"Expected a selected_<color> event. Trace written to: {trace_path}",
        )
        self.assertEqual(
            selected[0],
            "selected_red",
            msg=f"Expected ties to prefer COLORS order. Trace written to: {trace_path}",
        )


if __name__ == "__main__":
    unittest.main()
