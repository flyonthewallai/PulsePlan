# API Endpoints Organization

**Last Updated:** 01/27/25

## Overview

This document defines the organization structure and best practices for PulsePlan's API endpoints, as specified in RULES.md Section 1.3. All endpoints follow a consistent modular pattern for maintainability and discoverability.

---

## Architecture Layers

```
┌─────────────────────────────────┐
│   API Endpoints (THIS DOCUMENT) │  ← User-facing layer
├─────────────────────────────────┤
│      Service Layer              │  ← Business logic
├─────────────────────────────────┤
│     Repository Layer            │  ← Data access
├─────────────────────────────────┤
│        Database (Supabase)      │  ← Storage
└─────────────────────────────────┘
```

**Key Principle:** Endpoints are thin routers that delegate to services. Never skip layers. Always: Endpoint → Service → Repository → Database

---

## Directory Structure

### Root Level Organization

```
backend/app/api/v1/endpoints/
├── __init__.py
├── agent.py                    # Main agent entry point (large, cohesive)
├── auth.py                     # Wrapper for auth_modules
├── tasks.py                    # Wrapper for task_modules
├── users.py                    # Wrapper for user_modules
├── integrations.py             # Wrapper for integrations_modules
├── infrastructure.py           # Wrapper for infrastructure_modules
├── admin.py                    # Wrapper for admin_modules
├── focus.py                    # Wrapper for focus_modules
├── calendar.py                 # Wrapper for calendar_modules
└── [domain]_modules/           # Domain-specific sub-routers
```

### Module Pattern

Each domain follows this consistent structure:

```
{domain}_modules/
├── __init__.py                 # Exports router from main.py
├── main.py                     # Consolidates all sub-routers
├── {subdomain1}.py             # Individual router
├── {subdomain2}.py             # Individual router
└── ...
```

---

## Module Organization

### 1. Authentication Module (`auth_modules/`)

**Location:** `backend/app/api/v1/endpoints/auth_modules/`

**Purpose:** User authentication and authorization

**Structure:**
```
auth_modules/
├── __init__.py
├── main.py                     # Consolidates auth routers
├── oauth.py                    # OAuth flows (Google, Microsoft)
├── tokens.py                   # Token management
└── token_refresh.py            # Token refresh endpoints
```

**Root Wrapper:** `auth.py` imports from `auth_modules`

**API Routes:**
- `/auth/oauth/*` - OAuth authentication
- `/auth/tokens/*` - Token operations
- `/auth/refresh/*` - Token refresh

---

### 2. User Management Module (`user_modules/`)

**Location:** `backend/app/api/v1/endpoints/user_modules/`

**Purpose:** User profile and preferences management

**Structure:**
```
user_modules/
├── __init__.py
├── main.py                     # Consolidates user routers
├── users.py                    # User CRUD operations
├── preferences.py              # User preferences
├── contacts.py                 # User contacts
├── courses.py                  # Course management
└── hobbies.py                  # Hobby tracking
```

**Root Wrapper:** `users.py` imports from `user_modules`

**API Routes:**
- `/user-management/users/*` - User operations
- `/user-management/preferences/*` - Preferences
- `/user-management/contacts/*` - Contacts
- `/user-management/courses/*` - Courses
- `/user-management/hobbies/*` - Hobbies

---

### 3. Task Management Module (`task_modules/`)

**Location:** `backend/app/api/v1/endpoints/task_modules/`

**Purpose:** Task, todo, and tag management

**Structure:**
```
task_modules/
├── __init__.py
├── main.py                     # Consolidates task routers
├── tasks.py                    # Task CRUD operations
├── todos.py                    # Todo list management
└── tags.py                     # Tag operations
```

**Root Wrapper:** `tasks.py` imports from `task_modules`

**API Routes:**
- `/tasks/*` - Task operations
- `/todos/*` - Todo operations
- `/tags/*` - Tag operations

---

### 4. Integrations Module (`integrations_modules/`)

**Location:** `backend/app/api/v1/endpoints/integrations_modules/`

**Purpose:** External service integrations

**Structure:**
```
integrations_modules/
├── __init__.py
├── main.py                     # Consolidates integration routers
├── calendar.py                 # Calendar integration endpoints
├── canvas.py                   # Canvas LMS integration
├── email.py                    # Email integration
└── settings.py                  # Integration settings (was integration_settings.py)
```

**Root Wrapper:** `integrations.py` imports from `integrations_modules`

**API Routes:**
- `/integrations/calendar/*` - Calendar operations
- `/integrations/canvas/*` - Canvas operations
- `/integrations/email/*` - Email operations
- `/integrations/integration-settings/*` - Settings management

---

### 5. Infrastructure Module (`infrastructure_modules/`)

**Location:** `backend/app/api/v1/endpoints/infrastructure_modules/`

**Purpose:** System infrastructure and monitoring

**Structure:**
```
infrastructure_modules/
├── __init__.py
├── main.py                     # Consolidates infrastructure routers
├── health.py                   # Health check endpoints
├── rate_limiting.py            # Rate limiting management
└── usage.py                    # Usage tracking and quotas (was usage.py)
```

**Root Wrapper:** `infrastructure.py` imports from `infrastructure_modules`

**API Routes:**
- `/system/health/*` - Health checks
- `/system/rate-limiting/*` - Rate limiting
- `/system/usage/*` - Usage tracking

---

### 6. Focus Module (`focus_modules/`) ⭐ NEW

**Location:** `backend/app/api/v1/endpoints/focus_modules/`

**Purpose:** Focus sessions, Pomodoro, and productivity tracking

**Structure:**
```
focus_modules/
├── __init__.py
├── main.py                     # Consolidates focus routers
├── pomodoro.py                 # Pomodoro settings and phases (was pomodoro.py)
├── sessions.py                 # Focus session management (was focus_sessions.py)
└── entity_matching.py          # Entity matching for sessions (was entity_matching.py)
```

**Root Wrapper:** `focus.py` imports from `focus_modules`

**API Routes:**
- `/focus/pomodoro/*` - Pomodoro settings and phases
- `/focus/sessions/*` - Focus session operations
- `/focus/entity-matching/*` - Entity matching

---

### 7. Calendar Module (`calendar_modules/`) ⭐ NEW

**Location:** `backend/app/api/v1/endpoints/calendar_modules/`

**Purpose:** Unified calendar view and webhooks

**Structure:**
```
calendar_modules/
├── __init__.py
├── main.py                     # Consolidates calendar routers
├── timeblocks.py               # Unified timeblocks API (was timeblocks.py)
└── webhooks.py                 # Calendar webhooks (was calendar_webhooks.py)
```

**Root Wrapper:** `calendar.py` imports from `calendar_modules`

**API Routes:**
- `/timeblocks/*` - Timeblock operations
- `/webhooks/*` - Calendar webhook handlers

---

### 8. Agent Module (`agent_modules/`)

**Location:** `backend/app/api/v1/endpoints/agent_modules/`

**Purpose:** AI agent operations and workflows

**Structure:**
```
agent_modules/
├── __init__.py                 # Exports helper functions/models
├── commands.py                 # Deterministic commands (was commands.py)
├── briefings.py                # Daily briefings (was briefings.py)
├── gates.py                    # Policy gates (was gates.py)
├── conversation.py             # Conversation management
├── models.py                      # Request/response models
├── operations.py               # CRUD operations
└── workflows.py                # Workflow execution
```

**Main Entry Point:** `agent.py` (large unified agent endpoint, ~540 lines)

**API Routes:**
- `/agents/*` - Main agent endpoint (from agent.py)
- `/commands/*` - Command execution
- `/briefings/*` - Briefing operations
- `/gates/*` - Gate confirmation/cancellation

---

### 9. Payments Module (`payments_modules/`)

**Location:** `backend/app/api/v1/endpoints/payments_modules/`

**Purpose:** Payment and subscription management

**Structure:**
```
payments_modules/
├── __init__.py
├── main.py                     # Consolidates payment routers
├── subscriptions.py            # Subscription management
└── revenuecat.py               # RevenueCat integration
```

**API Routes:**
- `/payments/subscriptions/*` - Subscription operations
- `/payments/revenuecat/*` - RevenueCat webhooks

---

### 10. Admin Module (`admin_modules/`)

**Location:** `backend/app/api/v1/endpoints/admin_modules/`

**Purpose:** Administrative operations

**Structure:**
```
admin_modules/
├── __init__.py
├── main.py                     # Consolidates admin routers
└── nlu.py                      # NLU admin operations
```

**Root Wrapper:** `admin.py` imports from `admin_modules`

**API Routes:**
- `/admin/*` - Admin operations

---

## Module Pattern Template

### Creating a New Module

When adding a new domain of endpoints:

1. **Create module directory:**
   ```bash
   mkdir -p backend/app/api/v1/endpoints/{domain}_modules
   ```

2. **Create module structure:**
   ```
   {domain}_modules/
   ├── __init__.py
   ├── main.py
   └── {subdomain}.py
   ```

3. **Module `__init__.py`:**
   ```python
   """
   {Domain} Module Endpoints
   Consolidates all {domain}-related endpoints
   """
   from .main import router

   __all__ = ['router']
   ```

4. **Module `main.py`:**
   ```python
   """
   Main {Domain} Router
   Consolidates all {domain}-related endpoints
   """
   from fastapi import APIRouter

   # Import individual routers
   from .{subdomain} import router as {subdomain}_router

   # Create main router
   router = APIRouter()

   # Include sub-routers with appropriate prefixes
   router.include_router(
       {subdomain}_router,
       prefix="/{subdomain}",
       tags=["{subdomain}"]
   )
   ```

5. **Root-level wrapper:**
   ```python
   """
   {Domain} Endpoints
   Consolidated {domain} module router
   """
   from .{domain}_modules import router

   __all__ = ['router']
   ```

6. **Register in `api.py`:**
   ```python
   from app.api.v1.endpoints import {domain}

   api_router.include_router(
       {domain}.router,
       prefix="/{domain}",
       tags=["{domain}"]
   )
   ```

---

## Endpoint File Template

### Individual Router File

```python
"""
{Subdomain} API Endpoints
Handles {subdomain} operations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.{domain}.{subdomain}_service import get_{subdomain}_service
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class {Resource}Create(BaseModel):
    """Request model for creating {resource}"""
    field1: str = Field(..., description="Description")
    field2: Optional[int] = Field(None, description="Optional field")


class {Resource}Response(BaseModel):
    """Response model for {resource}"""
    id: str
    field1: str
    created_at: str


# Endpoints
@router.post("/", response_model={Resource}Response)
async def create_{resource}(
    data: {Resource}Create,
    current_user: CurrentUser = Depends(get_current_user),
    service = Depends(get_{subdomain}_service)
):
    """
    Create a new {resource}

    Args:
        data: {Resource} creation data
        current_user: Current authenticated user
        service: {Subdomain}Service instance

    Returns:
        Created {resource} data
    """
    try:
        result = await service.create_{resource}(
            user_id=current_user.user_id,
            data=data.model_dump()
        )
        return {Resource}Response(**result)

    except HTTPException:
        raise
    except Exception as e:
        return handle_endpoint_error(e, logger, "create_{resource}")
```

---

## Router Registration Pattern

### In `api.py`

```python
from fastapi import APIRouter
from app.api.v1.endpoints import (
    agent, auth, tasks, integrations, infrastructure,
    users, admin, focus, calendar
)
from app.api.v1.endpoints.payments_modules import main as payments
from app.api.v1.endpoints.agent_modules import commands, briefings, gates

api_router = APIRouter()

# Consolidated modules (with wrapper files)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(users.router, prefix="/user-management", tags=["user-management"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(infrastructure.router, prefix="/system", tags=["system"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(focus.router, tags=["focus"])
api_router.include_router(calendar.router, tags=["calendar"])

# Standalone modules
api_router.include_router(agent.router, prefix="/agents", tags=["agents"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])

# Agent sub-modules (imported directly)
api_router.include_router(commands.router, prefix="/commands", tags=["commands"])
api_router.include_router(briefings.router, prefix="/briefings", tags=["briefings"])
api_router.include_router(gates.router, prefix="/gates", tags=["gates"])
```

---

## Naming Conventions

### Module Directories
- **Pattern:** `{domain}_modules/`
- **Examples:** `auth_modules/`, `task_modules/`, `focus_modules/`
- **Location:** `backend/app/api/v1/endpoints/{domain}_modules/`

### Root Wrapper Files
- **Pattern:** `{domain}.py`
- **Purpose:** Clean import interface for consolidated modules
- **Examples:** `auth.py`, `tasks.py`, `focus.py`

### Router Files
- **Pattern:** `{subdomain}.py`
- **Examples:** `pomodoro.py`, `sessions.py`, `timeblocks.py`
- **Location:** Inside `{domain}_modules/` directory

### Router Variables
- **Pattern:** `router = APIRouter()`
- **Consistent across all endpoint files**

---

## File Organization Rules

### ✅ DO

- **Group related endpoints** into domain modules
- **Use `{domain}_modules/` pattern** for sub-routers
- **Create wrapper files** at root level for clean imports
- **Consolidate routers** in `main.py` within each module
- **Keep endpoints thin** - delegate to services
- **Use consistent naming** across all modules

### ❌ DON'T

- **Don't create standalone files** at root level (use modules)
- **Don't mix domains** in a single module
- **Don't put business logic** in endpoints
- **Don't access repositories directly** from endpoints
- **Don't create duplicate routers** for the same domain
- **Don't leave `.pyc` files** in version control

---

## Migration History

### 2025-01-27: Major Reorganization

**Changes:**
- Created `focus_modules/` - Consolidated pomodoro, focus_sessions, entity_matching
- Created `calendar_modules/` - Consolidated timeblocks, calendar_webhooks
- Moved `commands.py`, `briefings.py`, `gates.py` to `agent_modules/`
- Moved `usage.py` to `infrastructure_modules/`
- Moved `integration_settings.py` to `integrations_modules/settings.py`
- Removed all `.pyc` files and `__pycache__/` directories
- Created wrapper files (`focus.py`, `calendar.py`) for clean imports

**Files Moved:**
- `pomodoro.py` → `focus_modules/pomodoro.py`
- `focus_sessions.py` → `focus_modules/sessions.py`
- `entity_matching.py` → `focus_modules/entity_matching.py`
- `timeblocks.py` → `calendar_modules/timeblocks.py`
- `calendar_webhooks.py` → `calendar_modules/webhooks.py`
- `commands.py` → `agent_modules/commands.py`
- `briefings.py` → `agent_modules/briefings.py`
- `gates.py` → `agent_modules/gates.py`
- `usage.py` → `infrastructure_modules/usage.py`
- `integration_settings.py` → `integrations_modules/settings.py`

**Benefits:**
- Consistent module organization pattern
- Related endpoints grouped together
- Easier to find and maintain code
- No compiled files in version control

---

## Adding New Endpoints

### Checklist

When adding new endpoints to an existing module:

- [ ] Determine if endpoint belongs to existing module or needs new module
- [ ] Create router file in appropriate `{domain}_modules/` directory
- [ ] Add router to module's `main.py`
- [ ] Update module's `__init__.py` if needed
- [ ] Register router in `api.py` (if new module)
- [ ] Add authentication via `Depends(get_current_user)`
- [ ] Use service layer (never direct repository access)
- [ ] Add error handling with `handle_endpoint_error`
- [ ] Add request/response models with Pydantic
- [ ] Add comprehensive docstrings
- [ ] Write integration tests

### Creating New Module

When creating a completely new domain:

- [ ] Create `{domain}_modules/` directory
- [ ] Create `__init__.py` and `main.py`
- [ ] Create individual router files
- [ ] Create root-level wrapper `{domain}.py`
- [ ] Register in `api.py`
- [ ] Update this documentation
- [ ] Add tests for all endpoints

---

## Common Patterns

### 1. CRUD Endpoints

```python
@router.post("/", response_model=ResourceResponse)
async def create_resource(
    data: ResourceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service = Depends(get_resource_service)
):
    """Create resource"""
    result = await service.create(user_id=current_user.user_id, data=data.dict())
    return ResourceResponse(**result)

@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service = Depends(get_resource_service)
):
    """Get resource"""
    result = await service.get(resource_id=resource_id, user_id=current_user.user_id)
    return ResourceResponse(**result)
```

### 2. List with Filters

```python
@router.get("/", response_model=List[ResourceResponse])
async def list_resources(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    service = Depends(get_resource_service)
):
    """List resources with optional filters"""
    filters = {"user_id": current_user.user_id}
    if status:
        filters["status"] = status
    
    results = await service.list(filters=filters, limit=limit)
    return [ResourceResponse(**r) for r in results]
```

### 3. Update Operations

```python
@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    data: ResourceUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service = Depends(get_resource_service)
):
    """Update resource"""
    result = await service.update(
        resource_id=resource_id,
        user_id=current_user.user_id,
        updates=data.dict(exclude_unset=True)
    )
    return ResourceResponse(**result)
```

---

## Anti-Patterns to Avoid

### ❌ Direct Repository Access

```python
# WRONG
from app.database.repositories.task_repositories import TaskRepository

@router.get("/tasks")
async def get_tasks(user_id: str):
    repo = TaskRepository()  # ❌ Bypasses service layer
    return await repo.get_by_user(user_id)
```

### ❌ Business Logic in Endpoints

```python
# WRONG
@router.post("/tasks")
async def create_task(data: TaskCreate):
    # ❌ Validation should be in service
    if data.estimated_minutes > 480:
        raise HTTPException(400, "Task too long")
    
    # ❌ Data transformation should be in service
    task_data = {
        "title": data.title.strip().title(),
        "status": "pending"
    }
    return await service.create(task_data)
```

### ❌ Standalone Files at Root

```python
# WRONG - Don't create standalone files
# backend/app/api/v1/endpoints/my_endpoint.py

# CORRECT - Use module pattern
# backend/app/api/v1/endpoints/my_domain_modules/my_endpoint.py
```

---

## Related Documentation

- **Architecture:** [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- **Service Layer:** [SERVICE_LAYER_PATTERNS.md](./SERVICE_LAYER_PATTERNS.md)
- **API Examples:** [EXAMPLES.md](./EXAMPLES.md)
- **Rules:** [RULES.md](../02-architecture/RULES.md) Section 1.3
- **Testing:** [TESTING.md](./TESTING.md)

---

**Last Updated:** 01/27/25

