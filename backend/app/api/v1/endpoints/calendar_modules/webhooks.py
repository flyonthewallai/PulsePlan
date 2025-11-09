"""
Google Calendar webhook endpoint for watch notifications.
Handles real-time sync updates from Google Calendar.
"""
from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks
from typing import Optional
import logging
import secrets

from app.config.core.settings import get_settings
from app.database.repositories.calendar_repositories.calendar_repository import get_calendar_calendar_repository
from app.jobs.calendar.calendar_sync_worker import get_calendar_sync_worker

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/google/calendar")
async def google_calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_goog_channel_id: Optional[str] = Header(None, alias="X-Goog-Channel-Id"),
    x_goog_channel_token: Optional[str] = Header(None, alias="X-Goog-Channel-Token"),
    x_goog_resource_id: Optional[str] = Header(None, alias="X-Goog-Resource-Id"),
    x_goog_resource_state: Optional[str] = Header(None, alias="X-Goog-Resource-State"),
):
    """
    Handle Google Calendar watch notifications.

    Headers:
        X-Goog-Channel-Id: Channel ID
        X-Goog-Channel-Token: Verification token
        X-Goog-Resource-Id: Resource ID
        X-Goog-Resource-State: State (sync, exists, not_exists)
    """
    settings = get_settings()

    # Verify token using constant-time comparison to prevent timing attacks
    if not x_goog_channel_token or not secrets.compare_digest(
        x_goog_channel_token, settings.GOOGLE_WEBHOOK_VERIFICATION_TOKEN
    ):
        logger.warning(f"Invalid webhook token received from channel {x_goog_channel_id}")
        raise HTTPException(status_code=403, detail="Invalid verification token")

    # Log webhook event
    logger.info(
        f"Received Google Calendar webhook: channel={x_goog_channel_id}, "
        f"resource={x_goog_resource_id}, state={x_goog_resource_state}"
    )

    # Handle different resource states
    if x_goog_resource_state == "sync":
        # Initial sync message - acknowledge but don't process
        logger.info(f"Sync message received for channel {x_goog_channel_id}")
        return {"status": "acknowledged", "message": "Sync message received"}

    if x_goog_resource_state in ["exists", "not_exists"]:
        # Calendar has changed - trigger incremental pull
        calendar_repo = get_calendar_calendar_repository()

        # Find calendar by watch channel details using repository
        calendar = await calendar_repo.get_by_watch_channel(
            channel_id=x_goog_channel_id,
            resource_id=x_goog_resource_id
        )

        if not calendar:
            logger.warning(f"Calendar not found for channel {x_goog_channel_id}")
            return {"status": "ignored", "message": "Calendar not found"}

        calendar_id = calendar["id"]

        # Enqueue pull_incremental in background
        sync_worker = get_calendar_sync_worker()
        background_tasks.add_task(sync_worker.pull_incremental, calendar_id)

        logger.info(f"Queued incremental pull for calendar {calendar_id}")

        return {
            "status": "queued",
            "message": f"Incremental sync queued for calendar {calendar_id}"
        }

    # Unknown state
    logger.warning(f"Unknown resource state: {x_goog_resource_state}")
    return {"status": "ignored", "message": "Unknown resource state"}


@router.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "healthy"}

