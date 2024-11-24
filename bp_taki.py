import bppy as bp
import random

random.seed(10)

def create_and_shuffle_cards():
    all_cards = []
    colors = ["blue", "red"]
    values = ["1", "3", "4", "5"]
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

def init_b_program():
    b_program = bp.BProgram(bthreads=[deal_cards()],
                         event_selection_strategy=bp.SimpleEventSelectionStrategy(),
                         listener=bp.PrintBProgramRunnerListener())
    return b_program

if __name__ == "__main__":
    b_program = init_b_program()
    b_program.run()



