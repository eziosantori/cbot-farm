# UI Phase 2 Roadmap

## Goal
Move from static run inspection to an operator console for strategy lifecycle management.

## Product Objectives
- Explore batch results with ratios and equity curves without opening raw JSON.
- Launch simulations from UI by editing strategy parameters.
- Track lifecycle state of each strategy/bot in a clear workflow.
- Prepare a UI-first entry point for strategy intake metadata (code writing remains terminal-driven).

## Milestones

### M2.8 Batch Analytics Console
- API
  - `GET /batches`
  - `GET /batches/{batch_id}` with enriched scenario details
  - stale-index fallback for `/runs` and `/ingest-manifests`
- UI
  - `/batches` list page with batch KPIs
  - `/batches/:batchId` scenario drill-down
  - ratios panel (`return`, `sharpe`, `max_dd`, `oos_degradation`)
  - equity curve for best run per scenario

### M2.9 Simulation Launcher
- API
  - launch simulation from selected baseline run or strategy profile
  - parameter override payload validation
  - result artifact creation and run registration
- UI
  - simulation form (market/symbol/timeframe/iterations + parameter overrides)
  - run trigger and progress/result surface
  - quick link to generated run details

### M2.10 Strategy Workflow Board
- Domain model
  - `draft` -> `research` -> `backtest` -> `candidate` -> `paper` -> `approved` -> `archived`
- API
  - list/update workflow state per strategy
  - audit trail on state changes
- UI
  - board/table of strategies with state, last run, key ratios, next action
  - guarded transitions (e.g. cannot move to `candidate` without minimum checks)

### M2.11 Strategy Intake UI (Metadata)
- UI form for:
  - strategy thesis
  - markets/timeframes targets
  - risk gates
  - notes/prompts
- Output
  - structured artifact under `docs/` or `reports/campaigns/` for terminal-based code generation flow

## Acceptance Criteria
- Batch analysis can be done entirely from UI.
- User can launch and compare simulations from UI without touching JSON files.
- Workflow status is visible and actionable for each strategy.
- UI data remains fresh after new runs are produced (no stale index confusion).
