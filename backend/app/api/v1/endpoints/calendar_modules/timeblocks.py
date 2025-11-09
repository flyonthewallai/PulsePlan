"""
Unified timeblocks API - centralized calendar view.
Merges PulsePlan tasks with external calendar events.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.timeblock_service import TimeblockService, get_timeblock_service
from app.jobs.calendar.calendar_sync_worker import get_calendar_sync_worker
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)
router = APIRouter()


class TimeblockItem(BaseModel):
    """A single timeblock item (task or external event)."""
    id: str
    source: str  # "task" or "calendar"
    provider: Optional[str] = None  # "google", "outlook", "apple", or None
    title: str
    start: str  # ISO datetime
    end: str  # ISO datetime
    isAllDay: bool = False
    readonly: bool = True
    linkId: Optional[str] = None  # calendar_links.id if linked
    description: Optional[str] = None
    location: Optional[str] = None
    color: Optional[str] = None  # For visual distinction

    # Rich metadata for calendar events
    htmlLink: Optional[str] = None  # Direct link to Google Calendar/Outlook
    attendees: Optional[list] = None  # List of attendees with email/name
    organizer: Optional[dict] = None  # Event organizer {email, name}
    creator: Optional[dict] = None  # Event creator {email, name}
    status: Optional[str] = None  # Event status (confirmed, tentative, cancelled)
    transparency: Optional[str] = None  # opaque or transparent (busy/free)
    visibility: Optional[str] = None  # default, public, private
    categories: Optional[list] = None  # Event categories/labels
    importance: Optional[str] = None  # Outlook importance
    sensitivity: Optional[str] = None  # Outlook sensitivity
    recurrence: Optional[dict] = None  # Recurrence rules
    hasAttachments: bool = False  # Whether event has attachments

    # Task-specific metadata
    priority: Optional[str] = None  # Task priority (high, medium, low)
    taskStatus: Optional[str] = None  # Task status (todo, in_progress, completed)
    estimatedMinutes: Optional[int] = None  # Estimated duration
    schedulingRationale: Optional[str] = None  # Why AI scheduled it here
    tags: Optional[list] = None  # Task tags
    courseId: Optional[str] = None  # Associated course ID
    courseName: Optional[str] = None  # Course name
    courseColor: Optional[str] = None  # Course color


class TimeblockResponse(BaseModel):
    """Response containing all timeblocks."""
    items: List[TimeblockItem]


class SetPrimaryWriteRequest(BaseModel):
    """Request to set primary write calendar."""
    calendarId: str


class SelectCalendarsRequest(BaseModel):
    """Request to select active calendars."""
    calendarIds: List[str]


class LinkTaskRequest(BaseModel):
    """Request to link a task to calendar."""
    taskId: str


class UnlinkTaskRequest(BaseModel):
    """Request to unlink a task from calendar."""
    taskId: str
    deleteEvent: bool = False  # Whether to delete the provider event


@router.get("", response_model=TimeblockResponse)
async def get_timeblocks(
    from_dt: str = Query(..., alias="from", description="Start datetime (ISO format)"),
    to_dt: str = Query(..., alias="to", description="End datetime (ISO format)"),
    current_user: CurrentUser = Depends(get_current_user),
    service: TimeblockService = Depends(get_timeblock_service)
):
    """
    Get unified timeblocks (tasks + calendar events + busy blocks) for the specified time range.

    Uses optimized v_timeblocks VIEW with efficient range queries.

    Args:
        from_dt: Start datetime in ISO format
        to_dt: End datetime in ISO format
        current_user: Current authenticated user
        service: TimeblockService instance

    Returns:
        TimeblockResponse with all items in the time range
    """
    try:
        # Parse and validate datetimes with user timezone normalization
        from app.core.utils.timezone_utils import get_timezone_manager
        tz_manager = get_timezone_manager()

        user_id = current_user.user_id
        user_tz = await tz_manager.get_user_timezone(user_id)

        def _parse_bound(s: str) -> datetime:
            try:
                # If incoming has offset or Z, parse directly
                if "Z" in s or "+" in s or "-" in s[10:]:
                    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
                # Otherwise, treat as local time in user's timezone
                localized = tz_manager.ensure_timezone_aware(datetime.fromisoformat(s), user_tz)
                return localized.astimezone(timezone.utc)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid 'from'/'to' ISO timestamps")

        start_time = _parse_bound(from_dt)
        end_time = _parse_bound(to_dt)

        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="'from' must be before 'to'")

        # Get enriched timeblocks from service
        enriched_items = await service.get_timeblocks(user_id, start_time, end_time)

        # Convert to TimeblockItem objects
        items = [TimeblockItem(**item) for item in enriched_items]

        logger.info(f"[Timeblocks] Returning {len(items)} items to frontend")
        return TimeblockResponse(items=items)

    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_timeblocks")


@router.post("/link-task")
async def link_task(
    request: LinkTaskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: TimeblockService = Depends(get_timeblock_service),
    sync_worker = Depends(get_calendar_sync_worker)
):
    """
    Link a task to the primary write calendar (premium only).
    Creates or updates the provider event.

    Args:
        request: LinkTaskRequest with taskId
        current_user: Current authenticated user
        service: TimeblockService instance
        sync_worker: Calendar sync worker

    Returns:
        Success response with event details
    """
    try:
        result = await service.link_task_to_calendar(
            task_id=request.taskId,
            user_id=current_user.user_id,
            sync_worker=sync_worker
        )
        return result

    except ValueError as e:
        status_code = 402 if "premium" in str(e).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "link_task")


@router.delete("/unlink-task")
async def unlink_task(
    request: UnlinkTaskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: TimeblockService = Depends(get_timeblock_service)
):
    """
    Unlink a task from calendar (premium only).
    Optionally deletes the provider event.

    Args:
        request: UnlinkTaskRequest with taskId and deleteEvent flag
        current_user: Current authenticated user
        service: TimeblockService instance

    Returns:
        Success response
    """
    try:
        result = await service.unlink_task_from_calendar(
            task_id=request.taskId,
            user_id=current_user.user_id,
            delete_event=request.deleteEvent
        )
        return result

    except ValueError as e:
        status_code = 402 if "premium" in str(e).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "unlink_task")


@router.post("/set-primary-write")
async def set_primary_write(
    request: SetPrimaryWriteRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: TimeblockService = Depends(get_timeblock_service)
):
    """
    Set a calendar as the primary write calendar.
    Only one primary write calendar per user.

    Args:
        request: SetPrimaryWriteRequest with calendarId
        current_user: Current authenticated user
        service: TimeblockService instance

    Returns:
        Success response
    """
    try:
        result = await service.set_primary_write_calendar(
            calendar_id=request.calendarId,
            user_id=current_user.user_id
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "set_primary_write")


@router.post("/select-calendars")
async def select_calendars(
    request: SelectCalendarsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: TimeblockService = Depends(get_timeblock_service)
):
    """
    Set which calendars are active (shown in central view).

    Args:
        request: SelectCalendarsRequest with list of calendarIds
        current_user: Current authenticated user
        service: TimeblockService instance

    Returns:
        Success response
    """
    try:
        result = await service.select_active_calendars(
            calendar_ids=request.calendarIds,
            user_id=current_user.user_id
        )
        return result

    except Exception as e:
        return handle_endpoint_error(e, logger, "select_calendars")

