from __future__ import annotations

import json
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
        # v1 placeholder transition to indicate orchestration layer attachment.
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

        out_file = self.store.iterations_dir(campaign_id) / f"{iteration_id}.json"
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        campaign.setdefault("stats", {})["iterations_total"] = total
        self.store.save_campaign(campaign)
        self._transition(campaign, "campaign_running", "iteration stub created")

        return payload

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
