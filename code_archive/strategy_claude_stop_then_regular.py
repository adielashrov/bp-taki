@bp.thread
def strategy_stop_then_regular(index, num_of_cards=2):
    """
    B-thread implementing the STOP-then-regular-card strategy.

    Strategy: If you have a STOP card and a regular card of the same color,
    and both match the leading card, play the STOP card first to skip the
    opponent's turn, then play the regular card to earn an extra turn.

    This b-thread adjusts priorities to encourage this tactical sequence.

    This strategy was designed by Adiel and written by Claude .

    Parameters
    ----------
    index : int
        The player index (0 or 1)
    num_of_cards : int
        Number of cards to deal initially
    """
    # Wait for this player's cards to be dealt
    yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))

    card_events = []
    deal_player_cards_event_set = DealCardsEventSet()

    # Receive initial hand
    for i in range(num_of_cards):
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
        card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

    # Wait for game to start
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    # Setup event references
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    no_more_cards_event = BPEvent(f"p_{index}_no_more_cards", priority=8.0)
    next_turn = BPEvent("next_turn", priority=10.0)

    # Track state across turns
    stop_card_color_played = None  # Track if we just played a STOP card
    turn_number = 0

    while True:
        turn_number += 1

        # Analyze current hand for STOP + regular card combos
        stop_cards = {}  # color -> list of stop card events
        regular_cards = {}  # color -> list of regular card events

        for card in card_events:
            if is_stop_card_event(card):
                color, _ = extract_card_color_and_type(card)
                if color:
                    if color not in stop_cards:
                        stop_cards[color] = []
                    stop_cards[color].append(card)
            elif is_regular_card_event(card):
                color, _ = extract_card_color_and_type(card)
                if color:
                    if color not in regular_cards:
                        regular_cards[color] = []
                    regular_cards[color].append(card)

        # Find colors where we have both STOP and regular cards
        combo_colors = set(stop_cards.keys()) & set(regular_cards.keys())

        if combo_colors:
            logger.debug(
                f"[STRATEGY_STOP_COMBO] P{index} Turn #{turn_number} | Found STOP+regular combos in colors: {combo_colors}")

            # If we just played a STOP card and have a matching regular card, boost it
            if stop_card_color_played and stop_card_color_played in regular_cards:
                logger.debug(
                    f"[STRATEGY_STOP_COMBO] P{index} | Boosting regular {stop_card_color_played} cards (follow-up after STOP)")
                # Boost priority of regular cards of this color to play them next
                for reg_card in regular_cards[stop_card_color_played]:
                    if reg_card in card_events:
                        card_events.remove(reg_card)
                        boosted_card = BPEvent(reg_card.name, priority=4.0)  # Higher priority than normal
                        card_events.append(boosted_card)
                        logger.debug(f"[STRATEGY_STOP_COMBO] P{index} | Boosted {reg_card.name} to priority 4.0")

                stop_card_color_played = None  # Reset after boosting follow-up
            else:
                # Not following up a STOP - check if we should prioritize STOP cards
                for color in combo_colors:
                    logger.debug(f"[STRATEGY_STOP_COMBO] P{index} | Has both STOP and regular cards in {color}")
                    # Boost STOP card priority to encourage playing it first
                    for stop_card in stop_cards[color]:
                        if stop_card in card_events:
                            card_events.remove(stop_card)
                            boosted_stop = BPEvent(stop_card.name,
                                                   priority=6.0)  # Between TAKI (5.0) and regular (10.0)
                            card_events.append(boosted_stop)
                            logger.debug(
                                f"[STRATEGY_STOP_COMBO] P{index} | Boosted STOP card {stop_card.name} to priority 6.0")

        # Request a card to play (or wait-for draw_card)
        card_event = yield bp.sync(request=card_events, waitFor=[draw_card_event])

        # Track if we played a STOP card for combo follow-up
        if is_stop_card_event(card_event):
            color, _ = extract_card_color_and_type(card_event)
            if color and color in regular_cards:
                stop_card_color_played = color
                logger.debug(
                    f"[STRATEGY_STOP_COMBO] P{index} → STOP {color} played! Will boost regular {color} cards on next turn")
            else:
                stop_card_color_played = None

            card_events.remove(card_event)
            yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))

        elif is_regular_card_event(card_event):
            color, _ = extract_card_color_and_type(card_event)
            if color == stop_card_color_played:
                logger.debug(
                    f"[STRATEGY_STOP_COMBO] P{index} → ✅ COMBO COMPLETE! Played regular {color} card after STOP")
            card_events.remove(card_event)
            stop_card_color_played = None  # Reset combo tracking

        elif is_action_card_event(card_event):
            # Handle other action cards
            if is_any_taki_event(card_event):
                card_events.remove(card_event)
                closed_taki_event = BPEvent(f"p_{index}_closed_taki", priority=15.0)
                card_events.append(closed_taki_event)

                while True:
                    card_event = yield bp.sync(waitFor=card_events)
                    card_events.remove(card_event)
                    if card_event.name == f"p_{index}_closed_taki":
                        break

                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
            else:
                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
                card_events.remove(card_event)

            stop_card_color_played = None  # Reset combo tracking

        elif is_draw_card_event(card_event):
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            card_events.append(BPEvent(card_name, priority=deal_card_event.priority))
            stop_card_color_played = None  # Reset combo tracking

        # Wait for turn to complete
        last_event = yield bp.sync(waitFor=[no_more_cards_event, next_turn])

        if "no_more_cards" in last_event.name:
            logger.debug(f"[STRATEGY_STOP_COMBO] Player {index}: 🏆 Game over")
            break

    logger.debug(f"[STRATEGY_STOP_COMBO] Player {index}: B-thread terminated after {turn_number} turns")
