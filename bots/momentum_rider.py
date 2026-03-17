from typing import Dict, List, Optional

from bots.base import BaseBotStrategy
from cbot_farm.indicators import adx_series, atr_series, ema_series, macd_series, rsi_series


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


class MomentumRiderBot(BaseBotStrategy):
    strategy_id = "momentum_rider"
    display_name = "Momentum Rider"

    def sample_params(self, iteration: int) -> dict:
        fast_steps = [15, 20, 25]
        slow_steps = [50, 60, 70]
        signal_steps = [6, 9, 12]
        rsi_steps = [56, 60, 64]
        adx_steps = [18, 22, 26]
        vol_steps = [1.4, 1.6, 1.8]
        stop_steps = [1.5, 2.0, 2.5]
        take_steps = [2.5, 3.5, 4.5]
        return {
            "ema_fast": fast_steps[(iteration - 1) % len(fast_steps)],
            "ema_slow": slow_steps[(iteration - 1) % len(slow_steps)],
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": signal_steps[(iteration - 1) % len(signal_steps)],
            "rsi_period": 14,
            "rsi_gate": rsi_steps[(iteration - 1) % len(rsi_steps)],
            "adx_period": 14,
            "min_adx": adx_steps[(iteration - 1) % len(adx_steps)],
            "atr_period": 14,
            "atr_vol_window": 50,
            "atr_vol_ratio_max": vol_steps[(iteration - 1) % len(vol_steps)],
            "atr_mult_stop": stop_steps[(iteration - 1) % len(stop_steps)],
            "atr_mult_take": take_steps[(iteration - 1) % len(take_steps)],
        }

    def normalize_params(self, params: dict, bars_count: int) -> dict:
        max_period = max(5, bars_count // 3)
        ema_slow = max(20, min(int(params.get("ema_slow", 50)), max_period))
        ema_fast = max(5, min(int(params.get("ema_fast", 20)), ema_slow - 1))
        macd_slow = max(10, min(int(params.get("macd_slow", 26)), max_period))
        macd_fast = max(4, min(int(params.get("macd_fast", 12)), macd_slow - 1))
        macd_signal = max(3, min(int(params.get("macd_signal", 9)), max_period))

        normalized = dict(params)
        normalized["ema_fast"] = ema_fast
        normalized["ema_slow"] = ema_slow
        normalized["macd_fast"] = macd_fast
        normalized["macd_slow"] = macd_slow
        normalized["macd_signal"] = macd_signal
        normalized["rsi_period"] = max(2, min(int(params.get("rsi_period", 14)), max_period))
        normalized["rsi_gate"] = max(50, min(int(params.get("rsi_gate", 58)), 70))
        normalized["adx_period"] = max(5, min(int(params.get("adx_period", 14)), max_period))
        normalized["min_adx"] = max(10, min(int(params.get("min_adx", 20)), 50))
        normalized["atr_period"] = max(5, min(int(params.get("atr_period", 14)), max_period))
        normalized["atr_vol_window"] = max(5, min(int(params.get("atr_vol_window", 50)), max_period))
        normalized["atr_vol_ratio_max"] = max(1.0, float(params.get("atr_vol_ratio_max", 1.6)))
        normalized["atr_mult_stop"] = max(0.5, float(params.get("atr_mult_stop", 1.5)))
        normalized["atr_mult_take"] = max(0.5, float(params.get("atr_mult_take", 2.5)))
        return normalized

    def prepare_indicators(self, bars: List[Dict[str, float]], params: dict) -> dict:
        closes = [bar["close"] for bar in bars]
        highs = [bar["high"] for bar in bars]
        lows = [bar["low"] for bar in bars]
        macd_line, macd_signal, macd_hist = macd_series(
            closes,
            fast_period=int(params["macd_fast"]),
            slow_period=int(params["macd_slow"]),
            signal_period=int(params["macd_signal"]),
        )
        atr = atr_series(highs, lows, closes, int(params["atr_period"]))
        return {
            "ema_fast": ema_series(closes, int(params["ema_fast"])),
            "ema_slow": ema_series(closes, int(params["ema_slow"])),
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "rsi": rsi_series(closes, int(params["rsi_period"])),
            "adx": adx_series(highs, lows, closes, int(params["adx_period"])),
            "atr": atr,
            "atr_avg": _sma_optional(atr, int(params["atr_vol_window"])),
            "entry_filters": {
                "rsi_gate": int(params["rsi_gate"]),
                "min_adx": int(params["min_adx"]),
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
        if i < 1:
            return 0

        fast = indicators["ema_fast"]
        slow = indicators["ema_slow"]
        macd_line = indicators["macd_line"]
        macd_signal = indicators["macd_signal"]
        macd_hist = indicators["macd_hist"]
        rsi = indicators["rsi"]
        adx = indicators["adx"]
        gate = int(indicators["entry_filters"]["rsi_gate"])
        min_adx = int(indicators["entry_filters"]["min_adx"])

        price_prev = bars[i - 1]["close"]
        fast_prev = fast[i - 1]
        slow_prev = slow[i - 1]
        macd_prev = macd_line[i - 1]
        signal_prev = macd_signal[i - 1]
        macd_curr = macd_line[i]
        signal_curr = macd_signal[i]
        hist_curr = macd_hist[i]
        rsi_prev = rsi[i - 1]
        adx_prev = adx[i - 1]

        if any(
            value is None
            for value in [
                fast_prev,
                slow_prev,
                macd_prev,
                signal_prev,
                macd_curr,
                signal_curr,
                hist_curr,
                rsi_prev,
                adx_prev,
            ]
        ):
            return 0

        if not self._volatility_allowed(i=i, indicators=indicators):
            return 0
        if float(adx_prev) < float(min_adx):
            return 0

        long_trend = price_prev > fast_prev > slow_prev
        short_trend = price_prev < fast_prev < slow_prev
        long_cross = (
            float(macd_prev) <= float(signal_prev)
            and float(macd_curr) > float(signal_curr)
            and float(hist_curr) > 0
            and float(macd_curr) > 0
        )
        short_cross = (
            float(macd_prev) >= float(signal_prev)
            and float(macd_curr) < float(signal_curr)
            and float(hist_curr) < 0
            and float(macd_curr) < 0
        )

        if long_trend and long_cross and float(rsi_prev) >= float(gate):
            return 1
        if short_trend and short_cross and float(rsi_prev) <= float(100 - gate):
            return -1
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

    def default_trade_cost(self, market: Optional[str], timeframe: Optional[str]) -> float:
        if market == "forex":
            return 0.0001
        if market == "crypto":
            return 0.0005
        if market == "indices":
            return 0.0002
        if market == "equities":
            return 0.00025
        return 0.0002
