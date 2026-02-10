# Progress Tracker

## Update Rule
From now on, every completed implementation step must immediately update this file by:
- checking the task as complete (`[x]`)
- adding completion date (YYYY-MM-DD)
- adding a short outcome note

## Project Status
- Current phase: `Planning / UI bootstrap pending`
- Last updated: `2026-02-10`

## Milestone Checklist

### M0 - Foundations (Completed)
- [x] Repository initialized and base docs created
  - Completed: 2026-02-10
  - Notes: Initial strategy/risk/opportunity docs in place.
- [x] Dukascopy ingestion integrated
  - Completed: 2026-02-10
  - Notes: `dukascopy-node` wired into pipeline, manifests generated.
- [x] Python codebase modularized
  - Completed: 2026-02-10
  - Notes: Migrated into `cbot_farm/` package.
- [x] Instrument validation utility added
  - Completed: 2026-02-10
  - Notes: `verify:instruments` script available.

### M1 - Real Backtest Core (In Progress)
- [x] Replace random stub with real CSV-based backtest
  - Completed: 2026-02-10
  - Notes: EMA cross backtest with real metrics integrated.
- [ ] Add ATR-based stop/take-profit and trade log
- [ ] Add robust IS/OOS walk-forward split logic
- [ ] Add per-market transaction cost profiles

### M2 - Web UI Phase 1 (Planned)
- [ ] Bootstrap backend (`FastAPI`) in `api/`
- [ ] Implement report reader service (`reports`, `ingest`)
- [ ] Implement API endpoints (`/runs`, `/ingest-manifests`, details)
- [ ] Bootstrap frontend (`React + Vite`) in `web/`
- [ ] Build dashboard tables (runs + ingestion)
- [ ] Build run/manifest detail pages
- [ ] Add charts for key metrics

### M3 - Reliability and Scale (Planned)
- [ ] Introduce SQLite index for reports
- [ ] Add pagination and filtering at API level
- [ ] Add report schema versioning and migration helpers
- [ ] Add smoke tests for API and UI routes

## Active Task Board

### Now
- [ ] Start M2.1: backend bootstrap (`api/`)

### Next
- [ ] Start M2.4: frontend bootstrap (`web/`)
- [ ] Start M2.5: dashboard tables

### Blocked / Decisions Needed
- [ ] Finalize UI design system choice (minimal custom vs component library)

## Change Log
- 2026-02-10: Added initial UI implementation plan and formal tracker process.
