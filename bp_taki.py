import bppy as bp
from bppy.analysis.symbolic_bprogram_verifier import SymbolicBProgramVerifier
from bppy.model.event_selection.statement_priority_event_selection_strategy import StatementPriorityBasedEventSelectionStrategy
from bppy.model.b_priority_event import BPEvent
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy
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

pattern = r"p_\d+_card_\d+_\w+"
general_player_event_set = bp.EventSet(lambda e:
    hasattr(e, 'name') and re.match(pattern, e.name) is not None
)

any_player_0 = bp.EventSet(lambda e: 'p_0' in e.name)
any_player_1 = bp.EventSet(lambda e: 'p_1' in e.name)

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


@bp.thread
def game_manager():
    yield bp.sync(request=BPEvent("start_dealing_cards_to_players", priority=10.0))
    yield bp.sync(waitFor=BPEvent("finished_dealing_cards_to_players", priority=10.0))
    yield bp.sync(request=BPEvent("deal_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(request=BPEvent("start_game", priority=10.0))
    last_event = yield bp.sync(waitFor=any_player_no_more_cards)
    yield bp.sync(request=BPEvent("end_game", priority=10.0))



@bp.thread
def end_of_game():  # blocks moves after the game is over
    yield bp.sync(waitFor=BPEvent("end_game", priority=10.0))
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
        card_event = cards.pop()
        deal_player_card_event = BPEvent("deal_p_" + str(player_index) + "_" + card_event.name, priority=9.0)
        other_player_cards_event_set = PlayerEventSet(1-player_index)
        yield bp.sync(request=deal_player_card_event)

def remove_deal_prefix_from_event(event):
    card_name = event.name.removeprefix("deal_")
    return card_name

@bp.thread
def player_behavior(index, num_of_cards=2):
    yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))
    cards_events = []
    deal_player_cards_event_set = DealCardsPlayerEventSet(index)
    for i in range(num_of_cards):
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_from_event(deal_card_event)
        cards_events.append(BPEvent(card_name, priority=10.0))

    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    # Add draw_card_event to the cards events(Possible actions of player)
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    cards_events.append(draw_card_event)

    while cards_events:
        event = yield bp.sync(waitFor=general_player_event_set, request=cards_events)
        if event.name.startswith(f"p_{index}_card"):
            cards_events.remove(event)
        # If there is a draw card event, wait for a card to be dealt.
        if event.name.startswith(f"p_{index}_draw_card"):
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            print(f"player_{index} received card event: ", deal_card_event)
            card_name = remove_deal_prefix_from_event(deal_card_event)
            cards_events.append(BPEvent(card_name, priority=10.0))

    yield bp.sync(request=BPEvent(f"p_{index}_no_more_cards ", priority=10.0))

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
    for color in ["blue", "red","green"]:
        if color in event.name:
            return True
    for number in   ["1", "3", "4", "5", "6", "7", "8", "9"]:
        if number in event.name:
            return True
    return False


@bp.thread
def enforce_turns():  # blocks moves that are not in turn
    yield bp.sync(waitFor=BPEvent("start_game",priority=10.0))
    while True:
        last_event_p_0 = yield bp.sync(waitFor=any_player_0, block=any_player_1)
        if is_event_draw_card_event(0, last_event_p_0):
            yield bp.sync(waitFor=any_player_0, block=any_player_1)

        last_event_p_1 = yield bp.sync(waitFor=any_player_1, block=any_player_0)
        if is_event_draw_card_event(1, last_event_p_1):
            yield bp.sync(waitFor=any_player_1, block=any_player_0)


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


def init_b_program():
    b_program = bp.BProgram(bthreads=[  game_manager(),
                                        deal_cards(2,NUM_OF_CARDS),
                                        player_behavior(0, NUM_OF_CARDS),
                                        player_behavior(1, NUM_OF_CARDS) ,
                                        enforce_turns(),
                                        enforce_same_color_or_number()],
                         event_selection_strategy=EventPrioritySelectionStrategy(),
                         listener=bp.PrintBProgramRunnerListener())
    return b_program


def regular_execution_of_bp_program():
    b_program = init_b_program()
    b_program.run()


def verify_taki_bp_program():
    # Initialize verifier and check that the program does not end using the BPROGRAM_DONE flag.
    # The verifier will use BDDs to check the property.
    verifier = SymbolicBProgramVerifier(init_b_program, all_events)
    result, explanation_str = verifier.verify(spec="G (!(event = BPROGRAM_DONE))", type="BMC", bound=10, find_counterexample=True,
                                              print_info=True)

    if result:
        print("OK")
    else:
        print("Violation Found")
        print("Counterexample:")
        print(explanation_str)

if __name__ == "__main__":
    regular_execution_of_bp_program()
    # verify_taki_bp_program()



