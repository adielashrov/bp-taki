import unittest

from bppy.model.b_priority_event import BPEvent

from bp_taki import (
    init_external_bridge_state,
    update_external_bridge_state_from_event,
)


class TestExternalBridgeState(unittest.TestCase):

    def _make_state(self, index=1, starting_player=0, num_of_players=2):
        return init_external_bridge_state(index=index, starting_player=starting_player, num_of_players=num_of_players)

    # ------------------------------------------------------------------
    # init_external_bridge_state
    # ------------------------------------------------------------------

    def test_init_state(self):
        state = self._make_state(index=1, starting_player=0, num_of_players=2)
        self.assertEqual(state["player_index"], 1)
        self.assertEqual(state["current_player"], 0)
        self.assertEqual(state["next_player"], 1)
        self.assertIsNone(state["top_card"])
        self.assertIsNone(state["active_color"])
        self.assertIsNone(state["match_color"])
        self.assertIsNone(state["match_type"])
        self.assertEqual(state["rule_mode"], "color_or_type")
        self.assertIsNone(state["taki_color"])
        self.assertIsNone(state["taki_last_event"])
        self.assertIsNone(state["taki_last_color"])
        self.assertIsNone(state["taki_last_type"])

    # ------------------------------------------------------------------
    # leading card
    # ------------------------------------------------------------------

    def test_leading_card_sets_match_state(self):
        state = self._make_state()
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 2)
        self.assertEqual(state["top_card"], "leading_deal_p_card_3_red")
        self.assertEqual(state["active_color"], "red")
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "3")
        self.assertEqual(state["rule_mode"], "color_or_type")
        self.assertIsNone(state["taki_color"])

    # ------------------------------------------------------------------
    # next_turn
    # ------------------------------------------------------------------

    def test_next_turn_advances_current_player(self):
        state = self._make_state(starting_player=0, num_of_players=2)
        update_external_bridge_state_from_event(state, BPEvent("next_turn"), 2)
        self.assertEqual(state["current_player"], 1)
        self.assertEqual(state["next_player"], 0)

    def test_next_turn_wraps_around(self):
        state = self._make_state(index=0, starting_player=1, num_of_players=2)
        update_external_bridge_state_from_event(state, BPEvent("next_turn"), 2)
        self.assertEqual(state["current_player"], 0)
        self.assertEqual(state["next_player"], 1)

    # ------------------------------------------------------------------
    # regular card play
    # ------------------------------------------------------------------

    def test_regular_card_updates_match_state(self):
        state = self._make_state()
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 2)
        update_external_bridge_state_from_event(state, BPEvent("p_0_card_5_blue"), 2)
        self.assertEqual(state["top_card"], "p_0_card_5_blue")
        self.assertEqual(state["active_color"], "blue")
        self.assertEqual(state["match_color"], "blue")
        self.assertEqual(state["match_type"], "5")
        self.assertEqual(state["rule_mode"], "color_or_type")

    # ------------------------------------------------------------------
    # stop card
    # ------------------------------------------------------------------

    def test_opponent_stop_sequence(self):
        """
        When the opponent plays STOP while the external player is observing events
        via `waitFor=bp.All()`, the bridge should:
        1. Update placement matching based on the STOP card itself.
        2. Ignore `done_post_action` for placement purposes.
        3. Apply the skip effect only when `next_turn` arrives.
        """
        state = self._make_state(index=1, starting_player=0, num_of_players=2)

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

    # ------------------------------------------------------------------
    # change_color card
    # ------------------------------------------------------------------

    def test_change_color_then_selected_color(self):
        state = self._make_state()
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 2)
        update_external_bridge_state_from_event(state, BPEvent("p_0_change_color"), 2)
        self.assertEqual(state["top_card"], "p_0_change_color")
        # rule_mode should not change until color is selected
        self.assertEqual(state["rule_mode"], "color_or_type")

        update_external_bridge_state_from_event(state, BPEvent("selected_blue"), 2)
        self.assertEqual(state["top_card"], "selected_blue")
        self.assertEqual(state["active_color"], "blue")
        self.assertEqual(state["match_color"], "blue")
        self.assertEqual(state["match_type"], "CHANGE_COLOR")
        self.assertEqual(state["rule_mode"], "color_only")

    # ------------------------------------------------------------------
    # TAKI sequence
    # ------------------------------------------------------------------

    def test_taki_sequence_with_cards_then_close(self):
        state = self._make_state()
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 2)

        # Player 0 plays TAKI red
        update_external_bridge_state_from_event(state, BPEvent("p_0_taki_red"), 2)
        self.assertEqual(state["top_card"], "p_0_taki_red")
        self.assertEqual(state["rule_mode"], "taki")
        self.assertEqual(state["taki_color"], "red")
        self.assertEqual(state["active_color"], "red")

        # Player 0 plays card_5_red inside the TAKI sequence
        update_external_bridge_state_from_event(state, BPEvent("p_0_card_5_red"), 2)
        self.assertEqual(state["top_card"], "p_0_card_5_red")
        self.assertEqual(state["rule_mode"], "taki")
        self.assertEqual(state["taki_last_event"], "p_0_card_5_red")
        self.assertEqual(state["taki_last_color"], "red")
        self.assertEqual(state["taki_last_type"], "5")
        # match_color/match_type should NOT be updated mid-sequence
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "3")

        # Player 0 closes the TAKI
        update_external_bridge_state_from_event(state, BPEvent("p_0_closed_taki"), 2)
        self.assertEqual(state["rule_mode"], "taki")  # not yet finalized

        # done_post_action finalizes the TAKI sequence
        update_external_bridge_state_from_event(state, BPEvent("done_post_action"), 2)
        self.assertEqual(state["rule_mode"], "color_or_type")
        self.assertEqual(state["match_color"], "red")
        self.assertEqual(state["match_type"], "5")
        self.assertEqual(state["top_card"], "p_0_card_5_red")
        self.assertIsNone(state["taki_color"])
        self.assertIsNone(state["taki_last_event"])
        self.assertIsNone(state["taki_last_color"])
        self.assertIsNone(state["taki_last_type"])

    def test_super_taki_sequence(self):
        state = self._make_state()
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_blue"), 2)

        update_external_bridge_state_from_event(state, BPEvent("p_0_super_taki"), 2)
        self.assertEqual(state["top_card"], "p_0_super_taki")
        self.assertEqual(state["rule_mode"], "taki")
        self.assertEqual(state["taki_last_type"], "SUPER_TAKI")
        # super_taki inherits the current active_color
        self.assertEqual(state["taki_color"], "blue")

    def test_done_post_action_no_op_outside_taki(self):
        state = self._make_state()
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 2)
        update_external_bridge_state_from_event(state, BPEvent("p_0_card_5_blue"), 2)
        update_external_bridge_state_from_event(state, BPEvent("done_post_action"), 2)
        # State should be unchanged
        self.assertEqual(state["match_color"], "blue")
        self.assertEqual(state["match_type"], "5")
        self.assertEqual(state["rule_mode"], "color_or_type")

    # ------------------------------------------------------------------
    # 3-player stop skip logic
    # ------------------------------------------------------------------

    def test_stop_skips_correct_player_in_3_player_game(self):
        state = self._make_state(index=2, starting_player=0, num_of_players=3)
        update_external_bridge_state_from_event(state, BPEvent("leading_deal_p_card_3_red"), 3)

        # Player 0 plays STOP — should skip player 1, making next_player = player 2
        update_external_bridge_state_from_event(state, BPEvent("p_0_stop_red"), 3)
        self.assertEqual(state["next_player"], 2)

        update_external_bridge_state_from_event(state, BPEvent("next_turn"), 3)
        self.assertEqual(state["current_player"], 2)
        self.assertEqual(state["next_player"], 0)


if __name__ == "__main__":
    unittest.main()
