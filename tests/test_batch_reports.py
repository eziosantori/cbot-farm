import json
import tempfile
import unittest
from pathlib import Path

from api.batch_reports import BatchReportService


class BatchReportServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.reports_root = Path(self._tmp.name) / "reports"
        self.reports_root.mkdir(parents=True, exist_ok=True)

        batch_dir = self.reports_root / "batch_demo_001"
        (batch_dir / "EURUSD_1h").mkdir(parents=True, exist_ok=True)

        run_payload = {
            "strategy_id": "ema_cross_atr",
            "backtest": {
                "trade_log": [
                    {"net_pnl_pct": 1.0},
                    {"net_pnl_pct": -0.5},
                    {"net_pnl_pct": 2.0},
                ]
            },
        }
        run_path = batch_dir / "EURUSD_1h" / "run_20260220_101055_60.json"
        run_path.write_text(json.dumps(run_payload), encoding="utf-8")

        summary = {
            "batch_id": "batch_demo_001",
            "created_at": "2026-02-20T10:10:45Z",
            "strategy": "ema_cross_atr",
            "max_retries": 200,
            "scenarios": [
                {
                    "name": "EURUSD_1h",
                    "reports": 100,
                    "promoted_count": 0,
                    "best": {
                        "report": "reports/batch_demo_001/EURUSD_1h/run_20260220_101055_60.json",
                        "metrics": {
                            "total_return_pct": 2.38,
                            "max_drawdown_pct": 1.69,
                            "sharpe": 0.51,
                            "oos_degradation_pct": 70.76,
                        },
                    },
                }
            ],
        }
        (batch_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

        self.service = BatchReportService(reports_root=self.reports_root)

    def test_list_batches(self) -> None:
        out = self.service.list_batches(limit=10, offset=0)
        self.assertEqual(out["total"], 1)
        item = out["items"][0]
        self.assertEqual(item["batch_id"], "batch_demo_001")
        self.assertEqual(item["scenarios"], 1)
        self.assertEqual(item["total_reports"], 100)

    def test_get_batch_enriches_best_run(self) -> None:
        out = self.service.get_batch("batch_demo_001")
        self.assertEqual(out["batch_id"], "batch_demo_001")
        self.assertEqual(len(out["scenarios"]), 1)

        scenario = out["scenarios"][0]
        self.assertEqual(scenario["best_run_id"], "20260220_101055_60")
        self.assertEqual(scenario["best_trades_count"], 3)
        self.assertGreaterEqual(len(scenario["best_equity_curve"]), 2)


if __name__ == "__main__":
    unittest.main()
