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

random.seed(0)

leading_card_event_set = bp.EventSet(lambda e: e.name.startswith('leading_'))

pattern = pattern = r"(p_\d+_(draw_card|card_\d+_\w+))|end_game"
general_player_event_set = bp.EventSet(lambda e:
    hasattr(e, 'name') and re.match(pattern, e.name) is not None
)
#Maybe we should support union of EventSets, like this case.
all_player_0_except_no_more_cards = bp.EventSet(lambda e: 'p_0' in e.name and not 'no_more_cards' in e.name)
all_player_1_except_no_more_cards = bp.EventSet(lambda e: 'p_1' in e.name and not 'no_more_cards' in e.name)

any_player_no_more_cards = bp.EventSet(lambda e: 'no_more_cards' in e.name)

def is_event_draw_card_event(player_index, event):
    if f"p_{player_index}_draw_card" == event.name:
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
        colors = ["blue", "red","green"]
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
        if number==current_card_number:
            return False
        elif current_card_number in numbers:
            return True
        else:
            return False

    return bp.EventSet(cards_from_the_different_number)

def create_cards_from_different_number_or_color_event_set(card_color, card_number):
    colors = ["blue", "red", "green"]
    numbers = ["1", "3", "4", "5", "6", "7", "8", "9"]
    if card_color in colors and card_number in numbers:
        colors.remove(card_color)
        numbers.remove(card_number)
    else:
        raise Exception(f"Wrong parameter to "
                        f"create_cards_from_different_number_or_"
                        f"color_event_set: {card_color,card_number}")

    def cards_from_the_different_color_or_number(event):
        # Edge case, we don't want to block events from different
        # colors/number if they are a new card being dealt.
        if event.name.startswith("deal_p_"):
            return False
        t_card_color, t_card_number = extract_card_color_and_number(event)
        if t_card_color == card_color or t_card_number == card_number:
            return False
        elif t_card_color in colors or t_card_number in numbers:
            return True
        else: # default return false.
            return False

    return bp.EventSet(cards_from_the_different_color_or_number)


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
            raise TypeError(f"Player_{self.index}_DealCardsPlayerEventSet: Expected item of type BPEvent, got {type(item)}")

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

def create_and_shuffle_cards():
    # option 2:
    all_cards = [BPEvent(name="card_8_red", data={}, priority=10.0),
                 BPEvent(name="card_1_blue", data={}, priority=10.0),
                 BPEvent(name="card_9_green", data={}, priority=10.0),
                 BPEvent(name="card_4_green", data={}, priority=10.0),
                 BPEvent(name="card_8_blue", data={}, priority=10.0),
                 BPEvent(name="card_7_blue", data={}, priority=10.0),
                 BPEvent(name="card_9_blue", data={}, priority=10.0),
                 BPEvent(name="card_4_red", data={}, priority=10.0),
                 BPEvent(name="card_8_green", data={}, priority=10.0),
                 BPEvent(name="card_6_green", data={}, priority=10.0),
                 BPEvent(name="card_6_blue", data={}, priority=10.0),
                 BPEvent(name="card_4_blue", data={}, priority=10.0),
                 BPEvent(name="card_7_green", data={}, priority=10.0),
                 BPEvent(name="card_5_blue", data={}, priority=10.0),
                 BPEvent(name="card_3_green", data={}, priority=10.0),
                 BPEvent(name="card_5_red", data={}, priority=10.0),
                 BPEvent(name="card_5_green", data={}, priority=10.0),
                 BPEvent(name="card_3_red", data={}, priority=10.0),
                 BPEvent(name="card_6_red", data={}, priority=10.0),
                 BPEvent(name="card_9_red", data={}, priority=10.0),
                 BPEvent(name="card_1_green", data={}, priority=10.0),
                 BPEvent(name="card_1_red", data={}, priority=10.0),
                 BPEvent(name="card_3_blue", data={}, priority=10.0),
                 BPEvent(name="card_7_red", data={}, priority=10.0)]
    return all_cards

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


@bp.thread
def deal_cards(num_of_players=2, num_of_cards=2):
    yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))
    cards = create_and_shuffle_cards()
    for i in range(num_of_players):
        for j in range(num_of_cards):
            card_event = cards.pop()
            deal_player_card_event = BPEvent("deal_p_" + str(i) + "_" + card_event.name, priority=10.0)
            yield bp.sync(request= deal_player_card_event)
    yield bp.sync(request=BPEvent("finished_dealing_cards_to_players", priority=10.0))

    # Deal the leading card
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    top_card = cards.pop()
    yield bp.sync(request=BPEvent(f"leading_{top_card.name}", priority=10.0))
    yield bp.sync(request=BPEvent("finished_leading_card", priority=10.0))

    while True:
        last_event = yield bp.sync(waitFor=[BPEvent("p_0_draw_card"), BPEvent("p_1_draw_card")])
        player_index = 0 if "p_0" in last_event.name else 1
        if not cards: # imagine an infinite pile of cards.
            cards = create_and_shuffle_cards()
        card_event = cards.pop()
        deal_player_card_event = BPEvent("deal_p_" + str(player_index) + "_" + card_event.name, priority=9.0)
        other_player_cards_event_set = PlayerEventSet(1-player_index)
        yield bp.sync(request=deal_player_card_event)

def remove_deal_prefix_from_event(event):
    card_name = event.name.removeprefix("deal_")
    return card_name

def list_contains_only_draw_card_event(action_events):
    if len(action_events) == 1 and "_draw_card" in action_events[0].name:
        return True
    return False

@bp.thread
def player_behavior(index, num_of_cards=2):
    yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))
    action_events = []
    deal_player_cards_event_set = DealCardsPlayerEventSet(index)
    for i in range(num_of_cards):
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_from_event(deal_card_event)
        action_events.append(BPEvent(card_name, priority=10.0))

    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    # Add draw_card_event to the cards events(Possible actions of player)
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    action_events.append(draw_card_event)

    while True:
        event = yield bp.sync(waitFor=general_player_event_set, request=action_events)
        if event.name.startswith(f"p_{index}_card"):
            action_events.remove(event)
            # If the only event left is draw_card, break and end the game.
            if list_contains_only_draw_card_event(action_events):
                yield bp.sync(request=BPEvent(f"p_{index}_no_more_cards ", priority=8.0))
                break
        # If there is a draw card event, wait for a card to be dealt.
        if event.name.startswith(f"p_{index}_draw_card"):
            # if we want to simulate a deadlock - add the following block   - block=bp.AllExcept(BPEvent("deadlock"))
            # deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set, block=bp.AllExcept(BPEvent("deadlock")))
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_from_event(deal_card_event)
            action_events.append(BPEvent(card_name, priority=10.0))
        # If the other player ended the game.
        if event.name.startswith(f"end_game"): # similar to breakupon.
            break

def extract_card_color(event: BPEvent) -> str:
    card_str_index = event.name.find("card")
    card_color = event.name[card_str_index+7:]
    return card_color


def extract_card_number(event: BPEvent) -> str:
    print(f"extract_card_color event: {event}")
    card_str_index = event.name.find("card")
    card_number = event.name[card_str_index + 5:card_str_index+6]
    return card_number


def  extract_card_color_and_number(event: BPEvent) -> tuple[str,str]:
    card_str_index = event.name.find("card")
    if card_str_index != -1:
        card_color = event.name[card_str_index+7:]
        card_number = event.name[card_str_index + 5:card_str_index + 6]
        return card_color,  card_number
    else:
        return None, None


def is_color_card_event(event: BPEvent) -> bool:
    for color in ["blue", "red","green"]:
        if color in event.name:
            return True
    return False


def is_color_or_number_card_event(event: BPEvent) -> bool:
    pattern = r"p_\d+_card_\d+_\w+"
    if re.match(pattern, event.name) is not None:
        return True
    return False


@bp.thread
def enforce_turns():  # blocks moves that are not in turn
    yield bp.sync(waitFor=BPEvent("start_game",priority=10.0))
    while True:
        last_event_p_0 = yield bp.sync(waitFor=all_player_0_except_no_more_cards, block=all_player_1_except_no_more_cards)
        if is_event_draw_card_event(0, last_event_p_0):
            yield bp.sync(waitFor=all_player_0_except_no_more_cards, block=all_player_1_except_no_more_cards)

        last_event_p_1 = yield bp.sync(waitFor=all_player_1_except_no_more_cards, block=all_player_0_except_no_more_cards)
        if is_event_draw_card_event(1, last_event_p_1):
            yield bp.sync(waitFor=all_player_1_except_no_more_cards, block=all_player_0_except_no_more_cards)


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
def enforce_same_color_or_number():
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    card_color, card_number = extract_card_color_and_number(event=last_event)
    different_colors_or_numbers_event_set = create_cards_from_different_number_or_color_event_set(card_color, card_number)
    last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_or_numbers_event_set)

    while True:
        if is_color_or_number_card_event(last_event):
            card_color, card_number = extract_card_color_and_number(event=last_event)
            different_colors_or_numbers_event_set = create_cards_from_different_number_or_color_event_set(card_color,
                                                                                                          card_number)
        last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_or_numbers_event_set)


@bp.thread
def identify_deadlock():
    last_event = yield bp.sync(request = BPEvent("deadlock"), waitFor=BPEvent("end_game", priority=10.0))
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
def enforce_last_card_announcement():
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    hand_sizes = {0: NUM_OF_CARDS, 1: NUM_OF_CARDS}
    pending_announcement = {0: False, 1: False}

    while True:
        event = yield bp.sync(waitFor=general_player_event_set)

        if event.name.startswith("p_0_card"):
            hand_sizes[0] -= 1
            print(f"[HAND_SIZE] Player 0 played a card. New hand size: {hand_sizes[0]}")

            if hand_sizes[0] == 1:
                pending_announcement[0] = True
                print(f"[LAST_CARD] Player 0 has 1 card and must announce 'last card!'")

        elif event.name.startswith("p_1_card"):
            hand_sizes[1] -= 1
            print(f"[HAND_SIZE] Player 1 played a card. New hand size: {hand_sizes[1]}")

            if hand_sizes[1] == 1:
                pending_announcement[1] = True
                print(f"[LAST_CARD] Player 1 has 1 card and must announce 'last card!'")

        elif event.name == "p_0_draw_card":
            # Wait for the actual card to be dealt
            deal_event = yield bp.sync(waitFor=DealCardsPlayerEventSet(0))
            hand_sizes[0] += 1
            print(f"[HAND_SIZE] Player 0 drew a card ({deal_event.name}). New hand size: {hand_sizes[0]}")

            if hand_sizes[0] != 1 and pending_announcement[0]:
                pending_announcement[0] = False
                print(f"[LAST_CARD] Player 0 no longer has 1 card - announcement no longer needed")

        elif event.name == "p_1_draw_card":
            # Wait for the actual card to be dealt
            deal_event = yield bp.sync(waitFor=DealCardsPlayerEventSet(1))
            hand_sizes[1] += 1
            print(f"[HAND_SIZE] Player 1 drew a card ({deal_event.name}). New hand size: {hand_sizes[1]}")

            if hand_sizes[1] != 1 and pending_announcement[1]:
                pending_announcement[1] = False
                print(f"[LAST_CARD] Player 1 no longer has 1 card - announcement no longer needed")

        # Skip other events (like announcements, game events, etc.)
        elif event.name == "end_game":
            break


def init_b_program():
    b_program = bp.BProgram(bthreads=[  game_manager(),
                                        deal_cards(2,NUM_OF_CARDS),
                                        player_behavior(0, NUM_OF_CARDS),
                                        player_behavior(1, NUM_OF_CARDS) ,
                                        enforce_turns(),
                                        enforce_same_color_or_number(),
                                        enforce_last_card_announcement(),
                                        identify_deadlock(),
                                        detect_illegal_post_game_moves(),
                                        verify_turn_alternation()],
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



