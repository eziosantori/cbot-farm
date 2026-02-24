import csv
import json
import tempfile
import unittest
from pathlib import Path

from api.simulations import SimulationService


class SimulationServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        root = Path(self._tmp.name)
        self.reports_root = root / "reports"
        self.data_root = root / "data" / "dukascopy"
        (self.data_root / "forex" / "eurusd" / "1h" / "download").mkdir(parents=True, exist_ok=True)

        csv_path = self.data_root / "forex" / "eurusd" / "1h" / "download" / "eurusd-h1-bid-2024-01-01-2024-01-10.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["timestamp", "open", "high", "low", "close"])
            writer.writeheader()
            price = 1.10
            for i in range(200):
                ts = 1704067200 + i * 3600
                drift = 0.0002 if i % 3 else -0.0001
                price = max(0.9, price + drift)
                writer.writerow(
                    {
                        "timestamp": ts,
                        "open": f"{price:.6f}",
                        "high": f"{price + 0.0008:.6f}",
                        "low": f"{price - 0.0008:.6f}",
                        "close": f"{price + 0.0001:.6f}",
                    }
                )

        self.universe = {
            "markets": {
                "forex": {
                    "symbols": ["EURUSD"],
                    "timeframes": ["1h"],
                }
            }
        }
        self.risk = {
            "optimization": {
                "min_sharpe": 1.2,
                "max_oos_degradation_pct": 30.0,
            },
            "risk_limits": {
                "strategy_max_drawdown_pct": 12.0,
            },
            "execution": {
                "default": {
                    "fee_bps_per_side": 0.0,
                    "slippage_bps_per_side": 0.0,
                },
                "market_costs": {},
            },
        }

        self.service = SimulationService(
            reports_root=self.reports_root,
            data_root=self.data_root,
            universe_cfg=self.universe,
            risk_cfg=self.risk,
        )

    def test_options_contains_markets_and_strategies(self) -> None:
        out = self.service.options()
        self.assertIn("ema_cross_atr", out["strategies"])
        self.assertIn("forex", out["markets"])

    def test_run_creates_report(self) -> None:
        out = self.service.run(
            {
                "strategy_id": "ema_cross_atr",
                "market": "forex",
                "symbol": "EURUSD",
                "timeframe": "1h",
                "params": {
                    "ema_fast": 20,
                    "ema_slow": 50,
                    "rsi_gate": 55,
                    "atr_vol_ratio_max": 1.8,
                },
            }
        )

        self.assertTrue(out["run_id"].startswith("run_"))
        report_path = self.reports_root.parent / Path(out["report_path"])
        self.assertTrue(report_path.exists())

        payload = json.loads(report_path.read_text())
        self.assertEqual(payload["strategy_id"], "ema_cross_atr")
        self.assertEqual(payload["market"], "forex")
        self.assertEqual(payload["symbol"], "EURUSD")
        self.assertEqual(payload["timeframes"], ["1h"])


if __name__ == "__main__":
    unittest.main()
