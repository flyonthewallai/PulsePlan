"""
Task management API endpoints.
Handles CRUD operations for tasks (assignments, quizzes, exams) with tag support.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.core.auth import get_current_user, CurrentUser
from app.database.models import TaskModel, TaskPriority, TaskStatus
from app.services.task_service import TaskService, get_task_service
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)

router = APIRouter()


class TaskCreateRequest(BaseModel):
    """Request model for creating tasks"""
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    task_type: str = Field("assignment", description="Task type (assignment, quiz, exam)")
    course: Optional[str] = Field(None, description="Course name")
    priority: Optional[TaskPriority] = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    estimated_minutes: Optional[int] = Field(None, description="Estimated duration")


class TaskUpdateRequest(BaseModel):
    """Request model for updating tasks"""
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    task_type: Optional[str] = Field(None, description="Task type")
    course: Optional[str] = Field(None, description="Course name")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    completed_at: Optional[str] = Field(None, description="Completion timestamp (ISO format)")
    estimated_minutes: Optional[int] = Field(None, description="Estimated duration")


class TaskFilters(BaseModel):
    """Filters for listing tasks"""
    status: Optional[TaskStatus] = Field(None, description="Filter by status")
    task_type: Optional[str] = Field(None, description="Filter by task type")
    priority: Optional[TaskPriority] = Field(None, description="Filter by priority")
    course: Optional[str] = Field(None, description="Filter by course")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    start_date: Optional[str] = Field(None, description="Filter by start date")
    end_date: Optional[str] = Field(None, description="Filter by end date")


@router.post("/", response_model=Dict[str, Any])
async def create_task(
    request: TaskCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """Create a new task"""
    try:
        task_data = {
            "title": request.title,
            "description": request.description,
            "task_type": request.task_type,
            "course": request.course,
            "priority": request.priority.value if request.priority else "medium",
            "due_date": request.due_date,
            "tags": request.tags or [],
            "estimated_minutes": request.estimated_minutes
        }
        
        task = await service.create_task(current_user.user_id, task_data)
        return {"data": {"task": task}, "error": None}
            
    except Exception as e:
        return handle_endpoint_error(e, logger, "create_task")


@router.get("/", response_model=Dict[str, Any])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    course: Optional[str] = Query(None, description="Filter by course"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """List tasks with optional filters"""
    try:
        filters = {}
        if status:
            filters["status"] = status.value
        if task_type:
            filters["task_type"] = task_type
        if priority:
            filters["priority"] = priority.value
        if course:
            filters["course"] = course
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        
        result = await service.list_tasks(current_user.user_id, filters)
        
        # Return in format expected by frontend: {tasks: Task[], count: number}
        return {"tasks": result["tasks"], "count": result["total"]}
            
    except Exception as e:
        return handle_endpoint_error(e, logger, "list_tasks")


@router.patch("/{task_id}", response_model=Dict[str, Any])
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """Update an existing task"""
    try:
        # Build update data from request
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.task_type is not None:
            update_data["task_type"] = request.task_type
        if request.course is not None:
            update_data["course"] = request.course
        if request.priority is not None:
            update_data["priority"] = request.priority.value
        if request.due_date is not None:
            update_data["due_date"] = request.due_date
        if request.tags is not None:
            update_data["tags"] = request.tags
        if request.status is not None:
            update_data["status"] = request.status.value
        if request.completed_at is not None:
            update_data["completed_at"] = request.completed_at
        if request.estimated_minutes is not None:
            update_data["estimated_minutes"] = request.estimated_minutes
        
        task = await service.update_task(task_id, current_user.user_id, update_data)
        
        # Emit websocket event for task update
        try:
            from app.core.infrastructure.websocket import websocket_manager
            task_data = task.copy()
            task_data["user_id"] = current_user.user_id
            task_data["type"] = "task"  # Distinguish from todos
            
            # Use a default workflow_id for direct API updates
            workflow_id = f"api_update_{current_user.user_id}"
            await websocket_manager.emit_task_updated(workflow_id, task_data)
        except Exception as ws_error:
            # Don't fail the request if websocket emission fails
            logger.warning(f"Failed to emit task_updated websocket event: {ws_error}")
        
        return {"data": {"task": task}, "error": None}
            
    except Exception as e:
        return handle_endpoint_error(e, logger, "update_task")


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def delete_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """Delete a task"""
    try:
        result = await service.delete_task(task_id, current_user.user_id)
        return {"data": result, "error": None}
            
    except Exception as e:
        return handle_endpoint_error(e, logger, "delete_task")


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """Get a specific task by ID"""
    try:
        task = await service.get_task(task_id, current_user.user_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"data": {"task": task}, "error": None}
            
    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_task")
