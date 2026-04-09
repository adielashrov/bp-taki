"""Debug script: trace events and external player decisions for a deadlock seed."""
import logging
import os
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import datetime
from unittest.mock import patch

from taki_simulation import (
    create_simulation_bprogram_basic_vs_external,
    SimulationListener,
)
from bp_taki import NUM_OF_CARDS, NUM_OF_PLAYERS
import bp_taki
from external_bridge_state import build_external_observation

SEED = 4
STARTING_PLAYER = 0  # From balanced schedule: seed 4 -> starting_player=0


class TraceListener(SimulationListener):
    """Listener that prints every selected event."""

    def event_selected(self, b_program, event):
        super().event_selected(b_program, event)
        idx = len(self.events)
        print(f"  [{idx:>4}] {event.name}  (pri={getattr(event, 'priority', '?')})")


import bppy as bp
from bppy.model.b_priority_event import BPEvent
from python_taki_api.python_agent import PythonAgent, _legal_cards
from external_bridge_state import (
    init_external_bridge_state,
    update_external_bridge_state_from_event,
)

# We'll directly import the helpers we need
from bp_taki import (
    leading_card_event_set,
    DealCardsEventSet,
    remove_deal_prefix_and_add_player_index,
    is_regular_card_event,
    is_draw_card_event,
    is_action_card_event,
    is_any_taki_event,
    is_change_color_event,
    list_does_not_contain_card_events,
    resolve_external_action_event,
    COLORS,
    SEED as _SEED,
)


@bp.thread
def player_behavior_external_debug(index, num_of_cards=2, starting_player=0, num_of_players=2):
    python_agent = PythonAgent(seed=bp_taki.SEED)
    state = init_external_bridge_state(index, starting_player, num_of_players)

    yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))
    card_events = []
    deal_player_cards_event_set = DealCardsEventSet()

    for i in range(num_of_cards):
        yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
        card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

    yield bp.sync(waitFor=BPEvent("finished_dealing_cards_to_players", priority=10.0))
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    leading_event = yield bp.sync(waitFor=leading_card_event_set)
    update_external_bridge_state_from_event(state, leading_event, num_of_players)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    card_events.append(draw_card_event)

    turn_num = 0
    while True:
        if state["current_player"] != index:
            observed_event = yield bp.sync(waitFor=bp.All())
            update_external_bridge_state_from_event(state, observed_event, num_of_players)
            continue

        turn_num += 1
        observation = build_external_observation(index, "turn", card_events, state)

        # ---- DEBUG: print decision state ----
        hand_cards = [e.name for e in card_events if 'draw_card' not in e.name]
        hand_descriptors = observation["hand"].split(",") if observation["hand"] else []
        legal = _legal_cards(hand_descriptors, observation)
        print(f"\n>>> EXT TURN #{turn_num}  state={state}")
        print(f"    observation = {observation}")
        print(f"    hand_events = {hand_cards}")
        print(f"    legal_cards = {legal}")
        # ---- END DEBUG ----

        action_name = python_agent.get_action(observation)
        requested_event = resolve_external_action_event(action_name, observation, card_events)
        print(f"    ACTION = {action_name}  ->  request={requested_event.name} (pri={requested_event.priority})")

        card_event = yield bp.sync(request=requested_event)
        update_external_bridge_state_from_event(state, card_event, num_of_players)

        if is_regular_card_event(card_event):
            card_events.remove(card_event)
        elif is_draw_card_event(card_event):
            yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            card_events.append(BPEvent(card_name, priority=deal_card_event.priority))
        elif is_action_card_event(card_event):
            if is_any_taki_event(card_event):
                card_events.remove(card_event)
                closed_taki_event = BPEvent(f"p_{index}_closed_taki", priority=15.0)
                card_events.append(closed_taki_event)
                while True:
                    observation = build_external_observation(index, "taki_sequence", card_events, state)
                    hand_descriptors = observation["hand"].split(",") if observation["hand"] else []
                    legal = _legal_cards(hand_descriptors, observation)
                    action_name = python_agent.get_action(observation)
                    print(f"    TAKI_SEQ: legal={legal}, action={action_name}")
                    requested_event = resolve_external_action_event(action_name, observation, card_events)
                    taki_event = yield bp.sync(request=requested_event)
                    update_external_bridge_state_from_event(state, taki_event, num_of_players)
                    if taki_event.name != f"p_{index}_closed_taki":
                        if taki_event in card_events:
                            card_events.remove(taki_event)
                    else:
                        card_events.remove(taki_event)
                        break
                done = yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
                update_external_bridge_state_from_event(state, done, num_of_players)
            elif is_change_color_event(card_event):
                card_events.remove(card_event)
                selected_color_events = [BPEvent(f"selected_{c}", priority=5.0) for c in COLORS]
                observation = build_external_observation(index, "change_color", selected_color_events, state)
                action_name = python_agent.get_action(observation)
                requested_color_event = resolve_external_action_event(action_name, observation, selected_color_events)
                selected_color_event = yield bp.sync(request=requested_color_event)
                update_external_bridge_state_from_event(state, selected_color_event, num_of_players)
                done = yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
                update_external_bridge_state_from_event(state, done, num_of_players)
            else:
                done = yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
                update_external_bridge_state_from_event(state, done, num_of_players)
                card_events.remove(card_event)

        if list_does_not_contain_card_events(card_events):
            no_more = BPEvent(f"p_{index}_no_more_cards", priority=8.0)
            final = yield bp.sync(request=no_more)
            update_external_bridge_state_from_event(state, final, num_of_players)
            break

        next_turn_event = BPEvent("next_turn", priority=10.0)
        observed = yield bp.sync(request=next_turn_event)
        update_external_bridge_state_from_event(state, observed, num_of_players)


def run_debug():
    """Run one game with detailed tracing."""
    from bppy.model.event_selection.event_priority_selection_strategy import (
        EventPrioritySelectionStrategy,
    )
    from bp_taki import (
        game_manager,
        deal_cards,
        player_behavior,
        enforce_turns,
        enforce_card_placement_rules,
        identify_deadlock,
        identify_livelock,
        verify_turn_alternation,
        basic_strategy_taki,
    )

    # Match the simulation: pass starting_player directly (don't consume a random.randint)
    random.seed(SEED)
    bp_taki.SEED = SEED

    listener = TraceListener()

    actual_starting_player = STARTING_PLAYER
    print(f"Seed={SEED}, starting_player={actual_starting_player}")

    bthreads = [
        game_manager(),
        deal_cards(NUM_OF_PLAYERS, NUM_OF_CARDS, actual_starting_player),
        player_behavior(0, NUM_OF_CARDS),
        player_behavior_external_debug(1, NUM_OF_CARDS, actual_starting_player, NUM_OF_PLAYERS),
        enforce_turns(NUM_OF_PLAYERS, actual_starting_player),
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation(),
        basic_strategy_taki(0, NUM_OF_CARDS),
    ]

    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=listener,
    )

    try:
        b_program.run()
    except AssertionError:
        if not (listener.get_deadlock() or listener.get_draw()):
            raise

    print(f"\n{'='*60}")
    if listener.get_deadlock():
        print("RESULT: DEADLOCK!")
        print(f"Last 15 events:")
        for i, ev in enumerate(listener.events[-15:]):
            print(f"  {ev}")
    elif listener.get_winner() is not None:
        print(f"RESULT: Player {listener.get_winner()} wins!")
    else:
        print("RESULT: Draw or unknown")
    print(f"Total events: {len(listener.events)}")


if __name__ == "__main__":
    # Suppress noisy TakiGame logger
    logging.getLogger("TakiGame").setLevel(logging.WARNING)
    run_debug()
