import unittest

from bots.momentum_rider import MomentumRiderBot


class MomentumRiderBotTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = MomentumRiderBot()

    def test_normalize_params_clamps_ranges_and_order(self) -> None:
        normalized = self.bot.normalize_params(
            {
                "ema_fast": 200,
                "ema_slow": 10,
                "macd_fast": 30,
                "macd_slow": 8,
                "macd_signal": 1,
                "rsi_period": 1,
                "rsi_gate": 90,
                "atr_period": 1,
                "atr_mult_stop": 0.1,
                "atr_mult_take": 0.2,
            },
            bars_count=180,
        )

        self.assertLess(normalized["ema_fast"], normalized["ema_slow"])
        self.assertLess(normalized["macd_fast"], normalized["macd_slow"])
        self.assertGreaterEqual(normalized["macd_signal"], 3)
        self.assertGreaterEqual(normalized["rsi_period"], 2)
        self.assertGreaterEqual(normalized["atr_period"], 5)
        self.assertLessEqual(normalized["rsi_gate"], 65)
        self.assertGreaterEqual(normalized["atr_mult_stop"], 0.5)
        self.assertGreaterEqual(normalized["atr_mult_take"], 0.5)

    def test_entry_signal_requires_trend_macd_cross_and_rsi(self) -> None:
        bars = [{"close": 90.0}, {"close": 100.0}, {"close": 101.0}]
        indicators = {
            "ema_fast": [80.0, 95.0, 96.0],
            "ema_slow": [75.0, 90.0, 92.0],
            "macd_line": [-0.2, -0.1, 0.3],
            "macd_signal": [-0.1, 0.0, 0.1],
            "macd_hist": [-0.1, 0.2, 0.2],
            "rsi": [None, 56.0, 60.0],
            "atr": [None, 1.2, 1.1],
            "entry_filters": {"rsi_gate": 55},
        }

        self.assertEqual(self.bot.entry_signal(2, bars, indicators), 1)

        fail_rsi = dict(indicators)
        fail_rsi["rsi"] = [None, 50.0, 60.0]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_rsi), 0)

        fail_trend = dict(indicators)
        fail_trend["ema_fast"] = [80.0, 101.0, 96.0]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_trend), 0)


if __name__ == "__main__":
    unittest.main()
