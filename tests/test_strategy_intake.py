import tempfile
import unittest
from pathlib import Path

from api.strategy_intake import StrategyIntakeService


class StrategyIntakeServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        root = Path(self._tmp.name)
        self.service = StrategyIntakeService(
            storage_dir=root / "reports" / "strategy_intake",
            universe_cfg={
                "markets": {
                    "forex": {"symbols": ["EURUSD", "GBPUSD"], "timeframes": ["15m", "1h"]},
                    "indices": {"symbols": ["NAS100"], "timeframes": ["1h", "4h"]},
                }
            },
            risk_cfg={
                "risk_limits": {"strategy_max_drawdown_pct": 10.0},
                "optimization": {"min_sharpe": 1.1, "max_oos_degradation_pct": 25.0},
            },
        )

    def test_create_and_get_intake(self) -> None:
        created = self.service.create(
            {
                "title": "Session Momentum Breakout",
                "thesis": "Trade London session continuation after range compression.",
                "target_markets": ["forex", "indices"],
                "target_symbols": ["EURUSD", "NAS100"],
                "target_timeframes": ["1h"],
                "risk_gates": {"max_drawdown_pct": 8, "min_sharpe": 1.4, "max_oos_degradation_pct": 20},
            }
        )

        self.assertEqual(created["status"], "captured")
        self.assertEqual(created["title"], "Session Momentum Breakout")
        self.assertIn("implementation_prompt", created["prompts"])
        self.assertEqual(created["artifact_path"].split("/")[0], "reports")

        fetched = self.service.get_intake(created["intake_id"])
        self.assertEqual(fetched["intake_id"], created["intake_id"])
        self.assertEqual(fetched["target_universe"]["markets"], ["forex", "indices"])

        listing = self.service.list_intakes(limit=10, offset=0)
        self.assertEqual(listing["total"], 1)
        self.assertEqual(listing["items"][0]["intake_id"], created["intake_id"])

    def test_create_requires_core_fields(self) -> None:
        with self.assertRaises(ValueError):
            self.service.create(
                {
                    "title": "",
                    "thesis": "",
                    "target_markets": [],
                    "target_timeframes": [],
                }
            )

    def test_create_rejects_unknown_strategy(self) -> None:
        with self.assertRaises(ValueError):
            self.service.create(
                {
                    "title": "Bad Link",
                    "thesis": "Invalid linked strategy id",
                    "linked_strategy_id": "does_not_exist",
                    "target_markets": ["forex"],
                    "target_timeframes": ["1h"],
                }
            )


if __name__ == "__main__":
    unittest.main()
