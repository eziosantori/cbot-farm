import json
import tempfile
import unittest
from pathlib import Path

from api.report_reader import ReportReader


class ReportReaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.reports_root = Path(self._tmp.name) / "reports"
        (self.reports_root / "ingest").mkdir(parents=True, exist_ok=True)

        run_payload = {
            "run_id": "20260217_000001_1",
            "strategy": "SuperTrend + RSI Momentum",
            "strategy_id": "supertrend_rsi",
            "market": "indices",
            "timeframes": ["1h"],
            "backtest": {"status": "ok"},
            "metrics": {"total_return_pct": 1.23},
        }
        (self.reports_root / "run_20260217_000001_1.json").write_text(json.dumps(run_payload))

        run_payload_target = {
            "strategy": {"name": "EMA", "strategy_id": "ema_cross_atr"},
            "target": {"market": "forex", "symbol": "EURUSD", "timeframe": "15m"},
            "status": "ok",
            "backtest": {"metrics": {"sharpe": 1.5}},
        }
        (self.reports_root / "run_20260217_000002_1.json").write_text(json.dumps(run_payload_target))

        manifest_payload = {
            "created_at": "2026-02-17T00:00:00+00:00",
            "status": "ok",
            "results": [
                {"market": "forex", "symbol": "EURUSD", "timeframe": "1h", "status": "ok"},
                {"market": "indices", "symbol": "NAS100", "timeframe": "1h", "status": "failed"},
            ],
        }
        (self.reports_root / "ingest" / "manifest_20260217_000001.json").write_text(json.dumps(manifest_payload))

        self.reader = ReportReader(reports_root=self.reports_root)

    def test_list_runs_and_filters(self) -> None:
        all_runs = self.reader.list_runs(limit=10, offset=0)
        self.assertEqual(all_runs["total"], 2)

        forex_runs = self.reader.list_runs(limit=10, offset=0, market="forex")
        self.assertEqual(forex_runs["total"], 1)
        self.assertEqual(forex_runs["items"][0]["strategy_id"], "ema_cross_atr")

    def test_get_run_supports_id_variants(self) -> None:
        by_stem = self.reader.get_run("run_20260217_000001_1")
        self.assertEqual(by_stem["run_id"], "run_20260217_000001_1")

        by_raw = self.reader.get_run("20260217_000001_1")
        self.assertEqual(by_raw["run_id"], "run_20260217_000001_1")

    def test_ingest_manifest_list_and_detail(self) -> None:
        manifests = self.reader.list_ingest_manifests(limit=10, offset=0)
        self.assertEqual(manifests["total"], 1)
        item = manifests["items"][0]
        self.assertEqual(item["ok"], 1)
        self.assertEqual(item["failed"], 1)

        detail_stem = self.reader.get_ingest_manifest("manifest_20260217_000001")
        self.assertEqual(detail_stem["manifest_id"], "manifest_20260217_000001")

        detail_raw = self.reader.get_ingest_manifest("20260217_000001")
        self.assertEqual(detail_raw["manifest_id"], "manifest_20260217_000001")


if __name__ == "__main__":
    unittest.main()
