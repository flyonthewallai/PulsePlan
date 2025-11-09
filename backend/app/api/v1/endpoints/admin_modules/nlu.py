"""
Admin NLU Monitoring API

Endpoints for NLU model performance monitoring, manual corrections, and retraining workflow.
Separate from PostHog product analytics - this is pure ML ops tooling.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID

from app.core.auth import get_current_user
from app.services.nlu_monitoring_service import NLUMonitoringService, get_nlu_monitoring_service
from app.core.utils.error_handlers import handle_endpoint_error
import logging

logger = logging.getLogger(__name__)

router = APIRouter()  # Prefix is set in admin_modules/__init__.py


# ============================================================================
# Request/Response Models
# ============================================================================

class NLUStatsResponse(BaseModel):
    """NLU statistics for monitoring."""
    total_prompts: int
    total_prompts_today: int
    total_prompts_week: int
    avg_confidence: float
    avg_confidence_today: float
    low_confidence_count: int  # < 0.7
    failed_workflows: int
    correction_count: int
    intent_distribution: List[Dict[str, Any]]
    confidence_distribution: List[Dict[str, int]]
    workflow_success_rate: Dict[str, Any]


class PromptLogResponse(BaseModel):
    """Prompt log entry."""
    id: str
    user_id: str
    prompt: str
    predicted_intent: str
    confidence: float
    secondary_intents: Optional[List[Dict[str, Any]]] = None
    corrected_intent: Optional[str] = None
    correction_notes: Optional[str] = None
    was_successful: Optional[bool] = None
    workflow_type: Optional[str] = None
    execution_error: Optional[str] = None
    created_at: datetime


class AddCorrectionRequest(BaseModel):
    """Request to add manual correction."""
    log_id: UUID
    corrected_intent: str
    correction_notes: Optional[str] = None


class ExportDataRequest(BaseModel):
    """Request to export training data."""
    days: Optional[int] = 30
    mode: str = Field("retraining", description="Export mode: 'retraining' or 'review'")


# ============================================================================
# Admin Auth Dependency
# ============================================================================

async def verify_admin(
    current_user: dict = Depends(get_current_user),
    service: NLUMonitoringService = Depends(get_nlu_monitoring_service)
) -> dict:
    """
    Verify user is admin.

    Checks the 'role' field in public.users table.
    """
    user_id = current_user.get("id")

    is_admin = await service.verify_admin(user_id)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/stats", response_model=NLUStatsResponse)
async def get_nlu_stats(
    days: int = Query(7, description="Number of days to analyze"),
    admin: dict = Depends(verify_admin),
    service: NLUMonitoringService = Depends(get_nlu_monitoring_service)
):
    """
    Get NLU performance statistics.

    Returns:
        - Total prompts (all time, today, last N days)
        - Average confidence scores
        - Low confidence count
        - Failed workflow count
        - Intent distribution
        - Confidence distribution
        - Workflow success rates
    """
    try:
        stats = await service.get_nlu_stats(days=days)
        return NLUStatsResponse(**stats)
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_nlu_stats")


@router.get("/low-confidence", response_model=List[PromptLogResponse])
async def get_low_confidence_prompts(
    threshold: float = Query(0.7, description="Confidence threshold"),
    limit: int = Query(100, description="Max results"),
    admin: dict = Depends(verify_admin),
    service: NLUMonitoringService = Depends(get_nlu_monitoring_service)
):
    """Get prompts with low confidence for manual review."""
    try:
        prompts = await service.get_low_confidence_prompts(
            threshold=threshold,
            limit=limit
        )
        return [PromptLogResponse(**p) for p in prompts]
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_low_confidence_prompts")


@router.get("/failed-workflows", response_model=List[PromptLogResponse])
async def get_failed_workflows(
    limit: int = Query(100, description="Max results"),
    admin: dict = Depends(verify_admin),
    service: NLUMonitoringService = Depends(get_nlu_monitoring_service)
):
    """Get prompts that led to failed workflows."""
    try:
        prompts = await service.get_failed_workflows(limit=limit)
        return [PromptLogResponse(**p) for p in prompts]
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_failed_workflows")


@router.post("/correct-intent")
async def add_correction(
    request: AddCorrectionRequest,
    admin: dict = Depends(verify_admin),
    service: NLUMonitoringService = Depends(get_nlu_monitoring_service)
):
    """Add manual correction to a prompt log."""
    try:
        result = await service.add_correction(
            log_id=request.log_id,
            corrected_intent=request.corrected_intent,
            correction_notes=request.correction_notes
        )
        return result
    except Exception as e:
        return handle_endpoint_error(e, logger, "add_correction")


@router.post("/export-training-data")
async def export_training_data(
    request: ExportDataRequest,
    admin: dict = Depends(verify_admin),
    service: NLUMonitoringService = Depends(get_nlu_monitoring_service)
):
    """
    Trigger export of training data.

    NOTE: This returns the data directly. In production, you might want to:
    - Queue a background job
    - Generate a downloadable file
    - Email the export link
    """
    try:
        result = await service.export_training_data(
            mode=request.mode,
            days=request.days
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return handle_endpoint_error(e, logger, "export_training_data")
