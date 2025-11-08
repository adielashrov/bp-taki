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
NUM_OF_PLAYERS = 2

# Control the randomness of card dealing
SEED = 5
random.seed(SEED)
print("Random seed for card dealing:", SEED)

leading_card_event_set = bp.EventSet(lambda e: e.name.startswith('leading_'))

# A bypass for EventSetUnify
pattern = r"(p_\d+_(draw_card|card_\d+_\w+|last_card|stop_\w+|plus_2_\w+|change_color))|end_game"
general_player_event_set = bp.EventSet(lambda e:
                                       hasattr(e, 'name') and re.match(pattern, e.name) is not None
                                       )

def all_player_events():
    def match_event_name(e):
        if hasattr(e, 'name') and 'p_' in e.name:
            return True
        return False
    return bp.EventSet(match_event_name)

def all_player_index_events(index):
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

def all_players_cards_except_special_cards(index):
    def predicate(e: BPEvent):
        if f'p_{index}' in e.name and not 'no_more_cards' in e.name:
            return True
        return False

    return bp.EventSet(predicate)

def all_other_player_cards_besides_special_cards(index):
    def predicate(e: BPEvent):
        if f'p_{index}' not in e.name and 'p_' in e.name and not 'no_more_cards' in e.name\
                and not 'deal_p_' in e.name:
            return True
        return False

    return bp.EventSet(predicate)

def player_stop_card_event_set(index):
    return bp.EventSet(lambda e: e.name.startswith(f"p_{index}_stop"))


def init_selected_color_or_type_event_set(card_color: str, card_type: str):
    def predicate(e: BPEvent):
        # System events that are always allowed regardless of placement rules
        if "draw_card" in e.name: # Single Edge case
            return True
        if "no_more_cards" in e.name:  # Second edge case
            return True
        if "change_color" in e.name:  # Third edge case
            return True
        if f"card_{card_type}" in e.name or card_color in e.name:
            return True
        return False

    return bp.EventSet(predicate)

def all_events_not_by_current_player(index: int):
    '''
    Return an EventSet that matches all events except those emitted by the given player.

    Parameters
    ----------
    index : int
        Player index used to identify player-specific event names (for example `p_0`).

    Returns
    -------
    bp.AllExcept
        An EventSet that is the complement of `bp.EventSet(lambda e: f'p_{index}' in e.name)`.
        Events whose `name` contains the substring `p_{index}` will be excluded.
    '''''
    def is_event_of_current_player(event):
        try:
            result = f"p_{index}" in getattr(event, "name", "") or f"deal_p" in getattr(event, "name", "")
            if not result:
                result = True if event.name == "next_turn" or event.name == "stop" else False
        except Exception as e:
            print(f"[DEBUG is_event_of_current_player] index={index} error reading event.name: {event}")
            raise
        return result


    return bp.AllExcept(bp.EventSet(is_event_of_current_player))

all_player_0_except_no_more_cards_and_last_card = bp.EventSet(
    lambda e: 'p_0' in e.name and not 'no_more_cards' in e.name and not 'last_card' in e.name)
all_player_1_except_no_more_cards_and_last_card = bp.EventSet(
    lambda e: 'p_1' in e.name and not 'no_more_cards' in e.name and not 'last_card' in e.name)

any_player_no_more_cards = bp.EventSet(lambda e: 'no_more_cards' in e.name)

announce_color_event_set = bp.EventSet(lambda e: 'announce_color' in e.name)


def get_player_id(name: str):
    player_reg_exp = re.compile(r"^p_(\d+)_")
    m = player_reg_exp.match(name)
    if m:
        id = int(m.group(1))
    else:
        id = None
    return id



def all_player_stop_card_events(player_index):
    def is_event_stop_card_event(event):
        pattern = fr"p_{player_index}_stop_\w+"
        if re.match(pattern, event.name) is not None:
            return True
        return False
    return bp.EventSet(is_event_stop_card_event)


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
    """
    Creates an EventSet that identifies cards matching NEITHER the given color NOR type.

    Enforces Taki's rule: players must match either color or type of the leading card.
    Returns an EventSet that blocks illegal moves (cards that match neither).

    Parameters
    ----------
    card_color : str
        The reference color: "blue", "red", or "green"
    card_type : str
        The reference type: "1", "3", "4", "5", "6", "7", "8", "9", "STOP", "PLUS_2"

    Returns
    -------
    bp.EventSet
        EventSet returning True for cards matching neither color nor type (illegal moves)

    Raises
    ------
    Exception
        If card_color or card_type are invalid

    Examples
    --------
    If the leading card is blue 5:
    blocked_set = create_cards_from_different_color_or_type_event_set("blue", "5")
    # Returns False (don't block): blue 3 (matches color)
    # Returns False (don't block): red 5 (matches type)
    # Returns False (don't block): blue 5 (matches both)
    # Returns True (block): red 3 (matches neither color nor type - illegal play)
    # Returns True (block): green 7 (matches neither color nor type - illegal play)
    """
    colors = ["blue", "red", "green"]
    types = ["1", "3", "4", "5", "6", "7", "8", "9", "STOP", "PLUS_2"]
    if card_color in colors and card_type in types:
        colors.remove(card_color)
        types.remove(card_type)
    elif card_type.startswith("CHANGE_COLOR") : # Special case for change_color card
        return bp.EventSet(lambda e: False)  # Don't block anything for change_color
    else:
        raise Exception(f"Wrong parameter to "
                        f"create_cards_from_different_color_or_type_event_set"
                        f"{card_color, card_type}")

    def cards_from_the_different_color_or_type(event):
        """
        Returns True for cards that match neither color nor type (should be blocked).

        Logic:
        - Never block "deal_p_" events (card dealing)
        - Don't block if color OR type matches (legal plays)
        - Block card events that match neither (illegal plays)
        - Don't block non-card events (return False by default)

        The OR condition identifies card events: after removing the reference color/type,
        `colors` and `types` contain all OTHER color/type values, so checking membership
        confirms this is an illegal play.
        """

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


def create_block_set_color_only(color: str):
    def is_play_event(e):
        return (
            isinstance(e, BPEvent)
            and re.match(r"^p_\d+_(card_\d+|stop|plus_2)_(red|green|blue)$", e.name) is not None
        )
    def to_block(e):
        if not is_play_event(e):
            return False
        if is_change_color_event(e):
            return False
        c, _ = extract_card_color_and_type(e)
        return c is not None and c != color
    return bp.EventSet(to_block)


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


def init_cards_events():

    all_cards = []
    # Init regular cards
    colors = ["red", "blue", "green"]
    numbers = ["1", "3", "4", "5"]
    for color in colors: # Add regular cards - 1 of each number and color
        for number in numbers:
            all_cards.append(BPEvent(name=f"card_{number}_{color}", priority=10.0))

    for color in colors: # Add color cards - 2 of each color
        all_cards.append(BPEvent(name=f"stop_{color}", priority=10.0))
        all_cards.append(BPEvent(name=f"stop_{color}", priority=10.0))

    for color in colors: # Add Change color cards - 2 of each color
        all_cards.append(BPEvent(name=f"change_color_{color}", priority=10.0))
        all_cards.append(BPEvent(name=f"change_color_{color}", priority=10.0))

    '''
    all_cards = [BPEvent(name="card_5_blue", data={}, priority=10.0),
         # BPEvent(name="stop_red", data={}, priority=10.0),
         BPEvent(name="card_5_blue", data={}, priority=10.0),
         # BPEvent(name="change_color", data={}, priority=10.0),
         # BPEvent(name="stop_blue", data={}, priority=10.0),
         BPEvent(name="card_1_red", data={}, priority=10.0),
         # BPEvent(name="plus_2_red", data={}, priority=10.0),
         BPEvent(name="card_4_blue", data={}, priority=10.0),
         # BPEvent(name="change_color", data={}, priority=10.0),
         # BPEvent(name="stop_green", data={}, priority=10.0),
         BPEvent(name="card_5_green", data={}, priority=10.0),
         # BPEvent(name="plus_2_green", data={}, priority=10.0),
         BPEvent(name="card_1_blue", data={}, priority=10.0),
         # BPEvent(name="change_color", data={}, priority=10.0),
         BPEvent(name="card_3_green", data={}, priority=10.0),
         BPEvent(name="card_1_green", data={}, priority=10.0),
         BPEvent(name="card_4_red", data={}, priority=10.0),
         # BPEvent(name="stop_red", data={}, priority=10.0),
         # BPEvent(name="change_color", data={}, priority=10.0),
         # BPEvent(name="plus_2_blue", data={}, priority=10.0),
         BPEvent(name="card_5_red", data={}, priority=10.0),
         BPEvent(name="card_4_green", data={}, priority=10.0),
         # BPEvent(name="stop_green", data={}, priority=10.0),
         BPEvent(name="card_3_blue", data={}, priority=10.0)]
         # BPEvent(name="stop_blue", data={}, priority=10.0),
         # BPEvent(name="plus_2_red", data={}, priority=10.0)]
    '''

    return all_cards

def is_plus_2_card_event(event: BPEvent) -> bool:
    """Check if event is a Plus 2 card"""
    return "plus_2" in event.name

def extract_plus_2_color(event: BPEvent) -> Optional[str]:
    """Extract color from Plus 2 card event"""
    if "plus_2" in event.name:
        return event.name.split("_")[-1]  # returns "red", "blue", or "green"
    return None

def is_change_color_event(event: BPEvent) -> bool:
    """Check if event is a change color card"""
    return "change_color" in event.name


def is_change_color_play(e) -> bool:
    # PLAY only: p_<i>_change_color
    return isinstance(e, BPEvent) and re.match(r"^p_\d+_change_color$", e.name) is not None

def is_announce_color_play(e) -> bool:
    # PLAY only: p_<i>_announce_color_(red|green|blue|ד)
    return isinstance(e, BPEvent) and re.match(r"^p_\d+_announce_color_(red|green|blue)$", e.name) is not None

def player_idx_of(event_name: str) -> int:
    m = re.match(r"^p_(\d+)_", event_name)
    return int(m.group(1)) if m else -1


@bp.thread
def game_manager():
    yield bp.sync(request=BPEvent("start_dealing_cards_to_players", priority=10.0))
    yield bp.sync(waitFor=BPEvent("finished_dealing_cards_to_players", priority=10.0))
    yield bp.sync(request=BPEvent("deal_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(request=BPEvent("start_game", priority=10.0))
    yield bp.sync(waitFor=any_player_no_more_cards)
    # End the game, the only event allowed is end_game
    yield bp.sync(request=BPEvent("end_game", priority=7.0),
                           block=bp.AllExcept(BPEvent("end_game", priority=7.0)))
    yield bp.sync(block=bp.All())


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
def is_deal_regular_card_event(event: BPEvent) -> bool:
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
                     if is_deal_regular_card_event(card)]
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

# Check if the following method could be removed in the future if not needed.
def select_color_for_change_color_card(index, card_events):
    """
    Selects a color after playing a change_color card.
    Prefers colors that the player has in their hand (chooses the most frequent).
    If tied, prefers in order: red, blue, green.
    If no colored cards remain, defaults to red.

    Parameters
    ----------
    index : int
        The player index
    card_events : list[BPEvent]
        The current cards in the player's hand

    Returns
    -------
    str
        The selected color: "red", "blue", or "green"
    """
    # Count available colors from remaining cards
    color_counts = {"red": 0, "blue": 0, "green": 0}
    available_colors = []

    for card in card_events:
        if card.name != f"p_{index}_draw_card":
            color, _ = extract_card_color_and_type(card)
            if color in color_counts:
                color_counts[color] += 1

    # Select color with the highest count, with deterministic tiebreaking (red > blue > green)
    max_count = max(color_counts.values())

    if max_count == 0:
        return "red"  # No colored cards, default to red

    # Return first color (in priority order) with max count
    for color in ["red", "blue", "green"]:
        if color_counts[color] == max_count:
            return color


# A regular card is a card with a number (1-9) and a color (red, blue, green).
# a possible input event to this method is p_1_card_4_blue
def is_regular_card_event(event: BPEvent) -> bool:
    card_event_pattern = r"p_\d+_card_\d+_\w+"
    if re.match(card_event_pattern, event.name) is not None:
        return True
    return False


def is_draw_card_event(event: BPEvent) -> bool:
    draw_card_pattern = r"p_\d+_draw_card"
    if re.match(draw_card_pattern, event.name) is not None:
            return True
    return False

def is_action_card_event(event: BPEvent) -> bool:
    action_card_pattern = r"p_\d+_(change_color|plus_2_\w+|stop_\w+)"
    if re.match(action_card_pattern, event.name) is not None:
            return True
    return False

def is_stop_card_event(event: BPEvent) -> bool:
    stop_card_pattern = r"p_\d+_stop_\w+"
    if re.match(stop_card_pattern, event.name) is not None:
            return True
    return False

# TODO: Remove this b-thread if it's continues to be unused.
@bp.thread
def post_stop_card_handler():
    while True:
        stop_event = yield bp.sync(waitFor=bp.EventSet(is_stop_card_event))
        print(f"[post_stop_card_handler] stop card event detected: {stop_event.name}")
        last_event = yield bp.sync(waitFor=BPEvent("finished_stop_card", priority=9.0))
        print(f"[post_stop_card_handler] recieved the finished_stop_card event")
        yield bp.sync(request=BPEvent("done_post_action", priority=10.0))
        print(f"[post_stop_card_handler] requested done_post_action for event: {stop_event.name}")


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

    # Add draw_card_event to the cards events(Possible actions of player)
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    card_events.append(draw_card_event)

    while True:
        card_event = yield bp.sync(request=card_events)

        if is_regular_card_event(card_event):
            card_events.remove(card_event)
        # If there is a draw card event, wait for a card to be dealt.
        elif is_draw_card_event(card_event):
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            card_events.append(BPEvent(card_name, priority=deal_card_event.priority))
        # If this is an action card - wait for done_post_action event.
        elif is_action_card_event(card_event):
            yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
            card_events.remove(card_event)

        # If the only event left is draw_card, break and end the game.
        if list_contains_only_draw_card_event(card_events):
            yield bp.sync(request=BPEvent(f"p_{index}_no_more_cards", priority=8.0))
            break
        else: # else announce that you have finished your turn.
            # print(f"Player {index} finished turn with cards: {[e.name for e in card_events if e.name != draw_card_event.name]}")
            yield bp.sync(request=BPEvent("next_turn", priority=10.0))



def extract_card_color(event: BPEvent) -> str:
    card_str_index = event.name.find("card")
    card_color = event.name[card_str_index + 7:]
    return card_color


def extract_card_number(event: BPEvent) -> str:
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
        tuple[str, str]: (color, "STOP") if the event is a stop event.
        tuple[str, str]: (color, "PLUS_2") if the event is a plus_2 event.
        tuple[str, str]: ("", "CHANGE_COLOR") if the event is a change_color event.
        tuple[None, None]: (None, None) if neither card nor stop information is found.

    Example:
        - For event.name == "card_5_blue", returns ("blue", "5")
        - For event.name == "stop_red", returns ("red", "STOP")
        - For event.name == "plus_2_red", returns ("red", "PLUS_2")
        - For event.name == "change_color", returns ("", "CHANGE_COLOR")
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
                change_color_index = event.name.find("change_color")
                if change_color_index != -1:
                    # Extract color from patterns like "change_color_red" or "p_0_change_color_red"
                    parts = event.name.split("_")
                    if len(parts) >= 3 and parts[-2] == "color":
                        color = parts[-1]
                        if color in ["red", "blue", "green"]:
                            return color ,"CHANGE_COLOR"
                        else:
                            print("Received change_color event with no color specified, defaulting to empty string.")
                            return "", "CHANGE_COLOR"
                else: # card is unmatched - return None, None
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
        # print("[is_color_or_type_card_event]: Plus 2 card detected")
        return True

    return False


@bp.thread
def enforce_turns(num_of_players=2):
    next_or_stop_lst = [BPEvent("next_turn", priority=10.0), bp.EventSet(is_stop_card_event)]
    next_turn_or_stop_event_set = bp.EventSetList(next_or_stop_lst)

    yield bp.sync(waitFor=BPEvent("start_game"))

    current_player = 0
    next_player = (current_player + 1) % num_of_players
    while True: # We should block the other player from playing out of turn in all the while loop.
        last_event = yield bp.sync(waitFor=next_turn_or_stop_event_set,
                      block=all_other_player_cards_besides_special_cards(current_player))

        if last_event.name.startswith("next_turn"):
            current_player = next_player
            next_player = (next_player + 1) % num_of_players
        if last_event.name.startswith(f"p_{current_player}_stop"):
            next_player = (next_player + 1) % num_of_players
            yield bp.sync(request=BPEvent("done_post_action", priority=10.0),
                                   block=all_other_player_cards_besides_special_cards(current_player))


@bp.thread
def enforce_card_placement_rules():
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    card_color, card_type = extract_card_color_and_type(event=last_event)
    different_colors_or_types_event_set = bp.EventSetsDifference(all_player_events(), init_selected_color_or_type_event_set(card_color,card_type))
    last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_or_types_event_set)

    while True:
        if is_regular_card_event(last_event):
            card_color, card_type = extract_card_color_and_type(event=last_event)
            different_colors_or_types_event_set = bp.EventSetsDifference(all_player_events(),
                                                                         init_selected_color_or_type_event_set(
                                                                             card_color, card_type))

        elif is_change_color_event(last_event):
            card_color, card_type = extract_card_color_and_type(event=last_event)
            different_colors_or_types_event_set = create_block_set_color_only(card_color)
            yield bp.sync(request=BPEvent("done_post_action", priority=10.0))

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

'''
@bp.thread
def verify_turn_alternation():
    yield bp.sync(waitFor=BPEvent("start_game"))

    last_acting_player = None

    while True:
        # Wait for any game event (not just player actions)
        event = yield bp.sync(waitFor=bp.EventSet(lambda e: True))

        if event.name.startswith("p_"):
            # Determine which player acted
            acting_player = 0 if event.name.startswith("p_0_") else 1

            if last_acting_player is not None and acting_player == last_acting_player:
                raise AssertionError(
                    f"[Verifier ❌] Turn violation: Player {acting_player} acted twice in a row: {event}"
                )

            last_acting_player = acting_player
'''



@bp.thread
def verify_turn_alternation():
    yield bp.sync(waitFor=BPEvent("start_game"))

    active_player_id = None  # ID of the player currently allowed to act
    turn_boundary_cleared = True  # Has 'next_turn' been seen since the last turn began?

    while True:
        event = yield bp.sync(waitFor=bp.EventSet(lambda e: True))

        if event.name == "end_game":
            break

        if event.name == "next_turn":
            if turn_boundary_cleared and active_player_id is None:
                bp.log("verify_turn_alternation: duplicate next_turn (noop)")
            # Ready for a new turn
            turn_boundary_cleared = True
            active_player_id = None
            continue

        # Get the player who triggered the event
        event_player_id = get_player_id(event.name)
        if event_player_id is None:
            continue

        # --- Check Turn Logic ---

        # 1. Start of a turn (active_player_id is None)
        if active_player_id is None:
            # Check for illegal player switch (e.g., P0 acts, then P1 acts immediately without next_turn)
            # This check is complex in the original, relying on saw_next_turn
            if not turn_boundary_cleared:  # This case should ideally not be reachable if logic is sound elsewhere
                raise AssertionError(
                    f"[Verifier] Player {event_player_id} acted before 'next_turn': {event}"
                )

            # Establish the active player for this turn
            active_player_id = event_player_id
            turn_boundary_cleared = False
            continue

        # 2. Mid-turn action (active_player_id is defined)
        if event_player_id != active_player_id:
            # Another player acted without a 'next_turn' in between → violation
            raise AssertionError(
                f"[Verifier] Player {event_player_id} acted during Player "
                f"{active_player_id}'s turn without 'next_turn'. Event={event}, "
                f"turn_boundary_cleared={turn_boundary_cleared}"
            )
        # else: same active_player_id again within the same turn → OK (multi-action turn)


@bp.thread
def assert_change_color_announcer_is_same_player():
    # wait until the real game starts
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    while True:
        wild = yield bp.sync(waitFor=bp.EventSet(is_change_color_play))
        wild_p = player_idx_of(wild.name)

        announce = yield bp.sync(waitFor=bp.EventSet(is_announce_color_play))
        ann_p = player_idx_of(announce.name)

        assert ann_p == wild_p, (
            f"[ASSERT] announce_color by p_{ann_p} but change_color was by p_{wild_p} "
            f"(wild={wild.name}, announce={announce.name})"
        )


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
                                      enforce_turns(),
                                      enforce_card_placement_rules(),
                                      identify_deadlock(),
                                      verify_turn_alternation()],
                                      # enforce_last_card_announcement(),
                                      # apply_penalty(),
                                     # detect_illegal_post_game_moves()],
                                     # ()],
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
