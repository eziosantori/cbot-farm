# Progress Tracker

## Update Rule
From now on, every completed implementation step must immediately update this file by:
- checking the task as complete (`[x]`)
- adding completion date (YYYY-MM-DD)
- adding a short outcome note

## Project Status
- Current phase: `M1 - Real Backtest Core (in progress)`
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
- [x] Add ATR-based stop/take-profit and trade log
  - Completed: 2026-02-10
  - Notes: Implemented ATR exits and structured per-trade logging in backtest details.
- [x] Separate bot definitions from engine (`bots/` + base class)
  - Completed: 2026-02-10
  - Notes: Added `BaseBotStrategy`, `bots/ema_cross_atr.py`, strategy registry, and pipeline strategy selection.
- [ ] Add robust IS/OOS walk-forward split logic
- [ ] Add per-market transaction cost profiles
- [ ] Add Backtrader parity validation step (cross-check core strategy outputs)

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
- [ ] Start M1.4: per-market transaction cost profiles

### Next
- [ ] Start M1.3: robust IS/OOS walk-forward split logic
- [ ] Start M1.5: Backtrader parity validation

### Blocked / Decisions Needed
- [ ] Finalize UI design system choice (minimal custom vs component library)

## Change Log
- 2026-02-10: Added initial UI implementation plan and formal tracker process.
- 2026-02-10: Added Backtrader parity milestone step.
- 2026-02-10: Completed ATR stop/take-profit + trade log task in M1.
- 2026-02-10: Completed strategy-engine separation with `bots/` and base class.
