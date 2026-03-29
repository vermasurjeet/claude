"""Score-related API endpoints."""

from fastapi import APIRouter, Query

from backend.db.connection import execute_query

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.get("/top")
async def get_top_stocks(n: int = Query(20, ge=1, le=100)):
    """Get top N stocks by conviction score."""
    rows = await execute_query(
        """SELECT s.symbol, s.name, s.sector,
                  sc.total_score, sc.technical_score,
                  sc.fundamental_score, sc.quant_score,
                  sc.computed_at
           FROM scores sc
           JOIN stocks s ON sc.symbol = s.symbol
           WHERE sc.computed_at = (
               SELECT MAX(sc2.computed_at) FROM scores sc2
               WHERE sc2.symbol = sc.symbol
           )
           ORDER BY sc.total_score DESC
           LIMIT ?""",
        (n,),
    )
    return {"stocks": rows}


@router.get("/history/{symbol}")
async def get_score_history(
    symbol: str,
    days: int = Query(90, ge=1, le=365),
):
    """Get historical conviction scores for a stock."""
    rows = await execute_query(
        """SELECT computed_at, total_score, technical_score,
                  fundamental_score, quant_score
           FROM scores
           WHERE symbol = ?
           ORDER BY computed_at DESC
           LIMIT ?""",
        (symbol, days),
    )
    return {"symbol": symbol, "history": list(reversed(rows))}


@router.get("/changes")
async def get_score_changes(days: int = Query(7, ge=1, le=30)):
    """Get stocks with biggest conviction score changes."""
    rows = await execute_query(
        """WITH latest AS (
               SELECT symbol, total_score, computed_at,
                      ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY computed_at DESC) as rn
               FROM scores
           ),
           previous AS (
               SELECT symbol, total_score, computed_at,
                      ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY computed_at DESC) as rn
               FROM scores
               WHERE computed_at < date('now', ? || ' days')
           )
           SELECT l.symbol, s.name, s.sector,
                  l.total_score as current_score,
                  p.total_score as previous_score,
                  ROUND(l.total_score - p.total_score, 1) as change
           FROM latest l
           JOIN previous p ON l.symbol = p.symbol AND p.rn = 1
           JOIN stocks s ON l.symbol = s.symbol
           WHERE l.rn = 1
           ORDER BY ABS(l.total_score - p.total_score) DESC
           LIMIT 20""",
        (f"-{days}",),
    )
    return {"changes": rows, "days": days}
