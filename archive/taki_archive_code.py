'''
@b_thread
def request_number_card():
    card_events = create_number_events()
    card = yield {waitFor: card_events}
    type = card.data["type"]
    value = card.data["value"]
    print(f"card placed type: {type}, value:{value}")
'''

'''
@b_thread
def player_1():
    events = BEvent("TopCard")
    hand = []
    while True:
        # event set instead of single event
        topCard = yield {waitFor: EventSet("all_cards")}
        # basic solution that encapsulates the logic of the game
        cards = create_valid_card_events(topCard, hand)
        lastEvent = yield {request: cards + [BEvent("draw", {"count": 1})]}

        if lastEvent.name == "draw":
            hand.append(lastEvent.data["cards"])
'''

'''
@b_thread
def handle_plus_3():
    count = 0
    while True:
        yield {
            waitFor: BEvent("place_card", {"type": "Action", "value": "+3"})}
        count += 3
        yield {l_request: (BEvent("draw_card"),
                           lambda event: BEvent("draw_card",
                                                {"count": 3})),
               waitFor: EventSet("TopCard")}
'''
