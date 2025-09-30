"""
Token Refresh API endpoints
Provides management and monitoring for the token refresh service
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user, CurrentUser
from app.services.auth.token_refresh import TokenRefreshService, TokenProvider

# Initialize service
token_refresh_service = TokenRefreshService()


router = APIRouter()


class ForceRefreshRequest(BaseModel):
    provider: Optional[str] = None


class RefreshMetricsResponse(BaseModel):
    total_attempts: int
    success_rate: float
    attempts_by_provider: Dict[str, Dict[str, int]]
    attempts_by_result: Dict[str, int]
    background_task_running: bool


class TokenHealthResponse(BaseModel):
    user_id: str
    total_tokens: int
    tokens_by_provider: Dict[str, int]
    expiring_soon: list
    expired: list
    missing_refresh_token: list


@router.get("/health", response_model=TokenHealthResponse)
async def get_user_token_health(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get health status of current user's OAuth tokens
    """
    try:
        health_data = await token_refresh_service.get_token_health(current_user.user_id)
        return TokenHealthResponse(**health_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get token health: {str(e)}"
        )


@router.post("/force-refresh")
async def force_refresh_user_tokens(
    request: ForceRefreshRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Force refresh all tokens for the current user
    """
    try:
        provider = None
        if request.provider:
            try:
                provider = TokenProvider(request.provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: {request.provider}"
                )
        
        attempts = await token_refresh_service.force_refresh_user_tokens(
            current_user.user_id,
            provider
        )
        
        success_count = sum(1 for a in attempts if a.result.value == "success")
        
        return {
            "message": f"Refresh completed for {len(attempts)} tokens",
            "successful_refreshes": success_count,
            "total_attempts": len(attempts),
            "attempts": [
                {
                    "provider": a.provider.value,
                    "result": a.result.value,
                    "error": a.error,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in attempts
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force refresh tokens: {str(e)}"
        )


@router.get("/metrics", response_model=RefreshMetricsResponse)
async def get_refresh_metrics(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get token refresh service metrics (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        metrics = token_refresh_service.get_refresh_metrics()
        return RefreshMetricsResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get refresh metrics: {str(e)}"
        )


@router.post("/start-background")
async def start_background_refresh(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Start background token refresh service (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        await token_refresh_service.start_background_refresh()
        return {"message": "Background token refresh service started"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start background refresh: {str(e)}"
        )


@router.post("/stop-background")
async def stop_background_refresh(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Stop background token refresh service (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        await token_refresh_service.stop_background_refresh()
        return {"message": "Background token refresh service stopped"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop background refresh: {str(e)}"
        )


@router.get("/service-status")
async def get_service_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current status of the token refresh service (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    metrics = token_refresh_service.get_refresh_metrics()
    
    return {
        "background_task_running": metrics["background_task_running"],
        "recent_activity": {
            "total_attempts": metrics["total_attempts"],
            "success_rate": metrics["success_rate"],
            "attempts_by_result": metrics["attempts_by_result"]
        },
        "configuration": {
            "refresh_margin_minutes": token_refresh_service.refresh_margin_minutes,
            "max_retry_attempts": token_refresh_service.max_retry_attempts,
            "batch_size": token_refresh_service.batch_size
        }
    }