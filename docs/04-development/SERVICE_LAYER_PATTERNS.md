# Service Layer Best Practices

**Last Updated:** 11/05/25

## Overview

This document defines the service layer patterns and best practices for PulsePlan's backend architecture, as specified in RULES.md Section 1.2 and 1.4.

---

## Architecture Layers

```
┌─────────────────────────────────┐
│   API Endpoints / Agent Tools   │  ← User-facing layer
├─────────────────────────────────┤
│      Service Layer              │  ← Business logic (THIS DOCUMENT)
├─────────────────────────────────┤
│     Repository Layer            │  ← Data access
├─────────────────────────────────┤
│        Database (Supabase)      │  ← Storage
└─────────────────────────────────┘
```

**Key Principle:** Never skip layers. Always: Endpoint → Service → Repository → Database

---

## Service Layer Responsibilities

### 1. Business Logic
- Validation of input data
- Business rule enforcement
- Data transformation and enrichment
- Orchestration of multiple repository calls
- Complex calculations and aggregations

### 2. Error Handling
- Catch repository exceptions
- Transform to `ServiceError` with context
- Log errors with appropriate level
- Return user-friendly error messages

### 3. Logging
- Log all operations (INFO level)
- Log errors with stack traces (ERROR level)
- Include contextual information (user_id, entity_id, etc.)

### 4. Dependency Injection
- Accept repositories via constructor
- Support optional injection for testing
- Provide sensible defaults

### 5. Transaction Management
- Coordinate multiple repository operations
- Ensure data consistency
- Handle rollback scenarios

---

## Service Template

```python
"""
{Domain} Service
Business logic layer for {domain} operations

Implements RULES.md Section 1.2 - Service layer pattern.
"""
import logging
from typing import Dict, Any, List, Optional

from app.database.repositories.{domain}_repositories import (
    {Repository},
    get_{repository}
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class {Domain}Service:
    """
    Service for {domain} business logic

    Handles:
    - {Responsibility 1}
    - {Responsibility 2}
    - {Responsibility 3}
    """

    def __init__(self, repository: {Repository} = None):
        """
        Initialize service with optional repository injection

        Args:
            repository: Repository instance (injected for testing)
        """
        self.repo = repository or {Repository}()

    async def operation_name(
        self,
        required_param: str,
        optional_param: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Business operation description

        Args:
            required_param: Description
            optional_param: Description (optional)

        Returns:
            Result dictionary

        Raises:
            ServiceError: If operation fails
        """
        try:
            # 1. Validate input
            if not required_param:
                raise ServiceError(
                    message="Required parameter is missing",
                    operation="operation_name"
                )

            # 2. Business logic
            result = await self.repo.database_operation(required_param)

            # 3. Transform/enrich data if needed
            enriched_result = self._enrich_data(result)

            # 4. Log success
            logger.info(
                f"Operation completed: {enriched_result.get('id')}"
            )

            return enriched_result

        except ServiceError:
            # Re-raise service errors
            raise

        except Exception as e:
            # Log and wrap unexpected errors
            logger.error(f"Error in operation: {e}", exc_info=True)
            raise ServiceError(
                message="Operation failed",
                operation="operation_name",
                details={"param": required_param}
            )

    def _enrich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Private helper method for data enrichment"""
        # Business logic here
        return data


def get_{domain}_service() -> {Domain}Service:
    """
    Factory function for dependency injection

    Returns:
        Configured service instance
    """
    return {Domain}Service()
```

---

## Naming Conventions

### Service Classes
- **Pattern:** `{Domain}Service`
- **Examples:** `TaskService`, `UserService`, `CalendarEventService`
- **Location:** `/backend/app/services/{domain}_service.py`

### Factory Functions
- **Pattern:** `get_{domain}_service()`
- **Purpose:** Dependency injection
- **Returns:** Service instance with default dependencies

### Methods
- **Public methods:** Async, descriptive names (`create_task`, `get_user_events`)
- **Private methods:** Prefix with `_` (`_validate_input`, `_enrich_data`)

---

## Error Handling Pattern

### ServiceError Usage

```python
from app.core.utils.error_handlers import ServiceError

# Validation errors
if not required_field:
    raise ServiceError(
        message="Field is required",
        operation="create_entity"
    )

# Business logic errors
if entity.status != "active":
    raise ServiceError(
        message="Cannot operate on inactive entity",
        operation="update_entity",
        details={"entity_id": entity.id, "status": entity.status}
    )

# Wrap repository errors
try:
    result = await self.repo.create(data)
except Exception as e:
    logger.error(f"Repository error: {e}", exc_info=True)
    raise ServiceError(
        message="Failed to create entity",
        operation="create_entity",
        details={"data": data}
    )
```

### Error Response in Endpoints

```python
from app.core.utils.error_handlers import handle_endpoint_error, ServiceError

@router.post("/entities")
async def create_entity(
    data: EntityCreate,
    service: EntityService = Depends(get_entity_service)
):
    try:
        entity = await service.create_entity(data.dict())
        return {"success": True, "data": entity}

    except ServiceError as e:
        # Handle specific business errors
        if "already exists" in e.message.lower():
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)

    except Exception as e:
        # Handle unexpected errors
        return handle_endpoint_error(e, logger, "create_entity")
```

---

## Dependency Injection Patterns

### In API Endpoints

```python
from fastapi import APIRouter, Depends
from app.services.task_service import TaskService, get_task_service

router = APIRouter()

@router.get("/tasks")
async def get_tasks(
    current_user: Dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)  # ← Injected
):
    tasks_result = await service.list_tasks(
        user_id=current_user.user_id,
        filters={"status": "active"}
    )
    return {"success": True, "data": tasks_result}
```

### In Agent Tools

```python
from app.services.task_service import TaskService

class TaskDatabaseTool(TaskTool):
    def __init__(self, task_service: TaskService = None):
        super().__init__(name="task_database")
        # Inject service, not repository
        self.task_service = task_service or TaskService()

    async def execute(self, input_data: Dict, context: Dict):
        # Use service methods
        tasks = await self.task_service.list_tasks(
            user_id=context["user_id"],
            filters=input_data.get("filters", {})
        )
        return ToolResult(success=True, data=tasks)
```

### In Other Services (Service→Service)

```python
class BriefingService:
    def __init__(
        self,
        task_service: TaskService = None,
        calendar_service: CalendarEventService = None
    ):
        # Inject other services
        self.task_service = task_service or TaskService()
        self.calendar_service = calendar_service or CalendarEventService()

    async def generate_briefing(self, user_id: str):
        # Coordinate multiple services
        tasks = await self.task_service.list_tasks(user_id)
        events = await self.calendar_service.get_upcoming_events(user_id)

        # Business logic to combine
        return self._format_briefing(tasks, events)
```

---

## Testing Pattern

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.task_service import TaskService

@pytest.mark.asyncio
async def test_create_task():
    # Arrange: Mock repository
    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value={"id": "123", "title": "Test"})

    # Act: Inject mock into service
    service = TaskService(repository=mock_repo)
    result = await service.create_task(
        user_id="user123",
        task_data={"title": "Test Task"}
    )

    # Assert
    assert result["id"] == "123"
    assert result["title"] == "Test"
    mock_repo.create.assert_called_once()
```

---

## Common Patterns

### 1. List with Filters

```python
async def list_entities(
    self,
    user_id: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = 100
) -> Dict[str, Any]:
    """List entities with optional filters"""
    try:
        filters = filters or {}
        filters["user_id"] = user_id

        entities = await self.repo.get_all(filters=filters, limit=limit)

        return {
            "entities": entities,
            "count": len(entities)
        }
    except Exception as e:
        raise ServiceError(
            message="Failed to list entities",
            operation="list_entities"
        )
```

### 2. Get with Authorization

```python
async def get_entity(
    self,
    entity_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Get entity with user authorization check"""
    try:
        entity = await self.repo.get_by_id(entity_id)

        if not entity:
            raise ServiceError(
                message="Entity not found",
                operation="get_entity"
            )

        # Authorization check
        if entity["user_id"] != user_id:
            raise ServiceError(
                message="Access denied",
                operation="get_entity"
            )

        return entity
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(
            message="Failed to fetch entity",
            operation="get_entity"
        )
```

### 3. Update with Validation

```python
async def update_entity(
    self,
    entity_id: str,
    user_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Update entity with validation"""
    try:
        # Get existing entity
        entity = await self.get_entity(entity_id, user_id)

        # Validate updates
        if "status" in updates:
            valid_statuses = ["pending", "active", "completed"]
            if updates["status"] not in valid_statuses:
                raise ServiceError(
                    message=f"Invalid status. Must be one of: {valid_statuses}",
                    operation="update_entity"
                )

        # Perform update
        updated = await self.repo.update(entity_id, updates)

        logger.info(f"Updated entity {entity_id}")
        return updated

    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(
            message="Failed to update entity",
            operation="update_entity"
        )
```

### 4. Create with Enrichment

```python
async def create_entity(
    self,
    user_id: str,
    entity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create entity with data enrichment"""
    try:
        # Validate required fields
        if not entity_data.get("title"):
            raise ServiceError(
                message="Title is required",
                operation="create_entity"
            )

        # Enrich with defaults
        enriched_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
            **entity_data
        }

        # Create in database
        created = await self.repo.create(enriched_data)

        logger.info(f"Created entity {created['id']} for user {user_id}")
        return created

    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(
            message="Failed to create entity",
            operation="create_entity"
        )
```

---

## Existing Services Reference

### Core Business Services
Located in `/backend/app/services/`:

- **`task_service.py`** - Task CRUD and management
- **`todo_service.py`** - Todo CRUD and management
- **`tag_service.py`** - Tag operations and analytics
- **`user_service.py`** - User profile operations
- **`course_service.py`** - Course management
- **`timeblock_service.py`** - Unified calendar timeblocks
- **`briefing_service.py`** - Daily briefing aggregation
- **`gate_service.py`** - Policy gate management
- **`nlu_service.py`** - NLU action records and gates ← NEW
- **`calendar_event_service.py`** - Calendar events CRUD ← NEW

### Infrastructure Services
- **`services/infrastructure/cache_service.py`** - Redis caching
- **`services/infrastructure/preferences_service.py`** - User preferences
- **`services/auth/token_service.py`** - OAuth token management
- **`services/integrations/calendar_sync_service.py`** - Calendar sync operations

---

## Migration Checklist

When converting direct repository access to service layer:

- [ ] Create service class in `/backend/app/services/{domain}_service.py`
- [ ] Implement all business operations as service methods
- [ ] Add validation and error handling with ServiceError
- [ ] Add comprehensive logging
- [ ] Create factory function `get_{domain}_service()`
- [ ] Update API endpoints to use `Depends(get_{domain}_service)`
- [ ] Update agent tools to inject service in constructor
- [ ] Update other services to inject service dependencies
- [ ] Remove direct repository imports from endpoints/tools
- [ ] Add unit tests with mocked repository
- [ ] Update documentation

---

## Anti-Patterns to Avoid

### ❌ Direct Repository Access in Endpoints

```python
# WRONG
from app.database.repositories import TaskRepository

@router.get("/tasks")
async def get_tasks(user_id: str):
    repo = TaskRepository()  # ❌ Bypasses service layer
    tasks = await repo.get_by_user(user_id)
    return tasks
```

### ❌ Direct Supabase Calls

```python
# WRONG
from app.config.database.supabase import get_supabase

@router.get("/tasks")
async def get_tasks(user_id: str):
    supabase = get_supabase()  # ❌ Bypasses both layers
    result = supabase.table("tasks").select("*").eq("user_id", user_id).execute()
    return result.data
```

### ❌ Business Logic in Endpoints

```python
# WRONG
@router.post("/tasks")
async def create_task(
    data: TaskCreate,
    service: TaskService = Depends(get_task_service)
):
    # ❌ Validation should be in service
    if data.estimated_minutes > 480:
        raise HTTPException(400, "Task too long")

    # ❌ Data transformation should be in service
    task_data = {
        "title": data.title.strip().title(),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    return await service.create_task(task_data)
```

### ❌ Repository Creation in Service Methods

```python
# WRONG
class TaskService:
    async def get_task(self, task_id: str):
        repo = TaskRepository()  # ❌ Should be injected via constructor
        return await repo.get_by_id(task_id)
```

---

## Questions?

- **Architecture:** See [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- **Repository Layer:** See [DATABASE_PATTERNS.md](./DATABASE_PATTERNS.md)
- **API Patterns:** See [API_PATTERNS.md](./API_PATTERNS.md)
- **RULES.md:** Section 1.2, 1.4, 6.1

**Last Updated:** 11/05/25
