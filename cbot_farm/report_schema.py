from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


CURRENT_RUN_REPORT_SCHEMA_VERSION = 2
CURRENT_INGEST_MANIFEST_SCHEMA_VERSION = 2

RUN_REPORT_KIND = "run_report"
INGEST_MANIFEST_KIND = "ingest_manifest"


def _clone(payload: Dict[str, Any]) -> Dict[str, Any]:
    return deepcopy(payload)


def _is_run_report(path: Optional[Path], payload: Dict[str, Any]) -> bool:
    if path and path.name.startswith("run_"):
        return True
    if payload.get("report_kind") == RUN_REPORT_KIND:
        return True
    return "backtest" in payload or "metrics" in payload or "strategy_id" in payload


def _is_ingest_manifest(path: Optional[Path], payload: Dict[str, Any]) -> bool:
    if path and path.name.startswith("manifest_"):
        return True
    if payload.get("report_kind") == INGEST_MANIFEST_KIND:
        return True
    return "results" in payload and "provider" in payload


def migrate_run_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = _clone(payload)

    strategy = out.get("strategy")
    strategy_id = out.get("strategy_id")
    if isinstance(strategy, dict):
        if strategy_id is None:
            strategy_id = strategy.get("strategy_id")
        out["strategy"] = strategy.get("name") or strategy_id or "unknown"
    if strategy_id is not None:
        out["strategy_id"] = strategy_id

    target = out.get("target")
    if not isinstance(target, dict):
        target = {}

    market = out.get("market") or target.get("market")
    symbol = out.get("symbol") or target.get("symbol")
    timeframe = target.get("timeframe")
    if timeframe is None:
        timeframes = out.get("timeframes")
        if isinstance(timeframes, list) and timeframes:
            timeframe = timeframes[0]

    if market is not None:
        out["market"] = market
        target["market"] = market
    if symbol is not None:
        out["symbol"] = symbol
        target["symbol"] = symbol
    if timeframe is not None:
        target["timeframe"] = timeframe
        timeframes = out.get("timeframes")
        if not isinstance(timeframes, list) or not timeframes:
            out["timeframes"] = [timeframe]

    if target:
        out["target"] = target

    metrics = out.get("metrics")
    if not isinstance(metrics, dict):
        metrics = out.get("backtest", {}).get("metrics", {})
    out["metrics"] = metrics if isinstance(metrics, dict) else {}

    status = out.get("status")
    if status is None:
        status = out.get("backtest", {}).get("status") or out.get("ingest", {}).get("status")
    if status is not None:
        out["status"] = status

    created_at = out.get("created_at") or out.get("run_at")
    run_at = out.get("run_at") or created_at
    if created_at is not None:
        out["created_at"] = created_at
    if run_at is not None:
        out["run_at"] = run_at

    out["report_kind"] = RUN_REPORT_KIND
    out["schema_version"] = CURRENT_RUN_REPORT_SCHEMA_VERSION
    return out


def migrate_ingest_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = _clone(payload)

    results = out.get("results")
    if not isinstance(results, list):
        results = []
    out["results"] = results

    ok_count = sum(1 for item in results if str(item.get("status", "")).lower() == "ok")
    failed_count = len(results) - ok_count
    out["summary"] = {
        "total": len(results),
        "ok": ok_count,
        "failed": failed_count,
    }

    filters = out.get("filters")
    if not isinstance(filters, dict):
        filters = {}
    out["filters"] = {
        "markets": filters.get("markets") if isinstance(filters.get("markets"), list) else [],
        "symbols": filters.get("symbols") if isinstance(filters.get("symbols"), list) else [],
        "timeframes": filters.get("timeframes") if isinstance(filters.get("timeframes"), list) else [],
    }

    out["report_kind"] = INGEST_MANIFEST_KIND
    out["schema_version"] = CURRENT_INGEST_MANIFEST_SCHEMA_VERSION
    return out


def migrate_report_payload(payload: Dict[str, Any], path: Optional[Path] = None) -> Dict[str, Any]:
    if _is_run_report(path, payload):
        return migrate_run_report(payload)
    if _is_ingest_manifest(path, payload):
        return migrate_ingest_manifest(payload)
    return _clone(payload)

