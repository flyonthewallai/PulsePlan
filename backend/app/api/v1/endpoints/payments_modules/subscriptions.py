"""
Subscription status endpoints
Reads subscription data updated by RevenueCat webhooks
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.database.repositories.user_repositories.user_repository import get_user_repository
from app.services.infrastructure.cache_service import get_cache_service

logger = logging.getLogger(__name__)
router = APIRouter()


class SubscriptionResponse(BaseModel):
    """Response model for subscription status"""
    status: str
    apple_transaction_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = False


class SubscriptionService:
    """Service for retrieving subscription status"""
    
    def __init__(self):
        self._user_repository = None
        self._cache_service = None
    
    @property
    def user_repository(self):
        """Lazy-load user repository"""
        if self._user_repository is None:
            self._user_repository = get_user_repository()
        return self._user_repository
    
    @property
    def cache_service(self):
        """Lazy-load cache service"""
        if self._cache_service is None:
            self._cache_service = get_cache_service()
        return self._cache_service
    
    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get current subscription status for user"""
        try:
            # Try cache first
            cached_status = await self.cache_service.get_user_subscription(user_id)
            if cached_status:
                return cached_status
            
            # Query database
            data = await self.user_repository.get_subscription_data(user_id)
            
            if not data:
                return {
                    "status": "free",
                    "apple_transaction_id": None,
                    "expires_at": None,
                    "is_active": False
                }
            
            status = data.get("subscription_status", "free")
            expires_at_str = data.get("subscription_expires_at")
            expires_at = (
                datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                if expires_at_str else None
            )
            
            is_active = (
                status == "premium" and 
                expires_at and 
                expires_at > datetime.utcnow()
            ) if expires_at else status == "premium"
            
            subscription_data = {
                "status": status,
                "apple_transaction_id": data.get("apple_transaction_id"),
                "expires_at": expires_at,
                "is_active": is_active
            }
            
            # Cache result
            await self.cache_service.set_user_subscription(user_id, subscription_data)
            
            return subscription_data
            
        except Exception as e:
            logger.error(f"Failed to get subscription status for user {user_id}: {e}")
            return {
                "status": "free",
                "apple_transaction_id": None,
                "expires_at": None,
                "is_active": False
            }


# Initialize service
subscription_service = SubscriptionService()


@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: dict = Depends(get_current_user)
):
    """Get current subscription status for authenticated user"""
    try:
        user_id = current_user["id"]
        subscription_data = await subscription_service.get_subscription_status(user_id)
        
        return SubscriptionResponse(**subscription_data)
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get subscription status"}
        )


@router.get("/health")
async def subscription_health_check():
    """Health check for subscription service"""
    return {
        "service": "subscription",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

