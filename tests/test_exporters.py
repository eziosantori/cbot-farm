import unittest

from cbot_farm.exporters import build_contract_from_strategy, evaluate_export_parity


class ExportersTestCase(unittest.TestCase):
    def test_export_parity_passes_for_supported_ema_cross_atr_contract(self) -> None:
        contract = build_contract_from_strategy(
            strategy_id="ema_cross_atr",
            params={
                "ema_fast": 20,
                "ema_slow": 50,
                "atr_period": 14,
                "atr_mult_stop": 1.5,
                "atr_mult_take": 2.0,
                "rsi_period": 14,
                "rsi_gate": 55,
                "atr_vol_window": 50,
                "atr_vol_ratio_max": 1.8,
            },
        )

        result = evaluate_export_parity(target="ctrader", contract=contract)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["missing_params"], [])
        self.assertEqual(result["unsupported_params"], [])
        self.assertTrue(all(item["pass"] for item in result["feature_checks"].values()))

    def test_export_parity_reports_missing_and_unsupported_params(self) -> None:
        contract = build_contract_from_strategy(
            strategy_id="ema_cross_atr",
            params={
                "ema_fast": 20,
                "ema_slow": 50,
                "unexpected_param": 123,
            },
        )

        result = evaluate_export_parity(target="pine", contract=contract)
        self.assertEqual(result["status"], "fail")
        self.assertIn("atr_period", result["missing_params"])
        self.assertIn("unexpected_param", result["unsupported_params"])

    def test_export_parity_blocks_unsupported_strategy(self) -> None:
        contract = build_contract_from_strategy(
            strategy_id="unsupported_bot",
            params={"foo": 1},
        )

        result = evaluate_export_parity(target="ctrader", contract=contract)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["diagnostics"])


if __name__ == "__main__":
    unittest.main()
