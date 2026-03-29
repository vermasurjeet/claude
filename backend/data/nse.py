"""NSE India data fetcher using jugaad-data library.

This module is optional — the system works with yfinance alone.
jugaad-data provides delivery volumes and FII/DII data that enhance scoring.
"""

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


def fetch_delivery_data(symbol: str, from_date: date = None, to_date: date = None) -> dict:
    """Fetch delivery volume data from NSE.

    Args:
        symbol: NSE symbol
        from_date: Start date (default: 30 days ago)
        to_date: End date (default: today)

    Returns:
        Dict with avg_delivery_pct and recent delivery data
    """
    if from_date is None:
        from_date = date.today() - timedelta(days=30)
    if to_date is None:
        to_date = date.today()

    try:
        from jugaad_data.nse import stock_df

        df = stock_df(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            series="EQ",
        )

        if df.empty:
            return {}

        # jugaad-data returns DELIVERY_PCT column
        if "DELIV_PER" in df.columns:
            avg_delivery = df["DELIV_PER"].mean()
            recent_delivery = df["DELIV_PER"].iloc[-1] if len(df) > 0 else None
        elif "%DIFFDELIVERYQTY" in df.columns:
            avg_delivery = df["%DIFFDELIVERYQTY"].mean()
            recent_delivery = df["%DIFFDELIVERYQTY"].iloc[-1] if len(df) > 0 else None
        else:
            return {}

        return {
            "avg_delivery_pct": float(avg_delivery) if avg_delivery else None,
            "recent_delivery_pct": float(recent_delivery) if recent_delivery else None,
        }

    except ImportError:
        logger.info("jugaad-data not installed, skipping delivery data")
        return {}
    except Exception as e:
        logger.warning(f"Error fetching delivery data for {symbol}: {e}")
        return {}


def fetch_fii_dii(for_date: date = None) -> dict:
    """Fetch FII/DII buy-sell data.

    Args:
        for_date: Date to fetch (default: today)

    Returns:
        Dict with fii_buy, fii_sell, dii_buy, dii_sell
    """
    if for_date is None:
        for_date = date.today()

    try:
        from jugaad_data.nse import NSELive

        nse = NSELive()
        data = nse.fii_dii()

        if not data:
            return {}

        result = {}
        for entry in data:
            category = entry.get("category", "")
            if "FII" in category or "FPI" in category:
                result["fii_buy"] = entry.get("buyValue")
                result["fii_sell"] = entry.get("sellValue")
            elif "DII" in category:
                result["dii_buy"] = entry.get("buyValue")
                result["dii_sell"] = entry.get("sellValue")

        return result

    except ImportError:
        logger.info("jugaad-data not installed, skipping FII/DII data")
        return {}
    except Exception as e:
        logger.warning(f"Error fetching FII/DII data: {e}")
        return {}


def fetch_promoter_holding(symbol: str) -> float | None:
    """Fetch promoter holding percentage from NSE.

    Args:
        symbol: NSE symbol

    Returns:
        Promoter holding percentage or None
    """
    try:
        from jugaad_data.nse import NSELive

        nse = NSELive()
        data = nse.stock_quote(symbol)

        if data and "securityInfo" in data:
            promoter_pct = data["securityInfo"].get("promoterHolding")
            return float(promoter_pct) if promoter_pct else None

        return None

    except ImportError:
        logger.info("jugaad-data not installed, skipping promoter data")
        return None
    except Exception as e:
        logger.warning(f"Error fetching promoter holding for {symbol}: {e}")
        return None
