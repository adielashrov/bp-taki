import re
import sys
import glob

COLORS = ["red", "blue", "green"]

EVENT_RE = re.compile(r"BPEvent\(name=([^,]+),data=\{\}, priority=([\d.]+)\)")


def extract_card_color_and_type(name):
    card_str_index = name.find("card")
    if card_str_index != -1:
        card_color = name[card_str_index + 7:]
        card_number = name[card_str_index + 5:card_str_index + 6]
        return card_color, card_number

    stop_str_index = name.find("stop")
    if stop_str_index != -1:
        card_color = name[stop_str_index + 5:]
        return card_color, "STOP"

    change_color_index = name.find("change_color")
    if change_color_index != -1 and "selected_" not in name:
        return "", "CHANGE_COLOR"

    selected_change_color_index = name.find("selected_")
    if selected_change_color_index != -1:
        color = next((c for c in COLORS if c in name), None)
        if color in COLORS:
            return color, "CHANGE_COLOR"
        return None, None

    super_taki_index = name.find("super_taki")
    if super_taki_index != -1:
        return None, "SUPER_TAKI"

    taki_str_index = name.find("taki_")
    if taki_str_index != -1:
        parts = name.split("_")
        color = parts[-1]
        if color in COLORS:
            return color, "TAKI"
        return None, None

    return None, None


def update_placement(name, current_color, current_type):
    card_color, card_type = extract_card_color_and_type(name)
    if card_type == "CHANGE_COLOR" and card_color == "":
        return current_color, current_type
    if card_color is not None or card_type is not None:
        return card_color, card_type
    return current_color, current_type


def hand_remove(hand, color, ctype):
    for i, c in enumerate(hand):
        if c == (color, ctype):
            del hand[i]
            return True
    return False


def analyze(path, player=1):
    hand = []
    placement_color = None
    placement_type = None
    dealing_to = None  # which player index is currently being dealt to
    in_taki = False

    play_prefix = f"p_{player}_"
    play_re = re.compile(rf"^p_{player}_(card|stop|taki|super_taki|change_color)")

    choice_points = []  # list of dicts

    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            m = EVENT_RE.search(line)
            if not m:
                continue
            name = m.group(1)

            # --- dealing tracking ---
            dm = re.match(r"deal_cards_to_player_(\d+)", name)
            if dm:
                dealing_to = int(dm.group(1))
                continue

            if name.startswith("deal_p_") and not name.startswith("leading_deal_p_"):
                if dealing_to == player:
                    color, ctype = extract_card_color_and_type(name)
                    hand.append((color, ctype))
                continue

            if name.startswith("leading_deal_p_"):
                placement_color, placement_type = update_placement(name, placement_color, placement_type)
                continue

            if name in ("finished_dealing_cards_to_players", "deal_leading_card",
                         "finished_leading_card", "start_game", "start_dealing_cards_to_players",
                         "next_turn", "done_post_action"):
                continue

            # --- TAKI sequence tracking for the tracked player ---
            if name == f"{play_prefix}closed_taki":
                in_taki = False
                continue

            # --- tracked player plays a card ---
            if play_re.match(name):
                color, ctype = extract_card_color_and_type(name)

                if name.startswith(f"{play_prefix}draw_card"):
                    continue

                # Check for "choice point": before this play, did hand contain
                # both stop_X and a regular card_n_X for the X matching the
                # current placement color (i.e. both are legal-by-color-match)?
                if not in_taki:
                    combo_colors = set()
                    for c in COLORS:
                        has_stop = (c, "STOP") in hand
                        has_regular = any(h[0] == c and h[1] in ("1", "3", "4", "5") for h in hand)
                        if has_stop and has_regular:
                            combo_colors.add(c)

                    if placement_color in combo_colors:
                        c = placement_color
                        stop_count = hand.count((c, "STOP"))
                        reg_cards = [h for h in hand if h[0] == c and h[1] in ("1", "3", "4", "5")]
                        if ctype == "STOP" and color == c:
                            outcome = "stop"
                        elif color == c and ctype in ("1", "3", "4", "5"):
                            outcome = "regular"
                        else:
                            outcome = f"other({name})"

                        choice_points.append({
                            "line": lineno,
                            "color": c,
                            "placement": f"{placement_color}/{placement_type}",
                            "stop_count": stop_count,
                            "regular_cards": reg_cards,
                            "played": name,
                            "outcome": outcome,
                        })

                # remove played card from hand (if it's a real card the player held)
                if ctype != "CHANGE_COLOR" or color != "":
                    hand_remove(hand, color, ctype)
                else:
                    # change_color card itself (color="", type="CHANGE_COLOR")
                    hand_remove(hand, "", "CHANGE_COLOR")

                # entering TAKI sequence
                if ctype in ("TAKI", "SUPER_TAKI"):
                    in_taki = True

                # update placement (mirrors prefer_stop strategy's update rules)
                if (
                    name.startswith("leading_")
                    or name.startswith("selected_")
                    or ctype in ("1", "3", "4", "5", "STOP")
                    or (ctype == "CHANGE_COLOR" and color == "")
                ):
                    placement_color, placement_type = update_placement(name, placement_color, placement_type)
                continue

            # --- other players' plays / selected_ events update placement ---
            if (
                name.startswith("selected_")
                or re.match(r"^p_\d+_(card|stop|change_color)", name)
            ):
                placement_color, placement_type = update_placement(name, placement_color, placement_type)
                continue

    return choice_points


def main():
    args = sys.argv[1:]
    player = 1
    if args and args[0] in ("0", "1"):
        player = int(args[0])
        args = args[1:]

    files = args or sorted(glob.glob("taki_game_*.log"))
    total = {"regular": 0, "stop": 0, "other": 0}
    print(f"Tracking player {player}")
    for path in files:
        cps = analyze(path, player=player)
        print(f"\n=== {path} ===")
        if not cps:
            print("  (no choice points found)")
        for cp in cps:
            print(
                f"  line {cp['line']:5d}: placement={cp['placement']:12s} "
                f"color={cp['color']:6s} stop_in_hand={cp['stop_count']} "
                f"regulars_in_hand={cp['regular_cards']} -> played {cp['played']} "
                f"[{cp['outcome']}]"
            )
            if cp["outcome"] == "regular":
                total["regular"] += 1
            elif cp["outcome"] == "stop":
                total["stop"] += 1
            else:
                total["other"] += 1

    print("\n=== TOTALS across all files ===")
    print(total)


if __name__ == "__main__":
    main()
