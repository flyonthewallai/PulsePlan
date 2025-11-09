"""
Monthly usage aggregation job.

This job runs on the 1st of each month to:
1. Aggregate detailed usage data into monthly summaries
2. Clean up old detailed records (> 3 months)
3. Reset monthly quotas for all users
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.workers.usage_job_runner import get_usage_job_runner

logger = logging.getLogger(__name__)

runner = get_usage_job_runner()


async def run_monthly_aggregation():
    await runner.run_monthly_aggregation()


async def run_daily_quota_check():
    await runner.run_daily_quota_check()


def schedule_usage_jobs(scheduler: AsyncIOScheduler):
    """
    Schedule recurring usage jobs.

    Args:
        scheduler: APScheduler instance
    """
    # Run monthly aggregation on the 1st of each month at 2 AM
    scheduler.add_job(
        run_monthly_aggregation,
        trigger="cron",
        day=1,
        hour=2,
        minute=0,
        id="monthly_usage_aggregation",
        name="Monthly Usage Aggregation",
        replace_existing=True,
    )

    # Run daily quota check at 1 AM
    scheduler.add_job(
        run_daily_quota_check,
        trigger="cron",
        hour=1,
        minute=0,
        id="daily_quota_check",
        name="Daily Quota Check",
        replace_existing=True,
    )

    logger.info("Usage aggregation jobs scheduled successfully")
