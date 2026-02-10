# Development-Backtest-Optimization Loop

## Loop Objective

Automate fast and controlled iterations:

1. data update
2. baseline backtest
3. parameter optimization
4. out-of-sample validation
5. retry/promotion decision

## Pipeline

1. `ingest`:
   - download/update data from Dukascopy.
   - normalize OHLCV format/timezone.
2. `develop`:
   - apply strategy/market/timeframe configuration.
3. `backtest`:
   - compute KPIs and risk metrics.
4. `optimize`:
   - run grid or random search with drawdown constraint.
5. `validate`:
   - compare IS vs OOS.
6. `report`:
   - save JSON/Markdown outputs per iteration.
7. `retry`:
   - if thresholds fail, adjust parameters and rerun.

## Stop Rules

- Immediate stop for an iteration if `max_drawdown > 12%`.
- Stop campaign if no KPI improvement after `N` retries (default `5`).
- Promote candidate only if:
  - positive OOS return
  - drawdown under threshold
  - acceptable stability.

## Minimum Iteration Outputs

- `reports/run_YYYYMMDD_HHMMSS.json`
- content:
  - run id
  - market, timeframe, strategy
  - parameters used
  - metrics (return, sharpe, drawdown)
  - pass/fail gates
  - retry notes
