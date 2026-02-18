from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ALLOWED_STATES = {
    "queued",
    "brief_generated",
    "code_generated",
    "campaign_running",
    "campaign_evaluated",
    "refinement_planned",
    "completed",
    "failed",
    "paused",
    "cancelled",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class CampaignStore:
    def __init__(self, campaigns_root: Path) -> None:
        self.campaigns_root = campaigns_root
        self.campaigns_root.mkdir(parents=True, exist_ok=True)

    def campaign_dir(self, campaign_id: str) -> Path:
        return self.campaigns_root / campaign_id

    def campaign_file(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "campaign.json"

    def iterations_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "iterations"

    def artifacts_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "artifacts"

    def patches_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "patches"

    def exports_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "exports"

    def iteration_file(self, campaign_id: str, iteration_id: str) -> Path:
        return self.iterations_dir(campaign_id) / f"{iteration_id}.json"

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    def create_campaign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = payload.get("campaign_id") or f"cmp_{uuid.uuid4().hex[:12]}"
        now = _utc_now()

        campaign = {
            "campaign_id": campaign_id,
            "name": payload.get("name") or campaign_id,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "prompt": payload.get("prompt", ""),
            "prompts": payload.get("prompts", []),
            "targets": payload.get("targets", {}),
            "constraints": payload.get("constraints", {}),
            "gates": payload.get("gates", {}),
            "budgets": payload.get("budgets", {}),
            "metadata": payload.get("metadata", {}),
            "history": [
                {
                    "at": now,
                    "event": "created",
                    "from_state": None,
                    "to_state": "queued",
                    "reason": "campaign created",
                }
            ],
            "stats": {
                "iterations_total": 0,
                "best_iteration": None,
                "best_score": None,
                "last_score": None,
                "no_improve_streak": 0,
            },
        }

        base = self.campaign_dir(campaign_id)
        base.mkdir(parents=True, exist_ok=True)
        self.iterations_dir(campaign_id).mkdir(parents=True, exist_ok=True)
        self.artifacts_dir(campaign_id).mkdir(parents=True, exist_ok=True)
        self.patches_dir(campaign_id).mkdir(parents=True, exist_ok=True)
        self.exports_dir(campaign_id).mkdir(parents=True, exist_ok=True)
        self._save_json(self.campaign_file(campaign_id), campaign)
        return campaign

    def list_campaigns(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
        files = sorted(
            [p for p in self.campaigns_root.glob("*/campaign.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        items: List[Dict[str, Any]] = []
        for path in files:
            payload = self._load_json(path)
            if status and str(payload.get("status", "")).lower() != status.lower():
                continue
            items.append(
                {
                    "campaign_id": payload.get("campaign_id"),
                    "name": payload.get("name"),
                    "status": payload.get("status"),
                    "created_at": payload.get("created_at"),
                    "updated_at": payload.get("updated_at"),
                    "prompt": payload.get("prompt", ""),
                    "iterations_total": payload.get("stats", {}).get("iterations_total", 0),
                    "best_score": payload.get("stats", {}).get("best_score"),
                }
            )

        total = len(items)
        page = items[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": page}

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        path = self.campaign_file(campaign_id)
        if not path.exists():
            raise FileNotFoundError(f"campaign not found: {campaign_id}")
        return self._load_json(path)

    def save_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = str(campaign["campaign_id"])
        campaign["updated_at"] = _utc_now()
        self._save_json(self.campaign_file(campaign_id), campaign)
        return campaign

    def get_iteration(self, campaign_id: str, iteration_id: str) -> Dict[str, Any]:
        path = self.iteration_file(campaign_id, iteration_id)
        if not path.exists():
            raise FileNotFoundError(f"iteration not found: {iteration_id}")
        return self._load_json(path)

    def save_iteration(self, campaign_id: str, iteration_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._save_json(self.iteration_file(campaign_id, iteration_id), payload)
        return payload

    def list_iterations(self, campaign_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        base = self.iterations_dir(campaign_id)
        if not base.exists():
            raise FileNotFoundError(f"campaign not found: {campaign_id}")

        files = sorted(
            [p for p in base.glob("iter_*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        items: List[Dict[str, Any]] = []
        for path in files:
            payload = self._load_json(path)
            items.append(
                {
                    "iteration_id": path.stem,
                    "status": payload.get("status", "unknown"),
                    "score": payload.get("score"),
                    "decision": payload.get("decision"),
                    "created_at": payload.get("created_at"),
                    "summary": payload.get("summary", ""),
                }
            )

        total = len(items)
        page = items[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": page}

    def list_artifacts(self, campaign_id: str) -> Dict[str, Any]:
        base = self.campaign_dir(campaign_id)
        if not base.exists():
            raise FileNotFoundError(f"campaign not found: {campaign_id}")

        folders = {
            "iterations": self.iterations_dir(campaign_id),
            "artifacts": self.artifacts_dir(campaign_id),
            "patches": self.patches_dir(campaign_id),
            "exports": self.exports_dir(campaign_id),
        }

        out: Dict[str, Any] = {"campaign_id": campaign_id}
        for name, folder in folders.items():
            files: List[Dict[str, Any]] = []
            if folder.exists():
                for p in sorted(folder.rglob("*")):
                    if p.is_file():
                        files.append(
                            {
                                "path": str(p.relative_to(base)),
                                "bytes": p.stat().st_size,
                                "modified_at": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
                            }
                        )
            out[name] = files

        return out


class CampaignOrchestrator:
    def __init__(self, store: CampaignStore) -> None:
        self.store = store

    def _transition(self, campaign: Dict[str, Any], to_state: str, reason: str) -> Dict[str, Any]:
        if to_state not in ALLOWED_STATES:
            raise ValueError(f"invalid state: {to_state}")

        from_state = campaign.get("status")
        if from_state == to_state:
            return campaign

        event = {
            "at": _utc_now(),
            "event": "state_transition",
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
        }
        campaign["status"] = to_state
        campaign.setdefault("history", []).append(event)
        return self.store.save_campaign(campaign)

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        campaign = self.store.create_campaign(payload)
        return self._transition(campaign, "brief_generated", "orchestrator initialized")

    def pause(self, campaign_id: str, reason: str) -> Dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        return self._transition(campaign, "paused", reason or "paused by user")

    def resume(self, campaign_id: str, reason: str) -> Dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        next_state = "campaign_running" if campaign.get("stats", {}).get("iterations_total", 0) > 0 else "brief_generated"
        return self._transition(campaign, next_state, reason or "resumed by user")

    def cancel(self, campaign_id: str, reason: str) -> Dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        return self._transition(campaign, "cancelled", reason or "cancelled by user")

    def register_iteration_stub(self, campaign_id: str, summary: str = "") -> Dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        total = int(campaign.get("stats", {}).get("iterations_total", 0)) + 1
        iteration_id = f"iter_{total:04d}"
        payload = {
            "iteration": total,
            "iteration_id": iteration_id,
            "status": "created",
            "created_at": _utc_now(),
            "summary": summary,
            "score": None,
        }

        self.store.save_iteration(campaign_id, iteration_id, payload)
        campaign.setdefault("stats", {})["iterations_total"] = total
        self.store.save_campaign(campaign)
        self._transition(campaign, "campaign_running", "iteration stub created")

        return payload

    def _evaluate_metrics(self, metrics: Dict[str, Any], gates: Dict[str, Any]) -> Dict[str, Any]:
        total_return = _safe_float(metrics.get("total_return_pct"), 0.0)
        sharpe = _safe_float(metrics.get("sharpe"), 0.0)
        max_dd = _safe_float(metrics.get("max_drawdown_pct"), 100.0)
        oos_deg = _safe_float(metrics.get("oos_degradation_pct"), 100.0)

        gate_dd = _safe_float(gates.get("max_drawdown_pct"), 12.0)
        gate_sharpe = _safe_float(gates.get("min_sharpe"), 1.2)
        gate_oos = _safe_float(gates.get("max_oos_degradation_pct"), 30.0)

        pass_drawdown = max_dd <= gate_dd
        pass_sharpe = sharpe >= gate_sharpe
        pass_oos = oos_deg <= gate_oos

        ret_component = _clamp(((total_return + 20.0) / 40.0) * 100.0, 0.0, 100.0)
        dd_component = _clamp((gate_dd / max(max_dd, 1e-6)) * 100.0, 0.0, 100.0)
        sharpe_component = _clamp((sharpe / max(gate_sharpe, 1e-6)) * 100.0, 0.0, 100.0)
        oos_component = _clamp((gate_oos / max(oos_deg, 1e-6)) * 100.0, 0.0, 100.0)

        score = (
            ret_component * 0.35
            + dd_component * 0.30
            + sharpe_component * 0.20
            + oos_component * 0.15
        )

        return {
            "metrics": {
                "total_return_pct": total_return,
                "sharpe": sharpe,
                "max_drawdown_pct": max_dd,
                "oos_degradation_pct": oos_deg,
            },
            "gates": {
                "max_drawdown_pct": gate_dd,
                "min_sharpe": gate_sharpe,
                "max_oos_degradation_pct": gate_oos,
            },
            "pass": {
                "drawdown": pass_drawdown,
                "sharpe": pass_sharpe,
                "oos_degradation": pass_oos,
                "all": pass_drawdown and pass_sharpe and pass_oos,
            },
            "components": {
                "return_component": round(ret_component, 4),
                "drawdown_component": round(dd_component, 4),
                "sharpe_component": round(sharpe_component, 4),
                "oos_component": round(oos_component, 4),
            },
            "score": round(score, 4),
        }

    def evaluate_iteration(
        self,
        campaign_id: str,
        iteration_id: str,
        metrics: Dict[str, Any],
        notes: str = "",
    ) -> Dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        iteration = self.store.get_iteration(campaign_id, iteration_id)

        evaluation = self._evaluate_metrics(metrics=metrics, gates=campaign.get("gates", {}))
        score = float(evaluation["score"])

        stats = campaign.setdefault("stats", {})
        best_score = stats.get("best_score")
        improved = best_score is None or score > float(best_score)
        if improved:
            stats["best_score"] = score
            stats["best_iteration"] = iteration_id
            stats["no_improve_streak"] = 0
        else:
            stats["no_improve_streak"] = int(stats.get("no_improve_streak", 0)) + 1

        stats["last_score"] = score

        budgets = campaign.get("budgets", {})
        max_loops = int(budgets.get("max_loops", 50))
        max_no_improve = int(budgets.get("max_no_improve_loops", 5))
        loops = int(stats.get("iterations_total", 0))

        if evaluation["pass"]["all"]:
            decision = "promote_candidate"
        else:
            decision = "iterate"

        stop_reasons: List[str] = []
        if loops >= max_loops:
            stop_reasons.append("max_loops_reached")
        if int(stats.get("no_improve_streak", 0)) >= max_no_improve:
            stop_reasons.append("no_improvement_limit_reached")

        if decision == "iterate" and stop_reasons:
            decision = "reject_stop"

        iteration["status"] = "evaluated"
        iteration["evaluated_at"] = _utc_now()
        iteration["input_metrics"] = metrics
        iteration["evaluation"] = evaluation
        iteration["score"] = score
        iteration["decision"] = decision
        iteration["notes"] = notes
        iteration["stop_reasons"] = stop_reasons
        self.store.save_iteration(campaign_id, iteration_id, iteration)
        self.store.save_campaign(campaign)

        self._transition(campaign, "campaign_evaluated", f"iteration {iteration_id} evaluated")

        if decision == "promote_candidate":
            self._transition(campaign, "completed", f"iteration {iteration_id} passed all gates")
        elif decision == "reject_stop":
            self._transition(campaign, "failed", f"iteration {iteration_id} reached stop criteria")
        else:
            self._transition(campaign, "refinement_planned", f"iteration {iteration_id} requires refinement")

        artifact = {
            "campaign_id": campaign_id,
            "iteration_id": iteration_id,
            "created_at": _utc_now(),
            "evaluation": evaluation,
            "decision": decision,
            "stop_reasons": stop_reasons,
        }
        ev_path = self.store.artifacts_dir(campaign_id) / f"evaluation_{iteration_id}.json"
        with ev_path.open("w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2)

        return {
            "campaign_id": campaign_id,
            "iteration_id": iteration_id,
            "score": score,
            "decision": decision,
            "evaluation": evaluation,
            "stop_reasons": stop_reasons,
        }

    def critic_proposal(self, campaign_id: str, iteration_id: str) -> Dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        iteration = self.store.get_iteration(campaign_id, iteration_id)

        evaluation = iteration.get("evaluation", {})
        pass_flags = evaluation.get("pass", {})
        metrics = evaluation.get("metrics", {})

        suggestions: List[str] = []

        if not pass_flags.get("drawdown", False):
            suggestions.append("Reduce risk_per_trade and tighten ATR stop multiplier range.")
        if not pass_flags.get("sharpe", False):
            suggestions.append("Narrow entry conditions and remove low-quality parameter combinations.")
        if not pass_flags.get("oos_degradation", False):
            suggestions.append("Shrink parameter-space and prioritize stability-oriented ranges.")

        if _safe_float(metrics.get("total_return_pct"), 0.0) <= 0:
            suggestions.append("Rebalance take-profit/stop-loss ratio and test stronger trend filters.")

        if not suggestions:
            suggestions.append("Promote this candidate to manual review and run parity/export checks.")

        proposal = {
            "proposal_id": f"critic_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "campaign_id": campaign_id,
            "iteration_id": iteration_id,
            "created_at": _utc_now(),
            "decision": iteration.get("decision"),
            "suggestions": suggestions,
            "next_action": "iterate" if iteration.get("decision") != "promote_candidate" else "manual_review",
        }

        out_file = self.store.artifacts_dir(campaign_id) / f"critic_{iteration_id}.json"
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(proposal, fh, indent=2)

        iteration["critic"] = proposal
        self.store.save_iteration(campaign_id, iteration_id, iteration)

        if proposal["next_action"] == "iterate":
            self._transition(campaign, "refinement_planned", f"critic proposal created for {iteration_id}")

        return proposal

    def loop_tick(
        self,
        campaign_id: str,
        metrics: Dict[str, Any],
        summary: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        iteration = self.register_iteration_stub(campaign_id=campaign_id, summary=summary)
        evaluation = self.evaluate_iteration(
            campaign_id=campaign_id,
            iteration_id=iteration["iteration_id"],
            metrics=metrics,
            notes=notes,
        )

        critic = None
        if evaluation["decision"] != "promote_candidate":
            critic = self.critic_proposal(campaign_id=campaign_id, iteration_id=iteration["iteration_id"])

        return {
            "iteration": iteration,
            "evaluation": evaluation,
            "critic": critic,
        }

    def request_export(self, campaign_id: str, target: str) -> Dict[str, Any]:
        normalized = target.lower().strip()
        if normalized not in {"ctrader", "pine"}:
            raise ValueError("unsupported export target")

        campaign = self.store.get_campaign(campaign_id)
        stub = {
            "campaign_id": campaign_id,
            "target": normalized,
            "status": "queued",
            "requested_at": _utc_now(),
            "note": "Exporter v1 placeholder artifact",
        }

        out_file = self.store.exports_dir(campaign_id) / f"{normalized}_request_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(stub, fh, indent=2)

        self._transition(campaign, "refinement_planned", f"export requested for {normalized}")
        return stub
