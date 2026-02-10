# Strategy Specs (Initial Set)

## Design Principles

- Simple algorithms with few interpretable parameters.
- Same conceptual logic across markets; tuned per market/timeframe.
- No strategy promotion without strict drawdown compliance.

## S1 Trend EMA Breakout

- Idea: trade in trend direction when price breaks recent highs/lows with EMA filter.
- Indicators:
  - Fast EMA (`20`)
  - Slow EMA (`50`)
  - Breakout lookback (`20` bars)
- Long entry: `EMA20 > EMA50` and close > lookback high.
- Short entry: `EMA20 < EMA50` and close < lookback low.
- Exit:
  - ATR-based stop loss (`1.5x ATR14`)
  - Dynamic take profit (`2.0x ATR14`) or trailing stop.
- Preferred markets: indices, forex.
- Timeframes: `15m`, `1h`.

## S2 Mean Reversion Bollinger RSI

- Idea: capture price extremes in range-bound markets.
- Indicators:
  - Bollinger Bands (`20`, `2.0`)
  - RSI (`14`)
- Long entry: close < lower band and RSI < `30`.
- Short entry: close > upper band and RSI > `70`.
- Exit:
  - mean reversion to middle band
  - emergency ATR stop (`1.2x ATR14`).
- Preferred markets: major forex pairs, liquid crypto.
- Timeframes: `5m`, `15m`.

## S3 Session Momentum (Forex/Index Intraday)

- Idea: capture momentum around Europe/US session opens.
- Rules:
  - define opening range (e.g., first 30 minutes).
  - enter on range breakout with volume/volatility filter.
- Exit:
  - time-based session close
  - ATR trailing stop.
- Preferred markets: forex, indices.
- Timeframes: `5m`, `15m`.

## S4 Volatility Contraction Expansion

- Idea: after volatility compression, trade expansion breakout.
- Indicators:
  - Rolling ATR percentile
  - Donchian channel (`20`)
- Entry: low ATR percentile + Donchian breakout.
- Exit: trailing stop and bar timeout.
- Preferred markets: crypto, indices.
- Timeframes: `15m`, `1h`.

## Common Risk Rules

- Risk per trade: `0.25%`-`0.75%` of capital.
- Max concurrent positions per asset class: configurable.
- Daily stop: halt trading if daily loss > `2%`.
- Hard strategy max drawdown: `12%`.

## Validation Standard

- Walk-forward split:
  - IS: `60%`
  - Validation: `20%`
  - OOS: `20%`
- Monte Carlo trade reshuffling for stress testing.
- Parameter sensitivity test (+/-20%) to verify robustness.
