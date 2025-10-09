from typing import Union, Optional

import bppy as bp
from bppy.analysis.symbolic_bprogram_verifier import SymbolicBProgramVerifier
from bppy.model.event_selection.statement_priority_event_selection_strategy import StatementPriorityBasedEventSelectionStrategy
from bppy.model.b_priority_event import BPEvent
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy
from bppy.analysis.dfs_bprogram_verifier import DFSBProgramVerifier
import random
import re
from typing import *

NUM_OF_CARDS = 4

# Control events
all_events = [
    bp.BEvent("p_0_card_7_red"),
    bp.BEvent("p_0_card_9_blue"),
    bp.BEvent("p_1_card_3_red"),
    bp.BEvent("p_1_card_1_blue"),
    bp.BEvent("start_dealing_cards_to_players"),
    bp.BEvent("finished_dealing_cards_to_players"),
    bp.BEvent("deal_leading_card"),
    bp.BEvent("finished_leading_card"),
    bp.BEvent("start_game"),
    bp.BEvent("no_more_cards"),
    bp.BEvent("end_game"),
    bp.BEvent("leading_card_5_blue"),
    bp.BEvent("start_game"),
    bp.BEvent("end_game")
]

# Control the randomness of card dealing
random.seed(7)

leading_card_event_set = bp.EventSet(lambda e: e.name.startswith('leading_'))

# A bypass for EventSetUnify
pattern = r"(p_\d+_(draw_card|card_\d+_\w+|last_card|stop_\w+|plus_2_\w+))|end_game"
general_player_event_set = bp.EventSet(lambda e:
                                       hasattr(e, 'name') and re.match(pattern, e.name) is not None
                                       )
def all_player_events(index):
    return bp.EventSet(lambda e: f'p_{index}' in e.name)

all_player_0_events = bp.EventSet(lambda e: 'p_0' in e.name)
all_player_1_events = bp.EventSet(lambda e: 'p_1' in e.name)

def all_player_post_action_events(index):
    return bp.EventSet(lambda e: f'post_action_p_{index}' in e.name)

all_player_0_post_action_events = bp.EventSet(lambda e: 'post_action_p_0' in e.name)
all_player_1_post_action_events = bp.EventSet(lambda e: 'post_action_p_1' in e.name)

#Maybe we should support union of EventSets, like this case.
all_player_0_except_no_more_cards = bp.EventSet(lambda e: 'p_0' in e.name and not 'no_more_cards' in e.name)
all_player_1_except_no_more_cards = bp.EventSet(lambda e: 'p_1' in e.name and not 'no_more_cards' in e.name)

def all_player_except_no_more_cards_and_last_card(index):
    return bp.EventSet(lambda e: f'p_{index}' in e.name and not 'no_more_cards' in e.name and not 'last_card' in e.name)

all_player_0_except_no_more_cards_and_last_card = bp.EventSet(
    lambda e: 'p_0' in e.name and not 'no_more_cards' in e.name and not 'last_card' in e.name)
all_player_1_except_no_more_cards_and_last_card = bp.EventSet(
    lambda e: 'p_1' in e.name and not 'no_more_cards' in e.name and not 'last_card' in e.name)

any_player_no_more_cards = bp.EventSet(lambda e: 'no_more_cards' in e.name)


def is_event_draw_card_event(player_index, event):
    if f"p_{player_index}_draw_card" == event.name:
        return True
    return False


def is_event_stop_card_event(player_index, event):
    if event.name.startswith(f"p_{player_index}_stop"):
        return True
    return False


def create_cards_from_same_color_event_set(color):
    def cards_from_the_same_color(event):
        if color in event.name:
            return True
        return False

    return bp.EventSet(cards_from_the_same_color)


def create_cards_from_different_color_event_set(color):
    def cards_from_the_different_color(event):
        colors = ["blue", "red", "green"]
        if color in colors:
            colors.remove(color)
        else:
            raise Exception(f"Wrong parameter to cards_from_the_different_color: {color}")
        if color in event.name:
            return False
        for c in colors:
            if c in event.name:
                return True
        return False

    return bp.EventSet(cards_from_the_different_color)


def create_cards_from_different_number_event_set(number):
    numbers = ["1", "3", "4", "5", "6", "7", "8", "9"]
    numbers.remove(number)

    def cards_from_the_different_number(event):
        current_card_number = extract_card_number(event)
        if number == current_card_number:
            return False
        elif current_card_number in numbers:
            return True
        else:
            return False

    return bp.EventSet(cards_from_the_different_number)


def create_cards_from_different_color_or_type_event_set(card_color, card_type):
    colors = ["blue", "red", "green"]
    types = ["1", "3", "4", "5", "6", "7", "8", "9", "STOP", "PLUS_2"]
    if card_color in colors and card_type in types:
        colors.remove(card_color)
        types.remove(card_type)
    elif card_color in colors and card_type is None: # stop card
        print("We shouldn't reach this case, since we now have a type named STOP")
        colors.remove(card_color)
    else:
        raise Exception(f"Wrong parameter to "
                        f"create_cards_from_different_color_or_type_event_set"
                        f"{card_color, card_type}")

    def cards_from_the_different_color_or_type(event):
        # TODO: add documentation to this method
        # Edge case, we don't want to block events from different
        # colors/number if they are a new card being dealt.
        if event.name.startswith("deal_p_"):
            return False
        t_card_color, t_card_type = extract_card_color_and_type(event)
        if t_card_color == card_color or t_card_type == card_type:
            return False
        elif t_card_color in colors or t_card_type in types: #Should we block "STOP" events?
            return True
        else:  # default return false.
            return False

    return bp.EventSet(cards_from_the_different_color_or_type)


class PlayerEventSet(bp.EventSet):
    def __init__(self, index):
        self.index = index
        super().__init__(lambda event: event.name.startswith(f"p_{self.index}"))

    def __contains__(self, item):
        if isinstance(item, BPEvent):
            return item.name.startswith(f"p_{self.index}")
        else:
            raise TypeError(f"Player_{self.index}_EventSet: Expected item of type BPEvent, got {type(item)}")


class DealCardsPlayerEventSet(bp.EventSet):
    def __init__(self, index):
        self.index = index
        super().__init__(lambda event: event.name.startswith(f"deal_p_{self.index}"))

    def __contains__(self, item):
        if isinstance(item, BPEvent):
            return item.name.startswith(f"deal_p_{self.index}")
        else:
            raise TypeError(
                f"Player_{self.index}_DealCardsPlayerEventSet: Expected item of type BPEvent, got {type(item)}")

class DealCardsEventSet(bp.EventSet):
    def __init__(self):
        super().__init__(lambda event: event.name.startswith(f"deal_p_"))

    def __contains__(self, item):
        if isinstance(item, BPEvent):
            return item.name.startswith(f"deal_p_")
        else:
            raise TypeError(
                f"DealCardsEventSet: Expected item of type BPEvent, got {type(item)}")


'''
def create_and_shuffle_cards():
    all_cards = []
    colors = ["blue", "red","green"]
    numbers = ["1", "3", "4", "5","6","7","8","9"]
    for color in colors:
        for number in numbers:
            card_event_name= "card_" + number + "_" + color
            all_cards.append(BPEvent(card_event_name, priority=10.0))

    random.shuffle(all_cards)
    return all_cards
'''


def init_cards_events():

    all_cards = [BPEvent(name="stop_red", data={}, priority=10.0),
         BPEvent(name="card_5_blue", data={}, priority=10.0),
         BPEvent(name="stop_blue", data={}, priority=10.0),
         BPEvent(name="card_1_red", data={}, priority=10.0),
         BPEvent(name="plus_2_red", data={}, priority=10.0),
         BPEvent(name="card_4_blue", data={}, priority=10.0),
         BPEvent(name="stop_green", data={}, priority=10.0),
         BPEvent(name="card_5_green", data={}, priority=10.0),
         BPEvent(name="plus_2_green", data={}, priority=10.0),
         BPEvent(name="card_1_blue", data={}, priority=10.0),
         BPEvent(name="card_3_green", data={}, priority=10.0),
         BPEvent(name="card_1_green", data={}, priority=10.0),
         BPEvent(name="card_4_red", data={}, priority=10.0),
         BPEvent(name="stop_red", data={}, priority=10.0),
         BPEvent(name="plus_2_blue", data={}, priority=10.0),
         BPEvent(name="card_5_red", data={}, priority=10.0),
         BPEvent(name="card_4_green", data={}, priority=10.0),
         BPEvent(name="stop_green", data={}, priority=10.0),
         BPEvent(name="card_3_blue", data={}, priority=10.0),
         BPEvent(name="stop_blue", data={}, priority=10.0),
         BPEvent(name="plus_2_red", data={}, priority=10.0)]

    return all_cards

def is_plus_2_card_event(event: BPEvent) -> bool:
    """Check if event is a Plus 2 card"""
    return "plus_2" in event.name

def extract_plus_2_color(event: BPEvent) -> Optional[str]:
    """Extract color from Plus 2 card event"""
    if "plus_2" in event.name:
        return event.name.split("_")[-1]  # returns "red", "blue", or "green"
    return None

@bp.thread
def game_manager():
    yield bp.sync(request=BPEvent("start_dealing_cards_to_players", priority=10.0))
    yield bp.sync(waitFor=BPEvent("finished_dealing_cards_to_players", priority=10.0))
    yield bp.sync(request=BPEvent("deal_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(request=BPEvent("start_game", priority=10.0))
    yield bp.sync(waitFor=any_player_no_more_cards)
    yield bp.sync(request=BPEvent("end_game", priority=7.0))


@bp.thread
def end_of_game():  # blocks moves after the game is over
    yield bp.sync(waitFor=BPEvent("end_game", priority=7.0))
    yield bp.sync(block=bp.All())


def create_deal_events(card_events_list):
    deal_cards_events = []
    for index, card_event in enumerate(card_events_list):
        deal_player_card_event = BPEvent("deal_p_" + card_event.name, priority=card_event.priority)
        deal_cards_events.append(deal_player_card_event)

    return deal_cards_events

# A regular card is a card with a number (1-9) and a color (red, blue, green).
# a possible input event to this method is deal_p_card_5_blue
def is_regular_card(event: BPEvent) -> bool:
    pattern = r"deal_p_card_\d+_\w+"
    if re.match(pattern, event.name) is not None:
        return True
    return False

@bp.thread
def deal_cards(num_of_players=2, num_of_cards=2):
    yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))
    cards_events = init_cards_events()
    deal_cards_events = create_deal_events(cards_events)
    for i in range(num_of_players):
        yield bp.sync(request=BPEvent(f"deal_cards_to_player_{i}", priority=10.0))
        for j in range(num_of_cards):
            last_event = yield bp.sync(request=deal_cards_events) # possible pattern here?
            deal_cards_events.remove(last_event)
    yield bp.sync(request=BPEvent("finished_dealing_cards_to_players", priority=10.0))

    # Deal the leading card
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))

    # Filter to only regular numbered cards
    regular_cards = [card for card in deal_cards_events
                     if is_regular_card(card)]
    # We want that the leading card will be a regular card.
    last_event = yield bp.sync(request=regular_cards)  # possible pattern here?
    deal_cards_events.remove(last_event)
    yield bp.sync(request=BPEvent(f"leading_{last_event.name}", priority=10.0))
    yield bp.sync(request=BPEvent("finished_leading_card", priority=10.0))

    while True:
        last_event = yield bp.sync(waitFor=[BPEvent("p_0_draw_card"), BPEvent("p_1_draw_card")])
        if not deal_cards_events:  # imagine an infinite pile of cards.
            deal_cards_events = create_deal_events(init_cards_events())
        yield bp.sync(request=deal_cards_events)


def remove_deal_prefix_from_event(event):
    card_name = event.name.removeprefix("deal_")
    return card_name

def remove_deal_prefix_and_add_player_index(event, player_index):
    card_name = event.name.removeprefix("deal_p_")
    card_name = f"p_{player_index}_" + card_name
    return card_name


def list_contains_only_draw_card_event(action_events):
    if len(action_events) == 1 and "_draw_card" in action_events[0].name:
        return True
    return False


def count_num_of_cards(index: int, action_events: list[BPEvent]) -> int:
    card_count = len([e for e in action_events if e.name.startswith(f"p_{index}_card")])
    return card_count


@bp.thread
def request_post_action_for_regular_cards(index):
    while True:
        last_event = yield bp.sync(waitFor=general_player_event_set)
        if (last_event.name.startswith(f"p_{index}_card") or
                last_event.name.startswith(f"p_{index}_draw_card") or
                last_event.name.startswith(f"p_{index}_stop") or
                last_event.name.startswith(f"p_{index}_plus_2")):
            event_name = "post_action_" + last_event.name
            yield bp.sync( request=BPEvent(event_name, priority=last_event.priority),
                                    block=general_player_event_set)


@bp.thread
def player_behavior(index, num_of_cards=2):
    yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
    card_events = []
    deal_player_cards_event_set = DealCardsEventSet()
    for i in range(num_of_cards):
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
        card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    # Define announce last card event
    last_card_event = BPEvent(f"p_{index}_last_card", priority=6.0)
    # Add draw_card_event to the cards events(Possible actions of player)
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    card_events.append(draw_card_event)

    while True:
        event = yield bp.sync(waitFor=general_player_event_set, request=card_events)
        if (event.name.startswith(f"p_{index}_card") or
            event.name.startswith(f"p_{index}_stop") or
            event.name.startswith(f"p_{index}_plus_2")):
            card_events.remove(event)

            # If the only event is a single regular card, announce last card!
            card_count = count_num_of_cards(index, card_events)
            # if card_count == 1:
            # print(f"player_{index} Should have announced last_card_event")
            # event = yield bp.sync(request=last_card_event)

            # If the only event left is draw_card, break and end the game.
            if list_contains_only_draw_card_event(card_events):
                yield bp.sync(request=BPEvent(f"p_{index}_no_more_cards", priority=8.0))
                break
        # If there is a draw card event, wait for a card to be dealt.
        if event.name.startswith(f"p_{index}_draw_card"):
            # if we want to simulate a deadlock - add the following block   - block=bp.AllExcept(BPEvent("deadlock"))
            # deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set, block=bp.AllExcept(BPEvent("deadlock")))
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            card_events.append(BPEvent(card_name, priority=deal_card_event.priority))
        # If the other player ended the game.
        if event.name.startswith(f"end_game"):  # similar to breakupon.
            break


def extract_card_color(event: BPEvent) -> str:
    card_str_index = event.name.find("card")
    card_color = event.name[card_str_index + 7:]
    return card_color


def extract_card_number(event: BPEvent) -> str:
    # print(f"extract_card_color event: {event}")
    card_str_index = event.name.find("card")
    card_number = event.name[card_str_index + 5:card_str_index + 6]
    return card_number


def extract_card_color_and_type(event: BPEvent) -> Union[tuple[str, str], tuple[None, None]]:
    """
    Extracts the color and number from a card or stop event name.

    Args:
        event (BPEvent): The event whose name encodes card or stop information.

    Returns:
        tuple[str, str]: (color, number) if the event is a card event.
        tuple[str, None]: (color, None) if the event is a stop event.
        tuple[None, None]: (None, None) if neither card nor stop information is found.

    Example:
        - For event.name == "card_5_blue", returns ("blue", "5")
        - For event.name == "stop_red", returns ("red", "STOP")
        - For event.name == "plus_2_red", returns ("red", "PLUS_2")
        - For other event names, returns (None, None)
    """
    card_str_index = event.name.find("card")
    if card_str_index != -1:
        card_color = event.name[card_str_index + 7:]
        card_number = event.name[card_str_index + 5:card_str_index + 6]
        return card_color, card_number
    else:
        stop_str_index = event.name.find("stop")
        if stop_str_index != -1:
            card_color = event.name[stop_str_index + 5:]
            return card_color, "STOP"
        else:
            plus_2_str_index = event.name.find("plus_2")
            if plus_2_str_index != -1:
                card_color = event.name[plus_2_str_index + 7:]
                return card_color, "PLUS_2"
            else:
                return None, None


def is_color_card_event(event: BPEvent) -> bool:
    for color in ["blue", "red", "green"]:
        if color in event.name:
            return True
    return False


def is_color_or_type_card_event(event: BPEvent) -> bool:
    # Regular numbered cards
    pattern = r"p_\d+_card_\d+_\w+"
    if re.match(pattern, event.name) is not None:
        return True

    # Stop cards
    stop_pattern = r"p_\d+_stop_\w+"
    if re.match(stop_pattern, event.name) is not None:
        return True

    # Plus 2 cards
    plus_2_pattern = r"p_\d+_plus_2_\w+"
    if re.match(plus_2_pattern, event.name) is not None:
        print("[is_color_or_type_card_event]: Plus 2 card detected")
        return True

    return False


@bp.thread
def enforce_turns():
    yield bp.sync(waitFor=BPEvent("start_game"))
    player = 0
    while True:
        yield bp.sync(waitFor=all_player_events(player),
                      block=all_player_except_no_more_cards_and_last_card(1 - player))
        last_event = yield bp.sync(waitFor=all_player_post_action_events(player), block=bp.EventSet(lambda e: 'p_' in e.name and 'post_action' not in e.name)) # pattern here +Block here can cause deadlocks!

        if f'p_{player}_draw_card' in last_event.name: # if the player requested to draw a card, wait for a deal_card event
            yield bp.sync(waitFor=DealCardsEventSet(),block=bp.EventSet(lambda e: f'deal_p_' not in e.name))  # pattern and here

        if is_plus_2_card_event(last_event):
            print("[enforce_turns] Plus 2 card played by player:", player)
            pass

        if f'p_{player}_stop' in last_event.name: # if the player played a Stop card, skip the other player's turn
            continue
        player = 1 - player


'''
@bp.thread
def enforce_turns():  # blocks moves that are not in turn
    yield bp.sync(waitFor=BPEvent("start_game",priority=10.0))
    while True:
        last_event_p_0 = yield bp.sync(waitFor=all_player_0_events, block=all_player_1_except_no_more_cards_and_last_card)
        if is_event_draw_card_event(0, last_event_p_0):
            yield bp.sync(waitFor=all_player_0_events, block=all_player_1_except_no_more_cards_and_last_card)

        last_event_p_1 = yield bp.sync(waitFor=all_player_1_events, block=all_player_0_except_no_more_cards_and_last_card)
        if is_event_draw_card_event(1, last_event_p_1):
            yield bp.sync(waitFor=all_player_1_events, block=all_player_0_except_no_more_cards_and_last_card)
'''

'''
# Updated enforce_turns b-thread that addresses the Stop action card
@bp.thread
def enforce_turns():
    yield bp.sync(waitFor=BPEvent("start_game",priority=10.0))
    while True:
        while True:
            last_event_p_0 = yield bp.sync(waitFor=all_player_0_events, block=all_player_1_except_no_more_cards_and_last_card)
            if not is_event_stop_card_event(0, last_event_p_0):
                break

        if is_event_draw_card_event(0, last_event_p_0):
            yield bp.sync(waitFor=all_player_0_events, block=all_player_1_except_no_more_cards_and_last_card)

        while True:
            last_event_p_1 = yield bp.sync(waitFor=all_player_1_events, block=all_player_0_except_no_more_cards_and_last_card)
            if not is_event_stop_card_event(1, last_event_p_1):
                break

        if is_event_draw_card_event(1, last_event_p_1):
            yield bp.sync(waitFor=all_player_1_events, block=all_player_0_except_no_more_cards_and_last_card)
'''

'''
@bp.thread
def enforce_turns():  # blocks moves that are not in turn
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    # Track penalty state
    penalty_in_progress = False
    penalty_player = None
    penalty_draws_remaining = 0

    while True:
        # Listen for penalty events
        event = yield bp.sync(
            waitFor=bp.EventSet(lambda e:
                                e.name.startswith("penalize_player_") or
                                e.name.startswith("p_0_") or
                                e.name.startswith("p_1_")
                                ),
            block=bp.EventSet(lambda e: False)  # Don't block anything initially
        )

        # Handle penalty start
        if event.name.startswith("penalize_player_"):
            penalty_in_progress = True
            penalty_player = 0 if event.name == "penalize_player_0" else 1
            penalty_draws_remaining = 4
            print(f"[TURNS] Penalty mode: Player {penalty_player} can take {penalty_draws_remaining} penalty draws")
            continue

        # Handle penalty draws
        if penalty_in_progress and event.name == f"p_{penalty_player}_draw_card":
            penalty_draws_remaining -= 1
            print(f"[TURNS] Penalty draw: {penalty_draws_remaining} draws remaining for Player {penalty_player}")

            if penalty_draws_remaining <= 0:
                penalty_in_progress = False
                penalty_player = None
                print(f"[TURNS] Penalty complete - resuming normal turn enforcement")
            continue

        # Normal turn enforcement (when not in penalty mode)
        if not penalty_in_progress:
            if event.name.startswith("p_0_"):
                acting_player = 0
                other_player = 1
            elif event.name.startswith("p_1_"):
                acting_player = 1
                other_player = 0
            else:
                continue

            # Block the other player's actions during this player's turn
            yield bp.sync(
                waitFor=all_player_0_events if acting_player == 0 else all_player_1_events,
                block=all_player_1_except_no_more_cards_and_last_card if acting_player == 0
                else all_player_0_except_no_more_cards_and_last_card
            )

            # Handle draw card extensions (if player draws, they get another action)
            if is_event_draw_card_event(acting_player, event):
                yield bp.sync(
                    waitFor=all_player_0_events if acting_player == 0 else all_player_1_events,
                    block=all_player_1_except_no_more_cards_and_last_card if acting_player == 0
                    else all_player_0_except_no_more_cards_and_last_card
                )
'''


@bp.thread
def enforce_same_color():
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    card_color = extract_card_color(event=last_event)
    different_colors_event_set = create_cards_from_different_color_event_set(card_color)
    last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_event_set)

    while True:
        if is_color_card_event(last_event):
            card_color = extract_card_color(event=last_event)
            different_colors_event_set = create_cards_from_different_color_event_set(card_color)
        last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_event_set)


# This b-thread is currently not used in the b-program.
@bp.thread
def enforce_same_number():
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    card_number = extract_card_number(event=last_event)
    different_numbers_event_set = create_cards_from_different_number_event_set(card_number)
    last_event = yield bp.sync(waitFor=general_player_event_set, block=different_numbers_event_set)

    while True:
        if is_color_card_event(last_event):
            card_number = extract_card_number(event=last_event)
            different_numbers_event_set = create_cards_from_different_number_event_set(card_number)
        last_event = yield bp.sync(waitFor=general_player_event_set, block=different_numbers_event_set)


@bp.thread
def enforce_same_color_or_type():
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    card_color, card_type = extract_card_color_and_type(event=last_event)
    different_colors_or_types_event_set = create_cards_from_different_color_or_type_event_set(card_color,
                                                                                              card_type)
    last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_or_types_event_set)

    while True:
        if is_color_or_type_card_event(last_event):
            card_color, card_type = extract_card_color_and_type(event=last_event)
            different_colors_or_types_event_set = create_cards_from_different_color_or_type_event_set(card_color,
                                                                                                      card_type)
        # else:
        #    print(f"[enforce_same_color_or_number] Ignored event (not a color/number/stop card): {last_event.name}")
        last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_or_types_event_set)


@bp.thread
def identify_deadlock():
    last_event = yield bp.sync(request=BPEvent("deadlock"), waitFor=BPEvent("end_game", priority=10.0))
    if last_event.name.startswith("deadlock"):
        assert False
    else:
        assert True


@bp.thread
def detect_illegal_post_game_moves():
    yield bp.sync(waitFor=BPEvent("end_game", priority=7.0))
    # Allow one more event and check
    illegal_event = yield bp.sync(waitFor=bp.All())
    assert False, f"Illegal event occurred after game ended: {illegal_event}"


@bp.thread
def verify_turn_alternation():
    yield bp.sync(waitFor=BPEvent("start_game"))

    last_acting_player = None

    while True:
        # Wait for any game event (not just player actions)
        event = yield bp.sync(waitFor=bp.EventSet(lambda e: True))

        # Determine if this event is a player action
        is_player_action = (
                (event.name.startswith("p_0_card_") or event.name.startswith("p_1_card_")) or
                (event.name == "p_0_draw_card" or event.name == "p_1_draw_card")
        )

        if is_player_action:
            # Determine which player acted
            acting_player = 0 if event.name.startswith("p_0_") else 1

            if last_acting_player is not None and acting_player == last_acting_player:
                raise AssertionError(
                    f"[Verifier ❌] Turn violation: Player {acting_player} acted twice in a row: {event}"
                )

            last_acting_player = acting_player
        # else:
        # Not a player action — just log
        # print(f"[Verifier] Ignored (not a player action): {event.name}")


@bp.thread
def apply_penalty():
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    penalty_events = bp.EventSet(lambda e: e.name.startswith("penalize_player_"))

    while True:
        penalty_event = yield bp.sync(waitFor=penalty_events)

        if penalty_event.name == "penalize_player_0":
            player = 0
        elif penalty_event.name == "penalize_player_1":
            player = 1
        else:
            print(f"[PENALTY_THREAD] WARNING: Unknown penalty event {penalty_event.name}")
            continue

        other_player = 1 - player
        other_player_actions = bp.EventSet(lambda e:
                                           e.name.startswith(f"p_{other_player}_card") or
                                           e.name == f"p_{other_player}_draw_card")

        print(f"[PENALTY_APPLY] Applying 4-card penalty to Player {player} (simplified)")

        for i in range(4):
            # Add just this one debug line before the problematic second request
            if i == 1:  # Only debug the second penalty draw
                print(f"[DEBUG_DEADLOCK] About to request penalty draw 2/4 for Player {player}")

            # Simple request with blocking - no game-end logic
            draw_event = yield bp.sync(
                request=BPEvent(f"p_{player}_draw_card", priority=3.0),
                block=other_player_actions
            )

            print(f"[PENALTY_DEBUG] Draw event selected: {draw_event.name}")

            deal_event = yield bp.sync(waitFor=DealCardsPlayerEventSet(player))
            print(f"[PENALTY_DRAW] Player {player} penalty draw {i + 1}/4: {deal_event.name}")

        print(f"[PENALTY_COMPLETE] Penalty for Player {player} complete")


@bp.thread
def enforce_last_card_announcement():
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    hand_sizes = {0: NUM_OF_CARDS, 1: NUM_OF_CARDS}
    pending_announcement = {0: False, 1: False}

    def handle_card_play(player):
        hand_sizes[player] -= 1
        # print(f"[HAND_SIZE] Player {player} played a card. New hand size: {hand_sizes[player]}")

        if hand_sizes[player] == 1:
            pending_announcement[player] = True
            # print(f"[LAST_CARD] Player {player} has 1 card and must announce 'last card!'")

    def handle_card_draw(player, deal_event):
        hand_sizes[player] += 1
        # print(f"[HAND_SIZE] Player {player} drew a card ({deal_event.name}). New hand size: {hand_sizes[player]}")

        if hand_sizes[player] != 1 and pending_announcement[player]:
            pending_announcement[player] = False
            # print(f"[LAST_CARD] Player {player} no longer has 1 card - announcement no longer needed")

    def handle_last_card(player):
        if pending_announcement[player]:
            pending_announcement[player] = False
            print(f"[ANNOUNCE] Player {player} announced 'last card!' - penalty avoided!")
        else:
            print(f"[ANNOUNCE] Player {player} announced 'last card!' but no announcement was needed")

    def check_for_penalty_violation(acting_player):
        """Check if the opponent failed to announce and should be penalized"""
        opponent = 1 - acting_player

        if pending_announcement[opponent]:
            print(f"[PENALTY] Player {opponent} failed to announce 'last card!' - applying 4-card penalty")
            pending_announcement[opponent] = False
            return True
        return False

    def get_player_from_event(event_name):
        if event_name.startswith("p_0_"):
            return 0
        elif event_name.startswith("p_1_"):
            return 1
        return None

    while True:
        event = yield bp.sync(waitFor=general_player_event_set)

        if event.name == "end_game":
            break

        player = get_player_from_event(event.name)
        if player is None:
            print(f"Couldn't extract player from event: {event.name}")
            continue

        if event.name.startswith(f"p_{player}_card") or event.name == f"p_{player}_draw_card":
            apply_penalty = check_for_penalty_violation(player)
            if apply_penalty:
                yield bp.sync(request=BPEvent(f"penalize_player_{1 - player}", priority=3.5))

        if event.name.startswith(f"p_{player}_card"):
            handle_card_play(player)

        elif event.name == f"p_{player}_draw_card":
            deal_event = yield bp.sync(waitFor=DealCardsPlayerEventSet(player))
            handle_card_draw(player, deal_event)

        elif event.name == f"p_{player}_last_card":
            handle_last_card(player)


def init_b_program():
    b_program = bp.BProgram(bthreads=[game_manager(),
                                      deal_cards(2, NUM_OF_CARDS),
                                      player_behavior(0, NUM_OF_CARDS),
                                      player_behavior(1, NUM_OF_CARDS),
                                      request_post_action_for_regular_cards(0),
                                      request_post_action_for_regular_cards(1),
                                      enforce_turns(),
                                      enforce_same_color_or_type(),
                                      # enforce_last_card_announcement(),
                                      # apply_penalty(),
                                      identify_deadlock()],
                            #detect_illegal_post_game_moves()],
                            # verify_turn_alternation()],
                            event_selection_strategy=EventPrioritySelectionStrategy(),
                            listener=bp.PrintBProgramRunnerListener())
    return b_program


def regular_execution_of_bp_program():
    b_program = init_b_program()
    b_program.run()


def verify_with_dfs():
    # initialize DFS verifier with the b-program generator and specify max_trace_length
    ver = DFSBProgramVerifier(init_b_program, max_trace_length=100)
    ok, counter_example = ver.verify()

    # check the verification results and print accordingly
    if ok:
        print("OK")
    else:
        print("Violation Found")
        print("Counterexample:")
        print(counter_example)


if __name__ == "__main__":
    regular_execution_of_bp_program()
    # verify_with_dfs()
