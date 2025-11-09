"""Canvas sync scheduler - coordinates delta + nightly jobs via APScheduler."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config.database.supabase import get_supabase_client
from app.services.workers.canvas_job_runner import get_canvas_job_runner

logger = logging.getLogger(__name__)


class CanvasScheduler:
    """Thin APScheduler wrapper for Canvas sync routines."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.job_runner = get_canvas_job_runner()
        self.supabase = get_supabase_client()
        self.max_concurrent_delta = 5

    async def start(self) -> None:
        logger.info("Starting canvas scheduler...")

        # Delta sync cycle every 20 minutes (similar to calendar incremental pulls)
        self.scheduler.add_job(
            func=self.run_delta_cycle,
            trigger=CronTrigger(minute="*/20"),
            id="canvas_delta_sync",
            name="Canvas Delta Sync",
            replace_existing=True,
        )

        # Nightly catch-up job at 02:30 UTC
        self.scheduler.add_job(
            func=self.run_nightly_sync,
            trigger=CronTrigger(hour=2, minute=30),
            id="canvas_nightly_sync",
            name="Canvas Nightly Sync",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Canvas scheduler started")

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Canvas scheduler stopped")

    async def run_delta_cycle(self) -> None:
        """Incrementally sync all active Canvas users."""
        users = await self._get_active_canvas_users()
        if not users:
            logger.info("No active Canvas integrations for delta sync")
            return

        logger.info("Running Canvas delta sync for %s users", len(users))
        semaphore = asyncio.Semaphore(self.max_concurrent_delta)
        tasks = [self._sync_user_delta(user_id, semaphore) for user_id in users]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures = sum(1 for result in results if isinstance(result, Exception) or result is False)
        logger.info(
            "Canvas delta cycle complete. Success: %s, Failed: %s",
            len(users) - failures,
            failures,
        )

    async def _sync_user_delta(self, user_id: str, semaphore: asyncio.Semaphore) -> bool:
        async with semaphore:
            try:
                result = await self.job_runner.run_delta_sync(user_id)
                if result.get("status") == "completed":
                    return True
                logger.warning("Canvas delta sync for user %s returned error: %s", user_id, result.get("errors"))
                return False
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Canvas delta sync failed for user %s: %s", user_id, exc, exc_info=True)
                return False

    async def run_nightly_sync(self) -> None:
        try:
            await self.job_runner.run_nightly_sync()
        except Exception as exc:
            logger.error("Nightly Canvas sync failed: %s", exc, exc_info=True)

    async def _get_active_canvas_users(self) -> List[str]:
        try:
            response = await self.supabase.table("canvas_integrations").select("user_id, is_active").eq("is_active", True).execute()
            if not response.data:
                return []
            return [row["user_id"] for row in response.data if row.get("user_id")]
        except Exception as exc:
            logger.error("Failed to fetch active Canvas users: %s", exc, exc_info=True)
            return []


_canvas_scheduler: Optional[CanvasScheduler] = None


def get_canvas_scheduler() -> CanvasScheduler:
    global _canvas_scheduler
    if _canvas_scheduler is None:
        _canvas_scheduler = CanvasScheduler()
    return _canvas_scheduler
