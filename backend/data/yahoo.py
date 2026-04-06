"""Yahoo Finance data fetcher using yfinance library."""

import json
import time
import logging
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

import pandas as pd
import yfinance as yf

from backend.config import settings
from backend.db.connection import get_db

logger = logging.getLogger(__name__)


def fetch_ohlcv(symbol: str, period: str = None) -> pd.DataFrame:
    """Fetch OHLCV data for a stock from Yahoo Finance.

    Args:
        symbol: NSE symbol (e.g., 'RELIANCE')
        period: yfinance period string (default from config)

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    period = period or settings.OHLCV_PERIOD
    yahoo_symbol = f"{symbol}.NS"

    try:
        df = yf.download(yahoo_symbol, period=period, progress=False)
        if df.empty:
            logger.warning(f"No OHLCV data for {symbol}")
            return pd.DataFrame()

        # Handle multi-level columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.index = pd.to_datetime(df.index)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        return df

    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {e}")
        return pd.DataFrame()


def fetch_ohlcv_batch(symbols: list[str], period: str = None) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data for multiple stocks in one request.

    Args:
        symbols: List of NSE symbols
        period: yfinance period string

    Returns:
        Dict mapping symbol to DataFrame
    """
    period = period or settings.OHLCV_PERIOD
    yahoo_symbols = [f"{s}.NS" for s in symbols]

    try:
        data = yf.download(
            " ".join(yahoo_symbols),
            period=period,
            progress=False,
            group_by="ticker",
        )

        result = {}
        for i, symbol in enumerate(symbols):
            yahoo_sym = yahoo_symbols[i]
            try:
                if len(symbols) == 1:
                    df = data.copy()
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                else:
                    df = data[yahoo_sym].copy() if yahoo_sym in data.columns.get_level_values(0) else pd.DataFrame()

                if not df.empty:
                    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    result[symbol] = df
            except Exception as e:
                logger.warning(f"Error extracting batch data for {symbol}: {e}")

        return result

    except Exception as e:
        logger.error(f"Error in batch OHLCV fetch: {e}")
        return {}


def fetch_stock_info(symbol: str) -> dict:
    """Fetch fundamental data for a stock from Yahoo Finance.

    Args:
        symbol: NSE symbol

    Returns:
        Dict with fundamental metrics
    """
    yahoo_symbol = f"{symbol}.NS"

    try:
        ticker = yf.Ticker(yahoo_symbol)
        info = ticker.info

        return {
            "symbol": symbol,
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "eps_growth": _calc_eps_growth(info),
            "revenue_growth": info.get("revenueGrowth"),
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "info_json": json.dumps(info, default=str),
        }
    except Exception as e:
        logger.error(f"Error fetching info for {symbol}: {e}")
        return {"symbol": symbol}


def _calc_eps_growth(info: dict) -> float | None:
    """Calculate EPS growth from trailing and forward EPS."""
    trailing = info.get("trailingEps")
    forward = info.get("forwardEps")
    if trailing and forward and trailing != 0:
        return (forward - trailing) / abs(trailing)
    return None


async def save_ohlcv_to_db(symbol: str, df: pd.DataFrame):
    """Save OHLCV data to the database."""
    if df.empty:
        return

    db = await get_db()
    try:
        rows = []
        for date, row in df.iterrows():
            rows.append((
                symbol,
                date.strftime("%Y-%m-%d"),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"]),
            ))

        await db.executemany(
            """INSERT INTO price_history (symbol, date, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(symbol, date) DO UPDATE SET
                   open=excluded.open, high=excluded.high, low=excluded.low,
                   close=excluded.close, volume=excluded.volume""",
            rows,
        )
        await db.commit()
    finally:
        await db.close()


async def save_fundamentals_to_db(info: dict):
    """Save fundamental data to the database."""
    symbol = info.get("symbol")
    if not symbol:
        return

    now = datetime.now(IST).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO fundamentals
               (symbol, pe_ratio, pb_ratio, roe, debt_to_equity, eps_growth,
                revenue_growth, market_cap, dividend_yield, info_json, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(symbol) DO UPDATE SET
                   pe_ratio=excluded.pe_ratio, pb_ratio=excluded.pb_ratio,
                   roe=excluded.roe, debt_to_equity=excluded.debt_to_equity,
                   eps_growth=excluded.eps_growth, revenue_growth=excluded.revenue_growth,
                   market_cap=excluded.market_cap, dividend_yield=excluded.dividend_yield,
                   info_json=excluded.info_json, fetched_at=excluded.fetched_at""",
            (symbol, info.get("pe_ratio"), info.get("pb_ratio"),
             info.get("roe"), info.get("debt_to_equity"),
             info.get("eps_growth"), info.get("revenue_growth"),
             info.get("market_cap"), info.get("dividend_yield"),
             info.get("info_json"), now),
        )
        await db.commit()
    finally:
        await db.close()


async def load_ohlcv_from_db(symbol: str, days: int = 365) -> pd.DataFrame:
    """Load OHLCV data from the database."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT date, open, high, low, close, volume
               FROM price_history
               WHERE symbol = ?
               ORDER BY date DESC
               LIMIT ?""",
            (symbol, days),
        )
        rows = await cursor.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(
            [dict(r) for r in rows],
            columns=["date", "open", "high", "low", "close", "volume"],
        )
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        return df

    finally:
        await db.close()
