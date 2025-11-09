# CONTEXT.md - Context Loading Guide

**Last Updated:** 11/05/25
**Purpose:** Route Claude to the right documentation for each type of task

> As documentation grows beyond practical context limits, this file tells Claude exactly what to read for each type of work. This prevents missing critical rules and ensures consistent implementation.

---

## How to Use This Document

**When starting any task:**

1. **Find your task type** in the sections below
2. **Load the required reading** listed for that task
3. **Follow the patterns** specified
4. **Update docs** as indicated

**For Claude Code:**

```
Read CONTEXT.md and load context for: [Your Task Type]

Then proceed with implementation.
```

---

## Context Maps by Task Type

### 🎯 Intent Classification Work

**When:** Modifying NLU pipeline, intent classification, or routing logic

**Required Reading:**

- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - Section: "Agent System Architecture" → "Agent Tool Organization"
- **[RULES.md](../02-architecture/RULES.md)** - Section 5.2: "Agent System"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - `IntentRequest`, `IntentResponse`, `ActionRecord`
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Intent classification patterns
- **[PITFALLS.md](../04-development/PITFALLS.md)** - Intent classification common mistakes

**Key Contracts:**

- Input: `IntentRequest` with user prompt and history
- Output: `IntentResponse` with intent type, confidence, extracted params
- Confidence thresholds: `>= 0.85` execute, `0.60-0.85` confirm, `< 0.60` clarify

**Implementation Location:**

- Core logic: `backend/app/agents/nlu/`
- Intent specs: `backend/app/agents/core/intent_specs.py`
- Classifiers: `backend/app/agents/nlu/classifier_onnx.py`
- Services: `backend/app/agents/services/nlu_service.py`

**After Implementation:**

- [ ] Update [EXAMPLES.md](../04-development/EXAMPLES.md) if new pattern
- [ ] Update [PITFALLS.md](../04-development/PITFALLS.md) if edge cases discovered
- [ ] Update [INTERFACES.md](../02-architecture/INTERFACES.md) if contracts changed

---

### ⚙️ Scheduling Engine Work

**When:** Modifying OR-Tools solver, scheduling algorithms, or optimization

**Required Reading:**

- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - "Scheduling Engine" overview
- **[RULES.md](../02-architecture/RULES.md)** - Section 5.1: "Scheduling Engine"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - `SchedulingRequest`, `SchedulingResponse`, `SchedulingRule`
- **[TESTING.md](../04-development/TESTING.md)** - Scheduling test requirements
- **[PITFALLS.md](../04-development/PITFALLS.md)** - OR-Tools constraints section

**Key Constraints:**

- **MUST** complete within 5 seconds
- **MUST** be deterministic and idempotent
- **MUST** respect user-defined hard constraints
- All datetime handling in UTC internally

**Implementation Location:**

- Core: `backend/app/scheduler/core/`
- Optimization: `backend/app/scheduler/optimization/`
- Constraints: `backend/app/scheduler/utils/constraint_helpers.py`

**Critical Invariants:**

- No overlapping timeblocks in schedules
- All schedules respect working hours (if enabled)
- Solver completes within timeout
- Handles infeasible cases gracefully

**After Implementation:**

- [ ] Run full test suite: `pytest backend/app/scheduler/testing/`
- [ ] Update [PITFALLS.md](../04-development/PITFALLS.md) with new edge cases
- [ ] Update [TESTING.md](../04-development/TESTING.md) if new test scenarios

---

### 🔌 API Endpoint Work

**When:** Creating or modifying FastAPI endpoints

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Sections 1.1 (Layering), 2.1 (Python standards), 3 (Security)
- **[API_ENDPOINTS_ORGANIZATION.md](../04-development/API_ENDPOINTS_ORGANIZATION.md)** ⭐ **REQUIRED for endpoint organization**
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - "Service Layer Patterns", "Common Patterns"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - Request/Response contracts, validation rules
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - API endpoint pattern

**Pattern to Follow:**

```python
# Thin router - call service only
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, CurrentUser
from app.services.my_service import MyService, get_my_service

@router.post("/resource")
async def create_resource(
    data: ResourceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: MyService = Depends(get_my_service)
):
    return await service.create_resource(current_user.id, data)
```

**Implementation Location:**

- Main endpoints: `backend/app/api/v1/endpoints/{domain}.py`
- Sub-routers: `backend/app/api/v1/endpoints/{domain}_modules/`
- **See [API_ENDPOINTS_ORGANIZATION.md](../04-development/API_ENDPOINTS_ORGANIZATION.md)** for complete module structure and organization patterns

**Security Checklist:**

- [ ] Uses `get_current_user` dependency
- [ ] Validates input with Pydantic models
- [ ] Calls service layer (not repositories directly)
- [ ] Returns standard response format
- [ ] Has proper error handling

**After Implementation:**

- [ ] Add integration test
- [ ] Update [INTERFACES.md](../02-architecture/INTERFACES.md) with new endpoints
- [ ] Update [API_ENDPOINTS_ORGANIZATION.md](../04-development/API_ENDPOINTS_ORGANIZATION.md) if new module created
- [ ] Document in API docs (if external-facing)

---

### 🌐 Web Application / Frontend Work

**When:** Creating or modifying React components, TypeScript code, or frontend features

**Required Reading:**

- **[WEB_RULES.md](../04-development/WEB_RULES.md)** ⭐ **REQUIRED for ALL web changes**
- **[STYLES.md](../04-development/STYLES.md)** - Design system tokens and styling patterns
- **[TESTING.md](../04-development/TESTING.md)** - Frontend testing requirements
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - API contracts and data types
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Frontend patterns if available

**Critical Rules:**

- ❌ **ZERO `any` types** - Define proper interfaces for all data
- ❌ **NO global variables** - Use React Context with `useRef` instead
- ❌ **NO localStorage for tokens** - Use httpOnly cookies (automatic with Supabase)
- ❌ **NO debug `console.log` in production** - Remove before commit
- ✅ Components < 500 lines (split if larger)
- ✅ Extract duplicate utilities to `lib/utils/`
- ✅ Add error boundaries to page-level components
- ✅ Validate all external input with Zod
- ✅ Use TanStack Query for all data fetching

**Technology Stack:**

- **Framework:** React 18 + TypeScript (strict mode)
- **Build Tool:** Vite
- **Styling:** TailwindCSS + Radix UI components
- **Routing:** React Router
- **State:** React Context + TanStack Query
- **Auth:** Supabase Auth (httpOnly cookies)

**Implementation Location:**

- Pages: `web/src/pages/{name}Page.tsx`
- Components: `web/src/components/{domain}/{Name}.tsx`
- Shared UI: `web/src/components/ui/{Name}.tsx`
- Hooks: `web/src/hooks/use{Name}.ts`
- Utils: `web/src/lib/utils/{domain}.ts`
- Services: `web/src/services/{name}Service.ts`
- Types: `web/src/types/{domain}.ts`

**Type Safety Checklist:**

- [ ] Zero `any` types (use `unknown`, `Record<string, unknown>`, or proper interfaces)
- [ ] All WebSocket event handlers have typed interfaces
- [ ] All API responses have proper type definitions
- [ ] Generic return types use `T = unknown` not `T = any`

**Security Checklist:**

- [ ] No tokens in localStorage (only sessionStorage for temporary cross-window data)
- [ ] No sensitive data in console.log
- [ ] All user input validated with Zod schemas
- [ ] CSRF protection enabled (via Supabase)

**Performance Checklist:**

- [ ] List items wrapped in `React.memo` with proper comparison
- [ ] Expensive computations memoized with `useMemo`
- [ ] Event handlers stabilized with `useCallback`
- [ ] Proper dependency arrays (no missing or extra deps)

**Before Submitting:**

- [ ] Run `npm run lint` (ESLint strict mode)
- [ ] Run `npm run type-check` (TypeScript strict)
- [ ] Run `npm test` (Vitest component tests)
- [ ] Search for duplicates: `rg "function formatCourseCode|function formatDate" web/src`
- [ ] Search for `any` types: `rg ": any\b|<any>|\(any\)" web/src --type tsx --type ts`
- [ ] Search for localStorage: `rg "localStorage\." web/src`
- [ ] Search for console.log: `rg "console\.(log|debug)" web/src`

**After Implementation:**

- [ ] Update [WEB_RULES.md](../04-development/WEB_RULES.md) if new pattern discovered
- [ ] Update [STYLES.md](../04-development/STYLES.md) if new design token added
- [ ] Add component tests per [TESTING.md](../04-development/TESTING.md)
- [ ] Update [INTERFACES.md](../02-architecture/INTERFACES.md) if API contracts changed

---

### 💾 Repository Layer Work

**When:** Creating or modifying database repositories

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 1.2: "Repository Organization"
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - "Repository Organization", "Adding New Repositories"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - `BaseRepository` interface, database schemas
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Repository pattern

**Current Structure:**

```
backend/app/database/repositories/
├── task_repositories/       # Tasks, todos, tags
├── user_repositories/       # Users, courses, hobbies
├── calendar_repositories/   # Calendars, events, timeblocks
└── integration_repositories/# NLU, usage, briefings
```

**Pattern to Follow:**

```python
from app.database.base_repository import BaseRepository

class MyRepository(BaseRepository):
    @property
    def table_name(self) -> str:
        return "my_table"

    async def custom_query(self, user_id: str) -> List[Dict[str, Any]]:
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

**Implementation Checklist:**

- [ ] Extends `BaseRepository`
- [ ] All methods are `async`
- [ ] Uses `RepositoryError` for exceptions
- [ ] Returns `None`/empty list for not found (doesn't raise)
- [ ] Has factory function for dependency injection

**After Implementation:**

- [ ] Update domain `__init__.py`
- [ ] Update `repositories/__init__.py`
- [ ] Update [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) repository table
- [ ] Add repository tests

---

### 🧠 Service Layer Work

**When:** Creating or modifying business logic services

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 1.1 (Layering), 2.1 (Standards)
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - "Service Layer Patterns"
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Service pattern
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - Relevant data contracts

**Pattern to Follow:**

```python
class MyService:
    def __init__(self, repo: Optional[MyRepository] = None):
        self.repo = repo or MyRepository()

    async def operation(self, user_id: str) -> Dict[str, Any]:
        try:
            # Business logic
            result = await self.repo.get_data(user_id)
            # Transform, validate, orchestrate
            return result
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise ServiceError(...)

def get_my_service() -> MyService:
    return MyService()
```

**Implementation Location:**

- Simple services: `backend/app/services/{name}_service.py`
- Complex domains: `backend/app/services/{domain}/{name}_service.py`

**Service Responsibilities:**

- ✅ Business logic and validation
- ✅ Cross-repository operations
- ✅ Data transformation
- ✅ External API calls
- ❌ NO direct database access (use repositories)
- ❌ NO HTTP handling (that's API layer)

**After Implementation:**

- [ ] Add service tests with mocked repositories
- [ ] Update [EXAMPLES.md](../04-development/EXAMPLES.md) if new pattern
- [ ] Document in [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) if complex

---

### 🤖 Agent Tool Work

**When:** Creating or modifying LangGraph agent tools

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 5.2: "Agent System"
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - "Agent Tool Organization"
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Agent tool pattern
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - `WorkflowState`

**Critical Rule:**
**Agent tools MUST call services, NEVER repositories**

**Pattern to Follow:**

```python
from langchain.tools import tool
from app.services.task_service import get_task_service

@tool
async def create_task_tool(
    title: str,
    user_id: str,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new task"""
    service = get_task_service()
    return await service.create_task(user_id, {
        "title": title,
        "due_date": due_date
    })
```

**Implementation Location:**

```
backend/app/agents/tools/
├── data/          # tasks.py, todos.py, events.py
├── scheduling/    # planner.py, optimizer.py
├── search/        # web_search.py
├── integrations/  # calendar.py, email.py, canvas.py
└── communication/ # briefing.py, notifications.py
```

**After Implementation:**

- [ ] Test tool in isolation
- [ ] Test within workflow
- [ ] Update [EXAMPLES.md](../04-development/EXAMPLES.md) if new domain

---

### 📊 Agent Workflow Work

**When:** Creating or modifying LangGraph workflows

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 5.2: "Agent System"
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - "Agent System Architecture"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - `WorkflowState`, `WorkflowType`
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Workflow pattern

**Workflow Requirements:**

- ✅ Error boundaries around all operations
- ✅ State checkpointing for recovery
- ✅ Idempotent where possible
- ✅ Timeout handling
- ✅ Proper logging with correlation IDs

**Implementation Location:**

- `backend/app/agents/graphs/{name}_graph.py`

**Workflow Structure:**

```python
from langgraph.graph import StateGraph
from app.agents.core.state.workflow_container import WorkflowState

def create_my_workflow():
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("respond", respond_node)

    # Add edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "execute")
    workflow.add_edge("execute", "respond")

    return workflow.compile()
```

**After Implementation:**

- [ ] Add workflow tests
- [ ] Test error boundaries
- [ ] Update [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) workflow list

---

### 🔐 Security Work

**When:** Implementing authentication, authorization, or encryption

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 3: "Security (Non-Negotiable)"
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - Security section
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - Auth interfaces
- **[PITFALLS.md](../04-development/PITFALLS.md)** - Security pitfalls

**Security Requirements:**

- ✅ All OAuth tokens encrypted with KMS
- ✅ Supabase Auth for all endpoints
- ✅ RLS policies on all tables
- ✅ Input validation via Pydantic
- ❌ NEVER log PII or tokens
- ❌ NEVER skip authentication checks

**Implementation Location:**

- Auth: `backend/app/core/auth/`
- Encryption: `backend/app/security/encryption.py`
- Token management: `backend/app/services/auth/`

**Security Checklist:**

- [ ] Uses parameterized queries only
- [ ] Validates all input
- [ ] Encrypts sensitive data at rest
- [ ] Uses HTTPS for all external calls
- [ ] Implements rate limiting

---

### 🗄️ Database Migration Work

**When:** Creating or modifying database schema

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 1.2: "Data Layer"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - Database schemas section
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - Migration section

**Migration Requirements:**

- ✅ All migrations via Supabase SQL
- ✅ Include rollback notes in comments
- ✅ Update RLS policies
- ✅ Never mutate schema without migration

**Pattern:**

```sql
-- Migration: add_task_tags_table
-- Date: 11/05/25
-- Description: Create tags system for tasks

CREATE TABLE task_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for performance
CREATE INDEX idx_task_tags_task_id ON task_tags(task_id);

-- RLS policies
ALTER TABLE task_tags ENABLE ROW LEVEL SECURITY;

CREATE POLICY task_tags_user_policy ON task_tags
    USING (task_id IN (
        SELECT id FROM tasks WHERE user_id = auth.uid()
    ));

-- Rollback:
-- DROP TABLE task_tags CASCADE;
```

**After Implementation:**

- [ ] Test migration on dev database
- [ ] Update [INTERFACES.md](../02-architecture/INTERFACES.md) schemas
- [ ] Update repository layer
- [ ] Document in [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)

---

### 🧪 Testing Work

**When:** Writing or modifying tests

**Required Reading:**

- **[TESTING.md](../04-development/TESTING.md)** - Complete test strategy
- **[RULES.md](../02-architecture/RULES.md)** - Section 8: "Testing Requirements"
- **[INTERFACES.md](../02-architecture/INTERFACES.md)** - Data contracts to test
- **[EXAMPLES.md](../04-development/EXAMPLES.md)** - Test patterns

**Test Categories:**

1. **Unit tests** - Business logic, pure functions
2. **Integration tests** - API endpoints, database ops
3. **Workflow tests** - Agent workflows end-to-end
4. **Guardrail tests** - Critical invariants (always passing)

**Implementation Location:**

- Unit: `backend/tests/unit/`
- Integration: `backend/tests/integration/`
- Guardrails: `backend/tests/guardrails/`

**After Implementation:**

- [ ] All tests pass
- [ ] Coverage meets requirements
- [ ] Guardrail tests added for critical paths

---

### 📝 Documentation Work

**When:** Updating documentation

**Required Reading:**

- **[RULES.md](../02-architecture/RULES.md)** - Section 12: "When to Update This File"
- **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - Migration history section

**Documentation Hierarchy:**

1. **[RULES.md](../02-architecture/RULES.md)** - Rarely (backend enforcement rules only)
2. **[WEB_RULES.md](../04-development/WEB_RULES.md)** - Rarely (frontend enforcement rules only)
3. **[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)** - Frequently (patterns, migrations)
4. **[INTERFACES.md](../02-architecture/INTERFACES.md)** - When contracts change
5. **[EXAMPLES.md](../04-development/EXAMPLES.md)** - When new patterns emerge
6. **[PITFALLS.md](../04-development/PITFALLS.md)** - When bugs/edge cases discovered
7. **[TESTING.md](../04-development/TESTING.md)** - When test strategy changes
8. **[STYLES.md](../04-development/STYLES.md)** - When design tokens change

**Update Checklist:**

- [ ] Identify which doc needs update
- [ ] Make changes
- [ ] Update "Last Updated" date
- [ ] Cross-reference other docs if needed

---

## Context Loading Strategy

### For Small Changes (<100 lines)

**Load:**

- This file (CONTEXT.md)
- Relevant section from [RULES.md](../02-architecture/RULES.md)
- Relevant pattern from [EXAMPLES.md](../04-development/EXAMPLES.md)

### For Medium Changes (100-500 lines)

**Load:**

- This file (CONTEXT.md)
- Full [RULES.md](../02-architecture/RULES.md)
- Relevant sections from [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- Relevant contracts from [INTERFACES.md](../02-architecture/INTERFACES.md)
- [PITFALLS.md](../04-development/PITFALLS.md) for the domain

### For Large Changes (>500 lines or new features)

**Load:**

- This file (CONTEXT.md)
- Full [RULES.md](../02-architecture/RULES.md)
- Full [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- All relevant sections from [INTERFACES.md](../02-architecture/INTERFACES.md)
- [TESTING.md](../04-development/TESTING.md)
- [PITFALLS.md](../04-development/PITFALLS.md)
- [EXAMPLES.md](../04-development/EXAMPLES.md)

---

## Prompt Template

Use this template when working with Claude:

```markdown
## Context Loading

Reading CONTEXT.md for task type: [Your Task Type]

Loading required documentation:

- [ ] [Document 1]
- [ ] [Document 2]
- [ ] ...

## Task

[Your detailed task description]

## Implementation Requirements

Following:

- Interfaces defined in INTERFACES.md
- Patterns from EXAMPLES.md
- Rules from RULES.md section X
- Architecture from ARCHITECTURE.md section Y

## After Implementation

Will update:

- [ ] INTERFACES.md (if contracts changed)
- [ ] EXAMPLES.md (if new pattern)
- [ ] PITFALLS.md (if edge cases found)
- [ ] Tests (per TESTING.md)

---

[Your specific implementation details]
```

---

## Document Interdependencies

```
CONTEXT.md (this file)
    ↓ Routes to
[RULES.md] ← Backend enforcement rules
[WEB_RULES.md] ← Frontend enforcement rules
[ARCHITECTURE.md] ← System design & patterns
[INTERFACES.md] ← Data contracts
[EXAMPLES.md] ← Reference implementations
[PITFALLS.md] ← Known issues
[TESTING.md] ← Test strategy
[STYLES.md] ← Design system
```

**Navigation:**

- **Start here** for any task
- **End at** EXAMPLES.md for concrete patterns
- **Reference** INTERFACES.md for contracts
- **Check** PITFALLS.md before implementing
- **Test** per TESTING.md requirements

---

## Questions?

- **Unclear which context to load?** Find the closest match above
- **Multiple task types apply?** Load the union of all required reading
- **New task type not listed?** Add it to this file following the pattern

**Remember:** Context loading prevents missing critical rules. When in doubt, load more context, not less.
