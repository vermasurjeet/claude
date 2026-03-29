"""Central scoring engine — combines technical, fundamental, and quantitative analysis."""

import json
import logging
import time
from datetime import datetime

import pandas as pd

from backend.config import settings
from backend.db.connection import get_db
from backend.data.yahoo import (
    fetch_ohlcv, fetch_ohlcv_batch, fetch_stock_info,
    save_ohlcv_to_db, save_fundamentals_to_db, load_ohlcv_from_db,
)
from backend.data.nse import fetch_promoter_holding
from backend.data.universe import get_stock_list, SECTOR_MAP
from backend.analysis.technical import aggregate_technical
from backend.analysis.fundamental import aggregate_fundamental
from backend.analysis.quantitative import (
    aggregate_quantitative, compute_sector_returns,
)

logger = logging.getLogger(__name__)

# Nifty 50 index symbol for benchmark
NIFTY50_SYMBOL = "^NSEI"


def fetch_benchmark() -> pd.DataFrame:
    """Fetch Nifty 50 index data for benchmark comparison."""
    import yfinance as yf

    try:
        df = yf.download(NIFTY50_SYMBOL, period=settings.OHLCV_PERIOD, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception as e:
        logger.error(f"Error fetching benchmark: {e}")
        return pd.DataFrame()


async def compute_conviction(
    symbol: str,
    ohlcv_df: pd.DataFrame,
    info: dict,
    benchmark_df: pd.DataFrame = None,
    sector_returns: dict = None,
) -> dict:
    """Compute conviction score for a single stock.

    Returns:
        Dict with total_score, sub-scores, and details
    """
    sector = SECTOR_MAP.get(symbol, info.get("sector", ""))

    # Get sector median PE for context
    sector_median_pe = await _get_sector_median_pe(sector)

    # Merge promoter holding into info if available
    if info.get("promoter_holding") is None:
        promoter = fetch_promoter_holding(symbol)
        if promoter is not None:
            info["promoter_holding"] = promoter

    # Technical analysis
    tech_score, tech_details = aggregate_technical(ohlcv_df)

    # Fundamental analysis
    fund_score, fund_details = aggregate_fundamental(info, sector_median_pe)

    # Quantitative analysis
    quant_score, quant_details = aggregate_quantitative(
        ohlcv_df, benchmark_df, sector_returns, sector
    )

    # Weighted combination
    total = (
        settings.WEIGHT_TECHNICAL * tech_score
        + settings.WEIGHT_FUNDAMENTAL * fund_score
        + settings.WEIGHT_QUANTITATIVE * quant_score
    )

    return {
        "symbol": symbol,
        "total_score": round(total, 1),
        "technical_score": tech_score,
        "fundamental_score": fund_score,
        "quant_score": quant_score,
        "details": {
            "technical": tech_details,
            "fundamental": fund_details,
            "quantitative": quant_details,
        },
        "computed_at": datetime.utcnow().isoformat(),
    }


async def save_score(result: dict):
    """Save a conviction score to the database."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO scores
               (symbol, computed_at, total_score, technical_score,
                fundamental_score, quant_score, details_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                result["symbol"],
                result["computed_at"],
                result["total_score"],
                result["technical_score"],
                result["fundamental_score"],
                result["quant_score"],
                json.dumps(result["details"]),
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def refresh_all_scores(progress_callback=None) -> dict:
    """Full refresh: fetch data and compute scores for all stocks.

    Args:
        progress_callback: Optional callable(current, total, symbol)

    Returns:
        Summary dict with counts and errors
    """
    stocks = get_stock_list()
    total = len(stocks)
    logger.info(f"Starting full refresh for {total} stocks")

    # 1. Fetch benchmark
    benchmark_df = fetch_benchmark()

    # 2. Batch fetch OHLCV
    symbols = [s["symbol"] for s in stocks]
    batch_size = settings.YAHOO_BATCH_SIZE

    all_ohlcv = {}
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        logger.info(f"Fetching OHLCV batch {i // batch_size + 1}")
        batch_data = fetch_ohlcv_batch(batch)
        all_ohlcv.update(batch_data)
        time.sleep(settings.YAHOO_RATE_LIMIT_SECONDS)

    # 3. Save OHLCV to DB
    for symbol, df in all_ohlcv.items():
        await save_ohlcv_to_db(symbol, df)

    # 4. Compute sector returns for sector rotation scoring
    sector_dfs = {}
    for stock in stocks:
        sector = stock["sector"]
        symbol = stock["symbol"]
        if symbol in all_ohlcv and sector:
            if sector not in sector_dfs:
                sector_dfs[sector] = []
            sector_dfs[sector].append(all_ohlcv[symbol])

    # Average each sector's close prices
    sector_avg = {}
    for sector, dfs in sector_dfs.items():
        if dfs:
            combined = pd.concat([df["Close"] for df in dfs], axis=1)
            avg = combined.mean(axis=1)
            sector_avg[sector] = pd.DataFrame({"Close": avg})

    sector_returns = compute_sector_returns(sector_avg)

    # 5. Compute scores for each stock
    results = []
    errors = []

    for idx, stock in enumerate(stocks):
        symbol = stock["symbol"]

        if progress_callback:
            progress_callback(idx + 1, total, symbol)

        try:
            ohlcv = all_ohlcv.get(symbol, pd.DataFrame())
            if ohlcv.empty:
                logger.warning(f"No OHLCV data for {symbol}, skipping")
                errors.append(symbol)
                continue

            # Fetch fundamental data (with rate limiting)
            info = fetch_stock_info(symbol)
            time.sleep(settings.YAHOO_RATE_LIMIT_SECONDS)

            await save_fundamentals_to_db(info)

            # Compute conviction
            result = await compute_conviction(
                symbol, ohlcv, info, benchmark_df, sector_returns
            )
            await save_score(result)
            results.append(result)

            logger.info(
                f"[{idx + 1}/{total}] {symbol}: "
                f"Score={result['total_score']:.1f} "
                f"(T={result['technical_score']:.1f} "
                f"F={result['fundamental_score']:.1f} "
                f"Q={result['quant_score']:.1f})"
            )

        except Exception as e:
            logger.error(f"Error scoring {symbol}: {e}")
            errors.append(symbol)

    # 6. Update sector aggregate scores
    await _update_sector_scores()

    summary = {
        "total": total,
        "scored": len(results),
        "errors": len(errors),
        "error_symbols": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info(f"Refresh complete: {summary}")
    return summary


async def _get_sector_median_pe(sector: str) -> float | None:
    """Get median PE ratio for a sector from the fundamentals table."""
    if not sector:
        return None

    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT pe_ratio FROM fundamentals f
               JOIN stocks s ON f.symbol = s.symbol
               WHERE s.sector = ? AND f.pe_ratio > 0""",
            (sector,),
        )
        rows = await cursor.fetchall()
        if not rows:
            return None
        pes = sorted([r[0] for r in rows])
        mid = len(pes) // 2
        return pes[mid]
    finally:
        await db.close()


async def _update_sector_scores():
    """Update the sector_scores table with latest aggregates."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    db = await get_db()
    try:
        # Get latest score per stock
        cursor = await db.execute(
            """SELECT s.sector, sc.symbol, sc.total_score
               FROM scores sc
               JOIN stocks s ON sc.symbol = s.symbol
               WHERE sc.computed_at = (
                   SELECT MAX(sc2.computed_at) FROM scores sc2
                   WHERE sc2.symbol = sc.symbol
               )"""
        )
        rows = await cursor.fetchall()

        sector_data = {}
        for row in rows:
            sector = row[0]
            if sector not in sector_data:
                sector_data[sector] = {"scores": [], "top_symbol": "", "top_score": 0}
            score = row[2]
            sector_data[sector]["scores"].append(score)
            if score > sector_data[sector]["top_score"]:
                sector_data[sector]["top_score"] = score
                sector_data[sector]["top_symbol"] = row[1]

        for sector, data in sector_data.items():
            avg = sum(data["scores"]) / len(data["scores"])
            await db.execute(
                """INSERT INTO sector_scores (sector, date, avg_score, top_symbol, top_score, stock_count)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(sector, date) DO UPDATE SET
                       avg_score=excluded.avg_score, top_symbol=excluded.top_symbol,
                       top_score=excluded.top_score, stock_count=excluded.stock_count""",
                (sector, today, round(avg, 1), data["top_symbol"],
                 data["top_score"], len(data["scores"])),
            )
        await db.commit()
    finally:
        await db.close()
