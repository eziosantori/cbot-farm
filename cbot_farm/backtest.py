import csv
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional

from .types import Metrics


def _split_csv_filter(raw: Optional[List[str]]) -> Optional[List[str]]:
    if not raw:
        return None
    return [item.lower() for item in raw]


def _find_candidate_files(
    data_root: Path,
    markets_filter: Optional[List[str]],
    symbols_filter: Optional[List[str]],
    timeframes_filter: Optional[List[str]],
) -> List[Path]:
    markets = _split_csv_filter(markets_filter)
    symbols = _split_csv_filter(symbols_filter)
    timeframes = _split_csv_filter(timeframes_filter)

    files: List[Path] = []
    if not data_root.exists():
        return files

    for csv_path in data_root.rglob("*.csv"):
        parts = [p.lower() for p in csv_path.parts]
        # Expected tail: .../<market>/<symbol>/<timeframe>/download/<file>.csv
        if len(parts) < 6:
            continue
        market = parts[-5]
        symbol = parts[-4]
        timeframe = parts[-3]

        if markets and market not in markets:
            continue
        if symbols and symbol not in symbols:
            continue
        if timeframes and timeframe not in timeframes:
            continue
        files.append(csv_path)

    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _load_ohlc_bars(csv_path: Path) -> List[Dict[str, float]]:
    bars: List[Dict[str, float]] = []
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                bars.append(
                    {
                        "timestamp": float(row["timestamp"]),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return bars


def _ema_series(values: List[float], period: int) -> List[Optional[float]]:
    if period <= 1:
        return [float(v) for v in values]

    k = 2.0 / (period + 1.0)
    out: List[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return out

    seed = sum(values[:period]) / period
    out[period - 1] = seed
    ema_prev = seed

    for idx in range(period, len(values)):
        ema_prev = values[idx] * k + ema_prev * (1.0 - k)
        out[idx] = ema_prev
    return out


def _atr_series(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[Optional[float]]:
    trs: List[float] = []
    for i in range(len(closes)):
        if i == 0:
            tr = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        trs.append(tr)

    atr: List[Optional[float]] = [None] * len(closes)
    if len(closes) < period:
        return atr

    seed = sum(trs[:period]) / period
    atr[period - 1] = seed
    prev = seed
    for i in range(period, len(closes)):
        prev = ((prev * (period - 1)) + trs[i]) / period
        atr[i] = prev
    return atr


def _bars_per_year(timeframe: str) -> int:
    mapping = {
        "1m": 525600,
        "5m": 105120,
        "15m": 35040,
        "30m": 17520,
        "1h": 8760,
        "4h": 2190,
        "1d": 365,
    }
    return mapping.get(timeframe.lower(), 8760)


def _max_drawdown_pct(equity_curve: List[float]) -> float:
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd * 100.0


def _oos_degradation_pct(returns: List[float]) -> float:
    n = len(returns)
    if n < 20:
        return 100.0

    split = int(n * 0.8)
    is_returns = returns[:split]
    oos_returns = returns[split:]
    is_total = math.prod((1.0 + r) for r in is_returns) - 1.0
    oos_total = math.prod((1.0 + r) for r in oos_returns) - 1.0

    if is_total <= 0:
        return 100.0

    degradation = ((is_total - oos_total) / abs(is_total)) * 100.0
    return max(0.0, round(degradation, 2))


def _close_trade(
    open_trade: dict,
    exit_timestamp: float,
    exit_price: float,
    side: int,
    reason: str,
    per_trade_cost: float,
) -> dict:
    gross_pct = side * ((exit_price / open_trade["entry_price"]) - 1.0) * 100.0
    # Entry and exit fees are both accounted at trade level for reporting.
    net_pct = gross_pct - (2.0 * per_trade_cost * 100.0)
    trade = dict(open_trade)
    trade.update(
        {
            "exit_timestamp": int(exit_timestamp),
            "exit_price": round(exit_price, 6),
            "exit_reason": reason,
            "gross_pnl_pct": round(gross_pct, 4),
            "net_pnl_pct": round(net_pct, 4),
        }
    )
    return trade


def run_real_backtest(
    params: dict,
    data_root: Path,
    markets_filter: Optional[List[str]],
    symbols_filter: Optional[List[str]],
    timeframes_filter: Optional[List[str]],
) -> tuple[Metrics, dict]:
    candidates = _find_candidate_files(
        data_root=data_root,
        markets_filter=markets_filter,
        symbols_filter=symbols_filter,
        timeframes_filter=timeframes_filter,
    )

    if not candidates:
        return (
            Metrics(
                total_return_pct=-100.0,
                sharpe=0.0,
                max_drawdown_pct=100.0,
                oos_degradation_pct=100.0,
            ),
            {"status": "failed", "reason": "no csv dataset found for current filters"},
        )

    dataset_path = candidates[0]
    bars = _load_ohlc_bars(dataset_path)
    if len(bars) < 12:
        return (
            Metrics(
                total_return_pct=-100.0,
                sharpe=0.0,
                max_drawdown_pct=100.0,
                oos_degradation_pct=100.0,
            ),
            {
                "status": "failed",
                "reason": f"insufficient bars ({len(bars)})",
                "dataset": str(dataset_path),
            },
        )

    closes = [bar["close"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]

    max_slow = max(6, min(int(params.get("ema_slow", 50)), len(closes) // 2))
    ema_slow = max(5, max_slow)
    ema_fast = max(3, min(int(params.get("ema_fast", 20)), ema_slow - 1))
    atr_period = 14
    atr_mult_stop = float(params.get("atr_mult_stop", 1.5))
    atr_mult_take = float(params.get("atr_mult_take", 2.0))

    fast = _ema_series(closes, ema_fast)
    slow = _ema_series(closes, ema_slow)
    atr = _atr_series(highs, lows, closes, period=atr_period)

    timeframe = dataset_path.parent.parent.name if dataset_path.parent.name == "download" else dataset_path.parent.name
    per_trade_cost = 0.0002  # 2 bps transaction estimate

    position = 0
    entry_price: Optional[float] = None
    stop_price: Optional[float] = None
    take_price: Optional[float] = None
    open_trade: Optional[dict] = None
    trade_log: List[dict] = []

    equity = 1.0
    equity_curve = [equity]
    returns: List[float] = []

    for i in range(1, len(bars)):
        prev_close = bars[i - 1]["close"]
        close = bars[i]["close"]
        high = bars[i]["high"]
        low = bars[i]["low"]
        ts = bars[i]["timestamp"]

        prev_fast, prev_slow = fast[i - 1], slow[i - 1]
        curr_fast, curr_slow = fast[i], slow[i]
        bull_cross = (
            prev_fast is not None
            and prev_slow is not None
            and curr_fast is not None
            and curr_slow is not None
            and prev_fast <= prev_slow
            and curr_fast > curr_slow
        )
        bear_cross = (
            prev_fast is not None
            and prev_slow is not None
            and curr_fast is not None
            and curr_slow is not None
            and prev_fast >= prev_slow
            and curr_fast < curr_slow
        )

        bar_ret = 0.0

        if position != 0:
            exit_price: Optional[float] = None
            exit_reason: Optional[str] = None

            if position == 1 and stop_price is not None and take_price is not None:
                stop_hit = low <= stop_price
                take_hit = high >= take_price
                if stop_hit:
                    exit_price = stop_price
                    exit_reason = "stop_loss"
                elif take_hit:
                    exit_price = take_price
                    exit_reason = "take_profit"
            elif position == -1 and stop_price is not None and take_price is not None:
                stop_hit = high >= stop_price
                take_hit = low <= take_price
                if stop_hit:
                    exit_price = stop_price
                    exit_reason = "stop_loss"
                elif take_hit:
                    exit_price = take_price
                    exit_reason = "take_profit"

            if exit_price is not None:
                bar_ret += position * ((exit_price / prev_close) - 1.0)
                bar_ret -= per_trade_cost
                if open_trade and entry_price is not None:
                    trade_log.append(
                        _close_trade(
                            open_trade=open_trade,
                            exit_timestamp=ts,
                            exit_price=exit_price,
                            side=position,
                            reason=exit_reason or "exit",
                            per_trade_cost=per_trade_cost,
                        )
                    )
                position = 0
                entry_price = None
                stop_price = None
                take_price = None
                open_trade = None
            else:
                bar_ret += position * ((close / prev_close) - 1.0)

                signal_flip = (position == 1 and bear_cross) or (position == -1 and bull_cross)
                if signal_flip:
                    bar_ret -= per_trade_cost
                    if open_trade and entry_price is not None:
                        trade_log.append(
                            _close_trade(
                                open_trade=open_trade,
                                exit_timestamp=ts,
                                exit_price=close,
                                side=position,
                                reason="signal_flip",
                                per_trade_cost=per_trade_cost,
                            )
                        )
                    position = 0
                    entry_price = None
                    stop_price = None
                    take_price = None
                    open_trade = None

        if position == 0 and (bull_cross or bear_cross):
            side = 1 if bull_cross else -1
            entry_price = close
            atr_value = atr[i] if atr[i] is not None else max(close * 0.005, 1e-8)
            stop_distance = atr_value * atr_mult_stop
            take_distance = atr_value * atr_mult_take

            if side == 1:
                stop_price = entry_price - stop_distance
                take_price = entry_price + take_distance
            else:
                stop_price = entry_price + stop_distance
                take_price = entry_price - take_distance

            open_trade = {
                "entry_timestamp": int(ts),
                "side": "long" if side == 1 else "short",
                "entry_price": round(entry_price, 6),
                "stop_price": round(stop_price, 6),
                "take_price": round(take_price, 6),
                "atr_at_entry": round(atr_value, 6),
            }
            position = side
            bar_ret -= per_trade_cost

        equity *= (1.0 + bar_ret)
        returns.append(bar_ret)
        equity_curve.append(equity)

    total_return = (equity - 1.0) * 100.0
    max_dd = _max_drawdown_pct(equity_curve)

    returns_std = pstdev(returns) if len(returns) > 1 else 0.0
    if returns_std > 0:
        sharpe = (mean(returns) / returns_std) * math.sqrt(_bars_per_year(timeframe))
    else:
        sharpe = 0.0

    metrics = Metrics(
        total_return_pct=round(total_return, 2),
        sharpe=round(sharpe, 2),
        max_drawdown_pct=round(max_dd, 2),
        oos_degradation_pct=_oos_degradation_pct(returns),
    )

    wins = sum(1 for trade in trade_log if trade["net_pnl_pct"] > 0)
    win_rate = (wins / len(trade_log)) * 100.0 if trade_log else 0.0

    details = {
        "status": "ok",
        "dataset": str(dataset_path),
        "bars": len(closes),
        "timeframe": timeframe,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "atr_period": atr_period,
        "atr_mult_stop": atr_mult_stop,
        "atr_mult_take": atr_mult_take,
        "per_trade_cost": per_trade_cost,
        "trades_count": len(trade_log),
        "win_rate_pct": round(win_rate, 2),
        "trade_log": trade_log,
    }
    return metrics, details
