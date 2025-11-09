"""
RevenueCat webhook handler
Processes subscription events from RevenueCat
"""
import logging
import secrets
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from app.database.repositories.user_repositories.user_repository import get_user_repository
from app.services.infrastructure.cache_service import get_cache_service
from app.config.core.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class RevenueCatWebhookEvent(BaseModel):
    """RevenueCat webhook event model"""
    event: Dict[str, Any] = Field(..., description="The webhook event data")


@router.post("/webhook")
async def revenuecat_webhook(
    request: Request,
    authorization: str = Header(None)
):
    """
    Handle RevenueCat webhook events
    
    RevenueCat sends events for:
    - INITIAL_PURCHASE
    - RENEWAL
    - CANCELLATION
    - NON_RENEWING_PURCHASE
    - EXPIRATION
    - BILLING_ISSUE
    - PRODUCT_CHANGE
    - SUBSCRIBER_ALIAS
    - SUBSCRIPTION_EXTENDED
    - SUBSCRIPTION_PAUSED
    """
    settings = get_settings()
    
    # Check if webhook secret is configured
    if not settings.REVENUECAT_WEBHOOK_SECRET:
        logger.error("RevenueCat webhook secret not configured")
        raise HTTPException(status_code=503, detail="RevenueCat webhook not configured")
    
    # Verify webhook authorization using constant-time comparison to prevent timing attacks
    # RevenueCat sends Authorization header with webhook secret
    expected_auth = f"Bearer {settings.REVENUECAT_WEBHOOK_SECRET}"
    if not authorization or not secrets.compare_digest(authorization, expected_auth):
        logger.warning("Unauthorized RevenueCat webhook attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Parse webhook payload
        payload = await request.json()
        event = payload.get("event", {})
        event_type = event.get("type")
        
        logger.info(f"Received RevenueCat webhook event: {event_type}")
        
        # Extract subscriber info
        app_user_id = event.get("app_user_id")
        if not app_user_id:
            logger.error("No app_user_id in RevenueCat webhook")
            return {"received": True}
        
        # Get subscription info
        subscriber = event.get("subscriber", {})
        entitlements = subscriber.get("entitlements", {})
        
        # Determine subscription status
        has_premium = False
        expires_at = None
        transaction_id = None
        
        # Check for premium entitlement
        premium_entitlement = entitlements.get("premium") or entitlements.get("pro")
        if premium_entitlement:
            has_premium = premium_entitlement.get("expires_date") is not None
            expires_date_ms = premium_entitlement.get("expires_date")
            transaction_id = premium_entitlement.get("original_transaction_id")
            
            if expires_date_ms:
                # RevenueCat sends timestamps in milliseconds
                expires_at = datetime.fromtimestamp(int(expires_date_ms) / 1000)
                has_premium = expires_at > datetime.utcnow()
        
        # Map event type to subscription status
        subscription_status = "premium" if has_premium else "free"
        
        # Update user subscription in database
        user_repository = get_user_repository()
        cache_service = get_cache_service()
        
        update_data = {
            "subscription_status": subscription_status,
            "subscription_updated_at": datetime.utcnow().isoformat()
        }
        
        if transaction_id:
            update_data["apple_transaction_id"] = transaction_id
        
        if expires_at:
            update_data["subscription_expires_at"] = expires_at.isoformat()
        
        success = await user_repository.update_subscription(
            user_id=app_user_id,
            subscription_data=update_data
        )
        
        if success:
            # Invalidate cache
            await cache_service.invalidate_user_data(app_user_id)
            logger.info(
                f"Updated subscription for user {app_user_id}: "
                f"{subscription_status} (event: {event_type})"
            )
        else:
            logger.error(f"Failed to update subscription for user {app_user_id}")
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Error processing RevenueCat webhook: {e}", exc_info=True)
        # Return 200 to prevent RevenueCat from retrying
        # We've logged the error for investigation
        return {"received": True, "error": str(e)}


@router.get("/health")
async def revenuecat_health_check():
    """Health check for RevenueCat webhook service"""
    return {
        "service": "revenuecat-webhook",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

