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

### Terminal-First Intake Workflow
Use this workflow when the idea already exists as an intake artifact and the implementation loop is executed from terminal with Codex.

1. Identify the intake artifact under `reports/strategy_intake/`.
2. Read the thesis, target universe, and risk gates.
3. Reduce the first validation scope to datasets that are actually present locally.
4. Convert the intake into:
   - a strategy brief in this document
   - a canonical bot module in `bots/`
   - a parameter space entry in `config/risk.json`
   - unit tests for the touched strategy logic
5. Run a first controlled validation on 1-2 scenarios.
6. Evaluate gates and log the result in `Iteration Log`.
7. Decide one of:
   - `iterate`
   - `reject`
   - `promote_candidate`

Recommended operator prompt:
```text
Use intake <intake_id>.
Read the artifact, convert it into a canonical bot module, add tests and optimization space, run a first validation on locally available datasets, and return an explicit decision: iterate, reject, or promote_candidate.
```

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

### Momentum Rider
- `strategy_id`: `momentum_rider`
- Name: Momentum Rider
- Markets: Forex, Crypto, Equities, Indices
- Timeframes: 1h
- Thesis: Trade directional momentum only when price is already aligned with the fast/slow EMA stack, then require MACD crossover confirmation and RSI participation before entry. Use ATR-based stop and take-profit to normalize risk across markets.
- Core indicators:
  - EMA fast / EMA slow trend stack
  - MACD line / signal crossover as momentum trigger
  - RSI gate to confirm participation strength
  - ATR for volatility-scaled exits
- Risk model:
  - Stop Loss: Entry ± ATR x `atr_mult_stop`
  - Take Profit: Entry ± ATR x `atr_mult_take`
  - Flip exit: allow reversal only when the opposite full entry condition is satisfied
- Initial gates:
  - Max Drawdown: ≤12%
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

---

## Iteration 3: Intake-Driven Workflow Validation (`momentum_rider`)
- Iteration ID: `momentum_rider_validation_v1`
- Date: `2026-03-17`
- Strategy ID: `momentum_rider`
- Market/Timeframe: `forex/EURUSD/1h, indices/NAS100/1h`
- Data window:
  - `EURUSD 1h`: `2022-01-01` to `2024-12-31`
  - `NAS100 1h`: `2024-01-01` to `2024-12-31`
- Parameter set:
  - Search space from `optimization.parameter_space.momentum_rider`
  - First validation scope reduced to locally available high-quality datasets from the intake universe
  - 8 iterations per scenario
- Key metrics:
  - Best `EURUSD 1h` run: `reports/run_20260317_114643_2.json`
    - Return %: `-4.41`
    - Max DD %: `4.97`
    - Sharpe: `-0.54`
    - OOS degradation %: `124.64`
    - Trades: `149`
  - Best `NAS100 1h` run: `reports/run_20260317_114702_2.json`
    - Return %: `2.90`
    - Max DD %: `5.33`
    - Sharpe: `0.51`
    - OOS degradation %: `144.87`
    - Trades: `55`
  - Best shared parameter pattern in this sweep:
    - `ema_fast=15`
    - `ema_slow=60`
    - `macd_signal=6`
    - `rsi_gate=60`
    - `atr_mult_stop=2.5`
    - `atr_mult_take=4.0`
- Walk-forward summary:
  - Drawdown remained inside the intake gate on both scenarios
  - Sharpe failed the gate on both scenarios
  - OOS degradation was far above the intake gate on both scenarios
  - EURUSD remained structurally weak; NAS100 showed some profitability but still not robust enough
- Decision: `iterate`
- Next action:
  - Add a stronger regime filter before entry to reduce noisy momentum crosses
  - Prefer markets with confirmed local data coverage before widening the intake universe
  - Run a second refinement pass on `EURUSD 1h` and `NAS100 1h` before any workflow transition above `research/backtest`

---

## Iteration 4: `momentum_rider` Regime Filter Refinement
- Iteration ID: `momentum_rider_validation_v2`
- Date: `2026-03-17`
- Strategy ID: `momentum_rider`
- Market/Timeframe: `forex/EURUSD/1h, indices/NAS100/1h`
- Data window:
  - `EURUSD 1h`: `2022-01-01` to `2024-12-31`
  - `NAS100 1h`: `2024-01-01` to `2024-12-31`
- Parameter set:
  - Added regime filters:
    - MACD zero-line alignment
    - `min_adx`
    - `atr_vol_ratio_max`
  - Expanded search controls now include:
    - `rsi_gate`
    - `min_adx`
    - `atr_vol_ratio_max`
    - `atr_mult_stop`
    - `atr_mult_take`
  - 24 iterations per scenario
- Key metrics:
  - Best `EURUSD 1h` run: `reports/run_20260317_131315_256472_2.json`
    - Return %: `-0.15`
    - Max DD %: `4.34`
    - Sharpe: `0.00`
    - OOS degradation %: `81.68`
    - Trades: `112`
  - Best `NAS100 1h` run: `reports/run_20260317_131325_727565_12.json`
    - Return %: `5.50`
    - Max DD %: `3.06`
    - Sharpe: `1.15`
    - OOS degradation %: `90.85`
    - Trades: `44`
  - Best `NAS100 1h` parameter set:
    - `ema_fast=15`
    - `ema_slow=50`
    - `macd_signal=6`
    - `rsi_gate=60`
    - `min_adx=22`
    - `atr_vol_ratio_max=1.8`
    - `atr_mult_stop=2.5`
    - `atr_mult_take=2.5`
- Walk-forward summary:
  - `EURUSD 1h`: materially improved from v1, but still not profitable and still too weak OOS
  - `NAS100 1h`: stronger return, lower drawdown, lower trade count, and Sharpe close to gate
  - OOS degradation remains the blocking metric on both scenarios
- Decision: `iterate`
- Next action:
  - Keep `NAS100 1h` as the lead validation scenario
  - Reduce `EURUSD 1h` priority until a more robust regime or session filter is added
  - Add one more selective filter layer before considering a workflow move to `candidate`

---

## Iteration 5: `momentum_rider` Extension Filter Probe
- Iteration ID: `momentum_rider_validation_v3`
- Date: `2026-03-17`
- Strategy ID: `momentum_rider`
- Market/Timeframe: `indices/NAS100/1h`
- Data window: `2024-01-01` to `2024-12-31`
- Parameter set:
  - Added temporary `max_ema_gap_atr` filter to avoid entries too far from the fast EMA
  - 24 iterations on the lead scenario only
- Key metrics:
  - Best run: `reports/run_20260317_131705_110011_15.json`
    - Return %: `1.31`
    - Max DD %: `2.19`
    - Sharpe: `0.60`
    - OOS degradation %: `114.74`
    - Trades: `26`
- Walk-forward summary:
  - The extension filter reduced trade count and drawdown further
  - It also reduced return and Sharpe materially versus v2
  - OOS degradation remained unacceptable
- Decision: `reject`
- Next action:
  - Keep v2 as the active baseline
  - Do not keep `max_ema_gap_atr` in the production parameter space
  - Explore a more structural filter next (session filter or higher-timeframe regime context)

---

## Iteration 6: `momentum_rider` Session Filter Probe
- Iteration ID: `momentum_rider_validation_v4`
- Date: `2026-03-17`
- Strategy ID: `momentum_rider`
- Market/Timeframe: `indices/NAS100/1h`
- Data window: `2024-01-01` to `2024-12-31`
- Parameter set:
  - Added temporary UTC entry session filter with:
    - `session_start_hour`
    - `session_end_hour`
  - 24 iterations on the lead scenario only
- Key metrics:
  - Best score run: `reports/run_20260317_132225_061716_14.json`
    - Return %: `1.16`
    - Max DD %: `3.36`
    - Sharpe: `0.35`
    - OOS degradation %: `102.09`
    - Trades: `32`
  - Best Sharpe run: `reports/run_20260317_132224_726816_9.json`
    - Return %: `2.06`
    - Max DD %: `5.92`
    - Sharpe: `0.43`
    - OOS degradation %: `103.05`
    - Trades: `23`
- Walk-forward summary:
  - The session filter reduced trade count materially
  - Return, Sharpe, and OOS behavior all remained worse than the v2 baseline
  - The best v2 `NAS100 1h` result is still stronger on every meaningful promotion metric
- Decision: `reject`
- Next action:
  - Keep v2 as the active baseline
  - Do not keep session filter parameters in the active search space
  - If we continue, the next structural experiment should use higher-timeframe context rather than narrower intraday timing

---

## Iteration 7: `momentum_rider` Higher-Timeframe Context Probe
- Iteration ID: `momentum_rider_validation_v5`
- Date: `2026-03-17`
- Strategy ID: `momentum_rider`
- Market/Timeframe: `indices/NAS100/1h`
- Data window: `2024-01-01` to `2024-12-31`
- Parameter set:
  - Added temporary higher-timeframe regime context:
    - completed `4h` close
    - completed `4h EMA(20)`
  - Longs allowed only when `4h close > 4h EMA`
  - Shorts allowed only when `4h close < 4h EMA`
  - 24 iterations on the lead scenario only
- Key metrics:
  - Best run: `reports/run_20260317_132820_410924_12.json`
    - Return %: `5.50`
    - Max DD %: `3.06`
    - Sharpe: `1.15`
    - OOS degradation %: `90.85`
    - Trades: `44`
- Walk-forward summary:
  - The best result matched the v2 baseline exactly
  - The higher-timeframe regime filter did not improve any promotion metric on the lead scenario
  - Additional complexity is not justified without measurable improvement
- Decision: `reject`
- Next action:
  - Keep v2 as the active baseline
  - Do not keep higher-timeframe regime parameters in the active search space
  - If we continue, the next experiments should target exit logic or more explicit OOS robustness rules rather than extra entry filters

---

## Iteration 8: `momentum_rider` Dynamic Exit Probe
- Iteration ID: `momentum_rider_validation_v6`
- Date: `2026-03-17`
- Strategy ID: `momentum_rider`
- Market/Timeframe: `indices/NAS100/1h`
- Data window: `2024-01-01` to `2024-12-31`
- Parameter set:
  - Added temporary runtime exit management using:
    - break-even trigger in ATR units
    - ATR trailing stop anchored to fast EMA
  - 24 iterations on the lead scenario only
- Key metrics:
  - Best run: `reports/run_20260317_135929_263734_8.json`
    - Return %: `-5.04`
    - Max DD %: `5.61`
    - Sharpe: `-1.37`
    - OOS degradation %: `115.57`
    - Trades: `64`
- Walk-forward summary:
  - The dynamic exit probe materially worsened return, Sharpe, and OOS behavior
  - Trade count also increased instead of becoming more selective
  - The runtime exit hook remains useful at engine level, but this specific exit policy is not suitable for `momentum_rider`
- Decision: `reject`
- Next action:
  - Keep v2 as the active baseline
  - Do not keep break-even/trailing parameters in the active `momentum_rider` search space
  - Reuse the new runtime exit hook only for future strategies or different exit designs

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

## Iteration 5: EMA Cross ATR Reinforcement Filters
- Iteration ID: `ema_cross_atr_rsi_vol_filter_v1`
- Date: `2026-02-20`
- Strategy ID: `ema_cross_atr`
- Market/Timeframe: `forex/EURUSD/1h`
- Data window: `2022-01-01 to 2024-12-31`
- Parameter set:
  - Fixed: `ema_fast=20`, `ema_slow=50`, `atr_period=14`, `rsi_period=14`, `atr_vol_window=50`
  - Variable (initial grid): `rsi_gate` step 5 (`45..60`), `atr_vol_ratio_max` (`1.2..2.0`)
- Key metrics:
  - Return: `-6.79%`
  - Max DD: `7.09%`
  - Sharpe: `-2.25`
  - OOS degradation: `100.0%`
- Walk-forward summary: `filters reduced activity and drawdown versus previous baseline, but no OOS pass yet`
- Decision: `iterate`
- Next action:
  - Run wider campaign on EURUSD+NAS100 with 50-100 combinations per scenario.
  - Validate whether RSI/vol filters improve OOS stability across symbols.
- Artifact:
  - Report: `reports/run_20260220_093912_1.json`
