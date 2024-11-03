from bppy import *
import random

random.seed(10)


class PlayerEventSet(EventSet):
    def __init__(self, player_index):
        super().__init__(lambda event: event.get_name().startswith(f"player_{player_index}"))
        self.player_index = player_index  # Added this line

    def __contains__(self, item):
        if isinstance(item, BEvent):
            return item.get_name().startswith(f"player_{self.player_index}")
        raise TypeError(f"PlayerEventSet: Expected BEvent, got {type(item)}")


class TopCardEventSet(EventSet):
    def __init__(self):
        super().__init__(lambda event: event.get_name() == "top_card")

    def __contains__(self, item):
        if isinstance(item, BEvent):
            return item.get_name() == "top_card"
        raise TypeError(f"TopCardEventSet: Expected BEvent, got {type(item)}")


class MatchingCardEventSet(EventSet):
    def __init__(self, top_card):
        super().__init__(lambda event: self._is_matching(event, top_card))
        self.top_card = top_card

    def _is_matching(self, event, top_card):
        if not isinstance(event, BEvent):
            return False

        # Only check player card events
        if not event.get_name().startswith("player_"):
            return False

        try:
            # For player events: player_X_card_value_color
            parts = event.get_name().split('_')
            if len(parts) < 5:  # player_X_card_value_color should have 5 parts
                return False

            # Get the top card info from data
            if not top_card.data or 'name' not in top_card.data:
                return False

            top_parts = top_card.data['name'].split('_')
            if len(top_parts) < 3:  # card_value_color should have 3 parts
                return False

            # Compare value and color (parts[3] is value, parts[4] is color)
            return parts[3] == top_parts[1] or parts[4] == top_parts[2]

        except (IndexError, KeyError):
            return False

    def __contains__(self, item):
        return self._is_matching(item, self.top_card)


@b_thread
def deal_cards(num_of_players=2, num_of_cards=2):
    # Create and shuffle deck
    cards = []
    values = ["1", "3", "4", "5"]
    colors = ["blue", "red"]
    for color in colors:
        for value in values:
            cards.append(BEvent(f"card_{value}_{color}"))
    random.shuffle(cards)

    # Deal cards to players
    for i in range(num_of_players):
        for j in range(num_of_cards):
            card = cards.pop()
            # Format: player_X_card_value_color
            player_card_event = BEvent(f"player_{i}_card_{card.get_name().split('_', 1)[1]}")
            yield {request: player_card_event}

    yield {request: BEvent("finished_dealing")}

    # Set top card
    top_card = cards.pop()
    yield {request: BEvent("top_card", {"name": top_card.get_name()})}


@b_thread
def player_behavior(index, num_cards):
    player_events = PlayerEventSet(index)
    hand = []

    # Draw initial cards
    for _ in range(num_cards):
        card_event = yield {waitFor: player_events}
        hand.append(card_event)

    yield {waitFor: BEvent("finished_dealing")}

    # Wait for top card
    top_card_set = TopCardEventSet()
    top_card = yield {waitFor: top_card_set}

    rounds = 0
    while rounds < 3 and hand:  # Limiting to 3 rounds as in original
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
    # Wait for initial top card
    top_card_set = TopCardEventSet()
    current_top = yield {waitFor: top_card_set}

    while True:
        # Create event set for matching cards
        matching_cards = MatchingCardEventSet(current_top)
        # Allow matching cards and block others
        current_top = yield {waitFor: All(), block: AllExcept(matching_cards)}


if __name__ == "__main__":
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
    b_program.run()