"""Seed script: loads scraped Google Finance data into the DB and computes scores."""

import asyncio
import json
import random
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Scraped data from Google Finance via Firecrawl (March 2026)
SCRAPED_DATA = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "price": 1348.0, "change_percent": -4.61, "pe_ratio": 21.92, "market_cap": "18.24T INR", "high_52w": 1611.8, "low_52w": 1114.85, "previous_close": 1413.1, "eps": 184.89, "sector": "Energy"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "price": 2387.5, "change_percent": 0.42, "pe_ratio": 18.1, "market_cap": "8.65T INR", "high_52w": 3663.0, "low_52w": 2348.0, "previous_close": 2377.4, "eps": 36.59, "sector": "Technology"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "price": 757.95, "change_percent": -3.11, "pe_ratio": 15.68, "market_cap": "5.79T INR", "high_52w": 1020.5, "low_52w": 741.05, "previous_close": 782.3, "eps": 48.34, "sector": "Financial Services"},
    {"symbol": "INFY", "name": "Infosys Ltd", "price": 1267.5, "change_percent": -0.91, "pe_ratio": 18.78, "market_cap": "5.26T INR", "high_52w": 1728.0, "low_52w": 1215.1, "previous_close": 1279.1, "eps": 67.49, "sector": "Technology"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "price": 1237.9, "change_percent": -1.73, "pe_ratio": 16.89, "market_cap": "8.80T INR", "high_52w": 1500.0, "low_52w": 1218.1, "previous_close": 1259.7, "eps": 73.3, "sector": "Financial Services"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "price": 2075.0, "change_percent": -2.80, "pe_ratio": 33.6, "market_cap": "4.87T INR", "high_52w": 2715.44, "low_52w": 2033.3, "previous_close": 2134.8, "eps": 30.22, "sector": "Consumer Staples"},
    {"symbol": "ITC", "name": "ITC Ltd", "price": 294.55, "change_percent": -0.39, "pe_ratio": 10.54, "market_cap": "3.69T INR", "high_52w": 444.2, "low_52w": 288.75, "previous_close": 295.7, "eps": 4.23, "sector": "Consumer Staples"},
    {"symbol": "SBIN", "name": "State Bank of India", "price": 1019.2, "change_percent": -3.90, "pe_ratio": 11.12, "market_cap": "9.42T INR", "high_52w": 1234.7, "low_52w": 730.0, "previous_close": 1060.6, "eps": 22.78, "sector": "Financial Services"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "price": 1850.0, "change_percent": 0.82, "pe_ratio": 36.6, "market_cap": "11.04T INR", "high_52w": 2174.5, "low_52w": 1660.0, "previous_close": 1834.9, "eps": 11.5, "sector": "Communication"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "price": 846.5, "change_percent": -4.11, "pe_ratio": 29.22, "market_cap": "524.51B INR", "high_52w": 1102.5, "low_52w": 787.9, "previous_close": 882.75, "eps": 8.79, "sector": "Financial Services"},
]

# Additional stocks with estimated data from universe
ADDITIONAL_STOCKS = [
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "price": 1950.0, "pe_ratio": 18.5, "market_cap": "3.87T INR", "high_52w": 2300.0, "low_52w": 1700.0, "eps": 105.4, "sector": "Financial Services"},
    {"symbol": "LT", "name": "Larsen & Toubro", "price": 3280.0, "pe_ratio": 32.5, "market_cap": "4.49T INR", "high_52w": 3950.0, "low_52w": 2800.0, "eps": 100.9, "sector": "Industrials"},
    {"symbol": "AXISBANK", "name": "Axis Bank", "price": 1085.0, "pe_ratio": 12.3, "market_cap": "3.36T INR", "high_52w": 1320.0, "low_52w": 950.0, "eps": 88.2, "sector": "Financial Services"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki", "price": 11500.0, "pe_ratio": 25.8, "market_cap": "3.61T INR", "high_52w": 13600.0, "low_52w": 10000.0, "eps": 445.7, "sector": "Consumer Discretionary"},
    {"symbol": "TITAN", "name": "Titan Company", "price": 3150.0, "pe_ratio": 68.5, "market_cap": "2.80T INR", "high_52w": 3850.0, "low_52w": 2700.0, "eps": 46.0, "sector": "Consumer Discretionary"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical", "price": 1620.0, "pe_ratio": 35.2, "market_cap": "3.89T INR", "high_52w": 1920.0, "low_52w": 1400.0, "eps": 46.0, "sector": "Healthcare"},
    {"symbol": "WIPRO", "name": "Wipro", "price": 248.0, "pe_ratio": 17.5, "market_cap": "2.59T INR", "high_52w": 310.0, "low_52w": 210.0, "eps": 14.2, "sector": "Technology"},
    {"symbol": "HCLTECH", "name": "HCL Technologies", "price": 1480.0, "pe_ratio": 21.3, "market_cap": "4.02T INR", "high_52w": 1850.0, "low_52w": 1300.0, "eps": 69.5, "sector": "Technology"},
    {"symbol": "NTPC", "name": "NTPC", "price": 310.0, "pe_ratio": 14.8, "market_cap": "3.01T INR", "high_52w": 420.0, "low_52w": 280.0, "eps": 20.9, "sector": "Utilities"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors", "price": 620.0, "pe_ratio": 7.2, "market_cap": "2.28T INR", "high_52w": 1050.0, "low_52w": 580.0, "eps": 86.1, "sector": "Consumer Discretionary"},
]

ALL_STOCKS = SCRAPED_DATA + ADDITIONAL_STOCKS


def parse_market_cap(mc_str: str) -> float:
    """Parse market cap string like '18.24T INR' to number."""
    if not mc_str:
        return 0
    mc_str = mc_str.replace(" INR", "").replace(",", "")
    if mc_str.endswith("T"):
        return float(mc_str[:-1]) * 1e12
    elif mc_str.endswith("B"):
        return float(mc_str[:-1]) * 1e9
    return 0


def generate_ohlcv(current_price: float, high_52w: float, low_52w: float, days: int = 252) -> pd.DataFrame:
    """Generate realistic OHLCV data working backwards from current price."""
    dates = pd.bdate_range(end=datetime(2026, 3, 28), periods=days)

    # Generate price path using geometric brownian motion
    price_range = high_52w - low_52w
    volatility = (price_range / current_price) * 0.01  # daily vol from 52w range
    drift = 0.0001  # slight upward drift

    prices = [current_price]
    for i in range(days - 1):
        change = prices[-1] * (drift + volatility * random.gauss(0, 1))
        new_price = max(low_52w * 0.95, min(high_52w * 1.05, prices[-1] - change))
        prices.append(new_price)

    prices.reverse()  # oldest first

    rows = []
    for i, date in enumerate(dates):
        close = prices[i]
        daily_range = close * random.uniform(0.005, 0.025)
        high = close + random.uniform(0, daily_range)
        low = close - random.uniform(0, daily_range)
        open_price = close + random.uniform(-daily_range * 0.5, daily_range * 0.5)
        volume = int(random.uniform(500000, 15000000))
        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "Open": round(open_price, 2),
            "High": round(high, 2),
            "Low": round(low, 2),
            "Close": round(close, 2),
            "Volume": volume,
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df


async def seed_database():
    """Seed the database with scraped + generated data."""
    from backend.db.connection import init_db, get_db
    from backend.data.universe import populate_stock_universe
    from backend.analysis.technical import aggregate_technical
    from backend.analysis.fundamental import aggregate_fundamental
    from backend.analysis.quantitative import aggregate_quantitative, compute_sector_returns

    # Init DB and populate universe
    await init_db()
    await populate_stock_universe()
    print(f"Database initialized, stock universe populated")

    db = await get_db()
    now = datetime.utcnow().isoformat()

    # Generate OHLCV and fundamentals for each stock
    all_ohlcv = {}
    sector_dfs = {}

    for stock in ALL_STOCKS:
        symbol = stock["symbol"]
        price = stock["price"]
        high_52w = stock.get("high_52w", price * 1.3)
        low_52w = stock.get("low_52w", price * 0.7)
        sector = stock["sector"]

        # Generate OHLCV
        ohlcv = generate_ohlcv(price, high_52w, low_52w)
        all_ohlcv[symbol] = ohlcv

        # Save OHLCV to DB
        for date, row in ohlcv.iterrows():
            await db.execute(
                """INSERT OR REPLACE INTO price_history (symbol, date, open, high, low, close, volume)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (symbol, date.strftime("%Y-%m-%d"), float(row["Open"]), float(row["High"]),
                 float(row["Low"]), float(row["Close"]), int(row["Volume"])),
            )

        # Save fundamentals
        mc = parse_market_cap(stock.get("market_cap", ""))
        pe = stock.get("pe_ratio")
        eps = stock.get("eps")
        roe = random.uniform(0.08, 0.28)  # estimated
        de = random.uniform(0.1, 1.5)
        eps_growth = random.uniform(-0.1, 0.35)
        rev_growth = random.uniform(-0.05, 0.25)
        promoter = random.uniform(45, 75)

        await db.execute(
            """INSERT OR REPLACE INTO fundamentals
               (symbol, pe_ratio, pb_ratio, roe, debt_to_equity, eps_growth,
                revenue_growth, promoter_holding, market_cap, dividend_yield, info_json, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (symbol, pe, None, roe, de, eps_growth, rev_growth, promoter, mc, None, "{}", now),
        )

        # Track sector data
        if sector not in sector_dfs:
            sector_dfs[sector] = []
        sector_dfs[sector].append(ohlcv)

        print(f"  Seeded {symbol}: price={price}, PE={pe}")

    await db.commit()

    # Compute sector returns
    sector_avg = {}
    for sector, dfs in sector_dfs.items():
        combined = pd.concat([df["Close"] for df in dfs], axis=1)
        avg = combined.mean(axis=1)
        sector_avg[sector] = pd.DataFrame({"Close": avg})
    sector_returns = compute_sector_returns(sector_avg)

    # Generate Nifty50 benchmark
    benchmark = generate_ohlcv(22500, 26300, 19500)

    # Compute conviction scores
    print("\nComputing conviction scores...")
    for stock in ALL_STOCKS:
        symbol = stock["symbol"]
        ohlcv = all_ohlcv[symbol]
        sector = stock["sector"]

        # Build info dict for fundamental scoring
        cursor = await db.execute("SELECT * FROM fundamentals WHERE symbol = ?", (symbol,))
        fund_row = await cursor.fetchone()
        info = {
            "symbol": symbol,
            "pe_ratio": fund_row[1] if fund_row else None,
            "roe": fund_row[3] if fund_row else None,
            "debt_to_equity": fund_row[4] if fund_row else None,
            "eps_growth": fund_row[5] if fund_row else None,
            "revenue_growth": fund_row[6] if fund_row else None,
            "promoter_holding": fund_row[7] if fund_row else None,
        }

        # Technical
        tech_score, tech_details = aggregate_technical(ohlcv)

        # Fundamental
        fund_score, fund_details = aggregate_fundamental(info)

        # Quantitative
        quant_score, quant_details = aggregate_quantitative(
            ohlcv, benchmark, sector_returns, sector
        )

        # Weighted total
        total = (0.40 * tech_score + 0.35 * fund_score + 0.25 * quant_score)

        details = {
            "technical": tech_details,
            "fundamental": fund_details,
            "quantitative": quant_details,
        }

        await db.execute(
            """INSERT INTO scores (symbol, computed_at, total_score, technical_score,
                                   fundamental_score, quant_score, details_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (symbol, now, round(total, 1), tech_score, fund_score, quant_score,
             json.dumps(details)),
        )

        print(f"  {symbol}: Score={total:.1f} (T={tech_score:.1f} F={fund_score:.1f} Q={quant_score:.1f})")

    await db.commit()

    # Update sector scores
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cursor = await db.execute(
        """SELECT s.sector, sc.symbol, sc.total_score
           FROM scores sc JOIN stocks s ON sc.symbol = s.symbol
           ORDER BY s.sector"""
    )
    rows = await cursor.fetchall()
    sector_data = {}
    for row in rows:
        sector = row[0]
        if sector and sector not in sector_data:
            sector_data[sector] = {"scores": [], "top_symbol": "", "top_score": 0}
        if sector:
            sector_data[sector]["scores"].append(row[2])
            if row[2] > sector_data[sector]["top_score"]:
                sector_data[sector]["top_score"] = row[2]
                sector_data[sector]["top_symbol"] = row[1]

    for sector, data in sector_data.items():
        avg = sum(data["scores"]) / len(data["scores"])
        await db.execute(
            """INSERT OR REPLACE INTO sector_scores (sector, date, avg_score, top_symbol, top_score, stock_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sector, today, round(avg, 1), data["top_symbol"], data["top_score"], len(data["scores"])),
        )

    await db.commit()
    await db.close()

    print(f"\nDone! Seeded {len(ALL_STOCKS)} stocks with scores and sector data.")


if __name__ == "__main__":
    asyncio.run(seed_database())
