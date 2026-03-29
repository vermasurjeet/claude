"""Fundamental analysis scoring.

Each function takes stock info and returns a score from 0-100.
Higher scores indicate stronger fundamentals / better buy signals.
"""

from backend.config import settings
from backend.data.universe import SECTOR_MAP


def score_pe_ratio(info: dict, sector_median_pe: float = None) -> float:
    """Score based on PE ratio relative to sector median.

    Lower PE (relative to sector) = higher score (undervalued).
    Negative PE (loss-making) = very low score.
    """
    pe = info.get("pe_ratio")
    if pe is None:
        return 50.0

    if pe < 0:
        return 10.0  # Loss-making

    # Compare to sector median if available
    if sector_median_pe and sector_median_pe > 0:
        ratio = pe / sector_median_pe
        if ratio < 0.5:
            return 90.0  # Significantly undervalued
        elif ratio < 0.75:
            return 75.0
        elif ratio < 1.0:
            return 60.0
        elif ratio < 1.25:
            return 45.0
        elif ratio < 1.5:
            return 30.0
        else:
            return 15.0  # Significantly overvalued
    else:
        # Absolute PE scoring (no sector context)
        if pe < 10:
            return 85.0
        elif pe < 15:
            return 75.0
        elif pe < 20:
            return 60.0
        elif pe < 30:
            return 45.0
        elif pe < 50:
            return 30.0
        else:
            return 15.0


def score_roe(info: dict) -> float:
    """Score based on Return on Equity.

    ROE > 20% = excellent.
    """
    roe = info.get("roe")
    if roe is None:
        return 50.0

    # roe from yfinance is a decimal (0.15 = 15%)
    roe_pct = roe * 100 if abs(roe) < 1 else roe

    if roe_pct < 0:
        return 10.0
    elif roe_pct < 5:
        return 25.0
    elif roe_pct < 10:
        return 40.0
    elif roe_pct < 15:
        return 55.0
    elif roe_pct < 20:
        return 70.0
    elif roe_pct < 30:
        return 85.0
    else:
        return 95.0


def score_debt_to_equity(info: dict) -> float:
    """Score based on Debt-to-Equity ratio.

    Lower D/E = higher score (less leveraged).
    Financial sector has naturally higher D/E.
    """
    de = info.get("debt_to_equity")
    if de is None:
        return 50.0

    # yfinance returns D/E as percentage sometimes (e.g., 50 means 0.5)
    if de > 10:
        de = de / 100

    symbol = info.get("symbol", "")
    sector = SECTOR_MAP.get(symbol, "")

    # Financial services companies naturally have higher leverage
    if sector == "Financial Services":
        if de < 2:
            return 80.0
        elif de < 5:
            return 60.0
        elif de < 8:
            return 40.0
        else:
            return 20.0

    # Non-financial companies
    if de < 0.1:
        return 90.0  # Nearly debt-free
    elif de < 0.3:
        return 80.0
    elif de < 0.5:
        return 70.0
    elif de < 1.0:
        return 55.0
    elif de < 1.5:
        return 40.0
    elif de < 2.0:
        return 25.0
    else:
        return 10.0


def score_eps_growth(info: dict) -> float:
    """Score based on EPS growth rate.

    Higher growth = higher score.
    """
    growth = info.get("eps_growth")
    if growth is None:
        return 50.0

    # growth is a decimal (0.20 = 20%)
    growth_pct = growth * 100 if abs(growth) < 5 else growth

    if growth_pct < -20:
        return 10.0
    elif growth_pct < -10:
        return 20.0
    elif growth_pct < 0:
        return 35.0
    elif growth_pct < 5:
        return 45.0
    elif growth_pct < 10:
        return 55.0
    elif growth_pct < 20:
        return 70.0
    elif growth_pct < 30:
        return 85.0
    else:
        return 95.0


def score_revenue_growth(info: dict) -> float:
    """Score based on revenue growth rate."""
    growth = info.get("revenue_growth")
    if growth is None:
        return 50.0

    growth_pct = growth * 100 if abs(growth) < 5 else growth

    if growth_pct < -10:
        return 15.0
    elif growth_pct < 0:
        return 30.0
    elif growth_pct < 5:
        return 45.0
    elif growth_pct < 10:
        return 55.0
    elif growth_pct < 15:
        return 65.0
    elif growth_pct < 20:
        return 75.0
    elif growth_pct < 30:
        return 85.0
    else:
        return 95.0


def score_promoter_holding(info: dict) -> float:
    """Score based on promoter holding percentage.

    > 65% = strong promoter confidence.
    Declining holding is a red flag.
    """
    holding = info.get("promoter_holding")
    if holding is None:
        return 50.0

    if holding > 75:
        return 90.0
    elif holding > 65:
        return 75.0
    elif holding > 55:
        return 60.0
    elif holding > 45:
        return 45.0
    elif holding > 35:
        return 35.0
    else:
        return 20.0


def aggregate_fundamental(info: dict, sector_median_pe: float = None) -> tuple[float, dict]:
    """Compute weighted fundamental score from all indicators.

    Returns:
        Tuple of (aggregate_score, details_dict)
    """
    factors = {}
    weights = {}

    factor_funcs = [
        ("pe_ratio", lambda i: score_pe_ratio(i, sector_median_pe), settings.W_PE),
        ("roe", score_roe, settings.W_ROE),
        ("debt_to_equity", score_debt_to_equity, settings.W_DEBT_EQUITY),
        ("eps_growth", score_eps_growth, settings.W_EPS_GROWTH),
        ("revenue_growth", score_revenue_growth, settings.W_REVENUE_GROWTH),
        ("promoter_holding", score_promoter_holding, settings.W_PROMOTER),
    ]

    for name, func, weight in factor_funcs:
        try:
            score = func(info)
            factors[name] = round(score, 1)
            weights[name] = weight
        except Exception:
            factors[name] = None

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
