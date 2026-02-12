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


def rsi_series(values: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Relative Strength Index (RSI) using Wilder's smoothing.
    RSI = 100 - (100 / (1 + RS)), where RS = Average Gain / Average Loss
    """
    if len(values) < period + 1:
        return [None] * len(values)
    
    rsi: List[Optional[float]] = [None] * len(values)
    gains: List[float] = []
    losses: List[float] = []
    
    # Calculate price changes
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    
    if len(gains) < period:
        return rsi
    
    # Initial average gain/loss (SMA)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Calculate first RSI value
    rs = avg_gain / avg_loss if avg_loss != 0 else 100.0
    rsi[period] = 100.0 - (100.0 / (1.0 + rs))
    
    # Wilder's smoothing for subsequent values
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 100.0
        rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi


def adx_series(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Average Directional Index (ADX) using Wilder's method.
    Measures trend strength (0-100). Values > 25 indicate strong trend.
    """
    if len(closes) < period * 2:
        return [None] * len(closes)
    
    adx: List[Optional[float]] = [None] * len(closes)
    
    # Calculate directional movements and true range
    plus_dm: List[float] = [0.0]
    minus_dm: List[float] = [0.0]
    trs: List[float] = []
    
    for i in range(len(closes)):
        if i == 0:
            tr = highs[i] - lows[i]
        else:
            # +DM and -DM
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0.0)
            
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0.0)
            
            # True Range
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        trs.append(tr)
    
    if len(trs) < period:
        return adx
    
    # Initial smoothed values
    smoothed_tr = sum(trs[:period])
    smoothed_plus_dm = sum(plus_dm[:period])
    smoothed_minus_dm = sum(minus_dm[:period])
    
    # Calculate +DI and -DI, then DX
    dx_values: List[float] = []
    
    for i in range(period - 1, len(closes)):
        if i > period - 1:
            # Wilder's smoothing
            smoothed_tr = smoothed_tr - (smoothed_tr / period) + trs[i]
            smoothed_plus_dm = smoothed_plus_dm - (smoothed_plus_dm / period) + plus_dm[i]
            smoothed_minus_dm = smoothed_minus_dm - (smoothed_minus_dm / period) + minus_dm[i]
        
        plus_di = 100 * (smoothed_plus_dm / smoothed_tr) if smoothed_tr != 0 else 0
        minus_di = 100 * (smoothed_minus_dm / smoothed_tr) if smoothed_tr != 0 else 0
        
        # Calculate DX
        di_sum = plus_di + minus_di
        di_diff = abs(plus_di - minus_di)
        dx = 100 * (di_diff / di_sum) if di_sum != 0 else 0
        dx_values.append(dx)
    
    if len(dx_values) < period:
        return adx
    
    # Calculate ADX (smoothed DX)
    adx_value = sum(dx_values[:period]) / period
    adx[period * 2 - 2] = adx_value
    
    for i in range(period, len(dx_values)):
        adx_value = ((adx_value * (period - 1)) + dx_values[i]) / period
        adx[period - 1 + i] = adx_value
    
    return adx


def supertrend_series(
    highs: List[float], 
    lows: List[float], 
    closes: List[float], 
    period: int = 10, 
    multiplier: float = 3.0
) -> tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Calculate SuperTrend indicator using ATR bands.
    Returns (uptrend_series, downtrend_series) where:
    - uptrend_series[i] = support level when in uptrend, None otherwise
    - downtrend_series[i] = resistance level when in downtrend, None otherwise
    
    Logic:
    - Basic bands: HL2 ± (ATR × multiplier)
    - Trend switches when price crosses opposite band
    - Only one series has values at each bar (uptrend OR downtrend)
    """
    n = len(closes)
    atr = atr_series(highs, lows, closes, period)
    
    uptrend: List[Optional[float]] = [None] * n
    downtrend: List[Optional[float]] = [None] * n
    
    if n < period:
        return uptrend, downtrend
    
    # Calculate HL/2 (typical price without volume)
    hl2 = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    
    # Basic bands
    basic_upper: List[Optional[float]] = [None] * n
    basic_lower: List[Optional[float]] = [None] * n
    
    for i in range(n):
        if atr[i] is not None:
            basic_upper[i] = hl2[i] + (multiplier * atr[i])
            basic_lower[i] = hl2[i] - (multiplier * atr[i])
    
    # Final bands (with smoothing logic)
    final_upper: List[Optional[float]] = [None] * n
    final_lower: List[Optional[float]] = [None] * n
    
    for i in range(n):
        if basic_upper[i] is not None and basic_lower[i] is not None:
            # Upper band: don't let it increase if price is below it
            if i == 0 or final_upper[i - 1] is None:
                final_upper[i] = basic_upper[i]
            else:
                final_upper[i] = basic_upper[i]
                if basic_upper[i] < final_upper[i - 1] or closes[i - 1] > final_upper[i - 1]:
                    final_upper[i] = basic_upper[i]
                else:
                    final_upper[i] = final_upper[i - 1]
            
            # Lower band: don't let it decrease if price is above it
            if i == 0 or final_lower[i - 1] is None:
                final_lower[i] = basic_lower[i]
            else:
                final_lower[i] = basic_lower[i]
                if basic_lower[i] > final_lower[i - 1] or closes[i - 1] < final_lower[i - 1]:
                    final_lower[i] = basic_lower[i]
                else:
                    final_lower[i] = final_lower[i - 1]
    
    # Determine trend
    is_uptrend = True  # Start with uptrend assumption
    
    for i in range(n):
        if final_upper[i] is None or final_lower[i] is None:
            continue
        
        # Trend switch logic
        if i > 0:
            if is_uptrend:
                if closes[i] <= final_lower[i]:
                    is_uptrend = False
            else:
                if closes[i] >= final_upper[i]:
                    is_uptrend = True
        
        # Assign to appropriate series
        if is_uptrend:
            uptrend[i] = final_lower[i]
            downtrend[i] = None
        else:
            downtrend[i] = final_upper[i]
            uptrend[i] = None
    
    return uptrend, downtrend
