"""
Calendar Synchronization API Endpoints
Provides REST API for calendar sync operations, webhook handling, and conflict management
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, CurrentUser
from app.services.calendar_sync_service import get_calendar_sync_service, get_calendar_webhook_service
from app.services.calendar_background_worker import get_calendar_scheduler, get_calendar_background_worker
from app.agents.orchestrator import get_agent_orchestrator, WorkflowRequest, WorkflowType

logger = logging.getLogger(__name__)
router = APIRouter()


# Request Models
class CalendarSyncRequest(BaseModel):
    days_ahead: int = Field(default=30, ge=1, le=365)
    force_refresh: bool = False
    providers: Optional[List[str]] = None  # ["google", "microsoft"] or None for all


class CalendarEventRequest(BaseModel):
    provider: str = Field(..., regex="^(google|microsoft)$")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: str  # ISO 8601 datetime
    end_time: str    # ISO 8601 datetime
    location: Optional[str] = None
    timezone: str = "UTC"


class CalendarEventUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None


class ConflictResolutionRequest(BaseModel):
    conflict_id: str
    resolution_action: str = Field(..., regex="^(keep_event1|keep_event2|merge_events|manual)$")
    keep_event_id: Optional[str] = None


class WebhookSubscriptionRequest(BaseModel):
    provider: str = Field(..., regex="^(google|microsoft)$")
    enabled: bool = True


# Response Models
class CalendarSyncResponse(BaseModel):
    user_id: str
    sync_timestamp: str
    providers_synced: List[str]
    total_events: int
    errors: List[str]
    conflict_summary: Optional[Dict[str, Any]] = None


class CalendarEventResponse(BaseModel):
    id: str
    provider: str
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    location: Optional[str] = None
    status: str
    is_all_day: bool
    created_at: str
    updated_at: str


class ConflictResponse(BaseModel):
    id: str
    user_id: str
    event1_id: str
    event2_id: str
    conflict_type: str
    confidence_score: float
    resolution_status: str
    detected_at: str
    resolved_at: Optional[str] = None


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendars(
    request: CalendarSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Trigger calendar synchronization from connected providers
    """
    try:
        calendar_service = get_calendar_sync_service()
        
        # Perform calendar sync
        sync_results = await calendar_service.sync_user_calendars(
            user_id=current_user.user_id,
            days_ahead=request.days_ahead,
            force_refresh=request.force_refresh
        )
        
        # Schedule conflict detection in background
        background_tasks.add_task(
            _detect_conflicts_background,
            current_user.user_id
        )
        
        return CalendarSyncResponse(
            user_id=current_user.user_id,
            sync_timestamp=sync_results["sync_timestamp"],
            providers_synced=sync_results["providers_synced"],
            total_events=sync_results["total_events"],
            errors=sync_results["errors"]
        )
        
    except Exception as e:
        logger.error(f"Error syncing calendars for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calendar sync failed: {str(e)}"
        )


@router.get("/events", response_model=List[CalendarEventResponse])
async def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get calendar events for the current user
    """
    try:
        calendar_service = get_calendar_sync_service()
        
        # Parse date filters
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        events = await calendar_service.get_user_events(
            user_id=current_user.user_id,
            start_date=start_dt,
            end_date=end_dt,
            provider=provider
        )
        
        return [
            CalendarEventResponse(
                id=event["id"],
                provider=event["provider"],
                title=event["title"],
                description=event.get("description"),
                start_time=event["start_time"],
                end_time=event["end_time"],
                location=event.get("location"),
                status=event.get("status", "confirmed"),
                is_all_day=event.get("is_all_day", False),
                created_at=event.get("created_at", ""),
                updated_at=event.get("updated_at", "")
            )
            for event in events
        ]
        
    except Exception as e:
        logger.error(f"Error getting calendar events for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar events: {str(e)}"
        )


@router.post("/events", response_model=CalendarEventResponse)
async def create_calendar_event(
    request: CalendarEventRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new calendar event via AI agent workflow
    """
    try:
        # Use the AI agent system for calendar operations
        orchestrator = get_agent_orchestrator()
        
        workflow_request = WorkflowRequest(
            workflow_type=WorkflowType.CALENDAR,
            input_data={
                "operation": "create",
                "provider": request.provider,
                "event_data": {
                    "title": request.title,
                    "description": request.description,
                    "start": request.start_time,
                    "end": request.end_time,
                    "location": request.location,
                    "timezone": request.timezone
                }
            },
            user_id=current_user.user_id
        )
        
        result = await orchestrator.execute_workflow(workflow_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create calendar event: {result.error}"
            )
        
        event_data = result.output_data.get("event", {})
        
        return CalendarEventResponse(
            id=event_data.get("id", ""),
            provider=request.provider,
            title=event_data.get("title", request.title),
            description=event_data.get("description"),
            start_time=event_data.get("start_time", request.start_time),
            end_time=event_data.get("end_time", request.end_time),
            location=event_data.get("location"),
            status=event_data.get("status", "confirmed"),
            is_all_day=event_data.get("is_all_day", False),
            created_at=event_data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=event_data.get("updated_at", datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating calendar event for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create calendar event: {str(e)}"
        )


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: str,
    request: CalendarEventUpdateRequest,
    provider: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update an existing calendar event
    """
    try:
        # Use the AI agent system for calendar operations
        orchestrator = get_agent_orchestrator()
        
        # Prepare update data (only include provided fields)
        event_data = {}
        if request.title is not None:
            event_data["title"] = request.title
        if request.description is not None:
            event_data["description"] = request.description
        if request.start_time is not None:
            event_data["start"] = request.start_time
        if request.end_time is not None:
            event_data["end"] = request.end_time
        if request.location is not None:
            event_data["location"] = request.location
        
        workflow_request = WorkflowRequest(
            workflow_type=WorkflowType.CALENDAR,
            input_data={
                "operation": "update",
                "provider": provider,
                "event_id": event_id,
                "event_data": event_data
            },
            user_id=current_user.user_id
        )
        
        result = await orchestrator.execute_workflow(workflow_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update calendar event: {result.error}"
            )
        
        event_data = result.output_data.get("event", {})
        
        return CalendarEventResponse(
            id=event_data.get("id", event_id),
            provider=provider,
            title=event_data.get("title", ""),
            description=event_data.get("description"),
            start_time=event_data.get("start_time", ""),
            end_time=event_data.get("end_time", ""),
            location=event_data.get("location"),
            status=event_data.get("status", "confirmed"),
            is_all_day=event_data.get("is_all_day", False),
            created_at=event_data.get("created_at", ""),
            updated_at=event_data.get("updated_at", datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating calendar event {event_id} for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update calendar event: {str(e)}"
        )


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    provider: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a calendar event
    """
    try:
        # Use the AI agent system for calendar operations
        orchestrator = get_agent_orchestrator()
        
        workflow_request = WorkflowRequest(
            workflow_type=WorkflowType.CALENDAR,
            input_data={
                "operation": "delete",
                "provider": provider,
                "event_id": event_id
            },
            user_id=current_user.user_id
        )
        
        result = await orchestrator.execute_workflow(workflow_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete calendar event: {result.error}"
            )
        
        return {
            "message": "Calendar event deleted successfully",
            "event_id": event_id,
            "provider": provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting calendar event {event_id} for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete calendar event: {str(e)}"
        )


@router.get("/conflicts", response_model=List[ConflictResponse])
async def get_calendar_conflicts(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get unresolved calendar conflicts for the current user
    """
    try:
        from app.config.supabase import get_supabase_client
        
        supabase = get_supabase_client()
        
        response = await supabase.table("calendar_sync_conflicts").select(
            "id, user_id, event1_id, event2_id, conflict_type, confidence_score, "
            "resolution_status, detected_at, resolved_at"
        ).eq("user_id", current_user.user_id).eq("resolution_status", "unresolved").execute()
        
        conflicts = []
        for conflict in response.data:
            conflicts.append(ConflictResponse(
                id=conflict["id"],
                user_id=conflict["user_id"],
                event1_id=conflict["event1_id"],
                event2_id=conflict["event2_id"],
                conflict_type=conflict["conflict_type"],
                confidence_score=conflict["confidence_score"],
                resolution_status=conflict["resolution_status"],
                detected_at=conflict["detected_at"],
                resolved_at=conflict.get("resolved_at")
            ))
        
        return conflicts
        
    except Exception as e:
        logger.error(f"Error getting calendar conflicts for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar conflicts: {str(e)}"
        )


@router.post("/conflicts/resolve")
async def resolve_calendar_conflict(
    request: ConflictResolutionRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Resolve a calendar synchronization conflict
    """
    try:
        calendar_service = get_calendar_sync_service()
        
        # Get conflict details
        from app.config.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        conflict_response = await supabase.table("calendar_sync_conflicts").select(
            "*"
        ).eq("id", request.conflict_id).eq("user_id", current_user.user_id).single().execute()
        
        if not conflict_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conflict not found"
            )
        
        conflict = conflict_response.data
        
        # Resolve conflict based on action
        if request.resolution_action == "keep_event1":
            await calendar_service._resolve_conflict(
                current_user.user_id,
                conflict["event1_id"],
                conflict["event2_id"],
                "keep_event1",
                "manual_resolution"
            )
        elif request.resolution_action == "keep_event2":
            await calendar_service._resolve_conflict(
                current_user.user_id,
                conflict["event2_id"],
                conflict["event1_id"],
                "keep_event1",  # Keep the second event by swapping parameters
                "manual_resolution"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported resolution action"
            )
        
        return {
            "message": "Conflict resolved successfully",
            "conflict_id": request.conflict_id,
            "resolution_action": request.resolution_action
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflict {request.conflict_id} for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflict: {str(e)}"
        )


@router.get("/sync/status")
async def get_sync_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get calendar synchronization status for the current user
    """
    try:
        calendar_service = get_calendar_sync_service()
        sync_status = await calendar_service.get_sync_status(current_user.user_id)
        
        return sync_status
        
    except Exception as e:
        logger.error(f"Error getting sync status for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/sync/schedule")
async def schedule_auto_sync(
    sync_frequency_minutes: int = 10,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Schedule automatic calendar synchronization for the current user
    """
    try:
        scheduler = get_calendar_scheduler()
        success = await scheduler.schedule_user_sync(
            current_user.user_id,
            sync_frequency_minutes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to schedule automatic sync"
            )
        
        return {
            "message": "Automatic sync scheduled successfully",
            "sync_frequency_minutes": sync_frequency_minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling auto sync for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule automatic sync: {str(e)}"
        )


@router.post("/webhooks/google")
async def handle_google_calendar_webhook(
    request: Request
):
    """
    Handle Google Calendar webhook notifications
    """
    try:
        # Get headers for webhook validation
        resource_state = request.headers.get("X-Goog-Resource-State")
        resource_id = request.headers.get("X-Goog-Resource-Id")
        channel_id = request.headers.get("X-Goog-Channel-Id")
        
        if not resource_state or not resource_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook headers"
            )
        
        # Extract user_id from channel_id (format: user_{user_id})
        if not channel_id or not channel_id.startswith("user_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid channel ID"
            )
        
        user_id = channel_id.replace("user_", "")
        
        # Queue webhook for background processing
        background_worker = get_calendar_background_worker()
        success = await background_worker.queue_webhook("google", {
            "user_id": user_id,
            "resource_id": resource_id,
            "resource_state": resource_state,
            "received_at": datetime.utcnow().isoformat()
        })
        
        if not success:
            logger.error(f"Failed to queue Google webhook for user {user_id}")
        
        return {"status": "received"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Google calendar webhook: {e}")
        # Return 200 to prevent webhook retries for server errors
        return {"status": "error", "message": str(e)}


@router.post("/webhooks/microsoft")
async def handle_microsoft_calendar_webhook(
    request: Request
):
    """
    Handle Microsoft Graph webhook notifications
    """
    try:
        body = await request.json()
        
        # Microsoft Graph sends an array of notifications
        notifications = body.get("value", [])
        
        background_worker = get_calendar_background_worker()
        
        for notification in notifications:
            subscription_id = notification.get("subscriptionId")
            change_type = notification.get("changeType")
            resource = notification.get("resource")
            
            # Extract user_id from subscription (you would store this mapping)
            # For now, we'll use a placeholder implementation
            user_id = "placeholder"  # This should be retrieved from subscription mapping
            
            success = await background_worker.queue_webhook("microsoft", {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "change_type": change_type,
                "resource": resource,
                "received_at": datetime.utcnow().isoformat()
            })
            
            if not success:
                logger.error(f"Failed to queue Microsoft webhook for subscription {subscription_id}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling Microsoft calendar webhook: {e}")
        # Return 200 to prevent webhook retries for server errors
        return {"status": "error", "message": str(e)}


# Background task functions
async def _detect_conflicts_background(user_id: str):
    """Background task to detect and resolve conflicts"""
    try:
        calendar_service = get_calendar_sync_service()
        conflict_results = await calendar_service.detect_and_resolve_conflicts(user_id)
        
        logger.info(
            f"Background conflict detection completed for user {user_id}: "
            f"{conflict_results['conflicts_detected']} detected, "
            f"{conflict_results['conflicts_resolved']} resolved"
        )
        
    except Exception as e:
        logger.error(f"Error in background conflict detection for user {user_id}: {e}")