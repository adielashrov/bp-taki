import bppy as bp
import random
from typing import *

random.seed(10)

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

    yield bp.sync(waitFor=bp.BEvent("finished_dealing_cards"))
    yield bp.sync(request=bp.BEvent(f"player_{index} is ready to play"))

    yield bp.sync(request=cards_events)

def init_b_program():
    b_program = bp.BProgram(bthreads=[ deal_cards(2,2),
                                                                player_behavior(0,2),
                                                                player_behavior(1, 2)],
                         event_selection_strategy=bp.SimpleEventSelectionStrategy(),
                         listener=bp.PrintBProgramRunnerListener())
    return b_program

if __name__ == "__main__":
    # test git commit
    b_program = init_b_program()
    b_program.run()



