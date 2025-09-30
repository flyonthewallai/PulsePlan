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
from app.agents.tools.data.tasks import TaskDatabaseTool

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
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new task"""
    try:
        task_tool = TaskDatabaseTool()
        
        result = await task_tool.execute(
            input_data={
                "operation": "create",
                "task_data": {
                    "title": request.title,
                    "description": request.description,
                    "task_type": request.task_type,
                    "course": request.course,
                    "priority": request.priority.value if request.priority else "medium",
                    "due_date": request.due_date,
                    "tags": request.tags or [],
                    "estimated_minutes": request.estimated_minutes
                }
            },
            context={"user_id": current_user.user_id}
        )
        
        if result.success:
            return {"data": result.data, "error": None}
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    course: Optional[str] = Query(None, description="Filter by course"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """List tasks with optional filters"""
    try:
        task_tool = TaskDatabaseTool()
        
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
        
        result = await task_tool.execute(
            input_data={
                "operation": "list",
                "filters": filters
            },
            context={"user_id": current_user.user_id}
        )
        
        if result.success:
            # Return in format expected by frontend: {tasks: Task[], count: number}
            tasks_data = result.data.get("tasks", [])
            return {"tasks": tasks_data, "count": len(tasks_data)}
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.patch("/{task_id}", response_model=Dict[str, Any])
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an existing task"""
    try:
        task_tool = TaskDatabaseTool()
        
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
        
        result = await task_tool.execute(
            input_data={
                "operation": "update",
                "task_id": task_id,
                "task_data": update_data
            },
            context={"user_id": current_user.user_id}
        )
        
        if result.success:
            # Emit websocket event for task update
            try:
                from ....core.infrastructure.websocket import websocket_manager
                task_data = result.data.get("task", {})
                task_data["user_id"] = current_user.user_id
                task_data["type"] = "task"  # Distinguish from todos
                
                # Use a default workflow_id for direct API updates
                workflow_id = f"api_update_{current_user.user_id}"
                await websocket_manager.emit_task_updated(workflow_id, task_data)
            except Exception as ws_error:
                # Don't fail the request if websocket emission fails
                logger.warning(f"Failed to emit task_updated websocket event: {ws_error}")
            
            return {"data": result.data, "error": None}
        else:
            if "not found" in result.error.lower():
                raise HTTPException(status_code=404, detail="Task not found")
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def delete_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a task"""
    try:
        task_tool = TaskDatabaseTool()
        
        result = await task_tool.execute(
            input_data={
                "operation": "delete",
                "task_id": task_id
            },
            context={"user_id": current_user.user_id}
        )
        
        if result.success:
            return {"data": None, "error": None}
        else:
            if "not found" in result.error.lower():
                raise HTTPException(status_code=404, detail="Task not found")
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific task by ID"""
    try:
        task_tool = TaskDatabaseTool()
        
        result = await task_tool.execute(
            input_data={
                "operation": "get",
                "task_id": task_id
            },
            context={"user_id": current_user.user_id}
        )
        
        if result.success:
            return {"data": result.data, "error": None}
        else:
            if "not found" in result.error.lower():
                raise HTTPException(status_code=404, detail="Task not found")
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")
