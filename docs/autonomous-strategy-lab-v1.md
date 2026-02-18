# Autonomous Strategy Lab v1 Blueprint

## Objective
Build an autonomous strategy factory that can:
1. generate a strategy draft from one or more prompts,
2. implement and run large backtest/optimization campaigns,
3. self-analyze results and iterate code/params in a loop for hours/days,
4. output a promotion decision with full traceability,
5. export validated strategies to external targets (cTrader C#, TradingView Pine Script).

## Scope v1
- Single orchestrated campaign at a time.
- Strategy-first focus on one pilot (`ema_cross_atr`) then expansion.
- Batch, asynchronous loops (not low-latency live trading).
- Deterministic and reproducible runs.

## Non-Goals v1
- Live order execution.
- Full broker integration.
- Fully automatic production deployment.

## Target Workflow
1. User creates a campaign from prompts + constraints.
2. LLM synthesizes a `strategy brief` and implementation diff.
3. Engine executes market/timeframe/parameter combinations.
4. Evaluator ranks outcomes (IS/OOS, drawdown, stability, degradation).
5. Critic proposes refinements (logic or parameter space changes).
6. Orchestrator retries until stop criteria or time budget is reached.
7. Final report issues verdict: `promote_candidate`, `iterate`, or `reject`.
8. Optional exporters generate cTrader C# and Pine Script artifacts.

## System Components
- `Prompt Intake Service`
  - Stores campaign prompt(s), constraints, target markets/timeframes, risk gates.
- `Strategy Spec Compiler`
  - Converts natural-language intent into a structured internal strategy contract.
- `Codegen Worker`
  - Produces/updates bot code under `bots/` plus test notes.
- `Campaign Runner`
  - Executes backtest and optimization matrix over selected markets/timeframes.
- `Evaluator`
  - Computes ranking score and robustness diagnostics.
- `Critic`
  - Generates next-iteration edits to logic and/or parameter-space bounds.
- `Orchestrator`
  - State machine coordinating loop steps and retries.
- `Exporter`
  - Converts normalized strategy contract into target code (C#, Pine).

## Canonical Strategy Contract (Required)
Use a normalized JSON/YAML contract as the single source of truth before exporter generation.

Minimum fields:
- `strategy_id`
- `thesis`
- `markets[]`
- `timeframes[]`
- `indicators[]` (name + parameters)
- `entry_rules[]`
- `exit_rules[]`
- `risk_model` (stop/take/breakeven/sizing)
- `optimization_space` (`enabled/min/max/step/value`)
- `gates` (max drawdown, min sharpe, max OOS degradation)
- `version`

## Orchestrator State Machine
- `queued`
- `brief_generated`
- `code_generated`
- `campaign_running`
- `campaign_evaluated`
- `refinement_planned`
- `completed`
- `failed`
- `paused`

Transitions are persisted with timestamps and reason codes.

## Loop Stop Criteria
Hard stops:
- max wall-clock budget exceeded,
- max token/cost budget exceeded,
- max consecutive failed executions,
- risk gate breach policy triggered.

Soft stops:
- no score improvement after `N` loops,
- metric volatility indicates non-convergence,
- overfitting signal above threshold.

## Scoring and Ranking (v1)
Composite score (example):
- return quality: 35%
- drawdown control: 30%
- Sharpe/risk-adjusted return: 20%
- OOS degradation and walk-forward stability: 15%

Mandatory pass gates:
- `max_drawdown_pct <= gate`
- `sharpe >= gate`
- `oos_degradation_pct <= gate`

## Safety Guardrails
- Sandbox code generation and execution.
- Allowlist modules for generated code.
- Max file-change footprint per iteration.
- Mandatory syntax checks and backtest health checks.
- Full audit log: prompt, generated patch, metrics, decision rationale.

## API Surface (planned)
- `POST /campaigns`
- `GET /campaigns`
- `GET /campaigns/{campaign_id}`
- `POST /campaigns/{campaign_id}/pause`
- `POST /campaigns/{campaign_id}/resume`
- `POST /campaigns/{campaign_id}/cancel`
- `GET /campaigns/{campaign_id}/iterations`
- `GET /campaigns/{campaign_id}/artifacts`
- `POST /export/{campaign_id}/{target}` (`ctrader`, `pine`)

## Data Artifacts
- `reports/campaigns/<campaign_id>/campaign.json`
- `reports/campaigns/<campaign_id>/iterations/iter_<n>.json`
- `reports/campaigns/<campaign_id>/patches/iter_<n>.diff`
- `reports/campaigns/<campaign_id>/exports/` (C#, Pine)

## Export Strategy (cTrader / Pine)
Phase E1:
- Implement exporter from canonical contract for simple indicator/rule subset.
- Include unsupported-feature diagnostics per target.

Phase E2:
- Add richer constructs (multi-timeframe conditions, advanced risk controls).
- Add regression parity checks vs Python engine on shared datasets.

## Observability
Track at campaign and iteration level:
- duration, retries, cost usage,
- best score trajectory,
- gate pass/fail counts,
- convergence status,
- export readiness.

## Milestones
- `M4.1` Protocol and contracts finalized (this document + schema draft).
- `M4.2` Orchestrator v1 and campaign persistence.
- `M4.3` Evaluator/Critic loop with stop rules.
- `M4.4` Pilot campaign on `ema_cross_atr`.
- `M4.5` Exporter v1 for cTrader and Pine.

## Definition of Done (M4)
- Autonomous loop executes unattended for configured budget.
- System outputs explainable decision and best candidate.
- All iterations are auditable and reproducible.
- At least one strategy exported to both cTrader C# and Pine with documented limitations.
