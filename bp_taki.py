import bppy as bp
import random
from typing import *

random.seed(10)

leading_card_event_set = bp.EventSet(lambda e: e.name.startswith('leading_'))

general_player_event_set = bp.EventSet(lambda e: e.name.startswith('p_'))

def create_cards_from_same_color_event_set(color):
    def cards_from_the_same_color(event):
        if color in event.name:
            return True
        return False
    return bp.EventSet(cards_from_the_same_color)

def create_cards_from_different_color_event_set(color):
    def cards_from_the_different_color(event):
        if color in event.name:
            return False
        return True
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
def deal_cards(num_of_players=2, num_of_cards=2):
    cards = create_and_shuffle_cards()
    for i in range(num_of_players):
        for j in range(num_of_cards):
            card_event = cards.pop()
            player_card_event = bp.BEvent("p_" + str(i) + "_" + card_event.name)
            yield bp.sync(request= player_card_event)

    yield bp.sync(request= bp.BEvent("finished_dealing_cards"))

    top_card = cards.pop()
    yield bp.sync(request=bp.BEvent(f"leading_{top_card.name}"))

@bp.thread
def player_behavior(index, num_of_cards=2):
    cards_events = []
    player_cards_event_set = PlayerEventSet(index)
    for i in range(num_of_cards):
        card_event = yield bp.sync(waitFor=player_cards_event_set)
        cards_events.append(card_event)

    yield bp.sync(waitFor=leading_card_event_set)

    while cards_events:
        event = yield bp.sync(waitFor=general_player_event_set, request=cards_events)
        print(f"player{index} recived event:{event}")
        if event.name.startswith(f"p_{index}"):
            cards_events.remove(event)

@bp.thread
def enforce_same_color():
    while True:
        event = yield bp.sync(waitFor=leading_card_event_set)
        card_color_index = event.name.find("card")
        card_color = event.name[card_color_index+7:]
        same_color_event_set = create_cards_from_same_color_event_set(card_color)
        different_colors_event_set = create_cards_from_different_color_event_set(card_color)
        yield bp.sync(waitFor=same_color_event_set,block=different_colors_event_set)

def init_b_program():
    b_program = bp.BProgram(bthreads=[  deal_cards(2,2),
                                        player_behavior(0,2),
                                        player_behavior(1,2)],
                                        #enforce_same_color() ],
                         event_selection_strategy=bp.SimpleEventSelectionStrategy(),
                         listener=bp.PrintBProgramRunnerListener())
    return b_program

if __name__ == "__main__":
    b_program = init_b_program()
    b_program.run()



