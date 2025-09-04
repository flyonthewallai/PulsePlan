"""
Subscription and Apple Pay integration endpoints
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import httpx

from ...core.auth import get_current_user
from ...config.supabase import get_supabase_client
from ...services.cache_service import get_cache_service
from ...config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ApplePayReceiptRequest(BaseModel):
    """Request model for Apple Pay receipt verification"""
    receipt_data: str = Field(..., description="Base64 encoded receipt data")
    is_production: bool = Field(False, description="Whether to use production endpoint")


class SubscriptionUpdateRequest(BaseModel):
    """Request model for subscription updates"""
    apple_transaction_id: str = Field(..., description="Apple transaction ID")
    subscription_status: str = Field(..., description="Subscription status")
    expires_at: Optional[datetime] = Field(None, description="Expiration datetime")


class SubscriptionResponse(BaseModel):
    """Response model for subscription status"""
    status: str
    apple_transaction_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = False


class ApplePayService:
    """Service for handling Apple Pay subscription operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.cache_service = get_cache_service()
    
    async def verify_receipt(
        self, 
        receipt_data: str, 
        is_production: bool = False
    ) -> Dict[str, Any]:
        """Verify Apple Pay receipt with Apple servers"""
        
        # Apple's receipt verification endpoints
        verification_url = (
            "https://buy.itunes.apple.com/verifyReceipt" if is_production
            else "https://sandbox.itunes.apple.com/verifyReceipt"
        )
        
        payload = {
            "receipt-data": receipt_data,
            "password": self.settings.APPLE_SHARED_SECRET,
            "exclude-old-transactions": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    verification_url,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                apple_response = response.json()
            
            if apple_response.get("status") != 0:
                logger.error(f"Apple receipt verification failed: {apple_response}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid receipt",
                        "apple_status": apple_response.get("status")
                    }
                )
            
            # Extract subscription info
            latest_receipt_info = apple_response.get("latest_receipt_info")
            if not latest_receipt_info:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "No subscription found in receipt"}
                )
            
            # Get the most recent transaction
            latest_transaction = latest_receipt_info[0]
            
            expires_date = datetime.fromtimestamp(
                int(latest_transaction["expires_date_ms"]) / 1000
            )
            is_active = expires_date > datetime.utcnow()
            transaction_id = latest_transaction["transaction_id"]
            
            return {
                "transaction_id": transaction_id,
                "expires_at": expires_date,
                "is_active": is_active,
                "status": "premium" if is_active else "free"
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Apple receipt verification: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to verify receipt with Apple"}
            )
        except Exception as e:
            logger.error(f"Unexpected error during Apple receipt verification: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Receipt verification failed"}
            )
    
    async def update_user_subscription(
        self,
        user_id: str,
        transaction_id: str,
        status: str,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Update user subscription in database"""
        try:
            update_data = {
                "subscription_status": status,
                "apple_transaction_id": transaction_id,
                "subscription_updated_at": datetime.utcnow().isoformat()
            }
            
            if expires_at:
                update_data["subscription_expires_at"] = expires_at.isoformat()
            
            response = await self.supabase.table("users").update(
                update_data
            ).eq("id", user_id).execute()
            
            if response.data:
                # Invalidate user cache
                await self.cache_service.invalidate_user_data(user_id)
                logger.info(f"Updated subscription for user {user_id}: {status}")
                return True
            else:
                logger.error(f"Failed to update subscription for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Database error updating subscription for user {user_id}: {e}")
            return False
    
    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get current subscription status for user"""
        try:
            # Try cache first
            cached_status = await self.cache_service.get_user_subscription(user_id)
            if cached_status:
                return cached_status
            
            # Query database
            response = await self.supabase.table("users").select(
                "subscription_status, apple_transaction_id, subscription_expires_at"
            ).eq("id", user_id).single().execute()
            
            if not response.data:
                return {
                    "status": "free",
                    "apple_transaction_id": None,
                    "expires_at": None,
                    "is_active": False
                }
            
            data = response.data
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
apple_pay_service = ApplePayService()


@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: dict = Depends(get_current_user)
):
    """Get current subscription status for authenticated user"""
    try:
        user_id = current_user["id"]
        subscription_data = await apple_pay_service.get_subscription_status(user_id)
        
        return SubscriptionResponse(**subscription_data)
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get subscription status"}
        )


@router.post("/apple-pay/verify-receipt")
async def verify_apple_pay_receipt(
    request: ApplePayReceiptRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Verify Apple Pay receipt and update user subscription"""
    try:
        user_id = current_user["id"]
        
        # Verify receipt with Apple
        verification_result = await apple_pay_service.verify_receipt(
            request.receipt_data, 
            request.is_production
        )
        
        # Update user subscription in background
        background_tasks.add_task(
            apple_pay_service.update_user_subscription,
            user_id,
            verification_result["transaction_id"],
            verification_result["status"],
            verification_result["expires_at"]
        )
        
        return {
            "success": True,
            "subscription": {
                "status": verification_result["status"],
                "transaction_id": verification_result["transaction_id"],
                "expires_at": verification_result["expires_at"].isoformat(),
                "is_active": verification_result["is_active"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying Apple Pay receipt: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to verify receipt"}
        )


@router.post("/update")
async def update_subscription(
    request: SubscriptionUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update subscription status from Apple Pay transaction"""
    try:
        user_id = current_user["id"]
        
        success = await apple_pay_service.update_user_subscription(
            user_id,
            request.apple_transaction_id,
            request.subscription_status,
            request.expires_at
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to update subscription"}
            )
        
        return {
            "success": True,
            "message": "Subscription updated successfully",
            "status": request.subscription_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update subscription"}
        )


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user)
):
    """Cancel user subscription"""
    try:
        user_id = current_user["id"]
        
        success = await apple_pay_service.update_user_subscription(
            user_id,
            "",  # Clear transaction ID
            "free"
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to cancel subscription"}
            )
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to cancel subscription"}
        )


@router.get("/health")
async def subscription_health_check():
    """Health check for subscription service"""
    return {
        "service": "subscription",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }