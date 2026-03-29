"""Sector API endpoints."""

from fastapi import APIRouter

from backend.db.connection import execute_query

router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("")
async def list_sectors():
    """List all sectors with aggregate conviction scores."""
    rows = await execute_query(
        """SELECT ss.sector, ss.avg_score, ss.stock_count,
                  ss.top_symbol, ss.top_score
           FROM sector_scores ss
           WHERE ss.date = (SELECT MAX(date) FROM sector_scores)
           ORDER BY ss.avg_score DESC"""
    )

    if not rows:
        # Fallback: compute from scores table directly
        rows = await execute_query(
            """SELECT s.sector,
                      ROUND(AVG(sc.total_score), 1) as avg_score,
                      COUNT(*) as stock_count,
                      MAX(sc.total_score) as top_score
               FROM stocks s
               JOIN scores sc ON s.symbol = sc.symbol
                   AND sc.computed_at = (
                       SELECT MAX(sc2.computed_at) FROM scores sc2
                       WHERE sc2.symbol = sc.symbol
                   )
               WHERE s.sector IS NOT NULL
               GROUP BY s.sector
               ORDER BY avg_score DESC"""
        )

    return {"sectors": rows}


@router.get("/{sector_name}")
async def get_sector_detail(sector_name: str):
    """Get all stocks in a sector ranked by conviction score."""
    stocks = await execute_query(
        """SELECT s.symbol, s.name, s.industry,
                  sc.total_score, sc.technical_score,
                  sc.fundamental_score, sc.quant_score
           FROM stocks s
           JOIN scores sc ON s.symbol = sc.symbol
               AND sc.computed_at = (
                   SELECT MAX(sc2.computed_at) FROM scores sc2
                   WHERE sc2.symbol = sc.symbol
               )
           WHERE s.sector = ?
           ORDER BY sc.total_score DESC""",
        (sector_name,),
    )

    avg_score = (
        sum(s["total_score"] for s in stocks) / len(stocks)
        if stocks else 0
    )

    return {
        "sector": sector_name,
        "avg_score": round(avg_score, 1),
        "stock_count": len(stocks),
        "stocks": stocks,
    }
