# Opportunity Analysis (Phase 1)

## Initial Scope

- Target markets: `crypto`, `forex`, `equities`, `indices`.
- Initial timeframes: `5m`, `15m`, `1h`.
- Priority: market-specific performance with strict drawdown limits.
- Stack: Python first, with later portability through adapters/APIs.

## Strategy Rationale

- `5m`:
  - Pros: more signals, strong intraday granularity.
  - Cons: higher noise, transaction costs matter more.
- `15m`:
  - Pros: balanced trade-off between signal frequency and stability.
  - Cons: can miss very short-term moves.
- `1h`:
  - Pros: cleaner signals, typically better drawdown control.
  - Cons: fewer daily opportunities.

## Opportunity by Asset Class

## Crypto

- Strong regime shifts (trend + intraday mean reversion).
- Special care on fees/slippage and weekend volatility.

## Forex

- High liquidity on major pairs.
- Session-driven patterns (Asia/Europe/US) are useful for time filters.

## Equities

- Strong open/close and news impact.
- Requires gap filters and overnight risk handling.

## Indices

- Good fit for intraday trend-following strategies.
- Sensitive to macro events and calendar effects.

## Hard Risk Constraints

- Strategy max drawdown (backtest) <= `12%`.
- Portfolio max drawdown <= `10%`.
- Kill-switch: stop new entries if rolling drawdown exceeds threshold.
- Risk-based position sizing (volatility-targeted or fixed risk per trade).

## Data Source

- Primary tick source: `dukascopy-node`.
- Initial aggregation recommendation:
  - tick -> `m1` -> `m5`/`m15`/`h1`.
- Use bid/ask data when available for realistic spread estimation.

## Selection KPIs

- CAGR / Annualized return.
- Sharpe and Sortino.
- Profit Factor.
- Win rate + payoff ratio.
- Max Drawdown (absolute and rolling).
- Stability score (out-of-sample vs in-sample behavior).

## Promotion Criteria (Next Phase)

- Drawdown threshold respected.
- Sharpe > `1.2` (initial target).
- OOS degradation <= `30%` vs IS.
- Positive results across at least two independent sub-periods.
