import json
import tempfile
import time
import unittest
from pathlib import Path

from api.report_index import ReportIndexService


class ReportIndexServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.reports_root = Path(self._tmp.name) / "reports"
        self.reports_root.mkdir(parents=True, exist_ok=True)
        (self.reports_root / "ingest").mkdir(parents=True, exist_ok=True)

        run_1 = {
            "strategy": "S1",
            "strategy_id": "s1",
            "market": "forex",
            "symbol": "EURUSD",
            "timeframes": ["1h"],
            "status": "ok",
            "metrics": {
                "total_return_pct": 4.5,
                "sharpe": 1.3,
                "max_drawdown_pct": 7.2,
                "oos_degradation_pct": 22.0,
            },
        }
        (self.reports_root / "run_20260217_000001_1.json").write_text(json.dumps(run_1), encoding="utf-8")

        run_2 = {
            "strategy": {"name": "S2", "strategy_id": "s2"},
            "target": {"market": "indices", "symbol": "NAS100", "timeframe": "15m"},
            "backtest": {
                "status": "failed",
                "metrics": {
                    "total_return_pct": -2.0,
                    "sharpe": -0.5,
                    "max_drawdown_pct": 10.0,
                    "oos_degradation_pct": 100.0,
                },
            },
        }
        (self.reports_root / "run_20260217_000002_1.json").write_text(json.dumps(run_2), encoding="utf-8")

        manifest = {
            "created_at": "2026-02-17T00:00:00+00:00",
            "status": "ok",
            "results": [
                {"status": "ok"},
                {"status": "failed"},
            ],
        }
        (self.reports_root / "ingest" / "manifest_20260217_100000.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        self.index = ReportIndexService(
            reports_root=self.reports_root,
            db_path=self.reports_root / "index" / "reports.db",
        )

    def test_rebuild_and_status(self) -> None:
        summary = self.index.rebuild()
        self.assertEqual(summary["runs_indexed"], 2)
        self.assertEqual(summary["manifests_indexed"], 1)

        status = self.index.status()
        self.assertTrue(status["ready"])
        self.assertEqual(status["runs_count"], 2)
        self.assertEqual(status["manifests_count"], 1)
        self.assertFalse(status["stale"])

    def test_status_marks_stale_when_new_report_arrives(self) -> None:
        self.index.rebuild()
        time.sleep(1.1)

        run_3 = {
            "strategy": "S3",
            "strategy_id": "s3",
            "market": "forex",
            "timeframes": ["1h"],
            "status": "ok",
            "metrics": {"total_return_pct": 0.1, "max_drawdown_pct": 0.2, "sharpe": 0.3, "oos_degradation_pct": 40},
        }
        (self.reports_root / "run_20260217_000003_1.json").write_text(json.dumps(run_3), encoding="utf-8")

        status = self.index.status()
        self.assertTrue(status["stale"])
        self.assertIsNotNone(status["latest_source_updated_at"])

    def test_list_runs_filters(self) -> None:
        self.index.rebuild()

        all_runs = self.index.list_runs(limit=10, offset=0)
        self.assertEqual(all_runs["total"], 2)

        forex = self.index.list_runs(limit=10, offset=0, market="forex")
        self.assertEqual(forex["total"], 1)
        self.assertEqual(forex["items"][0]["strategy_id"], "s1")

        failed = self.index.list_runs(limit=10, offset=0, status="failed")
        self.assertEqual(failed["total"], 1)
        self.assertEqual(failed["items"][0]["strategy_id"], "s2")

    def test_list_ingest_manifests(self) -> None:
        self.index.rebuild()
        manifests = self.index.list_ingest_manifests(limit=10, offset=0)
        self.assertEqual(manifests["total"], 1)
        self.assertEqual(manifests["items"][0]["ok"], 1)
        self.assertEqual(manifests["items"][0]["failed"], 1)


if __name__ == "__main__":
    unittest.main()
