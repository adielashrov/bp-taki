"""
Experiment: sweep the priority value that
`prefer_popular_color_regular_cards_strategy_original` assigns to regular
cards of the player's dominant hand color, and measure Player 1's win rate
against basic-strategy Player 0 for each candidate value.

Background
-----------
bp_taki.prefer_popular_color_regular_cards_strategy_original (bp_taki.py:1107)
currently requests dominant-color regular cards at priority 11.0 and all
other regular cards at the default 10.0. Since EventPrioritySelectionStrategy
selects the *lowest* priority number first (bppy/model/event_selection/
event_priority_selection_strategy.py:8), 11.0 vs 10.0 means dominant-color
cards are actually *deprioritized* relative to the default.

This script does not change bp_taki.py. It builds a parameterized copy of the
same b-thread logic (dominant_priority is a free parameter, default behavior
unchanged from the field's perspective) and runs many games per candidate
value to see which value (if any) actually improves Player 1's win rate.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import bppy as bp
from bppy.model.b_priority_event import BPEvent
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy

import bp_taki
from bp_taki import (
    game_manager,
    deal_cards,
    player_behavior,
    block_next_turn_during_open_taki,
    enforce_turns,
    enforce_card_placement_rules,
    identify_deadlock,
    identify_livelock,
    verify_turn_alternation,
    DealCardsEventSet,
    remove_deal_prefix_and_add_player_index,
    is_regular_card_event,
    is_draw_card_event,
    is_no_more_cards_event,
    extract_card_color_and_type,
    COLORS,
    NUM_OF_CARDS,
)
from taki_simulation import SimulationListener, SimulationStats, build_game_schedule


def make_prefer_popular_color_strategy(dominant_priority: float, other_priority: float = 10.0):
    """Same logic as prefer_popular_color_regular_cards_strategy_original,
    but with the dominant-color priority value parameterized.

    Note: ``other_priority`` is the priority assigned to *non*-dominant-color
    regular cards. Set it below 10.0 (with dominant_priority=10.0) to test
    the inverse heuristic: prefer playing minority colors first and conserve
    the dominant color."""

    @bp.thread
    def _strategy(index, num_of_cards=2):
        all_card_events = []
        deal_player_cards_event_set = DealCardsEventSet()

        yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))

        for _ in range(num_of_cards):
            yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            all_card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

        yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

        draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
        closed_taki_event = BPEvent(f"p_{index}_closed_taki", priority=15.0)
        no_more_cards_ev = BPEvent(f"p_{index}_no_more_cards", priority=8.0)
        all_card_events.append(draw_card_event)
        all_card_events.append(closed_taki_event)
        all_card_events.append(no_more_cards_ev)

        while True:
            color_counts = {color: 0 for color in COLORS}
            for e in all_card_events:
                if is_regular_card_event(e):
                    card_color, _ = extract_card_color_and_type(e)
                    if card_color in COLORS:
                        color_counts[card_color] += 1

            dominant_color = max(COLORS, key=lambda c: color_counts[c])

            regular_request_events = []
            for e in all_card_events:
                if is_regular_card_event(e):
                    card_color, _ = extract_card_color_and_type(e)
                    if card_color == dominant_color and color_counts[dominant_color] > 0:
                        regular_request_events.append(BPEvent(e.name, priority=dominant_priority))
                    else:
                        regular_request_events.append(BPEvent(e.name, priority=other_priority))

            observe_set = [e for e in all_card_events if not is_regular_card_event(e)]

            card_event = yield bp.sync(request=regular_request_events, waitFor=observe_set)

            if is_draw_card_event(card_event):
                yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
                deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
                card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
                all_card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

            elif is_no_more_cards_event(card_event):
                break

            elif card_event.name == f"p_{index}_closed_taki":
                pass

            elif card_event in all_card_events:
                all_card_events.remove(card_event)

    return _strategy


def make_prefer_popular_color_strategy_probabilistic(
    boost_priority: float,
    boost_probability: float,
    coin_rng: random.Random,
    other_priority: float = 10.0,
):
    """Same as make_prefer_popular_color_strategy, but each turn the boost is
    only applied with probability ``boost_probability`` (decided by an
    independent local RNG, NOT the shared global ``random`` stream used for
    dealing/shuffling, so the coin flip itself doesn't perturb game setup).
    When the coin flip fails, this turn's request is identical to doing
    nothing (all regular cards at the neutral default priority)."""

    @bp.thread
    def _strategy(index, num_of_cards=2):
        all_card_events = []
        deal_player_cards_event_set = DealCardsEventSet()

        yield bp.sync(waitFor=BPEvent("start_dealing_cards_to_players", priority=10.0))

        for _ in range(num_of_cards):
            yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            all_card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

        yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

        draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
        closed_taki_event = BPEvent(f"p_{index}_closed_taki", priority=15.0)
        no_more_cards_ev = BPEvent(f"p_{index}_no_more_cards", priority=8.0)
        all_card_events.append(draw_card_event)
        all_card_events.append(closed_taki_event)
        all_card_events.append(no_more_cards_ev)

        while True:
            color_counts = {color: 0 for color in COLORS}
            for e in all_card_events:
                if is_regular_card_event(e):
                    card_color, _ = extract_card_color_and_type(e)
                    if card_color in COLORS:
                        color_counts[card_color] += 1

            dominant_color = max(COLORS, key=lambda c: color_counts[c])
            apply_boost_this_turn = coin_rng.random() < boost_probability

            regular_request_events = []
            for e in all_card_events:
                if is_regular_card_event(e):
                    card_color, _ = extract_card_color_and_type(e)
                    if apply_boost_this_turn and card_color == dominant_color and color_counts[dominant_color] > 0:
                        regular_request_events.append(BPEvent(e.name, priority=boost_priority))
                    else:
                        regular_request_events.append(BPEvent(e.name, priority=other_priority))

            observe_set = [e for e in all_card_events if not is_regular_card_event(e)]

            card_event = yield bp.sync(request=regular_request_events, waitFor=observe_set)

            if is_draw_card_event(card_event):
                yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))
                deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
                card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
                all_card_events.append(BPEvent(card_name, priority=deal_card_event.priority))

            elif is_no_more_cards_event(card_event):
                break

            elif card_event.name == f"p_{index}_closed_taki":
                pass

            elif card_event in all_card_events:
                all_card_events.remove(card_event)

    return _strategy


def run_one_game(seed, starting_player, dominant_priority, other_priority=10.0, num_cards=NUM_OF_CARDS):
    listener = SimulationListener()
    random.seed(seed)

    bthreads = [
        game_manager(),
        deal_cards(2, num_cards, starting_player),
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        block_next_turn_during_open_taki(0),
        block_next_turn_during_open_taki(1),
        enforce_turns(2, starting_player),
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation(),
        make_prefer_popular_color_strategy(dominant_priority, other_priority)(1, num_cards),
    ]

    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=listener,
    )

    try:
        b_program.run()
    except AssertionError:
        if not (listener.get_deadlock() or listener.get_draw()):
            raise

    return listener.get_winner(), listener.get_deadlock(), listener.get_draw()


def run_one_game_probabilistic(
    seed, starting_player, boost_priority, boost_probability, other_priority=10.0, num_cards=NUM_OF_CARDS
):
    listener = SimulationListener()
    random.seed(seed)
    # Independent local RNG for the per-turn coin flip, seeded off the game
    # seed for reproducibility but never touching the shared global stream.
    coin_rng = random.Random(seed * 7919 + 13)

    bthreads = [
        game_manager(),
        deal_cards(2, num_cards, starting_player),
        player_behavior(0, num_cards),
        player_behavior(1, num_cards),
        block_next_turn_during_open_taki(0),
        block_next_turn_during_open_taki(1),
        enforce_turns(2, starting_player),
        enforce_card_placement_rules(),
        identify_deadlock(),
        identify_livelock(),
        verify_turn_alternation(),
        make_prefer_popular_color_strategy_probabilistic(
            boost_priority, boost_probability, coin_rng, other_priority
        )(1, num_cards),
    ]

    b_program = bp.BProgram(
        bthreads=bthreads,
        event_selection_strategy=EventPrioritySelectionStrategy(),
        listener=listener,
    )

    try:
        b_program.run()
    except AssertionError:
        if not (listener.get_deadlock() or listener.get_draw()):
            raise

    return listener.get_winner(), listener.get_deadlock(), listener.get_draw()


def sweep_probability(probabilities, boost_priority=8.0, num_games=2000, start_seed=0):
    """Sweep boost_probability in [0, 1] for the dominant-color boost.
    p=0.0 should reproduce the no-op baseline; p=1.0 should reproduce the
    fully-deterministic dominant_priority=boost_priority result from sweep()."""
    schedule = build_game_schedule(
        num_games=num_games,
        start_seed=start_seed,
        balanced_starting_players=True,
    )

    print(
        f"Sweeping {len(probabilities)} boost_probability candidates "
        f"(boost_priority={boost_priority}) over {len(schedule)} games each."
    )
    print("-" * 70)

    rows = []
    for p in probabilities:
        p0_wins = p1_wins = deadlocks = draws = 0
        for seed, starting_player in schedule:
            winner, deadlock, draw = run_one_game_probabilistic(
                seed, starting_player, boost_priority, p, other_priority=10.0
            )
            if winner == 0:
                p0_wins += 1
            elif winner == 1:
                p1_wins += 1
            if deadlock:
                deadlocks += 1
            if draw:
                draws += 1

        total = len(schedule)
        p1_rate = p1_wins / total * 100
        ci_lo, ci_hi = SimulationStats.wilson_ci(p1_wins, total)
        rows.append((p, p1_wins, p0_wins, deadlocks, draws, p1_rate, ci_lo * 100, ci_hi * 100))
        print(
            f"boost_probability={p:4.2f} | "
            f"P1 wins: {p1_wins:4d}/{total} ({p1_rate:5.1f}%) "
            f"[{ci_lo*100:5.1f}%, {ci_hi*100:5.1f}%] | "
            f"P0 wins: {p0_wins:4d} | deadlocks: {deadlocks} | draws: {draws}"
        )

    return rows


def sweep(candidates, num_games=2000, start_seed=0):
    schedule = build_game_schedule(
        num_games=num_games,
        start_seed=start_seed,
        balanced_starting_players=True,
    )

    print(f"Sweeping {len(candidates)} dominant_priority candidates over {len(schedule)} games each.")
    print(f"(other_priority fixed at 10.0; lower priority number = selected first)")
    print("-" * 70)

    rows = []
    for dominant_priority in candidates:
        p0_wins = p1_wins = deadlocks = draws = 0
        for seed, starting_player in schedule:
            winner, deadlock, draw = run_one_game(seed, starting_player, dominant_priority, other_priority=10.0)
            if winner == 0:
                p0_wins += 1
            elif winner == 1:
                p1_wins += 1
            if deadlock:
                deadlocks += 1
            if draw:
                draws += 1

        total = len(schedule)
        p1_rate = p1_wins / total * 100
        ci_lo, ci_hi = SimulationStats.wilson_ci(p1_wins, total)
        rows.append((dominant_priority, p1_wins, p0_wins, deadlocks, draws, p1_rate, ci_lo * 100, ci_hi * 100))
        print(
            f"dominant_priority={dominant_priority:5.1f} | "
            f"P1 wins: {p1_wins:4d}/{total} ({p1_rate:5.1f}%) "
            f"[{ci_lo*100:5.1f}%, {ci_hi*100:5.1f}%] | "
            f"P0 wins: {p0_wins:4d} | deadlocks: {deadlocks} | draws: {draws}"
        )

    return rows


def sweep_inverse(candidates, num_games=2000, start_seed=0):
    """Boost the MINORITY-color regular cards instead of the dominant one
    (dominant_priority pinned at the neutral default 10.0, other_priority
    swept below it). Tests: does conserving the dominant color help?"""
    schedule = build_game_schedule(
        num_games=num_games,
        start_seed=start_seed,
        balanced_starting_players=True,
    )

    print(f"Sweeping {len(candidates)} other_priority (minority-color boost) candidates over {len(schedule)} games each.")
    print(f"(dominant_priority fixed at 10.0; lower priority number = selected first)")
    print("-" * 70)

    rows = []
    for other_priority in candidates:
        p0_wins = p1_wins = deadlocks = draws = 0
        for seed, starting_player in schedule:
            winner, deadlock, draw = run_one_game(seed, starting_player, dominant_priority=10.0, other_priority=other_priority)
            if winner == 0:
                p0_wins += 1
            elif winner == 1:
                p1_wins += 1
            if deadlock:
                deadlocks += 1
            if draw:
                draws += 1

        total = len(schedule)
        p1_rate = p1_wins / total * 100
        ci_lo, ci_hi = SimulationStats.wilson_ci(p1_wins, total)
        rows.append((other_priority, p1_wins, p0_wins, deadlocks, draws, p1_rate, ci_lo * 100, ci_hi * 100))
        print(
            f"other_priority={other_priority:5.1f} | "
            f"P1 wins: {p1_wins:4d}/{total} ({p1_rate:5.1f}%) "
            f"[{ci_lo*100:5.1f}%, {ci_hi*100:5.1f}%] | "
            f"P0 wins: {p0_wins:4d} | deadlocks: {deadlocks} | draws: {draws}"
        )

    return rows


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dominant"

    if mode == "dominant":
        # 10.0 is the "no effect" baseline (identical to plain basic strategy).
        # 11.0 is the current (buggy) value actually shipped in bp_taki.py.
        # Values below 10.0 are the "fix the direction" candidates; we sweep a
        # spread to see how strong the boost should be.
        candidates = [13.0, 12.0, 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0]
        sweep(candidates, num_games=2000, start_seed=0)
    elif mode == "inverse":
        # Test the opposite heuristic: boost minority colors, conserve the
        # dominant color as a flexibility reserve.
        candidates = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0]
        sweep_inverse(candidates, num_games=2000, start_seed=0)
    elif mode == "probability":
        # Apply the dominant-color boost (priority=8.0) only with probability
        # p each turn; p=0.0 ~ no-op baseline, p=1.0 ~ fully deterministic
        # boost (matches sweep([8.0]) result). Tests whether partial
        # determinism is less harmful than full determinism.
        probabilities = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
        sweep_probability(probabilities, boost_priority=8.0, num_games=2000, start_seed=0)
    else:
        raise SystemExit(f"Unknown mode: {mode!r} (expected 'dominant', 'inverse', or 'probability')")
