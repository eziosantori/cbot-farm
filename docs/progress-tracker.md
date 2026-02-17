# Progress Tracker

## Update Rule
From now on, every completed implementation step must immediately update this file by:
- ensuring unit tests for touched business logic are added/updated where applicable
- ensuring unit tests are passing before marking the step complete
- checking the task as complete (`[x]`)
- adding completion date (YYYY-MM-DD)
- adding a short outcome note
- updating `/Users/esantori/Documents/cbot-farm/docs/strategy-development-playbook.md` (Iteration Log) when the step includes strategy development/backtest iterations


## Definition of Done Rule
A step can be marked as completed only if:
- implementation is merged in workspace
- relevant checks pass
- unit tests that provide business value are present and green (where applicable)

Recommended command:
- `npm run test:unit`

## Project Status
- Current phase: `M2 - Web UI Phase 1 (in progress)`
- Last updated: `2026-02-17`

## Milestone Checklist

### M0 - Foundations (Completed)
- [x] Add strategy development playbook for new bots
  - Completed: 2026-02-11
  - Notes: Added end-to-end guide and LLM prompt templates in `docs/strategy-development-playbook.md`.
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
- [x] Add configurable optimization parameter space (`enabled/min/max/step/value`)
  - Completed: 2026-02-11
  - Notes: Added parameter-space engine and strategy config in `config/risk.json`; cycle now iterates candidates instead of simple incremental params.
- [x] Add Backtrader parity validation step (cross-check core strategy outputs)
  - Completed: 2026-02-16
  - Notes: Added `scripts/backtrader_parity.py` with strict + directional parity statuses; latest run reported `directional_pass` for EMA Cross ATR on EURUSD 1h.

### M2 - Web UI Phase 1 (In Progress)
- [x] Bootstrap backend (`FastAPI`) in `api/`
  - Completed: 2026-02-17
  - Notes: Added `api/main.py` with base FastAPI app and health endpoint.
- [x] Implement report reader service (`reports`, `ingest`)
  - Completed: 2026-02-17
  - Notes: Added `api/report_reader.py` for run and manifest listing/detail reads from filesystem JSON.
- [x] Implement API endpoints (`/runs`, `/ingest-manifests`, details)
  - Completed: 2026-02-17
  - Notes: Exposed `/runs`, `/runs/{run_id}`, `/ingest-manifests`, `/ingest-manifests/{manifest_id}` with pagination filters.
- [x] Bootstrap frontend (`React + Vite`) in `web/`
  - Completed: 2026-02-17
  - Notes: Added `web/` app with dashboard skeleton and API consumption for runs/manifests.
- [x] Build dashboard tables (runs + ingestion)
  - Completed: 2026-02-17
  - Notes: Added initial dashboard table rendering in `web/src/pages/DashboardPage.tsx` for latest runs and ingest manifests.
- [x] Build run/manifest detail pages
  - Completed: 2026-02-17
  - Notes: Added routed detail pages in `web/src/pages/RunDetailPage.tsx` and `web/src/pages/ManifestDetailPage.tsx`.
- [x] Build optimization parameter panel (`enabled/min/max/step/value`)
  - Completed: 2026-02-17
  - Notes: Added optimization API endpoints and `/optimization` TypeScript UI page with preview/save flow over `config/risk.json`.
- [x] Add charts for key metrics
  - Completed: 2026-02-17
  - Notes: Added dashboard trend chart and run-detail metric bar chart in `web/src/components/MetricsChart.tsx` and integrated into pages.
- [x] Migrate web frontend from JavaScript to TypeScript
  - Completed: 2026-02-17
  - Notes: Converted `web/src` to `.ts/.tsx`, added TS config and typecheck script, and validated build + routing pages.

### M3 - Reliability and Scale (Planned)
- [ ] Introduce SQLite index for reports
- [ ] Add pagination and filtering at API level
- [ ] Add report schema versioning and migration helpers
- [ ] Add smoke tests for API and UI routes

### M4 - Feedback Loop Validation (Planned)
- [x] Define evaluation protocol for strategy iteration loop (inputs, gates, outputs)
  - Completed: 2026-02-17
  - Notes: Added `docs/autonomous-strategy-lab-v1.md` with architecture, state machine, stop criteria, and artifact/API blueprint.
- [x] Implement orchestrator v1 and campaign persistence
  - Completed: 2026-02-17
  - Notes: Added `api/campaigns.py` and new campaign APIs (`/campaigns`, state actions, iterations, artifacts, export request stub).
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
- [ ] Start M3.1: SQLite report index

### Next
- [ ] Start M4.3: evaluator/critic loop integration
- [ ] Start M4.4: controlled pilot campaign on S1 (`ema_cross_atr`)
- [ ] Start M2.8: dashboard filtering and pagination UX

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
- 2026-02-11: Added and completed configurable optimization parameter-space backend support.

- 2026-02-11: Added strategy development playbook with iteration log workflow.

- 2026-02-16: Completed Backtrader parity validation baseline (strict + directional).

- 2026-02-17: Bootstrapped monorepo UI/API layout with FastAPI + React/Vite.

- 2026-02-17: Migrated web app to TypeScript with typed API hooks/components.

- 2026-02-17: Added M4 autonomous strategy lab blueprint and protocol.

- 2026-02-17: Implemented M4.2 orchestrator v1 and campaign persistence APIs.

- 2026-02-17: Enforced unit-test quality gate for step completion.

- 2026-02-17: Completed M2.6 optimization parameter panel (API + UI).

- 2026-02-17: Completed M2.7 key metrics charts in web UI.
