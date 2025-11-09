"""
Calendar sync worker - handles all calendar sync operations
Includes: discover calendars, pull incremental, push from task, renew watch
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import asyncio

from app.config.core.settings import get_settings
from app.config.database.supabase import get_supabase_client
from app.integrations.providers.google import GoogleCalendarClient
from app.integrations.providers.google.mapping import (
    gcal_to_cache_row,
    gcal_to_task_update,
    task_to_gcal_event,
    extract_pulseplan_task_id
)
from app.integrations.providers.base import SyncTokenInvalid, PreconditionFailed, ProviderError

logger = logging.getLogger(__name__)


class CalendarSyncWorker:
    """Worker for calendar sync operations"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.google_client = GoogleCalendarClient()

    async def discover_calendars(self, user_id: str, provider: str = "google") -> Dict[str, Any]:
        """
        Discover calendars for the user's active account.

        Args:
            user_id: User ID
            provider: Calendar provider (default: google)

        Returns:
            Dict with discovery results
        """
        logger.info(f"Discovering {provider} calendars for user {user_id}")

        try:
            # Get active OAuth token for this provider
            token_response = self.supabase.table("oauth_tokens").select("*").eq("user_id", user_id).eq("provider", provider).eq("is_active", True).limit(1).execute()

            if not token_response.data:
                return {
                    "success": False,
                    "error": f"No active {provider} account found for user"
                }

            oauth_token = token_response.data[0]
            oauth_token_id = UUID(oauth_token["id"])

            # List calendars from provider
            calendars = await self.google_client.list_calendars(oauth_token_id)

            # Upsert into calendar_calendars
            discovered_count = 0
            for cal in calendars:
                # Check if calendar already exists
                existing = self.supabase.table("calendar_calendars").select("*").eq("user_id", user_id).eq("provider", provider).eq("provider_calendar_id", cal["provider_calendar_id"]).execute()

                calendar_data = {
                    "user_id": user_id,
                    "oauth_token_id": oauth_token["id"],
                    "provider": provider,
                    "provider_calendar_id": cal["provider_calendar_id"],
                    "summary": cal["summary"],
                    "timezone": cal["timezone"],
                    "is_active": True,
                    "updated_at": datetime.utcnow().isoformat()
                }

                if existing.data:
                    # Update existing
                    self.supabase.table("calendar_calendars").update(calendar_data).eq("id", existing.data[0]["id"]).execute()
                else:
                    # Insert new - check if this should be primary write
                    primary_check = self.supabase.table("calendar_calendars").select("id").eq("user_id", user_id).eq("is_primary_write", True).execute()

                    if not primary_check.data and cal.get("is_primary"):
                        # This is the user's primary calendar and they have no primary write set
                        calendar_data["is_primary_write"] = True

                    self.supabase.table("calendar_calendars").insert(calendar_data).execute()

                discovered_count += 1

            logger.info(f"Discovered {discovered_count} calendars for user {user_id}")

            return {
                "success": True,
                "discovered_count": discovered_count,
                "calendars": calendars
            }

        except Exception as e:
            logger.error(f"Error discovering calendars for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def pull_incremental(self, calendar_id: str) -> Dict[str, Any]:
        """
        Pull incremental updates from a calendar.

        Args:
            calendar_id: Calendar ID (calendar_calendars.id)

        Returns:
            Dict with sync results
        """
        logger.info(f"Pulling incremental updates for calendar {calendar_id}")

        try:
            # Get calendar details
            calendar_response = self.supabase.table("calendar_calendars").select("*").eq("id", calendar_id).single().execute()

            if not calendar_response.data:
                return {
                    "success": False,
                    "error": "Calendar not found"
                }

            calendar = calendar_response.data
            sync_token = calendar.get("sync_token")
            provider_calendar_id = calendar["provider_calendar_id"]

            # Determine sync strategy
            if sync_token:
                # Incremental sync
                logger.info(f"Using incremental sync with token for calendar {calendar_id}")
                result = await self._pull_with_sync_token(calendar_id, provider_calendar_id, sync_token)
            else:
                # Initial window sync (30 days back, 90 days forward)
                logger.info(f"Performing initial window sync for calendar {calendar_id}")
                time_min = datetime.utcnow() - timedelta(days=30)
                time_max = datetime.utcnow() + timedelta(days=90)
                result = await self._pull_window(calendar_id, provider_calendar_id, time_min, time_max)

            return result

        except SyncTokenInvalid:
            logger.warning(f"Sync token invalid for calendar {calendar_id}, resetting")
            # Clear sync token and re-sync window
            self.supabase.table("calendar_calendars").update({"sync_token": None}).eq("id", calendar_id).execute()

            # Retry with window sync
            calendar_response = self.supabase.table("calendar_calendars").select("*").eq("id", calendar_id).single().execute()
            calendar = calendar_response.data
            time_min = datetime.utcnow() - timedelta(days=30)
            time_max = datetime.utcnow() + timedelta(days=90)
            return await self._pull_window(calendar_id, calendar["provider_calendar_id"], time_min, time_max)

        except Exception as e:
            logger.error(f"Error pulling updates for calendar {calendar_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _pull_with_sync_token(self, calendar_id: str, provider_calendar_id: str, sync_token: str) -> Dict[str, Any]:
        """Pull events using sync token (incremental)."""
        calendar_uuid = UUID(calendar_id)
        events_updated = 0
        events_created = 0
        events_deleted = 0

        page_token = None
        while True:
            result = await self.google_client.list_events(
                calendar_id=calendar_uuid,
                provider_calendar_id=provider_calendar_id,
                sync_token=sync_token,
                page_token=page_token
            )

            # Process events
            for event in result["events"]:
                if event.get("status") == "cancelled":
                    # Mark as cancelled
                    await self._mark_event_cancelled(calendar_id, event["id"])
                    events_deleted += 1
                else:
                    # Upsert event
                    created = await self._upsert_event(calendar_id, event)
                    if created:
                        events_created += 1
                    else:
                        events_updated += 1

            # Check for next page
            page_token = result.get("next_page_token")
            if not page_token:
                # Update sync token
                if result.get("next_sync_token"):
                    self.supabase.table("calendar_calendars").update({
                        "sync_token": result["next_sync_token"]
                    }).eq("id", calendar_id).execute()
                break

        return {
            "success": True,
            "events_created": events_created,
            "events_updated": events_updated,
            "events_deleted": events_deleted
        }

    async def _pull_window(self, calendar_id: str, provider_calendar_id: str, time_min: datetime, time_max: datetime) -> Dict[str, Any]:
        """Pull events within a time window."""
        calendar_uuid = UUID(calendar_id)
        events_synced = 0

        page_token = None
        while True:
            result = await self.google_client.list_events(
                calendar_id=calendar_uuid,
                provider_calendar_id=provider_calendar_id,
                time_min=time_min,
                time_max=time_max,
                page_token=page_token
            )

            # Process events
            for event in result["events"]:
                if event.get("status") == "cancelled":
                    await self._mark_event_cancelled(calendar_id, event["id"])
                else:
                    await self._upsert_event(calendar_id, event)
                    events_synced += 1

            # Check for next page
            page_token = result.get("next_page_token")
            if not page_token:
                # Save sync token for future incremental syncs
                if result.get("next_sync_token"):
                    self.supabase.table("calendar_calendars").update({
                        "sync_token": result["next_sync_token"]
                    }).eq("id", calendar_id).execute()
                break

        return {
            "success": True,
            "events_synced": events_synced
        }

    async def _upsert_event(self, calendar_id: str, gcal_event: Dict[str, Any]) -> bool:
        """
        Upsert a calendar event into cache.

        Returns:
            True if created, False if updated
        """
        calendar_response = self.supabase.table("calendar_calendars").select("user_id").eq("id", calendar_id).single().execute()
        user_id = calendar_response.data["user_id"]

        # Convert to cache row
        cache_row = gcal_to_cache_row(gcal_event, user_id, calendar_id)

        # Check if event exists
        existing = self.supabase.table("calendar_events").select("id").eq("calendar_id_ref", calendar_id).eq("external_id", gcal_event["id"]).execute()

        if existing.data:
            # Update
            self.supabase.table("calendar_events").update(cache_row).eq("id", existing.data[0]["id"]).execute()

            # Check if linked to a task - update task if calendar wins
            await self._handle_calendar_update(calendar_id, gcal_event)
            return False
        else:
            # Insert
            self.supabase.table("calendar_events").insert(cache_row).execute()
            return True

    async def _mark_event_cancelled(self, calendar_id: str, event_id: str):
        """Mark an event as cancelled and unlink any tasks."""
        # Update cache
        self.supabase.table("calendar_events").update({
            "is_cancelled": True,
            "last_synced": datetime.utcnow().isoformat()
        }).eq("calendar_id_ref", calendar_id).eq("external_id", event_id).execute()

        # Unlink any calendar_links
        link_response = self.supabase.table("calendar_links").select("*").eq("calendar_id", calendar_id).eq("provider_event_id", event_id).execute()

        if link_response.data:
            link = link_response.data[0]
            # Delete link (task remains but unscheduled)
            self.supabase.table("calendar_links").delete().eq("id", link["id"]).execute()
            logger.info(f"Unlinked task {link['task_id']} from deleted event {event_id}")

    async def _handle_calendar_update(self, calendar_id: str, gcal_event: Dict[str, Any]):
        """Handle updates from calendar (conflict resolution)."""
        # Check if event is linked to a task
        link_response = self.supabase.table("calendar_links").select("*").eq("calendar_id", calendar_id).eq("provider_event_id", gcal_event["id"]).execute()

        if not link_response.data:
            return

        link = link_response.data[0]

        # Get task
        task_response = self.supabase.table("tasks").select("*").eq("id", link["task_id"]).single().execute()
        if not task_response.data:
            return

        task = task_response.data

        # Apply conflict resolution based on source_of_truth
        source_of_truth = link.get("source_of_truth", "latest_update")

        if source_of_truth == "calendar":
            # Calendar always wins
            await self._update_task_from_event(link["task_id"], gcal_event)
        elif source_of_truth == "latest_update":
            # Compare timestamps
            event_updated = datetime.fromisoformat(gcal_event.get("updated", "").replace("Z", "+00:00"))
            task_updated = datetime.fromisoformat(task["updated_at"].replace("Z", "+00:00"))
            last_pushed = link.get("last_pushed_at")

            if last_pushed:
                last_pushed_dt = datetime.fromisoformat(last_pushed.replace("Z", "+00:00"))
                # If event was updated after our last push, calendar wins
                if event_updated > last_pushed_dt:
                    await self._update_task_from_event(link["task_id"], gcal_event)
                    self.supabase.table("calendar_links").update({
                        "last_pulled_at": datetime.utcnow().isoformat()
                    }).eq("id", link["id"]).execute()

    async def _update_task_from_event(self, task_id: str, gcal_event: Dict[str, Any]):
        """Update a task from a calendar event."""
        task_update = gcal_to_task_update(gcal_event)
        task_update["updated_at"] = datetime.utcnow().isoformat()

        self.supabase.table("tasks").update(task_update).eq("id", task_id).execute()
        logger.info(f"Updated task {task_id} from calendar event")

    async def push_from_task(self, task_id: str) -> Dict[str, Any]:
        """
        Push a task to the user's primary write calendar.

        Args:
            task_id: Task ID

        Returns:
            Dict with push results
        """
        logger.info(f"Pushing task {task_id} to primary write calendar")

        try:
            # Get task
            task_response = self.supabase.table("tasks").select("*").eq("id", task_id).single().execute()
            if not task_response.data:
                return {"success": False, "error": "Task not found"}

            task = task_response.data
            user_id = task["user_id"]

            # Check if user is premium
            user_response = self.supabase.table("users").select("subscription_status").eq("id", user_id).single().execute()
            if not user_response.data or user_response.data.get("subscription_status") not in ["active", "premium"]:
                return {"success": False, "error": "Premium subscription required for two-way sync"}

            # Get primary write calendar
            primary_cal_response = self.supabase.table("calendar_calendars").select("*").eq("user_id", user_id).eq("is_primary_write", True).execute()

            if not primary_cal_response.data:
                return {"success": False, "error": "No primary write calendar configured"}

            primary_calendar = primary_cal_response.data[0]

            # Check if task already linked
            link_response = self.supabase.table("calendar_links").select("*").eq("task_id", task_id).execute()

            if link_response.data:
                # Update existing event
                link = link_response.data[0]
                result = await self._update_provider_event(task, link, primary_calendar)
            else:
                # Create new event
                result = await self._create_provider_event(task, primary_calendar)

            return result

        except Exception as e:
            logger.error(f"Error pushing task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _create_provider_event(self, task: Dict[str, Any], calendar: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new provider event from a task."""
        # Convert task to Google Calendar event
        gcal_event = task_to_gcal_event(task, calendar.get("timezone", "UTC"))

        # Insert event
        result = await self.google_client.insert_event(
            calendar_id=UUID(calendar["id"]),
            provider_calendar_id=calendar["provider_calendar_id"],
            event_dict=gcal_event
        )

        # Create link
        self.supabase.table("calendar_links").insert({
            "user_id": task["user_id"],
            "task_id": task["id"],
            "calendar_id": calendar["id"],
            "provider": calendar["provider"],
            "provider_event_id": result["id"],
            "last_pushed_at": datetime.utcnow().isoformat(),
            "source_of_truth": "latest_update"
        }).execute()

        # Cache the event
        cache_row = gcal_to_cache_row(result, task["user_id"], calendar["id"])
        self.supabase.table("calendar_events").insert(cache_row).execute()

        logger.info(f"Created provider event for task {task['id']}")

        return {
            "success": True,
            "event_id": result["id"],
            "action": "created"
        }

    async def _update_provider_event(self, task: Dict[str, Any], link: Dict[str, Any], calendar: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing provider event."""
        # Convert task to Google Calendar event
        gcal_event = task_to_gcal_event(task, calendar.get("timezone", "UTC"))

        try:
            # Get current event etag for concurrency control
            event_response = self.supabase.table("calendar_events").select("etag").eq("calendar_id_ref", calendar["id"]).eq("external_id", link["provider_event_id"]).execute()

            etag = event_response.data[0]["etag"] if event_response.data else None

            # Update event
            result = await self.google_client.update_event(
                calendar_id=UUID(calendar["id"]),
                provider_calendar_id=calendar["provider_calendar_id"],
                event_id=link["provider_event_id"],
                event_dict=gcal_event,
                etag=etag
            )

            # Update link timestamp
            self.supabase.table("calendar_links").update({
                "last_pushed_at": datetime.utcnow().isoformat()
            }).eq("id", link["id"]).execute()

            # Update cache
            cache_row = gcal_to_cache_row(result, task["user_id"], calendar["id"])
            self.supabase.table("calendar_events").update(cache_row).eq("calendar_id_ref", calendar["id"]).eq("external_id", link["provider_event_id"]).execute()

            logger.info(f"Updated provider event for task {task['id']}")

            return {
                "success": True,
                "event_id": result["id"],
                "action": "updated"
            }

        except PreconditionFailed:
            # Etag mismatch - pull latest and retry once
            logger.warning(f"Precondition failed for task {task['id']}, pulling latest and retrying")
            await self.pull_incremental(calendar["id"])

            # Retry update (without etag this time)
            result = await self.google_client.update_event(
                calendar_id=UUID(calendar["id"]),
                provider_calendar_id=calendar["provider_calendar_id"],
                event_id=link["provider_event_id"],
                event_dict=gcal_event
            )

            self.supabase.table("calendar_links").update({
                "last_pushed_at": datetime.utcnow().isoformat()
            }).eq("id", link["id"]).execute()

            return {
                "success": True,
                "event_id": result["id"],
                "action": "updated_after_retry"
            }

    async def ensure_watch(self, calendar_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Ensure a watch channel exists for the calendar.

        Args:
            calendar_id: Calendar ID
            force: If True, always create a fresh watch

        Returns:
            Dict with renewal results
        """
        logger.info("Ensuring watch channel for calendar %s (force=%s)", calendar_id, force)

        try:
            calendar_response = self.supabase.table("calendar_calendars").select("*").eq("id", calendar_id).single().execute()
            if not calendar_response.data:
                return {"success": False, "error": "Calendar not found"}

            calendar = calendar_response.data
            existing_channel = calendar.get("watch_channel_id")
            existing_resource = calendar.get("watch_resource_id")
            expiration_raw = calendar.get("watch_expiration_at")

            need_new_channel = force or not existing_channel or not existing_resource

            if not need_new_channel and expiration_raw:
                expiration = datetime.fromisoformat(expiration_raw.replace("Z", "+00:00"))
                if expiration <= datetime.utcnow() + timedelta(hours=1):
                    need_new_channel = True

            if not need_new_channel:
                logger.info("Existing watch channel still valid for calendar %s", calendar_id)
                return {
                    "success": True,
                    "channel_id": existing_channel,
                    "expiration": expiration_raw,
                    "skipped": True
                }

            if existing_channel and existing_resource:
                try:
                    await self.google_client.stop_watch(
                        calendar_id=UUID(calendar_id),
                        channel_id=existing_channel,
                        resource_id=existing_resource
                    )
                except Exception as exc:
                    logger.warning("Failed to stop existing watch channel: %s", exc)

            settings = get_settings()
            callback_url = f"{settings.API_BASE_URL}/webhooks/google/calendar"
            channel_token = settings.GOOGLE_WEBHOOK_VERIFICATION_TOKEN

            watch_result = await self.google_client.watch_calendar(
                calendar_id=UUID(calendar_id),
                provider_calendar_id=calendar["provider_calendar_id"],
                callback_url=callback_url,
                channel_token=channel_token,
                ttl_days=7
            )

            self.supabase.table("calendar_calendars").update({
                "watch_channel_id": watch_result["channel_id"],
                "watch_resource_id": watch_result["resource_id"],
                "watch_expiration_at": watch_result["expiration"].isoformat()
            }).eq("id", calendar_id).execute()

            logger.info("Provisioned watch channel for calendar %s", calendar_id)

            return {
                "success": True,
                "channel_id": watch_result["channel_id"],
                "expiration": watch_result["expiration"].isoformat()
            }

        except Exception as e:
            logger.error(f"Error ensuring watch for calendar {calendar_id}: {e}")
            return {"success": False, "error": str(e)}

    async def renew_watch(self, calendar_id: str) -> Dict[str, Any]:
        """Backward compatible helper that forces a new watch."""

        return await self.ensure_watch(calendar_id, force=True)


# Singleton instance
_calendar_sync_worker = None


def get_calendar_sync_worker() -> CalendarSyncWorker:
    """Get the calendar sync worker singleton."""
    global _calendar_sync_worker
    if _calendar_sync_worker is None:
        _calendar_sync_worker = CalendarSyncWorker()
    return _calendar_sync_worker
