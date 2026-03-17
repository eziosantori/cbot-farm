from typing import Dict, List, Optional

from bots.base import BaseBotStrategy
from cbot_farm.indicators import atr_series, ema_series, macd_series, rsi_series


class MomentumRiderBot(BaseBotStrategy):
    strategy_id = "momentum_rider"
    display_name = "Momentum Rider"

    def sample_params(self, iteration: int) -> dict:
        fast_steps = [15, 20, 25]
        slow_steps = [50, 60, 70]
        rsi_steps = [52, 55, 58]
        stop_steps = [1.5, 2.0, 2.5]
        take_steps = [2.5, 3.0, 3.5]
        return {
            "ema_fast": fast_steps[(iteration - 1) % len(fast_steps)],
            "ema_slow": slow_steps[(iteration - 1) % len(slow_steps)],
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "rsi_period": 14,
            "rsi_gate": rsi_steps[(iteration - 1) % len(rsi_steps)],
            "atr_period": 14,
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
        normalized["rsi_gate"] = max(50, min(int(params.get("rsi_gate", 55)), 65))
        normalized["atr_period"] = max(5, min(int(params.get("atr_period", 14)), max_period))
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
        return {
            "ema_fast": ema_series(closes, int(params["ema_fast"])),
            "ema_slow": ema_series(closes, int(params["ema_slow"])),
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "rsi": rsi_series(closes, int(params["rsi_period"])),
            "atr": atr_series(highs, lows, closes, int(params["atr_period"])),
            "entry_filters": {"rsi_gate": int(params["rsi_gate"])},
        }

    def entry_signal(self, i: int, bars: List[Dict[str, float]], indicators: dict) -> int:
        if i < 1:
            return 0

        fast = indicators["ema_fast"]
        slow = indicators["ema_slow"]
        macd_line = indicators["macd_line"]
        macd_signal = indicators["macd_signal"]
        macd_hist = indicators["macd_hist"]
        rsi = indicators["rsi"]
        gate = int(indicators["entry_filters"]["rsi_gate"])

        price_prev = bars[i - 1]["close"]
        fast_prev = fast[i - 1]
        slow_prev = slow[i - 1]
        macd_prev = macd_line[i - 1]
        signal_prev = macd_signal[i - 1]
        macd_curr = macd_line[i]
        signal_curr = macd_signal[i]
        hist_curr = macd_hist[i]
        rsi_prev = rsi[i - 1]

        if any(value is None for value in [fast_prev, slow_prev, macd_prev, signal_prev, macd_curr, signal_curr, hist_curr, rsi_prev]):
            return 0

        long_trend = price_prev > fast_prev > slow_prev
        short_trend = price_prev < fast_prev < slow_prev
        long_cross = float(macd_prev) <= float(signal_prev) and float(macd_curr) > float(signal_curr) and float(hist_curr) > 0
        short_cross = float(macd_prev) >= float(signal_prev) and float(macd_curr) < float(signal_curr) and float(hist_curr) < 0

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
