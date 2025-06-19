import bppy as bp
from bppy.analysis.symbolic_bprogram_verifier import SymbolicBProgramVerifier
from bppy.model.event_selection.statement_priority_event_selection_strategy import StatementPriorityBasedEventSelectionStrategy
import random
from typing import *

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

random.seed(10)

leading_card_event_set = bp.EventSet(lambda e: e.name.startswith('leading_'))

general_player_event_set = bp.EventSet(lambda e: e.name.startswith('p_'))

any_player_0 = bp.EventSet(lambda e: e.name.startswith('p_0'))
any_player_1 = bp.EventSet(lambda e: e.name.startswith('p_1'))

any_player_no_more_cards = bp.EventSet(lambda e: 'no_more_cards' in e.name)

def create_cards_from_same_color_event_set(color):
    def cards_from_the_same_color(event):
        if color in event.name:
            return True
        return False
    return bp.EventSet(cards_from_the_same_color)


def create_cards_from_different_color_event_set(color):
    def cards_from_the_different_color(event):
        colors = ["blue", "red"]
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


class PlayerEventSet(bp.EventSet):
    def __init__(self, index):
        self.index = index
        super().__init__(lambda event: event.name.startswith(f"p_{self.index}"))
    def __contains__(self, item):
        if isinstance(item, bp.BEvent):
            return item.name.startswith(f"p_{self.index}")
        else:
            raise TypeError(f"PlayerOneEventSet: Expected item of type BEvent, got {type(item)}")


def create_and_shuffle_cards():
    all_cards = []
    colors = ["blue", "red"]
    values = ["1", "3", "4", "5","6","7","8","9"]
    for color in colors:
        for value in values:
            card_event_name= "card_" + value + "_" + color
            all_cards.append(bp.BEvent(card_event_name))

    random.shuffle(all_cards)
    return all_cards


@bp.thread
def game_manager():
    yield bp.sync(request=bp.BEvent("start_dealing_cards_to_players"))
    yield bp.sync(waitFor=bp.BEvent("finished_dealing_cards_to_players"))
    yield bp.sync(request=bp.BEvent("deal_leading_card"))
    yield bp.sync(waitFor=bp.BEvent("finished_leading_card"))
    yield bp.sync(request=bp.BEvent("start_game"))
    last_event = yield bp.sync(waitFor=any_player_no_more_cards)
    yield bp.sync(request=bp.BEvent("end_game"))



@bp.thread
def end_of_game():  # blocks moves after the game is over
    yield bp.sync(waitFor=bp.BEvent("end_game"))
    yield bp.sync(block=bp.All())


@bp.thread
def deal_cards(num_of_players=2, num_of_cards=2):
    yield bp.sync(waitFor=bp.BEvent("start_dealing_cards_to_players"))
    cards = create_and_shuffle_cards()
    for i in range(num_of_players):
        for j in range(num_of_cards):
            card_event = cards.pop()
            player_card_event = bp.BEvent("p_" + str(i) + "_" + card_event.name)
            yield bp.sync(request= player_card_event)
    yield bp.sync(request=bp.BEvent("finished_dealing_cards_to_players"))

    # Deal the leading card
    yield bp.sync(waitFor=bp.BEvent("deal_leading_card"))
    top_card = cards.pop()
    yield bp.sync(request=bp.BEvent(f"leading_{top_card.name}"))
    yield bp.sync(request=bp.BEvent("finished_leading_card"))


@bp.thread
def player_behavior(index, num_of_cards=2):
    yield bp.sync(waitFor=bp.BEvent("start_dealing_cards_to_players"))
    cards_events = []
    player_cards_event_set = PlayerEventSet(index)
    for i in range(num_of_cards):
        card_event = yield bp.sync(waitFor=player_cards_event_set)
        cards_events.append(card_event)

    yield bp.sync(waitFor=bp.BEvent("start_game"))

    while cards_events:
        event = yield bp.sync(waitFor=general_player_event_set, request=cards_events)
        if event.name.startswith(f"p_{index}"):
            cards_events.remove(event)

    yield bp.sync(request=bp.BEvent(f"p_{index}_no_more_cards "))

def extract_card_color(event: bp.BEvent) -> str:
    card_color_index = event.name.find("card")
    card_color = event.name[card_color_index+7:]
    return card_color

def is_color_card_event(event: bp.BEvent) -> bool:
    for color in ["blue", "red"]:
        if color in event.name:
            return True
    return False

@bp.thread
def enforce_turns():  # blocks moves that are not in turn
    yield bp.sync(waitFor=bp.BEvent("start_game"))
    while True:
        yield bp.sync(waitFor=any_player_0, block=any_player_1)
        yield bp.sync(waitFor=any_player_1, block=any_player_0)


@bp.thread
def enforce_same_color():
    yield bp.sync(waitFor=bp.BEvent("deal_leading_card"))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=bp.BEvent("finished_leading_card"))
    yield bp.sync(waitFor=bp.BEvent("start_game"))
    card_color = extract_card_color(event=last_event)
    different_colors_event_set = create_cards_from_different_color_event_set(card_color)
    last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_event_set)

    while True:
        if is_color_card_event(last_event):
            card_color = extract_card_color(event=last_event)
            different_colors_event_set = create_cards_from_different_color_event_set(card_color)
        last_event = yield bp.sync(waitFor=general_player_event_set, block=different_colors_event_set)


def init_b_program():
    b_program = bp.BProgram(bthreads=[  game_manager(),
                                        deal_cards(2,4),
                                        player_behavior(0,4),
                                        player_behavior(1,4) ,
                                        enforce_turns(),
                                        enforce_same_color()],
                                        #end_of_game()],
                         event_selection_strategy=StatementPriorityBasedEventSelectionStrategy(),
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



