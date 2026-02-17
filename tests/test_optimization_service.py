import json
import tempfile
import unittest
from pathlib import Path

from api.optimization import OptimizationService


class OptimizationServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.risk_path = Path(self._tmp.name) / "risk.json"
        self.risk_path.write_text(
            json.dumps(
                {
                    "optimization": {
                        "parameter_space": {
                            "demo_strategy": {
                                "search_mode": "grid",
                                "max_combinations": 100,
                                "shuffle": False,
                                "seed": 42,
                                "parameters": {
                                    "ema_fast": {
                                        "enabled": True,
                                        "type": "int",
                                        "min": 5,
                                        "max": 7,
                                        "step": 1,
                                    },
                                    "ema_slow": {
                                        "enabled": False,
                                        "type": "int",
                                        "value": 20,
                                    },
                                },
                            }
                        }
                    }
                }
            )
        )
        self.service = OptimizationService(self.risk_path)

    def test_list_and_get_space(self) -> None:
        listed = self.service.list_spaces()
        self.assertEqual(listed["total"], 1)
        self.assertEqual(listed["items"][0]["strategy_id"], "demo_strategy")

        detail = self.service.get_space("demo_strategy")
        self.assertEqual(detail["strategy_id"], "demo_strategy")
        self.assertEqual(detail["preview"]["total_candidates"], 3)

    def test_update_and_preview_space(self) -> None:
        updated_payload = {
            "search_mode": "grid",
            "max_combinations": 10,
            "shuffle": False,
            "seed": 42,
            "parameters": {
                "ema_fast": {"enabled": True, "type": "int", "min": 5, "max": 6, "step": 1},
                "ema_slow": {"enabled": True, "type": "int", "min": 20, "max": 22, "step": 1},
            },
        }

        updated = self.service.update_space("demo_strategy", updated_payload)
        self.assertEqual(updated["preview"]["total_candidates"], 6)

        preview = self.service.preview_space("demo_strategy")
        self.assertEqual(preview["total_candidates"], 6)
        self.assertEqual(len(preview["sample_candidates"]), 5)

    def test_preview_override_does_not_persist(self) -> None:
        override = {
            "search_mode": "grid",
            "max_combinations": 10,
            "shuffle": False,
            "seed": 42,
            "parameters": {
                "ema_fast": {"enabled": True, "type": "int", "min": 1, "max": 1, "step": 1},
                "ema_slow": {"enabled": False, "type": "int", "value": 20},
            },
        }

        preview = self.service.preview_space("demo_strategy", override_payload=override)
        self.assertEqual(preview["total_candidates"], 1)

        persisted = self.service.get_space("demo_strategy")
        self.assertEqual(persisted["preview"]["total_candidates"], 3)


if __name__ == "__main__":
    unittest.main()
