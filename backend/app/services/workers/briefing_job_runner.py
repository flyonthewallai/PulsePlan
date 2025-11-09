"""Briefing job runner used by worker and timezone schedulers."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.config.database.supabase import get_supabase_client
from app.core.utils.timezone_utils import get_timezone_manager
from app.services.infrastructure.cache_service import get_cache_service
from app.workers.core.types import JobResult

if TYPE_CHECKING:
    from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class BriefingJobRunner:
    """Executes briefing-related jobs independent of any scheduler."""

    def __init__(
        self,
        *,
        supabase=None,
        email_service=None,
        agent_orchestrator=None,
        cache_service=None,
    ) -> None:
        self.supabase = supabase or get_supabase_client()
        self._email_service = email_service
        self._agent_orchestrator = agent_orchestrator
        self.cache_service = cache_service or get_cache_service()
        self.timezone_manager = get_timezone_manager()

    @property
    def email_service(self):
        """Lazy import to avoid circular dependency."""
        if self._email_service is None:
            from app.workers.communication.email_service import get_email_service
            self._email_service = get_email_service()
        return self._email_service

    @property
    def agent_orchestrator(self):
        """Lazy import to avoid circular dependency."""
        if self._agent_orchestrator is None:
            from app.agents.orchestrator import get_agent_orchestrator
            self._agent_orchestrator = get_agent_orchestrator()
        return self._agent_orchestrator

    # ------------------------------------------------------------------
    # Public job entry points
    # ------------------------------------------------------------------

    async def run_daily_briefings(self) -> List[JobResult]:
        """Generate and send daily briefings for eligible users."""

        logger.info("Starting daily briefing job execution")
        start_time = datetime.utcnow()
        users = await self._get_briefing_eligible_users()

        if not users:
            logger.info("No eligible users for daily briefing")
            return []

        results = await self._process_users(users, self._process_daily_briefing)
        self._log_summary("Daily briefing job", results, start_time)
        return results

    async def run_weekly_pulse(self) -> List[JobResult]:
        """Generate and send weekly pulse emails for eligible users."""

        logger.info("Starting weekly pulse job execution")
        start_time = datetime.utcnow()
        users = await self._get_pulse_eligible_users()

        if not users:
            logger.info("No eligible users for weekly pulse")
            return []

        results = await self._process_users(users, self._process_weekly_pulse)
        self._log_summary("Weekly pulse job", results, start_time)
        return results

    async def process_briefings_for_users(self, users: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process briefings for a pre-filtered user list."""

        results = await self._process_users(users, self._process_daily_briefing)
        return self._result_counts(results)

    async def process_weekly_pulse_for_users(self, users: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process weekly pulse emails for a provided user list."""

        results = await self._process_users(users, self._process_weekly_pulse)
        return self._result_counts(results)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _process_users(
        self,
        users: List[Dict[str, Any]],
        processor,
    ) -> List[JobResult]:
        results: List[JobResult] = []
        for user in users:
            try:
                result = await processor(user)
                results.append(result)
            except Exception as exc:  # pragma: no cover - safety net
                logger.error("Job processor failed for user %s: %s", user.get("id"), exc)
                results.append(
                    JobResult(
                        success=False,
                        user_id=user.get("id", "unknown"),
                        email=user.get("email", "unknown"),
                        error=str(exc),
                        timestamp=datetime.utcnow(),
                    )
                )
        return results

    def _log_summary(self, label: str, results: List[JobResult], start_time: datetime) -> None:
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "%s completed: %s success, %s failed in %.2fs",
            label,
            success_count,
            failure_count,
            elapsed,
        )

    def _result_counts(self, results: List[JobResult]) -> Dict[str, int]:
        return {
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "total": len(results),
        }

    # ------------------------------------------------------------------
    # Data gathering helpers
    # ------------------------------------------------------------------

    async def _get_briefing_eligible_users(self) -> List[Dict[str, Any]]:
        try:
            response = await self.supabase.table("user_preferences").select(
                "user_id, daily_briefing_enabled, daily_briefing_time, daily_briefing_timezone, daily_briefing_email_enabled"
            ).eq("daily_briefing_enabled", True).execute()

            if not response.data:
                return []

            eligible: List[Dict[str, Any]] = []
            current_utc = datetime.utcnow()

            for prefs in response.data:
                try:
                    user_id = prefs["user_id"]
                    timezone_name = prefs.get("daily_briefing_timezone", "UTC")
                    briefing_time_str = prefs.get("daily_briefing_time", "08:00:00")
                    user_tz = await self.timezone_manager.get_user_timezone(user_id)

                    user_time = current_utc.replace(tzinfo=self.timezone_manager._default_timezone).astimezone(user_tz)
                    hour, minute, *_ = briefing_time_str.split(":")
                    target = user_time.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

                    if abs((user_time - target).total_seconds()) <= 1800:
                        user_record = await self._get_user_record(user_id)
                        if user_record:
                            user_record.update({
                                "briefing_preferences": prefs,
                                "timezone": timezone_name,
                            })
                            eligible.append(user_record)
                except Exception as exc:
                    logger.warning("Failed to evaluate briefing eligibility for %s: %s", prefs.get("user_id"), exc)

            return eligible

        except Exception as exc:
            logger.error("Failed to load briefing eligible users: %s", exc)
            return []

    async def _get_pulse_eligible_users(self) -> List[Dict[str, Any]]:
        try:
            response = await self.supabase.table("user_preferences").select(
                "user_id, weekly_pulse_enabled, weekly_pulse_day, weekly_pulse_time, daily_briefing_timezone, weekly_pulse_email_enabled"
            ).eq("weekly_pulse_enabled", True).execute()

            if not response.data:
                return []

            eligible: List[Dict[str, Any]] = []
            current_utc = datetime.utcnow()

            for prefs in response.data:
                try:
                    user_id = prefs["user_id"]
                    timezone_name = prefs.get("daily_briefing_timezone", "UTC")
                    pulse_time_str = prefs.get("weekly_pulse_time", "18:00:00")
                    pulse_day = prefs.get("weekly_pulse_day", 0)
                    user_tz = await self.timezone_manager.get_user_timezone(user_id)

                    user_time = current_utc.replace(tzinfo=self.timezone_manager._default_timezone).astimezone(user_tz)
                    target_weekday = (pulse_day + 6) % 7

                    if user_time.weekday() != target_weekday:
                        continue

                    hour, minute, *_ = pulse_time_str.split(":")
                    target = user_time.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

                    if abs((user_time - target).total_seconds()) <= 3600:
                        user_record = await self._get_user_record(user_id)
                        if user_record:
                            user_record.update({
                                "pulse_preferences": prefs,
                                "timezone": timezone_name,
                            })
                            eligible.append(user_record)
                except Exception as exc:
                    logger.warning("Failed to evaluate pulse eligibility for %s: %s", prefs.get("user_id"), exc)

            return eligible

        except Exception as exc:
            logger.error("Failed to load pulse eligible users: %s", exc)
            return []

    async def _get_user_record(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = await self.supabase.table("users").select("id, email, name, full_name").eq("id", user_id).execute()
        return response.data[0] if response.data else None

    # ------------------------------------------------------------------
    # Processing helpers
    # ------------------------------------------------------------------

    async def _process_daily_briefing(self, user: Dict[str, Any]) -> JobResult:
        try:
            user_id = user["id"]
            email = user["email"]
            name = user.get("full_name") or user.get("name") or "User"

            today = datetime.utcnow().date().isoformat()
            cache_key = f"briefing_sent:{user_id}:{today}"

            if await self.cache_service.exists(cache_key):
                return JobResult(
                    success=True,
                    user_id=user_id,
                    email=email,
                    timestamp=datetime.utcnow(),
                    data={"briefing_sent": False, "reason": "Already sent today"},
                )

            briefing_result = await self.agent_orchestrator.run_briefing_workflow(
                user_id=user_id,
                context={
                    "user_email": email,
                    "user_name": name,
                    "timezone": user.get("timezone", "UTC"),
                    "briefing_type": "daily",
                },
            )

            if not briefing_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error="Agent failed to generate briefing",
                    timestamp=datetime.utcnow(),
                )

            email_result = await self.email_service.send_daily_briefing(
                to=email,
                user_name=name,
                briefing_data=briefing_result.get("data", {}),
            )

            if not email_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error=email_result.get("error", "Email sending failed"),
                    timestamp=datetime.utcnow(),
                )

            await self.cache_service.set(cache_key, True, ttl=86400)

            return JobResult(
                success=True,
                user_id=user_id,
                email=email,
                timestamp=datetime.utcnow(),
                data={"briefing_sent": True, "email_id": email_result.get("message_id")},
            )

        except Exception as exc:
            logger.error("Briefing processing failed for user %s: %s", user.get("id"), exc)
            return JobResult(
                success=False,
                user_id=user.get("id", "unknown"),
                email=user.get("email", "unknown"),
                error=str(exc),
                timestamp=datetime.utcnow(),
            )

    async def _process_weekly_pulse(self, user: Dict[str, Any]) -> JobResult:
        try:
            user_id = user["id"]
            email = user["email"]
            name = user.get("full_name") or user.get("name") or "User"

            pulse_result = await self.agent_orchestrator.run_weekly_pulse_workflow(
                user_id=user_id,
                context={
                    "user_email": email,
                    "user_name": name,
                    "timezone": user.get("timezone", "UTC"),
                    "pulse_type": "weekly",
                },
            )

            if not pulse_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error="Agent failed to generate weekly pulse",
                    timestamp=datetime.utcnow(),
                )

            email_result = await self.email_service.send_weekly_pulse(
                to=email,
                user_name=name,
                pulse_data=pulse_result.get("data", {}),
            )

            if not email_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error=email_result.get("error", "Email sending failed"),
                    timestamp=datetime.utcnow(),
                )

            return JobResult(
                success=True,
                user_id=user_id,
                email=email,
                timestamp=datetime.utcnow(),
                data={"pulse_sent": True, "email_id": email_result.get("message_id")},
            )

        except Exception as exc:
            logger.error("Weekly pulse processing failed for user %s: %s", user.get("id"), exc)
            return JobResult(
                success=False,
                user_id=user.get("id", "unknown"),
                email=user.get("email", "unknown"),
                error=str(exc),
                timestamp=datetime.utcnow(),
            )


_briefing_job_runner: Optional[BriefingJobRunner] = None


def get_briefing_job_runner() -> BriefingJobRunner:
    global _briefing_job_runner
    if _briefing_job_runner is None:
        _briefing_job_runner = BriefingJobRunner()
    return _briefing_job_runner

