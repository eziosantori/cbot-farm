import unittest

from bots.ema_cross_atr import EmaCrossAtrBot


class EmaCrossAtrBotTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = EmaCrossAtrBot()

    def test_normalize_params_clamps_expected_ranges(self) -> None:
        normalized = self.bot.normalize_params(
            {
                "ema_fast": 100,
                "ema_slow": 3,
                "atr_period": 1,
                "atr_mult_stop": 0.1,
                "atr_mult_take": 0.2,
                "rsi_period": 1,
                "rsi_gate": 80,
                "atr_vol_window": 1,
                "atr_vol_ratio_max": 0.5,
            },
            bars_count=120,
        )

        self.assertLess(normalized["ema_fast"], normalized["ema_slow"])
        self.assertGreaterEqual(normalized["atr_period"], 5)
        self.assertGreaterEqual(normalized["rsi_period"], 2)
        self.assertGreaterEqual(normalized["atr_mult_stop"], 0.5)
        self.assertGreaterEqual(normalized["atr_mult_take"], 0.5)
        self.assertLessEqual(normalized["rsi_gate"], 60)
        self.assertGreaterEqual(normalized["rsi_gate"], 40)
        self.assertGreaterEqual(normalized["atr_vol_window"], 5)
        self.assertGreaterEqual(normalized["atr_vol_ratio_max"], 1.0)

    def test_entry_signal_requires_rsi_and_volatility_filters(self) -> None:
        bars = [{"close": 1.0}, {"close": 1.0}, {"close": 1.0}]

        base = {
            "ema_fast": [1.0, 1.0, 3.0],
            "ema_slow": [2.0, 2.0, 2.0],
            "rsi": [None, 45.0, 55.0],
            "atr": [None, 1.0, 1.5],
            "atr_avg": [None, 1.0, 1.0],
            "entry_filters": {"rsi_gate": 50, "atr_vol_ratio_max": 2.0},
        }

        # Fails RSI filter for long signal.
        self.assertEqual(self.bot.entry_signal(2, bars, base), 0)

        # Pass RSI but fail volatility filter.
        fail_vol = dict(base)
        fail_vol["rsi"] = [None, 55.0, 55.0]
        fail_vol["atr"] = [None, 2.5, 1.5]
        self.assertEqual(self.bot.entry_signal(2, bars, fail_vol), 0)

        # Pass both filters.
        pass_all = dict(base)
        pass_all["rsi"] = [None, 55.0, 55.0]
        pass_all["atr"] = [None, 1.5, 1.5]
        self.assertEqual(self.bot.entry_signal(2, bars, pass_all), 1)


if __name__ == "__main__":
    unittest.main()
