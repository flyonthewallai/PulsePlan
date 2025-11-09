"""Calendar job runner used by APScheduler jobs.

This module intentionally keeps the name `calendar_background_worker`
to maintain backward compatibility with older imports while providing
single-run job methods that the scheduler can invoke.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

from app.config.cache.redis_client import get_redis_client
from app.config.core.settings import get_settings
from app.database.repositories.calendar_repositories import (
    CalendarCalendarRepository,
    CalendarEventRepository,
    CalendarPreferencesRepository,
    CalendarSyncConflictRepository,
    CalendarSyncStatusRepository,
    get_calendar_calendar_repository,
    get_calendar_event_repository,
    get_calendar_preferences_repository,
    get_calendar_sync_conflict_repository,
    get_calendar_sync_status_repository,
)
from app.database.repositories.user_repositories import (
    UserRepository,
    get_user_repository,
)
from app.services.integrations.calendar_sync_service import (
    CalendarSyncService,
    CalendarWebhookService,
    get_calendar_sync_service,
    get_calendar_webhook_service,
)
from app.services.workers.calendar_sync_worker import CalendarSyncWorker, get_calendar_sync_worker
from app.core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class CalendarJobRunner:
    """Executes discrete calendar jobs (auto-sync, webhooks, cleanup)."""

    def __init__(
        self,
        calendar_calendar_repository: Optional[CalendarCalendarRepository] = None,
        calendar_event_repository: Optional[CalendarEventRepository] = None,
        calendar_sync_conflict_repository: Optional[CalendarSyncConflictRepository] = None,
        calendar_sync_status_repository: Optional[CalendarSyncStatusRepository] = None,
        calendar_preferences_repository: Optional[CalendarPreferencesRepository] = None,
        user_repository: Optional[UserRepository] = None,
        calendar_sync_service: Optional[CalendarSyncService] = None,
        webhook_service: Optional[CalendarWebhookService] = None,
        sync_worker: Optional[CalendarSyncWorker] = None,
    ) -> None:
        self.settings = get_settings()
        self._calendar_calendar_repository = calendar_calendar_repository
        self._calendar_event_repository = calendar_event_repository
        self._calendar_sync_conflict_repository = calendar_sync_conflict_repository
        self._calendar_sync_status_repository = calendar_sync_status_repository
        self._calendar_preferences_repository = calendar_preferences_repository
        self._user_repository = user_repository
        self.redis_client = get_redis_client()
        self.calendar_sync_service = calendar_sync_service or get_calendar_sync_service()
        self.webhook_service = webhook_service or get_calendar_webhook_service(
            self.calendar_sync_service
        )
        self.sync_worker = sync_worker or get_calendar_sync_worker()
        self.timezone_manager = get_timezone_manager()

    @property
    def calendar_event_repository(self) -> CalendarEventRepository:
        if self._calendar_event_repository is None:
            self._calendar_event_repository = get_calendar_event_repository()
        return self._calendar_event_repository

    @property
    def calendar_sync_conflict_repository(self) -> CalendarSyncConflictRepository:
        if self._calendar_sync_conflict_repository is None:
            self._calendar_sync_conflict_repository = get_calendar_sync_conflict_repository()
        return self._calendar_sync_conflict_repository

    @property
    def calendar_sync_status_repository(self) -> CalendarSyncStatusRepository:
        if self._calendar_sync_status_repository is None:
            self._calendar_sync_status_repository = get_calendar_sync_status_repository()
        return self._calendar_sync_status_repository

    @property
    def calendar_preferences_repository(self) -> CalendarPreferencesRepository:
        if self._calendar_preferences_repository is None:
            self._calendar_preferences_repository = get_calendar_preferences_repository()
        return self._calendar_preferences_repository

    @property
    def calendar_calendar_repository(self) -> CalendarCalendarRepository:
        if self._calendar_calendar_repository is None:
            self._calendar_calendar_repository = get_calendar_calendar_repository()
        return self._calendar_calendar_repository

    @property
    def user_repository(self) -> UserRepository:
        if self._user_repository is None:
            self._user_repository = get_user_repository()
        return self._user_repository

    async def run_auto_sync_cycle(self, batch_size: int = 5) -> Dict[str, Any]:
        """Sync all users who are due based on their auto-sync preferences."""

        users_to_sync = await self._get_users_for_auto_sync()
        summary: Dict[str, Any] = {
            "scheduled_users": len(users_to_sync),
            "synced": 0,
            "failed": 0,
            "details": [],
        }

        if not users_to_sync:
            logger.info("No users due for auto-sync")
            return summary

        for chunk in _chunk(users_to_sync, batch_size):
            tasks = [self._sync_user_calendar(user) for user in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(results):
                user_id = chunk[idx]["user_id"]
                if isinstance(result, Exception):
                    logger.error(
                        "Auto-sync failed for user %s: %s", user_id, result, exc_info=True
                    )
                    summary["failed"] += 1
                    summary["details"].append({"user_id": user_id, "error": str(result)})
                else:
                    summary["synced"] += 1
                    summary["details"].append({"user_id": user_id, **result})

        logger.info(
            "Auto-sync summary: scheduled=%s synced=%s failed=%s",
            summary["scheduled_users"],
            summary["synced"],
            summary["failed"],
        )
        return summary

    async def process_webhook_queue(self) -> Dict[str, Any]:
        """Drain pending webhook notifications and trigger incremental syncs."""

        pending = await self._get_pending_webhooks()
        processed = {"processed": 0, "failed": 0}

        if not pending:
            return processed

        for webhook in pending:
            try:
                await self._process_webhook(webhook)
                processed["processed"] += 1
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Webhook processing failed: %s", exc, exc_info=True)
                processed["failed"] += 1

        logger.info(
            "Processed calendar webhooks: success=%s failed=%s",
            processed["processed"],
            processed["failed"],
        )
        return processed

    async def run_conflict_resolution(self) -> Dict[str, Any]:
        """Resolve outstanding calendar conflicts for active users."""

        users = await self._get_users_with_conflicts()
        summary = {"users": len(users), "resolved": 0, "failed": 0}

        for user_id in users:
            try:
                result = await self.calendar_sync_service.detect_and_resolve_conflicts(user_id)
                summary["resolved"] += result.get("conflicts_resolved", 0)
            except Exception as exc:
                summary["failed"] += 1
                logger.error(
                    "Conflict resolution failed for user %s: %s", user_id, exc, exc_info=True
                )

        return summary

    async def cleanup_calendar_data(self) -> Dict[str, Any]:
        """Cleanup stale calendar caches, conflicts, and sync metadata."""

        cutoff_events = datetime.utcnow() - timedelta(days=90)
        cutoff_conflicts = datetime.utcnow() - timedelta(days=30)
        cutoff_sync_status = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Delete old events using repository
        events_deleted = await self.calendar_event_repository.delete_old_events(cutoff_events)

        # Delete old resolved conflicts using repository
        conflicts_deleted = await self.calendar_sync_conflict_repository.delete_old_resolved_conflicts(
            cutoff_conflicts
        )

        # Delete old sync status records using repository
        await self.calendar_sync_status_repository.delete_old_records(cutoff_sync_status)

        logger.info("Calendar cleanup completed")
        return {
            "events_deleted": events_deleted,
            "conflicts_deleted": conflicts_deleted,
        }

    async def queue_webhook(self, provider: str, webhook_data: Dict[str, Any]) -> bool:
        """Push a webhook notification to Redis for later processing."""

        try:
            if not self.redis_client.client:
                await self.redis_client.initialize()

            queue_key = f"calendar_webhooks:{provider}"
            await self.redis_client.lpush(queue_key, json.dumps(webhook_data))
            logger.info("Queued %s webhook for processing", provider)
            return True
        except Exception as exc:
            logger.error("Error queueing webhook: %s", exc, exc_info=True)
            return False

    async def _get_users_for_auto_sync(self) -> List[Dict[str, Any]]:
        try:
            user_prefs = await self.calendar_preferences_repository.get_users_with_auto_sync()
        except Exception as exc:
            logger.error("Failed to load calendar preferences: %s", exc, exc_info=True)
            return []

        users_for_sync: List[Dict[str, Any]] = []
        current_time = datetime.utcnow()

        for pref in user_prefs:
            user_id = pref["user_id"]
            frequency = pref.get("sync_frequency_minutes", 10)
            last_sync = await self._get_last_sync_time(user_id)

            if not last_sync or (current_time - last_sync).total_seconds() >= frequency * 60:
                users_for_sync.append(
                    {
                        "user_id": user_id,
                        "sync_frequency_minutes": frequency,
                        "last_sync": last_sync.isoformat() if last_sync else None,
                    }
                )

        return users_for_sync

    async def _get_last_sync_time(self, user_id: str) -> Optional[datetime]:
        status = await self.calendar_sync_status_repository.get_by_user(user_id)
        if status and status.get("last_sync_at"):
            return datetime.fromisoformat(status["last_sync_at"].replace("Z", "+00:00"))
        return None

    async def _sync_user_calendar(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = user_data["user_id"]
        sync_results = await self.calendar_sync_service.sync_user_calendars(
            user_id=user_id, days_ahead=30, force_refresh=False
        )
        conflict_results = await self.calendar_sync_service.detect_and_resolve_conflicts(user_id)

        logger.info(
            "Auto-sync completed for user %s: %s events, %s conflicts",
            user_id,
            sync_results.get("total_events", 0),
            conflict_results.get("conflicts_resolved", 0),
        )

        return {
            "sync_results": sync_results,
            "conflict_results": conflict_results,
        }

    async def _get_pending_webhooks(self) -> List[Dict[str, Any]]:
        try:
            if not self.redis_client.client:
                await self.redis_client.initialize()
        except Exception as exc:
            logger.error("Failed to initialize Redis client: %s", exc, exc_info=True)
            return []

        webhooks: List[Dict[str, Any]] = []

        for provider in ("google", "microsoft"):
            raw_items = await self.redis_client.lrange(f"calendar_webhooks:{provider}", 0, -1)
            for raw in raw_items:
                try:
                    payload = json.loads(raw)
                    payload["provider"] = provider
                    webhooks.append(payload)
                except json.JSONDecodeError:
                    logger.error("Invalid webhook payload: %s", raw)

            if raw_items:
                await self.redis_client.delete(f"calendar_webhooks:{provider}")

        return webhooks

    async def _process_webhook(self, webhook: Dict[str, Any]) -> None:
        provider = webhook.get("provider")
        user_id = webhook.get("user_id")

        if not provider or not user_id:
            logger.warning("Skipping webhook missing provider or user_id: %s", webhook)
            return

        if provider == "google":
            await self.webhook_service.handle_google_webhook(
                user_id=user_id,
                resource_id=webhook.get("resource_id", ""),
                resource_state=webhook.get("resource_state", "sync"),
            )
        elif provider == "microsoft":
            await self.webhook_service.handle_microsoft_webhook(
                user_id=user_id,
                subscription_id=webhook.get("subscription_id", ""),
                change_type=webhook.get("change_type", "updated"),
            )
        else:
            logger.warning("Unsupported webhook provider: %s", provider)

    async def _get_users_with_conflicts(self) -> List[str]:
        try:
            return await self.calendar_sync_conflict_repository.get_users_with_unresolved_conflicts()
        except Exception as exc:
            logger.error("Failed to fetch users with conflicts: %s", exc, exc_info=True)
            return []

    async def run_incremental_pulls(self) -> Dict[str, Any]:
        """
        Run incremental pulls for all active calendars during user active hours.

        Returns:
            Summary dict with success/failed/skipped counts
        """
        logger.info("Starting calendar incremental pull job")
        start_time = datetime.utcnow()

        try:
            # Get all active calendars using repository
            calendars = await self.calendar_calendar_repository.get_all_active()

            if not calendars:
                logger.info("No active calendars found for incremental pull")
                return {"success": 0, "failed": 0, "skipped": 0}
            logger.info(f"Found {len(calendars)} active calendars for incremental pull")

            # Filter calendars to only those in user active hours
            eligible_calendars = []
            for calendar in calendars:
                if await self._is_user_active_hour(calendar["user_id"]):
                    eligible_calendars.append(calendar)

            logger.info(f"Found {len(eligible_calendars)} calendars in active hours")

            # Pull incrementally for each calendar
            results = {
                "success": 0,
                "failed": 0,
                "skipped": len(calendars) - len(eligible_calendars),
            }

            for calendar in eligible_calendars:
                try:
                    result = await self.sync_worker.pull_incremental(calendar["id"])
                    if result.get("success"):
                        results["success"] += 1
                        logger.info(
                            f"Incremental pull successful for calendar {calendar['id']}"
                        )
                    else:
                        results["failed"] += 1
                        logger.warning(
                            f"Incremental pull failed for calendar {calendar['id']}: {result.get('error')}"
                        )
                except Exception as e:
                    results["failed"] += 1
                    logger.error(f"Error pulling calendar {calendar['id']}: {e}", exc_info=True)

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Calendar incremental pull job completed in {elapsed:.2f}s - "
                f"Success: {results['success']}, Failed: {results['failed']}, Skipped: {results['skipped']}"
            )

            return results

        except Exception as e:
            logger.error(f"Error in incremental pull job: {e}", exc_info=True)
            return {"success": 0, "failed": 0, "skipped": 0, "error": str(e)}

    async def run_watch_renewals(self) -> Dict[str, Any]:
        """
        Renew watch channels that are expiring soon (within 12 hours).

        Returns:
            Summary dict with success/failed counts
        """
        logger.info("Starting watch channel renewal job")
        start_time = datetime.utcnow()

        try:
            expiration_threshold = datetime.utcnow() + timedelta(hours=12)

            # Get all calendars with watch channels using repository
            calendars_with_watches = await self.calendar_calendar_repository.get_with_watch_channels()

            if not calendars_with_watches:
                logger.info("No watch channels found for renewal")
                return {"success": 0, "failed": 0}

            # Filter calendars needing renewal
            calendars_needing_renewal = []
            for calendar in calendars_with_watches:
                if calendar.get("watch_expiration_at"):
                    expiration = datetime.fromisoformat(
                        calendar["watch_expiration_at"].replace("Z", "+00:00")
                    )
                    if expiration <= expiration_threshold:
                        calendars_needing_renewal.append(calendar)

            logger.info(f"Found {len(calendars_needing_renewal)} watch channels needing renewal")

            results = {"success": 0, "failed": 0}

            for calendar in calendars_needing_renewal:
                try:
                    result = await self.sync_worker.renew_watch(calendar["id"])
                    if result.get("success"):
                        results["success"] += 1
                        logger.info(f"Watch renewal successful for calendar {calendar['id']}")
                    else:
                        results["failed"] += 1
                        logger.warning(
                            f"Watch renewal failed for calendar {calendar['id']}: {result.get('error')}"
                        )
                except Exception as e:
                    results["failed"] += 1
                    logger.error(f"Error renewing watch for calendar {calendar['id']}: {e}", exc_info=True)

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Watch renewal job completed in {elapsed:.2f}s - "
                f"Success: {results['success']}, Failed: {results['failed']}"
            )

            return results

        except Exception as e:
            logger.error(f"Error in watch renewal job: {e}", exc_info=True)
            return {"success": 0, "failed": 0, "error": str(e)}

    async def _is_user_active_hour(self, user_id: str) -> bool:
        """
        Check if current time is within user's active hours.

        Args:
            user_id: User ID

        Returns:
            True if current time is in user's active hours
        """
        try:
            # Get user timezone and working hours using repository
            user_data = await self.user_repository.get_timezone_and_working_hours(user_id)

            if not user_data:
                # Default to allowing sync if user not found
                return True

            timezone = user_data.get("timezone", "UTC")
            working_hours = user_data.get("working_hours")

            # If no working hours configured, assume active all day
            if not working_hours:
                return True

            # Convert current time to user's timezone
            try:
                user_tz_obj = self.timezone_manager.convert_to_user_timezone(
                    datetime.utcnow().replace(tzinfo=self.timezone_manager._default_timezone),
                    timezone,
                )
                current_time_user = user_tz_obj
            except Exception:
                # Fallback: treat as UTC if conversion fails
                current_time_user = datetime.utcnow()
            current_hour = current_time_user.hour

            # Parse working hours (expected format: {"start": 9, "end": 17})
            if isinstance(working_hours, dict):
                start_hour = working_hours.get("start", 0)
                end_hour = working_hours.get("end", 24)

                # Check if current hour is within working hours
                return start_hour <= current_hour < end_hour

            # Default to active if working hours format is unexpected
            return True

        except Exception as e:
            logger.warning(f"Error checking active hours for user {user_id}: {e}")
            # Default to allowing sync on error
            return True


_job_runner: Optional[CalendarJobRunner] = None


def get_calendar_job_runner() -> CalendarJobRunner:
    """Singleton accessor for CalendarJobRunner."""

    global _job_runner
    if _job_runner is None:
        _job_runner = CalendarJobRunner()
    return _job_runner


# Backward-compatible aliases -------------------------------------------------
CalendarBackgroundWorker = CalendarJobRunner


def get_calendar_background_worker() -> CalendarJobRunner:
    return get_calendar_job_runner()


# Helpers ---------------------------------------------------------------------

def _chunk(items: Sequence[Any], size: int) -> List[Sequence[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]

