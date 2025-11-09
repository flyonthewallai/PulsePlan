"""
Timeblock Service
Business logic for unified calendar view (timeblocks)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.database.repositories.calendar_repositories import (
    TimeblocksRepository,
    get_timeblocks_repository,
    CalendarLinkRepository,
    CalendarCalendarRepository,
    CalendarEventRepository,
    get_calendar_link_repository,
    get_calendar_calendar_repository,
    get_calendar_event_repository
)
from app.database.repositories.user_repositories import UserRepository, get_user_repository, CourseRepository, get_course_repository
from app.database.repositories.task_repositories import TaskRepository
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TimeblockService:
    """
    Service layer for timeblock operations
    
    Handles business logic for unified calendar view including:
    - Fetching and enriching timeblocks with metadata
    - Two-way calendar sync (task linking)
    - Calendar selection and configuration
    """

    def __init__(
        self,
        timeblock_repo: TimeblocksRepository = None,
        user_repo: UserRepository = None,
        course_repo: CourseRepository = None,
        calendar_link_repo: CalendarLinkRepository = None,
        calendar_calendar_repo: CalendarCalendarRepository = None,
        calendar_event_repo: CalendarEventRepository = None,
        task_repo: TaskRepository = None
    ):
        """Initialize TimeblockService with optional dependencies"""
        self.timeblock_repo = timeblock_repo or TimeblocksRepository()
        self.user_repo = user_repo or UserRepository()
        self.course_repo = course_repo or CourseRepository()
        self.calendar_link_repo = calendar_link_repo or CalendarLinkRepository()
        self.calendar_calendar_repo = calendar_calendar_repo or CalendarCalendarRepository()
        self.calendar_event_repo = calendar_event_repo or CalendarEventRepository()
        self.task_repo = task_repo or TaskRepository()

    async def get_timeblocks(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get unified timeblocks with full enriched metadata
        
        Fetches timeblocks from the v_timeblocks view and enriches them with:
        - Premium status for readonly determination
        - Course colors for tasks
        - Calendar link IDs
        - Full task metadata (for tasks)
        - Full event metadata (for calendar events)
        
        Args:
            user_id: User ID
            start_time: Start of time window (timezone-aware)
            end_time: End of time window (timezone-aware)
        
        Returns:
            List of enriched timeblock dictionaries
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            # Fetch base timeblocks
            rows = await self.timeblock_repo.fetch_timeblocks(user_id, start_time, end_time)
            
            logger.info(f"[Timeblocks] Fetched {len(rows)} raw rows for user {user_id}")
            
            if not rows:
                return []

            # Get user premium status
            is_premium = await self.user_repo.is_premium(user_id)
            
            # Get course colors
            courses = await self.course_repo.get_by_user_id(user_id)
            course_colors = {c["id"]: c.get("color") for c in courses}
            
            # Get calendar links
            links = await self.calendar_link_repo.get_by_user_id(user_id)
            task_links = {link["task_id"]: link["id"] for link in links if link.get("task_id")}
            event_links = {
                (link["provider"], link["provider_event_id"]): link["id"]
                for link in links if link.get("provider_event_id")
            }
            
            # Get primary write calendar
            primary_write_cal = await self.calendar_calendar_repo.get_primary_write_calendar(user_id)
            primary_write_cal_id = primary_write_cal["provider_calendar_id"] if primary_write_cal else None
            
            # Enrich each timeblock
            enriched_items = []
            for row in rows:
                enriched = await self._enrich_timeblock(
                    row,
                    is_premium,
                    course_colors,
                    task_links,
                    event_links,
                    primary_write_cal_id
                )
                enriched_items.append(enriched)
            
            logger.info(f"[Timeblocks] Returning {len(enriched_items)} enriched items")
            return enriched_items
        
        except Exception as e:
            logger.error(f"Failed to get timeblocks for user {user_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get timeblocks: {str(e)}",
                service="TimeblockService",
                operation="get_timeblocks",
                details={"user_id": user_id, "start_time": start_time, "end_time": end_time}
            )

    async def _enrich_timeblock(
        self,
        row: Dict[str, Any],
        is_premium: bool,
        course_colors: Dict[str, str],
        task_links: Dict[str, str],
        event_links: Dict[tuple, str],
        primary_write_cal_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Enrich a single timeblock with full metadata
        
        Args:
            row: Raw timeblock row from v_timeblocks view
            is_premium: Whether user has premium subscription
            course_colors: Mapping of course_id -> color
            task_links: Mapping of task_id -> link_id
            event_links: Mapping of (provider, provider_event_id) -> link_id
            primary_write_cal_id: Primary write calendar ID
        
        Returns:
            Enriched timeblock dictionary
        """
        # Determine linkId
        link_id = None
        if row.get("task_id"):
            link_id = task_links.get(row["task_id"])
        elif row.get("provider_event_id") and row.get("provider"):
            link_id = event_links.get((row["provider"], row["provider_event_id"]))
        
        # Determine readonly
        readonly = row.get("readonly", True)
        if row["source"] == "task":
            readonly = False  # Tasks always editable
        elif row["source"] == "calendar" and is_premium:
            # Calendar events editable if linked and on primary write calendar
            if link_id and row.get("provider_calendar_id") == primary_write_cal_id:
                readonly = False
        
        # Base enriched data
        enriched = {
            "id": row["id"],
            "source": row["source"],
            "provider": row.get("provider"),
            "title": row["title"],
            "start": self._format_datetime(row["start_at"]),
            "end": self._format_datetime(row["end_at"]),
            "isAllDay": row.get("is_all_day", False),
            "readonly": readonly,
            "linkId": link_id,
            "description": None,
            "location": None,
            "color": None,
        }
        
        # Enrich based on source type
        if row["source"] == "task":
            task_data = await self._enrich_task(row["task_id"], course_colors)
            enriched.update(task_data)
        elif row["source"] == "calendar":
            event_data = await self._enrich_calendar_event(row.get("provider_event_id"))
            enriched.update(event_data)
        
        return enriched

    async def _enrich_task(
        self,
        task_id: str,
        course_colors: Dict[str, str]
    ) -> Dict[str, Any]:
        """Fetch and format task-specific metadata"""
        try:
            # Fetch full task with course info
            task = await self.task_repo.get_by_id_with_course(task_id)
            
            if not task:
                return {}
            
            course_id = task.get("course_id")
            course_data = task.get("courses", {}) if isinstance(task.get("courses"), dict) else {}
            
            return {
                "description": task.get("description"),
                "location": task.get("location"),
                "color": course_colors.get(course_id) if course_id else None,
                "priority": task.get("priority"),
                "taskStatus": task.get("status"),
                "estimatedMinutes": task.get("estimated_minutes"),
                "schedulingRationale": task.get("scheduling_rationale"),
                "tags": task.get("tags"),
                "courseId": course_id,
                "courseName": course_data.get("name"),
                "courseColor": course_data.get("color"),
            }
        
        except Exception as e:
            logger.warning(f"Failed to enrich task {task_id}: {e}")
            return {}

    async def _enrich_calendar_event(
        self,
        provider_event_id: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch and format calendar event metadata"""
        try:
            if not provider_event_id:
                return {}
            
            event = await self.calendar_event_repo.get_by_external_id(provider_event_id)
            
            if not event:
                return {}
            
            # Format organizer and creator
            organizer = None
            creator = None
            if event.get("organizer_email"):
                organizer = {"email": event["organizer_email"]}
            if event.get("creator_email"):
                creator = {"email": event["creator_email"]}
            
            return {
                "description": event.get("description"),
                "location": event.get("location"),
                "htmlLink": event.get("html_link"),
                "attendees": event.get("attendees"),
                "organizer": organizer,
                "creator": creator,
                "status": event.get("status"),
                "transparency": event.get("transparency"),
                "visibility": event.get("visibility"),
                "categories": event.get("categories"),
                "importance": event.get("importance"),
                "sensitivity": event.get("sensitivity"),
                "recurrence": event.get("recurrence"),
                "hasAttachments": event.get("has_attachments", False),
            }
        
        except Exception as e:
            logger.warning(f"Failed to enrich calendar event {provider_event_id}: {e}")
            return {}

    def _format_datetime(self, dt) -> str:
        """Format datetime for API response"""
        if isinstance(dt, str):
            return dt
        else:
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    async def link_task_to_calendar(
        self,
        task_id: str,
        user_id: str,
        sync_worker
    ) -> Dict[str, Any]:
        """
        Link a task to the primary write calendar (premium only)
        
        Args:
            task_id: Task ID to link
            user_id: User ID for authorization
            sync_worker: Calendar sync worker instance
        
        Returns:
            Result dictionary with success, message, and event_id
            
        Raises:
            ServiceError: If operation fails
            ValueError: If not premium or task not found
        """
        try:
            # Check premium status
            is_premium = await self.user_repo.is_premium(user_id)
            if not is_premium:
                raise ValueError("Premium subscription required for two-way calendar sync")
            
            # Verify task belongs to user
            task = await self.task_repo.get_by_id_and_user(task_id, user_id)
            if not task:
                raise ValueError("Task not found")
            
            # Push to calendar via sync worker
            result = await sync_worker.push_from_task(task_id)
            
            if not result.get("success"):
                raise ValueError(result.get("error", "Failed to link task"))
            
            return {
                "success": True,
                "message": f"Task {result.get('action', 'linked')}",
                "eventId": result.get("event_id")
            }
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to link task {task_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to link task: {str(e)}",
                service="TimeblockService",
                operation="link_task_to_calendar",
                details={"task_id": task_id, "user_id": user_id}
            )

    async def unlink_task_from_calendar(
        self,
        task_id: str,
        user_id: str,
        delete_event: bool = False
    ) -> Dict[str, Any]:
        """
        Unlink a task from calendar (premium only)
        
        Args:
            task_id: Task ID to unlink
            user_id: User ID for authorization
            delete_event: Whether to delete the provider event
        
        Returns:
            Result dictionary with success and message
            
        Raises:
            ServiceError: If operation fails
            ValueError: If not premium or link not found
        """
        try:
            # Check premium status
            is_premium = await self.user_repo.is_premium(user_id)
            if not is_premium:
                raise ValueError("Premium subscription required")
            
            # Get link
            link = await self.calendar_link_repo.get_by_task_id(task_id, user_id)
            if not link:
                raise ValueError("Task not linked")
            
            # Delete provider event if requested
            if delete_event:
                try:
                    calendar = await self.calendar_calendar_repo.get_by_id(link["calendar_id"])
                    if calendar:
                        from app.integrations.providers.google import GoogleCalendarClient
                        
                        google_client = GoogleCalendarClient()
                        await google_client.delete_event(
                            calendar_id=UUID(calendar["id"]),
                            provider_calendar_id=calendar["provider_calendar_id"],
                            event_id=link["provider_event_id"]
                        )
                except Exception as e:
                    logger.warning(f"Failed to delete provider event: {e}")
            
            # Delete link
            await self.calendar_link_repo.delete_by_id(link["id"])
            
            return {
                "success": True,
                "message": "Task unlinked successfully",
                "eventDeleted": delete_event
            }
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to unlink task {task_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to unlink task: {str(e)}",
                service="TimeblockService",
                operation="unlink_task_from_calendar",
                details={"task_id": task_id, "user_id": user_id, "delete_event": delete_event}
            )

    async def set_primary_write_calendar(
        self,
        calendar_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Set a calendar as the primary write calendar
        
        Args:
            calendar_id: Calendar ID to set as primary
            user_id: User ID for authorization
        
        Returns:
            Result dictionary with success and message
            
        Raises:
            ServiceError: If operation fails
            ValueError: If calendar not found
        """
        try:
            # Verify calendar belongs to user
            calendars = await self.calendar_calendar_repo.get_by_user_id(user_id)
            calendar_ids = [cal["id"] for cal in calendars]
            
            if calendar_id not in calendar_ids:
                raise ValueError("Calendar not found")
            
            # Unset current primary write
            await self.calendar_calendar_repo.unset_primary_write(user_id)
            
            # Set new primary
            await self.calendar_calendar_repo.set_primary_write(calendar_id)
            
            return {
                "success": True,
                "message": f"Calendar {calendar_id} set as primary write"
            }
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to set primary write calendar: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to set primary write calendar: {str(e)}",
                service="TimeblockService",
                operation="set_primary_write_calendar",
                details={"calendar_id": calendar_id, "user_id": user_id}
            )

    async def select_active_calendars(
        self,
        calendar_ids: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Set which calendars are active (shown in central view)
        
        Args:
            calendar_ids: List of calendar IDs to activate
            user_id: User ID for authorization
        
        Returns:
            Result dictionary with success and message
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            # Deactivate all calendars for user
            await self.calendar_calendar_repo.deactivate_all(user_id)
            
            # Activate selected calendars
            for calendar_id in calendar_ids:
                await self.calendar_calendar_repo.activate_calendar(calendar_id, user_id)
            
            return {
                "success": True,
                "message": f"Updated {len(calendar_ids)} active calendars"
            }
        
        except Exception as e:
            logger.error(f"Failed to select active calendars: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to select active calendars: {str(e)}",
                service="TimeblockService",
                operation="select_active_calendars",
                details={"calendar_ids": calendar_ids, "user_id": user_id}
            )


    async def create_timeblock(
        self,
        user_id: str,
        timeblock_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new timeblock
        
        Args:
            user_id: User ID
            timeblock_data: Timeblock data including title, start_time, end_time, type, etc.
                Required fields: title, start_time, end_time
                Optional fields: task_id, type, status, source, location, notes, metadata, etc.
        
        Returns:
            Created timeblock dictionary
            
        Raises:
            ServiceError: If operation fails or required fields are missing
        """
        try:
            # Validate required fields
            if not timeblock_data.get("title"):
                raise ValueError("title is required")
            if not timeblock_data.get("start_time"):
                raise ValueError("start_time is required")
            if not timeblock_data.get("end_time"):
                raise ValueError("end_time is required")
            
            # Parse datetime fields if they're strings
            start_time = timeblock_data["start_time"]
            end_time = timeblock_data["end_time"]
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            
            # Create timeblock with repository method
            created = await self.timeblock_repo.create_timeblock(
                user_id=user_id,
                title=timeblock_data["title"],
                start_time=start_time,
                end_time=end_time,
                task_id=timeblock_data.get("task_id"),
                type=timeblock_data.get("type", "task_block"),
                status=timeblock_data.get("status", "scheduled"),
                source=timeblock_data.get("source", "pulse"),
                agent_reasoning=timeblock_data.get("agent_reasoning"),
                location=timeblock_data.get("location"),
                all_day=timeblock_data.get("all_day", False),
                notes=timeblock_data.get("notes"),
                metadata=timeblock_data.get("metadata", {})
            )
            
            if not created:
                raise ServiceError(
                    message="Failed to create timeblock",
                    service="TimeblockService",
                    operation="create_timeblock"
                )
            
            logger.info(f"Created timeblock {created.get('id')} for user {user_id}")
            return created
        
        except ValueError as e:
            logger.error(f"Invalid timeblock data: {e}")
            raise ServiceError(
                message=f"Invalid timeblock data: {str(e)}",
                service="TimeblockService",
                operation="create_timeblock",
                details={"user_id": user_id}
            )
        except Exception as e:
            logger.error(f"Failed to create timeblock: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to create timeblock: {str(e)}",
                service="TimeblockService",
                operation="create_timeblock",
                details={"user_id": user_id}
            )

    async def update_timeblock(
        self,
        timeblock_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing timeblock
        
        Args:
            timeblock_id: Timeblock ID
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update
        
        Returns:
            Updated timeblock dictionary or None if not found
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            # Update timeblock with ownership check
            updated = await self.timeblock_repo.update_timeblock(
                timeblock_id,
                user_id,
                updates
            )
            
            if not updated:
                logger.warning(f"Timeblock {timeblock_id} not found for user {user_id}")
                return None
            
            logger.info(f"Updated timeblock {timeblock_id} for user {user_id}")
            return updated
        
        except Exception as e:
            logger.error(f"Failed to update timeblock {timeblock_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to update timeblock: {str(e)}",
                service="TimeblockService",
                operation="update_timeblock",
                details={"timeblock_id": timeblock_id, "user_id": user_id}
            )

    async def delete_timeblock(
        self,
        timeblock_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a timeblock
        
        Args:
            timeblock_id: Timeblock ID
            user_id: User ID for ownership verification
        
        Returns:
            True if deleted, False if not found
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            # Delete timeblock with ownership check
            deleted = await self.timeblock_repo.delete_timeblock(timeblock_id, user_id)
            
            if deleted:
                logger.info(f"Deleted timeblock {timeblock_id} for user {user_id}")
            else:
                logger.warning(f"Timeblock {timeblock_id} not found for user {user_id}")
            
            return deleted
        
        except Exception as e:
            logger.error(f"Failed to delete timeblock {timeblock_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to delete timeblock: {str(e)}",
                service="TimeblockService",
                operation="delete_timeblock",
                details={"timeblock_id": timeblock_id, "user_id": user_id}
            )

    async def get_timeblock(
        self,
        timeblock_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single timeblock by ID
        
        Args:
            timeblock_id: Timeblock ID
            user_id: User ID for ownership verification
        
        Returns:
            Timeblock dictionary or None if not found
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            timeblock = await self.timeblock_repo.get_timeblock(timeblock_id, user_id)
            return timeblock
        
        except Exception as e:
            logger.error(f"Failed to get timeblock {timeblock_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get timeblock: {str(e)}",
                service="TimeblockService",
                operation="get_timeblock",
                details={"timeblock_id": timeblock_id, "user_id": user_id}
            )

    async def list_timeblocks_with_filters(
        self,
        user_id: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        List timeblocks with filters
        
        Args:
            user_id: User ID
            filters: Filter criteria (start_after, end_before, type, etc.)
        
        Returns:
            List of timeblock dictionaries
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            timeblocks = await self.timeblock_repo.list_timeblocks(user_id, filters)
            logger.info(f"Listed {len(timeblocks)} timeblocks for user {user_id} with filters")
            return timeblocks
        
        except Exception as e:
            logger.error(f"Failed to list timeblocks: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to list timeblocks: {str(e)}",
                service="TimeblockService",
                operation="list_timeblocks_with_filters",
                details={"user_id": user_id, "filters": filters}
            )


def get_timeblock_service() -> TimeblockService:
    """
    Dependency injection function for TimeblockService
    
    Returns:
        TimeblockService instance with default dependencies
    """
    return TimeblockService(
        timeblock_repo=get_timeblocks_repository(),
        user_repo=get_user_repository(),
        course_repo=get_course_repository(),
        calendar_link_repo=get_calendar_link_repository(),
        calendar_calendar_repo=get_calendar_calendar_repository(),
        calendar_event_repo=get_calendar_event_repository(),
        task_repo=get_task_repository()
    )

