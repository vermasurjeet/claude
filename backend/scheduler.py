"""APScheduler configuration for automated data refresh."""

import logging
import asyncio
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# IST timezone offset
IST = timezone(timedelta(hours=5, minutes=30))


def is_market_hours() -> bool:
    """Check if current time is within Indian market hours (IST)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    market_open = now.replace(
        hour=settings.MARKET_OPEN_HOUR, minute=settings.MARKET_OPEN_MINUTE, second=0
    )
    market_close = now.replace(
        hour=settings.MARKET_CLOSE_HOUR, minute=settings.MARKET_CLOSE_MINUTE, second=0
    )
    return market_open <= now <= market_close


async def scheduled_refresh():
    """Scheduled job: refresh all stock scores."""
    from backend.analysis.scorer import refresh_all_scores

    logger.info("Scheduled refresh starting...")
    try:
        result = await refresh_all_scores()
        logger.info(f"Scheduled refresh complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled refresh failed: {e}")


async def intraday_price_update():
    """Intraday job: fetch latest prices and recompute technical scores.

    Only runs during market hours. Lighter than full refresh — skips
    fundamental data fetch and only updates prices + technical scores.
    """
    if not is_market_hours():
        return

    from backend.data.yahoo import fetch_ohlcv_batch, save_ohlcv_to_db
    from backend.data.universe import get_stock_list
    from backend.analysis.scorer import refresh_all_scores

    logger.info("Intraday price update starting...")
    try:
        stocks = get_stock_list()
        symbols = [s["symbol"] for s in stocks]

        # Fetch latest OHLCV (short period for speed)
        batch_data = fetch_ohlcv_batch(symbols, period="5d")
        for symbol, df in batch_data.items():
            await save_ohlcv_to_db(symbol, df)

        logger.info(f"Intraday update: fetched prices for {len(batch_data)} stocks")

        # Recompute all scores with updated prices
        result = await refresh_all_scores()
        logger.info(f"Intraday score refresh complete: {result}")

    except Exception as e:
        logger.error(f"Intraday update failed: {e}")


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    # Daily full refresh at configured time (default 6 PM)
    scheduler.add_job(
        scheduled_refresh,
        trigger=CronTrigger(
            hour=settings.REFRESH_HOUR,
            minute=settings.REFRESH_MINUTE,
            day_of_week="mon-fri",
        ),
        id="daily_refresh",
        name="Daily stock score refresh",
        replace_existing=True,
    )

    # Intraday price refresh every N minutes during market hours
    if settings.INTRADAY_ENABLED:
        scheduler.add_job(
            intraday_price_update,
            trigger=IntervalTrigger(minutes=settings.INTRADAY_INTERVAL_MINUTES),
            id="intraday_refresh",
            name=f"Intraday price update (every {settings.INTRADAY_INTERVAL_MINUTES}min)",
            replace_existing=True,
        )
        logger.info(
            f"Intraday refresh enabled: every {settings.INTRADAY_INTERVAL_MINUTES} min "
            f"during market hours ({settings.MARKET_OPEN_HOUR}:{settings.MARKET_OPEN_MINUTE:02d}"
            f"-{settings.MARKET_CLOSE_HOUR}:{settings.MARKET_CLOSE_MINUTE:02d} IST)"
        )

    scheduler.start()
    logger.info(
        f"Scheduler started. Daily refresh at "
        f"{settings.REFRESH_HOUR}:{settings.REFRESH_MINUTE:02d} UTC (Mon-Fri)"
    )


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
