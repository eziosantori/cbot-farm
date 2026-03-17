from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bots import list_strategies


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "strategy"


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _float_value(value: Any, default: float) -> float:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric value: {value}") from exc
    if parsed <= 0:
        raise ValueError("risk gate values must be positive")
    return parsed


class StrategyIntakeService:
    def __init__(self, storage_dir: Path, universe_cfg: Dict[str, Any], risk_cfg: Dict[str, Any]) -> None:
        self.storage_dir = storage_dir
        self.index_path = self.storage_dir / "index.json"
        self.universe_cfg = universe_cfg
        self.risk_cfg = risk_cfg
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {
                "schema_version": 1,
                "updated_at": _now(),
                "items": [],
            }
        with self.index_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_index(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload["updated_at"] = _now()
        with self.index_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return payload

    def _default_risk_gates(self) -> Dict[str, float]:
        limits = self.risk_cfg.get("risk_limits", {})
        optimization = self.risk_cfg.get("optimization", {})
        return {
            "max_drawdown_pct": float(limits.get("strategy_max_drawdown_pct", 12.0)),
            "min_sharpe": float(optimization.get("min_sharpe", 1.2)),
            "max_oos_degradation_pct": float(optimization.get("max_oos_degradation_pct", 30.0)),
        }

    def _artifact_relpath(self, artifact_path: Path) -> str:
        return str(Path("reports") / "strategy_intake" / artifact_path.name)

    def options(self) -> Dict[str, Any]:
        return {
            "strategies": list_strategies(),
            "markets": self.universe_cfg.get("markets", {}),
            "defaults": {
                "linked_strategy_id": "",
                "target_markets": ["forex"],
                "target_timeframes": ["1h"],
                "risk_gates": self._default_risk_gates(),
            },
        }

    def list_intakes(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = self._load_index()
        items = [item for item in payload.get("items", []) if isinstance(item, dict)]
        if status:
            items = [item for item in items if str(item.get("status") or "") == status]
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        total = len(items)
        page = items[offset : offset + limit]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": page,
        }

    def get_intake(self, intake_id: str) -> Dict[str, Any]:
        artifact_path = self.storage_dir / f"{intake_id}.json"
        if not artifact_path.exists():
            raise FileNotFoundError(f"strategy intake not found: {intake_id}")
        with artifact_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _build_prompts(
        self,
        title: str,
        thesis: str,
        target_markets: List[str],
        target_symbols: List[str],
        target_timeframes: List[str],
        risk_gates: Dict[str, float],
        notes: str,
        prompts_payload: Dict[str, Any],
    ) -> Dict[str, str]:
        targets = [
            f"markets: {', '.join(target_markets) or 'n/a'}",
            f"symbols: {', '.join(target_symbols) or 'use market defaults'}",
            f"timeframes: {', '.join(target_timeframes) or 'n/a'}",
            (
                "risk gates: "
                f"max_dd<={risk_gates['max_drawdown_pct']:.2f}%, "
                f"min_sharpe>={risk_gates['min_sharpe']:.2f}, "
                f"max_oos_deg<={risk_gates['max_oos_degradation_pct']:.2f}%"
            ),
        ]
        note_line = f"Additional notes: {notes}" if notes else "Additional notes: none"

        def prompt_text(key: str, fallback: str) -> str:
            raw = str(prompts_payload.get(key) or "").strip()
            return raw or fallback

        return {
            "research_prompt": prompt_text(
                "research_prompt",
                (
                    f"Analyze the trading idea '{title}'. Thesis: {thesis}. "
                    f"Focus on {', '.join(target_markets)} across {', '.join(target_timeframes)}. "
                    "Return the market structure assumptions, entry/exit logic candidates, "
                    f"main failure modes, and data requirements. {' '.join(targets)}. {note_line}"
                ),
            ),
            "implementation_prompt": prompt_text(
                "implementation_prompt",
                (
                    f"Implement a canonical bot strategy for '{title}' in the cbot-farm engine. "
                    f"Strategy thesis: {thesis}. Preserve portability for later export to cTrader and Pine. "
                    f"Define parameters, default values, and risk controls. {' '.join(targets)}. {note_line}"
                ),
            ),
            "evaluation_prompt": prompt_text(
                "evaluation_prompt",
                (
                    f"Evaluate whether '{title}' is robust enough to continue. "
                    "Review IS/OOS behavior, drawdown, Sharpe, and overfitting risk. "
                    f"Recommend iterate, reject, or promote with explicit reasons. {' '.join(targets)}. {note_line}"
                ),
            ),
        }

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = str(payload.get("title") or "").strip()
        thesis = str(payload.get("thesis") or "").strip()
        notes = str(payload.get("notes") or "").strip()
        linked_strategy_id = str(payload.get("linked_strategy_id") or "").strip() or None
        if not title:
            raise ValueError("title is required")
        if not thesis:
            raise ValueError("thesis is required")

        known_strategies = list_strategies()
        if linked_strategy_id and linked_strategy_id not in known_strategies:
            raise ValueError(f"unknown linked strategy: {linked_strategy_id}")

        target_markets = _string_list(payload.get("target_markets"))
        target_symbols = _string_list(payload.get("target_symbols"))
        target_timeframes = _string_list(payload.get("target_timeframes"))

        if not target_markets:
            raise ValueError("at least one target market is required")
        if not target_timeframes:
            raise ValueError("at least one target timeframe is required")

        defaults = self._default_risk_gates()
        risk_payload = payload.get("risk_gates") if isinstance(payload.get("risk_gates"), dict) else {}
        risk_gates = {
            "max_drawdown_pct": _float_value(risk_payload.get("max_drawdown_pct"), defaults["max_drawdown_pct"]),
            "min_sharpe": _float_value(risk_payload.get("min_sharpe"), defaults["min_sharpe"]),
            "max_oos_degradation_pct": _float_value(
                risk_payload.get("max_oos_degradation_pct"),
                defaults["max_oos_degradation_pct"],
            ),
        }

        prompts_payload = payload.get("prompts") if isinstance(payload.get("prompts"), dict) else {}
        prompts = self._build_prompts(
            title=title,
            thesis=thesis,
            target_markets=target_markets,
            target_symbols=target_symbols,
            target_timeframes=target_timeframes,
            risk_gates=risk_gates,
            notes=notes,
            prompts_payload=prompts_payload,
        )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        slug = _slugify(title)
        intake_id = f"intake_{timestamp}_{slug}"
        artifact_path = self.storage_dir / f"{intake_id}.json"
        created_at = _now()

        artifact = {
            "schema_version": 1,
            "intake_id": intake_id,
            "created_at": created_at,
            "updated_at": created_at,
            "status": "captured",
            "title": title,
            "slug": slug,
            "linked_strategy_id": linked_strategy_id,
            "thesis": thesis,
            "notes": notes,
            "target_universe": {
                "markets": target_markets,
                "symbols": target_symbols,
                "timeframes": target_timeframes,
            },
            "risk_gates": risk_gates,
            "prompts": prompts,
            "artifact_path": self._artifact_relpath(artifact_path),
        }

        with artifact_path.open("w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2)

        summary = {
            "intake_id": intake_id,
            "created_at": created_at,
            "status": artifact["status"],
            "title": title,
            "linked_strategy_id": linked_strategy_id,
            "target_markets": target_markets,
            "target_timeframes": target_timeframes,
            "artifact_path": artifact["artifact_path"],
        }

        index = self._load_index()
        items = [item for item in index.get("items", []) if isinstance(item, dict)]
        items.append(summary)
        index["items"] = items
        self._save_index(index)

        return artifact
