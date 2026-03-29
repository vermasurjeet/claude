"""Technical analysis scoring using the `ta` library.

Each function takes an OHLCV DataFrame and returns a score from 0-100.
Higher scores indicate stronger buy signals.
"""

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands

from backend.config import settings


def score_rsi(df: pd.DataFrame) -> float:
    """Score based on RSI(14).

    Oversold (<30) = buy opportunity (high score).
    Overbought (>70) = caution (low score).
    """
    if len(df) < 15:
        return 50.0

    rsi = RSIIndicator(close=df["Close"], window=14).rsi().iloc[-1]

    if np.isnan(rsi):
        return 50.0

    if rsi < 30:
        return 80 + (30 - rsi) / 30 * 20
    elif rsi < 45:
        return 60 + (45 - rsi) / 15 * 20
    elif rsi < 55:
        return 50 + (55 - rsi) / 10 * 10
    elif rsi < 70:
        return 30 + (70 - rsi) / 15 * 20
    else:
        return max(0, 30 - (rsi - 70) / 30 * 30)


def score_macd(df: pd.DataFrame) -> float:
    """Score based on MACD crossover and histogram.

    Bullish crossover = high score.
    Positive histogram growing = moderate-high.
    """
    if len(df) < 35:
        return 50.0

    macd_ind = MACD(close=df["Close"])
    macd_line = macd_ind.macd()
    signal_line = macd_ind.macd_signal()
    histogram = macd_ind.macd_diff()

    if macd_line.empty or signal_line.empty:
        return 50.0

    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    current_hist = histogram.iloc[-1]

    if np.isnan(current_macd) or np.isnan(current_signal):
        return 50.0

    score = 50.0

    # Bullish crossover (MACD crossed above signal recently)
    if len(macd_line) >= 3:
        prev_macd = macd_line.iloc[-3]
        prev_signal = signal_line.iloc[-3]
        if not np.isnan(prev_macd) and not np.isnan(prev_signal):
            if prev_macd <= prev_signal and current_macd > current_signal:
                score = 90.0  # Fresh bullish crossover
            elif current_macd > current_signal:
                score = 70.0  # Already above signal
            elif prev_macd >= prev_signal and current_macd < current_signal:
                score = 15.0  # Fresh bearish crossover
            else:
                score = 30.0  # Below signal

    # Adjust based on histogram momentum
    if len(histogram) >= 2:
        prev_hist = histogram.iloc[-2]
        if not np.isnan(prev_hist) and not np.isnan(current_hist):
            if current_hist > prev_hist and current_hist > 0:
                score = min(100, score + 10)  # Growing positive histogram
            elif current_hist < prev_hist and current_hist < 0:
                score = max(0, score - 10)  # Growing negative histogram

    return score


def score_moving_averages(df: pd.DataFrame) -> float:
    """Score based on SMA 50/200 crossover and price position.

    Price > SMA50 > SMA200 (aligned uptrend) = high score.
    Golden cross = very high score.
    Death cross = very low score.
    """
    if len(df) < 200:
        # Use shorter MAs if insufficient data
        if len(df) < 50:
            return 50.0
        sma_short = SMAIndicator(close=df["Close"], window=20).sma_indicator()
        sma_long = SMAIndicator(close=df["Close"], window=50).sma_indicator()
    else:
        sma_short = SMAIndicator(close=df["Close"], window=50).sma_indicator()
        sma_long = SMAIndicator(close=df["Close"], window=200).sma_indicator()

    price = df["Close"].iloc[-1]
    sma_s = sma_short.iloc[-1]
    sma_l = sma_long.iloc[-1]

    if np.isnan(sma_s) or np.isnan(sma_l):
        return 50.0

    # Check for golden/death cross in last 10 days
    golden_cross = False
    death_cross = False
    lookback = min(10, len(sma_short) - 1)
    for i in range(1, lookback + 1):
        prev_s = sma_short.iloc[-(i + 1)]
        prev_l = sma_long.iloc[-(i + 1)]
        if not np.isnan(prev_s) and not np.isnan(prev_l):
            if prev_s <= prev_l and sma_s > sma_l:
                golden_cross = True
            elif prev_s >= prev_l and sma_s < sma_l:
                death_cross = True
            break

    if golden_cross:
        return 95.0
    elif death_cross:
        return 10.0
    elif price > sma_s > sma_l:
        return 85.0  # Aligned uptrend
    elif price > sma_s and sma_s < sma_l:
        return 60.0  # Price recovering
    elif price < sma_s < sma_l:
        return 15.0  # Aligned downtrend
    elif price < sma_s and sma_s > sma_l:
        return 35.0  # Pullback in uptrend
    else:
        return 50.0


def score_bollinger(df: pd.DataFrame) -> float:
    """Score based on Bollinger Bands position and squeeze.

    Price near lower band + narrowing bands = high score (mean reversion opportunity).
    Price above upper band = low score (overbought).
    """
    if len(df) < 20:
        return 50.0

    bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
    upper = bb.bollinger_hband().iloc[-1]
    lower = bb.bollinger_lband().iloc[-1]
    mid = bb.bollinger_mavg().iloc[-1]
    width = bb.bollinger_wband().iloc[-1]
    price = df["Close"].iloc[-1]

    if np.isnan(upper) or np.isnan(lower) or np.isnan(price):
        return 50.0

    band_range = upper - lower
    if band_range <= 0:
        return 50.0

    # Position within bands (0 = at lower, 1 = at upper)
    position = (price - lower) / band_range

    # Squeeze detection: compare current width to 50-day avg width
    width_series = bb.bollinger_wband()
    if len(width_series) >= 50:
        avg_width = width_series.iloc[-50:].mean()
        is_squeeze = width < avg_width * 0.75
    else:
        is_squeeze = False

    if position < 0.1:
        score = 85.0  # Near lower band
    elif position < 0.3:
        score = 70.0
    elif position < 0.5:
        score = 55.0
    elif position < 0.7:
        score = 45.0
    elif position < 0.9:
        score = 30.0
    else:
        score = 15.0  # Near upper band

    # Squeeze bonus: a breakout from squeeze is significant
    if is_squeeze:
        score = min(100, score + 10)

    return score


def score_adx(df: pd.DataFrame) -> float:
    """Score based on ADX trend strength.

    ADX > 25 with +DI > -DI = strong uptrend (high score).
    ADX < 20 = no trend (neutral).
    """
    if len(df) < 20:
        return 50.0

    adx_ind = ADXIndicator(high=df["High"], low=df["Low"], close=df["Close"], window=14)
    adx = adx_ind.adx().iloc[-1]
    plus_di = adx_ind.adx_pos().iloc[-1]
    minus_di = adx_ind.adx_neg().iloc[-1]

    if np.isnan(adx) or np.isnan(plus_di) or np.isnan(minus_di):
        return 50.0

    if adx > 25 and plus_di > minus_di:
        # Strong uptrend
        return 75.0 + min(25, (adx - 25) / 25 * 25)
    elif adx > 25 and minus_di > plus_di:
        # Strong downtrend
        return max(0, 25.0 - (adx - 25) / 25 * 25)
    elif adx < 20:
        # No trend — neutral
        return 50.0
    else:
        # Weak trend
        if plus_di > minus_di:
            return 60.0
        else:
            return 40.0


def score_volume_breakout(df: pd.DataFrame) -> float:
    """Score based on volume relative to recent average.

    Volume > 2x 20-day avg with price up = bullish breakout.
    Volume spike with price down = bearish.
    """
    if len(df) < 21:
        return 50.0

    current_vol = df["Volume"].iloc[-1]
    avg_vol = df["Volume"].iloc[-21:-1].mean()
    price_change = (df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]

    if avg_vol <= 0 or np.isnan(current_vol):
        return 50.0

    vol_ratio = current_vol / avg_vol

    if vol_ratio > 2.0 and price_change > 0.01:
        return 90.0  # Bullish volume breakout
    elif vol_ratio > 1.5 and price_change > 0:
        return 75.0
    elif vol_ratio > 2.0 and price_change < -0.01:
        return 20.0  # Bearish volume spike
    elif vol_ratio > 1.5 and price_change < 0:
        return 35.0
    elif vol_ratio > 1.0:
        return 55.0 if price_change >= 0 else 45.0
    else:
        return 50.0  # Below average volume


def aggregate_technical(df: pd.DataFrame) -> tuple[float, dict]:
    """Compute weighted technical score from all indicators.

    Returns:
        Tuple of (aggregate_score, details_dict)
    """
    factors = {}
    weights = {}

    # Compute each factor score
    factor_funcs = [
        ("rsi", score_rsi, settings.W_RSI),
        ("macd", score_macd, settings.W_MACD),
        ("moving_avg", score_moving_averages, settings.W_MOVING_AVG),
        ("bollinger", score_bollinger, settings.W_BOLLINGER),
        ("adx", score_adx, settings.W_ADX),
        ("volume_breakout", score_volume_breakout, settings.W_VOLUME),
    ]

    for name, func, weight in factor_funcs:
        try:
            score = func(df)
            factors[name] = round(score, 1)
            weights[name] = weight
        except Exception:
            # Skip failed indicators, redistribute weight
            factors[name] = None

    # Weighted average (redistribute weight of failed indicators)
    valid_scores = {k: v for k, v in factors.items() if v is not None}
    if not valid_scores:
        return 50.0, factors

    total_weight = sum(weights[k] for k in valid_scores)
    if total_weight == 0:
        return 50.0, factors

    aggregate = sum(
        valid_scores[k] * weights[k] / total_weight
        for k in valid_scores
    )

    return round(min(100, max(0, aggregate)), 1), factors
