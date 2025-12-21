# tests/test_regression_p0_wins.py

import unittest

from tests.helpers.fixed_dealer import fixed_dealer
from tests.helpers.trace_listener import TraceListener
from tests.helpers.make_test_bprogram import make_test_bprogram

from bp_taki import run_bp_program

NUM_CARDS = 6  # use same constant as your game setup if needed

class TestRegressionP0Wins(unittest.TestCase):
    def test_p0_wins_simple(self):
        leading = "p_card_1_red"
        p0 = ["p_card_5_red"]  # only move -> empties hand
        p1 = ["p_card_7_blue", "p_card_9_green"]

        listener = TraceListener()
        dealer = fixed_dealer(p0, p1, leading)
        bp = make_test_bprogram(dealer, listener, num_cards=NUM_CARDS)

        run_bp_program(bp, configure_logger=False)

        self.assertEqual(listener.winner(), 0, msg=f"Trace: {listener.events}")
        self.assertIn("p_0_no_more_cards", listener.events)
