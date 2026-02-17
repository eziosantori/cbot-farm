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


if __name__ == "__main__":
    unittest.main()
