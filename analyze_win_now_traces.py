"""
Step 2: Parse trace files to check whether strategy_win_now_color_selection fires.

For every trace, we:
  1. Reconstruct player 1's hand event-by-event.
  2. When p_1_change_color is played, snapshot the hand and run _find_win_now_color.
  3. Record the selected_* color that immediately follows.
  4. Compare: did the selected color match what win-now would have chosen?
"""

import os
import re
import sys

sys.path.insert(0, ".")
from bp_taki import _find_win_now_color, COLORS

# ── helpers ──────────────────────────────────────────────────────────────────

EVENT_RE = re.compile(r"BPEvent\(name=([^,]+),")

DEAL_P1 = re.compile(r"^deal_p_(.+)$")          # deal_p_card_3_blue  →  card_3_blue
REMOVE_PREFIX = re.compile(r"^deal_p_")

COLORS_SET = set(COLORS)


def parse_event_name(line: str) -> str | None:
    m = EVENT_RE.search(line)
    return m.group(1).strip() if m else None


def deal_to_p1_card_name(event_name: str, index: int) -> str:
    """Convert deal_p_card_3_blue → p_1_card_3_blue."""
    inner = REMOVE_PREFIX.sub("", event_name)   # card_3_blue
    return f"p_{index}_{inner}"


class FakeEvent:
    """Minimal stand-in for BPEvent so _find_win_now_color can work."""
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"FakeEvent({self.name})"


# ── main analysis ─────────────────────────────────────────────────────────────

def analyze_file(path: str, player_index: int = 1):
    """
    Returns a list of dicts, one per change_color event played by player_index.
    """
    results = []
    hand = []            # list of FakeEvent
    events = []          # full event sequence
    expecting_deal = False   # True right after deal_cards_to_player_{index}

    with open(path) as f:
        raw = [parse_event_name(l) for l in f if l.strip()]
    events = [e for e in raw if e]

    i = 0
    while i < len(events):
        name = events[i]

        # ── deal sequence ──────────────────────────────────────────────────
        if name == f"deal_cards_to_player_{player_index}":
            # next event is the actual card
            i += 1
            if i < len(events):
                card_name = deal_to_p1_card_name(events[i], player_index)
                hand.append(FakeEvent(card_name))
            i += 1
            continue

        # ── card played by player_index ────────────────────────────────────
        if name.startswith(f"p_{player_index}_"):
            # remove from hand if present (skip closed_taki; it's virtual)
            if not name.endswith("_closed_taki") and not name.endswith("_draw_card") \
                    and not name.endswith("_no_more_cards"):
                hand = [e for e in hand if e.name != name]

            # change_color moment: snapshot hand and look ahead for selected_*
            if name == f"p_{player_index}_change_color":
                hand_snapshot = [FakeEvent(e.name) for e in hand]
                win_now_color = _find_win_now_color(hand_snapshot)

                # find the next selected_* event
                selected_color = None
                for j in range(i + 1, min(i + 10, len(events))):
                    if events[j].startswith("selected_"):
                        selected_color = events[j].replace("selected_", "")
                        break

                results.append({
                    "event_index": i,
                    "hand_snapshot": [e.name for e in hand_snapshot],
                    "win_now_color": win_now_color,
                    "selected_color": selected_color,
                    "win_now_fired": (
                        win_now_color is not None
                        and selected_color == win_now_color
                    ),
                    "win_now_missed": (
                        win_now_color is not None
                        and selected_color != win_now_color
                    ),
                })

        i += 1

    return results


def run_analysis(traces_dir: str = "traces", player_index: int = 1):
    files = sorted(
        f for f in os.listdir(traces_dir) if f.endswith(".log")
    )
    if not files:
        print("No trace files found.")
        return

    total_change_color = 0
    win_now_opportunities = 0
    win_now_fired = 0
    win_now_missed = 0
    examples_fired = []
    examples_missed = []

    for fname in files:
        path = os.path.join(traces_dir, fname)
        try:
            hits = analyze_file(path, player_index)
        except Exception as exc:
            print(f"  ERROR parsing {fname}: {exc}")
            continue

        for h in hits:
            total_change_color += 1
            if h["win_now_color"]:
                win_now_opportunities += 1
                if h["win_now_fired"]:
                    win_now_fired += 1
                    if len(examples_fired) < 3:
                        examples_fired.append((fname, h))
                else:
                    win_now_missed += 1
                    if len(examples_missed) < 3:
                        examples_missed.append((fname, h))

    print("=" * 60)
    print(f"Player {player_index} change_color events total : {total_change_color}")
    print(f"Win-now opportunities found                     : {win_now_opportunities}")
    print(f"  Win-now color was selected (fired correctly)  : {win_now_fired}")
    print(f"  Win-now color was NOT selected (missed/wrong) : {win_now_missed}")
    print("=" * 60)

    if examples_fired:
        print("\nExample(s) where win-now FIRED correctly:")
        for fname, h in examples_fired:
            print(f"  {fname}  event_idx={h['event_index']}")
            print(f"    hand      : {h['hand_snapshot']}")
            print(f"    win_now   : {h['win_now_color']}")
            print(f"    selected  : {h['selected_color']}")

    if examples_missed:
        print("\nExample(s) where win-now opportunity was MISSED:")
        for fname, h in examples_missed:
            print(f"  {fname}  event_idx={h['event_index']}")
            print(f"    hand      : {h['hand_snapshot']}")
            print(f"    win_now   : {h['win_now_color']}")
            print(f"    selected  : {h['selected_color']}")

    if win_now_opportunities == 0:
        print("\nNo win-now opportunities arose in these 100 games.")
        print("That is plausible (2-card hands rarely align), but Step 4")
        print("(controlled smoke test) is needed to confirm the logic works.")


if __name__ == "__main__":
    run_analysis()
