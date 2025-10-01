"""
Canvas integration API endpoints
Handles Canvas connection, token management, and sync operations
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
import asyncio
from datetime import datetime

from app.core.auth import get_current_user
from app.services.integrations.canvas_token_service import get_canvas_token_service
from app.jobs.canvas.canvas_backfill_job import get_canvas_backfill_job
from app.jobs.canvas.canvas_delta_sync_job import get_canvas_delta_sync_job
from app.middleware.rate_limiting import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API
class CanvasConnectionRequest(BaseModel):
    """Request model for Canvas connection"""
    canvas_url: str = Field(..., description="Canvas base URL (e.g., https://canvas.university.edu)")
    api_token: str = Field(..., description="Canvas API token", min_length=1)

    @validator("canvas_url")
    def validate_canvas_url(cls, v):
        v = v.strip().rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("Canvas URL must start with http:// or https://")
        return v

    @validator("api_token")
    def validate_api_token(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("API token appears to be too short")
        return v


class CanvasConnectionResponse(BaseModel):
    """Response model for Canvas connection"""
    success: bool
    message: str
    user_id: str
    canvas_url: str
    status: str
    stored_at: Optional[str] = None


class CanvasSyncRequest(BaseModel):
    """Request model for Canvas sync operations"""
    sync_type: str = Field("delta", description="Type of sync: 'full' or 'delta'")
    force_restart: bool = Field(False, description="Force restart from beginning")

    @validator("sync_type")
    def validate_sync_type(cls, v):
        if v not in ["full", "delta"]:
            raise ValueError("sync_type must be 'full' or 'delta'")
        return v


class CanvasSyncResponse(BaseModel):
    """Response model for Canvas sync operations"""
    success: bool
    message: str
    sync_id: Optional[str] = None
    status: str


class CanvasDisconnectResponse(BaseModel):
    """Response model for Canvas disconnection"""
    success: bool
    message: str
    user_id: str
    disconnected_at: Optional[str] = None


class CanvasIntegrationStatus(BaseModel):
    """Response model for Canvas integration status"""
    user_id: str
    connected: bool
    canvas_url: Optional[str] = None
    status: str
    last_sync: Optional[str] = None
    last_error: Optional[str] = None
    assignments_count: Optional[int] = None


@router.post("/connect", response_model=CanvasConnectionResponse)
@rate_limit("canvas_connect", max_calls=5, window_seconds=300)  # 5 calls per 5 minutes
async def connect_canvas(
    request: CanvasConnectionRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Connect Canvas integration for the current user

    This endpoint:
    1. Validates the Canvas API token
    2. Stores the token securely using envelope encryption
    3. Sets up the Canvas integration record
    """
    # Support both mapping-like and attribute-like CurrentUser implementations
    # Handle both dict payloads and CurrentUser objects (with user_id attribute)
    if isinstance(current_user, dict):
        user_id = current_user.get("id") or current_user.get("user_id")
    else:
        user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: missing user id")

    try:
        logger.info(f"Canvas connection request for user {user_id}")

        token_service = get_canvas_token_service()

        # First, validate the token by making a test API call
        if not await token_service.validate_token_direct(
            request.canvas_url, request.api_token
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Canvas API token or URL. Please check your credentials."
            )

        # Store the token securely
        result = await token_service.store_canvas_token(
            user_id=user_id,
            canvas_url=request.canvas_url,
            api_token=request.api_token
        )

        # Trigger initial sync after successful connection
        import uuid
        sync_id = str(uuid.uuid4())
        background_tasks.add_task(
            _execute_full_sync_job,
            user_id,
            sync_id,
            False  # force_restart = False
        )

        logger.info(f"Canvas integration connected successfully for user {user_id}, initial sync queued with ID: {sync_id}")

        return CanvasConnectionResponse(
            success=True,
            message="Canvas integration connected successfully. Initial sync has been started.",
            user_id=user_id,
            canvas_url=request.canvas_url,
            status="connected",
            stored_at=result["stored_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Canvas connection failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect Canvas integration: {str(e)}"
        )


@router.delete("/disconnect", response_model=CanvasDisconnectResponse)
@rate_limit("canvas_disconnect", max_calls=5, window_seconds=300)  # 5 calls per 5 minutes
async def disconnect_canvas(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Disconnect Canvas integration for the current user

    This endpoint:
    1. Removes the stored Canvas API token
    2. Clears the integration record
    3. Optionally removes synced Canvas assignments
    """
    # Support both mapping-like and attribute-like CurrentUser implementations
    if isinstance(current_user, dict):
        user_id = current_user.get("id") or current_user.get("user_id")
    else:
        user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: missing user id")

    try:
        logger.info(f"Canvas disconnection request for user {user_id}")

        token_service = get_canvas_token_service()

        # Check if integration exists
        token_data = await token_service.retrieve_canvas_token(user_id)
        if not token_data:
            raise HTTPException(
                status_code=404,
                detail="Canvas integration not found. Nothing to disconnect."
            )

        # Remove the stored token and integration data
        result = await token_service.delete_canvas_integration(user_id)

        # Optionally remove Canvas assignments (commented out for now to preserve user data)
        # await _remove_canvas_assignments(user_id)

        disconnected_at = datetime.utcnow().isoformat()
        logger.info(f"Canvas integration disconnected successfully for user {user_id}")

        return CanvasDisconnectResponse(
            success=True,
            message="Canvas integration disconnected successfully",
            user_id=user_id,
            disconnected_at=disconnected_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Canvas disconnection failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Canvas integration: {str(e)}"
        )


@router.post("/sync", response_model=CanvasSyncResponse)
@rate_limit("canvas_sync", max_calls=10, window_seconds=900)  # 10 calls per 15 minutes
async def sync_canvas(
    request: CanvasSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger Canvas sync operation

    This endpoint:
    1. Validates the user has a Canvas integration
    2. Queues the appropriate sync job (full backfill or delta sync)
    3. Returns immediately with a job ID
    """
    if isinstance(current_user, dict):
        user_id = current_user.get("id") or current_user.get("user_id")
    else:
        user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: missing user id")

    try:
        logger.info(f"Canvas sync request ({request.sync_type}) for user {user_id}")

        # Check if integration exists and is valid
        token_service = get_canvas_token_service()
        token_data = await token_service.retrieve_canvas_token(user_id)

        if not token_data:
            raise HTTPException(
                status_code=404,
                detail="Canvas integration not found. Please connect Canvas first."
            )

        if token_data.get("status") == "needs_reauth":
            raise HTTPException(
                status_code=401,
                detail="Canvas integration needs reauthorization. Please reconnect."
            )

        # Generate sync ID for tracking
        import uuid
        sync_id = str(uuid.uuid4())

        if request.sync_type == "full":
            # Queue full backfill job
            background_tasks.add_task(
                _execute_full_sync_job,
                user_id,
                sync_id,
                request.force_restart
            )
            message = "Full Canvas sync job queued successfully"

        else:  # delta sync
            # Queue delta sync job
            background_tasks.add_task(
                _execute_delta_sync_job,
                user_id,
                sync_id
            )
            message = "Delta Canvas sync job queued successfully"

        logger.info(f"Canvas sync job ({request.sync_type}) queued for user {user_id}, sync_id: {sync_id}")

        return CanvasSyncResponse(
            success=True,
            message=message,
            sync_id=sync_id,
            status="queued"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Canvas sync failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue Canvas sync: {str(e)}"
        )


@router.get("/status", response_model=CanvasIntegrationStatus)
@rate_limit("canvas_status", max_calls=30, window_seconds=60)  # 30 calls per minute
async def get_canvas_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get Canvas integration status for the current user

    Returns:
    - Connection status
    - Last sync information
    - Error status if any
    - Assignment count
    """
    if isinstance(current_user, dict):
        user_id = current_user.get("id") or current_user.get("user_id")
    else:
        user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: missing user id")

    try:
        token_service = get_canvas_token_service()
        token_data = await token_service.retrieve_canvas_token(user_id)

        if not token_data:
            return CanvasIntegrationStatus(
                user_id=user_id,
                connected=False,
                status="not_connected"
            )

        # Get additional integration info
        from app.config.database.supabase import get_supabase
        supabase = get_supabase()

        # Get integration record
        response = supabase.table("integration_canvas").select("*").eq(
            "user_id", user_id
        ).single().execute()

        integration_data = response.data if response.data else {}

        # Get assignment count
        tasks_response = supabase.table("tasks").select("id").eq(
            "user_id", user_id
        ).eq("external_source", "canvas").execute()

        assignments_count = len(tasks_response.data) if tasks_response.data else 0

        return CanvasIntegrationStatus(
            user_id=user_id,
            connected=True,
            canvas_url=token_data.get("base_url"),
            status=integration_data.get("status", "ok"),
            last_sync=integration_data.get("last_full_sync_at") or integration_data.get("last_delta_at"),
            last_error=integration_data.get("last_error_code"),
            assignments_count=assignments_count
        )

    except Exception as e:
        logger.error(f"Error getting Canvas status for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Canvas status: {str(e)}"
        )


@router.delete("/disconnect")
@rate_limit("canvas_disconnect", max_calls=5, window_seconds=300)  # 5 calls per 5 minutes
async def disconnect_canvas(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Disconnect Canvas integration for the current user

    This will:
    1. Delete the Canvas integration record
    2. Remove encrypted tokens
    3. Clean up Canvas-sourced tasks
    4. Clear sync cursors
    """
    user_id = current_user["id"]

    try:
        logger.info(f"Canvas disconnect request for user {user_id}")

        token_service = get_canvas_token_service()
        success = await token_service.delete_canvas_integration(user_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to disconnect Canvas integration"
            )

        logger.info(f"Canvas integration disconnected successfully for user {user_id}")

        return {
            "success": True,
            "message": "Canvas integration disconnected successfully",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Canvas disconnect failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Canvas integration: {str(e)}"
        )


@router.post("/validate-token")
@rate_limit("canvas_validate", max_calls=10, window_seconds=300)  # 10 calls per 5 minutes
async def validate_canvas_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validate the stored Canvas token for the current user

    Returns:
    - Token validity status
    - User info if valid
    - Error details if invalid
    """
    user_id = current_user["id"]

    try:
        logger.info(f"Canvas token validation request for user {user_id}")

        token_service = get_canvas_token_service()
        is_valid = await token_service.validate_token(user_id)

        if is_valid:
            return {
                "valid": True,
                "message": "Canvas token is valid",
                "user_id": user_id
            }
        else:
            return {
                "valid": False,
                "message": "Canvas token is invalid or expired",
                "user_id": user_id
            }

    except Exception as e:
        logger.error(f"Canvas token validation failed for user {user_id}: {e}")
        return {
            "valid": False,
            "message": f"Token validation failed: {str(e)}",
            "user_id": user_id
        }


@router.get("/assignments")
@rate_limit("canvas_assignments", max_calls=20, window_seconds=60)  # 20 calls per minute
async def get_canvas_assignments(
    limit: int = 50,
    include_completed: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get Canvas assignments for the current user

    Args:
    - limit: Maximum number of assignments to return
    - include_completed: Whether to include completed assignments

    Returns:
    - List of Canvas assignments as tasks
    """
    user_id = current_user["id"]

    try:
        from ....config.supabase import get_supabase_client
        supabase = get_supabase_client()

        # Build query
        query = supabase.table("tasks").select("*").eq(
            "user_id", user_id
        ).eq("external_source", "canvas")

        if not include_completed:
            query = query.eq("completed", False)

        query = query.order("due_date", desc=False, nullsfirst=False).limit(limit)

        response = await query.execute()
        assignments = response.data or []

        return {
            "success": True,
            "user_id": user_id,
            "assignments": assignments,
            "count": len(assignments),
            "include_completed": include_completed
        }

    except Exception as e:
        logger.error(f"Error getting Canvas assignments for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Canvas assignments: {str(e)}"
        )


# Background task functions
async def _execute_full_sync_job(user_id: str, sync_id: str, force_restart: bool = False):
    """Execute full Canvas sync job in background"""
    try:
        logger.info(f"Starting full Canvas sync job {sync_id} for user {user_id}")

        backfill_job = get_canvas_backfill_job()
        result = await backfill_job.execute_backfill(user_id, force_restart)

        logger.info(f"Full Canvas sync job {sync_id} completed for user {user_id}: {result['status']}")

        # Emit WebSocket event to notify frontend
        try:
            from app.core.infrastructure.websocket import websocket_manager as ws_manager
            await ws_manager.emit_to_user(
                user_id,
                'canvas_sync',
                {
                    'status': result['status'],
                    'sync_id': sync_id,
                    'assignments_upserted': result.get('assignments_upserted', 0),
                    'courses_processed': result.get('courses_processed', 0),
                    'message': f"Synced {result.get('assignments_upserted', 0)} assignments from {result.get('courses_processed', 0)} courses"
                }
            )
        except Exception as ws_error:
            logger.error(f"Failed to emit WebSocket event for Canvas sync {sync_id}: {ws_error}")

    except Exception as e:
        logger.error(f"Full Canvas sync job {sync_id} failed for user {user_id}: {e}")
        # Emit failure event
        try:
            from app.core.infrastructure.websocket import websocket_manager as ws_manager
            await ws_manager.emit_to_user(
                user_id,
                'canvas_sync',
                {
                    'status': 'error',
                    'sync_id': sync_id,
                    'message': str(e)
                }
            )
        except Exception:
            pass


async def _execute_delta_sync_job(user_id: str, sync_id: str):
    """Execute delta Canvas sync job in background"""
    try:
        logger.info(f"Starting delta Canvas sync job {sync_id} for user {user_id}")

        delta_job = get_canvas_delta_sync_job()
        result = await delta_job.execute_delta_sync(user_id)

        logger.info(f"Delta Canvas sync job {sync_id} completed for user {user_id}: {result['status']}")

        # You could store the result in a jobs table for later retrieval
        # or send a notification to the user

    except Exception as e:
        logger.error(f"Delta Canvas sync job {sync_id} failed for user {user_id}: {e}")