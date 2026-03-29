"""Quantitative analysis scoring.

Momentum, mean reversion, relative strength, and sector rotation signals.
"""

import numpy as np
import pandas as pd

from backend.config import settings


def score_momentum(df: pd.DataFrame) -> float:
    """Score based on 3/6/12 month returns (Jegadeesh-Titman momentum).

    Strong positive multi-timeframe momentum = high score.
    Weighted: 3M (40%), 6M (35%), 12M (25%).
    """
    if len(df) < 60:
        return 50.0

    close = df["Close"]
    current_price = close.iloc[-1]

    returns = {}
    # 3-month (~63 trading days)
    if len(close) >= 63:
        returns["3m"] = (current_price - close.iloc[-63]) / close.iloc[-63]
    # 6-month (~126 trading days)
    if len(close) >= 126:
        returns["6m"] = (current_price - close.iloc[-126]) / close.iloc[-126]
    # 12-month (~252 trading days)
    if len(close) >= 252:
        returns["12m"] = (current_price - close.iloc[-252]) / close.iloc[-252]

    if not returns:
        return 50.0

    # Score each return period
    def return_to_score(ret: float) -> float:
        if ret > 0.50:
            return 95.0
        elif ret > 0.30:
            return 85.0
        elif ret > 0.15:
            return 70.0
        elif ret > 0.05:
            return 60.0
        elif ret > -0.05:
            return 50.0
        elif ret > -0.15:
            return 35.0
        elif ret > -0.30:
            return 20.0
        else:
            return 10.0

    weights = {"3m": 0.40, "6m": 0.35, "12m": 0.25}
    total_weight = sum(weights[k] for k in returns)
    score = sum(
        return_to_score(returns[k]) * weights[k] / total_weight
        for k in returns
    )

    return round(score, 1)


def score_mean_reversion(df: pd.DataFrame) -> float:
    """Score based on Z-score of price vs 50-day mean.

    Extreme negative Z-score = oversold (high buy score).
    Only meaningful for non-trending stocks.
    """
    if len(df) < 50:
        return 50.0

    close = df["Close"]
    ma50 = close.rolling(window=50).mean().iloc[-1]
    std50 = close.rolling(window=50).std().iloc[-1]

    if np.isnan(ma50) or np.isnan(std50) or std50 == 0:
        return 50.0

    z_score = (close.iloc[-1] - ma50) / std50

    if z_score < -2.0:
        return 90.0  # Extremely oversold
    elif z_score < -1.5:
        return 80.0
    elif z_score < -1.0:
        return 70.0
    elif z_score < -0.5:
        return 60.0
    elif z_score < 0.5:
        return 50.0  # Near mean
    elif z_score < 1.0:
        return 40.0
    elif z_score < 1.5:
        return 30.0
    elif z_score < 2.0:
        return 20.0
    else:
        return 10.0  # Extremely overbought


def score_relative_strength(df: pd.DataFrame, benchmark_df: pd.DataFrame) -> float:
    """Score based on relative strength vs Nifty50.

    Outperforming the benchmark = high score.
    Uses rolling 3-month return comparison.
    """
    if len(df) < 63 or len(benchmark_df) < 63:
        return 50.0

    stock_close = df["Close"]
    bench_close = benchmark_df["Close"]

    # Align dates
    common_index = stock_close.index.intersection(bench_close.index)
    if len(common_index) < 63:
        return 50.0

    stock_aligned = stock_close.loc[common_index]
    bench_aligned = bench_close.loc[common_index]

    # 3-month return
    stock_return = (stock_aligned.iloc[-1] - stock_aligned.iloc[-63]) / stock_aligned.iloc[-63]
    bench_return = (bench_aligned.iloc[-1] - bench_aligned.iloc[-63]) / bench_aligned.iloc[-63]

    # Relative strength
    excess_return = stock_return - bench_return

    if excess_return > 0.20:
        return 95.0
    elif excess_return > 0.10:
        return 80.0
    elif excess_return > 0.05:
        return 65.0
    elif excess_return > -0.05:
        return 50.0
    elif excess_return > -0.10:
        return 35.0
    elif excess_return > -0.20:
        return 20.0
    else:
        return 10.0


def score_sector_rotation(sector_returns: dict, stock_sector: str) -> float:
    """Score based on sector momentum (sector rotation strategy).

    If the stock's sector is in the top performing sectors = high score.

    Args:
        sector_returns: Dict of {sector: 1_month_return}
        stock_sector: The sector this stock belongs to
    """
    if not sector_returns or stock_sector not in sector_returns:
        return 50.0

    # Rank sectors by return
    sorted_sectors = sorted(sector_returns.items(), key=lambda x: x[1], reverse=True)
    total = len(sorted_sectors)

    if total == 0:
        return 50.0

    rank = next(
        (i for i, (s, _) in enumerate(sorted_sectors) if s == stock_sector),
        total // 2,
    )

    # Convert rank to percentile (0 = best sector, 1 = worst)
    percentile = rank / max(total - 1, 1)

    if percentile < 0.2:
        return 85.0  # Top quintile
    elif percentile < 0.4:
        return 70.0
    elif percentile < 0.6:
        return 50.0
    elif percentile < 0.8:
        return 35.0
    else:
        return 20.0  # Bottom quintile


def compute_sector_returns(sector_data: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compute 1-month return for each sector.

    Args:
        sector_data: Dict mapping sector name to a DataFrame of sector average prices.

    Returns:
        Dict of {sector: 1_month_return}
    """
    returns = {}
    for sector, df in sector_data.items():
        if len(df) >= 21:
            close = df["Close"]
            ret = (close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]
            returns[sector] = float(ret)
    return returns


def aggregate_quantitative(
    df: pd.DataFrame,
    benchmark_df: pd.DataFrame = None,
    sector_returns: dict = None,
    stock_sector: str = None,
) -> tuple[float, dict]:
    """Compute weighted quantitative score.

    Returns:
        Tuple of (aggregate_score, details_dict)
    """
    factors = {}
    weights = {}

    # Momentum
    try:
        factors["momentum"] = round(score_momentum(df), 1)
        weights["momentum"] = settings.W_MOMENTUM
    except Exception:
        factors["momentum"] = None

    # Mean reversion
    try:
        factors["mean_reversion"] = round(score_mean_reversion(df), 1)
        weights["mean_reversion"] = settings.W_MEAN_REVERSION
    except Exception:
        factors["mean_reversion"] = None

    # Relative strength (needs benchmark)
    if benchmark_df is not None and not benchmark_df.empty:
        try:
            factors["relative_strength"] = round(
                score_relative_strength(df, benchmark_df), 1
            )
            weights["relative_strength"] = settings.W_RELATIVE_STRENGTH
        except Exception:
            factors["relative_strength"] = None
    else:
        factors["relative_strength"] = None

    # Sector rotation
    if sector_returns and stock_sector:
        try:
            factors["sector_rotation"] = round(
                score_sector_rotation(sector_returns, stock_sector), 1
            )
            weights["sector_rotation"] = settings.W_SECTOR_ROTATION
        except Exception:
            factors["sector_rotation"] = None
    else:
        factors["sector_rotation"] = None

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
