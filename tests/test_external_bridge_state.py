import unittest

from bppy.model.b_priority_event import BPEvent

from bp_taki import (
    init_external_bridge_state,
    update_external_bridge_state_from_event,
)


class TestExternalBridgeState(unittest.TestCase):

    def test_opponent_stop_sequence(self):
        """
        When the opponent plays STOP while the external player is observing events
        via `waitFor=bp.All()`, the bridge should:
        1. Update placement matching based on the STOP card itself.
        2. Ignore `done_post_action` for placement purposes.
        3. Apply the skip effect only when `next_turn` arrives.
        """
        state = init_external_bridge_state(index=1, starting_player=0, num_of_players=2)

        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 2)
        self.assertEqual(state["current_player"], 0)
        self.assertEqual(state["next_player"], 1)
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "3")

        update_external_bridge_state_from_event(state, BPEvent("p_0_stop_red"), 2)
        self.assertEqual(state["current_player"], 0)
        self.assertEqual(state["next_player"], 0)
        self.assertEqual(state["top_card"], "p_0_stop_red")
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "STOP")
        self.assertEqual(state["rule_mode"], "color_or_type")

        update_external_bridge_state_from_event(state, BPEvent("done_post_action"), 2)
        self.assertEqual(state["current_player"], 0)
        self.assertEqual(state["next_player"], 0)
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "STOP")
        self.assertEqual(state["rule_mode"], "color_or_type")

        update_external_bridge_state_from_event(state, BPEvent("next_turn"), 2)
        self.assertEqual(state["current_player"], 0)
        self.assertEqual(state["next_player"], 1)
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "STOP")
