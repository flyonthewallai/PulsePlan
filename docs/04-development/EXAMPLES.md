# EXAMPLES.md - Reference Implementation Patterns

**Last Updated:** 11/05/25
**Purpose:** Concrete examples showing correct patterns for each layer

> Abstract rules are hard to follow. This document provides copy-paste-ready examples for common implementation patterns. Use these as templates.

---

## Table of Contents

1. [Repository Pattern](#repository-pattern)
2. [Service Pattern](#service-pattern)
3. [API Endpoint Pattern](#api-endpoint-pattern)
4. [Agent Tool Pattern](#agent-tool-pattern)
5. [Agent Workflow Pattern](#agent-workflow-pattern)
6. [Intent Classification Pattern](#intent-classification-pattern)
7. [Scheduling Pattern](#scheduling-pattern)
8. [Test Patterns](#test-patterns)

---

## Repository Pattern

### Basic Repository

```python
"""
Task Repository
Database access layer for tasks table
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository):
    """Repository for tasks table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "tasks"

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks for a user, optionally filtered by status

        Args:
            user_id: User ID
            status: Optional status filter (pending, completed, etc.)

        Returns:
            List of task dictionaries

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)

            if status:
                query = query.eq("status", status)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(
                f"Error fetching tasks for user {user_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id, "status": status}
            )

    async def get_upcoming(
        self,
        user_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get tasks due in the next N days"""
        try:
            from datetime import datetime, timedelta

            deadline = datetime.utcnow() + timedelta(days=days)

            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .lte("due_date", deadline.isoformat())\
                .eq("status", "pending")\
                .order("due_date")\
                .execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching upcoming tasks: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_upcoming",
                details={"user_id": user_id, "days": days}
            )
```

**Key Points:**
- Extends `BaseRepository`
- All methods are `async`
- Uses `RepositoryError` for exceptions
- Returns empty list for not found (doesn't raise)
- Logs errors with context

---

## Service Pattern

### Business Logic Service

```python
"""
Task Service
Business logic layer for task operations
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from app.database.repositories.task_repositories import TaskRepository
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task business logic"""

    def __init__(
        self,
        task_repo: Optional[TaskRepository] = None
    ):
        """
        Initialize service with optional repository injection

        Args:
            task_repo: Repository instance (injected for testing)
        """
        self.task_repo = task_repo or TaskRepository()

    async def create_task(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new task with validation

        Args:
            user_id: User ID
            task_data: Task data dictionary

        Returns:
            Created task dictionary

        Raises:
            ServiceError: If creation fails or validation fails
        """
        try:
            # 1. Validate input
            validated_data = self._validate_task_data(task_data)

            # 2. Apply business rules
            validated_data["user_id"] = user_id
            validated_data["status"] = "pending"
            validated_data["created_at"] = datetime.utcnow().isoformat()

            # 3. Create via repository
            task = await self.task_repo.create(validated_data)

            # 4. Post-creation logic (e.g., notifications)
            await self._send_task_created_notification(task)

            logger.info(f"Created task {task['id']} for user {user_id}")
            return task

        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            raise ServiceError(
                message=str(e),
                service="TaskService",
                operation="create_task",
                details={"user_id": user_id}
            )

    async def get_task_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get task summary for user (combines multiple queries)

        This demonstrates orchestrating multiple repository calls
        """
        try:
            # Parallel fetches
            pending_tasks = await self.task_repo.get_by_user(user_id, status="pending")
            completed_tasks = await self.task_repo.get_by_user(user_id, status="completed")
            upcoming_tasks = await self.task_repo.get_upcoming(user_id, days=7)

            return {
                "total_pending": len(pending_tasks),
                "total_completed": len(completed_tasks),
                "upcoming_count": len(upcoming_tasks),
                "upcoming_tasks": upcoming_tasks[:5]  # Next 5
            }

        except Exception as e:
            logger.error(f"Error getting task summary: {e}", exc_info=True)
            raise ServiceError(
                message=str(e),
                service="TaskService",
                operation="get_task_summary"
            )

    def _validate_task_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize task data

        Private method for internal validation
        """
        # Trim whitespace from title
        if "title" in data:
            data["title"] = data["title"].strip()

        # Validate required fields
        if not data.get("title"):
            raise ValueError("Title is required")

        # Validate duration
        if "duration_minutes" in data:
            if data["duration_minutes"] <= 0:
                raise ValueError("Duration must be positive")

        return data

    async def _send_task_created_notification(self, task: Dict[str, Any]):
        """Send notification (placeholder)"""
        # Implementation would call notification service
        pass


def get_task_service() -> TaskService:
    """Dependency injection function"""
    return TaskService()
```

**Key Points:**
- Dependency injection via constructor
- Business logic orchestration
- Calls repositories, never direct DB
- Private methods for internal logic
- Factory function for DI

---

## API Endpoint Pattern

### FastAPI Router

```python
"""
Task API Endpoints
Handles task CRUD operations via REST API
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.auth import get_current_user, CurrentUser
from app.services.task_service import TaskService, get_task_service
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class TaskCreate(BaseModel):
    """Task creation request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    due_date: datetime | None = None
    duration_minutes: int | None = Field(None, gt=0, le=1440)
    priority: str = Field("medium", pattern="^(low|medium|high)$")


class TaskResponse(BaseModel):
    """Task response"""
    id: str
    title: str
    status: str
    created_at: datetime
    # ... other fields


# Endpoints
@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(
    data: TaskCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """
    Create a new task

    Args:
        data: Task creation data
        current_user: Authenticated user
        service: Task service

    Returns:
        Created task data

    Raises:
        HTTPException: If creation fails
    """
    try:
        task = await service.create_task(
            user_id=current_user.id,
            task_data=data.dict(exclude_none=True)
        )

        return {
            "success": True,
            "data": task,
            "message": "Task created successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        return handle_endpoint_error(
            error=e,
            log=logger,
            operation="create_task"
        )


@router.get("/tasks", response_model=Dict[str, Any])
async def get_tasks(
    status_filter: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    """
    Get all tasks for authenticated user

    Args:
        status_filter: Optional status filter
        current_user: Authenticated user
        service: Task service

    Returns:
        List of tasks
    """
    try:
        if status_filter:
            tasks = await service.get_tasks_by_status(
                user_id=current_user.id,
                status=status_filter
            )
        else:
            tasks = await service.get_all_tasks(current_user.id)

        return {
            "success": True,
            "data": tasks,
            "count": len(tasks)
        }

    except Exception as e:
        return handle_endpoint_error(
            error=e,
            log=logger,
            operation="get_tasks"
        )
```

**Key Points:**
- Thin router, calls service only
- Pydantic models for validation
- Dependency injection for auth and services
- Standard response format
- Error handling with proper status codes

---

## Agent Tool Pattern

### LangChain Tool

```python
"""
Task Management Tools
LangChain tools for task operations
"""
import logging
from typing import Dict, Any, Optional
from langchain.tools import tool

from app.services.task_service import get_task_service

logger = logging.getLogger(__name__)


@tool
async def create_task_tool(
    title: str,
    user_id: str,
    due_date: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Create a new task for the user

    Args:
        title: Task title
        user_id: User ID
        due_date: Optional due date (ISO format)
        duration_minutes: Optional duration in minutes
        priority: Priority level (low, medium, high)

    Returns:
        Created task data
    """
    try:
        service = get_task_service()

        task_data = {
            "title": title,
            "priority": priority
        }

        if due_date:
            task_data["due_date"] = due_date
        if duration_minutes:
            task_data["duration_minutes"] = duration_minutes

        result = await service.create_task(user_id, task_data)

        logger.info(f"Tool created task {result['id']} for user {user_id}")
        return {
            "success": True,
            "task_id": result["id"],
            "title": result["title"],
            "message": f"Task '{title}' created successfully"
        }

    except Exception as e:
        logger.error(f"Tool error creating task: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create task"
        }


@tool
async def get_upcoming_tasks_tool(
    user_id: str,
    days: int = 7
) -> Dict[str, Any]:
    """
    Get upcoming tasks for user

    Args:
        user_id: User ID
        days: Number of days to look ahead

    Returns:
        List of upcoming tasks
    """
    try:
        service = get_task_service()
        tasks = await service.get_upcoming_tasks(user_id, days=days)

        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks),
            "message": f"Found {len(tasks)} upcoming tasks"
        }

    except Exception as e:
        logger.error(f"Tool error fetching tasks: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
```

**Critical Rule:** ✅ Agent tools ALWAYS call services, NEVER repositories

---

## Agent Workflow Pattern

### LangGraph Workflow

```python
"""
Task Management Workflow
LangGraph workflow for task operations
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.core.state.workflow_container import WorkflowState
from app.agents.tools.data.tasks import create_task_tool, get_upcoming_tasks_tool

logger = logging.getLogger(__name__)


async def analyze_intent_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Analyze user intent

    Returns updated state with intent classification
    """
    try:
        user_message = state["user_message"]

        # Simple keyword-based intent detection
        # (In production, use NLU service)
        if "create" in user_message.lower():
            intent = "create_task"
        elif "show" in user_message.lower() or "list" in user_message.lower():
            intent = "list_tasks"
        else:
            intent = "unknown"

        return {
            **state,
            "intent": intent,
            "current_step": "execute"
        }

    except Exception as e:
        logger.error(f"Error in analyze_intent_node: {e}", exc_info=True)
        return {
            **state,
            "errors": [*state.get("errors", []), str(e)],
            "current_step": "error"
        }


async def execute_task_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Execute task operation based on intent

    Returns updated state with execution results
    """
    try:
        intent = state["intent"]
        user_id = state["user_id"]

        if intent == "create_task":
            # Extract parameters from user message
            # (In production, use NLU parameter extraction)
            result = await create_task_tool(
                title="New task",  # Extract from message
                user_id=user_id
            )
        elif intent == "list_tasks":
            result = await get_upcoming_tasks_tool(user_id=user_id)
        else:
            result = {"success": False, "error": "Unknown intent"}

        return {
            **state,
            "intermediate_results": {
                "task_operation": result
            },
            "current_step": "respond"
        }

    except Exception as e:
        logger.error(f"Error in execute_task_node: {e}", exc_info=True)
        return {
            **state,
            "errors": [*state.get("errors", []), str(e)],
            "current_step": "error"
        }


async def generate_response_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Generate final response to user

    Returns updated state with final response
    """
    try:
        result = state["intermediate_results"]["task_operation"]

        if result["success"]:
            response = result.get("message", "Operation completed successfully")
        else:
            response = f"Error: {result.get('error', 'Unknown error')}"

        return {
            **state,
            "final_response": response,
            "current_step": "complete"
        }

    except Exception as e:
        logger.error(f"Error in generate_response_node: {e}", exc_info=True)
        return {
            **state,
            "errors": [*state.get("errors", []), str(e)],
            "final_response": "I encountered an error processing your request.",
            "current_step": "error"
        }


def create_task_workflow():
    """
    Create and compile task management workflow

    Returns compiled workflow graph
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("analyze", analyze_intent_node)
    workflow.add_node("execute", execute_task_node)
    workflow.add_node("respond", generate_response_node)

    # Define edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "execute")
    workflow.add_edge("execute", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()
```

**Key Points:**
- Error boundaries in every node
- State is immutable (return new state)
- Clear node responsibilities
- Logs errors with context

---

## Intent Classification Pattern

See [CONTEXT.md](./CONTEXT.md) for full details. Quick example:

```python
async def classify_intent(prompt: str) -> IntentResponse:
    """Classify user intent"""
    # 1. Check explicit keywords first (fast, free)
    if any(kw in prompt.lower() for kw in ["cancel", "delete"]):
        return IntentResponse(
            intent_type="cancel_event",
            confidence=0.95,
            extracted_params={}
        )

    # 2. Use LLM for ambiguous cases
    return await llm_classify(prompt)
```

---

## Scheduling Pattern

See [INTERFACES.md](./INTERFACES.md) for complete contracts. Quick example:

```python
from ortools.sat.python import cp_model

def create_schedule(tasks, user_context):
    model = cp_model.CpModel()

    # Define variables
    start_vars = {
        task.id: model.NewIntVar(0, horizon, f"start_{task.id}")
        for task in tasks
    }

    # Add constraints
    for task in tasks:
        if task.due_date:
            model.Add(start_vars[task.id] <= task.due_date)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        return extract_schedule(solver, start_vars)
    else:
        raise SchedulingError("No feasible schedule")
```

---

## Test Patterns

### Unit Test

```python
import pytest
from app.services.task_service import TaskService


class MockTaskRepository:
    async def create(self, data):
        return {"id": "test-123", **data}


async def test_create_task_validates_title():
    """Test that service validates title"""
    service = TaskService(repo=MockTaskRepository())

    # Empty title should raise error
    with pytest.raises(ValueError, match="Title is required"):
        await service.create_task("user-123", {"title": ""})
```

### Integration Test

```python
async def test_create_task_endpoint(authenticated_client):
    """Test task creation via API"""
    response = authenticated_client.post("/api/v1/tasks", json={
        "title": "Test task",
        "priority": "high"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]
```

---

## Questions?

- **More examples needed?** Request specific patterns
- **Pattern unclear?** See [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Testing patterns?** See [TESTING.md](./TESTING.md)

**Remember:** Copy these patterns, don't reinvent them.
