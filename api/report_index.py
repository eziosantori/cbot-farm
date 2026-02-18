from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import Float, Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


def _to_float(v: Any) -> Optional[float]:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


class Base(DeclarativeBase):
    pass


class RunIndex(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    run_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    strategy: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    strategy_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    symbol: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timeframe: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_return_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sharpe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oos_degradation_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    indexed_at: Mapped[str] = mapped_column(String, nullable=False)


class IngestManifestIndex(Base):
    __tablename__ = "ingest_manifests"

    manifest_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rows_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ok_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[str] = mapped_column(String, nullable=False)


class ReportIndexService:
    def __init__(self, reports_root: Path, db_path: Path) -> None:
        self.reports_root = reports_root
        self.ingest_root = reports_root / "ingest"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{self.db_path}", future=True)
        Base.metadata.create_all(self.engine)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def rebuild(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()

        run_files = sorted([p for p in self.reports_root.glob("run_*.json") if p.is_file()])
        manifest_files = sorted([p for p in self.ingest_root.glob("manifest_*.json") if p.is_file()])

        with Session(self.engine) as session:
            session.query(RunIndex).delete()
            session.query(IngestManifestIndex).delete()

            run_rows = []
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

                run_rows.append(
                    RunIndex(
                        run_id=path.stem,
                        filename=path.name,
                        run_at=payload.get("run_at") or payload.get("created_at"),
                        status=run_status,
                        strategy=strategy_name,
                        strategy_id=strategy_id,
                        market=payload.get("market") or payload.get("target", {}).get("market"),
                        symbol=payload.get("symbol") or payload.get("target", {}).get("symbol"),
                        timeframe=timeframe,
                        total_return_pct=_to_float(metrics.get("total_return_pct")),
                        sharpe=_to_float(metrics.get("sharpe")),
                        max_drawdown_pct=_to_float(metrics.get("max_drawdown_pct")),
                        oos_degradation_pct=_to_float(metrics.get("oos_degradation_pct")),
                        indexed_at=now,
                    )
                )

            manifest_rows = []
            for path in manifest_files:
                payload = self._load_json(path)
                results = payload.get("results", [])
                ok_count = sum(1 for r in results if str(r.get("status", "")).lower() == "ok")
                failed_count = len(results) - ok_count
                manifest_rows.append(
                    IngestManifestIndex(
                        manifest_id=path.stem,
                        filename=path.name,
                        created_at=payload.get("created_at"),
                        status=payload.get("status"),
                        rows_count=len(results),
                        ok_count=ok_count,
                        failed_count=failed_count,
                        indexed_at=now,
                    )
                )

            session.add_all(run_rows)
            session.add_all(manifest_rows)
            session.commit()

        return {
            "runs_indexed": len(run_files),
            "manifests_indexed": len(manifest_files),
            "indexed_at": now,
            "db_path": str(self.db_path),
        }

    def status(self) -> Dict[str, Any]:
        with Session(self.engine) as session:
            runs_count = int(session.scalar(select(func.count()).select_from(RunIndex)) or 0)
            manifests_count = int(session.scalar(select(func.count()).select_from(IngestManifestIndex)) or 0)
            max_runs_idx = session.scalar(select(func.max(RunIndex.indexed_at)))
            max_manifest_idx = session.scalar(select(func.max(IngestManifestIndex.indexed_at)))

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
        with Session(self.engine) as session:
            query = session.query(RunIndex)

            if market:
                query = query.filter(func.lower(RunIndex.market) == market.lower())
            if status:
                query = query.filter(func.lower(RunIndex.status) == status.lower())

            total = int(query.count())
            rows = (
                query.order_by(func.coalesce(RunIndex.run_at, RunIndex.indexed_at).desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

        items = []
        for r in rows:
            items.append(
                {
                    "run_id": r.run_id,
                    "filename": r.filename,
                    "run_at": r.run_at,
                    "status": r.status,
                    "strategy": r.strategy,
                    "strategy_id": r.strategy_id,
                    "market": r.market,
                    "symbol": r.symbol,
                    "timeframe": r.timeframe,
                    "metrics": {
                        "total_return_pct": r.total_return_pct,
                        "sharpe": r.sharpe,
                        "max_drawdown_pct": r.max_drawdown_pct,
                        "oos_degradation_pct": r.oos_degradation_pct,
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
        with Session(self.engine) as session:
            query = session.query(IngestManifestIndex)

            if status:
                query = query.filter(func.lower(IngestManifestIndex.status) == status.lower())

            total = int(query.count())
            rows = (
                query.order_by(func.coalesce(IngestManifestIndex.created_at, IngestManifestIndex.indexed_at).desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

        items = []
        for r in rows:
            items.append(
                {
                    "manifest_id": r.manifest_id,
                    "filename": r.filename,
                    "created_at": r.created_at,
                    "status": r.status,
                    "rows": r.rows_count,
                    "ok": r.ok_count,
                    "failed": r.failed_count,
                }
            )

        return {"total": total, "limit": limit, "offset": offset, "items": items}
