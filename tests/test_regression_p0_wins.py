# tests/test_regression_p0_wins.py

import unittest

from tests.helpers.fixed_dealer import fixed_dealer
from tests.helpers.fixed_draw_pile import fixed_draw_pile
from tests.helpers.trace_listener import TraceListener
from tests.helpers.make_test_bprogram import make_test_bprogram

from bp_taki import run_bp_program
from tests.helpers.trace_utils import write_trace_to_file
NUM_CARDS = 1  # must match how many cards your fixed_dealer gives each player

class TestRegressionP0Wins(unittest.TestCase):
    
    def run_bp_with_trace(self, bp, listener):
        try:
            run_bp_program(bp, configure_logger=False)
        except Exception as e:
            trace_path = write_trace_to_file("test_p0_wins_simple", listener.events)
            raise AssertionError(
                f"BP run failed with {type(e).__name__}: {e}\n"
                f"Trace tail: {listener.tail(50)}"
            ) from e
    
    def test_p0_wins_simple(self):
        
        test_name = self.id().split(".")[-1]
        
        leading = "p_card_1_red"

        # P0 can play and (ideally) win immediately
        p0 = ["p_card_5_red"]

        # P1 has no playable card on red (assuming only same-color/number/type is allowed)
        p1 = ["p_card_7_blue"]

        self.assertEqual(len(p0), NUM_CARDS)
        self.assertEqual(len(p1), NUM_CARDS)

        # When P1 draws, force a red card so the game continues deterministically
        draw_thread = fixed_draw_pile(
            [],                 # p0_draws
            ["p_card_9_red"],   # p1_draws
        )

        listener = TraceListener()
        dealer = fixed_dealer(p0, p1, leading)

        bp = make_test_bprogram(
            dealer_bthread=dealer,
            listener=listener,
            num_cards=NUM_CARDS,
            extra_bthreads=[draw_thread],
        )

        self.run_bp_with_trace(bp, listener)

        trace_path = write_trace_to_file(test_name, listener.events)

        self.assertEqual(
            listener.winner(),
            0,
            msg=f"Winner mismatch. Trace written to: {trace_path}",
        )

        self.assertIn(
            "p_0_no_more_cards",
            listener.events,
            msg=f"Missing p_0_no_more_cards. Trace written to: {trace_path}",
        )

        print("\nFULL TRACE:")
        print("\n".join(listener.events))

