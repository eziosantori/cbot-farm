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
                "adx_period": 1,
                "min_adx": 90,
                "atr_period": 1,
                "atr_vol_window": 1,
                "atr_vol_ratio_max": 0.2,
                "atr_mult_stop": 0.1,
                "atr_mult_take": 0.2,
            },
            bars_count=180,
        )

        self.assertLess(normalized["ema_fast"], normalized["ema_slow"])
        self.assertLess(normalized["macd_fast"], normalized["macd_slow"])
        self.assertGreaterEqual(normalized["macd_signal"], 3)
        self.assertGreaterEqual(normalized["rsi_period"], 2)
        self.assertGreaterEqual(normalized["adx_period"], 5)
        self.assertLessEqual(normalized["min_adx"], 50)
        self.assertGreaterEqual(normalized["atr_period"], 5)
        self.assertGreaterEqual(normalized["atr_vol_window"], 5)
        self.assertGreaterEqual(normalized["atr_vol_ratio_max"], 1.0)
        self.assertLessEqual(normalized["rsi_gate"], 70)
        self.assertGreaterEqual(normalized["atr_mult_stop"], 0.5)
        self.assertGreaterEqual(normalized["atr_mult_take"], 0.5)

    def test_entry_signal_requires_trend_macd_cross_rsi_and_regime_filters(self) -> None:
        bars = [{"close": 90.0, "timestamp": 0}, {"close": 96.2, "timestamp": 1}, {"close": 97.0, "timestamp": 2}]
        indicators = {
            "ema_fast": [80.0, 95.0, 96.0],
            "ema_slow": [75.0, 90.0, 92.0],
            "macd_line": [-0.2, -0.1, 0.3],
            "macd_signal": [-0.1, 0.0, 0.1],
            "macd_hist": [-0.1, 0.2, 0.2],
            "rsi": [None, 56.0, 60.0],
            "adx": [None, 25.0, 27.0],
            "atr": [None, 1.2, 1.1],
            "atr_avg": [None, 1.0, 1.0],
            "entry_filters": {"rsi_gate": 55, "min_adx": 20, "atr_vol_ratio_max": 1.5},
        }

        self.assertEqual(self.bot.entry_signal(2, bars, indicators), 1)

        fail_rsi = dict(indicators)
        fail_rsi["rsi"] = [None, 50.0, 60.0]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_rsi), 0)

        fail_trend = dict(indicators)
        fail_trend["ema_fast"] = [80.0, 101.0, 96.0]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_trend), 0)

        fail_adx = dict(indicators)
        fail_adx["adx"] = [None, 15.0, 27.0]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_adx), 0)

        fail_volatility = dict(indicators)
        fail_volatility["atr"] = [None, 2.0, 1.1]
        fail_volatility["atr_avg"] = [None, 1.0, 1.0]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_volatility), 0)

    def test_entry_signal_requires_macd_zero_line_alignment(self) -> None:
        bars = [{"close": 110.0, "timestamp": 0}, {"close": 116.0, "timestamp": 1}, {"close": 117.0, "timestamp": 2}]
        indicators = {
            "ema_fast": [100.0, 115.0, 116.0],
            "ema_slow": [95.0, 110.0, 111.0],
            "macd_line": [-0.3, -0.05, 0.02],
            "macd_signal": [-0.2, 0.0, 0.01],
            "macd_hist": [-0.1, 0.02, 0.01],
            "rsi": [None, 60.0, 62.0],
            "adx": [None, 28.0, 29.0],
            "atr": [None, 1.1, 1.0],
            "atr_avg": [None, 1.0, 1.0],
            "entry_filters": {"rsi_gate": 55, "min_adx": 20, "atr_vol_ratio_max": 1.5},
        }

        self.assertEqual(self.bot.entry_signal(2, bars, indicators), 1)

        fail_zero_line = dict(indicators)
        fail_zero_line["macd_line"] = [-0.3, -0.2, -0.01]
        fail_zero_line["macd_signal"] = [-0.25, -0.15, -0.02]
        fail_zero_line["macd_hist"] = [-0.05, -0.05, 0.01]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_zero_line), 0)


if __name__ == "__main__":
    unittest.main()
