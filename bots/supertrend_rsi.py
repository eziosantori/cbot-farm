# SuperTrend + RSI Momentum Strategy (Bot 2)
# This bot combines trend direction (SuperTrend), momentum timing (RSI),
# trend strength filtering (ADX), and directional bias (EMA) to capture
# breakout opportunities while avoiding choppy, ranging markets.
#
# Trading Logic:
# 1. Entry Signal:
#    - LONG: SuperTrend switches from downtrend to uptrend + RSI > 50 + Price > EMA + ADX > min_adx
#    - SHORT: SuperTrend switches from uptrend to downtrend + RSI < 50 + Price < EMA + ADX > min_adx
# 2. Exit Strategy:
#    - Primary: SuperTrend reversal (opposite trend detected)
#    - Secondary: ATR-based stop-loss and take-profit levels
# 3. Filters:
#    - ADX: Ensures market has sufficient trend strength
#    - EMA: Provides directional bias (trade with larger trend)
#    - RSI: Confirms momentum alignment

from random import random, uniform
from typing import Dict, List, Optional

from bots.base import BaseBotStrategy
from cbot_farm.indicators import adx_series, atr_series, ema_series, rsi_series, supertrend_series


class SuperTrendRsiBot(BaseBotStrategy):
    strategy_id = "supertrend_rsi"
    display_name = "SuperTrend + RSI Momentum"

    def sample_params(self, iteration: int) -> dict:
        # Generate parameter samples for optimization iterations
        # Varies SuperTrend sensitivity, filters, and risk levels
        return {
            "st_period": int(8 + (iteration % 7)),
            "st_mult": round(2.0 + uniform(0, 2.0), 1),
            "rsi_period": 14,
            "ema_period": 150 + (iteration % 3) * 50,
            "min_adx": 15 + (iteration % 3) * 5,
            "atr_period": 14,
            "atr_mult_stop": round(1.5 + uniform(0, 1.5), 1),
            "atr_mult_take": round(2.0 + uniform(0, 3.0), 1),
        }

    def normalize_params(self, params: dict, bars_count: int) -> dict:
        # Validate and normalize parameters to dataset constraints
        # Ensure periods don't exceed available bars
        max_period = bars_count // 3
        
        normalized = dict(params)
        normalized["st_period"] = max(5, min(int(params.get("st_period", 10)), max_period))
        normalized["st_mult"] = max(1.0, min(float(params.get("st_mult", 3.0)), 5.0))
        normalized["rsi_period"] = max(2, min(int(params.get("rsi_period", 14)), max_period))
        normalized["ema_period"] = max(20, min(int(params.get("ema_period", 200)), max_period))
        normalized["min_adx"] = max(0, min(int(params.get("min_adx", 20)), 50))
        normalized["atr_period"] = max(5, min(int(params.get("atr_period", 14)), max_period))
        normalized["atr_mult_stop"] = max(0.5, float(params.get("atr_mult_stop", 2.0)))
        normalized["atr_mult_take"] = max(0.5, float(params.get("atr_mult_take", 3.0)))
        
        return normalized

    def prepare_indicators(self, bars: List[Dict[str, float]], params: dict) -> dict:
        # Precompute all technical indicators from price data
        closes = [bar["close"] for bar in bars]
        highs = [bar["high"] for bar in bars]
        lows = [bar["low"] for bar in bars]
        
        st_up, st_down = supertrend_series(
            highs, lows, closes, 
            period=int(params["st_period"]),
            multiplier=float(params["st_mult"])
        )
        
        return {
            "st_up": st_up,
            "st_down": st_down,
            "rsi": rsi_series(closes, period=int(params["rsi_period"])),
            "adx": adx_series(highs, lows, closes, period=14),
            "ema": ema_series(closes, period=int(params["ema_period"])),
            "atr": atr_series(highs, lows, closes, period=int(params["atr_period"])),
            # Store min_adx as metadata for entry_signal (params not passed there)
            "_min_adx": int(params["min_adx"]),
        }

    def entry_signal(self, i: int, bars: List[Dict[str, float]], indicators: dict) -> int:
        # Detect SuperTrend reversal with multi-filter confirmation
        # Returns: 1 (long), -1 (short), 0 (no entry)
        
        if i < 1:
            return 0
        
        st_up = indicators["st_up"]
        st_down = indicators["st_down"]
        rsi = indicators["rsi"]
        adx = indicators["adx"]
        ema = indicators["ema"]
        min_adx = indicators["_min_adx"]  # Retrieve from metadata
        
        # Current and previous bar values
        curr_up = st_up[i]
        curr_down = st_down[i]
        prev_up = st_up[i - 1]
        prev_down = st_down[i - 1]
        
        rsi_val = rsi[i - 1]  # Use previous bar's RSI (completed bar)
        adx_val = adx[i - 1]
        ema_val = ema[i - 1]
        close_price = bars[i - 1]["close"]
        
        # Check for None values
        if (curr_up is None and curr_down is None) or \
           (prev_up is None and prev_down is None) or \
           rsi_val is None or adx_val is None or ema_val is None:
            return 0
        
        # Filter 1: ADX strength (avoid choppy markets)
        if adx_val < min_adx:
            return 0
        
        # LONG: SuperTrend switches to uptrend + RSI > 50 + Price > EMA
        if prev_down is not None and curr_up is not None:
            if rsi_val > 50 and close_price > ema_val:
                return 1
        
        # SHORT: SuperTrend switches to downtrend + RSI < 50 + Price < EMA
        if prev_up is not None and curr_down is not None:
            if rsi_val < 50 and close_price < ema_val:
                return -1
        
        return 0

    def should_flip(
        self,
        i: int,
        position: int,
        bars: List[Dict[str, float]],
        indicators: dict,
    ) -> bool:
        # Exit when SuperTrend reverses (hard exit on trend change)
        # This is the primary exit mechanism for this strategy
        
        st_up = indicators["st_up"]
        st_down = indicators["st_down"]
        
        curr_up = st_up[i]
        curr_down = st_down[i]
        
        if curr_up is None and curr_down is None:
            return False
        
        # Long position but SuperTrend switched to downtrend
        if position == 1 and curr_down is not None:
            return True
        
        # Short position but SuperTrend switched to uptrend
        if position == -1 and curr_up is not None:
            return True
        
        return False

    def risk_levels(
        self,
        i: int,
        side: int,
        entry_price: float,
        bars: List[Dict[str, float]],
        indicators: dict,
        params: dict,
    ) -> tuple[float, float]:
        # Calculate ATR-based stop-loss and take-profit levels
        # Adapts to market volatility for dynamic risk management
        
        atr = indicators["atr"]
        atr_value = atr[i] if atr[i] is not None else max(entry_price * 0.01, 1e-8)
        
        stop_distance = atr_value * float(params["atr_mult_stop"])
        take_distance = atr_value * float(params["atr_mult_take"])
        
        # For long positions (side == 1): stop below, take above
        # For short positions (side == -1): stop above, take below
        if side == 1:
            return entry_price - stop_distance, entry_price + take_distance
        return entry_price + stop_distance, entry_price - take_distance

    def default_trade_cost(self, market: Optional[str], timeframe: Optional[str]) -> float:
        # Return per-side transaction cost as fraction based on market type
        # These values align with typical execution costs per market
        
        if market == "forex":
            return 0.0001  # 1 bps per side (0.02% round-trip)
        elif market == "crypto":
            return 0.0005  # 5 bps per side (0.10% round-trip)
        elif market == "indices":
            return 0.0002  # 2 bps per side (0.04% round-trip)
        elif market == "commodities":
            return 0.0003  # 3 bps per side (0.06% round-trip)
        elif market == "equities":
            return 0.00025  # 2.5 bps per side (0.05% round-trip)
        
        # Default for unknown markets
        return 0.0002
