import unittest

from taki_simulation import run_single_game


class TestTakiStrategyPostAction(unittest.TestCase):
    HISTORICAL_FAILING_SEEDS = [
        136, 196, 209, 234, 240, 374, 470, 493, 536, 826, 842, 864, 878,
        915, 927, 1044, 1111, 1288, 1355, 1421, 1761, 2020, 2077, 2214,
        2327, 2336, 2518, 2585, 2599, 2728, 2786, 2812, 2821, 2860, 2875,
        2915, 2922, 2929, 3034, 3071, 3083, 3148, 3163, 3274, 3378, 3498,
        3593, 3608, 3699, 3700, 3706, 3881, 3912,
    ]

    def test_historical_taki_vs_basic_deadlock_seeds_complete(self):
        for seed in self.HISTORICAL_FAILING_SEEDS:
            with self.subTest(seed=seed):
                result = run_single_game(
                    game_number=seed + 1,
                    seed=seed,
                    player_0_strategy="taki",
                    player_1_strategy="basic",
                    starting_player=-1,
                    silent=True,
                )
                self.assertIsNotNone(result)
                self.assertFalse(result.ended_in_deadlock)
                self.assertFalse(result.ended_in_draw)
