from bppy import *
from bppy.analysis.symbolic_bprogram_verifier import SymbolicBProgramVerifier
import random

#ChatGPT implmentation

random.seed(10)

# All possible events in the game
# Card events (card_value_color)
CARD_EVENTS = [BEvent(f"card_{value}_{color}")
               for value in ["1", "3", "4", "5"]
               for color in ["blue", "red"]]

# Player card events (player_X_card_value_color)
PLAYER_CARD_EVENTS = [BEvent(f"player_{i}_card_{value}_{color}")
                     for i in range(2)  # 2 players
                     for value in ["1", "3", "4", "5"]
                     for color in ["blue", "red"]]

# Control events
CONTROL_EVENTS = [
    BEvent("finished_dealing"),
    BEvent("top_card")
]

# Combine all events
all_events = CARD_EVENTS + PLAYER_CARD_EVENTS + CONTROL_EVENTS


class PlayerEventSet(EventSet):
    def __init__(self, player_index):
        super().__init__(lambda event: event.name.startswith(f"player_{player_index}"))
        self.player_index = player_index

    def __contains__(self, item):
        if isinstance(item, BEvent):
            return item.name.startswith(f"player_{self.player_index}")
        raise TypeError(f"PlayerEventSet: Expected BEvent, got {type(item)}")


class TopCardEventSet(EventSet):
    def __init__(self):
        super().__init__(lambda event: event.name == "top_card")

    def __contains__(self, item):
        if isinstance(item, BEvent):
            return item.name == "top_card"
        raise TypeError(f"TopCardEventSet: Expected BEvent, got {type(item)}")


class MatchingCardEventSet(EventSet):
    def __init__(self, top_card):
        super().__init__(lambda event: self._is_matching(event, top_card))
        self.top_card = top_card

    def _is_matching(self, event, top_card):
        if not isinstance(event, BEvent):
            return False

        if not event.name.startswith("player_"):
            return False

        try:
            # For player events: player_X_card_value_color
            parts = event.name.split('_')
            if len(parts) < 5:
                return False

            if not top_card.data or 'name' not in top_card.data:
                return False

            top_parts = top_card.data['name'].split('_')
            if len(top_parts) < 3:
                return False

            return parts[3] == top_parts[1] or parts[4] == top_parts[2]

        except (IndexError, KeyError):
            return False

    def __contains__(self, item):
        return self._is_matching(item, self.top_card)


@b_thread
def deal_cards(num_of_players=2, num_of_cards=2):
    cards = []
    values = ["1", "3", "4", "5"]
    colors = ["blue", "red"]
    for color in colors:
        for value in values:
            cards.append(BEvent(f"card_{value}_{color}"))
    random.shuffle(cards)

    for i in range(num_of_players):
        for j in range(num_of_cards):
            card = cards.pop()
            player_card_event = BEvent(f"player_{i}_card_{card.name.split('_', 1)[1]}")
            yield {request: player_card_event}

    yield {request: BEvent("finished_dealing")}

    top_card = cards.pop()
    yield {request: BEvent("top_card", {"name": top_card.name})}


@b_thread
def player_behavior(index, num_cards):
    player_events = PlayerEventSet(index)
    hand = []

    for _ in range(num_cards):
        card_event = yield {waitFor: player_events}
        hand.append(card_event)

    yield {waitFor: BEvent("finished_dealing")}

    top_card_set = TopCardEventSet()
    top_card = yield {waitFor: top_card_set}

    rounds = 0
    while rounds < 3 and hand:
        if len(hand) == 1:
            yield {request: hand[0]}
        else:
            yield {request: hand}

        rounds += 1


@b_thread
def enforce_turns():
    yield {waitFor: BEvent("finished_dealing")}

    while True:
        yield {waitFor: PlayerEventSet(0), block: PlayerEventSet(1)}
        yield {waitFor: PlayerEventSet(1), block: PlayerEventSet(0)}


@b_thread
def enforce_matching():
    top_card_set = TopCardEventSet()
    current_top = yield {waitFor: top_card_set}

    while True:
        matching_cards = MatchingCardEventSet(current_top)
        current_top = yield {waitFor: All(), block: AllExcept(matching_cards)}


def init_bprogram():
    b_program = BProgram(
        bthreads=[
            deal_cards(2, 2),
            player_behavior(0, 2),
            player_behavior(1, 2),
            enforce_turns(),
            enforce_matching()
        ],
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener()
    )
    return b_program

if __name__ == "__main__":

    ver_prgoram = False
    if not ver_prgoram:
        bprogram = init_bprogram()
        bprogram.run()
    else:
        # Initialize verifier and check that the program does not end using the BPROGRAM_DONE flag.
        # The verifier will use BDDs to check the property.
        verifier = SymbolicBProgramVerifier(init_bprogram, all_events)
        result, explanation_str = verifier.verify(spec="G( !(event = BPROGRAM_DONE))",
                                                  type="BMC",
                                                  bound=20,
                                                  find_counterexample=True,
                                                  print_info=True)

        if result:
            print("OK")
        else:
            print("Violation Found")
            print("Counterexample:")
            print(explanation_str)