import csv
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional

from bots.base import BaseBotStrategy
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


def _resolve_trade_cost(
    strategy: BaseBotStrategy,
    market: str,
    timeframe: str,
    execution_cfg: Optional[dict],
) -> tuple[float, dict]:
    cfg = execution_cfg or {}
    default_cfg = cfg.get("default", {})
    market_cfg = cfg.get("market_costs", {}).get(market.lower(), {})

    fee_bps = float(market_cfg.get("fee_bps_per_side", default_cfg.get("fee_bps_per_side", 0.0)))
    slippage_bps = float(
        market_cfg.get("slippage_bps_per_side", default_cfg.get("slippage_bps_per_side", 0.0))
    )

    if fee_bps == 0.0 and slippage_bps == 0.0:
        per_side_cost = strategy.default_trade_cost(market=market, timeframe=timeframe)
    else:
        per_side_cost = (fee_bps + slippage_bps) / 10000.0

    profile = {
        "market": market,
        "timeframe": timeframe,
        "fee_bps_per_side": fee_bps,
        "slippage_bps_per_side": slippage_bps,
        "per_side_cost_fraction": round(per_side_cost, 8),
    }
    return per_side_cost, profile


def run_real_backtest(
    strategy: BaseBotStrategy,
    params: dict,
    data_root: Path,
    markets_filter: Optional[List[str]],
    symbols_filter: Optional[List[str]],
    timeframes_filter: Optional[List[str]],
    execution_cfg: Optional[dict] = None,
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

    params = strategy.normalize_params(params=params, bars_count=len(bars))
    indicators = strategy.prepare_indicators(bars=bars, params=params)

    timeframe = dataset_path.parent.parent.name if dataset_path.parent.name == "download" else dataset_path.parent.name
    market = dataset_path.parent.parent.parent.parent.name if dataset_path.parent.name == "download" else "unknown"
    per_trade_cost, cost_profile = _resolve_trade_cost(
        strategy=strategy,
        market=market,
        timeframe=timeframe,
        execution_cfg=execution_cfg,
    )

    position = 0
    stop_price = None
    take_price = None
    open_trade = None
    trade_log = []

    equity = 1.0
    equity_curve = [equity]
    returns = []

    for i in range(1, len(bars)):
        prev_close = bars[i - 1]["close"]
        close = bars[i]["close"]
        high = bars[i]["high"]
        low = bars[i]["low"]
        ts = bars[i]["timestamp"]

        bar_ret = 0.0

        if position != 0:
            exit_price = None
            exit_reason = None

            if position == 1 and stop_price is not None and take_price is not None:
                if low <= stop_price:
                    exit_price = stop_price
                    exit_reason = "stop_loss"
                elif high >= take_price:
                    exit_price = take_price
                    exit_reason = "take_profit"
            elif position == -1 and stop_price is not None and take_price is not None:
                if high >= stop_price:
                    exit_price = stop_price
                    exit_reason = "stop_loss"
                elif low <= take_price:
                    exit_price = take_price
                    exit_reason = "take_profit"

            if exit_price is not None:
                bar_ret += position * ((exit_price / prev_close) - 1.0)
                bar_ret -= per_trade_cost
                if open_trade:
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
                stop_price = None
                take_price = None
                open_trade = None
            else:
                bar_ret += position * ((close / prev_close) - 1.0)
                if strategy.should_flip(i=i, position=position, bars=bars, indicators=indicators):
                    bar_ret -= per_trade_cost
                    if open_trade:
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
                    stop_price = None
                    take_price = None
                    open_trade = None

        if position == 0:
            side = strategy.entry_signal(i=i, bars=bars, indicators=indicators)
            if side in (-1, 1):
                entry_price = close
                stop_price, take_price = strategy.risk_levels(
                    i=i,
                    side=side,
                    entry_price=entry_price,
                    bars=bars,
                    indicators=indicators,
                    params=params,
                )
                open_trade = {
                    "entry_timestamp": int(ts),
                    "side": "long" if side == 1 else "short",
                    "entry_price": round(entry_price, 6),
                    "stop_price": round(stop_price, 6),
                    "take_price": round(take_price, 6),
                }
                position = side
                bar_ret -= per_trade_cost

        equity *= (1.0 + bar_ret)
        returns.append(bar_ret)
        equity_curve.append(equity)

    total_return = (equity - 1.0) * 100.0
    max_dd = _max_drawdown_pct(equity_curve)

    returns_std = pstdev(returns) if len(returns) > 1 else 0.0
    sharpe = (mean(returns) / returns_std) * math.sqrt(_bars_per_year(timeframe)) if returns_std > 0 else 0.0

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
        "bars": len(bars),
        "timeframe": timeframe,
        "strategy_id": strategy.strategy_id,
        "params_effective": params,
        "cost_profile": cost_profile,
        "per_trade_cost": per_trade_cost,
        "trades_count": len(trade_log),
        "win_rate_pct": round(win_rate, 2),
        "trade_log": trade_log,
    }
    return metrics, details
