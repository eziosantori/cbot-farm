import unittest
from pathlib import Path

from cbot_farm.report_schema import (
    CURRENT_INGEST_MANIFEST_SCHEMA_VERSION,
    CURRENT_RUN_REPORT_SCHEMA_VERSION,
    INGEST_MANIFEST_KIND,
    RUN_REPORT_KIND,
    migrate_ingest_manifest,
    migrate_report_payload,
    migrate_run_report,
)


class ReportSchemaTestCase(unittest.TestCase):
    def test_migrate_legacy_run_report(self) -> None:
        legacy = {
            "strategy": {"name": "EMA Cross", "strategy_id": "ema_cross_atr"},
            "target": {"market": "forex", "symbol": "EURUSD", "timeframe": "1h"},
            "backtest": {
                "status": "ok",
                "metrics": {"total_return_pct": 1.5, "sharpe": 1.2},
            },
        }

        migrated = migrate_run_report(legacy)
        self.assertEqual(migrated["schema_version"], CURRENT_RUN_REPORT_SCHEMA_VERSION)
        self.assertEqual(migrated["report_kind"], RUN_REPORT_KIND)
        self.assertEqual(migrated["strategy_id"], "ema_cross_atr")
        self.assertEqual(migrated["strategy"], "EMA Cross")
        self.assertEqual(migrated["market"], "forex")
        self.assertEqual(migrated["symbol"], "EURUSD")
        self.assertEqual(migrated["timeframes"], ["1h"])
        self.assertEqual(migrated["metrics"]["sharpe"], 1.2)
        self.assertEqual(migrated["status"], "ok")

    def test_migrate_legacy_ingest_manifest(self) -> None:
        legacy = {
            "provider": "dukascopy-node",
            "results": [{"status": "ok"}, {"status": "failed"}],
        }

        migrated = migrate_ingest_manifest(legacy)
        self.assertEqual(migrated["schema_version"], CURRENT_INGEST_MANIFEST_SCHEMA_VERSION)
        self.assertEqual(migrated["report_kind"], INGEST_MANIFEST_KIND)
        self.assertEqual(migrated["summary"]["total"], 2)
        self.assertEqual(migrated["summary"]["ok"], 1)
        self.assertEqual(migrated["summary"]["failed"], 1)
        self.assertEqual(migrated["filters"]["markets"], [])

    def test_migrate_report_payload_by_path(self) -> None:
        run_payload = migrate_report_payload({"metrics": {}}, path=Path("run_20260317_1.json"))
        manifest_payload = migrate_report_payload({"provider": "dukascopy-node", "results": []}, path=Path("manifest_1.json"))
        self.assertEqual(run_payload["report_kind"], RUN_REPORT_KIND)
        self.assertEqual(manifest_payload["report_kind"], INGEST_MANIFEST_KIND)


if __name__ == "__main__":
    unittest.main()
