"""
Focus Profile Worker - Thin wrapper for APScheduler integration.

This module provides a backward-compatible interface for the legacy worker pattern
while delegating all business logic to FocusJobRunner.
"""

import logging
import asyncio
from typing import Optional

from app.services.workers.focus_job_runner import get_focus_job_runner, FocusJobRunner

logger = logging.getLogger(__name__)


class FocusProfileWorker:
    """
    Thin wrapper around FocusJobRunner for backward compatibility.
    
    This class maintains the old worker interface (start/stop loop) while
    delegating all business logic to FocusJobRunner.
    """

    def __init__(self):
        self.job_runner = get_focus_job_runner()
        self.is_running = False

    async def start(self, interval_seconds: int = 300):
        """
        Start the worker loop (legacy pattern).

        Args:
            interval_seconds: How often to check for updates (default 5 minutes)
        """
        logger.info(f"Starting Focus Profile Worker (interval: {interval_seconds}s)")
        self.is_running = True

        while self.is_running:
            try:
                await self.process_pending_updates()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in focus profile worker loop: {e}", exc_info=True)
                # Sleep before retrying
                await asyncio.sleep(60)

    def stop(self):
        """Stop the worker loop"""
        logger.info("Stopping Focus Profile Worker")
        self.is_running = False

    async def process_pending_updates(self):
        """
        Main processing function - delegates to job runner.
        """
        await self.job_runner.run_profile_updates()


# Global worker instance
_focus_profile_worker: Optional[FocusProfileWorker] = None


def get_focus_profile_worker() -> FocusProfileWorker:
    """Get or create the Focus Profile Worker singleton (backward compatibility)"""
    global _focus_profile_worker
    if _focus_profile_worker is None:
        _focus_profile_worker = FocusProfileWorker()
    return _focus_profile_worker


async def start_focus_profile_worker():
    """Start the focus profile worker (for use in main app startup)"""
    worker = get_focus_profile_worker()
    # Run in background without blocking
    asyncio.create_task(worker.start())
    logger.info("Focus Profile Worker started")








