"""
Main Payments Router
Consolidates all payment and subscription endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .revenuecat import router as revenuecat_router
from .subscriptions import router as subscriptions_router

# Create main payments router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(revenuecat_router, prefix="/revenuecat", tags=["revenuecat"])
router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])

