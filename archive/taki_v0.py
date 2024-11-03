from bppy import *
from card import Card
import random

random.seed(10)

class PlayerZeroEventSet(EventSet):
    def __init__(self):
        super().__init__(lambda event: event.get_name().startswith("player_0"))
    def __contains__(self, item):
        # print("Called PlayerOneEventSet __contains__ with", item)
        # Check if item is of type BEvent, if not, handle or raise a specific error.
        if isinstance(item, BEvent):
            return item.get_name().startswith("player_0")
        else:
            raise TypeError(f"PlayerOneEventSet: Expected item of type BEvent, got {type(item)}")

class PlayerOneEventSet(EventSet):
    def __init__(self):
        super().__init__(lambda event: event.get_name().startswith("player_1"))
    def __contains__(self, item):
        # print("Called PlayerTwoEventSet __contains__ with", item)
        # Check if item is of type BEvent, if not, handle or raise a specific error.
        if isinstance(item, BEvent):
            return item.get_name().startswith("player_1")
        else:
            raise TypeError(f"PlayerTwoEventSet: Expected item of type BEvent, got {type(item)}")

class cards_event_set(EventSet):
    def __init__(self):
        super().__init__(lambda event: event.get_name().contains("card"))
    def __contains__(self, item):
        # print("Called cards_event_set __contains__ with", item)
        # Check if item is of type BEvent, if not, handle or raise a specific error.
        if isinstance(item, BEvent):
            return item.get_name().contains("card")
        else:
            raise TypeError(f"cards_event_set: Expected item of type BEvent, got {type(item)}")

class top_card_event_set(EventSet):
    def __init__(self):
        super().__init__(lambda event: event.get_name().startswith("top_card"))
    def __contains__(self, item):
        # print("Called top_card_event_set __contains__ with", item)
        # Check if item is of type BEvent, if not, handle or raise a specific error.
        if isinstance(item, BEvent):
            return item.get_name().startswith("top_card")
        else:
            raise TypeError(f"top_card_event_set: Expected item of type BEvent, got {type(item)}")

def create_and_shuffle_cards():
    all_cards = []
    # values = ["1", "3", "4", "5", "6", "7", "8", "9"]
    values = ["1", "3", "4", "5"]
    colors = ["blue", "red"]
    for color in colors:
        for value in values:
            card_event_name= "card_" + value + "_" + color
            all_cards.append(BEvent(card_event_name))

    # Shuffle the cards
    random.shuffle(all_cards)
    return all_cards


def select_cards(cards, num_of_cards):
    selected_cards = []
    for i in range(num_of_cards):
        selected_cards.append(cards.pop())
    return selected_cards


def create_card_events(player, cards):
    card_events = []
    for card in cards:
        card_events.append(BEvent(player,
                                  {"type": "simple", "number": card.number,
                                   "color": card.color}))
    return card_events


def exist_matching_card(card_event):
    print(card_event)
    pass


def create_valid_card_events(top_card, cards):
    print(top_card, " ", cards)
    pass

@b_thread
def deal_cards(num_of_players=2, num_of_cards=2):
    cards = create_and_shuffle_cards()
    # Dealing the cards to the players.
    for i in range(num_of_players):
        for j in range(num_of_cards):
            card_event = cards.pop()
            player_card_event = BEvent("player_" + str(i) + "_" + card_event.get_name())
            # print("deal_cards is dealing", player_card_event.get_name())
            yield {request: player_card_event}
            # print("deal_cards is done dealing", player_card_event.get_name())

    yield {request: BEvent("finished_dealing_cards")}

    # Top card
    top_card = cards.pop()
    top_card_event = BEvent("top_card", {"name": top_card.get_name()})
    yield {request: top_card_event,
           block: AllExcept(top_card_event)}



@b_thread
def simulate_player(index=0, num_of_cards=2):
    rounds = 0
    card_events = []
    player_cards_event_set = None
    if index == 0:
        player_cards_event_set = PlayerZeroEventSet()
    else:
        player_cards_event_set = PlayerOneEventSet()
    for i in range(num_of_cards):
        # print("Player ", index, " is waiting for card")
        card_event = yield {waitFor: player_cards_event_set}
        # print("Player ", index, " received card: ", card_event)
        # Remove the player_1 prefix from the card_event
        # card_event = BEvent(card_event.get_name().removeprefix("player_" + str(index) + "_"), card_event.data)
        card_events.append(card_event)

    yield {waitFor: BEvent("finished_dealing_cards")}

    while rounds < 3 and card_events:
        # print("Player ", index, " is requesting all of her cards", card_events)
        if len(card_events)==1:
            # print("Player ", index, " is requesting the last card")
            last_event = yield {request: card_events[0]}
        else:
            last_event = yield {request: card_events}
        # print("Player ", index, "last_event: ", last_event)
        if last_event in card_events:
            card_events.remove(last_event)
        rounds += 1

def create_event_set_cards_with_same_color(top_card):
    val = EventSet(lambda event: event.type == "rich" and event.data["color"] == top_card.color)
    return val

@b_thread
def place_legal_card():
    # Add loop
    top_card = yield {waitFor: BEvent("top_card", type="rich")}
    cards_with_top_card_color = create_event_set_cards_with_same_color(top_card)
    # pattern here
    # List 1 - all cards in the same color
    # List 2 - all cards with the same number
    # waitFor - any of List 1 or List 2
    # block - all other cards
    #selected_card = yield {waitFor: cards_with_top_card_color, block: AllExcept(cards_with_top_card_color)}
    yield {waitFor: All(), block: AllExcept(cards_with_top_card_color)}
    # print("Placing card: ", selected_card)

@b_thread
def enforce_turns():
    top_card_event_set_instance = top_card_event_set()
    top_card_event = yield {waitFor: top_card_event_set_instance}
    print("Received top_card_event ", top_card_event)
    while True:
        # print("Forcing turns, waiting for player_0, blocking player_1")
        yield {waitFor: PlayerZeroEventSet(), block: PlayerOneEventSet()}
        # print("Forcing turns, waiting for player_1, blocking player_0")
        yield {waitFor: PlayerOneEventSet(), block: PlayerZeroEventSet()}

'''
@b_thread
def start_game():
    yield {request: BEvent("place_card", {"type": "Number", "value": "1"})}
'''


if __name__ == "__main__":
    b_program = BProgram(bthreads=[deal_cards(2,2),
                                   simulate_player(0,2),
                                   simulate_player(1, 2),
                                   enforce_turns()],
                         event_selection_strategy=SimpleEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()