# CLAUDE.md

This file provides guidance to Claude Code when working with PulsePlan.

---

## ⚠️ MANDATORY: RULES.md COMPLIANCE

**BEFORE starting ANY work:**

1. **READ** [RULES.md](../02-architecture/RULES.md) - Essential rules and standards
2. **FOR WEB CHANGES**: **READ** [WEB_RULES.md](../04-development/WEB_RULES.md) - Web-specific patterns ⭐
3. **CONSULT** [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) - Detailed patterns and structure
4. **FOLLOW** all architectural invariants and workflows
5. **UPDATE** ARCHITECTURE.md when introducing architectural changes

**Enforcement**:

- Backend changes: RULES.md is authoritative
- Web changes: WEB_RULES.md is authoritative (takes precedence for frontend)
- Both: ARCHITECTURE.md provides detailed patterns

---

## Quick Architecture Overview

### System Components

- **Backend**: Python FastAPI with LangGraph multi-agent system
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Database**: PostgreSQL (Supabase) with RLS
- **Cache**: Upstash Redis
- **Integrations**: Canvas LMS, Google/Microsoft Calendar, OpenAI

### Code Organization

```
backend/app/
├── agents/          # LangGraph workflows + NLU
├── scheduler/       # OR-Tools scheduling engine
├── api/v1/endpoints/# FastAPI routers (THIN)
├── services/        # Business logic
├── database/        # Repositories (domain-organized)
├── jobs/            # Background jobs
├── workers/         # APScheduler tasks
└── memory/          # Dual-layer memory system

web/src/
├── pages/           # Route components
├── components/      # Reusable UI
├── features/        # Feature modules
├── hooks/           # API integration
└── services/        # API clients
```

### Layering (NEVER SKIP)

```
API → Service → Repository → Database
```

**Critical Rules:**

- API endpoints call **services only**
- Services call **repositories only**
- Agent tools call **services only**
- Repositories extend `BaseRepository`

---

## Development Commands

### Backend

```bash
cd backend

# Run dev server
python main.py

# Tests
pytest

# Code quality
ruff check .      # Linting
black .           # Formatting
mypy .            # Type checking
```

### Frontend

```bash
cd web

# Dev server
npm run dev

# Build
npm run build

# Code quality
npm run lint         # ESLint
npm run type-check   # TypeScript
npm run test         # Vitest
```

---

## Repository Organization (11/05/25 Update)

### Current Structure

```
backend/app/database/repositories/
├── task_repositories/       # Tasks, todos, tags
├── user_repositories/       # Users, courses, hobbies
├── calendar_repositories/   # Calendars, events, timeblocks
└── integration_repositories/# NLU, usage, briefings
```

### Import Pattern

```python
# ✅ CORRECT (current)
from app.database.repositories.task_repositories import TaskRepository
from app.database.repositories.user_repositories import UserRepository

# ❌ DEPRECATED (pre-11/05/25)
from app.database.task_repository import TaskRepository
```

**See [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md#repository-organization) for complete list and adding new repositories.**

---

## Common Workflows

### Add New Feature

1. **Understand**: Read existing code and [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
2. **Search**: Use ripgrep to find related patterns
3. **Decide Placement**: Consult [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
4. **Implement**: Follow patterns in [RULES.md](../02-architecture/RULES.md)
5. **Test**: Run quality gates
6. **Document**: Update [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) if architectural
7. **Verify**: Check against [RULES.md](../02-architecture/RULES.md)

### Fix Repository Import Issues

**Old pattern found:**

```python
from app.database.task_repository import TaskRepository
```

**Update to:**

```python
from app.database.repositories.task_repositories import TaskRepository
```

**Domains:**

- `task_repositories` - Tasks, todos, tags
- `user_repositories` - Users, courses, hobbies
- `calendar_repositories` - Calendars, events, timeblocks
- `integration_repositories` - NLU, usage, briefings

### Add New Repository

1. Create in correct domain: `database/repositories/{domain}_repositories/`
2. Extend `BaseRepository`
3. Add factory function
4. Update `{domain}_repositories/__init__.py`
5. Update `repositories/__init__.py`
6. Document in [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)

**Template:** See [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md#adding-new-repositories)

---

## Environment Variables

**Required:**

```bash
# AI
OPENAI_API_KEY=

# Database
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Cache
REDIS_URL=

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Canvas
CANVAS_API_KEY=
CANVAS_BASE_URL=

# Calendar Webhooks
GOOGLE_WEBHOOK_VERIFICATION_TOKEN=
API_BASE_URL=  # Use ngrok in development

# Security
SECRET_KEY=
ENCRYPTION_KEY=
```

See `.env.example` in `backend/` and `web/` for complete list.

---

## Key Patterns

### API Endpoint

```python
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, CurrentUser
from app.services.my_service import MyService, get_my_service

router = APIRouter()

@router.post("/resource")
async def create_resource(
    data: ResourceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: MyService = Depends(get_my_service)
):
    return await service.create_resource(current_user.id, data)
```

### Service

```python
from app.database.repositories.{domain}_repositories import MyRepository

class MyService:
    def __init__(self, repo: Optional[MyRepository] = None):
        self.repo = repo or MyRepository()

    async def operation(self, user_id: str) -> Dict[str, Any]:
        try:
            return await self.repo.get_data(user_id)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise ServiceError(...)

def get_my_service() -> MyService:
    return MyService()
```

### Repository

```python
from app.database.base_repository import BaseRepository

class MyRepository(BaseRepository):
    @property
    def table_name(self) -> str:
        return "my_table"

    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise RepositoryError(...)
```

**More patterns:** See [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md#common-patterns)

---

## Agent System

### Tool Pattern

**Agent tools ALWAYS call services:**

```python
# ✅ CORRECT
from app.services.task_service import get_task_service

async def create_task_tool(...):
    service = get_task_service()
    return await service.create_task(...)

# ❌ WRONG
from app.database.repositories.task_repositories import TaskRepository

async def create_task_tool(...):
    repo = TaskRepository()  # DON'T DO THIS
    return await repo.create(...)
```

### Workflow Types

- `NATURAL_LANGUAGE` - General chat/NLP
- `SCHEDULING` - Task scheduling with optimization
- `CALENDAR` - Calendar operations
- `TASK` - Task CRUD
- `BRIEFING` - Daily briefing generation
- `EMAIL` - Email operations
- `SEARCH` - Web search

**Details:** See [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md#agent-system-architecture)

---

## Security Requirements

### Database

- ✅ Use repositories only
- ✅ RLS policies on all tables
- ✅ Parameterized queries (automatic with Supabase client)
- ❌ NEVER access DB directly from API/agents

### Authentication

- ✅ Supabase Auth for all endpoints
- ✅ OAuth tokens encrypted with KMS
- ✅ Background token refresh
- ❌ NEVER log PII or tokens

### Input

- ✅ Pydantic validation for all inputs
- ✅ Sanitize user input
- ✅ HMAC signing for critical operations
- ❌ NEVER trust client input

---

## Quality Gates

**Before committing:**

**Backend:**

```bash
ruff check .
black .
mypy .
pytest
```

**Frontend:**

```bash
npm run lint
npm run type-check
npm run test
```

**All must pass** before creating PR.

---

## File Size Limits

- **500 lines** - Hard maximum
- **300 lines** - Target

**When approaching limit:**

1. Extract duplicate code
2. Split into subdirectories
3. Create module with `__init__.py`

**Example:** See [RULES.md](../02-architecture/RULES.md#file-size-limits)

---

## Common Search Patterns

```bash
# Find direct DB access
rg "get_supabase\(\)" --type py

# Find old repository imports
rg "from app\.database\.\w+_repository import" --type py

# Find missing type hints
rg "def \w+\([^)]*\):" --type py | grep -v " -> "

# Find TODOs
rg "TODO|FIXME|HACK" --type py --type ts
```

**More patterns:** See [RULES.md](../02-architecture/RULES.md#search-patterns-ripgrep)

---

## When to Update Docs

**ARCHITECTURE.md** (frequently):

- ✅ Adding new repository/service
- ✅ Changing file organization
- ✅ Adding new pattern
- ✅ Documenting migration
- ✅ Adding best practices

**RULES.md** (rarely):

- ✅ New enforcement rule
- ✅ Changed workflow
- ✅ Major breaking change

**CLAUDE.md** (occasionally):

- ✅ New quick reference
- ✅ Changed commands
- ✅ Updated patterns

---

## Prohibited Patterns

### Backend Violations

#### ❌ Direct DB Access

```python
# WRONG
from app.config.database.supabase import get_supabase
db = get_supabase()
result = db.table("tasks").select("*").execute()

# CORRECT
from app.database.repositories.task_repositories import TaskRepository
repo = TaskRepository()
result = await repo.get_all()
```

#### ❌ Service Logic in API

```python
# WRONG
@router.post("/tasks")
async def create_task(data: TaskCreate):
    # Complex business logic here

# CORRECT
@router.post("/tasks")
async def create_task(
    data: TaskCreate,
    service: TaskService = Depends(get_task_service)
):
    return await service.create_task(data)
```

#### ❌ Agent Tools Calling Repositories

```python
# WRONG
from app.database.repositories import TaskRepository

async def tool():
    repo = TaskRepository()
    return await repo.create(...)

# CORRECT
from app.services.task_service import get_task_service

async def tool():
    service = get_task_service()
    return await service.create_task(...)
```

### Web/Frontend Violations

#### ❌ Using `any` Types

```typescript
// WRONG - Eliminates TypeScript safety
function handleData(data: any) {}
interface Props {
  metadata?: any;
}

// CORRECT - Full type safety
interface Metadata {
  /* proper types */
}
function handleData(data: Record<string, unknown>) {}
interface Props {
  metadata?: Metadata;
}
```

#### ❌ Global Variables

```typescript
// WRONG - Module-level globals
let globalHandler: Function | null = null;

// CORRECT - React Context with useRef
const MyContext = createContext<ContextType>();
// Use refs in provider
```

#### ❌ localStorage for Tokens

```typescript
// WRONG - XSS vulnerable
localStorage.setItem("token", accessToken);

// CORRECT - httpOnly cookies (automatic with Supabase)
const {
  data: { session },
} = await supabase.auth.getSession();
```

**More Backend:** See [RULES.md](../02-architecture/RULES.md#prohibited-patterns)  
**More Frontend:** See [WEB_RULES.md](../04-development/WEB_RULES.md#prohibited-patterns)

---

## Testing Patterns

### Repository Test

```python
async def test_repository(mock_supabase):
    repo = MyRepository()
    repo.supabase = mock_supabase
    result = await repo.get_all()
    assert len(result) > 0
```

### Service Test

```python
async def test_service():
    mock_repo = MockRepository()
    service = MyService(repo=mock_repo)
    result = await service.operation()
    assert result["success"]
```

**More:** See [RULES.md](../02-architecture/RULES.md#testing-requirements)

---

## Quick Reference

| Task               | Location                                       | Pattern                           |
| ------------------ | ---------------------------------------------- | --------------------------------- |
| Add API endpoint   | `api/v1/endpoints/`                            | Thin router, call service         |
| Add service        | `services/`                                    | Business logic, call repositories |
| Add repository     | `database/repositories/{domain}_repositories/` | Extend BaseRepository             |
| Add agent tool     | `agents/tools/{domain}/`                       | Call services only                |
| Add agent workflow | `agents/graphs/`                               | Error boundaries, checkpointing   |
| Add background job | `jobs/` or `workers/`                          | APScheduler or one-time           |

---

## Help & Documentation

### Backend Development

- **Essential rules**: [RULES.md](../02-architecture/RULES.md)
- **Detailed architecture**: [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- **Service patterns**: [SERVICE_LAYER_PATTERNS.md](../04-development/SERVICE_LAYER_PATTERNS.md)

### Frontend Development

- **⭐ Web rules**: [WEB_RULES.md](../04-development/WEB_RULES.md) - **Required reading**
- **Testing**: [TESTING.md](../04-development/TESTING.md)
- **Examples**: [EXAMPLES.md](../04-development/EXAMPLES.md)

### General

- **User docs**: [README.md](../README.md)
- **Search patterns**: Use ripgrep (see above)
- **Code examples**: Search codebase for existing patterns

**Remember:**

- Code should be **obvious, not clever**
- **Backend**: RULES.md enforces standards
- **Frontend**: WEB_RULES.md enforces standards
- **ARCHITECTURE.md** documents patterns
- This file provides **quick reference**

---

## Making Changes: Required Workflow

1. **READ** [RULES.md](../02-architecture/RULES.md) and understand enforcement rules
2. **CONSULT** [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) for patterns
3. **SEARCH** codebase for similar examples
4. **IMPLEMENT** following established patterns
5. **TEST** with quality gates
6. **DOCUMENT** in [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) if architectural
7. **VERIFY** against [RULES.md](../02-architecture/RULES.md) checklist

**Never skip steps. Never deviate from patterns without explicit approval.**
