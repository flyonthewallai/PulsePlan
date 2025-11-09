"""
Event repository for scheduler data access.

Handles loading calendar events and busy periods from various storage backends.
"""

import logging
from typing import List
from datetime import datetime, timedelta

from .base_repository import BaseEventRepository
from ...core.domain import BusyEvent

logger = logging.getLogger(__name__)


class EventRepository(BaseEventRepository):
    """Repository for calendar event data access operations."""

    def __init__(self, storage_backend):
        """
        Initialize event repository.

        Args:
            storage_backend: Storage backend instance
        """
        self.storage = storage_backend

    async def load_calendar_busy(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """
        Load busy calendar events within the horizon.

        Args:
            user_id: User identifier
            horizon_days: Days ahead to consider

        Returns:
            List of busy events
        """
        try:
            if self.storage.backend_type == "memory":
                return await self._load_events_from_memory(user_id, horizon_days)
            elif self.storage.backend_type == "database":
                return await self._load_events_from_db(user_id, horizon_days)
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to load events for user {user_id}: {e}")
            return []

    async def _load_events_from_memory(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """Load events from memory storage."""
        events = self.storage.get_events(user_id)

        # Filter events within horizon
        now = datetime.now()
        horizon_start = now
        horizon_end = now + timedelta(days=horizon_days)

        relevant_events = [
            event for event in events
            if event.start < horizon_end and event.end > horizon_start
        ]

        logger.debug(f"Loaded {len(relevant_events)} events for user {user_id}")
        return relevant_events

    async def _load_events_from_db(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """Load events from database."""
        try:
            from app.config.database.supabase import get_supabase

            supabase = get_supabase()

            # Calculate date range
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=horizon_days)

            # Query calendar events from database - first check calendar_events table, then tasks table for events
            calendar_response = supabase.table("calendar_events").select("*").eq(
                "user_id", user_id
            ).gte("start_time", start_date.isoformat()).lte(
                "end_time", end_date.isoformat()
            ).execute()

            # Also get events from consolidated tasks table
            tasks_response = supabase.table("tasks").select("*").eq(
                "user_id", user_id
            ).eq("task_type", "event").gte(
                "start_date", start_date.isoformat()
            ).lte("end_date", end_date.isoformat()).execute()

            events = []

            # Process calendar_events table data
            for event_data in calendar_response.data:
                # Convert database event to scheduler BusyEvent
                start_time = datetime.fromisoformat(event_data["start_time"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event_data["end_time"].replace('Z', '+00:00'))

                event = BusyEvent(
                    id=event_data["id"],
                    user_id=user_id,
                    title=event_data.get("title", "Calendar Event"),
                    start=start_time,
                    end=end_time,
                    source=event_data.get("provider", "calendar"),
                    hard=True,
                    location=event_data.get("location", ""),
                    metadata={"original_table": "calendar_events"}
                )
                events.append(event)

            # Process tasks table events
            for event_data in tasks_response.data:
                # Convert task event to scheduler BusyEvent
                start_time = datetime.fromisoformat(event_data["start_date"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(
                    event_data["end_date"].replace('Z', '+00:00')
                ) if event_data.get("end_date") else start_time + timedelta(hours=1)

                event = BusyEvent(
                    id=event_data["id"],
                    user_id=user_id,
                    title=event_data.get("title", "Event"),
                    start=start_time,
                    end=end_time,
                    source=event_data.get("sync_source", "pulse"),
                    hard=True,
                    location=event_data.get("location", ""),
                    metadata={"original_table": "tasks", "task_type": event_data.get("task_type")}
                )
                events.append(event)

            logger.info(f"Loaded {len(events)} calendar events from database for user {user_id}")
            return events

        except Exception as e:
            logger.error(f"Failed to load events from database: {e}")
            return []
