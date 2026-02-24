import json
import tempfile
import unittest
from pathlib import Path

from api.strategy_workflow import StrategyWorkflowService


class StrategyWorkflowServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        root = Path(self._tmp.name)
        self.reports_root = root / "reports"
        self.reports_root.mkdir(parents=True, exist_ok=True)

        run_payload = {
            "strategy_id": "ema_cross_atr",
            "created_at": "2026-02-20T00:00:00+00:00",
            "metrics": {
                "total_return_pct": 1.2,
                "sharpe": 0.8,
                "max_drawdown_pct": 2.3,
                "oos_degradation_pct": 40.0,
            },
        }
        (self.reports_root / "run_20260220_000001_sim.json").write_text(json.dumps(run_payload), encoding="utf-8")

        self.service = StrategyWorkflowService(
            storage_path=self.reports_root / "strategy_workflow.json",
            reports_root=self.reports_root,
        )

    def test_init_and_board(self) -> None:
        init_payload = self.service.init_from_registry()
        self.assertIn("strategies", init_payload)

        board = self.service.get_board()
        self.assertIn("states", board)
        self.assertIn("items", board)

        ema = next((x for x in board["items"] if x["strategy_id"] == "ema_cross_atr"), None)
        self.assertIsNotNone(ema)
        self.assertEqual(ema["state"], "draft")
        self.assertIsNotNone(ema["last_run"])

    def test_transition_guard_and_success(self) -> None:
        self.service.init_from_registry()

        # Invalid jump from draft -> approved should fail.
        with self.assertRaises(ValueError):
            self.service.transition("ema_cross_atr", "approved", note="invalid")

        # Valid path draft -> research.
        updated = self.service.transition("ema_cross_atr", "research", note="start research")
        self.assertEqual(updated["state"], "research")


if __name__ == "__main__":
    unittest.main()
