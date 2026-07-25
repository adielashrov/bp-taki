import re
from bppy.model.b_priority_event import BPEvent


def extract_card_number(event: BPEvent) -> str:
    card_str_index = event.name.find("card")
    card_number = event.name[card_str_index + 5:card_str_index + 6]
    return card_number


def all_player_index_events(index):
    return bp.EventSet(lambda e: f'p_{index}' in e.name)


def add_event_to_card_events_according_to_basic_strategy_taki_2(index, card_name, original_priority, card_events):
    """
    Add a card event to player's hand with priority adjustment for TAKI cards.
    If you have both TAKI and Super TAKI cards, prioritize TAKI higher.
    TAKI will receive a priority of 4.0, Super TAKI 6.0, and
    other cards keep their original priority.
    """
    if "super_taki" in card_name :
        adjusted_priority = 6.0
        # logger.debug(f"[STRATEGY_TAKI_2] Player {index}: Adding SUPER TAKI card '{card_name}' with BOOSTED priority {adjusted_priority} (original: {original_priority})")
        card_events.append(BPEvent(card_name, priority=adjusted_priority))
    elif "taki_" in card_name:
        adjusted_priority = 4.0
        # logger.debug(f"[STRATEGY_TAKI_2] Player {index}: Adding TAKI card '{card_name}' with BOOSTED priority {adjusted_priority} (original: {original_priority})")
        card_events.append(BPEvent(card_name, priority=adjusted_priority))
    else:
        # logger.debug(f"[STRATEGY_TAKI_2] Player {index}: Adding regular card '{card_name}' with standard priority {original_priority}")
        card_events.append(BPEvent(card_name, priority=original_priority))


def add_event_to_card_events_according_to_basic_strategy_taki(index, card_name, original_priority, card_events):
    """
    Add a card event to player's hand with priority adjustment for TAKI cards.

    TAKI cards receive priority 5.0 (lower number = higher priority) to encourage playing them,
    while other cards keep their original priority (typically 10.0).
    """
    if "taki" in card_name:
        adjusted_priority = 5.0
        logger.debug(
            f"[STRATEGY_TAKI] Player {index}: Adding TAKI card '{card_name}' with BOOSTED priority {adjusted_priority} (original: {original_priority})")
        card_events.append(BPEvent(card_name, priority=adjusted_priority))
    else:
        logger.debug(
            f"[STRATEGY_TAKI] Player {index}: Adding regular card '{card_name}' with standard priority {original_priority}")
        card_events.append(BPEvent(card_name, priority=original_priority))

    # Summary log of current hand composition
    taki_count = sum(1 for e in card_events if "taki" in e.name)
    logger.debug(
        f"[STRATEGY_TAKI] Player {index}: Hand now contains {len(card_events)} cards ({taki_count} TAKI cards)")



def create_cards_from_different_number_event_set(number):
    numbers = ["1", "3", "4", "5", "6", "7", "8", "9"]
    numbers.remove(number)

    def cards_from_the_different_number(event):
        current_card_number = extract_card_number(event)
        if number == current_card_number:
            return False
        elif current_card_number in numbers:
            return True
        else:
            return False

    return bp.EventSet(cards_from_the_different_number)


def extract_card_color(event: BPEvent) -> str:
    card_str_index = event.name.find("card")
    card_color = event.name[card_str_index + 7:]
    return card_color


def add_event_to_card_events_according_to_color_dominance(index, card_name, original_priority, card_events, dominant_color):
    """
    Add a card event to player's hand with priority adjustment based on color dominance.
    
    Dominant color cards receive priority 5.0 (higher preference), 
    while off-color cards get priority 12.0 (lower preference).
    
    EXCLUDES change_color cards - they are managed exclusively by player_behavior.
    """
    # Skip change_color cards - let player_behavior handle them exclusively
    if "change_color" in card_name:
        logger.debug(
            f"[STRATEGY_COLOR_DOM] Player {index}: Skipping change_color card - "
            f"player_behavior will manage it"
        )
        return
    
    # Check if card is of the dominant color
    is_dominant = dominant_color in card_name
    
    if is_dominant:
        adjusted_priority = 5.0
        logger.debug(
            f"[STRATEGY_COLOR_DOM] Player {index}: Adding DOMINANT color card '{card_name}' "
            f"with BOOSTED priority {adjusted_priority} (original: {original_priority})"
        )
    else:
        adjusted_priority = 12.0
        logger.debug(
            f"[STRATEGY_COLOR_DOM] Player {index}: Adding off-color card '{card_name}' "
            f"with LOWERED priority {adjusted_priority} (original: {original_priority})"
        )
    
    card_events.append(BPEvent(card_name, priority=adjusted_priority))


def is_closed_taki_event(e):
    """Check if event is a closed_taki event signaling the end of a super taki sequence"""
    return isinstance(e, BPEvent) and re.match(r"^p_\d+_closed_taki$", e.name) is not None


def extract_player_id(event: BPEvent) -> Optional[int]:
    """Extract player ID from event name (e.g., p_0_card -> 0)"""
    player_reg_exp = re.compile(r"^p_(\d+)_")
    m = player_reg_exp.match(event.name)
    if m:
        return int(m.group(1))
    else:
        return None


def remove_deal_prefix_from_event(event):
    card_name = event.name.removeprefix("deal_")
    return card_name


def player_idx_of(event_name: str) -> int:
    m = re.match(r"^p_(\d+)_", event_name)
    return int(m.group(1)) if m else -1


def create_cards_from_different_color_or_type_event_set(card_color, card_type):
    """
    Creates an EventSet that identifies cards matching NEITHER the given color NOR type.

    Enforces Taki's rule: players must match either color or type of the leading card.
    Returns an EventSet that blocks illegal moves (cards that match neither).

    Parameters
    ----------
    card_color : str
        The reference color: "blue", "red", or "green"
    card_type : str
        The reference type: "1", "3", "4", "5", "6", "7", "8", "9", "STOP", "PLUS_2"

    Returns
    -------
    bp.EventSet
        EventSet returning True for cards matching neither color nor type (illegal moves)

    Raises
    ------
    Exception
        If card_color or card_type are invalid

    Examples
    --------
    If the leading card is blue 5:
    blocked_set = create_cards_from_different_color_or_type_event_set("blue", "5")
    # Returns False (don't block): blue 3 (matches color)
    # Returns False (don't block): red 5 (matches type)
    # Returns False (don't block): blue 5 (matches both)
    # Returns True (block): red 3 (matches neither color nor type - illegal play)
    # Returns True (block): green 7 (matches neither color nor type - illegal play)
    """
    colors = COLORS
    types = ["1", "3", "4", "5", "6", "7", "8", "9", "STOP",]
    if card_color in colors and card_type in types:
        colors.remove(card_color)
        types.remove(card_type)
    elif card_type.startswith("CHANGE_COLOR") : # Special case for change_color card
        return bp.EventSet(lambda e: False)  # Don't block anything for change_color
    else:
        raise Exception(f"Wrong parameter to "
                        f"create_cards_from_different_color_or_type_event_set"
                        f"{card_color, card_type}")

    def cards_from_the_different_color_or_type(event):
        """
        Returns True for cards that match neither color nor type (should be blocked).

        Logic:
        - Never block "deal_p_" events (card dealing)
        - Don't block if color OR type matches (legal plays)
        - Block card events that match neither (illegal plays)
        - Don't block non-card events (return False by default)

        The OR condition identifies card events: after removing the reference color/type,
        `colors` and `types` contain all OTHER color/type values, so checking membership
        confirms this is an illegal play.
        """

        # Edge case, we don't want to block events from different
        # colors/number if they are a new card being dealt.
        if event.name.startswith("deal_p_"):
            return False
        t_card_color, t_card_type = extract_card_color_and_type(event)
        if t_card_color == card_color or t_card_type == card_type:
            return False
        elif t_card_color in colors or t_card_type in types: #Should we block "STOP" events?
            return True
        else:  # default return false.
            return False

    return bp.EventSet(cards_from_the_different_color_or_type)


def create_cards_from_different_color_event_set(color):
    def cards_from_the_different_color(event):
        colors = COLORS
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


def create_cards_from_same_color_event_set(color):
    def cards_from_the_same_color(event):
        if color in event.name:
            return True
        return False


def all_player_stop_card_events(player_index):
    def is_event_stop_card_event(event):
        pattern = fr"p_{player_index}_stop_\w+"
        if re.match(pattern, event.name) is not None:
            return True
        return False
    return bp.EventSet(is_event_stop_card_event)


def all_events_not_by_current_player(index: int):
    '''
    Return an EventSet that matches all events except those emitted by the given player.

    Parameters
    ----------
    index : int
        Player index used to identify player-specific event names (for example `p_0`).

    Returns
    -------
    bp.AllExcept
        An EventSet that is the complement of `bp.EventSet(lambda e: f'p_{index}' in e.name)`.
        Events whose `name` contains the substring `p_{index}` will be excluded.
    '''''
    def is_event_of_current_player(event):
        try:
            result = f"p_{index}" in getattr(event, "name", "") or f"deal_p" in getattr(event, "name", "")
            if not result:
                result = True if event.name == "next_turn" or event.name == "stop" else False
        except Exception as e:
            logger.info(f"[DEBUG is_event_of_current_player] index={index} error reading event.name: {event}")
            raise
        return result


    return bp.AllExcept(bp.EventSet(is_event_of_current_player))


def player_stop_card_event_set(index):
    return bp.EventSet(lambda e: e.name.startswith(f"p_{index}_stop"))


def is_color_card_event(event: BPEvent) -> bool:
    for color in COLORS:
        if color in event.name:
            return True
    return False


def all_players_cards_except_special_cards(index):
    def predicate(e: BPEvent):
        if f'p_{index}' in e.name and not 'no_more_cards' in e.name:
            return True
        return False

    return bp.EventSet(predicate)


@bp.thread
def test_regular_card_placement_rules():
    """
    Regression test: Verifies regular numbered cards follow placement rules.

    Scope: ONLY regular numbered cards (card_1 through card_9)
    Rule (outside TAKI): Must match either COLOR or TYPE of the previous leading card.
    Rule (during TAKI): Must match TAKI color only (type does not matter).

    Does NOT validate the legality of special cards themselves (TAKI / SUPER_TAKI / STOP / CHANGE_COLOR),
    but it *does* track them as the new leading context so that regular-card validation is meaningful.

    This test only monitors (waitFor) and never interferes with gameplay.
    """

    logger.info("[TEST_REGULAR_CARDS] Test starting...")

    # ------------------------------------------------------------
    # Initialize from the leading card
    # ------------------------------------------------------------
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    lead_event = yield bp.sync(waitFor=leading_card_event_set)
    last_color, last_type = extract_card_color_and_type(lead_event)

    logger.debug(
        f"[TEST_REGULAR_CARDS] Initialized from leading card: {lead_event.name} -> {last_color}/{last_type}"
    )

    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    logger.info("[TEST_REGULAR_CARDS] Monitoring regular card placement...")

    # ------------------------------------------------------------
    # TAKI-mode tracking
    # ------------------------------------------------------------
    in_taki_mode = False
    taki_color = None
    
    # If cards are played during TAKI, the *last* one becomes the new leading card after closed_taki
    taki_last_color = None
    taki_last_type = None

    # ------------------------------------------------------------
    # Main event monitoring loop
    # ------------------------------------------------------------
    while True:
        event = yield bp.sync(waitFor=general_player_event_set)

        # ------------------------------------------------------------
        # Game ended - test passed
        # ------------------------------------------------------------
        if event.name == "end_game":
            logger.info("[TEST_REGULAR_CARDS] ✓ Test PASSED - all regular cards followed placement rules")
            break

        # ------------------------------------------------------------
        # Exit TAKI mode when we see closed_taki
        # ------------------------------------------------------------
        if "closed_taki" in event.name:
            if in_taki_mode:
                logger.debug("[TEST_REGULAR_CARDS] Exiting TAKI mode")

                # If any cards were played during TAKI, they become the new leading card
                if taki_last_color is not None and taki_last_type is not None:
                    last_color, last_type = taki_last_color, taki_last_type
                    logger.debug(
                        f"[TEST_REGULAR_CARDS] Post-TAKI leading card set to last TAKI-seq card: "
                        f"{last_color}/{last_type}"
                    )
                # else: keep last_color/last_type as the TAKI card itself

                in_taki_mode = False
                taki_color = None
                taki_last_color = None
                taki_last_type = None

            continue  # Ignore the closed_taki event itself
        
        # ------------------------------------------------------------
        # Ignore protocol/system events
        # ------------------------------------------------------------
        if (
            event.name.startswith("deal_")
            or "draw_card" in event.name
            or "no_more_cards" in event.name
            or event.name == "next_turn"
            or event.name == "done_post_action"
        ):
            continue

        # ------------------------------------------------------------
        # Enter TAKI mode (Regular TAKI or Super TAKI)
        # ------------------------------------------------------------
        if is_any_taki_event(event):
            in_taki_mode = True
            
            if is_taki_card_event(event):
                # Regular TAKI has its own color
                card_color, card_type = extract_card_color_and_type(event)
                taki_color = card_color
                if taki_color is None:
                    assert False, f"Regular TAKI played but no color parsed (event={event.name})"
                last_color, last_type = taki_color, "TAKI"
                logger.debug(f"[TEST_REGULAR_CARDS] Entering TAKI mode: color={taki_color}")
            else:
                # Super TAKI inherits previous color
                if last_color is None:
                    logger.error("=" * 60)
                    logger.error("[TEST_REGULAR_CARDS] X TEST FAILED - Super TAKI but no color to inherit!")
                    logger.error(f"  Event: {event.name}")
                    logger.error("=" * 60)
                    assert False, f"Super TAKI played but no prior color to inherit (event={event.name})"
                
                taki_color = last_color
                last_type = "SUPER_TAKI"
                logger.debug(f"[TEST_REGULAR_CARDS] Entering SUPER_TAKI mode: inherited color={taki_color}")
            
            # Reset last-card-in-sequence trackers for this TAKI sequence
            taki_last_color = None
            taki_last_type = None
        
            logger.debug(
                f"[TEST_REGULAR_CARDS] Tracking updated (no validation): {event.name} -> {last_color}/{last_type}"
            )
            continue
        
        # ------------------------------------------------------------
        # CHANGE_COLOR (wait for selected_<color>)
        # ------------------------------------------------------------
        if is_change_color_event(event):
            logger.debug(f"[TEST_REGULAR_CARDS] change_color played, waiting for color selection...")
            
            # Check if we're in TAKI mode - this should NEVER happen with correct rules
            if in_taki_mode:
                logger.error("=" * 60)
                logger.error("[TEST_REGULAR_CARDS] X TEST FAILED - change_color during TAKI!")
                logger.error(f"  change_color should be blocked during TAKI sequences")
                logger.error("=" * 60)
                assert False, "change_color played during TAKI (should be blocked by game rules)"
                # If assertions are disabled, we still need to handle this gracefully
                continue  # ← ADD THIS: Skip rest of handling
            
            # Outside TAKI: normal color selection handling
            selected_color_events = [BPEvent(f"selected_{c}", priority=5.0) for c in COLORS]
            color_event = yield bp.sync(waitFor=selected_color_events)
            
            selected_color, _ = extract_card_color_and_type(color_event)
            
            if selected_color is None:
                assert False, f"change_color played but selection color not parsed (event={color_event.name})"
            
            last_color = selected_color
            last_type = "CHANGE_COLOR"
            
            logger.debug(f"[TEST_REGULAR_CARDS] Color changed to: {selected_color}/CHANGE_COLOR")
            continue

        # ------------------------------------------------------------
        # STOP (track differently inside vs. outside TAKI)
        # ------------------------------------------------------------
        if is_stop_card_event(event):
            card_color, card_type = extract_card_color_and_type(event)
            
            if in_taki_mode:
                # Track as last card in TAKI sequence
                taki_last_color, taki_last_type = card_color, card_type
                logger.debug(
                    f"[TEST_REGULAR_CARDS] Stop during TAKI (tracked as last TAKI card): "
                    f"{event.name} -> {card_color}/{card_type}"
                )
            else:
                # Outside TAKI: becomes new leading card
                last_color, last_type = card_color, card_type
                logger.debug(
                    f"[TEST_REGULAR_CARDS] Tracking updated (no validation): {event.name} -> {last_color}/{last_type}"
                )
            continue

        # ------------------------------------------------------------
        # Validate REGULAR numbered cards ONLY (card_1..card_9)
        # ------------------------------------------------------------
        if is_regular_card_event(event):
            card_color, card_type = extract_card_color_and_type(event)

            if in_taki_mode:
                # During TAKI: must match TAKI color only
                if card_color != taki_color:
                    logger.error("=" * 60)
                    logger.error("[TEST_REGULAR_CARDS] X TEST FAILED - Illegal card during TAKI!")
                    logger.error(f"  TAKI color:      {taki_color}")
                    logger.error(f"  Played:          {event.name}")
                    logger.error(f"  Card color:      {card_color} X")
                    logger.error("=" * 60)
                    assert False, (
                        f"TAKI color violation: {event.name} (color={card_color}) "
                        f"doesn't match TAKI color {taki_color}"
                    )
                
                logger.debug(
                    f"[TEST_REGULAR_CARDS] V Legal in TAKI: {event.name} (matched TAKI color {taki_color})"
                )

                # Track as last played card in TAKI sequence
                taki_last_color, taki_last_type = card_color, card_type
                continue

            # Outside TAKI: must match color OR type
            color_matches = (card_color == last_color)
            type_matches = (card_type == last_type)

            if not (color_matches or type_matches):
                logger.error("=" * 60)
                logger.error("[TEST_REGULAR_CARDS] X TEST FAILED - Illegal regular card placement!")
                logger.error(f"  Previous leading: {last_color}/{last_type}")
                logger.error(f"  Played:          {event.name}")
                logger.error(f"  Card color:      {card_color} {'V' if color_matches else 'X'}")
                logger.error(f"  Card type:       {card_type} {'V' if type_matches else 'X'}")
                logger.error("=" * 60)
                assert False, (
                    f"Regular card placement violated: {event.name} "
                    f"(color={card_color}, type={card_type}) doesn't match "
                    f"previous (color={last_color}, type={last_type})"
                )

            logger.debug(
                f"[TEST_REGULAR_CARDS] V Legal regular: {event.name} "
                f"(matched {'color' if color_matches else 'type'})"
            )
            last_color, last_type = card_color, card_type
            continue

        # ------------------------------------------------------------
        # Everything else: ignore with breadcrumb
        # ------------------------------------------------------------
        logger.debug(f"[TEST_REGULAR_CARDS] Ignored unclassified event: {event.name}")


@bp.thread
def test_card_placement_rules_extended():
    """
    Validates that consecutive regular numbered cards follow color-or-type matching.

    Scope: ONLY regular card → regular card transitions
    Resets: On any non-regular player event
    """
    
    logger.info("[test_consecutive_regular_cards] Test starting...")

    yield bp.sync(waitFor=BPEvent("deal_leading_card"))
    leading_card = yield bp.sync(waitFor=leading_card_event_set)
    prev_color, prev_type = extract_card_color_and_type(leading_card)

    logger.debug(f"[test_consecutive_regular_cards] Leading: {prev_color}/{prev_type}")
    yield bp.sync(waitFor=BPEvent("start_game"))

    while True:
        event = yield bp.sync(waitFor=general_player_event_set)

        # Skip protocol events
        if event.name in ["next_turn", "done_post_action"] or "draw_card" in event.name:
            continue

        # End game
        if event.name == "end_game":
            logger.info("[test_consecutive_regular_cards] V Test PASSED")
            break

        # Reset on any non-regular played event
        if not is_regular_card_event(event):
            logger.debug(f"[test_consecutive_regular_cards] Non-regular {event.name}, resetting...")

            reset_event = yield bp.sync(
                waitFor=bp.EventSetList([played_regular_cards_event_set, BPEvent("end_game")])
            )
            
            if reset_event.name == "end_game":
                logger.info("[test_consecutive_regular_cards] V Test PASSED")
                break

            prev_color, prev_type = extract_card_color_and_type(reset_event)
            logger.debug(f"[test_consecutive_regular_cards] Reset to: {prev_color}/{prev_type}")
            continue

        # Validate regular -> regular
        curr_color, curr_type = extract_card_color_and_type(event)
        if not (curr_color == prev_color or curr_type == prev_type):
            logger.error("=" * 60)
            logger.error("[test_consecutive_regular_cards] X TEST FAILED")
            logger.error(f"  Previous: {prev_color}/{prev_type}")
            logger.error(f"  Current:  {curr_color}/{curr_type} ({event.name})")
            logger.error("=" * 60)
            assert False, "Consecutive regular cards don't match"

        logger.debug(f"[test_consecutive_regular_cards] V Valid: {event.name}")
        prev_color, prev_type = curr_color, curr_type


@bp.thread
def enforce_card_placement_rules_BROKEN():
    """
    TEMPORARILY BROKEN VERSION - allows illegal moves for testing
    """
    yield bp.sync(waitFor=BPEvent("deal_leading_card", priority=10.0))
    last_event = yield bp.sync(waitFor=leading_card_event_set)
    yield bp.sync(waitFor=BPEvent("finished_leading_card", priority=10.0))
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    
    # INTENTIONAL BUG: Don't block anything - allow any card!
    while True:
        last_event = yield bp.sync(waitFor=general_player_event_set)
        # Just track events, don't enforce any rules


@bp.thread  
def strategy_color_dominance(index, num_of_cards=2):
    """
    B-thread implementing color dominance strategy: prioritize one dominant color throughout the game.
    
    This strategy analyzes the player's initial hand, identifies the most common color,
    and consistently prioritizes playing cards of that color by adjusting event priorities.
    
    Works ALONGSIDE player_behavior in the sense that both can coexist in the system,
    but this strategy handles its own card management (like basic_strategy_taki).
    
    Parameters
    ----------
    index : int
        Player index (0 or 1)
    num_of_cards : int
        Initial number of cards dealt to the player
    
    Strategy Logic
    --------------
    1. Analyzes initial hand to find the most common color
    2. Adjusts priorities: dominant color cards get priority 5.0, others get 12.0
    3. Event selection will prefer dominant color cards while respecting game rules
    4. All game rule constraints are automatically respected (no deadlock risk)
    """
    logger.debug(f"[STRATEGY_COLOR_DOM] Player {index}: Starting color dominance strategy")
    
    # Track cards and their colors during initial deal
    card_colors = {color: 0 for color in COLORS}
    card_events = []
    deal_player_cards_event_set = DealCardsEventSet()
    
    # Receive initial hand and count colors
    for i in range(num_of_cards):
        # Wait for this player's turn to receive a card
        yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
        # Then wait for the actual card being dealt
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
        
        # Count colors
        for color in COLORS:
            if color in card_name:
                card_colors[color] += 1
                break
        
        # Store card info temporarily
        card_events.append({
            'name': card_name,
            'original_priority': deal_card_event.priority
        })
    
    # Determine dominant color (most common in hand)
    dominant_color = max(card_colors, key=card_colors.get)
    logger.debug(
        f"[STRATEGY_COLOR_DOM] Player {index}: Color analysis: "
        f"Red={card_colors['red']}, Blue={card_colors['blue']}, Green={card_colors['green']} "
        f"→ Dominant color: {dominant_color.upper()} ({card_colors[dominant_color]} cards)"
    )
    
    # Convert to BPEvents with adjusted priorities
    adjusted_card_events = []
    for card_info in card_events:
        add_event_to_card_events_according_to_color_dominance(
            index, 
            card_info['name'], 
            card_info['original_priority'],
            adjusted_card_events,
            dominant_color
        )
    
    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))
    logger.debug(f"[STRATEGY_COLOR_DOM] Player {index}: Game started! Prioritizing {dominant_color.upper()} cards")
    
    # Main game loop
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    no_more_cards_event = BPEvent(f"p_{index}_no_more_cards", priority=8.0)
    next_turn = BPEvent("next_turn", priority=10.0)
    
    turn_count = 0
    dominant_color_plays = 0
    other_color_plays = 0
    
    while True:
        turn_count += 1
        
        # Request cards with adjusted priorities
        card_event = yield bp.sync(request=adjusted_card_events, waitFor=[draw_card_event])
        
        logger.debug(f"[STRATEGY_COLOR_DOM] Player {index} Turn {turn_count}: {card_event.name} (priority {card_event.priority})")
        
        if is_regular_card_event(card_event):
            # Track and remove from hand
            if dominant_color in card_event.name:
                dominant_color_plays += 1
                logger.debug(f"[STRATEGY_COLOR_DOM] Player {index}: Played dominant color ({dominant_color})")
            else:
                other_color_plays += 1
                color_played = None
                for color in COLORS:
                    if color in card_event.name:
                        color_played = color
                        break
                logger.debug(f"[STRATEGY_COLOR_DOM] Player {index}: Played off-color ({color_played})")
            
            adjusted_card_events.remove(card_event)
        
        elif is_draw_card_event(card_event):
            # Draw a new card with appropriate priority
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            
            add_event_to_card_events_according_to_color_dominance(
                index,
                card_name,
                deal_card_event.priority,
                adjusted_card_events,
                dominant_color
            )
            
        elif is_action_card_event(card_event):
            if is_any_taki_event(card_event):
                # Handle TAKI sequence
                logger.debug(f"[STRATEGY_COLOR_DOM] Player {index}: TAKI sequence starting")
                adjusted_card_events.remove(card_event)
                
                # Add closed_taki
                closed_taki_event = BPEvent(f"p_{index}_closed_taki", priority=15.0)
                adjusted_card_events.append(closed_taki_event)
                
                # Play cards during TAKI sequence
                while True:
                    card_event = yield bp.sync(request=adjusted_card_events)
                    adjusted_card_events.remove(card_event)
                    
                    if card_event.name == f"p_{index}_closed_taki":
                        logger.debug(f"[STRATEGY_COLOR_DOM] Player {index}: TAKI sequence closed")
                        break
                
                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
            else:
                # Other action cards (stop, plus_2, etc.)
                # Note: change_color is never in adjusted_card_events, so this won't handle it
                adjusted_card_events.remove(card_event)
                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
        
        # Announce turn completion and wait for it
        if list_does_not_contain_card_events(adjusted_card_events):
            yield bp.sync(request=no_more_cards_event)
            logger.debug(
                f"[STRATEGY_COLOR_DOM] Player {index}: Game ended. "
                f"Dominant color ({dominant_color}) played: {dominant_color_plays} times, "
                f"Other colors: {other_color_plays} times"
            )
            break
        
        # Request next_turn and wait for turn to complete
        yield bp.sync(request=next_turn)
        last_event = yield bp.sync(waitFor=[no_more_cards_event, next_turn])
        
        if "next_turn" in last_event.name:
            logger.debug(f"[STRATEGY_COLOR_DOM] Player {index} | Remaining: {len(adjusted_card_events)} cards")
            continue
        elif "no_more_cards" in last_event.name:
            logger.debug(
                f"[STRATEGY_COLOR_DOM] Player {index}: Game ended. "
                f"Dominant color ({dominant_color}) played: {dominant_color_plays} times, "
                f"Other colors: {other_color_plays} times"
            )
            break