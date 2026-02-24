# Progress Tracker

## Update Rule
From now on, every completed implementation step must immediately update this file by:
- ensuring unit tests for touched business logic are added/updated where applicable
- ensuring unit tests are passing before marking the step complete
- checking the task as complete (`[x]`)
- adding completion date (YYYY-MM-DD)
- adding a short outcome note
- updating `docs/strategy-development-playbook.md` (Iteration Log) when the step includes strategy development/backtest iterations


## Definition of Done Rule
A step can be marked as completed only if:
- implementation is merged in workspace
- relevant checks pass
- unit tests that provide business value are present and green (where applicable)

Recommended command:
- `npm run test:unit`

## Engineering Standards
- Follow Python best practices for maintainable backend code (clear module boundaries, explicit validation, typed interfaces when useful, testable functions).
- Follow React/TypeScript best practices for frontend code (typed data contracts, reusable components, predictable state flows, minimal side-effects).
- Prefer incremental, production-ready changes to reduce future refactor cost.

## Project Status
- Current phase: `M2 - Web UI Phase 2 (in progress)`
- Last updated: `2026-02-20`

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

### M2 - Web UI Platform (In Progress)
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

- [x] Add stale-index fallback for fresh run visibility in API reads
  - Completed: 2026-02-20
  - Notes: `/runs` and `/ingest-manifests` now fallback to filesystem reader when SQLite index is stale.
- [x] Add batch analytics endpoints and UI pages (`/batches`, `/batches/:batchId`)
  - Completed: 2026-02-20
  - Notes: Added batch list/detail APIs and TypeScript pages with best-run ratio cards and equity curves.
- [x] Add simulation launcher from UI (parameter override + run trigger)
  - Completed: 2026-02-20
  - Notes: Added `/simulations` page plus `/simulations/options` and `/simulations/run` APIs with parameter override support and run link output.
- [x] Add strategy workflow board (state machine + transitions)
  - Completed: 2026-02-24
  - Notes: Added `/strategy-workflow` APIs and `/workflow` UI with guarded state transitions and last-run context.
- [ ] Add strategy intake UI for metadata/prompt capture


### M3 - Reliability and Scale (Planned)
- [x] Introduce SQLite index for reports
  - Completed: 2026-02-18
  - Notes: Added `api/report_index.py` with rebuild/status/query support and wired API fallback to SQLite index for runs/manifests.
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
- [x] Integrate evaluator/critic loop with stop rules in orchestrator
  - Completed: 2026-02-18
  - Notes: Added score-based evaluator, critic proposals, and stop criteria handling (`max_loops`, `max_no_improve_loops`) with new campaign APIs.
- [x] Run controlled optimization campaign on S1 (`ema_cross_atr`) across selected markets
  - Completed: 2026-02-19
  - Notes: Executed pilot on `forex/EURUSD/1h`, `indices/NAS100/1h`, `commodities/XAUUSD/1h`; stored summary artifact in `reports/campaigns/cmp_b2659f3c8e97/artifacts/pilot_m44_summary.json`.
- [x] Measure loop quality (stability, convergence, OOS degradation trend)
  - Completed: 2026-02-20
  - Notes: Computed loop stability and convergence signals from pilot outputs; no robust convergence detected and OOS degradation remained above gates.
- [x] Produce validation report and go/no-go criteria for scaling to other strategies
  - Completed: 2026-02-20
  - Notes: Added `docs/m44-validation-report.md` with criteria matrix and verdict `no-go` for scaling at current state.

### M5 - Strategy Rollout From Specs (Planned)
- [ ] Implement S1 Trend EMA Breakout as production bot module
- [ ] Implement S2 Mean Reversion Bollinger RSI as production bot module
- [ ] Implement S3 Session Momentum as production bot module
- [ ] Implement S4 Volatility Contraction Expansion as production bot module
- [ ] Run baseline backtests for all S1-S4 and publish comparison table

## Active Task Board

### Now
- [ ] Start M2.11: strategy intake UI metadata flow

### Next
- [ ] Start M3.2: pagination and filtering optimizations on SQLite paths
- [ ] Start exporter parity checks (`ctrader`, `pine`)
- [ ] Resume M5.1: implement S1 Trend EMA Breakout as production bot module

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

- 2026-02-18: Completed M3.1 SQLite report index and API integration.

- 2026-02-18: Adopted SQLAlchemy ORM for report index service.

- 2026-02-18: Migrated workspace to pnpm + Volta pinned toolchain.

- 2026-02-18: Completed M4.3 evaluator/critic integration with stop rules.

- 2026-02-19: Completed M4.4 controlled pilot campaign on S1 across forex/indices/commodities.
- 2026-02-20: Completed M4.5 loop quality measurement and M4.6 validation report with no-go verdict.
- 2026-02-20: Standardized documentation references to workspace-relative paths.
- 2026-02-20: Added RSI reinforcement and ATR volatility filter to `ema_cross_atr`; fixed EMA/ATR core parameters for initial test phase.

- 2026-02-20: Added UI Phase 2 roadmap for batch analytics, simulation launcher, and workflow board.
- 2026-02-20: Completed M2.8 slice with batch analytics pages and stale-index fallback behavior.

- 2026-02-20: Completed M2.9 simulation launcher (API + UI) with manual parameter override flow.

- 2026-02-24: Completed M2.10 strategy workflow board (API + UI) with guarded transitions.
