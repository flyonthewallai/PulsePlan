"""
Main Integrations Router
Consolidates all external service integration endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .canvas import router as canvas_router
from .calendar import router as calendar_router
from .email import router as email_router

# Create main integrations router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(canvas_router, prefix="/canvas", tags=["canvas"])
router.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
router.include_router(email_router, prefix="/email", tags=["email"])