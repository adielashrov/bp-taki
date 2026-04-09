import unittest

from taki_simulation import (
    build_game_schedule,
    SimulationListener,
    create_simulation_bprogram_basic_vs_external,
    run_single_game_basic_vs_external,
)


class TestTakiVsExternalStrategyRegression(unittest.TestCase):
    HISTORICAL_DEADLOCK_SEEDS = [
        4, 5, 7, 35, 38, 54, 61, 76, 83, 92, 102, 105, 112, 135, 137, 179,
        188, 200, 202, 205, 206, 211, 215, 240, 242, 244, 252, 258, 262, 265,
        293, 301, 303, 306, 316, 320, 322, 323, 334, 343, 347, 352, 356, 366,
        378, 394, 406, 409, 413, 419, 420, 421, 430, 439, 444, 456, 499,
    ]

    def test_historical_taki_vs_external_deadlock_seeds_complete(self):
        schedule = build_game_schedule(
            num_games=500,
            start_seed=0,
            starting_player=-1,
            balanced_starting_players=True,
            mirrored_starting_players=False,
        )
        seed_to_start = {seed: starter for seed, starter in schedule}

        for seed in self.HISTORICAL_DEADLOCK_SEEDS:
            with self.subTest(seed=seed):
                result = run_single_game_basic_vs_external(
                    game_number=seed + 1,
                    seed=seed,
                    player_0_strategy="taki",
                    starting_player=seed_to_start[seed],
                    silent=True,
                )
                self.assertIsNotNone(result)
                self.assertFalse(result.ended_in_deadlock)
                self.assertFalse(result.ended_in_draw)

    def test_mirrored_seed_3_starting_player_0_completes_without_premature_next_turn(self):
        result = run_single_game_basic_vs_external(
            game_number=7,
            seed=3,
            player_0_strategy="taki",
            starting_player=0,
            silent=True,
        )
        self.assertIsNotNone(result)
        self.assertFalse(result.ended_in_deadlock)
        self.assertFalse(result.ended_in_draw)

        listener = SimulationListener()
        b_program, actual_starting_player = create_simulation_bprogram_basic_vs_external(
            seed=3,
            listener=listener,
            starting_player=0,
            player_0_strategy="taki",
        )
        self.assertEqual(actual_starting_player, 0)

        try:
            b_program.run()
        except AssertionError:
            if not listener.get_deadlock():
                raise

        self.assertFalse(listener.get_deadlock())

        taki_open = False
        for event_name in listener.events:
            if event_name == "p_0_super_taki" or event_name.startswith("p_0_taki_"):
                taki_open = True
            elif event_name == "p_0_closed_taki":
                taki_open = False
            elif event_name == "next_turn" and taki_open:
                self.fail("next_turn occurred before p_0_closed_taki during Player 0 TAKI sequence")
