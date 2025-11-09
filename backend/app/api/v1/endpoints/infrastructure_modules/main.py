"""
Main Infrastructure Router
Consolidates all system infrastructure endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .health import router as health_router
from .rate_limiting import router as rate_limiting_router
from .usage import router as usage_router

# Create main infrastructure router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(rate_limiting_router, prefix="/rate-limiting", tags=["rate-limiting"])
router.include_router(usage_router, prefix="/usage", tags=["usage"])