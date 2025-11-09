"""Usage aggregation job runner."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.database.repositories.integration_repositories import get_usage_repository

logger = logging.getLogger(__name__)


class UsageJobRunner:
    """Handles monthly aggregation and daily quota checks."""

    def __init__(self, usage_repository=None) -> None:
        self.usage_repository = usage_repository or get_usage_repository()

    async def run_monthly_aggregation(self) -> None:
        logger.info("Starting monthly usage aggregation job")

        try:
            await self.usage_repository.aggregate_monthly_usage()
            await self.usage_repository.reset_all_monthly_quotas()
            logger.info("Monthly usage aggregation completed successfully")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error during monthly usage aggregation: %s", exc, exc_info=True)
            raise

    async def run_daily_quota_check(self) -> None:
        logger.info("Running daily quota check")

        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)
            stats = await self.usage_repository.get_platform_usage_stats(start_date, end_date)
            logger.info(
                "Daily quota check complete. Active users: %s, Total tokens: %s",
                stats.get("active_users", 0),
                stats.get("total_tokens", 0),
            )
        except Exception as exc:
            logger.error("Error during daily quota check: %s", exc, exc_info=True)


_usage_runner: Optional[UsageJobRunner] = None


def get_usage_job_runner() -> UsageJobRunner:
    global _usage_runner
    if _usage_runner is None:
        _usage_runner = UsageJobRunner()
    return _usage_runner

