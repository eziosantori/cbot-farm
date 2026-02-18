from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.campaigns import CampaignOrchestrator, CampaignStore
from api.optimization import OptimizationService
from api.report_index import ReportIndexService
from api.report_reader import ReportReader


ROOT = Path(__file__).resolve().parents[1]
reader = ReportReader(reports_root=ROOT / "reports")
campaign_store = CampaignStore(campaigns_root=ROOT / "reports" / "campaigns")
orchestrator = CampaignOrchestrator(store=campaign_store)
optimization_service = OptimizationService(risk_config_path=ROOT / "config" / "risk.json")
index_service = ReportIndexService(reports_root=ROOT / "reports", db_path=ROOT / "reports" / "index" / "reports.db")

app = FastAPI(title="cbot-farm API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/runs")
def runs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    market: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    idx = index_service.status()
    if idx.get("ready"):
        return index_service.list_runs(limit=limit, offset=offset, market=market, status=status)
    return reader.list_runs(limit=limit, offset=offset, market=market, status=status)


@app.get("/runs/{run_id}")
def run_detail(run_id: str) -> Dict[str, Any]:
    try:
        return reader.get_run(run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/ingest-manifests")
def ingest_manifests(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
) -> Dict[str, Any]:
    idx = index_service.status()
    if idx.get("ready"):
        return index_service.list_ingest_manifests(limit=limit, offset=offset, status=status)
    return reader.list_ingest_manifests(limit=limit, offset=offset, status=status)


@app.get("/ingest-manifests/{manifest_id}")
def ingest_manifest_detail(manifest_id: str) -> Dict[str, Any]:
    try:
        return reader.get_ingest_manifest(manifest_id=manifest_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/index/status")
def index_status() -> Dict[str, Any]:
    return index_service.status()


@app.post("/index/rebuild")
def rebuild_index() -> Dict[str, Any]:
    return index_service.rebuild()


@app.get("/optimization/spaces")
def list_optimization_spaces() -> Dict[str, Any]:
    return optimization_service.list_spaces()


@app.get("/optimization/spaces/{strategy_id}")
def get_optimization_space(strategy_id: str) -> Dict[str, Any]:
    try:
        return optimization_service.get_space(strategy_id=strategy_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/optimization/spaces/{strategy_id}")
def update_optimization_space(
    strategy_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    try:
        return optimization_service.update_space(strategy_id=strategy_id, space_payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/optimization/preview/{strategy_id}")
def preview_optimization_space(
    strategy_id: str,
    payload: Optional[Dict[str, Any]] = Body(default=None),
) -> Dict[str, Any]:
    try:
        return optimization_service.preview_space(strategy_id=strategy_id, override_payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/campaigns")
def create_campaign(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    try:
        campaign = orchestrator.create(payload)
        return {"campaign": campaign}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/campaigns")
def list_campaigns(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
) -> Dict[str, Any]:
    return campaign_store.list_campaigns(limit=limit, offset=offset, status=status)


@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str) -> Dict[str, Any]:
    try:
        return {"campaign": campaign_store.get_campaign(campaign_id)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/pause")
def pause_campaign(campaign_id: str, payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    reason = str(payload.get("reason", "paused by user"))
    try:
        campaign = orchestrator.pause(campaign_id=campaign_id, reason=reason)
        return {"campaign": campaign}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/resume")
def resume_campaign(campaign_id: str, payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    reason = str(payload.get("reason", "resumed by user"))
    try:
        campaign = orchestrator.resume(campaign_id=campaign_id, reason=reason)
        return {"campaign": campaign}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/cancel")
def cancel_campaign(campaign_id: str, payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    reason = str(payload.get("reason", "cancelled by user"))
    try:
        campaign = orchestrator.cancel(campaign_id=campaign_id, reason=reason)
        return {"campaign": campaign}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/campaigns/{campaign_id}/iterations")
def campaign_iterations(
    campaign_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    try:
        return campaign_store.list_iterations(campaign_id=campaign_id, limit=limit, offset=offset)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/iterations")
def create_iteration_stub(campaign_id: str, payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    summary = str(payload.get("summary", ""))
    try:
        item = orchestrator.register_iteration_stub(campaign_id=campaign_id, summary=summary)
        return {"iteration": item}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/evaluate")
def evaluate_campaign_iteration(
    campaign_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    iteration_id = payload.get("iteration_id")
    metrics = payload.get("metrics")
    notes = str(payload.get("notes", ""))
    summary = str(payload.get("summary", ""))

    if not isinstance(metrics, dict):
        raise HTTPException(status_code=400, detail="metrics payload is required")

    try:
        if not iteration_id:
            created = orchestrator.register_iteration_stub(campaign_id=campaign_id, summary=summary)
            iteration_id = created["iteration_id"]

        result = orchestrator.evaluate_iteration(
            campaign_id=campaign_id,
            iteration_id=str(iteration_id),
            metrics=metrics,
            notes=notes,
        )
        return {"evaluation": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/critic")
def critic_campaign_iteration(
    campaign_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    iteration_id = payload.get("iteration_id")
    if not iteration_id:
        raise HTTPException(status_code=400, detail="iteration_id is required")

    try:
        proposal = orchestrator.critic_proposal(campaign_id=campaign_id, iteration_id=str(iteration_id))
        return {"critic": proposal}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/campaigns/{campaign_id}/loop-tick")
def campaign_loop_tick(
    campaign_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    metrics = payload.get("metrics")
    summary = str(payload.get("summary", ""))
    notes = str(payload.get("notes", ""))

    if not isinstance(metrics, dict):
        raise HTTPException(status_code=400, detail="metrics payload is required")

    try:
        out = orchestrator.loop_tick(
            campaign_id=campaign_id,
            metrics=metrics,
            summary=summary,
            notes=notes,
        )
        return out
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/campaigns/{campaign_id}/artifacts")
def campaign_artifacts(campaign_id: str) -> Dict[str, Any]:
    try:
        return campaign_store.list_artifacts(campaign_id=campaign_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/export/{campaign_id}/{target}")
def export_campaign(campaign_id: str, target: str) -> Dict[str, Any]:
    try:
        result = orchestrator.request_export(campaign_id=campaign_id, target=target)
        return {"export": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
