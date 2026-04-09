import re
import logging
from typing import Any, Dict, Optional, Union

from bppy.model.b_priority_event import BPEvent

_COLORS = ["red", "blue", "green"]
_logger = logging.getLogger("TakiGame")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _is_selected_color_event(event: BPEvent) -> bool:
    return event.name.startswith("selected_")


def _is_taki_card_event(event: BPEvent) -> bool:
    return re.match(r"^p_\d+_taki_(red|blue|green)$", event.name) is not None


def _is_super_taki_event(event: BPEvent) -> bool:
    return re.match(r"^p_\d+_super_taki$", event.name) is not None


def _is_any_taki_event(event: BPEvent) -> bool:
    return _is_taki_card_event(event) or _is_super_taki_event(event)


def _is_regular_card_event(event: BPEvent) -> bool:
    return re.match(r"^p_\d+_card_\d+_\w+$", event.name) is not None


def _is_action_card_event(event: BPEvent) -> bool:
    return re.match(r"p_\d+_(change_color|plus_2_\w+|stop_\w+|taki_\w+|super_taki)", event.name) is not None


def _is_stop_card_event(event: BPEvent) -> bool:
    return re.match(r"p_\d+_stop_\w+", event.name) is not None


def _is_change_color_event(event: BPEvent) -> bool:
    return "change_color" in event.name


def _is_external_hand_card_event(event: BPEvent) -> bool:
    return _is_regular_card_event(event) or _is_action_card_event(event)


def _is_deal_card_event(event: BPEvent) -> bool:
    return event.name.startswith("deal_p_")


def _deal_target_player_id(event: BPEvent) -> Optional[int]:
    match = re.match(r"^deal_cards_to_player_(\d+)$", event.name)
    return int(match.group(1)) if match else None


def _played_card_owner(event: BPEvent) -> Optional[int]:
    match = re.match(r"^p_(\d+)_", event.name)
    return int(match.group(1)) if match else None


def _extract_card_color_and_type(event: BPEvent) -> Union[tuple, tuple]:
    card_str_index = event.name.find("card")
    if card_str_index != -1:
        return event.name[card_str_index + 7:], event.name[card_str_index + 5:card_str_index + 6]

    stop_str_index = event.name.find("stop")
    if stop_str_index != -1:
        return event.name[stop_str_index + 5:], "STOP"

    if "change_color" in event.name and "selected_" not in event.name:
        return "", "CHANGE_COLOR"

    if "selected_" in event.name:
        color = next((c for c in _COLORS if c in event.name), None)
        if color:
            return color, "CHANGE_COLOR"
        error_msg = (
            f"Invalid color selection in event '{event.name}'. "
            f"Expected 'selected_{{color}}' where color is one of {_COLORS}, "
            f"but extracted color was '{color}'"
        )
        _logger.error(error_msg)
        raise ValueError(error_msg)

    if "super_taki" in event.name:
        return None, "SUPER_TAKI"

    if "taki_" in event.name:
        color = event.name.split("_")[-1]
        if color in _COLORS:
            return color, "TAKI"

    return None, None


def _card_event_name_to_descriptor(event_name: Optional[str]) -> Optional[str]:
    if event_name is None:
        return None
    name = re.sub(r"^(deal_|leading_)+", "", event_name)
    name = re.sub(r"^p_\d+_", "", name)
    if name.startswith("p_"):
        name = name[2:]
    return name


def _update_top_card_fields(
    state: Dict[str, Any],
    event_name: Optional[str],
    color: Optional[str],
    card_type: Optional[str],
) -> None:
    state["top_card"] = event_name
    state["top_card_color"] = color
    state["top_card_type"] = card_type


def _update_opponent_card_count(state: Dict[str, Any], num_of_players: int) -> None:
    if num_of_players == 2:
        player_index = state["player_index"]
        opponent_index = 1 - player_index
        state["opponent_card_count"] = state["hand_counts"].get(opponent_index, 0)
    else:
        state["opponent_card_count"] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_external_bridge_state(index: int, starting_player: int, num_of_players: int) -> Dict[str, Any]:
    return {
        "player_index": index,
        "current_player": starting_player,
        "next_player": (starting_player + 1) % num_of_players,
        "top_card": None,
        "top_card_color": None,
        "top_card_type": None,
        "active_color": None,
        "match_color": None,
        "match_type": None,
        "rule_mode": "match_color_or_type",
        "taki_color": None,
        "taki_last_event": None,
        "taki_last_color": None,
        "taki_last_type": None,
        "pending_deal_player": None,
        "hand_counts": {player: 0 for player in range(num_of_players)},
        "opponent_card_count": 0 if num_of_players == 2 else None,
    }


def update_external_bridge_state_from_event(state: Dict[str, Any], event: BPEvent, num_of_players: int) -> None:
    pending_deal_player = state.get("pending_deal_player")

    deal_target_player = _deal_target_player_id(event)
    if deal_target_player is not None:
        state["pending_deal_player"] = deal_target_player
        return

    if _is_deal_card_event(event):
        if pending_deal_player is not None:
            state["hand_counts"][pending_deal_player] = state["hand_counts"].get(pending_deal_player, 0) + 1
            _update_opponent_card_count(state, num_of_players)
        state["pending_deal_player"] = None
        return

    if event.name == "next_turn":
        state["current_player"] = state["next_player"]
        state["next_player"] = (state["next_player"] + 1) % num_of_players
        return

    if (
        state["rule_mode"] != "taki"
        and event.name.startswith(f"p_{state['current_player']}_stop")
    ):
        state["next_player"] = (state["next_player"] + 1) % num_of_players

    if event.name.startswith("leading_"):
        card_color, card_type = _extract_card_color_and_type(event)
        _update_top_card_fields(state, event.name, card_color, card_type)
        state["active_color"] = card_color
        state["match_color"] = card_color
        state["match_type"] = card_type
        state["rule_mode"] = "match_color_or_type"
        state["taki_color"] = None
        state["taki_last_event"] = None
        state["taki_last_color"] = None
        state["taki_last_type"] = None
        return

    if _is_selected_color_event(event):
        selected_color, _ = _extract_card_color_and_type(event)
        _update_top_card_fields(state, event.name, selected_color, "CHANGE_COLOR")
        state["active_color"] = selected_color
        state["match_color"] = selected_color
        state["match_type"] = "CHANGE_COLOR"
        state["rule_mode"] = "color_only"
        return

    if _is_any_taki_event(event):
        state["rule_mode"] = "taki"
        if _is_taki_card_event(event):
            taki_color, taki_type = _extract_card_color_and_type(event)
        else:
            taki_color = state["active_color"]
            taki_type = "SUPER_TAKI"
        _update_top_card_fields(state, event.name, taki_color, taki_type)
        state["active_color"] = taki_color
        state["taki_color"] = taki_color
        state["taki_last_event"] = event.name
        state["taki_last_color"] = taki_color
        state["taki_last_type"] = taki_type
        owner = _played_card_owner(event)
        if owner is not None:
            state["hand_counts"][owner] = max(0, state["hand_counts"].get(owner, 0) - 1)
            _update_opponent_card_count(state, num_of_players)
        return

    if event.name.endswith("_closed_taki"):
        return

    if event.name == "done_post_action":
        if state["rule_mode"] == "taki":
            state["rule_mode"] = "match_color_or_type"
            state["match_color"] = state["taki_last_color"]
            state["match_type"] = state["taki_last_type"]
            state["active_color"] = state["match_color"]
            if state["taki_last_event"] is not None:
                _update_top_card_fields(
                    state,
                    state["taki_last_event"],
                    state["taki_last_color"],
                    state["taki_last_type"],
                )
            state["taki_color"] = None
            state["taki_last_event"] = None
            state["taki_last_color"] = None
            state["taki_last_type"] = None
        return

    if _is_regular_card_event(event) or _is_stop_card_event(event):
        card_color, card_type = _extract_card_color_and_type(event)
        _update_top_card_fields(state, event.name, card_color, card_type)
        state["active_color"] = card_color
        if state["rule_mode"] == "taki":
            state["taki_last_event"] = event.name
            state["taki_last_color"] = card_color
            state["taki_last_type"] = card_type
        else:
            state["match_color"] = card_color
            state["match_type"] = card_type
            state["rule_mode"] = "match_color_or_type"
        owner = _played_card_owner(event)
        if owner is not None:
            state["hand_counts"][owner] = max(0, state["hand_counts"].get(owner, 0) - 1)
            _update_opponent_card_count(state, num_of_players)
        return

    if _is_change_color_event(event):
        _update_top_card_fields(state, event.name, state["active_color"], "CHANGE_COLOR")
        if state["rule_mode"] == "taki":
            state["taki_last_event"] = event.name
            state["taki_last_color"] = state["active_color"]
            state["taki_last_type"] = "CHANGE_COLOR"
        owner = _played_card_owner(event)
        if owner is not None:
            state["hand_counts"][owner] = max(0, state["hand_counts"].get(owner, 0) - 1)
            _update_opponent_card_count(state, num_of_players)
        return

    if event.name.endswith("_no_more_cards"):
        owner = _played_card_owner(event)
        if owner is not None:
            state["hand_counts"][owner] = 0
            _update_opponent_card_count(state, num_of_players)
        return


def build_external_observation(
    index: int,
    phase: str,
    candidate_events: list,
    state: Dict[str, Any],
) -> Dict[str, str]:
    hand = ",".join(
        _card_event_name_to_descriptor(event.name)
        for event in candidate_events
        if _is_external_hand_card_event(event)
    )
    return {
        "player_index": str(index),
        "phase":         phase,
        "hand":          hand,
        "top_card":      _card_event_name_to_descriptor(state.get("top_card")) or "",
        "top_card_color": state.get("top_card_color") or "",
        "top_card_type": state.get("top_card_type") or "",
        "active_color":  state.get("active_color") or "",
        "rule_mode":     state.get("rule_mode") or "",
        "taki_color":    state.get("taki_color") or "",
        "opponent_card_count": str(state.get("opponent_card_count", "")),
    }
