from typing import Dict, List, Optional

from bots.base import BaseBotStrategy
from cbot_farm.indicators import atr_series, ema_series, rsi_series


def _sma_optional(values: List[Optional[float]], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if period <= 1:
        return [float(v) if v is not None else None for v in values]

    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        if any(v is None for v in window):
            continue
        out[i] = float(sum(window)) / float(period)
    return out


class EmaCrossAtrBot(BaseBotStrategy):
    strategy_id = "ema_cross_atr"
    display_name = "EMA Cross ATR Bot"

    def sample_params(self, iteration: int) -> dict:
        # Keep core structure stable and vary only reinforcement filters.
        rsi_steps = [45, 50, 55, 60]
        vol_steps = [1.2, 1.4, 1.6, 1.8, 2.0]
        return {
            "ema_fast": 20,
            "ema_slow": 50,
            "atr_period": 14,
            "atr_mult_stop": 1.5,
            "atr_mult_take": 2.0,
            "rsi_period": 14,
            "rsi_gate": rsi_steps[(iteration - 1) % len(rsi_steps)],
            "atr_vol_window": 50,
            "atr_vol_ratio_max": vol_steps[(iteration - 1) % len(vol_steps)],
        }

    def normalize_params(self, params: dict, bars_count: int) -> dict:
        max_slow = max(6, min(int(params.get("ema_slow", 50)), max(6, bars_count // 2)))
        ema_slow = max(5, max_slow)
        ema_fast = max(3, min(int(params.get("ema_fast", 20)), ema_slow - 1))

        max_period = max(5, bars_count // 3)
        atr_period = max(5, min(int(params.get("atr_period", 14)), max_period))
        rsi_period = max(2, min(int(params.get("rsi_period", 14)), max_period))
        atr_vol_window = max(5, min(int(params.get("atr_vol_window", 50)), max_period))

        normalized = dict(params)
        normalized["ema_fast"] = ema_fast
        normalized["ema_slow"] = ema_slow
        normalized["atr_period"] = atr_period
        normalized["atr_mult_stop"] = max(0.5, float(params.get("atr_mult_stop", 1.5)))
        normalized["atr_mult_take"] = max(0.5, float(params.get("atr_mult_take", 2.0)))
        normalized["rsi_period"] = rsi_period
        normalized["rsi_gate"] = max(40, min(int(params.get("rsi_gate", 50)), 60))
        normalized["atr_vol_window"] = atr_vol_window
        normalized["atr_vol_ratio_max"] = max(1.0, float(params.get("atr_vol_ratio_max", 1.8)))
        return normalized

    def prepare_indicators(self, bars: List[Dict[str, float]], params: dict) -> dict:
        closes = [bar["close"] for bar in bars]
        highs = [bar["high"] for bar in bars]
        lows = [bar["low"] for bar in bars]

        atr = atr_series(highs, lows, closes, period=int(params["atr_period"]))
        return {
            "ema_fast": ema_series(closes, int(params["ema_fast"])),
            "ema_slow": ema_series(closes, int(params["ema_slow"])),
            "atr": atr,
            "rsi": rsi_series(closes, period=int(params["rsi_period"])),
            "atr_avg": _sma_optional(atr, int(params["atr_vol_window"])),
            "entry_filters": {
                "rsi_gate": int(params["rsi_gate"]),
                "atr_vol_ratio_max": float(params["atr_vol_ratio_max"]),
            },
        }

    def _volatility_allowed(self, i: int, indicators: dict) -> bool:
        atr = indicators["atr"]
        atr_avg = indicators["atr_avg"]
        ratio_limit = float(indicators["entry_filters"]["atr_vol_ratio_max"])

        atr_value = atr[i - 1] if i - 1 >= 0 else None
        atr_mean = atr_avg[i - 1] if i - 1 >= 0 else None
        if atr_value is None or atr_mean is None or atr_mean <= 0:
            return False
        return float(atr_value) <= float(atr_mean) * ratio_limit

    def entry_signal(self, i: int, bars: List[Dict[str, float]], indicators: dict) -> int:
        fast = indicators["ema_fast"]
        slow = indicators["ema_slow"]
        rsi = indicators["rsi"]
        rsi_gate = int(indicators["entry_filters"]["rsi_gate"])

        prev_fast, prev_slow = fast[i - 1], slow[i - 1]
        curr_fast, curr_slow = fast[i], slow[i]
        rsi_prev = rsi[i - 1] if i - 1 >= 0 else None

        if (
            prev_fast is None
            or prev_slow is None
            or curr_fast is None
            or curr_slow is None
            or rsi_prev is None
        ):
            return 0

        if not self._volatility_allowed(i=i, indicators=indicators):
            return 0

        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return 1 if float(rsi_prev) >= float(rsi_gate) else 0
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            short_gate = 100.0 - float(rsi_gate)
            return -1 if float(rsi_prev) <= short_gate else 0
        return 0

    def should_flip(
        self,
        i: int,
        position: int,
        bars: List[Dict[str, float]],
        indicators: dict,
    ) -> bool:
        signal = self.entry_signal(i, bars, indicators)
        return (position == 1 and signal == -1) or (position == -1 and signal == 1)

    def risk_levels(
        self,
        i: int,
        side: int,
        entry_price: float,
        bars: List[Dict[str, float]],
        indicators: dict,
        params: dict,
    ) -> tuple[float, float]:
        atr = indicators["atr"]
        atr_value = atr[i] if atr[i] is not None else max(entry_price * 0.005, 1e-8)
        stop_distance = atr_value * float(params["atr_mult_stop"])
        take_distance = atr_value * float(params["atr_mult_take"])

        if side == 1:
            return entry_price - stop_distance, entry_price + take_distance
        return entry_price + stop_distance, entry_price - take_distance
