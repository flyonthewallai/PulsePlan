"""
Calendar sync scheduler - thin wrapper for APScheduler integration.

This module provides APScheduler job registration while delegating all
business logic to CalendarJobRunner.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.workers.calendar_background_worker import get_calendar_job_runner

logger = logging.getLogger(__name__)


class CalendarScheduler:
    """Thin scheduler that delegates work to CalendarJobRunner."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.job_runner = get_calendar_job_runner()

    async def start(self):
        """Start the calendar scheduler and register jobs"""
        logger.info("Starting calendar sync scheduler...")

        # Incremental pull job - Run every 15-30 minutes during active hours
        # We'll run every 20 minutes as a balance
        self.scheduler.add_job(
            func=self.run_incremental_pulls,
            trigger=CronTrigger(minute="*/20"),  # Every 20 minutes
            id="calendar_incremental_pull",
            name="Calendar Incremental Pull Job",
            replace_existing=True,
        )

        # Watch channel renewal job - Run every hour to check for expiring channels
        self.scheduler.add_job(
            func=self.run_watch_renewals,
            trigger=CronTrigger(minute=0),  # Every hour
            id="calendar_watch_renewal",
            name="Calendar Watch Renewal Job",
            replace_existing=True,
        )

        # Auto-sync job - honors user preferences
        self.scheduler.add_job(
            func=self.run_auto_sync_cycle,
            trigger=CronTrigger(minute="*/10"),
            id="calendar_auto_sync",
            name="Calendar Auto Sync Job",
            replace_existing=True,
        )

        # Webhook processor - drains redis frequently
        self.scheduler.add_job(
            func=self.process_webhook_queue,
            trigger=CronTrigger(second="*/30"),
            id="calendar_webhook_processor",
            name="Calendar Webhook Processor",
            replace_existing=True,
        )

        # Conflict resolver job
        self.scheduler.add_job(
            func=self.run_conflict_resolution,
            trigger=CronTrigger(minute="*/30"),
            id="calendar_conflict_resolution",
            name="Calendar Conflict Resolution",
            replace_existing=True,
        )

        # Cleanup job - nightly at 03:00 UTC
        self.scheduler.add_job(
            func=self.run_cleanup_task,
            trigger=CronTrigger(hour=3, minute=0),
            id="calendar_cleanup",
            name="Calendar Data Cleanup",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Calendar sync scheduler started successfully")

    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Calendar sync scheduler stopped")

    async def run_incremental_pulls(self):
        """Trigger the job runner incremental pulls cycle."""
        try:
            await self.job_runner.run_incremental_pulls()
        except Exception as exc:
            logger.error(f"Incremental pulls failed: {exc}", exc_info=True)

    async def run_watch_renewals(self):
        """Trigger the job runner watch renewals cycle."""
        try:
            await self.job_runner.run_watch_renewals()
        except Exception as exc:
            logger.error(f"Watch renewals failed: {exc}", exc_info=True)

    async def run_auto_sync_cycle(self):
        """Trigger the job runner auto-sync cycle."""

        try:
            await self.job_runner.run_auto_sync_cycle()
        except Exception as exc:
            logger.error(f"Auto-sync cycle failed: {exc}")

    async def process_webhook_queue(self):
        """Drain webhook queue and process notifications."""

        try:
            await self.job_runner.process_webhook_queue()
        except Exception as exc:
            logger.error(f"Webhook queue processing failed: {exc}")

    async def run_conflict_resolution(self):
        """Resolve pending conflicts via job runner."""

        try:
            await self.job_runner.run_conflict_resolution()
        except Exception as exc:
            logger.error(f"Conflict resolution job failed: {exc}")

    async def run_cleanup_task(self):
        """Cleanup calendar data on schedule."""

        try:
            await self.job_runner.cleanup_calendar_data()
        except Exception as exc:
            logger.error(f"Calendar cleanup job failed: {exc}")



# Singleton instance
_calendar_scheduler = None


def get_calendar_scheduler() -> CalendarScheduler:
    """Get the calendar scheduler singleton."""
    global _calendar_scheduler
    if _calendar_scheduler is None:
        _calendar_scheduler = CalendarScheduler()
    return _calendar_scheduler
