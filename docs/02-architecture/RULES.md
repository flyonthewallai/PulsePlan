# PulsePlan – Development Rules

**Version:** 3.0 | **Last Updated:** 11/05/25

> **Every change must follow these rules.** For detailed patterns and architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 0. Purpose

Keep PulsePlan **modular, deduplicated, and production-grade**.

- ✅ **Refactor** to shared functions instead of duplicating logic
- ✅ **Migrate cleanly** instead of commenting out old code
- ✅ **Small modules** (<500 lines) over giant files
- ✅ **Pure functions** for domain logic
- ✅ Every change leaves code **lint-clean, typed, tested**

---

## 1. Architecture Enforcement

### 1.1 Layering (Never Skip)

```
API Layer (FastAPI)
  ↓ calls
Service Layer (business logic)
  ↓ calls
Repository Layer (database access)
  ↓ accesses
Database (PostgreSQL)
```

**Rules:**
- API endpoints **call services only**, never repositories
- Services **call repositories only**, never direct DB
- Agent tools **call services only**, never repositories
- Repositories **extend BaseRepository** with domain methods

### 1.2 Repository Organization

**Current Structure** (11/05/25):

```
backend/app/database/repositories/
├── task_repositories/       # Tasks, todos, tags
├── user_repositories/       # Users, courses, hobbies
├── calendar_repositories/   # Calendars, events, timeblocks
└── integration_repositories/ # NLU, usage, briefings
```

**Import Pattern:**
```python
# ✅ CORRECT
from app.database.repositories.task_repositories import TaskRepository
from app.database.repositories.user_repositories import UserRepository
from app.database.repositories.calendar_repositories import TimeblocksRepository
from app.database.repositories.integration_repositories import NLURepository

# ❌ WRONG (old pattern)
from app.database.task_repository import TaskRepository  # Deprecated
```

**See [ARCHITECTURE.md](./ARCHITECTURE.md#repository-organization) for:**
- Complete repository list
- Adding new repositories
- Naming conventions

### 1.3 File Organization

**API Endpoints**: `backend/app/api/v1/endpoints/`
- Thin routers only
- Use `{domain}_modules/` for sub-routers
- Example: `task_modules/tasks.py`, `user_modules/hobbies.py`

**Services**: `backend/app/services/`
- Business logic and orchestration
- Use subdirectories for complex domains
- Example: `auth/`, `scheduling/`, `usage/`

**Agents**: `backend/app/agents/`
- `graphs/` - Workflow implementations
- `tools/` - Domain-organized tools (data, scheduling, search, integrations, communication)
- `nlu/` - NLU pipeline
- `services/` - Agent-specific services

**See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete structure.**

---

## 2. Coding Standards

### 2.1 Python (Backend)

**Type Hints (Required):**
```python
async def get_items(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get items for user"""
    ...
```

**Error Handling:**
```python
from app.core.utils.error_handlers import RepositoryError, ServiceError

try:
    result = await self.repo.get_data()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise ServiceError(
        message=str(e),
        service="MyService",
        operation="get_data"
    )
```

**Dependency Injection:**
```python
class MyService:
    def __init__(self, repo: Optional[MyRepository] = None):
        self.repo = repo or MyRepository()

def get_my_service() -> MyService:
    return MyService()

# In API:
@router.get("/endpoint")
async def endpoint(service: MyService = Depends(get_my_service)):
    ...
```

**Quality Gates (Must Pass):**
- `ruff check .` - Linting
- `black .` - Formatting
- `mypy .` - Type checking
- `pytest` - All tests

### 2.2 TypeScript (Frontend)

**Type Safety:**
```typescript
interface Task {
  id: string;
  title: string;
  due_date?: string;
}

function getTasks(userId: string): Promise<Task[]> {
  return api.get<Task[]>(`/tasks?user_id=${userId}`);
}
```

**Quality Gates:**
- `npm run lint` - ESLint
- `npm run type-check` - TypeScript
- `npm run test` - Vitest

---

## 3. Security (Non-Negotiable)

### 3.1 Database

- ✅ **Parameterized queries only** (Supabase client handles this)
- ✅ **RLS policies** on all tables
- ✅ **Repository layer** for all access
- ❌ **Never** access DB directly from API/agents

### 3.2 Authentication

- ✅ **Supabase Auth** for all endpoints
- ✅ **OAuth tokens** encrypted with KMS
- ✅ **Token refresh** background service
- ❌ **Never** log PII or tokens

### 3.3 Input Validation

- ✅ **Pydantic models** for all API inputs
- ✅ **Validate and sanitize** all user input
- ✅ **HMAC signing** for critical operations
- ❌ **Never** trust client input

---

## 4. Required Change Workflow

**ALWAYS follow this process:**

1. **Understand**: Read existing code and patterns
2. **Search**: Use ripgrep to find related code
   ```bash
   rg "pattern" --type py
   ```
3. **Decide Placement**: Consult [ARCHITECTURE.md](./ARCHITECTURE.md) decision table
4. **Implement**: Follow existing patterns
5. **Test**: Run quality gates
6. **Document**: Update ARCHITECTURE.md if architectural change
7. **Verify**: Check against this file

---

## 5. Domain-Specific Rules

### 5.1 Scheduling Engine

**Critical System** - `backend/app/scheduler/`

- ✅ **Deterministic** and **idempotent**
- ✅ **Timezone-aware** (all datetimes in UTC internally)
- ✅ **Pure functions** in core logic
- ✅ **OR-Tools CP-SAT** for optimization
- ❌ **Never** introduce side effects in core
- ❌ **Never** skip tests

### 5.2 Agent System

**LangGraph Multi-Agent** - `backend/app/agents/`

**Tools must:**
- ✅ Call services, **never** repositories
- ✅ Handle errors gracefully
- ✅ Return structured data
- ✅ Log operations

**Workflows must:**
- ✅ Have error boundaries
- ✅ Support state checkpointing
- ✅ Be idempotent where possible

### 5.3 Integrations

**Canvas LMS:**
- User-provided API key
- Backfill + delta sync jobs
- Auto-ingestion to memory

**Google Calendar:**
- OAuth 2.0
- Two-way sync (incremental pull, push)
- Watch channels for real-time updates
- Premium gating for write operations

**See [ARCHITECTURE.md](./ARCHITECTURE.md#agent-system-architecture) for details.**

---

## 6. Prohibited Patterns

### ❌ Never Do This

**Direct DB Access:**
```python
# ❌ WRONG
from app.config.database.supabase import get_supabase
db = get_supabase()
result = db.table("tasks").select("*").execute()

# ✅ CORRECT
from app.database.repositories.task_repositories import TaskRepository
repo = TaskRepository()
result = await repo.get_all()
```

**Service Logic in API:**
```python
# ❌ WRONG
@router.post("/tasks")
async def create_task(data: TaskCreate):
    # Business logic here...
    if task.priority == "high":
        # Complex validation...

# ✅ CORRECT
@router.post("/tasks")
async def create_task(
    data: TaskCreate,
    service: TaskService = Depends(get_task_service)
):
    return await service.create_task(data)
```

**Duplicate Logic:**
```python
# ❌ WRONG - Same logic in 3 places
def format_date_api(date): ...
def format_date_service(date): ...
def format_date_repo(date): ...

# ✅ CORRECT - Extract to utility
from app.core.utils.date_utils import format_date
```

**Circular Imports:**
```python
# ❌ WRONG
# services/a.py imports services/b.py
# services/b.py imports services/a.py

# ✅ CORRECT - Extract shared logic to utils or use dependency injection
```

---

## 7. File Size Limits

**Hard Limits:**
- **500 lines maximum** per file
- **300 lines target** for most files

**When approaching limit:**
1. Check for duplicate code to extract
2. Split into subdirectories by subdomain
3. Create module with `__init__.py`

**Example:**
```
# Before (600 lines)
services/task_service.py

# After
services/task_services/
├── __init__.py          # Re-exports
├── task_crud.py         # CRUD operations
├── task_scheduling.py   # Scheduling logic
└── task_validation.py   # Validation rules
```

---

## 8. Testing Requirements

### 8.1 Required Tests

**Every new feature must have:**
- ✅ Unit tests for business logic
- ✅ Integration tests for API endpoints
- ✅ Repository tests with mocked DB

**Critical systems need:**
- ✅ Comprehensive test coverage (>80%)
- ✅ Property-based testing (hypothesis)
- ✅ Load/stress testing

### 8.2 Test Patterns

**Repository Test:**
```python
async def test_repository(mock_supabase):
    repo = MyRepository()
    repo.supabase = mock_supabase
    result = await repo.get_all()
    assert len(result) > 0
```

**Service Test:**
```python
async def test_service():
    mock_repo = MockRepository()
    service = MyService(repo=mock_repo)
    result = await service.operation()
    assert result["success"]
```

---

## 9. Git & PR Standards

### 9.1 Commits

**Format:**
```
type(scope): brief description

Longer explanation if needed.

```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### 9.2 Pull Requests

**Before Creating PR:**
- [ ] All quality gates pass
- [ ] Tests added for new features
- [ ] ARCHITECTURE.md updated (if architectural change)
- [ ] No console.log/print statements
- [ ] No commented-out code
- [ ] No breaking changes (or documented)

**PR Description Must Include:**
- What changed and why
- Testing performed
- Breaking changes (if any)
- Screenshots (if UI change)

---

## 10. Common Tasks Quick Reference

### Add New Repository

1. **Create file**: `database/repositories/{domain}_repositories/{name}_repository.py`
2. **Extend BaseRepository**
3. **Add factory function**
4. **Update domain `__init__.py`**
5. **Update `repositories/__init__.py`**
6. **Update ARCHITECTURE.md**

**See [ARCHITECTURE.md](./ARCHITECTURE.md#adding-new-repositories) for template.**

### Add New Service

1. **Create file**: `services/{name}_service.py` or `services/{domain}/{name}_service.py`
2. **Import repositories** from correct domain
3. **Add factory function**
4. **Use in API** with `Depends()`

### Add New API Endpoint

1. **Create/update router**: `api/v1/endpoints/{domain}.py` or `api/v1/endpoints/{domain}_modules/`
2. **Use dependency injection** for services
3. **Add type hints** for all parameters
4. **Handle errors** properly
5. **Add docstrings**

---

## 11. Search Patterns (Ripgrep)

**Find all direct DB access:**
```bash
rg "get_supabase\(\)" --type py
rg "\.table\(" --type py
```

**Find imports of old repository pattern:**
```bash
rg "from app\.database\.\w+_repository import" --type py
```

**Find missing type hints:**
```bash
rg "def \w+\([^)]*\):" --type py | grep -v " -> "
```

**Find TODO comments:**
```bash
rg "TODO|FIXME|HACK" --type py --type ts
```

---

## 12. When to Update This File

**Update RULES.md when:**
- ❌ Almost never - this should be stable
- ✅ Adding new enforcement rules
- ✅ Changing required workflow
- ✅ Major breaking changes

**Update ARCHITECTURE.md when:**
- ✅ Adding new repository
- ✅ Changing file organization
- ✅ Adding new pattern
- ✅ Documenting migration
- ✅ Adding best practices

---

## Questions?

- **Detailed patterns**: See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **AI assistance**: See [CLAUDE.md](../03-ai-agents/CLAUDE.md)
- **Quick lookup**: Use ripgrep patterns above
- **Examples**: Search codebase for existing patterns

**Remember**: Code should be obvious, not clever.
