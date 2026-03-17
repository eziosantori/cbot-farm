from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class ReportReader:
    def __init__(self, reports_root: Path) -> None:
        self.reports_root = reports_root
        self.ingest_root = reports_root / "ingest"

    def _load_json(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _parse_datetime(self, raw: Any) -> Optional[datetime]:
        if not isinstance(raw, str) or not raw.strip():
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        market: Optional[str] = None,
        status: Optional[str] = None,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        from_at: Optional[str] = None,
        to_at: Optional[str] = None,
    ) -> dict[str, Any]:
        files = sorted(
            [p for p in self.reports_root.glob("run_*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        from_dt = self._parse_datetime(from_at)
        to_dt = self._parse_datetime(to_at)
        items: list[dict[str, Any]] = []
        for path in files:
            payload = self._load_json(path)

            run_market = str(payload.get("market") or payload.get("target", {}).get("market") or "").lower()
            run_status = str(
                payload.get("status")
                or payload.get("backtest", {}).get("status")
                or payload.get("ingest", {}).get("status")
                or "unknown"
            ).lower()

            if market and run_market != market.lower():
                continue
            if status and run_status != status.lower():
                continue

            strategy_name = payload.get("strategy")
            run_strategy_id = payload.get("strategy_id")
            if isinstance(strategy_name, dict):
                strategy_name = strategy_name.get("name")
                if run_strategy_id is None:
                    run_strategy_id = payload.get("strategy", {}).get("strategy_id")

            run_timeframe = payload.get("target", {}).get("timeframe")
            if run_timeframe is None:
                timeframes = payload.get("timeframes")
                if isinstance(timeframes, list) and timeframes:
                    run_timeframe = timeframes[0]

            run_symbol = payload.get("symbol") or payload.get("target", {}).get("symbol")
            run_at = payload.get("run_at") or payload.get("created_at")
            run_dt = self._parse_datetime(run_at)

            if strategy_id and str(run_strategy_id or "").lower() != strategy_id.lower():
                continue
            if symbol and str(run_symbol or "").lower() != symbol.lower():
                continue
            if timeframe and str(run_timeframe or "").lower() != timeframe.lower():
                continue
            if from_dt and (run_dt is None or run_dt < from_dt):
                continue
            if to_dt and (run_dt is None or run_dt > to_dt):
                continue

            items.append(
                {
                    "run_id": path.stem,
                    "external_run_id": payload.get("run_id"),
                    "filename": path.name,
                    "run_at": payload.get("run_at") or payload.get("created_at"),
                    "status": run_status,
                    "strategy": strategy_name,
                    "strategy_id": run_strategy_id,
                    "market": payload.get("market") or payload.get("target", {}).get("market"),
                    "symbol": run_symbol,
                    "timeframe": run_timeframe,
                    "metrics": payload.get("metrics") or payload.get("backtest", {}).get("metrics", {}),
                }
            )

        total = len(items)
        page = items[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": page}

    def get_run(self, run_id: str) -> dict[str, Any]:
        candidates = [
            self.reports_root / f"{run_id}.json",
            self.reports_root / f"run_{run_id}.json",
        ]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            raise FileNotFoundError(f"run not found: {run_id}")
        payload = self._load_json(path)
        return {"run_id": path.stem, "payload": payload}

    def list_ingest_manifests(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        from_at: Optional[str] = None,
        to_at: Optional[str] = None,
    ) -> dict[str, Any]:
        files = sorted(
            [p for p in self.ingest_root.glob("manifest_*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        from_dt = self._parse_datetime(from_at)
        to_dt = self._parse_datetime(to_at)
        items: list[dict[str, Any]] = []
        for path in files:
            payload = self._load_json(path)
            manifest_status = str(payload.get("status", "")).lower()
            if status and manifest_status != status.lower():
                continue

            created_at = payload.get("created_at")
            created_dt = self._parse_datetime(created_at)
            if from_dt and (created_dt is None or created_dt < from_dt):
                continue
            if to_dt and (created_dt is None or created_dt > to_dt):
                continue

            results = payload.get("results", [])
            ok_count = sum(1 for r in results if str(r.get("status", "")).lower() == "ok")
            fail_count = len(results) - ok_count

            items.append(
                {
                    "manifest_id": path.stem,
                    "filename": path.name,
                    "created_at": created_at,
                    "status": payload.get("status"),
                    "rows": len(results),
                    "ok": ok_count,
                    "failed": fail_count,
                }
            )

        total = len(items)
        page = items[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": page}

    def get_ingest_manifest(self, manifest_id: str) -> dict[str, Any]:
        candidates = [
            self.ingest_root / f"{manifest_id}.json",
            self.ingest_root / f"manifest_{manifest_id}.json",
        ]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            raise FileNotFoundError(f"manifest not found: {manifest_id}")
        payload = self._load_json(path)
        return {"manifest_id": path.stem, "payload": payload}
