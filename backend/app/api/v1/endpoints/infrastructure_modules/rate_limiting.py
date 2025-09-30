"""
Rate Limiting API endpoints
Provides management and monitoring for hierarchical rate limiting
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user, CurrentUser
from app.services.infrastructure.rate_limiting import hierarchical_rate_limiter, RateLimitLevel, RateLimitScope


router = APIRouter()


class CustomLimitRequest(BaseModel):
    identifier: str
    level: str  # user, provider, workflow
    scope: str  # minute, hour, day
    limit: int


class ResetLimitsRequest(BaseModel):
    user_id: Optional[str] = None


@router.get("/status")
async def get_user_rate_limit_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current rate limit status for the authenticated user
    """
    try:
        user_limits = await hierarchical_rate_limiter.get_user_limits(current_user.user_id)
        return user_limits
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )


@router.get("/global-metrics")
async def get_global_rate_limit_metrics(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get global rate limiting metrics (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        metrics = await hierarchical_rate_limiter.get_global_metrics()
        return {
            "global_metrics": metrics,
            "service_info": {
                "enabled": hierarchical_rate_limiter.redis_client is not None,
                "default_limits": {
                    level.value: {
                        scope.value: {
                            "limit": limit_config.limit,
                            "window_seconds": limit_config.window_seconds
                        }
                        for scope, limit_config in limits.items()
                    }
                    for level, limits in hierarchical_rate_limiter.default_limits.items()
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get global metrics: {str(e)}"
        )


@router.post("/custom-limit")
async def set_custom_rate_limit(
    request: CustomLimitRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Set custom rate limit for specific identifier (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Validate level and scope
        try:
            level = RateLimitLevel(request.level.lower())
            scope = RateLimitScope(request.scope.lower())
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid level or scope: {str(e)}"
            )
        
        if request.limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be greater than 0"
            )
        
        # Set custom limit
        hierarchical_rate_limiter.set_custom_limit(
            identifier=request.identifier,
            level=level,
            scope=scope,
            limit=request.limit
        )
        
        return {
            "message": f"Custom rate limit set for {request.identifier}",
            "identifier": request.identifier,
            "level": level.value,
            "scope": scope.value,
            "limit": request.limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set custom rate limit: {str(e)}"
        )


@router.post("/reset")
async def reset_rate_limits(
    request: ResetLimitsRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Reset rate limits for a user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        user_id = request.user_id or current_user.user_id
        
        await hierarchical_rate_limiter.reset_user_limits(user_id)
        
        return {
            "message": f"Rate limits reset for user {user_id}",
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limits: {str(e)}"
        )


@router.get("/check")
async def check_rate_limits(
    provider: Optional[str] = None,
    workflow_type: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Check current rate limit status for specific provider/workflow
    """
    try:
        rate_limit_status = await hierarchical_rate_limiter.check_rate_limits(
            user_id=current_user.user_id,
            provider=provider,
            workflow_type=workflow_type
        )
        
        return {
            "user_id": current_user.user_id,
            "provider": provider,
            "workflow_type": workflow_type,
            "allowed": rate_limit_status.allowed,
            "violations": [
                {
                    "level": v.level.value,
                    "identifier": v.identifier,
                    "limit": v.limit,
                    "current_count": v.current_count,
                    "window_seconds": v.window_seconds,
                    "reset_time": v.reset_time.isoformat(),
                    "violation_time": v.violation_time.isoformat()
                }
                for v in rate_limit_status.violations
            ],
            "current_limits": rate_limit_status.current_limits,
            "reset_times": {
                k: v.isoformat() for k, v in rate_limit_status.reset_times.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check rate limits: {str(e)}"
        )


@router.get("/configuration")
async def get_rate_limit_configuration(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current rate limit configuration (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "default_limits": {
            level.value: {
                scope.value: {
                    "limit": limit_config.limit,
                    "window_seconds": limit_config.window_seconds,
                    "scope": limit_config.scope.value,
                    "level": limit_config.level.value
                }
                for scope, limit_config in limits.items()
            }
            for level, limits in hierarchical_rate_limiter.default_limits.items()
        },
        "custom_limits": {
            identifier: {
                scope.value: {
                    "limit": limit_config.limit,
                    "window_seconds": limit_config.window_seconds,
                    "scope": limit_config.scope.value,
                    "level": limit_config.level.value
                }
                for scope, limit_config in limits.items()
            }
            for identifier, limits in hierarchical_rate_limiter.custom_limits.items()
        },
        "settings": {
            "enabled": True,  # Always true if this endpoint is accessible
            "redis_connected": hierarchical_rate_limiter.redis_client is not None
        }
    }