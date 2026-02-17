from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional

from cbot_farm.param_optimization import build_param_plan


class OptimizationService:
    def __init__(self, risk_config_path: Path) -> None:
        self.risk_config_path = risk_config_path

    def _load_risk(self) -> Dict[str, Any]:
        with self.risk_config_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_risk(self, payload: Dict[str, Any]) -> None:
        with self.risk_config_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")

    def list_spaces(self) -> Dict[str, Any]:
        risk = self._load_risk()
        spaces = risk.get("optimization", {}).get("parameter_space", {})

        items = []
        for strategy_id, space in spaces.items():
            params = space.get("parameters", {}) if isinstance(space, dict) else {}
            enabled_count = sum(1 for spec in params.values() if bool(spec.get("enabled", True)))
            items.append(
                {
                    "strategy_id": strategy_id,
                    "parameters_total": len(params),
                    "parameters_enabled": enabled_count,
                    "search_mode": space.get("search_mode", "grid") if isinstance(space, dict) else "grid",
                    "max_combinations": int(space.get("max_combinations", 0)) if isinstance(space, dict) else 0,
                }
            )

        items.sort(key=lambda x: x["strategy_id"])
        return {"total": len(items), "items": items}

    def get_space(self, strategy_id: str) -> Dict[str, Any]:
        risk = self._load_risk()
        spaces = risk.get("optimization", {}).get("parameter_space", {})
        space = spaces.get(strategy_id)
        if not isinstance(space, dict):
            raise FileNotFoundError(f"optimization space not found for strategy: {strategy_id}")

        plan = build_param_plan(strategy_id=strategy_id, risk_cfg=risk)
        return {
            "strategy_id": strategy_id,
            "space": space,
            "preview": {
                "total_candidates": int(plan.get("total_candidates", 0)),
                "raw_total_candidates": int(plan.get("raw_total_candidates", 0)),
                "truncated": bool(plan.get("truncated", False)),
                "search_mode": plan.get("search_mode", "grid"),
                "source": plan.get("source", "strategy_sample"),
                "space_summary": plan.get("space", {}),
            },
        }

    def update_space(self, strategy_id: str, space_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(space_payload, dict) or "parameters" not in space_payload:
            raise ValueError("invalid optimization space payload")

        risk = self._load_risk()
        risk.setdefault("optimization", {}).setdefault("parameter_space", {})[strategy_id] = space_payload

        # Validate by attempting plan build on an in-memory copy.
        risk_copy = copy.deepcopy(risk)
        _ = build_param_plan(strategy_id=strategy_id, risk_cfg=risk_copy)

        self._save_risk(risk)
        return self.get_space(strategy_id)

    def preview_space(self, strategy_id: str, override_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        risk = self._load_risk()

        if override_payload is not None:
            if not isinstance(override_payload, dict) or "parameters" not in override_payload:
                raise ValueError("invalid optimization space payload")
            risk = copy.deepcopy(risk)
            risk.setdefault("optimization", {}).setdefault("parameter_space", {})[strategy_id] = override_payload

        plan = build_param_plan(strategy_id=strategy_id, risk_cfg=risk)
        return {
            "strategy_id": strategy_id,
            "source": plan.get("source", "strategy_sample"),
            "search_mode": plan.get("search_mode", "grid"),
            "total_candidates": int(plan.get("total_candidates", 0)),
            "raw_total_candidates": int(plan.get("raw_total_candidates", 0)),
            "truncated": bool(plan.get("truncated", False)),
            "space_summary": plan.get("space", {}),
            "sample_candidates": plan.get("candidates", [])[:5],
        }
