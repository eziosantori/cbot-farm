# Strategy Development Playbook

## Purpose
This document explains how to develop, test, evaluate, and promote a new strategy in the farm.
It is also the reference log to update at the end of each iteration.

## Scope
Use this workflow when you want to add a new strategy under `bots` and run it through the cycle.

## Prerequisites
- Strategy specs available in `docs/strategy-specs.md`.
- Data ingestion working for target market/timeframe.
- Backtest pipeline running (`python3 -m cbot_farm.cli ...`).

## Mandatory Rule (End Of Iteration)
At the end of every development iteration, update:
1. this file (`strategy-development-playbook.md`) in section `Iteration Log`
2. `docs/progress-tracker.md`

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
- Create a new file in `bots`.
- Inherit from `BaseBotStrategy`.
- Implement required methods:
  - `sample_params`
  - `normalize_params`
  - `prepare_indicators`
  - `entry_signal`
  - `should_flip`
  - `risk_levels`
- Register strategy in `bots/__init__.py`.

Deliverable:
- Strategy selectable with `python3 -m cbot_farm.cli --list-strategies`.

### Step 3 - Configure Optimization Space
- Add strategy parameter space in `config/risk.json` under:
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
- Set of reports in `reports`.

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

### SuperTrend + RSI Momentum (Bot 2)
- `strategy_id`: `supertrend_rsi`
- Name: SuperTrend + RSI Momentum
- Markets: Forex, Crypto, Indices, Equities, Commodities (all volatile markets)
- Timeframes: 5m, 15m, 1h (optimal: 15m-1h)
- Thesis: Capture breakout and momentum by combining trend direction (SuperTrend), momentum timing (RSI), trend strength filter (ADX), and directional bias (EMA). Avoid choppy markets and false breakouts.
- Core indicators:
  - SuperTrend (period: 8-14, mult: 2.0-4.0) - Trend direction + entry trigger on reversal
  - RSI (period: 14) - Momentum filter (>50 for long, <50 for short)
  - ADX (period: 14, min: 15-25) - Trend strength filter to avoid ranging markets
  - EMA (period: 150-250) - Directional bias filter
  - ATR (period: 14) - Dynamic stop/take sizing
- Risk model:
  - Stop Loss: Entry ± (ATR × 1.5-3.0)
  - Take Profit: Entry ± (ATR × 2.0-5.0)
  - Exit: SuperTrend reversal (hard exit) or SL/TP
  - No breakeven in v1 (simplified)
- Initial gates:
  - Max Drawdown: ≤12% (strategy), ≤10% (portfolio)
  - Min Sharpe: ≥1.2
  - OOS Degradation: ≤30%

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

---

## Iteration 1: SuperTrend + RSI Initial Validation
- Iteration ID: `supertrend_rsi_validation_v1`
- Date: `2026-02-12`
- Strategy ID: `supertrend_rsi`
- Market/Timeframe: `forex/EURUSD/1h, indices/NAS100/1h`
- Data window: `2024-01-01 to 2024-02-15 (1080 bars EURUSD, NAS100 similar)`
- Parameter set: `grid search from parameter_space.supertrend_rsi (5 iterations each)`
- Key metrics:
  - **EURUSD**: Return: -0.17% to -1.12%, Sharpe: -0.79 to -4.11, DD: 0.28-1.12%, Trades: 7, WinRate: 43%
  - **NAS100**: Return: -6.12% to +0.16%, Sharpe: -1.57 to +0.07, DD: 2.61-7.83%, Trades: 37-63, WinRate: 30-52%
  - Best config (NAS100 iter4): st_period=8, st_mult=2.5, ema=150, min_adx=20 → +0.16% return, 52% WR, 2.61% DD
- Walk-forward summary:
  - EURUSD: avg_oos_return -0.03%, 0% OOS positive windows, 100% degradation
  - NAS100: avg_oos_degradation 87-180%, mostly negative OOS windows
- Decision: `iterate`
- Next action: 
  - **Issue**: OOS degradation >100%, poor risk/reward (winners don't compensate losers)
  - **Root cause**: Possible overfitting, insufficient TP/SL ratio optimization, or exit logic too aggressive (SuperTrend flip)
  - **Proposed fixes**: 
    1. Expand TP/SL multiplier ranges (test atr_mult_take up to 8-10x)
    2. Relax filters (reduce min_adx min to 10, test without EMA filter)
    3. Test on more volatile periods or additional symbols
    4. Consider alternative exit: partial SuperTrend flip (allow re-entry) vs hard exit
  - **Next iteration**: Run 20-50 iterations on NAS100 1h with expanded parameter space focusing on risk/reward optimization


## Iteration 2: Backtrader Parity Baseline (M1.5)
- Iteration ID: `ema_cross_atr_backtrader_parity_v1`
- Date: `2026-02-16`
- Strategy ID: `ema_cross_atr`
- Market/Timeframe: `forex/EURUSD/1h`
- Data window: `2022-01-01 to 2024-12-31`
- Parameter set: `candidate 0 from optimization.parameter_space.ema_cross_atr`
- Key metrics:
  - Engine: Return -24.76%, Sharpe -4.07, Max DD 25.02%, OOS degradation 100%
  - Backtrader: Return -15.49%, Sharpe -2.14, Max DD 15.74%, OOS degradation 100%
  - Trade count ratio: 0.8458
- Walk-forward summary: `engine walk-forward enabled; parity script compares aggregate outputs`
- Decision: `iterate`
- Next action:
  - Keep `strict` parity as hard gate for future engine alignment work
  - Use `directional` parity as baseline validation gate in current phase
  - Proceed with M2 UI/API implementation and expose parity status in dashboard

## Iteration 3: M4.4 Controlled Pilot Campaign
- Iteration ID: `ema_cross_atr_m44_pilot_v1`
- Date: `2026-02-19`
- Strategy ID: `ema_cross_atr`
- Market/Timeframe: `forex/EURUSD/1h, indices/NAS100/1h, commodities/XAUUSD/1h`
- Data window:
  - EURUSD: `2022-01-01 to 2024-12-31`
  - NAS100: `2024-01-01 to 2024-12-31`
  - XAUUSD: `2024-01-01 to 2024-01-02`
- Parameter set: `optimization.parameter_space.ema_cross_atr`, 2 iterations per scenario, best report per scenario used in loop tick
- Key metrics:
  - EURUSD best: Return `-21.93%`, Sharpe `-2.96`, Max DD `22.16%`, OOS degradation `100.0%`
  - NAS100 best: Return `-12.35%`, Sharpe `-3.12`, Max DD `12.57%`, OOS degradation `157.51%`
  - XAUUSD best: Return `-0.03%`, Sharpe `-19.95`, Max DD `0.03%`, OOS degradation `100.0%`
- Walk-forward summary: `negative OOS behavior across all tested scenarios; no promoted candidate`
- Decision: `iterate`
- Next action:
  - Run M4.5 loop quality measurement with convergence trend analysis over longer windows.
  - Expand commodities datasets before using them as quality signals (XAUUSD sample is too short).
  - Add a unique report id generator to avoid same-second filename collisions in CLI runs.
- Artifacts:
  - Campaign summary: `reports/campaigns/cmp_b2659f3c8e97/artifacts/pilot_m44_summary.json`
  - Pilot run snapshots: `reports/m44_pilot/`

## Iteration 4: M4.5 Loop Quality Review
- Iteration ID: `ema_cross_atr_m44_quality_review_v1`
- Date: `2026-02-20`
- Strategy ID: `ema_cross_atr`
- Market/Timeframe: `forex/EURUSD/1h, indices/NAS100/1h, commodities/XAUUSD/1h`
- Data window: `as captured in reports/m44_pilot/`
- Parameter set: `best-per-scenario from m44 pilot summary`
- Key metrics:
  - Loop decisions: `iterate=2`, `reject_stop=1`
  - Stability: `avg_score=36.9698`, `spread=31.2282`
  - OOS degradation trend: `100.0%`, `157.51%`, `100.0%`
- Walk-forward summary: `no robust convergence and no gate-compliant OOS behavior`
- Decision: `reject`
- Next action:
  - Keep strategy in refinement mode.
  - Re-run pilot after dataset expansion and CLI run-id uniqueness fix.
- Artifacts:
  - Validation report: `docs/m44-validation-report.md`
  - Source summary: `reports/campaigns/cmp_b2659f3c8e97/artifacts/pilot_m44_summary.json`
