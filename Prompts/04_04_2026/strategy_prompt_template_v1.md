# Prompt Template: LLM-Generated Strategy B-Thread for BP Taki

---

## SYSTEM PROMPT

You are an expert in Behavioral Programming (BP) and Python. Your task is to implement a **strategy b-thread** for a two-player card game called Taki, using a Python BP framework called BPpy.

---

## PART 1 — Behavioral Programming Concepts

### What is a b-thread?

A b-thread is a generator function (decorated with `@bp.thread`) that models one behavioral scenario. It expresses its intent at each step by calling:

```python
result = yield bp.sync(
    request=<events to propose>,   # Events this b-thread wants to trigger
    waitFor=<events to observe>,   # Events this b-thread wants to be notified of
    block=<events to forbid>,      # Events this b-thread prevents from being selected
)
```

All b-threads synchronize at each `yield`. The runtime selects one event that is **requested** by at least one b-thread and **not blocked** by any b-thread. All b-threads that requested or waited for that event are then notified and resume.

### Priority system

This implementation uses `BPEvent` objects with a numeric `priority` field:

```python
BPEvent("event_name", priority=5.0)
```

**Lower priority number = higher selection preference.** Default priority is `10.0`.

A strategy b-thread influences which card gets played by requesting all cards in the player's hand, but assigning lower priority numbers to preferred cards. The event selection strategy will pick the lowest-priority event that is not blocked.

Priority ranges used in this codebase:
- `4.0–6.0` → preferred strategic cards
- `8.0` → `no_more_cards` (win announcement)
- `10.0` → default / neutral
- `15.0` → `closed_taki` (closing a TAKI sequence — intentionally deprioritized)
- `20.0` → `draw_card` (last resort)

### Important constraints

- A strategy b-thread **must not** use `block=`. Blocking is reserved for rule-enforcement b-threads. A strategy that blocks events may cause deadlocks or violate game invariants.
- A strategy b-thread **must not** request game-lifecycle events like `next_turn`, `end_game`, `done_post_action`. Those are owned by `player_behavior`.
- A strategy b-thread **only influences selection** by adjusting priorities. It does not control the game flow.

---

## PART 2 — Game Overview: Taki

Taki is a shedding card game. The goal is to be the first player to empty your hand.

### Card types

| Card name pattern | Description |
|---|---|
| `card_{N}_{color}` | Regular numbered card. Colors: `red`, `blue`, `green`. Numbers: `1`, `3`, `4`, `5` |
| `stop_{color}` | Action card: the next player loses their turn |
| `change_color` | Wild card: can be played on anything; the player then announces the new color |
| `taki_{color}` | TAKI card: starts a sequence where the player may play multiple same-color cards |
| `super_taki` | Wild TAKI: starts a TAKI sequence of any color |

### Placement rules (enforced by the runtime — not your concern)

- A regular card must match the top card by **color** or by **number**.
- `change_color` and `super_taki` are **wild** — they can be played on anything.
- During a TAKI sequence, all cards played must match the **TAKI's color**.

### Observable game state during a strategy b-thread's turn

From the `card_events` list the strategy b-thread maintains, you can derive:
- Your own hand composition (card names, types, colors)
- How many cards you have

Additionally, if you use the `ExternalBridgeState` (available via `state` dict), you can observe:
- `state["opponent_card_count"]` — number of cards the opponent currently holds
- `state["top_card_color"]` — color of the top discard pile card
- `state["top_card_type"]` — type of the top discard pile card

*Note: The basic strategy b-thread shown in Part 3 does not use the external bridge state. You may add it if your strategy benefits from opponent awareness.*

---

## PART 3 — Code Context and Conventions

### Event naming conventions

Cards in a player's hand are tracked as `BPEvent` objects with player-scoped names:

```
p_{index}_card_{N}_{color}     # e.g. p_0_card_5_red
p_{index}_stop_{color}         # e.g. p_1_stop_blue
p_{index}_change_color
p_{index}_taki_{color}         # e.g. p_0_taki_red
p_{index}_super_taki
p_{index}_closed_taki          # Virtual event: closes a TAKI sequence
p_{index}_draw_card            # Virtual event: draw a card from the deck
p_{index}_no_more_cards        # Virtual event: player empties their hand
next_turn                      # Signals end of a player's turn
done_post_action               # Signals that an action card's effect is resolved
```

### Helper functions available to you

```python
is_regular_card_event(event)   # True for card_{N}_{color} events
is_action_card_event(event)    # True for stop, change_color, taki, super_taki
is_taki_card_event(event)      # True for taki_{color} (not super_taki)
is_super_taki_event(event)     # True for super_taki
is_any_taki_event(event)       # True for taki_{color} or super_taki
is_change_color_event(event)   # True for change_color
is_draw_card_event(event)      # True for draw_card events
extract_card_color_and_type(event)  # Returns (color, type) tuple, e.g. ("red", "5") or ("", "CHANGE_COLOR")
remove_deal_prefix_and_add_player_index(deal_event, index)  # Converts "deal_p_card_5_red" → "p_0_card_5_red"
```

### Imports and decorator

```python
import bppy as bp
from bppy.model.b_priority_event import BPEvent

# The @bp.thread decorator turns the generator function into a b-thread
@bp.thread
def my_strategy(index, num_of_cards=2):
    ...
```

---

## PART 4 — Reference Implementations (Few-Shot Examples)

### Example 1: `basic_strategy_taki` — Prefer TAKI cards

This strategy boosts the priority of any TAKI or Super TAKI card in hand so the runtime selects them before regular cards.

```python
def add_card_with_taki_priority(index, card_name, original_priority, card_events):
    """Assign priority 5.0 to any TAKI card; keep default for others."""
    if "taki" in card_name:
        card_events.append(BPEvent(card_name, priority=5.0))
    else:
        card_events.append(BPEvent(card_name, priority=original_priority))


@bp.thread
def basic_strategy_taki(index, num_of_cards=2):
    """Prioritize playing TAKI/Super TAKI cards above all others."""

    # --- Phase 1: Receive initial hand ---
    yield bp.sync(waitFor=BPEvent(f"deal_cards_to_player_{index}", priority=10.0))

    card_events = []
    deal_player_cards_event_set = DealCardsEventSet()

    for i in range(num_of_cards):
        deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
        card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
        add_card_with_taki_priority(index, card_name, deal_card_event.priority, card_events)

    yield bp.sync(waitFor=BPEvent("start_game", priority=10.0))

    # --- Phase 2: Turn loop ---
    draw_card_event = BPEvent(f"p_{index}_draw_card", priority=20.0)
    no_more_cards_event = BPEvent(f"p_{index}_no_more_cards", priority=8.0)
    next_turn = BPEvent("next_turn", priority=10.0)

    while True:
        # Request all cards in hand; runtime picks lowest-priority (most preferred)
        card_event = yield bp.sync(request=card_events, waitFor=[draw_card_event])

        if is_regular_card_event(card_event):
            card_events.remove(card_event)

        elif is_action_card_event(card_event):
            if is_any_taki_event(card_event):
                # Enter TAKI sequence
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
                # stop, plus_2, change_color, etc.
                yield bp.sync(waitFor=BPEvent("done_post_action", priority=10.0))
                card_events.remove(card_event)

        elif is_draw_card_event(card_event):
            deal_card_event = yield bp.sync(waitFor=deal_player_cards_event_set)
            card_name = remove_deal_prefix_and_add_player_index(deal_card_event, index)
            add_card_with_taki_priority(index, card_name, deal_card_event.priority, card_events)

        # Wait for turn to end
        last_event = yield bp.sync(waitFor=[no_more_cards_event, next_turn])

        if "no_more_cards" in last_event.name:
            break   # Game over — this player won
        # else: "next_turn" → continue to next iteration
```

### Example 2: `basic_strategy_taki_and_super_taki` — Distinguish TAKI vs Super TAKI

This strategy differentiates between regular TAKI (priority 4.0 — most preferred) and Super TAKI (priority 6.0 — preferred, but less so than regular TAKI). The reasoning: regular TAKI lets you chain same-color cards, which is typically more powerful when you have such cards in hand; Super TAKI is saved as a wildcard fallback.

```python
def add_card_with_taki_super_taki_priority(index, card_name, original_priority, card_events):
    if "super_taki" in card_name:
        card_events.append(BPEvent(card_name, priority=6.0))
    elif "taki_" in card_name:
        card_events.append(BPEvent(card_name, priority=4.0))
    else:
        card_events.append(BPEvent(card_name, priority=original_priority))
```

*(The turn loop is identical to Example 1 — only the priority assignment function differs.)*

---

## PART 5 — Your Task

Design and implement an **optimal strategy** for the BP Taki player described above.

You are free to reason about the game and determine what "optimal" means — consider the card types available, when each is most valuable, and what observable information can guide better decisions.

Your implementation may consist of **one or more b-threads**. BP naturally supports decomposing a strategy into multiple focused behaviors that each handle one strategic concern and compose together. Use this capability if it leads to a cleaner or more effective design.

The only hard constraints are:
- Your b-threads must follow the turn lifecycle established in the reference examples (deal phase → `start_game` → turn loop → termination on `no_more_cards`).
- Your b-threads must not use `block=` or request lifecycle events (`next_turn`, `done_post_action`, `end_game`) — those are owned by the runtime.
- Your code will be integrated into an existing file, so do not include import statements.

Explain your strategic reasoning before presenting the code.

---

## PART 6 — Common Pitfalls to Avoid

- **Missing `done_post_action` wait**: After playing any non-TAKI action card (stop, change_color), you MUST `yield bp.sync(waitFor=BPEvent("done_post_action", ...))` before continuing. Skipping this causes a deadlock.
- **Wrong TAKI sequence termination**: Inside a TAKI sequence, keep looping with `waitFor=card_events` until `card_event.name == f"p_{index}_closed_taki"`. Do not break early.
- **Forgetting to remove played cards**: After every played card (regular, action, closed_taki), call `card_events.remove(card_event)`.
- **Requesting `draw_card` in the main sync**: Use `waitFor=[draw_card_event]`, not `request=`. The `draw_card` event is requested by the `player_behavior` b-thread; your strategy only observes it.
- **Blocking events**: Do not add `block=` to any `yield bp.sync(...)` in a strategy b-thread.
- **Stale priorities**: If your strategy depends on dynamic conditions (e.g., opponent card count), update the priority of affected cards in `card_events` at the start of each turn iteration, not just at deal time.
