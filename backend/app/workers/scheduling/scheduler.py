"""APScheduler wiring for briefing jobs."""

import logging
from typing import Optional, List, TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.workers.core.types import JobResult

if TYPE_CHECKING:
    from app.services.workers.briefing_job_runner import BriefingJobRunner

logger = logging.getLogger(__name__)


class WorkerScheduler:
    """Thin scheduler that delegates work to `BriefingJobRunner`."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self._job_runner = None

    @property
    def job_runner(self):
        """Lazy import to avoid circular dependency."""
        if self._job_runner is None:
            from app.services.workers.briefing_job_runner import get_briefing_job_runner
            self._job_runner = get_briefing_job_runner()
        return self._job_runner

    async def start(self) -> None:
        logger.info("Starting worker scheduler...")

        self.scheduler.add_job(
            func=self.job_runner.run_daily_briefings,
            trigger=CronTrigger(minute="*/15"),
            id="daily_briefings",
            name="Daily Briefing Job",
            replace_existing=True,
        )

        self.scheduler.add_job(
            func=self.job_runner.run_weekly_pulse,
            trigger=CronTrigger(minute=0),
            id="weekly_pulse",
            name="Weekly Pulse Job",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Worker scheduler started successfully")

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Worker scheduler stopped")

    async def run_daily_briefings(self) -> List[JobResult]:
        """Expose runner method for direct invocations/tests."""

        return await self.job_runner.run_daily_briefings()

    async def run_weekly_pulse(self) -> List[JobResult]:
        return await self.job_runner.run_weekly_pulse()


_scheduler: Optional[WorkerScheduler] = None


def get_worker_scheduler() -> WorkerScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = WorkerScheduler()
    return _scheduler

