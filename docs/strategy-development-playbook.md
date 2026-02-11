# Strategy Development Playbook

## Purpose
This document explains how to develop, test, evaluate, and promote a new strategy in the farm.
It is also the reference log to update at the end of each iteration.

## Scope
Use this workflow when you want to add a new strategy under `/Users/esantori/Documents/cbot-farm/bots` and run it through the cycle.

## Prerequisites
- Strategy specs available in `/Users/esantori/Documents/cbot-farm/docs/strategy-specs.md`.
- Data ingestion working for target market/timeframe.
- Backtest pipeline running (`python3 -m cbot_farm.cli ...`).

## Mandatory Rule (End Of Iteration)
At the end of every development iteration, update:
1. this file (`strategy-development-playbook.md`) in section `Iteration Log`
2. `/Users/esantori/Documents/cbot-farm/docs/progress-tracker.md`

## Standard Workflow

### Step 1 - Define Strategy Brief
- Name and `strategy_id`
- Market(s) and timeframe(s)
- Entry/exit logic
- Risk logic (stop, take, optional breakeven)
- Initial parameter space (`enabled/min/max/step/value`)
- Promotion gates (drawdown, sharpe, OOS degradation)

Deliverable:
- Add a short brief in this file under `Strategy Briefs`.

### Step 2 - Implement Bot Module
- Create a new file in `/Users/esantori/Documents/cbot-farm/bots`.
- Inherit from `BaseBotStrategy`.
- Implement required methods:
  - `sample_params`
  - `normalize_params`
  - `prepare_indicators`
  - `entry_signal`
  - `should_flip`
  - `risk_levels`
- Register strategy in `/Users/esantori/Documents/cbot-farm/bots/__init__.py`.

Deliverable:
- Strategy selectable with `python3 -m cbot_farm.cli --list-strategies`.

### Step 3 - Configure Optimization Space
- Add strategy parameter space in `/Users/esantori/Documents/cbot-farm/config/risk.json` under:
  - `optimization.parameter_space.<strategy_id>`
- Keep combinatorics under control (`max_combinations`).

Deliverable:
- Report includes `optimization.mode` with `source=parameter_space`.

### Step 4 - Run Development Backtests
- Start with one market + one timeframe.
- Use short and long windows (sanity + realistic period).
- Run multiple iterations.

Example:
```bash
python3 -m cbot_farm.cli --strategy <strategy_id> --skip-ingest --iterations 20 --markets forex --symbols EURUSD --timeframes 1h
```

Deliverable:
- Set of reports in `/Users/esantori/Documents/cbot-farm/reports`.

### Step 5 - Evaluate Quality
Evaluate at least:
- `total_return_pct`
- `max_drawdown_pct`
- `sharpe`
- `oos_degradation_pct`
- walk-forward summary in `backtest.walk_forward`

Decision:
- `iterate`: if one or more gates fail
- `promote_candidate`: if all gates pass consistently

### Step 6 - Promotion Candidate Review
Before production candidate flag:
- verify cost profile realism for target market
- verify stability across at least 2 independent periods
- verify no parameter overfitting patterns

Deliverable:
- Promotion note in `Iteration Log` with rationale.

## LLM Prompt Templates

### A) Generate New Strategy Plan
```text
You are a quantitative strategy engineer.
Design a strategy for {market} on {timeframe} with these constraints:
- Max drawdown target: {dd_target}%
- Must be interpretable and implementable in BaseBotStrategy
- Must include parameter ranges for optimization (enabled/min/max/step/value)
Output:
1) strategy thesis
2) entry/exit rules
3) risk model
4) parameter space table
5) failure modes and mitigations
```

### B) Generate Bot Implementation Draft
```text
Given this BaseBotStrategy interface and the strategy rules below,
produce Python code for /bots/{strategy_id}.py.
Rules:
{paste rules}
Constraints:
- deterministic logic
- explicit normalization of parameters
- no external dependencies beyond current project modules
Return only code.
```

### C) Analyze Backtest Results And Decide Next Iteration
```text
You are reviewing strategy iteration results.
Input JSON report:
{paste report payload}
Evaluate:
- pass/fail against gates (drawdown, sharpe, OOS degradation)
- likely overfit symptoms
- parameter changes for next iteration
Output:
1) decision: iterate/promote/reject
2) top 3 changes
3) risk notes
4) exact parameter-space update proposal
```

### D) Production Readiness Decision
```text
Based on these N iteration reports and walk-forward summaries,
assess if strategy {strategy_id} is ready for production candidate status.
Criteria:
- robust OOS behavior
- acceptable drawdown
- no fragile dependence on narrow parameter values
Output:
- verdict: ready/not-ready
- evidence table
- mandatory next checks
```

## Strategy Briefs

### Template
- `strategy_id`:
- Name:
- Markets:
- Timeframes:
- Thesis:
- Core indicators:
- Risk model:
- Initial gates:

## Iteration Log

### Template (copy for each iteration)
- Iteration ID:
- Date:
- Strategy ID:
- Market/Timeframe:
- Data window:
- Parameter set:
- Key metrics:
  - Return %:
  - Max DD %:
  - Sharpe:
  - OOS degradation %:
- Walk-forward summary:
- Decision: `iterate` / `promote_candidate` / `reject`
- Next action:

---

## First Entry (Current State)
- Iteration ID: `bootstrap-ema-cross-atr`
- Date: `2026-02-11`
- Strategy ID: `ema_cross_atr`
- Market/Timeframe: `forex / 1h`
- Data window: `latest available report-driven window`
- Parameter set: `from optimization.parameter_space.ema_cross_atr`
- Key metrics: `see latest reports in /reports`
- Walk-forward summary: `enabled and included in backtest output`
- Decision: `iterate`
- Next action: `Backtrader parity validation (M1.5)`
