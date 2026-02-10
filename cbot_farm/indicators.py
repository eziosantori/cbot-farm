from typing import List, Optional


def ema_series(values: List[float], period: int) -> List[Optional[float]]:
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


def atr_series(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[Optional[float]]:
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
