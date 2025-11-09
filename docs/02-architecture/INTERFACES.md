# INTERFACES.md - Data Contracts & API Specifications

**Last Updated:** 11/05/25
**Purpose:** Explicit interface contracts to prevent implementation gaps

> This document defines all data structures, API contracts, and type definitions used across PulsePlan. All implementations MUST conform to these interfaces.

---

## Table of Contents

1. [Core Data Types](#core-data-types)
2. [Agent System Interfaces](#agent-system-interfaces)
3. [Scheduling System Interfaces](#scheduling-system-interfaces)
4. [Repository Interfaces](#repository-interfaces)
5. [API Request/Response Contracts](#api-requestresponse-contracts)
6. [Database Schemas](#database-schemas)
7. [External API Expectations](#external-api-expectations)

---

## Core Data Types

### UserContext

Complete user context for personalized operations.

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class UserContext:
    """User context aggregated from database"""
    user_id: str
    email: str
    full_name: Optional[str]
    timezone: str
    working_hours: Dict[str, Any]  # {start: "09:00", end: "17:00"}
    subscription_status: str  # "free", "premium"

    # Preferences
    hobbies: List[str]
    courses: List[Dict[str, Any]]
    scheduling_preferences: Dict[str, Any]

    # Constraints
    calendar_busy_times: List[Dict[str, datetime]]
    recurring_commitments: List[Dict[str, Any]]
```

**Used by:**
- Agent workflows
- Scheduling engine
- Briefing generation

---

## Agent System Interfaces

### IntentRequest

Input to intent classification system.

```python
@dataclass
class IntentRequest:
    """Request for intent classification"""
    user_id: str
    raw_prompt: str
    conversation_id: Optional[str]
    conversation_history: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
    timestamp: datetime

    # Optional context
    active_gate: Optional[str]  # Pending confirmation gate
    last_action_id: Optional[str]
```

### IntentResponse

Output from intent classification.

```python
@dataclass
class IntentResponse:
    """Result of intent classification"""
    intent_type: str  # "create_task", "schedule_week", "get_briefing", etc.
    confidence: float  # 0.0 to 1.0

    # Extracted parameters
    extracted_params: Dict[str, Any]

    # Secondary intents (for ambiguous cases)
    secondary_intents: List[Dict[str, Any]]  # [{"intent": "...", "confidence": 0.7}]

    # Routing decision
    workflow_type: str  # Maps to WorkflowType enum
    requires_clarification: bool
    clarification_questions: List[str]
```

**Contract:**
- `confidence >= 0.85` → Execute directly
- `0.60 <= confidence < 0.85` → Request confirmation (SLO gate)
- `confidence < 0.60` → Request clarification

### WorkflowState

State object passed between workflow nodes.

```python
from typing import Any, Dict, List
from enum import Enum

class WorkflowType(Enum):
    NATURAL_LANGUAGE = "natural_language"
    SCHEDULING = "scheduling"
    CALENDAR = "calendar"
    TASK = "task"
    BRIEFING = "briefing"
    EMAIL = "email"
    SEARCH = "search"

@dataclass
class WorkflowState:
    """State passed through LangGraph workflow"""
    user_id: str
    workflow_type: WorkflowType

    # Input
    user_message: str
    intent: str
    parameters: Dict[str, Any]

    # Context
    user_context: Optional[UserContext]
    conversation_history: List[Dict[str, str]]

    # Execution
    current_step: str
    errors: List[str]
    intermediate_results: Dict[str, Any]

    # Output
    final_response: Optional[str]
    structured_data: Optional[Dict[str, Any]]

    # Metadata
    execution_time_ms: int
    llm_calls_made: int
```

### ActionRecord

Persistent record of user actions for idempotency and continuation.

```python
@dataclass
class ActionRecord:
    """Database record for action tracking"""
    id: str  # UUID
    user_id: str
    intent: str
    params: Dict[str, Any]
    status: str  # "draft", "pending_confirmation", "executing", "completed", "failed"

    # Idempotency
    idempotency_key: Optional[str]

    # Execution
    external_refs: Optional[Dict[str, Any]]  # IDs of created resources
    error_message: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Continuation
    user_message: Optional[str]  # Original user prompt
```

---

## Scheduling System Interfaces

### SchedulingRequest

Input to intelligent scheduling system.

```python
@dataclass
class SchedulingRequest:
    """Request to schedule tasks for user"""
    user_id: str

    # Time window
    start_date: datetime
    end_date: datetime

    # Tasks to schedule
    task_ids: List[str]

    # Constraints
    respect_calendar_conflicts: bool = True
    respect_working_hours: bool = True
    allow_partial_schedule: bool = False

    # Optimization preferences
    optimization_goals: List[str]  # ["minimize_fragmentation", "respect_priorities"]
    max_solve_time_seconds: int = 5
```

### SchedulingResponse

Output from scheduling engine.

```python
@dataclass
class TimeSlot:
    """Scheduled time slot for a task"""
    task_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int

    # Metadata
    priority_score: float
    fragmentation_score: float


@dataclass
class SchedulingResponse:
    """Result of scheduling operation"""
    status: str  # "success", "partial", "infeasible"

    # Scheduled slots
    time_slots: List[TimeSlot]

    # Unscheduled tasks (if partial or infeasible)
    unscheduled_task_ids: List[str]
    unscheduled_reasons: Dict[str, str]

    # Metrics
    optimality_score: float  # 0.0 to 1.0
    total_scheduled_hours: float
    fragmentation_score: float

    # Constraints
    constraints_satisfied: List[str]
    constraints_violated: List[str]

    # Execution
    solve_time_ms: int
    solver_status: str  # "OPTIMAL", "FEASIBLE", "INFEASIBLE"
```

**Guarantees:**
- `status == "success"` → All tasks scheduled, respects all hard constraints
- `status == "partial"` → Some tasks scheduled, some violate constraints
- `status == "infeasible"` → No valid schedule found
- `solve_time_ms <= max_solve_time_seconds * 1000`

### SchedulingRule

User-defined scheduling constraint.

```python
@dataclass
class SchedulingRule:
    """User scheduling preference/constraint"""
    rule_type: str  # "no_work_before", "no_work_after", "break_required", "max_daily_hours"
    priority: str  # "hard" (must satisfy), "soft" (prefer to satisfy)
    parameters: Dict[str, Any]

    # Examples:
    # {"rule_type": "no_work_before", "priority": "hard", "parameters": {"time": "09:00"}}
    # {"rule_type": "max_daily_hours", "priority": "soft", "parameters": {"hours": 8}}
```

---

## Repository Interfaces

All repositories extend `BaseRepository` which provides:

### BaseRepository Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseRepository(ABC):
    """Base repository with standard CRUD operations"""

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the database table name"""
        pass

    # Standard CRUD
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get single record by ID"""
        pass

    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all records with optional filtering"""
        pass

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record"""
        pass

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing record"""
        pass

    async def delete(self, id: str) -> bool:
        """Delete record"""
        pass

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records"""
        pass

    async def exists(self, id: str) -> bool:
        """Check if record exists"""
        pass
```

**Contract:**
- All methods are `async`
- All raise `RepositoryError` on database failures
- `get_by_id` returns `None` if not found (doesn't raise)
- `update` returns `None` if record doesn't exist
- `delete` returns `False` if record doesn't exist

---

## API Request/Response Contracts

### Standard API Response Format

All API endpoints return this format:

```python
# Success response
{
    "success": true,
    "data": {...},  # Actual response data
    "message": "Operation completed successfully",
    "timestamp": "11/05/25T12:00:00Z"
}

# Error response
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid task duration",
        "details": {...}
    },
    "timestamp": "11/05/25T12:00:00Z"
}
```

### Agent Chat Request

```python
{
    "message": "Schedule my week",
    "conversation_id": "uuid-here",  # Optional
    "stream": false  # Optional, default false
}
```

### Agent Chat Response

```python
{
    "success": true,
    "data": {
        "response": "I've scheduled your week...",
        "conversation_id": "uuid-here",
        "workflow_type": "scheduling",
        "structured_data": {
            "scheduled_tasks": [...],
            "calendar_events": [...]
        },
        "requires_confirmation": false,
        "confirmation_token": null
    }
}
```

### Task Creation Request

```python
{
    "title": "Complete project report",
    "description": "Write final report for CS101",
    "due_date": "2025-01-10T23:59:00Z",
    "duration_minutes": 120,
    "priority": "high",  # "low", "medium", "high"
    "tags": ["school", "cs101"],
    "canvas_assignment_id": "12345"  # Optional
}
```

### Task Response

```python
{
    "success": true,
    "data": {
        "id": "task-uuid",
        "title": "Complete project report",
        "status": "pending",
        "scheduled_at": "2025-01-08T14:00:00Z",  # If scheduled
        "created_at": "11/05/25T12:00:00Z",
        "updated_at": "11/05/25T12:00:00Z",
        ...
    }
}
```

---

## Database Schemas

### Core Tables

**users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    timezone TEXT DEFAULT 'UTC',
    working_hours JSONB DEFAULT '{"start": "09:00", "end": "17:00"}',
    subscription_status TEXT DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**tasks**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    priority TEXT DEFAULT 'medium',  -- low, medium, high
    due_date TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    canvas_assignment_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
```

**calendar_links**
```sql
CREATE TABLE calendar_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    calendar_event_id UUID REFERENCES calendar_events(id) ON DELETE CASCADE,
    source_of_truth TEXT NOT NULL,  -- 'calendar', 'task', 'latest_update'
    sync_status TEXT DEFAULT 'synced',  -- synced, pending_push, conflict
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**action_records** (NLU pipeline)
```sql
CREATE TABLE action_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    intent TEXT NOT NULL,
    params JSONB NOT NULL,
    status TEXT DEFAULT 'draft',  -- draft, pending_confirmation, executing, completed, failed
    idempotency_key TEXT UNIQUE,
    user_message TEXT,
    external_refs JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_action_records_user_id ON action_records(user_id);
CREATE INDEX idx_action_records_status ON action_records(status);
CREATE INDEX idx_action_records_idempotency_key ON action_records(idempotency_key);
```

**Complete schema:** See `backend/app/database/schemas/schema.sql`

---

## External API Expectations

### OR-Tools CP-SAT Solver

**Input Format:**
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Variables
start_vars = {}  # task_id -> IntVar (start time in minutes from epoch)
end_vars = {}    # task_id -> IntVar
interval_vars = {}  # task_id -> IntervalVar

# Constraints
model.Add(start_vars[task_id] >= earliest_start)
model.Add(end_vars[task_id] <= deadline)

# Objective: Minimize fragmentation
model.Minimize(sum(fragmentation_penalties))
```

**Timeout Requirement:**
- **MUST** complete within 5 seconds
- Use `solver.parameters.max_time_in_seconds = 5`

**Error Handling:**
```python
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    # Best solution found
elif status == cp_model.FEASIBLE:
    # Valid solution found, may not be optimal
elif status == cp_model.INFEASIBLE:
    # No solution exists
elif status == cp_model.MODEL_INVALID:
    # Constraint error
else:
    # UNKNOWN - timeout or other issue
```

### OpenAI API

**Intent Classification Call:**
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.0,  # Deterministic
    max_tokens=150,
    response_format={"type": "json_object"}  # Structured output
)

# Expected response
{
    "intent": "create_task",
    "confidence": 0.92,
    "parameters": {
        "title": "...",
        "due_date": "..."
    }
}
```

**Token Usage Tracking:**
- Track `usage.prompt_tokens`, `usage.completion_tokens`
- Log to `llm_usage` table
- Enforce quota limits (see `app/services/usage/usage_limiter.py`)

### Google Calendar API

**Event Creation:**
```python
event = {
    'summary': 'Task: Complete project',
    'description': 'Scheduled via PulsePlan',
    'start': {
        'dateTime': '2025-01-08T14:00:00-08:00',
        'timeZone': 'America/Los_Angeles'
    },
    'end': {
        'dateTime': '2025-01-08T16:00:00-08:00',
        'timeZone': 'America/Los_Angeles'
    }
}

result = service.events().insert(
    calendarId='primary',
    body=event
).execute()
```

**Rate Limits:**
- 1000 queries per 100 seconds per user
- Implement exponential backoff on 429 errors

---

## Type Definitions

### Python Type Aliases

```python
from typing import TypeAlias, Dict, Any, List
from datetime import datetime

# Common types
UserId: TypeAlias = str
TaskId: TypeAlias = str
ConversationId: TypeAlias = str

# JSON types
JsonDict: TypeAlias = Dict[str, Any]
JsonList: TypeAlias = List[Any]

# Timestamps
ISOTimestamp: TypeAlias = str  # "11/05/25T12:00:00Z"
UnixTimestamp: TypeAlias = int  # Seconds since epoch
```

### TypeScript Interfaces (Frontend)

```typescript
// User
interface User {
  id: string;
  email: string;
  full_name?: string;
  timezone: string;
  subscription_status: 'free' | 'premium';
}

// Task
interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;  // ISO timestamp
  scheduled_at?: string;
  duration_minutes?: number;
  created_at: string;
  updated_at: string;
}

// API Response
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}
```

---

## Validation Rules

### Task Validation

```python
from pydantic import BaseModel, validator

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    priority: str = "medium"

    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title must be < 200 characters')
        return v.strip()

    @validator('duration_minutes')
    def duration_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duration must be positive')
        if v is not None and v > 1440:  # 24 hours
            raise ValueError('Duration cannot exceed 24 hours')
        return v

    @validator('priority')
    def priority_valid(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('Priority must be low, medium, or high')
        return v
```

---

## Contract Enforcement

**When implementing:**
1. Import types from this document
2. Add type hints to all functions
3. Validate inputs against schemas
4. Return outputs matching defined formats

**Example:**
```python
from docs.INTERFACES import UserContext, SchedulingRequest, SchedulingResponse

async def schedule_tasks(
    request: SchedulingRequest,
    user_context: UserContext
) -> SchedulingResponse:
    """
    Conforms to INTERFACES.md contracts
    """
    # Implementation
    ...
```

**Violations:**
- Missing type hints → Fails mypy check
- Wrong return type → Caught by type checker
- Invalid data structure → Pydantic validation error

---

## Questions?

- **Data flow unclear?** See [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Implementation patterns?** See [EXAMPLES.md](./EXAMPLES.md)
- **Testing contracts?** See [TESTING.md](./TESTING.md)

**Remember:** These interfaces are contracts. Breaking them breaks the system.
