import json
import tempfile
import unittest
from pathlib import Path

from api import main as api_main
from api.batch_reports import BatchReportService
from api.report_index import ReportIndexService
from api.report_reader import ReportReader
from api.strategy_intake import StrategyIntakeService
from api.strategy_workflow import StrategyWorkflowService
from cbot_farm.config import load_configs


class SmokeRoutesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.root = Path(self._tmp.name)
        self.reports_root = self.root / "reports"
        self.ingest_root = self.reports_root / "ingest"
        self.batch_root = self.reports_root / "batch_demo"
        self.reports_root.mkdir(parents=True, exist_ok=True)
        self.ingest_root.mkdir(parents=True, exist_ok=True)
        self.batch_root.mkdir(parents=True, exist_ok=True)

        run_payload = {
            "strategy": {"name": "EMA Cross", "strategy_id": "ema_cross_atr"},
            "target": {"market": "forex", "symbol": "EURUSD", "timeframe": "1h"},
            "created_at": "2026-03-17T10:00:00+00:00",
            "backtest": {
                "status": "ok",
                "metrics": {
                    "total_return_pct": 2.4,
                    "sharpe": 1.1,
                    "max_drawdown_pct": 3.2,
                    "oos_degradation_pct": 21.0,
                },
                "trade_log": [{"net_pnl_pct": 0.5}, {"net_pnl_pct": -0.2}],
            },
        }
        (self.reports_root / "run_20260317_100000_1.json").write_text(json.dumps(run_payload), encoding="utf-8")

        manifest_payload = {
            "provider": "dukascopy-node",
            "created_at": "2026-03-17T09:00:00+00:00",
            "status": "ok",
            "results": [{"status": "ok"}],
        }
        (self.ingest_root / "manifest_20260317_090000.json").write_text(json.dumps(manifest_payload), encoding="utf-8")

        batch_summary = {
            "created_at": "2026-03-17T11:00:00+00:00",
            "strategy": "ema_cross_atr",
            "max_retries": 5,
            "scenarios": [
                {
                    "name": "forex_EURUSD_1h",
                    "market": "forex",
                    "symbol": "EURUSD",
                    "timeframe": "1h",
                    "reports": 1,
                    "promoted_count": 0,
                    "best": {
                        "report": "reports/run_20260317_100000_1.json",
                        "candidate_index": 0,
                        "total_candidates": 1,
                        "metrics": {
                            "total_return_pct": 2.4,
                            "sharpe": 1.1,
                            "max_drawdown_pct": 3.2,
                            "oos_degradation_pct": 21.0,
                        },
                    },
                }
            ],
        }
        (self.batch_root / "summary.json").write_text(json.dumps(batch_summary), encoding="utf-8")

        universe_cfg, risk_cfg = load_configs()
        self._originals = {
            "reader": api_main.reader,
            "index_service": api_main.index_service,
            "batch_service": api_main.batch_service,
            "workflow_service": api_main.workflow_service,
            "intake_service": api_main.intake_service,
        }
        api_main.reader = ReportReader(reports_root=self.reports_root)
        api_main.index_service = ReportIndexService(
            reports_root=self.reports_root,
            db_path=self.reports_root / "index" / "reports.db",
        )
        api_main.index_service.rebuild()
        api_main.batch_service = BatchReportService(reports_root=self.reports_root)
        api_main.workflow_service = StrategyWorkflowService(
            storage_path=self.reports_root / "strategy_workflow.json",
            reports_root=self.reports_root,
        )
        api_main.intake_service = StrategyIntakeService(
            storage_dir=self.reports_root / "strategy_intake",
            universe_cfg=universe_cfg,
            risk_cfg=risk_cfg,
        )
        self.addCleanup(self._restore_services)

    def _restore_services(self) -> None:
        for name, original in self._originals.items():
            setattr(api_main, name, original)

    def test_api_route_functions_smoke(self) -> None:
        self.assertEqual(api_main.health()["status"], "ok")

        runs = api_main.runs(limit=20, offset=0, market=None, status=None, strategy_id=None, symbol=None, timeframe=None, from_at=None, to_at=None)
        self.assertGreaterEqual(runs["total"], 1)

        run_detail = api_main.run_detail("run_20260317_100000_1")
        self.assertEqual(run_detail["payload"]["report_kind"], "run_report")

        manifests = api_main.ingest_manifests(limit=20, offset=0, status=None, from_at=None, to_at=None)
        self.assertEqual(manifests["total"], 1)

        manifest_detail = api_main.ingest_manifest_detail("manifest_20260317_090000")
        self.assertEqual(manifest_detail["payload"]["report_kind"], "ingest_manifest")

        batches = api_main.list_batches(limit=20, offset=0)
        self.assertEqual(batches["total"], 1)

        batch_detail = api_main.batch_detail("batch_demo")
        self.assertEqual(batch_detail["batch_id"], "batch_demo")

        sim_options = api_main.simulations_options()
        self.assertIn("strategies", sim_options)

        intake_options = api_main.strategy_intake_options()
        self.assertIn("markets", intake_options)

        created_intake = api_main.create_strategy_intake(
            {
                "title": "Smoke intake",
                "thesis": "Simple smoke test idea",
                "target_markets": ["forex"],
                "target_timeframes": ["1h"],
            }
        )
        self.assertEqual(created_intake["intake"]["status"], "captured")

        listed_intakes = api_main.list_strategy_intakes(limit=20, offset=0)
        self.assertEqual(listed_intakes["total"], 1)

        workflow_init = api_main.strategy_workflow_init()
        self.assertIn("strategies", workflow_init)
        workflow_board = api_main.strategy_workflow_board()
        self.assertIn("items", workflow_board)

        spaces = api_main.list_optimization_spaces()
        self.assertIn("items", spaces)
        ema_space = api_main.get_optimization_space("ema_cross_atr")
        self.assertEqual(ema_space["strategy_id"], "ema_cross_atr")

        index_status = api_main.index_status()
        self.assertTrue(index_status["ready"])

    def test_ui_route_manifest_smoke(self) -> None:
        manifest_path = Path("web/src/route-manifest.json")
        app_path = Path("web/src/App.tsx")
        shell_path = Path("web/src/components/AppShell.tsx")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_keys = {
            "dashboard",
            "runDetail",
            "manifestDetail",
            "optimization",
            "batches",
            "batchDetail",
            "simulations",
            "intake",
            "workflow",
        }

        self.assertEqual(set(manifest.keys()), expected_keys)
        self.assertEqual(len(set(manifest.values())), len(manifest))

        app_source = app_path.read_text(encoding="utf-8")
        shell_source = shell_path.read_text(encoding="utf-8")
        self.assertIn("route-manifest.json", app_source)
        self.assertIn("route-manifest.json", shell_source)


if __name__ == "__main__":
    unittest.main()
