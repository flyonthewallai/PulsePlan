"""
Todo management API endpoints.
Handles CRUD operations for todos with tag support.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.core.auth import get_current_user
from app.database.models import TodoModel, TodoPriority
from app.services.todo_service import TodoService, get_todo_service
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)

router = APIRouter()


class TodoCreateRequest(BaseModel):
    """Request model for creating todos"""
    title: str = Field(..., description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")
    priority: Optional[TodoPriority] = Field(TodoPriority.MEDIUM, description="Todo priority")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Todo tags")
    estimated_minutes: Optional[int] = Field(None, description="Estimated duration")


class TodoUpdateRequest(BaseModel):
    """Request model for updating todos"""
    title: Optional[str] = Field(None, description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")
    priority: Optional[TodoPriority] = Field(None, description="Todo priority")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Todo tags")
    completed: Optional[bool] = Field(None, description="Completion status")
    estimated_minutes: Optional[int] = Field(None, description="Estimated duration")


class TodoFilters(BaseModel):
    """Filters for listing todos"""
    completed: Optional[bool] = Field(None, description="Filter by completion status")
    priority: Optional[TodoPriority] = Field(None, description="Filter by priority")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


@router.post("/", response_model=Dict[str, Any])
async def create_todo(
    request: TodoCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """Create a new todo"""
    try:
        todo_data = request.dict(exclude_none=True)
        todo = await service.create_todo(current_user["id"], todo_data)

        # Emit websocket event for todo creation
        try:
            from app.core.infrastructure.websocket import websocket_manager
            todo_ws_data = todo.copy()
            todo_ws_data["user_id"] = current_user["id"]
            todo_ws_data["type"] = "todo"  # Distinguish from tasks
            
            # Use a default workflow_id for direct API updates
            workflow_id = f"api_create_{current_user['id']}"
            await websocket_manager.emit_task_created(workflow_id, todo_ws_data)
        except Exception as ws_error:
            # Don't fail the request if websocket emission fails
            logger.warning(f"Failed to emit task_created websocket event for todo: {ws_error}")
        
        return {"success": True, "data": {"todo": todo}}

    except Exception as e:
        return handle_endpoint_error(e, logger, "create_todo")


@router.get("/", response_model=Dict[str, Any])
async def list_todos(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[TodoPriority] = Query(None, description="Filter by priority"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """List todos with optional filters"""
    try:
        filters = {}
        if completed is not None:
            filters["completed"] = completed
        if priority is not None:
            filters["priority"] = priority
        if tags is not None:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]

        result = await service.list_todos(current_user["id"], filters)
        return {"success": True, "data": result}

    except Exception as e:
        return handle_endpoint_error(e, logger, "list_todos")


@router.get("/{todo_id}", response_model=Dict[str, Any])
async def get_todo(
    todo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """Get a specific todo by ID"""
    try:
        todo = await service.get_todo(todo_id, current_user["id"])

        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")

        return {"success": True, "data": {"todo": todo}}

    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "get_todo")


@router.put("/{todo_id}", response_model=Dict[str, Any])
async def update_todo(
    todo_id: str,
    request: TodoUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """Update a todo"""
    try:
        todo_data = request.dict(exclude_none=True)
        todo = await service.update_todo(todo_id, current_user["id"], todo_data)

        # Emit websocket event for todo update
        try:
            from app.core.infrastructure.websocket import websocket_manager
            todo_ws_data = todo.copy()
            todo_ws_data["user_id"] = current_user["id"]
            todo_ws_data["type"] = "todo"  # Distinguish from tasks
            
            # Use a default workflow_id for direct API updates
            workflow_id = f"api_update_{current_user['id']}"
            await websocket_manager.emit_task_updated(workflow_id, todo_ws_data)
        except Exception as ws_error:
            # Don't fail the request if websocket emission fails
            logger.warning(f"Failed to emit task_updated websocket event for todo: {ws_error}")
        
        return {"success": True, "data": {"todo": todo}}

    except Exception as e:
        return handle_endpoint_error(e, logger, "update_todo")


@router.delete("/{todo_id}", response_model=Dict[str, Any])
async def delete_todo(
    todo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """Delete a todo"""
    try:
        result = await service.delete_todo(todo_id, current_user["id"])
        return {"success": True, "data": result}

    except Exception as e:
        return handle_endpoint_error(e, logger, "delete_todo")


@router.post("/bulk-toggle", response_model=Dict[str, Any])
async def bulk_toggle_todos(
    todo_ids: List[str],
    completed: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """Bulk toggle completion status for multiple todos"""
    try:
        result = await service.bulk_toggle_todos(todo_ids, current_user["id"], completed)
        return {"success": True, "data": result}

    except Exception as e:
        return handle_endpoint_error(e, logger, "bulk_toggle_todos")


@router.post("/{todo_id}/convert-to-task", response_model=Dict[str, Any])
async def convert_todo_to_task(
    todo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TodoService = Depends(get_todo_service)
):
    """Convert a todo to a full task"""
    try:
        result = await service.convert_to_task(todo_id, current_user["id"])
        return {"success": True, "data": result}

    except Exception as e:
        return handle_endpoint_error(e, logger, "convert_todo_to_task")