"""Configuration and control API endpoints."""

import asyncio
from fastapi import APIRouter, BackgroundTasks

from backend.db.connection import execute_query, get_db
from backend.config import settings

router = APIRouter(prefix="/api", tags=["config"])

# Track refresh state
_refresh_state = {"running": False, "progress": 0, "total": 0, "current": "", "last_result": None}


@router.get("/config")
async def get_config():
    """Get current scoring configuration."""
    return {
        "weights": {
            "technical": settings.WEIGHT_TECHNICAL,
            "fundamental": settings.WEIGHT_FUNDAMENTAL,
            "quantitative": settings.WEIGHT_QUANTITATIVE,
        },
        "universe": settings.STOCK_UNIVERSE,
        "refresh_schedule": f"{settings.REFRESH_HOUR}:{settings.REFRESH_MINUTE:02d} UTC",
    }


@router.get("/config/watchlist")
async def get_watchlist():
    """Get current watchlist (active stocks)."""
    rows = await execute_query(
        "SELECT symbol, name, sector FROM stocks WHERE is_active = 1 ORDER BY symbol"
    )
    return {"watchlist": rows}


@router.put("/config/watchlist")
async def update_watchlist(body: dict):
    """Update watchlist — set which stocks are active.

    Body: {"symbols": ["RELIANCE", "TCS", ...]}
    """
    symbols = body.get("symbols", [])
    if not symbols:
        return {"error": "No symbols provided"}

    db = await get_db()
    try:
        # Deactivate all
        await db.execute("UPDATE stocks SET is_active = 0")
        # Activate selected
        placeholders = ",".join(["?"] * len(symbols))
        await db.execute(
            f"UPDATE stocks SET is_active = 1 WHERE symbol IN ({placeholders})",
            symbols,
        )
        await db.commit()
    finally:
        await db.close()

    return {"updated": len(symbols)}


@router.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    """Trigger a manual full refresh of all scores."""
    if _refresh_state["running"]:
        return {"status": "already_running", "progress": _refresh_state}

    _refresh_state["running"] = True
    _refresh_state["progress"] = 0

    background_tasks.add_task(_run_refresh)
    return {"status": "started"}


@router.get("/refresh/status")
async def refresh_status():
    """Get current refresh status."""
    return _refresh_state


@router.get("/health")
async def health_check():
    """System health check."""
    from backend.scheduler import is_market_hours

    stock_count = await execute_query(
        "SELECT COUNT(*) as cnt FROM stocks WHERE is_active = 1", fetch="one"
    )
    score_count = await execute_query(
        "SELECT COUNT(*) as cnt FROM scores", fetch="one"
    )
    last_refresh = await execute_query(
        "SELECT MAX(computed_at) as last FROM scores", fetch="one"
    )

    return {
        "status": "ok",
        "stocks": stock_count["cnt"] if stock_count else 0,
        "scores": score_count["cnt"] if score_count else 0,
        "last_refresh": last_refresh["last"] if last_refresh else None,
        "market_open": is_market_hours(),
        "intraday_enabled": settings.INTRADAY_ENABLED,
        "intraday_interval": settings.INTRADAY_INTERVAL_MINUTES,
    }


async def _run_refresh():
    """Background task for full refresh."""
    from backend.analysis.scorer import refresh_all_scores

    def progress_cb(current, total, symbol):
        _refresh_state["progress"] = current
        _refresh_state["total"] = total
        _refresh_state["current"] = symbol

    try:
        result = await refresh_all_scores(progress_callback=progress_cb)
        _refresh_state["last_result"] = result
    except Exception as e:
        _refresh_state["last_result"] = {"error": str(e)}
    finally:
        _refresh_state["running"] = False
