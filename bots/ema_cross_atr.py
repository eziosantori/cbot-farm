# EMA Cross ATR Strategy
# This bot trades based on the crossover of two Exponential Moving Averages (EMA)
# and uses the Average True Range (ATR) to dynamically calculate stop-loss and take-profit levels.
#
# Trading Logic:
# 1. Entry Signal: When the fast EMA crosses above the slow EMA → BUY signal (long)
#                  When the fast EMA crosses below the slow EMA → SELL signal (short)
# 2. Exit Strategy: Uses ATR-based dynamic risk levels
#    - Stop Loss: Entry price ± (ATR × stop_loss_multiplier)
#    - Take Profit: Entry price ± (ATR × take_profit_multiplier)
# 3. Position Flipping: Reverses position when opposite EMA cross signal occurs

from random import random
from typing import Dict, List, Optional

from bots.base import BaseBotStrategy
from cbot_farm.indicators import atr_series, ema_series


class EmaCrossAtrBot(BaseBotStrategy):
    strategy_id = "ema_cross_atr"
    display_name = "EMA Cross ATR Bot"

    def sample_params(self, iteration: int) -> dict:
        # Generate sample parameters for backtesting iterations
        # Incrementally varies EMA periods and ATR multipliers
        return {
            "ema_fast": 20 + iteration,
            "ema_slow": 50 + iteration,
            "atr_mult_stop": round(1.2 + 0.1 * random(), 2),
            "atr_mult_take": round(1.8 + 0.2 * random(), 2),
            "atr_period": 14,
        }

    def normalize_params(self, params: dict, bars_count: int) -> dict:
        # Validate and normalize parameters to ensure they're within valid ranges
        # Prevent ema_fast from being greater than or equal to ema_slow
        # Ensure periods don't exceed available historical bars
        max_slow = max(6, min(int(params.get("ema_slow", 50)), bars_count // 2))
        ema_slow = max(5, max_slow)
        ema_fast = max(3, min(int(params.get("ema_fast", 20)), ema_slow - 1))

        normalized = dict(params)
        normalized["ema_fast"] = ema_fast
        normalized["ema_slow"] = ema_slow
        normalized["atr_period"] = int(params.get("atr_period", 14))
        normalized["atr_mult_stop"] = float(params.get("atr_mult_stop", 1.5))
        normalized["atr_mult_take"] = float(params.get("atr_mult_take", 2.0))
        return normalized

    def prepare_indicators(self, bars: List[Dict[str, float]], params: dict) -> dict:
        # Calculate all required technical indicators from price data
        closes = [bar["close"] for bar in bars]
        highs = [bar["high"] for bar in bars]
        lows = [bar["low"] for bar in bars]
        return {
            "ema_fast": ema_series(closes, int(params["ema_fast"])),
            "ema_slow": ema_series(closes, int(params["ema_slow"])),
            "atr": atr_series(highs, lows, closes, period=int(params["atr_period"])),
        }

    def entry_signal(self, i: int, bars: List[Dict[str, float]], indicators: dict) -> int:
        # Detect EMA crossover signals
        # Returns: 1 (bullish cross), -1 (bearish cross), 0 (no signal)
        fast = indicators["ema_fast"]
        slow = indicators["ema_slow"]
        prev_fast, prev_slow = fast[i - 1], slow[i - 1]
        curr_fast, curr_slow = fast[i], slow[i]

        if (
            prev_fast is None
            or prev_slow is None
            or curr_fast is None
            or curr_slow is None
        ):
            return 0

        # Bullish crossover: fast EMA moves above slow EMA
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return 1
        # Bearish crossover: fast EMA moves below slow EMA
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return -1
        return 0

    def should_flip(
        self,
        i: int,
        position: int,
        bars: List[Dict[str, float]],
        indicators: dict,
    ) -> bool:
        # Check if current position should be reversed based on opposite EMA signal
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
        # Calculate dynamic stop-loss and take-profit levels based on ATR
        # This adapts risk levels to market volatility
        atr = indicators["atr"]
        atr_value = atr[i] if atr[i] is not None else max(entry_price * 0.005, 1e-8)
        stop_distance = atr_value * float(params["atr_mult_stop"])
        take_distance = atr_value * float(params["atr_mult_take"])

        # For long positions (side == 1): stop below, take above
        # For short positions (side == -1): stop above, take below
        if side == 1:
            return entry_price - stop_distance, entry_price + take_distance
        return entry_price + stop_distance, entry_price - take_distance
