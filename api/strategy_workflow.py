from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bots import list_strategies

STATES = [
    "draft",
    "research",
    "backtest",
    "candidate",
    "paper",
    "approved",
    "archived",
]

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["research", "archived"],
    "research": ["backtest", "archived"],
    "backtest": ["research", "candidate", "archived"],
    "candidate": ["backtest", "paper", "archived"],
    "paper": ["candidate", "approved", "archived"],
    "approved": ["archived"],
    "archived": ["research"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrategyWorkflowService:
    def __init__(self, storage_path: Path, reports_root: Path) -> None:
        self.storage_path = storage_path
        self.reports_root = reports_root
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return {
                "schema_version": 1,
                "updated_at": _now(),
                "strategies": [],
            }
        with self.storage_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload["updated_at"] = _now()
        with self.storage_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return payload

    def _latest_run_for(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        files = sorted(
            [p for p in self.reports_root.glob("run_*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except Exception:
                continue
            if str(payload.get("strategy_id") or "") != strategy_id:
                continue
            return {
                "run_id": path.stem,
                "created_at": payload.get("created_at") or payload.get("run_at"),
                "metrics": payload.get("metrics") or payload.get("backtest", {}).get("metrics", {}),
            }
        return None

    def init_from_registry(self) -> Dict[str, Any]:
        payload = self._load()
        existing = {item.get("strategy_id"): item for item in payload.get("strategies", []) if isinstance(item, dict)}

        merged: List[Dict[str, Any]] = []
        for strategy_id, display_name in list_strategies().items():
            current = existing.get(strategy_id)
            if current:
                merged.append(current)
                continue
            merged.append(
                {
                    "strategy_id": strategy_id,
                    "display_name": display_name,
                    "state": "draft",
                    "updated_at": _now(),
                    "history": [
                        {
                            "at": _now(),
                            "event": "created",
                            "from_state": None,
                            "to_state": "draft",
                            "note": "auto-initialized",
                        }
                    ],
                }
            )

        payload["strategies"] = merged
        return self._save(payload)

    def get_board(self) -> Dict[str, Any]:
        payload = self.init_from_registry()

        items: List[Dict[str, Any]] = []
        for item in payload.get("strategies", []):
            if not isinstance(item, dict):
                continue
            strategy_id = str(item.get("strategy_id") or "")
            latest = self._latest_run_for(strategy_id)
            state = str(item.get("state") or "draft")
            items.append(
                {
                    "strategy_id": strategy_id,
                    "display_name": item.get("display_name") or strategy_id,
                    "state": state,
                    "updated_at": item.get("updated_at"),
                    "allowed_transitions": ALLOWED_TRANSITIONS.get(state, []),
                    "last_run": latest,
                    "history_size": len(item.get("history", [])) if isinstance(item.get("history"), list) else 0,
                }
            )

        state_counts = {state: 0 for state in STATES}
        for item in items:
            s = item.get("state")
            if s in state_counts:
                state_counts[s] += 1

        return {
            "states": STATES,
            "counts": state_counts,
            "items": items,
            "updated_at": payload.get("updated_at"),
        }

    def transition(self, strategy_id: str, to_state: str, note: str = "") -> Dict[str, Any]:
        if to_state not in STATES:
            raise ValueError(f"invalid state: {to_state}")

        payload = self.init_from_registry()
        strategies = payload.get("strategies", [])
        for item in strategies:
            if not isinstance(item, dict):
                continue
            if str(item.get("strategy_id")) != strategy_id:
                continue

            from_state = str(item.get("state") or "draft")
            if to_state == from_state:
                return item

            allowed = ALLOWED_TRANSITIONS.get(from_state, [])
            if to_state not in allowed:
                raise ValueError(f"transition not allowed: {from_state} -> {to_state}")

            event = {
                "at": _now(),
                "event": "transition",
                "from_state": from_state,
                "to_state": to_state,
                "note": note,
            }

            item["state"] = to_state
            item["updated_at"] = _now()
            history = item.setdefault("history", [])
            if isinstance(history, list):
                history.append(event)
            self._save(payload)
            return item

        raise FileNotFoundError(f"strategy not found: {strategy_id}")
