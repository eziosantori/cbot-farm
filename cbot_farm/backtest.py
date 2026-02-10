import csv
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable, List, Optional

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


def _load_close_prices(csv_path: Path) -> List[float]:
    closes: List[float] = []
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            close_value = row.get("close")
            if not close_value:
                continue
            try:
                closes.append(float(close_value))
            except ValueError:
                continue
    return closes


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
    closes = _load_close_prices(dataset_path)
    if len(closes) < 12:
        return (
            Metrics(
                total_return_pct=-100.0,
                sharpe=0.0,
                max_drawdown_pct=100.0,
                oos_degradation_pct=100.0,
            ),
            {
                "status": "failed",
                "reason": f"insufficient bars ({len(closes)})",
                "dataset": str(dataset_path),
            },
        )

    max_slow = max(6, min(int(params.get("ema_slow", 50)), len(closes) // 2))
    ema_slow = max(5, max_slow)
    ema_fast = max(3, min(int(params.get("ema_fast", 20)), ema_slow - 1))

    fast = _ema_series(closes, ema_fast)
    slow = _ema_series(closes, ema_slow)

    timeframe = dataset_path.parent.parent.name if dataset_path.parent.name == "download" else dataset_path.parent.name
    per_trade_cost = 0.0002  # 2 bps transaction estimate

    position = 0
    equity = 1.0
    equity_curve = [equity]
    returns: List[float] = []

    for i in range(1, len(closes)):
        prev_fast, prev_slow = fast[i - 1], slow[i - 1]
        curr_fast, curr_slow = fast[i], slow[i]
        if prev_fast is None or prev_slow is None or curr_fast is None or curr_slow is None:
            returns.append(0.0)
            equity_curve.append(equity)
            continue

        new_position = position
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            new_position = 1
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            new_position = -1

        price_ret = (closes[i] / closes[i - 1]) - 1.0
        bar_ret = position * price_ret

        if new_position != position:
            bar_ret -= per_trade_cost

        equity *= (1.0 + bar_ret)
        returns.append(bar_ret)
        equity_curve.append(equity)
        position = new_position

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

    details = {
        "status": "ok",
        "dataset": str(dataset_path),
        "bars": len(closes),
        "timeframe": timeframe,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "per_trade_cost": per_trade_cost,
    }
    return metrics, details
