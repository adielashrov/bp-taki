import unittest

from bppy.model.b_priority_event import BPEvent
from bppy.model.b_thread import b_thread
from bppy.model.event_selection.deterministic_event_priority_selection_strategy import (
    DeterministicEventPrioritySelectionStrategy,
)
from bppy.model.sync_statement import sync

from bp_taki import (
    block_next_turn_during_open_taki,
    build_b_program,
    enforce_card_placement_rules,
    enforce_turns,
    game_manager,
    identify_deadlock,
    optimal_change_color_strategy,
    optimal_strategy,
    player_behavior,
    run_bp_program,
    verify_turn_alternation,
)
from tests.helpers.trace_listener import TraceListener


def ev(name: str, priority: float = 10.0) -> BPEvent:
    return BPEvent(name=name, data={}, priority=priority)


@b_thread
def fixed_dealer_round_robin(p0_cards, p1_cards, leading_card):
    assert len(p0_cards) == len(p1_cards), "Both players must receive the same number of cards"

    yield sync(request=ev("start_dealing_cards_to_players"))

    for i in range(len(p0_cards)):
        yield sync(request=ev("deal_cards_to_player_0"))
        yield sync(request=ev(f"deal_{p0_cards[i]}"))
        yield sync(request=ev("deal_cards_to_player_1"))
        yield sync(request=ev(f"deal_{p1_cards[i]}"))

    yield sync(request=ev("finished_dealing_cards_to_players"))

    lead_deal = f"deal_{leading_card}"
    yield sync(request=ev("deal_leading_card"))
    yield sync(request=ev(lead_deal))
    yield sync(request=ev(f"leading_{lead_deal}"))
    yield sync(request=ev("finished_leading_card"))


class TestOptimalStrategy(unittest.TestCase):
    def run_program(self, b_program, listener, test_name):
        try:
            run_bp_program(b_program, configure_logger=False)
        except Exception as exc:
            raise AssertionError(
                f"{test_name} failed with {type(exc).__name__}: {exc}\nTrace tail: {listener.tail(50)}"
            ) from exc

    def make_bprogram(self, p0_cards, p1_cards, leading_card, extra_bthreads=None):
        num_cards = len(p0_cards)
        listener = TraceListener()
        bthreads = [
            game_manager(),
            fixed_dealer_round_robin(p0_cards, p1_cards, leading_card),
            *(extra_bthreads or []),
            player_behavior(0, num_cards),
            player_behavior(1, num_cards),
            optimal_strategy(0, num_cards, 0, 2),
            optimal_change_color_strategy(0, num_cards, 0, 2),
            block_next_turn_during_open_taki(0),
            block_next_turn_during_open_taki(1),
            enforce_turns(2, 0),
            enforce_card_placement_rules(),
            identify_deadlock(),
            verify_turn_alternation(),
        ]
        b_program = build_b_program(
            bthreads=bthreads,
            event_selection_strategy=DeterministicEventPrioritySelectionStrategy(),
            listener=listener,
        )
        return b_program, listener

    def test_stop_is_preferred_under_pressure_with_same_color_followup(self):
        p0 = ["p_stop_red", "p_card_5_red"]
        p1 = ["p_card_1_blue", "p_card_4_green"]
        b_program, listener = self.make_bprogram(p0, p1, "p_card_3_red")

        self.run_program(b_program, listener, self.id())

        self.assertIn("p_0_stop_red", listener.events)
        start_index = listener.events.index("start_game")
        self.assertEqual(listener.events[start_index + 1], "p_0_stop_red")

    def test_regular_taki_is_preferred_over_super_taki_for_longer_dump(self):
        p0 = ["p_taki_red", "p_super_taki", "p_card_5_red", "p_stop_red"]
        p1 = ["p_card_1_blue", "p_card_3_green", "p_card_4_blue", "p_card_5_green"]
        b_program, listener = self.make_bprogram(p0, p1, "p_card_3_red")

        self.run_program(b_program, listener, self.id())

        start_index = listener.events.index("start_game")
        self.assertEqual(listener.events[start_index + 1], "p_0_taki_red")

    def test_closed_taki_is_chosen_when_change_color_is_the_only_remaining_special(self):
        p0 = ["p_taki_red", "p_change_color"]
        p1 = ["p_card_1_red", "p_card_4_green"]
        b_program, listener = self.make_bprogram(p0, p1, "p_card_3_red")

        self.run_program(b_program, listener, self.id())

        self.assertIn("p_0_taki_red", listener.events)
        taki_index = listener.events.index("p_0_taki_red")
        self.assertEqual(listener.events[taki_index + 1], "p_0_closed_taki")

    def test_change_color_selects_dominant_remaining_color(self):
        p0 = ["p_change_color", "p_card_1_blue", "p_stop_blue"]
        p1 = ["p_card_4_blue", "p_card_5_green", "p_card_3_red"]
        b_program, listener = self.make_bprogram(p0, p1, "p_card_2_green")

        self.run_program(b_program, listener, self.id())

        self.assertIn("p_0_change_color", listener.events)
        change_index = listener.events.index("p_0_change_color")
        self.assertEqual(listener.events[change_index + 1], "selected_blue")


if __name__ == "__main__":
    unittest.main()
