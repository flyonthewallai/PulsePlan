# PulsePlan Architecture Guide

**Living Document** | Last Updated: 11/05/25
**Purpose**: Detailed architecture patterns, best practices, and migration history

> This document is updated after every significant architectural change. See [RULES.md](./RULES.md) for enforcement rules and [CLAUDE.md](../03-ai-agents/CLAUDE.md) for AI assistant guidance.

---

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [Repository Organization](#repository-organization)
3. [Service Layer Patterns](#service-layer-patterns)
4. [Agent System Architecture](#agent-system-architecture)
5. [Database Patterns](#database-patterns)
6. [Migration History](#migration-history)
7. [Common Patterns](#common-patterns)

---

## Architecture Principles

### Core Tenets

1. **Domain-Driven Organization**: Code organized by business domain, not technical layer
2. **Clear Layering**: API → Service → Repository → Database (never skip layers)
3. **Dependency Injection**: Use factory functions and FastAPI `Depends()`
4. **Type Safety**: Full type hints on all functions
5. **Error Boundaries**: Standardized error handling with custom exceptions
6. **No Duplication**: Extract shared logic to utilities/services

### File Size Limits

- **Maximum 500 lines** per file (hard limit)
- **Target 200-300 lines** (soft limit)
- When approaching limits: split by subdomain or create module directory

---

## Repository Organization

### Current Structure (Updated 11/05/25)

```
backend/app/database/
├── __init__.py                 # Re-exports all repositories
├── base_repository.py          # BaseRepository with CRUD operations
├── models.py                   # Pydantic models
├── session.py                  # Database session management
├── manager.py                  # DatabaseManager (legacy, being phased out)
└── repositories/               # Domain-organized repositories
    ├── __init__.py             # Re-exports all domain repositories
    ├── task_repositories/
    │   ├── __init__.py
    │   ├── tag_repository.py   # PredefinedTagRepository, UserTagRepository, TodoTagRepository
    │   ├── task_repository.py  # TaskRepository
    │   └── todo_repository.py  # TodoRepository
    ├── user_repositories/
    │   ├── __init__.py
    │   ├── user_repository.py  # UserRepository
    │   ├── course_repository.py # CourseRepository
    │   └── hobby_repository.py  # HobbiesRepository
    ├── calendar_repositories/
    │   ├── __init__.py
    │   ├── calendar_repository.py  # CalendarLinkRepository, CalendarCalendarRepository,
    │   │                           # CalendarEventRepository, CalendarSyncConflictRepository,
    │   │                           # WebhookSubscriptionRepository
    │   └── timeblocks_repository.py # TimeblocksRepository
    └── integration_repositories/
        ├── __init__.py
        ├── nlu_repository.py       # NLURepository
        ├── usage_repository.py     # UsageRepository
        └── briefings_repository.py # BriefingsRepository
```

### Import Patterns

**Correct:**
```python
# Task domain
from app.database.repositories.task_repositories import (
    TaskRepository,
    PredefinedTagRepository,
    get_predefined_tag_repository
)

# User domain
from app.database.repositories.user_repositories import (
    UserRepository,
    get_user_repository
)

# Calendar domain
from app.database.repositories.calendar_repositories import (
    TimeblocksRepository,
    get_timeblocks_repository
)

# Integration domain
from app.database.repositories.integration_repositories import (
    NLURepository,
    create_nlu_repository
)
```

**Incorrect (old pattern - deprecated):**
```python
# DON'T DO THIS - old pattern before 11/05/25
from app.database.task_repository import TaskRepository  # ❌
from app.database.user_repository import UserRepository  # ❌
```

### Repository Naming Conventions

| Table Name | Repository Class | Factory Function | Notes |
|------------|-----------------|------------------|-------|
| `tasks` | `TaskRepository` | N/A (instantiate directly) | No factory function |
| `todos` | `TodoRepository` | N/A (instantiate directly) | No factory function |
| `predefined_tags` | `PredefinedTagRepository` | `get_predefined_tag_repository()` | |
| `user_tags` | `UserTagRepository` | `get_user_tag_repository()` | |
| `todo_tags` | `TodoTagRepository` | `get_todo_tag_repository()` | |
| `users` | `UserRepository` | `get_user_repository()` | |
| `courses` | `CourseRepository` | `get_course_repository()` | |
| `user_hobbies` | `HobbiesRepository` | `get_hobbies_repository()` | Note: plural "Hobbies" |
| `calendar_links` | `CalendarLinkRepository` | `get_calendar_link_repository()` | |
| `calendar_calendars` | `CalendarCalendarRepository` | `get_calendar_calendar_repository()` | |
| `calendar_events` | `CalendarEventRepository` | `get_calendar_event_repository()` | |
| `calendar_sync_conflicts` | `CalendarSyncConflictRepository` | `get_calendar_sync_conflict_repository()` | |
| `webhook_subscriptions` | `WebhookSubscriptionRepository` | `get_webhook_subscription_repository()` | |
| `timeblocks` | `TimeblocksRepository` | `get_timeblocks_repository()` | |
| `action_records` | `NLURepository` | `create_nlu_repository()` | Handles multiple NLU tables |
| `llm_usage` | `UsageRepository` | `get_usage_repository()` | |
| `briefings` | `BriefingsRepository` | `get_briefings_repository()` | |

### Adding New Repositories

**When to create a new repository:**
- New database table requires data access
- Existing repository file exceeds 400 lines
- Clear subdomain boundary (e.g., notifications, payments)

**Steps:**

1. **Determine domain**: task, user, calendar, or integration?
2. **Create repository file**:
   ```python
   # backend/app/database/repositories/{domain}_repositories/{name}_repository.py
   from typing import Dict, Any, List, Optional
   import logging
   from app.database.base_repository import BaseRepository
   from app.core.utils.error_handlers import RepositoryError

   logger = logging.getLogger(__name__)

   class MyNewRepository(BaseRepository):
       @property
       def table_name(self) -> str:
           return "my_table"

       # Add domain-specific methods

   def get_my_new_repository() -> MyNewRepository:
       """Factory function"""
       return MyNewRepository()
   ```

3. **Update domain __init__.py**:
   ```python
   from .my_new_repository import (
       MyNewRepository,
       get_my_new_repository,
   )

   __all__ = [
       # ... existing exports
       "MyNewRepository",
       "get_my_new_repository",
   ]
   ```

4. **Update repositories/__init__.py** to re-export
5. **Update ARCHITECTURE.md** (this file) with the new repository
6. **Use in services**:
   ```python
   from app.database.repositories.{domain}_repositories import get_my_new_repository
   ```

---

## Service Layer Patterns

### Service Organization

```
backend/app/services/
├── auth/
│   ├── token_service.py        # OAuth token refresh
│   └── token_refresh.py        # Background token refresh
├── integrations/
│   ├── canvas_token_service.py
│   └── calendar_service.py     # (in jobs/calendar/)
├── scheduling/
│   └── smart_slot_finder.py    # Intelligent scheduling
├── analytics/
│   └── posthog_service.py      # Analytics integration
├── usage/
│   ├── usage_config.py
│   ├── usage_limiter.py
│   └── token_tracker.py
├── user/
│   └── hobby_parser.py
├── commands/
│   └── command_parser.py
├── focus/
│   └── focus_service.py
└── {domain}_service.py         # Task, tag, todo, course, timeblock, briefing, gate, nlu_monitoring
```

### Service Pattern

```python
"""
{Domain} Service
Business logic layer for {domain} operations
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.repositories.{domain}_repositories import (
    {Domain}Repository,
    get_{domain}_repository
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class {Domain}Service:
    """Service for {domain} business logic"""

    def __init__(
        self,
        {domain}_repo: Optional[{Domain}Repository] = None
    ):
        """
        Initialize service with optional repository injection

        Args:
            {domain}_repo: Repository instance (injected for testing)
        """
        self.{domain}_repo = {domain}_repo or {Domain}Repository()

    async def complex_operation(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Business logic method

        Args:
            user_id: User ID
            data: Operation data

        Returns:
            Result dictionary

        Raises:
            ServiceError: If operation fails
        """
        try:
            # 1. Validate input
            # 2. Apply business rules
            # 3. Call repository
            # 4. Transform result
            # 5. Return

            result = await self.{domain}_repo.some_method(user_id, data)
            return result

        except Exception as e:
            logger.error(f"Error in complex_operation: {e}", exc_info=True)
            raise ServiceError(
                message=str(e),
                service="{Domain}Service",
                operation="complex_operation",
                details={"user_id": user_id}
            )


def get_{domain}_service() -> {Domain}Service:
    """Dependency injection function"""
    return {Domain}Service()
```

### Service Responsibilities

**Services handle:**
- ✅ Business logic and rules
- ✅ Cross-repository operations
- ✅ Data transformation
- ✅ Validation beyond Pydantic
- ✅ Coordinating multiple repositories
- ✅ Caching strategies
- ✅ External API calls

**Services DO NOT:**
- ❌ Directly access database (use repositories)
- ❌ Handle HTTP requests (that's API layer)
- ❌ Duplicate repository logic
- ❌ Import from API layer

---

## Agent System Architecture

### Agent Tool Organization

```
backend/app/agents/tools/
├── __init__.py
├── data/               # Data operations
│   ├── tasks.py        # Task CRUD tools
│   ├── todos.py        # Todo CRUD tools
│   ├── events.py       # Event CRUD tools
│   └── memory.py       # Memory operations
├── scheduling/         # Scheduling tools
│   ├── planner.py      # Smart scheduling
│   └── optimizer.py    # Schedule optimization
├── search/             # Search tools
│   └── web_search.py
├── integrations/       # External integrations
│   ├── canvas.py       # Canvas LMS
│   ├── calendar.py     # Calendar sync
│   └── email.py        # Email operations
└── communication/      # User communication
    ├── briefing.py     # Daily briefings
    └── notifications.py
```

### Agent Tool Pattern

**Agent tools ALWAYS call services, NEVER repositories:**

```python
# ✅ CORRECT
from app.services.task_service import get_task_service

async def create_task_tool(...):
    task_service = get_task_service()
    return await task_service.create_task(...)

# ❌ WRONG
from app.database.repositories.task_repositories import TaskRepository

async def create_task_tool(...):
    task_repo = TaskRepository()  # DON'T DO THIS
    return await task_repo.create(...)
```

---

## Database Patterns

### BaseRepository

All repositories extend `BaseRepository`:

```python
from app.database.base_repository import BaseRepository

class MyRepository(BaseRepository):
    @property
    def table_name(self) -> str:
        return "my_table"

    # Standard CRUD methods inherited:
    # - get_by_id(id)
    # - get_all(filters, limit, offset)
    # - create(data)
    # - update(id, data)
    # - delete(id)
    # - count(filters)
    # - exists(id)

    # Add domain-specific methods:
    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Custom query"""
        ...
```

### Error Handling

All database operations use `RepositoryError`:

```python
from app.core.utils.error_handlers import RepositoryError

try:
    response = self.supabase.table(self.table_name).select("*").execute()
    return response.data or []
except Exception as e:
    logger.error(f"Error fetching data: {e}", exc_info=True)
    raise RepositoryError(
        message=str(e),
        table=self.table_name,
        operation="get_all",
        details={"filters": filters}
    )
```

### Query Patterns

**Best Practices:**

1. **Always use parameterized queries** (Supabase client does this automatically)
2. **Add error handling** to every database call
3. **Log errors** with context
4. **Return empty list/None** for not found (don't raise)
5. **Raise RepositoryError** for actual errors
6. **Use `.execute()` not `.await execute()`** (Supabase client is sync)

**Example:**

```python
async def get_active_items(self, user_id: str) -> List[Dict[str, Any]]:
    """Get active items for user"""
    try:
        response = self.supabase.table(self.table_name)\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .order("created_at", desc=True)\
            .execute()

        return response.data or []

    except Exception as e:
        logger.error(f"Error fetching active items: {e}", exc_info=True)
        raise RepositoryError(
            message=str(e),
            table=self.table_name,
            operation="get_active_items",
            details={"user_id": user_id}
        )
```

---

## Migration History

### 11/05/25: Database Repository Reorganization

**Motivation**: Database folder was becoming messy with 11+ repository files at the root level, making it hard to navigate and maintain.

**Changes**:
- Created domain-based subdirectories under `repositories/`
- Moved all repository files to appropriate domains
- Updated all 20+ import statements across the codebase
- Created proper `__init__.py` files for clean exports

**Impact**:
- Easier navigation (group by domain)
- Scalable structure (can add more repositories without clutter)
- Clear organization (follows API endpoint pattern)
- No breaking changes (all imports updated)

**Files Updated**:
- Created: 5 new `__init__.py` files
- Moved: 11 repository files
- Updated imports: 20 files across services, agents, API, jobs

**Before:**
```
database/
├── tag_repository.py
├── task_repository.py
├── todo_repository.py
├── user_repository.py
├── course_repository.py
├── hobbies_repository.py
├── calendar_repository.py
├── timeblocks_repository.py
├── nlu_repository.py
├── usage_repository.py
└── briefings_repository.py
```

**After:**
```
database/repositories/
├── task_repositories/
│   ├── tag_repository.py
│   ├── task_repository.py
│   └── todo_repository.py
├── user_repositories/
│   ├── user_repository.py
│   ├── course_repository.py
│   └── hobby_repository.py
├── calendar_repositories/
│   ├── calendar_repository.py
│   └── timeblocks_repository.py
└── integration_repositories/
    ├── nlu_repository.py
    ├── usage_repository.py
    └── briefings_repository.py
```

---

## Common Patterns

### API Endpoint Pattern

```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user, CurrentUser
from app.services.{domain}_service import get_{domain}_service, {Domain}Service

router = APIRouter()

@router.post("/{resource}")
async def create_resource(
    data: ResourceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: {Domain}Service = Depends(get_{domain}_service)
):
    """Create a new resource"""
    try:
        result = await service.create_resource(current_user.id, data.dict())
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Dependency Injection Pattern

**Repository:**
```python
def get_my_repository() -> MyRepository:
    """Factory function for dependency injection"""
    return MyRepository()
```

**Service:**
```python
class MyService:
    def __init__(self, repo: Optional[MyRepository] = None):
        self.repo = repo or MyRepository()

def get_my_service() -> MyService:
    """Factory function"""
    return MyService()
```

**API Usage:**
```python
@router.get("/endpoint")
async def endpoint(
    service: MyService = Depends(get_my_service)
):
    return await service.do_something()
```

### Testing Pattern

```python
import pytest
from app.services.my_service import MyService
from app.database.repositories.my_repositories import MyRepository

@pytest.fixture
def mock_repository():
    """Mock repository for testing"""
    class MockMyRepository(MyRepository):
        async def get_all(self):
            return [{"id": "1", "name": "test"}]

    return MockMyRepository()

async def test_service_operation(mock_repository):
    """Test service with mocked repository"""
    service = MyService(repo=mock_repository)
    result = await service.get_items()

    assert len(result) == 1
    assert result[0]["name"] == "test"
```

---

## Best Practices Checklist

When adding new code:

- [ ] **Determine domain**: Which domain does this belong to?
- [ ] **Check file size**: Will this exceed 500 lines? If so, split first.
- [ ] **Follow layering**: API → Service → Repository → Database
- [ ] **Use dependency injection**: Factory functions for all classes
- [ ] **Add type hints**: All function parameters and returns
- [ ] **Error handling**: Try/except with proper error types
- [ ] **Logging**: Log errors with context
- [ ] **Update this file**: Document architectural changes
- [ ] **Update RULES.md**: If adding new enforcement rules
- [ ] **Run quality gates**: pytest, ruff, black, mypy

---

## Questions?

For quick reference, see [RULES.md](./RULES.md).
For AI assistant guidance, see [CLAUDE.md](../03-ai-agents/CLAUDE.md).
For comprehensive analysis, search the codebase using ripgrep patterns in RULES.md Section 15.
