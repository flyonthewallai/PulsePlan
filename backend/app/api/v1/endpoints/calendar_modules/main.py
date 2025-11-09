"""
Main Calendar Router
Consolidates all calendar-related endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .timeblocks import router as timeblocks_router
from .webhooks import router as webhooks_router

# Create main calendar router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(timeblocks_router, prefix="/timeblocks", tags=["calendar"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

