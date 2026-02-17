from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.report_reader import ReportReader


ROOT = Path(__file__).resolve().parents[1]
reader = ReportReader(reports_root=ROOT / "reports")

app = FastAPI(title="cbot-farm API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/runs")
def runs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    market: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    return reader.list_runs(limit=limit, offset=offset, market=market, status=status)


@app.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict:
    try:
        return reader.get_run(run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/ingest-manifests")
def ingest_manifests(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
) -> dict:
    return reader.list_ingest_manifests(limit=limit, offset=offset, status=status)


@app.get("/ingest-manifests/{manifest_id}")
def ingest_manifest_detail(manifest_id: str) -> dict:
    try:
        return reader.get_ingest_manifest(manifest_id=manifest_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
