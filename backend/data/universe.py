"""Stock universe management — Nifty 50/500 constituent lists."""

from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

from backend.db.connection import get_db

# Nifty 50 constituents with sectors (as of 2025)
NIFTY50_STOCKS = [
    ("RELIANCE", "Reliance Industries", "Energy", "Oil & Gas"),
    ("TCS", "Tata Consultancy Services", "Technology", "IT Services"),
    ("HDFCBANK", "HDFC Bank", "Financial Services", "Banks"),
    ("INFY", "Infosys", "Technology", "IT Services"),
    ("ICICIBANK", "ICICI Bank", "Financial Services", "Banks"),
    ("HINDUNILVR", "Hindustan Unilever", "Consumer Staples", "FMCG"),
    ("ITC", "ITC", "Consumer Staples", "FMCG"),
    ("SBIN", "State Bank of India", "Financial Services", "Banks"),
    ("BHARTIARTL", "Bharti Airtel", "Communication", "Telecom"),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Financial Services", "Banks"),
    ("LT", "Larsen & Toubro", "Industrials", "Construction"),
    ("AXISBANK", "Axis Bank", "Financial Services", "Banks"),
    ("ASIANPAINT", "Asian Paints", "Materials", "Paints"),
    ("MARUTI", "Maruti Suzuki", "Consumer Discretionary", "Automobiles"),
    ("TITAN", "Titan Company", "Consumer Discretionary", "Jewellery"),
    ("SUNPHARMA", "Sun Pharmaceutical", "Healthcare", "Pharmaceuticals"),
    ("BAJFINANCE", "Bajaj Finance", "Financial Services", "NBFC"),
    ("WIPRO", "Wipro", "Technology", "IT Services"),
    ("HCLTECH", "HCL Technologies", "Technology", "IT Services"),
    ("NTPC", "NTPC", "Utilities", "Power"),
    ("POWERGRID", "Power Grid Corp", "Utilities", "Power"),
    ("TATAMOTORS", "Tata Motors", "Consumer Discretionary", "Automobiles"),
    ("ULTRACEMCO", "UltraTech Cement", "Materials", "Cement"),
    ("ONGC", "Oil & Natural Gas Corp", "Energy", "Oil & Gas"),
    ("NESTLEIND", "Nestle India", "Consumer Staples", "FMCG"),
    ("JSWSTEEL", "JSW Steel", "Materials", "Steel"),
    ("TATASTEEL", "Tata Steel", "Materials", "Steel"),
    ("M&M", "Mahindra & Mahindra", "Consumer Discretionary", "Automobiles"),
    ("ADANIENT", "Adani Enterprises", "Industrials", "Conglomerate"),
    ("ADANIPORTS", "Adani Ports", "Industrials", "Ports"),
    ("COALINDIA", "Coal India", "Energy", "Mining"),
    ("BAJAJFINSV", "Bajaj Finserv", "Financial Services", "NBFC"),
    ("TECHM", "Tech Mahindra", "Technology", "IT Services"),
    ("HDFCLIFE", "HDFC Life Insurance", "Financial Services", "Insurance"),
    ("SBILIFE", "SBI Life Insurance", "Financial Services", "Insurance"),
    ("DIVISLAB", "Divi's Laboratories", "Healthcare", "Pharmaceuticals"),
    ("GRASIM", "Grasim Industries", "Materials", "Cement"),
    ("DRREDDY", "Dr. Reddy's Laboratories", "Healthcare", "Pharmaceuticals"),
    ("CIPLA", "Cipla", "Healthcare", "Pharmaceuticals"),
    ("BRITANNIA", "Britannia Industries", "Consumer Staples", "FMCG"),
    ("EICHERMOT", "Eicher Motors", "Consumer Discretionary", "Automobiles"),
    ("APOLLOHOSP", "Apollo Hospitals", "Healthcare", "Hospitals"),
    ("INDUSINDBK", "IndusInd Bank", "Financial Services", "Banks"),
    ("HEROMOTOCO", "Hero MotoCorp", "Consumer Discretionary", "Automobiles"),
    ("BAJAJ-AUTO", "Bajaj Auto", "Consumer Discretionary", "Automobiles"),
    ("TATACONSUM", "Tata Consumer Products", "Consumer Staples", "FMCG"),
    ("WIPRO", "Wipro", "Technology", "IT Services"),
    ("BPCL", "Bharat Petroleum", "Energy", "Oil & Gas"),
    ("HINDALCO", "Hindalco Industries", "Materials", "Metals"),
    ("LTIM", "LTIMindtree", "Technology", "IT Services"),
]

# Sector mapping for quick lookups
SECTOR_MAP = {}
for sym, _, sector, _ in NIFTY50_STOCKS:
    SECTOR_MAP[sym] = sector


def get_yahoo_symbol(symbol: str) -> str:
    """Convert NSE symbol to Yahoo Finance symbol."""
    return f"{symbol}.NS"


def get_stock_list() -> list[dict]:
    """Get list of all stocks with metadata."""
    seen = set()
    stocks = []
    for symbol, name, sector, industry in NIFTY50_STOCKS:
        if symbol not in seen:
            seen.add(symbol)
            stocks.append({
                "symbol": symbol,
                "name": name,
                "sector": sector,
                "industry": industry,
                "yahoo_symbol": get_yahoo_symbol(symbol),
            })
    return stocks


async def populate_stock_universe():
    """Insert/update stock universe into database."""
    stocks = get_stock_list()
    now = datetime.now(IST).isoformat()

    db = await get_db()
    try:
        for stock in stocks:
            await db.execute(
                """INSERT INTO stocks (symbol, name, sector, industry, yahoo_symbol, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(symbol) DO UPDATE SET
                       name=excluded.name, sector=excluded.sector,
                       industry=excluded.industry, yahoo_symbol=excluded.yahoo_symbol,
                       updated_at=excluded.updated_at""",
                (stock["symbol"], stock["name"], stock["sector"],
                 stock["industry"], stock["yahoo_symbol"], now),
            )
        await db.commit()
    finally:
        await db.close()

    return len(stocks)


async def get_active_symbols() -> list[str]:
    """Get all active stock symbols."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT symbol FROM stocks WHERE is_active = 1"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        await db.close()


async def get_sector_symbols(sector: str) -> list[str]:
    """Get all symbols in a sector."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT symbol FROM stocks WHERE sector = ? AND is_active = 1",
            (sector,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        await db.close()
