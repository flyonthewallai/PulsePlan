"""
Usage tracking API endpoints.

Provides endpoints for:
- Querying user token usage
- Getting quota information
- Viewing usage history
- Checking operation costs
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, CurrentUser
from app.services.usage.token_tracker import get_token_tracker, TokenTracker
from app.services.usage.usage_limiter import get_usage_limiter, UsageLimiter
from app.services.usage.usage_config import OperationType

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics"""

    user_id: str
    period: str
    total_tokens_used: int
    monthly_limit: int
    tokens_remaining: int
    quota_percentage: float
    quota_status: str
    subscription_tier: str
    operation_breakdown: dict
    last_reset_at: str


class QuotaSummaryResponse(BaseModel):
    """Response model for quota summary"""

    user_id: str
    subscription_tier: str
    monthly: dict
    daily: dict
    operation_breakdown: dict
    last_reset_at: str
    warnings: list[str]


class OperationCostEstimate(BaseModel):
    """Response model for operation cost estimate"""

    operation_type: str
    model: str
    estimated_total_tokens: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float


class QuotaCheckRequest(BaseModel):
    """Request model for quota check"""

    operation_type: str = Field(..., description="Operation type to check")
    custom_token_estimate: Optional[int] = Field(
        None, description="Optional custom token estimate"
    )


class QuotaCheckResponse(BaseModel):
    """Response model for quota check"""

    allowed: bool
    reason: Optional[str]
    tokens_remaining: int
    tokens_needed: int
    subscription_tier: str
    requires_upgrade: bool
    quota_status: str


class UsageTrendsResponse(BaseModel):
    """Response model for usage trends"""

    user_id: str
    days_analyzed: int
    daily_average: float
    total_usage: int
    trend: str
    usage_history: list[dict]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    period: str = Query("month", regex="^(day|month|all)$"),
    current_user: CurrentUser = Depends(get_current_user),
    tracker: TokenTracker = Depends(get_token_tracker),
):
    """
    Get usage statistics for the current user.

    - **period**: 'day', 'month', or 'all'
    """
    try:
        stats = await tracker.get_usage_stats(current_user.id, period)
        return UsageStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage statistics")


@router.get("/quota", response_model=QuotaSummaryResponse)
async def get_quota_summary(
    current_user: CurrentUser = Depends(get_current_user),
    limiter: UsageLimiter = Depends(get_usage_limiter),
):
    """
    Get comprehensive quota summary for the current user.

    Includes monthly and daily limits, current usage, and warnings.
    """
    try:
        summary = await limiter.get_quota_summary(current_user.id)
        return QuotaSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error fetching quota summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quota summary")


@router.post("/check", response_model=QuotaCheckResponse)
async def check_quota(
    request: QuotaCheckRequest,
    current_user: CurrentUser = Depends(get_current_user),
    limiter: UsageLimiter = Depends(get_usage_limiter),
):
    """
    Check if user has quota for a specific operation.

    Returns whether the operation is allowed and quota details.
    """
    try:
        # Validate operation type
        try:
            operation_type = OperationType(request.operation_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid operation type: {request.operation_type}"
            )

        result = await limiter.check_operation_allowed(
            current_user.id, operation_type, request.custom_token_estimate
        )

        return QuotaCheckResponse(
            allowed=result.allowed,
            reason=result.reason,
            tokens_remaining=result.tokens_remaining,
            tokens_needed=result.tokens_needed,
            subscription_tier=result.subscription_tier,
            requires_upgrade=result.requires_upgrade,
            quota_status=result.quota_status,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking quota: {e}")
        raise HTTPException(status_code=500, detail="Failed to check quota")


@router.get("/estimate/{operation_type}", response_model=OperationCostEstimate)
async def estimate_operation_cost(
    operation_type: str,
    model: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    tracker: TokenTracker = Depends(get_token_tracker),
):
    """
    Get estimated token cost for an operation.

    - **operation_type**: Type of operation (from OperationType enum)
    - **model**: Optional model name (uses default if not provided)
    """
    try:
        # Validate operation type
        try:
            op_type = OperationType(operation_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid operation type: {operation_type}"
            )

        estimate = await tracker.estimate_operation_cost(op_type, model)
        return OperationCostEstimate(**estimate)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating operation cost: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to estimate operation cost"
        )


@router.get("/trends", response_model=UsageTrendsResponse)
async def get_usage_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    current_user: CurrentUser = Depends(get_current_user),
    tracker: TokenTracker = Depends(get_token_tracker),
):
    """
    Get usage trends over time.

    - **days**: Number of days to analyze (1-90)
    """
    try:
        trends = await tracker.get_usage_trends(current_user.id, days)
        return UsageTrendsResponse(**trends)
    except Exception as e:
        logger.error(f"Error fetching usage trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage trends")


@router.get("/history")
async def get_usage_history(
    days: int = Query(30, ge=1, le=90, description="Number of days of history"),
    current_user: CurrentUser = Depends(get_current_user),
    tracker: TokenTracker = Depends(get_token_tracker),
):
    """
    Get detailed usage history.

    - **days**: Number of days of history (1-90)
    """
    try:
        from app.database.repositories.integration_repositories import get_usage_repository

        usage_repo = get_usage_repository()
        history = await usage_repo.get_recent_usage_history(current_user.id, days)

        return {
            "user_id": str(current_user.id),
            "days": days,
            "history": history,
        }
    except Exception as e:
        logger.error(f"Error fetching usage history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage history")
