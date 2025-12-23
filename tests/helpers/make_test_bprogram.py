# tests/helpers/make_test_bprogram.py

from bppy.model.event_selection.deterministic_event_priority_selection_strategy import (
    DeterministicEventPrioritySelectionStrategy,
)

from bp_taki import (
    build_b_program,
    game_manager,
    player_behavior,
    enforce_turns,
    enforce_card_placement_rules,
    identify_deadlock,
    verify_turn_alternation,
)

def make_test_bprogram(dealer_bthread, listener, num_cards, num_players=2, extra_bthreads=None):
    extra_bthreads = extra_bthreads or []

    bthreads = [
        game_manager(),
        dealer_bthread,
        *extra_bthreads,
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        enforce_turns(),
        enforce_card_placement_rules(),
        identify_deadlock(),
        verify_turn_alternation(),
    ]

    return build_b_program(
        bthreads=bthreads,
        event_selection_strategy=DeterministicEventPrioritySelectionStrategy(),
        listener=listener,
    )
