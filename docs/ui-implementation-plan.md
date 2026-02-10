# UI Implementation Plan

## Goal
Build a simple web UI to visualize:
- backtest cycle outputs
- ingestion manifests
- run-level details and metrics

with an architecture that can grow into broader operational tooling.

## Scope (Phase 1)
- Read and display existing JSON reports from `reports/`.
- Dashboard view for cycle runs (table + quick filters).
- Dashboard view for ingestion manifests (table + status summary).
- Run detail page with key metrics and raw payload preview.
- Basic charts (return, drawdown, sharpe, OOS degradation).

## Proposed Architecture
- Backend: `FastAPI` (Python) in `api/`.
- Frontend: `React + Vite` in `web/`.
- Data source (initial): filesystem JSON (`reports/*.json`, `reports/ingest/*.json`).
- Data source (next): SQLite indexing for fast querying and pagination.

## API Design (Initial)
- `GET /health`
- `GET /runs`
  - query: `limit`, `offset`, `market`, `status`, `from`, `to`
- `GET /runs/{run_id}`
- `GET /ingest-manifests`
  - query: `limit`, `offset`, `status`, `from`, `to`
- `GET /ingest-manifests/{manifest_id}`

## Frontend Pages (Initial)
- `/` dashboard overview
  - KPI cards
  - latest runs table
  - latest ingestion table
- `/runs/:runId`
  - run metadata
  - metrics cards
  - chart panels
  - payload explorer
- `/ingestion/:manifestId`
  - summary cards
  - result table (ok/failed per symbol/timeframe)

## Milestones
1. Project bootstrap (`api/` + `web/`).
2. Read-model layer for reports.
3. Core API endpoints.
4. Dashboard UI (runs + ingestion).
5. Detail pages.
6. Chart integration and UX polish.
7. Optional SQLite index and pagination optimization.

## Technical Decisions
- Keep UI stateless on top of API-first design.
- Use typed schemas for report contracts.
- Keep report readers resilient to partial/legacy payloads.
- Add a service layer to decouple filesystem/SQLite backends.

## Risks / Notes
- JSON report schema may evolve: enforce versioning (`schema_version`) soon.
- Large report volume will require indexing (SQLite) for performance.
- Timezone handling should be explicit (UTC in API, localized in UI).

## Definition of Done (Phase 1)
- User can view latest runs and ingestion manifests from browser.
- User can open run/manifest detail without using CLI.
- Metrics/charts reflect actual report values.
- Error states are visible and understandable.
