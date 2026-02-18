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

    def test_export_request_creates_placeholder_artifact(self) -> None:
        campaign = self.orchestrator.create({"name": "exp-campaign"})
        campaign_id = campaign["campaign_id"]

        result = self.orchestrator.request_export(campaign_id, "ctrader")
        self.assertEqual(result["target"], "ctrader")
        self.assertEqual(result["status"], "queued")

        exports = self.store.list_artifacts(campaign_id)["exports"]
        self.assertEqual(len(exports), 1)
        self.assertTrue(exports[0]["path"].startswith("exports/ctrader_request_"))

        export_file = self.store.exports_dir(campaign_id) / Path(exports[0]["path"]).name
        payload = json.loads(export_file.read_text())
        self.assertEqual(payload["campaign_id"], campaign_id)

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
