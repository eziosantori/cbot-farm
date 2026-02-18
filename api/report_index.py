from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _to_float(v: Any) -> Optional[float]:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


class ReportIndexService:
    def __init__(self, reports_root: Path, db_path: Path) -> None:
        self.reports_root = reports_root
        self.ingest_root = reports_root / "ingest"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    run_at TEXT,
                    status TEXT,
                    strategy TEXT,
                    strategy_id TEXT,
                    market TEXT,
                    symbol TEXT,
                    timeframe TEXT,
                    total_return_pct REAL,
                    sharpe REAL,
                    max_drawdown_pct REAL,
                    oos_degradation_pct REAL,
                    indexed_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ingest_manifests (
                    manifest_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    created_at TEXT,
                    status TEXT,
                    rows_count INTEGER,
                    ok_count INTEGER,
                    failed_count INTEGER,
                    indexed_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_market ON runs(market)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_run_at ON runs(run_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ingest_status ON ingest_manifests(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ingest_created_at ON ingest_manifests(created_at)")

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def rebuild(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()

        run_files = sorted([p for p in self.reports_root.glob("run_*.json") if p.is_file()])
        manifest_files = sorted([p for p in self.ingest_root.glob("manifest_*.json") if p.is_file()])

        with self._conn() as conn:
            conn.execute("DELETE FROM runs")
            conn.execute("DELETE FROM ingest_manifests")

            for path in run_files:
                payload = self._load_json(path)
                strategy_name = payload.get("strategy")
                strategy_id = payload.get("strategy_id")
                if isinstance(strategy_name, dict):
                    strategy_name = strategy_name.get("name")
                    if strategy_id is None:
                        strategy_id = payload.get("strategy", {}).get("strategy_id")

                timeframe = payload.get("target", {}).get("timeframe")
                if timeframe is None:
                    timeframes = payload.get("timeframes")
                    if isinstance(timeframes, list) and timeframes:
                        timeframe = timeframes[0]

                run_status = str(
                    payload.get("status")
                    or payload.get("backtest", {}).get("status")
                    or payload.get("ingest", {}).get("status")
                    or "unknown"
                ).lower()

                metrics = payload.get("metrics") or payload.get("backtest", {}).get("metrics", {})

                conn.execute(
                    """
                    INSERT INTO runs (
                        run_id, filename, run_at, status, strategy, strategy_id,
                        market, symbol, timeframe,
                        total_return_pct, sharpe, max_drawdown_pct, oos_degradation_pct,
                        indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        path.stem,
                        path.name,
                        payload.get("run_at") or payload.get("created_at"),
                        run_status,
                        strategy_name,
                        strategy_id,
                        payload.get("market") or payload.get("target", {}).get("market"),
                        payload.get("symbol") or payload.get("target", {}).get("symbol"),
                        timeframe,
                        _to_float(metrics.get("total_return_pct")),
                        _to_float(metrics.get("sharpe")),
                        _to_float(metrics.get("max_drawdown_pct")),
                        _to_float(metrics.get("oos_degradation_pct")),
                        now,
                    ),
                )

            for path in manifest_files:
                payload = self._load_json(path)
                results = payload.get("results", [])
                ok_count = sum(1 for r in results if str(r.get("status", "")).lower() == "ok")
                failed_count = len(results) - ok_count
                conn.execute(
                    """
                    INSERT INTO ingest_manifests (
                        manifest_id, filename, created_at, status,
                        rows_count, ok_count, failed_count, indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        path.stem,
                        path.name,
                        payload.get("created_at"),
                        payload.get("status"),
                        len(results),
                        ok_count,
                        failed_count,
                        now,
                    ),
                )

        return {
            "runs_indexed": len(run_files),
            "manifests_indexed": len(manifest_files),
            "indexed_at": now,
            "db_path": str(self.db_path),
        }

    def status(self) -> Dict[str, Any]:
        with self._conn() as conn:
            runs_count = int(conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
            manifests_count = int(conn.execute("SELECT COUNT(*) FROM ingest_manifests").fetchone()[0])
            max_runs_idx = conn.execute("SELECT MAX(indexed_at) FROM runs").fetchone()[0]
            max_manifest_idx = conn.execute("SELECT MAX(indexed_at) FROM ingest_manifests").fetchone()[0]

        return {
            "db_path": str(self.db_path),
            "runs_count": runs_count,
            "manifests_count": manifests_count,
            "last_indexed_at": max_runs_idx or max_manifest_idx,
            "ready": runs_count > 0 or manifests_count > 0,
        }

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        market: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        where = []
        args = []
        if market:
            where.append("LOWER(market) = ?")
            args.append(market.lower())
        if status:
            where.append("LOWER(status) = ?")
            args.append(status.lower())

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        with self._conn() as conn:
            total = int(conn.execute(f"SELECT COUNT(*) FROM runs {where_sql}", args).fetchone()[0])
            rows = conn.execute(
                f"""
                SELECT run_id, filename, run_at, status, strategy, strategy_id,
                       market, symbol, timeframe,
                       total_return_pct, sharpe, max_drawdown_pct, oos_degradation_pct
                FROM runs
                {where_sql}
                ORDER BY COALESCE(run_at, indexed_at) DESC
                LIMIT ? OFFSET ?
                """,
                [*args, limit, offset],
            ).fetchall()

        items = []
        for r in rows:
            items.append(
                {
                    "run_id": r["run_id"],
                    "filename": r["filename"],
                    "run_at": r["run_at"],
                    "status": r["status"],
                    "strategy": r["strategy"],
                    "strategy_id": r["strategy_id"],
                    "market": r["market"],
                    "symbol": r["symbol"],
                    "timeframe": r["timeframe"],
                    "metrics": {
                        "total_return_pct": r["total_return_pct"],
                        "sharpe": r["sharpe"],
                        "max_drawdown_pct": r["max_drawdown_pct"],
                        "oos_degradation_pct": r["oos_degradation_pct"],
                    },
                }
            )

        return {"total": total, "limit": limit, "offset": offset, "items": items}

    def list_ingest_manifests(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        where = []
        args = []
        if status:
            where.append("LOWER(status) = ?")
            args.append(status.lower())

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        with self._conn() as conn:
            total = int(conn.execute(f"SELECT COUNT(*) FROM ingest_manifests {where_sql}", args).fetchone()[0])
            rows = conn.execute(
                f"""
                SELECT manifest_id, filename, created_at, status,
                       rows_count, ok_count, failed_count
                FROM ingest_manifests
                {where_sql}
                ORDER BY COALESCE(created_at, indexed_at) DESC
                LIMIT ? OFFSET ?
                """,
                [*args, limit, offset],
            ).fetchall()

        items = []
        for r in rows:
            items.append(
                {
                    "manifest_id": r["manifest_id"],
                    "filename": r["filename"],
                    "created_at": r["created_at"],
                    "status": r["status"],
                    "rows": r["rows_count"],
                    "ok": r["ok_count"],
                    "failed": r["failed_count"],
                }
            )

        return {"total": total, "limit": limit, "offset": offset, "items": items}
