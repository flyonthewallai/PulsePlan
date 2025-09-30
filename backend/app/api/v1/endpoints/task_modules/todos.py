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
from app.agents.tools.data.todos import TodoDatabaseTool

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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new todo"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        todo_data = request.dict(exclude_none=True)
        result = await todo_tool.create_todo(todo_data, context)

        if result.success:
            # Emit websocket event for todo creation
            try:
                from ....core.infrastructure.websocket import websocket_manager
                todo_data = result.data.get("todo", {})
                todo_data["user_id"] = current_user["id"]
                todo_data["type"] = "todo"  # Distinguish from tasks
                
                # Use a default workflow_id for direct API updates
                workflow_id = f"api_create_{current_user['id']}"
                await websocket_manager.emit_task_created(workflow_id, todo_data)
            except Exception as ws_error:
                # Don't fail the request if websocket emission fails
                logger.warning(f"Failed to emit task_created websocket event for todo: {ws_error}")
            
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=400, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def list_todos(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[TodoPriority] = Query(None, description="Filter by priority"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List todos with optional filters"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        filters = {}
        if completed is not None:
            filters["completed"] = completed
        if priority is not None:
            filters["priority"] = priority
        if tags is not None:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]

        result = await todo_tool.list_todos(filters, context)

        if result.success:
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=400, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{todo_id}", response_model=Dict[str, Any])
async def get_todo(
    todo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific todo by ID"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        result = await todo_tool.get_todo(todo_id, context)

        if result.success:
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=404, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{todo_id}", response_model=Dict[str, Any])
async def update_todo(
    todo_id: str,
    request: TodoUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a todo"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        todo_data = request.dict(exclude_none=True)
        result = await todo_tool.update_todo(todo_id, todo_data, context)

        if result.success:
            # Emit websocket event for todo update
            try:
                from ....core.infrastructure.websocket import websocket_manager
                todo_data = result.data.get("todo", {})
                todo_data["user_id"] = current_user["id"]
                todo_data["type"] = "todo"  # Distinguish from tasks
                
                # Use a default workflow_id for direct API updates
                workflow_id = f"api_update_{current_user['id']}"
                await websocket_manager.emit_task_updated(workflow_id, todo_data)
            except Exception as ws_error:
                # Don't fail the request if websocket emission fails
                logger.warning(f"Failed to emit task_updated websocket event for todo: {ws_error}")
            
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=400, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{todo_id}", response_model=Dict[str, Any])
async def delete_todo(
    todo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a todo"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        result = await todo_tool.delete_todo(todo_id, context)

        if result.success:
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=404, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-toggle", response_model=Dict[str, Any])
async def bulk_toggle_todos(
    todo_ids: List[str],
    completed: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Bulk toggle completion status for multiple todos"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        result = await todo_tool.bulk_toggle_todos(todo_ids, completed, context)

        if result.success:
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=400, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{todo_id}/convert-to-task", response_model=Dict[str, Any])
async def convert_todo_to_task(
    todo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Convert a todo to a full task"""
    try:
        todo_tool = TodoDatabaseTool()
        context = {"user_id": current_user["id"]}

        result = await todo_tool.convert_todo_to_task(todo_id, context)

        if result.success:
            return {"success": True, "data": result.data}
        else:
            raise HTTPException(status_code=400, detail=result.error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))