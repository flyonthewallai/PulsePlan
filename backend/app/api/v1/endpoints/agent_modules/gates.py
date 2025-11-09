"""
Gates API Endpoints

Provides confirmation/cancellation endpoints for pending gates.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from app.services.gate_service import GateService, get_gate_service
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class GateConfirmRequest(BaseModel):
    """Request to confirm a pending gate."""
    user_id: UUID = Field(..., description="User ID for authorization")
    modifications: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional modifications to parameters before execution"
    )


class GateCancelRequest(BaseModel):
    """Request to cancel a pending gate."""
    user_id: UUID = Field(..., description="User ID for authorization")
    reason: Optional[str] = Field(None, description="Cancellation reason")


class GateResponse(BaseModel):
    """Response for gate operations."""
    gate_token: str
    action_id: UUID
    status: str  # confirmed, cancelled, expired
    message: str
    execution_result: Optional[Dict[str, Any]] = None


class GateStatusResponse(BaseModel):
    """Response for gate status check."""
    gate_token: str
    action_id: UUID
    status: str  # pending, confirmed, cancelled, expired
    intent: str
    required_confirmations: Dict[str, Any]
    policy_reasons: list
    created_at: datetime
    expires_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


@router.post("/{token}/confirm", response_model=GateResponse)
async def confirm_gate(
    token: str,
    request: GateConfirmRequest,
    service: GateService = Depends(get_gate_service)
) -> GateResponse:
    """
    Confirm a pending gate and execute the action.

    This endpoint:
    1. Validates the gate token and checks expiration
    2. Verifies user authorization
    3. Applies any modifications to parameters
    4. Marks gate as confirmed
    5. Resumes workflow execution
    6. Returns execution result

    Args:
        token: Gate token from pending_gates table
        request: Confirmation request with user_id and optional modifications
        service: GateService instance

    Returns:
        GateResponse with execution result

    Raises:
        HTTPException: 404 if gate not found, 403 if unauthorized, 410 if expired
    """
    try:
        result = await service.confirm_gate(
            token=token,
            user_id=request.user_id,
            modifications=request.modifications
        )
        return GateResponse(**result)
    
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            status_code = status.HTTP_404_NOT_FOUND
        elif "not authorized" in error_msg or "unauthorized" in error_msg:
            status_code = status.HTTP_403_FORBIDDEN
        elif "expired" in error_msg:
            status_code = status.HTTP_410_GONE
        elif "already" in error_msg or "cancelled" in error_msg:
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "confirm_gate")


@router.post("/{token}/cancel", response_model=GateResponse)
async def cancel_gate(
    token: str,
    request: GateCancelRequest,
    service: GateService = Depends(get_gate_service)
) -> GateResponse:
    """
    Cancel a pending gate.

    This endpoint:
    1. Validates the gate token
    2. Verifies user authorization
    3. Marks gate as cancelled
    4. Updates action status to failed/cancelled
    5. Cleans up any partial execution

    Args:
        token: Gate token from pending_gates table
        request: Cancellation request with user_id and optional reason
        service: GateService instance

    Returns:
        GateResponse confirming cancellation

    Raises:
        HTTPException: 404 if gate not found, 403 if unauthorized
    """
    try:
        result = await service.cancel_gate(
            token=token,
            user_id=request.user_id,
            reason=request.reason
        )
        return GateResponse(**result)
    
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            status_code = status.HTTP_404_NOT_FOUND
        elif "not authorized" in error_msg or "unauthorized" in error_msg:
            status_code = status.HTTP_403_FORBIDDEN
        elif "already" in error_msg:
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "cancel_gate")


@router.get("/{token}", response_model=GateStatusResponse)
async def get_gate_status(
    token: str,
    user_id: UUID,
    service: GateService = Depends(get_gate_service)
) -> GateStatusResponse:
    """
    Get status of a pending gate.

    Args:
        token: Gate token
        user_id: User ID for authorization
        service: GateService instance

    Returns:
        GateStatusResponse with full gate details

    Raises:
        HTTPException: 404 if gate not found, 403 if unauthorized
    """
    try:
        result = await service.get_gate_status(token=token, user_id=user_id)
        return GateStatusResponse(**result)
    
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            status_code = status.HTTP_404_NOT_FOUND
        elif "not authorized" in error_msg or "unauthorized" in error_msg:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_gate_status")


@router.get("/action/{action_id}/trace", response_model=Dict[str, Any])
async def get_action_trace(
    action_id: UUID,
    user_id: UUID,
    service: GateService = Depends(get_gate_service)
) -> Dict[str, Any]:
    """
    Get ordered execution trace for an action.

    Returns chronological sequence: ingest → nlu → plan → propose → gate → execute.

    Args:
        action_id: Action record ID
        user_id: User ID for authorization
        service: GateService instance

    Returns:
        Dict with action details and ordered trace steps

    Raises:
        HTTPException: 404 if action not found, 403 if unauthorized
    """
    try:
        result = await service.get_action_trace(action_id=action_id, user_id=user_id)
        return result
    
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            status_code = status.HTTP_404_NOT_FOUND
        elif "not authorized" in error_msg or "unauthorized" in error_msg:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_action_trace")

