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
import logging
from datetime import datetime
from log_b_program_runner_listener import LogBProgramRunnerListener

NUM_OF_CARDS = 6
NUM_OF_PLAYERS = 2

# Control the randomness of card dealing
SEED = 0

LOG_LEVEL = logging.INFO


current_time = datetime.now().strftime("%d_%m_%Y-%H_%M_%S")
log_filename = f"taki_game_{current_time}.log"
logger = logging.getLogger("TakiGame")
logger.setLevel(LOG_LEVEL)

random.seed(SEED)
logger.info(f"Random seed for card dealing: {SEED}")

leading_card_event_set = bp.EventSet(lambda e: e.name.startswith('leading_'))

# A bypass for EventSetUnify
pattern = r"(p_\d+_(draw_card|card_\d+_\w+|last_card|stop_\w+|plus_2_\w+|change_color|taki_\w+|super_taki))|end_game"
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
        # 🔍 DEBUG: Track what gets allowed/blocked (VERY VERBOSE)
        allowed = False
        reason = ""

        # System events that are always allowed regardless of placement rules
        if "draw_card" in e.name:
            allowed = True
            reason = "draw_card always allowed"
        elif "no_more_cards" in e.name:
            allowed = True
            reason = "no_more_cards always allowed"
        elif "change_color" in e.name:
            allowed = True
            reason = "change_color is wild card"
        elif "super_taki" in e.name:
            allowed = True
            reason = "super_taki is wild card"
        elif "closed_taki" in e.name:  # Fifth edge case - allow closing TAKI sequences
            allowed = True
            reason = "closed_taki always allowed"
        elif f"card_{card_type}" in e.name or card_color in e.name:
            allowed = True
            reason = f"matches color={card_color} or type={card_type}"

        # If execution reaches this point, the event is about to be blocked.
        # We check if it is a "taki" card to verify if we are accidentally blocking a valid Taki-on-Taki move.
        if "taki" in e.name and card_type == "TAKI":
            logger.debug(f"[RULES] ❌ Blocking TAKI play: {e.name} on top of {card_type}/{card_color}")


        # 🔍 DEBUG: logger.debug only when checking TAKI cards (reduce noise)
        if "taki" in e.name.lower() or allowed:
            symbol = "✓" if allowed else "✗"
            logger.debug(f"[PLACEMENT_CHECK] {symbol} {e.name:30} | Reason: {reason if allowed else 'no match'}")

        return allowed

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
            logger.info(f"[DEBUG is_event_of_current_player] index={index} error reading event.name: {event}")
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
    """
    Creates an EventSet that blocks cards of colors different from the specified color.

    Used after a change_color card is played to enforce that the next card played
    must match the newly selected color. However, special cards like change_color
    and super_taki can bypass this color restriction.

    Parameters
    ----------
    color : str
        The required color that cards must match. Must be one of: "red", "green", "blue"

    Returns
    -------
    bp.EventSet
        An EventSet that returns True for play events that should be blocked
        (i.e., cards that don't match the required color and aren't special bypass cards)

    Examples
    --------
    After a change_color card selects "blue":
    block_set = create_block_set_color_only("blue")
    # Blocks: p_0_card_5_red, p_0_stop_green, p_0_plus_2_red
    # Allows: p_0_card_3_blue, p_0_stop_blue, p_0_super_taki, p_0_change_color

    Notes
    -----
    This function is specifically designed for use after change_color cards,
    where color matching is enforced but special cards can still be played.
    """

    def is_play_event(e):
        """
        Determines if an event is a card play event (as opposed to system events
        like draw_card, next_turn, etc.).

        Recognizes two categories of play events:
        1. Colored cards: regular cards, stop, and plus_2 with color suffixes
        2. Super Taki: special card without a color suffix

        Parameters
        ----------
        e : BPEvent
            The event to check

        Returns
        -------
        bool or Match object
            Returns a truthy value (Match object) if the event is a play event,
            None (falsy) otherwise

        Examples
        --------
        is_play_event(BPEvent("p_0_card_5_blue"))  # Returns Match object (truthy)
        is_play_event(BPEvent("p_0_super_taki"))   # Returns Match object (truthy)
        is_play_event(BPEvent("p_0_draw_card"))    # Returns None (falsy)
        is_play_event(BPEvent("next_turn"))        # Returns None (falsy)

        Notes
        -----
        The regex patterns are:
        - r"^p_\d+_(card_\d+|stop|plus_2)_(red|green|blue)$" for colored cards
        - r"^p_\d+_super_taki$" for super_taki (no color suffix)
        """
        # Match colored cards OR super_taki (which has no color suffix)
        return (
                isinstance(e, BPEvent)
                and (re.match(r"^p_\d+_(card_\d+|stop|plus_2|taki)_(red|green|blue)$", e.name) is not None
                     or re.match(r"^p_\d+_super_taki$", e.name) is not None)
        )

    def to_block(e):
        """
        Determines if a play event should be blocked based on color mismatch.

        The blocking logic follows these rules:
        1. Non-play events (e.g., draw_card, next_turn) are never blocked
        2. change_color cards bypass color restrictions (can be played on any color)
        3. super_taki cards bypass color restrictions (can be played on any color)
        4. All other play events are blocked if their color doesn't match the required color

        Parameters
        ----------
        e : BPEvent
            The event to evaluate for blocking

        Returns
        -------
        bool
            True if the event should be blocked (color mismatch), False otherwise

        Examples
        --------
        When the required color is "blue":
        to_block(BPEvent("p_0_card_5_red"))      # True - wrong color
        to_block(BPEvent("p_0_card_3_blue"))     # False - correct color
        to_block(BPEvent("p_0_super_taki"))      # False - bypass card
        to_block(BPEvent("p_0_change_color"))    # False - bypass card
        to_block(BPEvent("p_0_draw_card"))       # False - not a play event

        Notes
        -----
        This function is called by the EventSet for each event to determine
        if it should be included in the blocked set. The EventSet will then
        prevent any blocked events from being selected during event selection.
        """
        # Ignore non-play events (like draw_card, next_turn, etc.)
        if not is_play_event(e):
            return False

        # change_color cards can be played regardless of current color requirement
        if is_change_color_event(e):
            return False

        # Super Taki can be played on any card regardless of color
        if "super_taki" in e.name:
            return False

        # For all other play events, block if color doesn't match
        c, _ = extract_card_color_and_type(e)
        return c is not None and c != color

    return bp.EventSet(to_block)


def create_taki_color_block(color: str) -> bp.EventSet:
    """
    During a TAKI sequence of color `color`, block any *colored* card
    whose color is different from `color`.

    Cards with no color (draw_card, done_post_action, super_taki, etc.)
    are untouched by this block.
    """
    def to_block(e: BPEvent) -> bool:
        if not isinstance(e, BPEvent):
            return False

        card_color, _ = extract_card_color_and_type(e)

        # If the event has no color (None or ""), don't constrain it here
        # These are events like: draw_card, done_post_action, deadlock, super_taki and closed_taki.
        if not card_color:
            logger.debug(f"[TAKI_BLOCK] ALLOW non-colored event: {e.name} during TAKI({color})")
            return False

        # Block any colored card with a different color than the TAKI color
        should_block = (card_color != color)

        # Core debug line: every colored card checked against TAKI color
        logger.debug(
            f"[TAKI_BLOCK] CHECK event={e.name} "
            f"(card_color={card_color}, TAKI_color={color}) "
            f"-> {'BLOCK' if should_block else 'allow'}"
        )

        return should_block

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

    # for color in colors:
    #    all_cards.append(BPEvent(name=f"plus_2_{color}", priority=10.0))
    #    all_cards.append(BPEvent(name=f"plus_2_{color}", priority=10.0))

    # Add Regular Taki cards - 2 of each color
    for color in colors:
        all_cards.append(BPEvent(name=f"taki_{color}", priority=10.0))
        all_cards.append(BPEvent(name=f"taki_{color}", priority=10.0))

    all_cards.append(BPEvent(name=f"super_taki", priority=10.0))
    all_cards.append(BPEvent(name=f"super_taki", priority=10.0))

    return all_cards


def is_taki_card_event(event: BPEvent) -> bool:
    """Check if event is a regular taki card (not super taki)"""
    result =  isinstance(event, BPEvent) and re.match(r"^p_\d+_taki_(red|blue|green)$", event.name) is not None
    # if result:
    #     logger.debug(f"[DEBUG is_taki_card_event] ✓ Regular TAKI detected: {event.name}")
    return result

def is_any_taki_event(e):
    """Check if event is any type of TAKI card (regular or super)"""
    result = is_taki_card_event(e) or is_super_taki_event(e)
    # if result:
    #    taki_type = "Regular TAKI" if is_taki_card_event(e) else "Super TAKI"
    #    logger.debug(f"[DEBUG is_any_taki_event] ✓ {taki_type} detected: {e.name}")
    return result

def is_plus_2_card_event(e: BPEvent) -> bool:
    return isinstance(e, BPEvent) and re.match(r"^p_\d+_plus_2_\w+$", e.name) is not None

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


def list_does_not_contain_card_events(events: list[BPEvent]) -> bool:
    """
    Return True iff there are no more real card events in the list, i.e.,
    the only remaining actions are 'draw_card' and/or 'closed_taki'.

    This lets the player declare 'no_more_cards' when they have no playable
    cards left in hand (other than drawing).
    """
    if not events: # Defensive: shouldn't really happen, but treat as "no cards"
        return True

    for e in events:
        if "_draw_card" in e.name or "_closed_taki" in e.name:
            continue
        # Any other event means there is still at least one card in hand
        return False

    # We saw only draw/closed_taki
    return True


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
    action_card_pattern = r"p_\d+_(change_color|plus_2_\w+|stop_\w+|taki_\w+|super_taki)"
    if re.match(action_card_pattern, event.name) is not None:
            return True
    return False

def is_stop_card_event(event: BPEvent) -> bool:
    stop_card_pattern = r"p_\d+_stop_\w+"
    if re.match(stop_card_pattern, event.name) is not None:
            return True
    return False

def extract_player_id(event: BPEvent) -> Optional[int]:
                """Extract player ID from event name (e.g., p_0_card -> 0)"""
                player_reg_exp = re.compile(r"^p_(\d+)_")
                m = player_reg_exp.match(event.name)
                if m:
                    return int(m.group(1))
                else:
                    return None


def is_super_taki_event(e):
    ans = isinstance(e, BPEvent) and re.match(r"^p_\d+_super_taki$", e.name) is not None
    return ans

def is_closed_taki_event(e):
    """Check if event is a closed_taki event signaling the end of a super taki sequence"""
    return isinstance(e, BPEvent) and re.match(r"^p_\d+_closed_taki$", e.name) is not None


def add_dummy_events(index, card_events, color):
    numbers = ["1", "3", "4", "5"]
    for number in numbers:
        logger.debug(f"[add_dummy_events]: card_{number}_{color} for player: {index}")
        card_events.append(BPEvent(name=f"p_{index}_card_{number}_{color}", priority=10.0))


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
            if is_any_taki_event(card_event):
                # 🔍 DEBUG: TAKI sequence start
                taki_type = "Regular TAKI" if is_taki_card_event(card_event) else "Super TAKI"
                logger.debug(f"{'=' * 60}")
                logger.debug(f"[PLAYER_{index}] 🎴 {taki_type} SEQUENCE STARTING: {card_event.name}")
                logger.debug(f"[PLAYER_{index}] Removing TAKI from hand")
                logger.debug(f"[PLAYER_{index}] Adding closed_taki to possible actions")
                logger.debug(f"{'=' * 60}")

                card_events.remove(card_event) # Remove TAKI / Super_TAKI from player hand
                
				# Add closed_taki event to the possible actions of the player, the correct priority here is crucial!
                closed_taki_event = BPEvent(f"p_{index}_closed_taki", priority=15.0)
                card_events.append(closed_taki_event)

                cards_played_in_taki = []

                while True:
                    card_event = yield bp.sync(request=card_events)

                    if card_event.name != f"p_{index}_closed_taki":
                        cards_played_in_taki.append(card_event.name)
                        logger.debug(f"[PLAYER_{index}] 🃏 Card played in TAKI: {card_event.name}")

                    card_events.remove(card_event)
                    if card_event.name == f"p_{index}_closed_taki":
                        # 🔍 DEBUG: TAKI sequence end
                        logger.debug(f"{'=' * 60}")
                        logger.debug(f"[PLAYER_{index}] 🛑 TAKI SEQUENCE ENDING")
                        logger.debug(f"[PLAYER_{index}] Cards played: {cards_played_in_taki}")
                        logger.debug(f"[PLAYER_{index}] Total cards in sequence: {len(cards_played_in_taki)}")
                        logger.debug(f"{'=' * 60}")
                        break

                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
            else:
                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
                card_events.remove(card_event)

        # If the only event left is draw_card, break and end the game.
        if list_does_not_contain_card_events(card_events):
            yield bp.sync(request=BPEvent(f"p_{index}_no_more_cards", priority=8.0))
            break
        else: # else announce that you have finished your turn.
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
        - For event.name == "super_taki", returns (None, "SUPER_TAKI")
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
                            logger.debug("Received change_color event with no color specified, defaulting to empty string.")
                            return "", "CHANGE_COLOR"
                else:
                    super_taki_index = event.name.find("super_taki")
                    if super_taki_index != -1:
                        return None, "SUPER_TAKI"
                    else:
                        taki_str_index = event.name.find("taki_")
                        if taki_str_index != -1:
                            parts = event.name.split("_")
                            color = parts[-1]
                            if color in ["red", "blue", "green"]:
                                logger.debug(f"[DEBUG extract_card_color_and_type] Regular TAKI: {event.name} → Color: {color}, Type: TAKI")
                                return color, "TAKI"
                        else: # card is unmatched - return None, None
                            return None, None


def is_color_card_event(event: BPEvent) -> bool:
    for color in ["blue", "red", "green"]:
        if color in event.name:
            return True
    return False


@bp.thread
def enforce_turns(num_of_players=2):
    next_or_stop_or_taki_lst = [BPEvent("next_turn", priority=10.0), bp.EventSet(is_stop_card_event), bp.EventSet(is_any_taki_event)]
    next_turn_or_stop_or_taki_event_set = bp.EventSetList(next_or_stop_or_taki_lst)

    yield bp.sync(waitFor=BPEvent("start_game"))

    current_player = 0
    next_player = (current_player + 1) % num_of_players
    while True: # We should block the other player from playing out of turn in all the while loop.
        last_event = yield bp.sync(waitFor=next_turn_or_stop_or_taki_event_set,
                      block=all_other_player_cards_besides_special_cards(current_player))

        logger.debug(f"[ENFORCE_TURNS] Event received: {last_event.name}")

        if last_event.name.startswith("next_turn"): # 🔍 DEBUG: Turn change
            logger.debug(f"[ENFORCE_TURNS] Turn change: Player {current_player} → Player {next_player}")
            current_player = next_player
            next_player = (next_player + 1) % num_of_players

        if last_event.name.startswith(f"p_{current_player}_stop"): # stop_card
            next_player = (next_player + 1) % num_of_players
            logger.debug(f"[ENFORCE_TURNS] Stop card played by Player {current_player}, next player is: {next_player}")
            yield bp.sync(request=BPEvent("done_post_action", priority=10.0),
                                   block=all_other_player_cards_besides_special_cards(current_player))

        if is_any_taki_event(last_event):# Super TAKI or TAKI played
            taki_type = "Regular TAKI" if is_taki_card_event(last_event) else "Super TAKI"
            logger.debug(f"[ENFORCE_TURNS] 🎴 {taki_type} by Player {current_player}, requesting done_post_action")
            yield bp.sync(request=BPEvent("done_post_action", priority=17.5), # priority here is higher than draw_card, but lower than closed_taki
                                  block=all_other_player_cards_besides_special_cards(current_player))
            logger.debug(f"[ENFORCE_TURNS] ✓ done_post_action completed for {taki_type}")

def get_taki_mode_color(last_event, card_color):

    # If it's a regular Taki, the color is determined by the card itself.
    # Note that the TAKI color is relevant when TAKI is played on top of another TAKI (TAKI,"yellow") on top of (TAKI,"green").
    # If it's Super Taki, it inherits the previous color (which is already in card_color).
    if is_taki_card_event(last_event):
        card_color, card_type = extract_card_color_and_type(last_event)
        logger.debug(f"{'=' * 60}")
        logger.debug(f"[ENFORCE_RULES] 🎴 Regular TAKI detected: {last_event.name}")
        logger.debug(f"[ENFORCE_RULES] Color determined by TAKI card: {card_color}")
        logger.debug(f"[ENFORCE_RULES] Blocking all non-{card_color} cards")
        logger.debug(f"{'=' * 60}")
    else:
        logger.debug(f"{'=' * 60}")
        logger.debug(f"[ENFORCE_RULES] 🌟 Super TAKI detected: {last_event.name}")
        logger.debug(f"[ENFORCE_RULES] Color inherited from previous card: {card_color}")
        logger.debug(f"[ENFORCE_RULES] Blocking all non-{card_color} cards")
        logger.debug(f"{'=' * 60}")

    return card_color


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

        elif is_any_taki_event(last_event):

            logger.debug(f"{'=' * 60}")
            logger.debug(f"[ENFORCE_RULES] ENTER TAKI MODE, last_event={last_event.name}")
            logger.debug(f"[ENFORCE_RULES] Previous placement color={card_color}")
            logger.debug(f"{'=' * 60}")

            card_color = get_taki_mode_color(last_event, card_color) # Get the color for the TAKI mode

            strict_color_block = create_taki_color_block(card_color)

            last_taki_card_color = card_color
            last_taki_card_type = card_type

            taki_sequence_cards = []

            taki_wait_events = bp.EventSetList([general_player_event_set, BPEvent("done_post_action", priority=17.5)])

            while True:
                # Note: we do NOT handle `closed_taki` here.
                # The TAKI sequence is considered finished when `done_post_action`
                # (requested by `enforce_turns`) occurs. This keeps turn lifecycle
                # centralized in `enforce_turns`, and this b-thread only enforces
                # placement rules and tracks the last TAKI card.
                logger.debug(f"[ENFORCE_RULES] Waiting for card (must be {card_color}) or done_post_action.")

                taki_event = yield bp.sync(waitFor=taki_wait_events, block=strict_color_block)

                logger.debug(f"[ENFORCE_RULES] Event received: {taki_event.name}")

                # Check if TAKI sequence ended
                if taki_event.name == "done_post_action":
                    logger.debug(f"{'=' * 60}")
                    logger.debug(f"[ENFORCE_RULES] 🛑 TAKI sequence ended")
                    logger.debug(f"[ENFORCE_RULES] Cards played in sequence: {taki_sequence_cards}")
                    logger.debug(f"[ENFORCE_RULES] Last card color: {last_taki_card_color}, type: {last_taki_card_type}")
                    logger.debug(f"{'=' * 60}")
                    break

                # Update tracking with each card played during TAKI
                if is_regular_card_event(taki_event) or is_change_color_event(taki_event) or is_stop_card_event(taki_event):
                    taki_sequence_cards.append(taki_event.name)
                    last_taki_card_color, last_taki_card_type = extract_card_color_and_type(taki_event)
                    logger.debug(
                        f"[ENFORCE_RULES] ✓ Card accepted during TAKI: {taki_event.name} "
                        f"(color={last_taki_card_color}, type={last_taki_card_type})"
                    )
                else:
                    logger.info( # Catch untracked cards!
                        f"\n[ENFORCE_RULES] ⚠️ WARNING: Event '{taki_event.name}' was allowed in TAKI sequence but NOT TRACKED!")
                    logger.info(f"[ENFORCE_RULES] The 'last_card' state was NOT updated. Next player might face wrong rules.\n")

            # Update placement rules based on the last card from the TAKI sequence
            card_color, card_type = last_taki_card_color, last_taki_card_type
            different_colors_or_types_event_set = bp.EventSetsDifference(all_player_events(),
                                                                         init_selected_color_or_type_event_set(
                                                                             card_color, card_type))
            logger.debug(f"[ENFORCE_RULES] Post-TAKI placement rules: must match color={card_color} OR type={card_type}")

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
                logger.debug("verify_turn_alternation: duplicate next_turn (noop)")
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


def setup_logger():

    # Console Handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(LOG_LEVEL)
    c_format = logging.Formatter('%(asctime)s.%(msecs)03d - %(message)s', datefmt='%H:%M:%S')
    c_handler.setFormatter(c_format)

    # File Handler
    f_handler = logging.FileHandler(log_filename, mode='w')
    f_handler.setLevel(LOG_LEVEL)
    f_format = logging.Formatter('%(asctime)s.%(msecs)03d - %(message)s', datefmt='%H:%M:%S')
    f_handler.setFormatter(f_format)

    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
        logger.debug(f"--> Logger configured. Saving to: {log_filename}")


def init_b_program():
    b_program = bp.BProgram(bthreads=[game_manager(),
                                      deal_cards(2, NUM_OF_CARDS),
                                      player_behavior(0, NUM_OF_CARDS),
                                      player_behavior(1, NUM_OF_CARDS),
                                      enforce_turns(),
                                      enforce_card_placement_rules(),
                                      identify_deadlock(),
                                      verify_turn_alternation()],
                                     # detect_illegal_post_game_moves()],
                            event_selection_strategy=EventPrioritySelectionStrategy(),
                            listener=LogBProgramRunnerListener(logger=logger))
    return b_program


def regular_execution_of_bp_program():
    setup_logger()
    logger.info("Starting Taki Game BProgram Execution")
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
