from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class BatchReportService:
    def __init__(self, reports_root: Path) -> None:
        self.reports_root = reports_root

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _batch_dirs(self) -> List[Path]:
        dirs = [p for p in self.reports_root.glob("batch_*") if p.is_dir() and (p / "summary.json").exists()]
        dirs.sort(key=lambda p: (p / "summary.json").stat().st_mtime, reverse=True)
        return dirs

    def _run_id_from_report_path(self, report_path: str) -> Optional[str]:
        name = Path(report_path).name
        if not name.endswith(".json"):
            return None
        stem = name[:-5]
        if stem.startswith("run_"):
            return stem[4:]
        return stem

    def _resolve_report_path(self, report_path: str) -> Optional[Path]:
        p = Path(report_path)
        if p.is_absolute():
            return p if p.exists() else None

        # Standard format used by batch summary artifacts.
        if report_path.startswith("reports/"):
            candidate = self.reports_root.parent / p
            return candidate if candidate.exists() else None

        candidate = self.reports_root / p
        if candidate.exists():
            return candidate

        candidate = self.reports_root.parent / p
        if candidate.exists():
            return candidate

        return None

    def _equity_curve_from_trade_log(self, trade_log: Any, max_points: int = 240) -> List[Dict[str, float]]:
        if not isinstance(trade_log, list) or not trade_log:
            return []

        equity = 1.0
        points: List[Dict[str, float]] = []
        for idx, trade in enumerate(trade_log, start=1):
            if not isinstance(trade, dict):
                continue

            raw = trade.get("net_pnl_pct", 0.0)
            if isinstance(raw, (int, float)):
                pnl_pct = float(raw)
            elif isinstance(raw, str):
                try:
                    pnl_pct = float(raw)
                except ValueError:
                    pnl_pct = 0.0
            else:
                pnl_pct = 0.0

            equity *= 1.0 + (pnl_pct / 100.0)
            points.append({"x": float(idx), "equity": round(equity, 6)})

        if len(points) <= max_points:
            return points

        step = max(1, len(points) // max_points)
        reduced = points[::step]
        if reduced[-1] != points[-1]:
            reduced.append(points[-1])
        return reduced

    def list_batches(self, limit: int = 20, offset: int = 0, strategy: Optional[str] = None) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []
        for batch_dir in self._batch_dirs():
            summary_path = batch_dir / "summary.json"
            payload = self._load_json(summary_path)

            strategy_id = payload.get("strategy")
            if strategy and str(strategy_id or "").lower() != strategy.lower():
                continue

            scenarios = payload.get("scenarios", []) if isinstance(payload.get("scenarios"), list) else []
            total_reports = 0
            promoted_count = 0
            best_return_values: List[float] = []

            for scenario in scenarios:
                if not isinstance(scenario, dict):
                    continue
                total_reports += int(scenario.get("reports", 0) or 0)
                promoted_count += int(scenario.get("promoted_count", 0) or 0)
                best = scenario.get("best", {})
                metrics = best.get("metrics", {}) if isinstance(best, dict) else {}
                raw_return = metrics.get("total_return_pct") if isinstance(metrics, dict) else None
                if isinstance(raw_return, (int, float)):
                    best_return_values.append(float(raw_return))

            items.append(
                {
                    "batch_id": batch_dir.name,
                    "created_at": payload.get("created_at"),
                    "strategy": strategy_id,
                    "max_retries": payload.get("max_retries"),
                    "scenarios": len(scenarios),
                    "total_reports": total_reports,
                    "promoted_count": promoted_count,
                    "best_return_pct": max(best_return_values) if best_return_values else None,
                }
            )

        total = len(items)
        page = items[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": page}

    def get_batch(self, batch_id: str) -> Dict[str, Any]:
        summary_path = self.reports_root / batch_id / "summary.json"
        if not summary_path.exists():
            raise FileNotFoundError(f"batch not found: {batch_id}")

        summary = self._load_json(summary_path)
        scenarios_raw = summary.get("scenarios", []) if isinstance(summary.get("scenarios"), list) else []
        scenarios: List[Dict[str, Any]] = []

        for scenario in scenarios_raw:
            if not isinstance(scenario, dict):
                continue

            best = scenario.get("best") if isinstance(scenario.get("best"), dict) else None
            best_report_path = str(best.get("report")) if best else ""
            run_id = self._run_id_from_report_path(best_report_path) if best_report_path else None

            equity_curve: List[Dict[str, float]] = []
            trades_count: Optional[int] = None
            if best_report_path:
                run_path = self._resolve_report_path(best_report_path)
                if run_path and run_path.exists():
                    run_payload = self._load_json(run_path)
                    trade_log = run_payload.get("backtest", {}).get("trade_log", [])
                    equity_curve = self._equity_curve_from_trade_log(trade_log=trade_log)
                    if isinstance(trade_log, list):
                        trades_count = len(trade_log)

            scenario_enriched = dict(scenario)
            scenario_enriched["best_run_id"] = run_id
            scenario_enriched["best_equity_curve"] = equity_curve
            scenario_enriched["best_trades_count"] = trades_count
            scenarios.append(scenario_enriched)

        return {
            "batch_id": batch_id,
            "summary": summary,
            "scenarios": scenarios,
        }
