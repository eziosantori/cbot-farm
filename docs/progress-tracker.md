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
- [x] Add robust IS/OOS walk-forward split logic
  - Completed: 2026-02-11
  - Notes: Added rolling walk-forward windows (60/20/20 IS/Validation/OOS) with aggregated degradation metrics in report output.
- [x] Add per-market transaction cost profiles
  - Completed: 2026-02-10
  - Notes: Added fee/slippage profiles in `config/risk.json` and market-aware cost application in backtest reports.
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

### M4 - Feedback Loop Validation (Planned)
- [ ] Define evaluation protocol for strategy iteration loop (inputs, gates, outputs)
- [ ] Run controlled optimization campaign on S1 (`ema_cross_atr`) across selected markets
- [ ] Measure loop quality (stability, convergence, OOS degradation trend)
- [ ] Produce validation report and go/no-go criteria for scaling to other strategies

### M5 - Strategy Rollout From Specs (Planned)
- [ ] Implement S1 Trend EMA Breakout as production bot module
- [ ] Implement S2 Mean Reversion Bollinger RSI as production bot module
- [ ] Implement S3 Session Momentum as production bot module
- [ ] Implement S4 Volatility Contraction Expansion as production bot module
- [ ] Run baseline backtests for all S1-S4 and publish comparison table

## Active Task Board

### Now
- [ ] Start M1.5: Backtrader parity validation

### Next
- [ ] Start M2.1: backend bootstrap (`api/`)
- [ ] Start M2.4: frontend bootstrap (`web/`)

### Blocked / Decisions Needed
- [ ] Finalize UI design system choice (minimal custom vs component library)

## Change Log
- 2026-02-10: Added initial UI implementation plan and formal tracker process.
- 2026-02-10: Added Backtrader parity milestone step.
- 2026-02-10: Completed ATR stop/take-profit + trade log task in M1.
- 2026-02-10: Completed strategy-engine separation with `bots/` and base class.
- 2026-02-10: Completed per-market transaction cost profiles.
- 2026-02-10: Added milestones for feedback-loop validation and strategy-by-strategy rollout.

- 2026-02-11: Completed robust walk-forward IS/Validation/OOS logic.
