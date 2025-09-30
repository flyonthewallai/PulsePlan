"""
Main Tasks Router
Consolidates all task management endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .tasks import router as tasks_router
from .todos import router as todos_router
from .tags import router as tags_router

# Create main tasks router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(todos_router, prefix="/todos", tags=["todos"])
router.include_router(tags_router, prefix="/tags", tags=["tags"])