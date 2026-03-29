"""Stock API endpoints."""

import json
from fastapi import APIRouter, Query

from backend.db.connection import execute_query

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("")
async def list_stocks(
    sector: str = Query(None, description="Filter by sector"),
    min_score: float = Query(None, ge=0, le=100),
    max_score: float = Query(None, ge=0, le=100),
    sort_by: str = Query("score", regex="^(score|name|change|sector)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    search: str = Query(None, description="Search by symbol or name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List stocks with latest conviction scores, filterable and sortable."""
    # Build query to get latest score per stock
    query = """
        SELECT s.symbol, s.name, s.sector, s.industry, s.market_cap,
               sc.total_score, sc.technical_score, sc.fundamental_score,
               sc.quant_score, sc.computed_at, sc.details_json,
               ph.close as last_price,
               CASE WHEN ph2.close > 0
                    THEN ROUND((ph.close - ph2.close) / ph2.close * 100, 2)
                    ELSE NULL END as change_pct
        FROM stocks s
        LEFT JOIN scores sc ON s.symbol = sc.symbol
            AND sc.computed_at = (
                SELECT MAX(sc2.computed_at) FROM scores sc2
                WHERE sc2.symbol = sc.symbol
            )
        LEFT JOIN price_history ph ON s.symbol = ph.symbol
            AND ph.date = (
                SELECT MAX(ph3.date) FROM price_history ph3
                WHERE ph3.symbol = ph.symbol
            )
        LEFT JOIN price_history ph2 ON s.symbol = ph2.symbol
            AND ph2.date = (
                SELECT MAX(ph4.date) FROM price_history ph4
                WHERE ph4.symbol = ph.symbol AND ph4.date < ph.date
            )
        WHERE s.is_active = 1
    """
    params = []

    if sector:
        query += " AND s.sector = ?"
        params.append(sector)

    if min_score is not None:
        query += " AND sc.total_score >= ?"
        params.append(min_score)

    if max_score is not None:
        query += " AND sc.total_score <= ?"
        params.append(max_score)

    if search:
        query += " AND (s.symbol LIKE ? OR s.name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Sorting
    sort_map = {
        "score": "sc.total_score",
        "name": "s.name",
        "change": "change_pct",
        "sector": "s.sector",
    }
    sort_col = sort_map.get(sort_by, "sc.total_score")
    query += f" ORDER BY {sort_col} {'DESC' if order == 'desc' else 'ASC'} NULLS LAST"
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = await execute_query(query, tuple(params))

    # Get total count
    count_query = """
        SELECT COUNT(*) as cnt FROM stocks s
        LEFT JOIN scores sc ON s.symbol = sc.symbol
            AND sc.computed_at = (
                SELECT MAX(sc2.computed_at) FROM scores sc2
                WHERE sc2.symbol = sc.symbol
            )
        WHERE s.is_active = 1
    """
    count_params = []
    if sector:
        count_query += " AND s.sector = ?"
        count_params.append(sector)
    if min_score is not None:
        count_query += " AND sc.total_score >= ?"
        count_params.append(min_score)
    if max_score is not None:
        count_query += " AND sc.total_score <= ?"
        count_params.append(max_score)
    if search:
        count_query += " AND (s.symbol LIKE ? OR s.name LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])

    count_result = await execute_query(count_query, tuple(count_params), fetch="one")
    total = count_result["cnt"] if count_result else 0

    return {
        "stocks": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{symbol}")
async def get_stock_detail(symbol: str):
    """Get detailed info for a single stock including score breakdown."""
    # Stock info
    stock = await execute_query(
        "SELECT * FROM stocks WHERE symbol = ?", (symbol,), fetch="one"
    )
    if not stock:
        return {"error": "Stock not found"}

    # Latest score
    score = await execute_query(
        """SELECT * FROM scores WHERE symbol = ?
           ORDER BY computed_at DESC LIMIT 1""",
        (symbol,), fetch="one",
    )

    # Fundamentals
    fundamentals = await execute_query(
        "SELECT * FROM fundamentals WHERE symbol = ?",
        (symbol,), fetch="one",
    )

    # Recent price history (30 days)
    prices = await execute_query(
        """SELECT date, open, high, low, close, volume
           FROM price_history WHERE symbol = ?
           ORDER BY date DESC LIMIT 90""",
        (symbol,),
    )

    # Score history (last 90 entries)
    score_history = await execute_query(
        """SELECT computed_at, total_score, technical_score,
                  fundamental_score, quant_score
           FROM scores WHERE symbol = ?
           ORDER BY computed_at DESC LIMIT 90""",
        (symbol,),
    )

    # Parse details JSON
    details = None
    if score and score.get("details_json"):
        try:
            details = json.loads(score["details_json"])
        except (json.JSONDecodeError, TypeError):
            details = None

    return {
        "stock": stock,
        "score": score,
        "details": details,
        "fundamentals": fundamentals,
        "prices": list(reversed(prices)),
        "score_history": list(reversed(score_history)),
    }
