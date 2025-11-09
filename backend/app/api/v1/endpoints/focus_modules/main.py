"""
Main Focus Router
Consolidates all focus/Pomodoro-related endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .pomodoro import router as pomodoro_router
from .sessions import router as sessions_router
from .entity_matching import router as entity_matching_router

# Create main focus router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(pomodoro_router, prefix="/pomodoro", tags=["pomodoro"])
router.include_router(sessions_router, prefix="/sessions", tags=["focus-sessions"])
router.include_router(entity_matching_router, prefix="/entity-matching", tags=["entity-matching"])

