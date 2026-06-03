import unittest

from taki_simulation import run_single_game, run_single_game_basic_vs_external, PlayerStrategyConfig


class TestLeadingCardFallback(unittest.TestCase):
    HISTORICAL_FAILING_SEEDS = [121, 693, 820, 1841, 2199, 2774, 4143, 4201, 4437, 4885]

    def assert_game_completed(self, result):
        self.assertIsNotNone(result)
        self.assertFalse(result.ended_in_deadlock)
        self.assertFalse(result.ended_in_draw)

    def test_historical_failing_seeds_complete_for_basic_vs_basic(self):
        for seed in self.HISTORICAL_FAILING_SEEDS:
            with self.subTest(seed=seed, mode="basic_vs_basic"):
                result = run_single_game(
                    game_number=seed,
                    seed=seed,
                    player_0_config=PlayerStrategyConfig(base_strategy="basic"),
                    player_1_config=PlayerStrategyConfig(base_strategy="basic"),
                    starting_player=-1,
                    silent=True,
                )
                self.assert_game_completed(result)

    def test_historical_failing_seeds_complete_for_basic_vs_external(self):
        for seed in self.HISTORICAL_FAILING_SEEDS:
            with self.subTest(seed=seed, mode="basic_vs_external"):
                result = run_single_game_basic_vs_external(
                    game_number=seed,
                    seed=seed,
                    player_0_config=PlayerStrategyConfig(base_strategy="basic"),
                    starting_player=-1,
                    silent=True,
                )
                self.assert_game_completed(result)
