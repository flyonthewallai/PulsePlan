"""
Calendar Event Service
Business logic layer for calendar event operations

Handles CRUD operations for calendar events with proper validation and enrichment.
Implements RULES.md Section 1.2 - Service layer pattern.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from app.database.repositories.calendar_repositories import (
    CalendarEventRepository,
    get_calendar_event_repository
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class CalendarEventService:
    """
    Service for calendar event business logic

    Handles:
    - Calendar event CRUD operations
    - Event validation
    - Time range filtering
    - Event enrichment with metadata
    """

    def __init__(self, repository: CalendarEventRepository = None):
        """
        Initialize calendar event service with optional repository injection

        Args:
            repository: Calendar event repository instance (injected for testing)
        """
        self.repo = repository or get_calendar_event_repository()

    async def get_events(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        calendar_ids: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events for a user with optional filters

        Args:
            user_id: User ID
            start_time: Filter events starting after this time
            end_time: Filter events starting before this time
            calendar_ids: Filter by specific calendar IDs
            limit: Maximum number of events to return

        Returns:
            List of calendar event dictionaries

        Raises:
            ServiceError: If fetch fails
        """
        try:
            filters = {"user_id": user_id}

            if calendar_ids:
                filters["calendar_id__in"] = calendar_ids

            events = await self.repo.get_all(filters=filters, limit=limit)

            # Filter by time range if provided
            if start_time or end_time:
                filtered_events = []
                for event in events:
                    event_start = event.get("start_time")
                    if isinstance(event_start, str):
                        event_start = datetime.fromisoformat(event_start.replace('Z', '+00:00'))

                    # Check if event falls within range
                    if start_time and event_start < start_time:
                        continue
                    if end_time and event_start > end_time:
                        continue

                    filtered_events.append(event)

                events = filtered_events

            # Sort by start time
            events.sort(key=lambda e: e.get("start_time", ""))

            logger.info(
                f"Retrieved {len(events)} calendar events for user {user_id}"
            )

            return events

        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to fetch calendar events",
                operation="get_events",
                details={
                    "user_id": user_id,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                }
            )

    async def get_event(
        self,
        event_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single calendar event by ID

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)

        Returns:
            Event dictionary or None if not found

        Raises:
            ServiceError: If fetch fails
        """
        try:
            event = await self.repo.get_by_id(event_id)

            # Verify user owns this event
            if event and event.get("user_id") != user_id:
                logger.warning(
                    f"User {user_id} attempted to access event {event_id} "
                    f"owned by {event.get('user_id')}"
                )
                return None

            return event

        except Exception as e:
            logger.error(f"Error fetching calendar event: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to fetch calendar event",
                operation="get_event",
                details={"event_id": event_id, "user_id": user_id}
            )

    async def create_event(
        self,
        user_id: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new calendar event

        Args:
            user_id: User ID
            event_data: Event data dictionary

        Returns:
            Created event dictionary

        Raises:
            ServiceError: If validation or creation fails
        """
        try:
            # Validate required fields
            if not event_data.get("title"):
                raise ServiceError(
                    message="Event title is required",
                    operation="create_event"
                )

            if not event_data.get("start_time"):
                raise ServiceError(
                    message="Event start_time is required",
                    operation="create_event"
                )

            if not event_data.get("end_time"):
                raise ServiceError(
                    message="Event end_time is required",
                    operation="create_event"
                )

            # Ensure user_id is set
            event_data["user_id"] = user_id

            # Create event
            created_event = await self.repo.create(event_data)

            logger.info(
                f"Created calendar event {created_event['id']} for user {user_id}"
            )

            return created_event

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to create calendar event",
                operation="create_event",
                details={"user_id": user_id}
            )

    async def update_event(
        self,
        event_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a calendar event

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)
            updates: Fields to update

        Returns:
            Updated event dictionary

        Raises:
            ServiceError: If not found, unauthorized, or update fails
        """
        try:
            # Verify user owns this event
            existing_event = await self.get_event(event_id, user_id)

            if not existing_event:
                raise ServiceError(
                    message="Event not found or access denied",
                    operation="update_event",
                    details={"event_id": event_id}
                )

            # Update event
            updated_event = await self.repo.update(event_id, updates)

            logger.info(f"Updated calendar event {event_id}")

            return updated_event

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error updating calendar event: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to update calendar event",
                operation="update_event",
                details={"event_id": event_id, "user_id": user_id}
            )

    async def delete_event(
        self,
        event_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a calendar event

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted successfully

        Raises:
            ServiceError: If not found, unauthorized, or delete fails
        """
        try:
            # Verify user owns this event
            existing_event = await self.get_event(event_id, user_id)

            if not existing_event:
                raise ServiceError(
                    message="Event not found or access denied",
                    operation="delete_event",
                    details={"event_id": event_id}
                )

            # Delete event
            deleted = await self.repo.delete(event_id)

            logger.info(f"Deleted calendar event {event_id}")

            return deleted

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to delete calendar event",
                operation="delete_event",
                details={"event_id": event_id, "user_id": user_id}
            )

    async def get_upcoming_events(
        self,
        user_id: str,
        hours_ahead: int = 24,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming events for a user

        Args:
            user_id: User ID
            hours_ahead: How many hours ahead to look
            limit: Maximum number of events

        Returns:
            List of upcoming events sorted by start time

        Raises:
            ServiceError: If fetch fails
        """
        from datetime import timezone, timedelta

        try:
            now = datetime.now(timezone.utc)
            end_time = now + timedelta(hours=hours_ahead)

            events = await self.get_events(
                user_id=user_id,
                start_time=now,
                end_time=end_time,
                limit=limit
            )

            logger.info(
                f"Retrieved {len(events)} upcoming events for user {user_id}"
            )

            return events

        except Exception as e:
            logger.error(f"Error fetching upcoming events: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to fetch upcoming events",
                operation="get_upcoming_events",
                details={"user_id": user_id, "hours_ahead": hours_ahead}
            )


def get_calendar_event_service() -> CalendarEventService:
    """
    Factory function for CalendarEventService

    Used for dependency injection in endpoints and services.
    """
    return CalendarEventService()
