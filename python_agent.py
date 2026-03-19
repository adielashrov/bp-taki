class PythonAgent:
    def __init__(self):
        self.last_observation = None

    def reset(self, initial_observation=None):
        self.last_observation = initial_observation

    def _extract_card_color_and_type(self, event_name):
        card_str_index = event_name.find("card")
        if card_str_index != -1:
            card_color = event_name[card_str_index + 7:]
            card_number = event_name[card_str_index + 5:card_str_index + 6]
            return card_color, card_number

        stop_str_index = event_name.find("stop")
        if stop_str_index != -1:
            card_color = event_name[stop_str_index + 5:]
            return card_color, "STOP"

        if "change_color" in event_name and "selected_" not in event_name:
            return "", "CHANGE_COLOR"

        if "selected_" in event_name:
            for color in ("red", "blue", "green"):
                if color in event_name:
                    return color, "CHANGE_COLOR"
            return None, None

        if "super_taki" in event_name:
            return None, "SUPER_TAKI"

        if "taki_" in event_name:
            parts = event_name.split("_")
            color = parts[-1]
            if color in ("red", "blue", "green"):
                return color, "TAKI"

        return None, None

    def _is_legal_action(self, action_name, observation):
        phase = observation.get("phase")
        top_card = observation.get("top_card")
        active_color = observation.get("active_color")
        rule_mode = observation.get("rule_mode")
        taki_color = observation.get("taki_color")

        if phase == "change_color":
            return action_name.startswith("selected_")

        if phase == "taki_sequence":
            if action_name.endswith("_closed_taki"):
                return True
            if "draw_card" in action_name or "change_color" in action_name:
                return False
            if "super_taki" in action_name:
                return True
            action_color, _ = self._extract_card_color_and_type(action_name)
            return action_color is not None and action_color == taki_color

        if "draw_card" in action_name:
            return True
        if "change_color" in action_name or "super_taki" in action_name:
            return True
        if action_name.endswith("_closed_taki"):
            return False

        if rule_mode == "color_only":
            action_color, _ = self._extract_card_color_and_type(action_name)
            return action_color is not None and action_color == active_color

        top_color, top_type = self._extract_card_color_and_type(top_card or "")
        action_color, action_type = self._extract_card_color_and_type(action_name)

        if top_type == "TAKI" and action_type == "TAKI":
            return True

        return (
            (action_color is not None and action_color == top_color)
            or (action_type is not None and action_type == top_type)
        )

    def get_action(self, observation):
        self.last_observation = observation
        candidate_actions = observation.get("candidate_actions", [])
        if not candidate_actions:
            return None

        for action_name in candidate_actions:
            if self._is_legal_action(action_name, observation):
                return action_name

        return None
