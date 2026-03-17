import json
import tempfile
import unittest
from pathlib import Path

from api.campaigns import CampaignOrchestrator, CampaignStore


class CampaignsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name) / "campaigns"
        self.store = CampaignStore(campaigns_root=root)
        self.orchestrator = CampaignOrchestrator(store=self.store)

    def test_create_campaign_and_state_transitions(self) -> None:
        campaign = self.orchestrator.create(
            {
                "name": "test-campaign",
                "prompt": "build strategy",
                "targets": {"markets": ["forex"], "timeframes": ["1h"]},
            }
        )

        campaign_id = campaign["campaign_id"]
        self.assertEqual(campaign["status"], "brief_generated")

        iteration = self.orchestrator.register_iteration_stub(
            campaign_id=campaign_id,
            summary="initial iteration",
        )
        self.assertEqual(iteration["iteration_id"], "iter_0001")

        loaded = self.store.get_campaign(campaign_id)
        self.assertEqual(loaded["stats"]["iterations_total"], 1)
        self.assertEqual(loaded["status"], "campaign_running")

        paused = self.orchestrator.pause(campaign_id, "manual pause")
        self.assertEqual(paused["status"], "paused")

        resumed = self.orchestrator.resume(campaign_id, "manual resume")
        self.assertEqual(resumed["status"], "campaign_running")

        cancelled = self.orchestrator.cancel(campaign_id, "manual cancel")
        self.assertEqual(cancelled["status"], "cancelled")

    def test_export_request_generates_code_artifacts_for_supported_strategy(self) -> None:
        campaign = self.orchestrator.create(
            {
                "name": "exp-campaign",
                "strategy_id": "ema_cross_atr",
                "params": {
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
            }
        )
        campaign_id = campaign["campaign_id"]

        result = self.orchestrator.request_export(campaign_id, "ctrader")
        self.assertEqual(result["target"], "ctrader")
        self.assertEqual(result["status"], "generated")

        exports = self.store.list_artifacts(campaign_id)["exports"]
        self.assertEqual(len(exports), 2)
        export_paths = [item["path"] for item in exports]
        self.assertTrue(any(path.endswith(".cs") for path in export_paths))
        self.assertTrue(any(path.startswith("exports/ctrader_export_") for path in export_paths))

        export_file = self.store.exports_dir(campaign_id) / result["manifest_file"]
        payload = json.loads(export_file.read_text())
        self.assertEqual(payload["campaign_id"], campaign_id)
        self.assertEqual(payload["strategy_id"], "ema_cross_atr")
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(len(payload["files"]), 1)
        code_file = self.store.exports_dir(campaign_id) / payload["files"][0]
        self.assertTrue(code_file.exists())
        self.assertIn("class EmaCrossAtrBot", code_file.read_text())

    def test_export_request_returns_diagnostics_when_campaign_is_incomplete(self) -> None:
        campaign = self.orchestrator.create({"name": "exp-campaign-incomplete"})
        campaign_id = campaign["campaign_id"]

        result = self.orchestrator.request_export(campaign_id, "pine")
        self.assertEqual(result["target"], "pine")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("missing strategy_id" in item for item in result["diagnostics"]))

        export_file = self.store.exports_dir(campaign_id) / result["manifest_file"]
        payload = json.loads(export_file.read_text())
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["files"], [])

    def test_evaluate_iteration_promotes_when_all_gates_pass(self) -> None:
        campaign = self.orchestrator.create(
            {
                "name": "eval-pass",
                "gates": {
                    "max_drawdown_pct": 12,
                    "min_sharpe": 1.2,
                    "max_oos_degradation_pct": 30,
                },
            }
        )
        campaign_id = campaign["campaign_id"]
        iteration = self.orchestrator.register_iteration_stub(campaign_id, "pass case")

        result = self.orchestrator.evaluate_iteration(
            campaign_id=campaign_id,
            iteration_id=iteration["iteration_id"],
            metrics={
                "total_return_pct": 8.5,
                "sharpe": 1.5,
                "max_drawdown_pct": 9.0,
                "oos_degradation_pct": 20.0,
            },
            notes="good result",
        )

        self.assertEqual(result["decision"], "promote_candidate")
        loaded = self.store.get_campaign(campaign_id)
        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(loaded["stats"]["best_iteration"], iteration["iteration_id"])
        self.assertIsNotNone(loaded["stats"]["best_score"])

    def test_evaluate_iteration_can_trigger_reject_stop(self) -> None:
        campaign = self.orchestrator.create(
            {
                "name": "eval-fail",
                "budgets": {"max_loops": 1, "max_no_improve_loops": 1},
                "gates": {
                    "max_drawdown_pct": 10,
                    "min_sharpe": 1.2,
                    "max_oos_degradation_pct": 30,
                },
            }
        )
        campaign_id = campaign["campaign_id"]
        iteration = self.orchestrator.register_iteration_stub(campaign_id, "fail case")

        result = self.orchestrator.evaluate_iteration(
            campaign_id=campaign_id,
            iteration_id=iteration["iteration_id"],
            metrics={
                "total_return_pct": -5.0,
                "sharpe": -0.4,
                "max_drawdown_pct": 20.0,
                "oos_degradation_pct": 90.0,
            },
            notes="bad result",
        )

        self.assertEqual(result["decision"], "reject_stop")
        self.assertIn("max_loops_reached", result["stop_reasons"])
        loaded = self.store.get_campaign(campaign_id)
        self.assertEqual(loaded["status"], "failed")

    def test_loop_tick_generates_critic_when_not_promoted(self) -> None:
        campaign = self.orchestrator.create({"name": "loop-with-critic"})
        campaign_id = campaign["campaign_id"]

        out = self.orchestrator.loop_tick(
            campaign_id=campaign_id,
            summary="iteration summary",
            metrics={
                "total_return_pct": -1.0,
                "sharpe": 0.2,
                "max_drawdown_pct": 18.0,
                "oos_degradation_pct": 70.0,
            },
            notes="needs refinement",
        )

        self.assertIsNotNone(out["critic"])
        self.assertEqual(out["evaluation"]["decision"], "iterate")

        artifacts = self.store.list_artifacts(campaign_id)
        artifact_paths = [x["path"] for x in artifacts["artifacts"]]
        self.assertTrue(any(p.startswith("artifacts/evaluation_iter_") for p in artifact_paths))
        self.assertTrue(any(p.startswith("artifacts/critic_iter_") for p in artifact_paths))


if __name__ == "__main__":
    unittest.main()
