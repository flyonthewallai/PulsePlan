# TESTING.md - Test Strategy & Requirements

**Last Updated:** 11/05/25
**Purpose:** Define testing strategy so Claude generates tests alongside code

> Comprehensive testing is non-negotiable for production systems. This document defines test categories, coverage requirements, and patterns to follow.

---

## Table of Contents

1. [Test Strategy Overview](#test-strategy-overview)
2. [Test Categories](#test-categories)
3. [Guardrail Tests (Critical)](#guardrail-tests-critical)
4. [Coverage Requirements](#coverage-requirements)
5. [Test File Conventions](#test-file-conventions)
6. [Test Patterns by Layer](#test-patterns-by-layer)
7. [Test Data & Fixtures](#test-data--fixtures)
8. [CI/CD Integration](#cicd-integration)

---

## Test Strategy Overview

### Philosophy

**Tests are executable specifications** - they document how the system should behave and prevent regressions.

**Three-Tier Strategy:**

1. **Unit Tests** - Fast, isolated, test single functions
2. **Integration Tests** - Test component interactions
3. **Guardrail Tests** - Critical invariants that MUST NEVER break

### Test Pyramid

```
     /\
    /  \  Guardrail Tests (5-10 critical tests)
   /____\
  /      \
 / Integration \ (100-200 tests)
/______________\
/              \
/   Unit Tests  \ (500+ tests)
/________________\
```

**Goal:** Fast feedback loop with high confidence

---

## Test Categories

### 1. Unit Tests

**What:** Test single function/method in isolation

**When:** For all business logic, pure functions, utilities

**Pattern:**
```python
import pytest
from app.services.task_service import TaskService
from app.database.repositories.task_repositories import TaskRepository


class MockTaskRepository:
    """Mock repository for testing"""
    async def create(self, data):
        return {"id": "test-123", **data}


async def test_create_task_with_valid_data():
    """Test task creation with valid input"""
    # Arrange
    service = TaskService(repo=MockTaskRepository())
    task_data = {
        "title": "Test task",
        "duration_minutes": 60
    }

    # Act
    result = await service.create_task("user-123", task_data)

    # Assert
    assert result["id"] == "test-123"
    assert result["title"] == "Test task"
    assert result["duration_minutes"] == 60
```

**Requirements:**
- Use mocks/fakes for dependencies
- Test happy path AND edge cases
- Test error handling
- Fast (<10ms per test)

---

### 2. Integration Tests

**What:** Test component interactions (API → Service → Repository → DB)

**When:** For all API endpoints, database operations, external API calls

**Pattern:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import test_db, authenticated_client


async def test_create_task_endpoint(authenticated_client, test_db):
    """Test task creation via API endpoint"""
    # Arrange
    task_data = {
        "title": "Integration test task",
        "due_date": "2025-01-10T23:59:00Z",
        "priority": "high"
    }

    # Act
    response = authenticated_client.post("/api/v1/tasks", json=task_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Integration test task"

    # Verify in database
    task = await test_db.get_task(data["data"]["id"])
    assert task is not None
    assert task["priority"] == "high"
```

**Requirements:**
- Use test database (separate from dev/prod)
- Clean up after each test
- Test full request/response cycle
- Test authentication/authorization
- Moderate speed (100-500ms per test)

---

### 3. Guardrail Tests

**What:** Critical invariants that protect system integrity

**When:** For mission-critical business rules

**Pattern:**
```python
import pytest
from app.scheduler.core.scheduler import schedule_tasks
from tests.fixtures.scheduling import create_test_tasks, create_test_user_context


@pytest.mark.guardrail
async def test_no_overlapping_timeblocks():
    """
    GUARDRAIL: Schedules MUST NOT contain overlapping timeblocks

    This is a critical invariant. If this test fails, the scheduler is broken.
    """
    # Arrange
    tasks = create_test_tasks(count=10)
    user_context = create_test_user_context()

    # Act
    schedule = await schedule_tasks(tasks, user_context)

    # Assert - No two timeblocks overlap
    time_slots = schedule.time_slots
    for i, slot1 in enumerate(time_slots):
        for slot2 in time_slots[i+1:]:
            assert not _timeslots_overlap(slot1, slot2), \
                f"Overlapping slots detected: {slot1} and {slot2}"


def _timeslots_overlap(slot1, slot2) -> bool:
    """Check if two timeslots overlap"""
    return (
        slot1.start_time < slot2.end_time and
        slot2.start_time < slot1.end_time
    )
```

**Requirements:**
- Must run on every PR
- Must pass 100% of the time
- Failure blocks merge
- Clear, descriptive failure messages

---

## Guardrail Tests (Critical)

### Scheduling Engine Guardrails

**MUST enforce:**

1. **No Overlapping Timeblocks**
   ```python
   @pytest.mark.guardrail
   async def test_no_overlapping_timeblocks():
       # Schedule must not have overlaps
   ```

2. **Respect User-Defined Rules**
   ```python
   @pytest.mark.guardrail
   async def test_respects_hard_constraints():
       # All hard constraints must be satisfied
   ```

3. **Solver Timeout**
   ```python
   @pytest.mark.guardrail
   async def test_solver_completes_within_timeout():
       # Must complete within 5 seconds
   ```

4. **Deterministic Output**
   ```python
   @pytest.mark.guardrail
   async def test_scheduling_is_deterministic():
       # Same input → same output
   ```

### Authentication Guardrails

1. **All Protected Routes Require Auth**
   ```python
   @pytest.mark.guardrail
   async def test_protected_routes_require_authentication():
       # Unauthenticated requests must be rejected
   ```

2. **RLS Policies Enforced**
   ```python
   @pytest.mark.guardrail
   async def test_users_cannot_access_other_users_data():
       # User A cannot see User B's data
   ```

### Data Integrity Guardrails

1. **No Data Loss on Sync**
   ```python
   @pytest.mark.guardrail
   async def test_calendar_sync_preserves_all_events():
       # Syncing must not lose events
   ```

2. **Idempotency**
   ```python
   @pytest.mark.guardrail
   async def test_duplicate_requests_are_idempotent():
       # Same idempotency key → same result
   ```

---

## Coverage Requirements

### By Component

| Component | Unit Coverage | Integration Coverage | Notes |
|-----------|--------------|---------------------|-------|
| **Scheduling Engine** | 100% | 90% | Mission-critical |
| **Intent Classification** | 100% | 90% | Core NLU pipeline |
| **API Endpoints** | 80% | 100% | All endpoints tested |
| **Repositories** | 80% | 90% | Database layer |
| **Services** | 90% | 80% | Business logic |
| **Agent Tools** | 80% | 90% | LangGraph tools |
| **Utilities** | 80% | N/A | Helper functions |

### Enforcement

```bash
# Run with coverage
pytest --cov=app --cov-report=html --cov-fail-under=80

# Check coverage by component
pytest --cov=app/scheduler --cov-fail-under=100  # Scheduling: 100%
pytest --cov=app/agents --cov-fail-under=90      # Agents: 90%
pytest --cov=app/services --cov-fail-under=90    # Services: 90%
```

---

## Test File Conventions

### Directory Structure

```
backend/tests/
├── unit/                    # Unit tests
│   ├── services/
│   ├── agents/
│   ├── scheduler/
│   └── utils/
├── integration/             # Integration tests
│   ├── api/
│   ├── database/
│   └── workflows/
├── guardrails/              # Critical invariant tests
│   ├── test_scheduling_invariants.py
│   ├── test_auth_invariants.py
│   └── test_data_integrity.py
├── fixtures/                # Test data and fixtures
│   ├── scheduling.py
│   ├── tasks.py
│   └── users.py
└── conftest.py              # Shared pytest configuration
```

### Naming Conventions

**Test Files:**
- Format: `test_{module_name}.py`
- Example: `test_task_service.py`, `test_scheduling.py`

**Test Functions:**
- Format: `test_{function_name}_{scenario}`
- Example: `test_create_task_with_valid_data()`
- Example: `test_create_task_with_missing_title_raises_error()`

**Test Classes (optional):**
- Format: `Test{ComponentName}`
- Example: `class TestTaskService:`

### Markers

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.guardrail      # Critical invariant
@pytest.mark.slow           # Slow test (>1s)
@pytest.mark.skip           # Skip (with reason)
@pytest.mark.parametrize    # Parameterized test
```

**Run specific markers:**
```bash
pytest -m unit              # Run only unit tests
pytest -m guardrail         # Run only guardrail tests
pytest -m "not slow"        # Skip slow tests
```

---

## Test Patterns by Layer

### Repository Tests

```python
import pytest
from app.database.repositories.task_repositories import TaskRepository


class MockSupabaseClient:
    """Mock Supabase client"""
    def table(self, name):
        return self

    def select(self, *args):
        return self

    def eq(self, field, value):
        return self

    def execute(self):
        class Response:
            data = [{"id": "test-123", "title": "Test"}]
        return Response()


async def test_get_tasks_by_user():
    """Test fetching tasks for a user"""
    # Arrange
    repo = TaskRepository()
    repo.supabase = MockSupabaseClient()

    # Act
    tasks = await repo.get_by_user("user-123")

    # Assert
    assert len(tasks) > 0
    assert tasks[0]["id"] == "test-123"
```

### Service Tests

```python
import pytest
from app.services.task_service import TaskService


class MockTaskRepository:
    async def create(self, data):
        return {"id": "created-123", **data}

    async def get_by_id(self, task_id):
        return {"id": task_id, "title": "Test"}


async def test_create_task_applies_business_rules():
    """Test that service applies validation rules"""
    # Arrange
    service = TaskService(repo=MockTaskRepository())

    # Act
    result = await service.create_task("user-123", {
        "title": "  Test Task  ",  # Has whitespace
        "duration_minutes": 60
    })

    # Assert
    assert result["title"] == "Test Task"  # Whitespace trimmed
```

### API Endpoint Tests

```python
import pytest
from fastapi.testclient import TestClient


async def test_create_task_endpoint_returns_201(authenticated_client):
    """Test task creation returns 201 Created"""
    response = authenticated_client.post("/api/v1/tasks", json={
        "title": "API Test Task",
        "priority": "high"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


async def test_create_task_endpoint_requires_auth(client):
    """Test that endpoint requires authentication"""
    response = client.post("/api/v1/tasks", json={
        "title": "Test"
    })

    assert response.status_code == 401  # Unauthorized
```

### Agent Workflow Tests

```python
import pytest
from app.agents.orchestrator import AgentOrchestrator
from app.agents.agent_models import WorkflowType


async def test_scheduling_workflow_end_to_end(test_db, test_user):
    """Test complete scheduling workflow"""
    # Arrange
    orchestrator = AgentOrchestrator()
    request = {
        "user_id": test_user.id,
        "message": "Schedule my week",
        "workflow_type": WorkflowType.SCHEDULING
    }

    # Act
    result = await orchestrator.execute_workflow(request)

    # Assert
    assert result["success"] is True
    assert "scheduled_tasks" in result["structured_data"]
    assert len(result["structured_data"]["scheduled_tasks"]) > 0
```

---

## Test Data & Fixtures

### Shared Fixtures (conftest.py)

```python
import pytest
from app.config.database.supabase import get_supabase_client


@pytest.fixture
async def test_db():
    """Provide test database client"""
    db = get_supabase_client()
    yield db
    # Cleanup after test
    await cleanup_test_data(db)


@pytest.fixture
def test_user():
    """Create test user"""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "timezone": "America/Los_Angeles"
    }


@pytest.fixture
def authenticated_client(test_user):
    """Provide authenticated test client"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {create_test_token(test_user)}"
    return client
```

### Domain-Specific Fixtures

```python
# tests/fixtures/scheduling.py

from datetime import datetime, timedelta
from typing import List, Dict, Any


def create_test_tasks(count: int = 5) -> List[Dict[str, Any]]:
    """Create test tasks for scheduling"""
    base_time = datetime.now()
    return [
        {
            "id": f"task-{i}",
            "title": f"Test Task {i}",
            "duration_minutes": 60,
            "due_date": base_time + timedelta(days=i),
            "priority": "medium"
        }
        for i in range(count)
    ]


def create_test_user_context() -> Dict[str, Any]:
    """Create test user context"""
    return {
        "user_id": "test-user",
        "timezone": "UTC",
        "working_hours": {"start": "09:00", "end": "17:00"},
        "hobbies": ["reading", "coding"],
        "scheduling_preferences": {}
    }
```

---

## CI/CD Integration

### Pre-commit Checks

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run fast tests before commit
pytest -m "unit and not slow" --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Fix tests before committing."
    exit 1
fi

echo "✅ Tests passed"
```

### Pull Request Checks

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run guardrail tests
        run: pytest -m guardrail --tb=short

      - name: Run unit tests with coverage
        run: pytest -m unit --cov=app --cov-fail-under=80

      - name: Run integration tests
        run: pytest -m integration

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Deployment Gates

**Before deploying to production:**
- [ ] All guardrail tests pass (100%)
- [ ] Unit test coverage >= 80%
- [ ] Integration tests pass
- [ ] No failing tests in main branch
- [ ] Code review approved

---

## Test Maintenance

### When to Update Tests

**Always update tests when:**
- ✅ Modifying existing functionality
- ✅ Adding new features
- ✅ Fixing bugs (add regression test)
- ✅ Changing interfaces

**Red flags:**
- ❌ Deleting tests to make build pass
- ❌ Skipping tests without reason
- ❌ Commenting out failing tests
- ❌ Coverage decreasing

### Test Smell Checklist

**Bad tests:**
- ❌ Tests that depend on external services
- ❌ Tests that depend on specific test order
- ❌ Tests that take >5 seconds
- ❌ Tests with unclear assertions
- ❌ Tests that test implementation details

**Good tests:**
- ✅ Fast, isolated, repeatable
- ✅ Clear arrange-act-assert structure
- ✅ Test behavior, not implementation
- ✅ Descriptive names and failure messages

---

## Testing Checklist

**For every feature implementation:**

- [ ] Unit tests written for business logic
- [ ] Integration tests for API endpoints
- [ ] Guardrail tests for critical invariants (if applicable)
- [ ] Test coverage meets requirements
- [ ] All tests pass locally
- [ ] Tests added to appropriate directory
- [ ] Fixtures created if needed
- [ ] Test data cleaned up after tests

**Before merging PR:**

- [ ] All guardrail tests pass
- [ ] Coverage check passes
- [ ] No skipped tests without reason
- [ ] Test failures investigated and fixed

---

## Questions?

- **Test strategy unclear?** See [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Test patterns unclear?** See [EXAMPLES.md](./EXAMPLES.md)
- **Contract testing?** See [INTERFACES.md](./INTERFACES.md)

**Remember:** Tests are not optional. They are executable specifications that prevent regressions and document expected behavior.
