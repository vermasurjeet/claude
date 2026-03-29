"""APScheduler configuration for automated data refresh."""

import logging
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_refresh():
    """Scheduled job: refresh all stock scores."""
    from backend.analysis.scorer import refresh_all_scores

    logger.info("Scheduled refresh starting...")
    try:
        result = await refresh_all_scores()
        logger.info(f"Scheduled refresh complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled refresh failed: {e}")


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    # Daily refresh at configured time (default 6 PM)
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
