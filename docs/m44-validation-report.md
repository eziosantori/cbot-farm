# M4.4-M4.6 Validation Report

## Scope
This report measures loop quality for the S1 pilot (`ema_cross_atr`) and defines a go/no-go decision for scaling to additional strategies.

## Inputs
- Pilot summary artifact: `reports/campaigns/cmp_b2659f3c8e97/artifacts/pilot_m44_summary.json`
- Pilot run snapshots: `reports/m44_pilot/`
- Tested scenarios:
  - `forex/EURUSD/1h`
  - `indices/NAS100/1h`
  - `commodities/XAUUSD/1h`

## Gate Baseline
Campaign gates used by orchestrator:
- `max_drawdown_pct <= 12`
- `min_sharpe >= 1.2`
- `max_oos_degradation_pct <= 30`

## Loop Quality Measurement (M4.5)

### Stability
From loop outputs:
- iterations: `3`
- average score: `36.9698`
- best score: `51.9737`
- worst score: `20.7455`
- spread: `31.2282`

Interpretation:
- Score variance is high relative to sample size.
- Samples are heterogeneous (different markets/datasets), so score spread does not prove robustness.

### Convergence
Observed decision path:
- `iterate`, `iterate`, `reject_stop` (stop reason: `max_loops_reached`)

Interpretation:
- No `promote_candidate` reached.
- Campaign stopped by budget, not by quality convergence.
- Convergence is not demonstrated.

### OOS Degradation Trend
Best-per-scenario OOS degradation:
- EURUSD: `100.0%`
- NAS100: `157.51%`
- XAUUSD: `100.0%`

Interpretation:
- All values are above the `<= 30%` gate.
- OOS behavior is consistently outside acceptable thresholds.

## Validation Decision (M4.6)

### Criteria Matrix
- Drawdown gate pass: `failed` (EURUSD and NAS100 exceed threshold)
- Sharpe gate pass: `failed` (all scenarios below threshold)
- OOS degradation gate pass: `failed` (all scenarios above threshold)
- Loop convergence: `failed`
- Data adequacy: `partially failed` (XAUUSD window is too short for reliable signal)

### Verdict
`NO-GO` for scaling this loop to additional strategies at current state.

## Required Actions Before Re-test
1. Improve dataset quality and coverage (especially commodities).
2. Fix report id uniqueness in CLI to avoid same-second overwrite risk.
3. Re-run pilot with longer campaigns and repeated runs per scenario.
4. Re-tune parameter space toward stability-first ranges before broad scaling.
