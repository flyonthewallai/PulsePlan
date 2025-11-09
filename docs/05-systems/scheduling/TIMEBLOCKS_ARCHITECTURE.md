# Timeblocks Architecture

**Version:** 1.0
**Last Updated:** 2025-10-28
**Status:** Implemented

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Database Schema](#database-schema)
4. [Data Model](#data-model)
5. [Repository Layer](#repository-layer)
6. [View Layer](#view-layer)
7. [Integration Points](#integration-points)
8. [Migration Strategy](#migration-strategy)
9. [Future Enhancements](#future-enhancements)

---

## 1. Overview

### Purpose

The timeblocks system provides a **normalized temporal scheduling architecture** for PulsePlan, separating the concept of "what needs to be done" (tasks) from "when it happens" (timeblocks). This enables:

- **Multi-session task scheduling**: Break large tasks into multiple work sessions
- **Rich scheduling metadata**: Store AI agent reasoning, completion tracking, and analytics
- **Flexible time management**: Support habits, breaks, focus sessions, and other non-task timeblocks
- **Performance optimization**: Efficient querying and indexing of temporal data

### Conceptual Model

```
Before:  tasks (what + when combined)
         calendar_events (external readonly)

After:   tasks (what needs doing)
         timeblocks (when and why it happens)
         calendar_events (external readonly)
         v_timeblocks (unified view of all temporal data)
```

---

## 2. Architecture Design

### 2.1 Conceptual Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Agents, Scheduler, API Endpoints)                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                           │
│  TimeblocksRepository (CRUD + Query Operations)             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     View Layer                               │
│  v_timeblocks (Unified Read View)                           │
│  ├── timeblocks (internal scheduling)                       │
│  ├── tasks (legacy compatibility)                           │
│  └── calendar_events (external readonly)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│  PostgreSQL + RLS Policies                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Design Principles

1. **Separation of Concerns**: Tasks define WHAT, timeblocks define WHEN
2. **Source of Truth**: Timeblocks table is the primary source for internal scheduling
3. **Backward Compatibility**: Legacy tasks with start_date/end_date still work via view union
4. **Performance First**: Optimized indexes and views for efficient queries
5. **RLS Security**: Row-level security ensures users only access their own data

---

## 3. Database Schema

### 3.1 Timeblocks Table

```sql
CREATE TABLE timeblocks (
  -- Primary Key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Ownership & Relationships
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,

  -- Core Temporal Data
  title TEXT NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  all_day BOOLEAN DEFAULT false,

  -- Classification
  type TEXT NOT NULL DEFAULT 'task_block' CHECK (
    type IN ('task_block', 'habit', 'focus', 'break', 'meeting',
             'class', 'study', 'exam', 'assignment', 'project',
             'hobby', 'admin')
  ),

  status TEXT NOT NULL DEFAULT 'scheduled' CHECK (
    status IN ('scheduled', 'completed', 'missed', 'cancelled', 'in_progress')
  ),

  source TEXT NOT NULL DEFAULT 'pulse' CHECK (
    source IN ('pulse', 'external', 'manual', 'agent', 'scheduler')
  ),

  -- Rich Metadata
  agent_reasoning JSONB DEFAULT NULL,  -- AI decision rationale
  location TEXT,
  notes TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,  -- Flexible additional data

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Constraints
  CONSTRAINT timeblocks_valid_time_range CHECK (end_time > start_time)
);
```

### 3.2 Indexes

```sql
-- Primary access pattern: user + time range
CREATE INDEX idx_timeblocks_user_time
  ON timeblocks(user_id, start_time, end_time);

-- Task relationship lookup
CREATE INDEX idx_timeblocks_task_id
  ON timeblocks(task_id) WHERE task_id IS NOT NULL;

-- Status filtering
CREATE INDEX idx_timeblocks_user_status
  ON timeblocks(user_id, status);

-- Efficient range queries using GiST
CREATE INDEX idx_timeblocks_time_range
  ON timeblocks USING gist (tstzrange(start_time, end_time));
```

### 3.3 Row-Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE timeblocks ENABLE ROW LEVEL SECURITY;

-- Users can only access their own timeblocks
CREATE POLICY "Users can view their own timeblocks"
  ON timeblocks FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own timeblocks"
  ON timeblocks FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own timeblocks"
  ON timeblocks FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own timeblocks"
  ON timeblocks FOR DELETE
  USING (auth.uid() = user_id);
```

---

## 4. Data Model

### 4.1 Type Enumeration

#### Timeblock Types

| Type | Description | Use Case |
|------|-------------|----------|
| `task_block` | General task work session | Default for scheduled task work |
| `habit` | Recurring habit/routine | Daily meditation, exercise |
| `focus` | Dedicated focus session | Deep work blocks |
| `break` | Rest period | Pomodoro breaks |
| `meeting` | Scheduled meeting | Team sync, 1-on-1s |
| `class` | Educational session | Lectures, seminars |
| `study` | Study session | Exam prep, reading |
| `exam` | Examination | Tests, quizzes |
| `assignment` | Assignment work | Homework, projects |
| `project` | Project work | Multi-session projects |
| `hobby` | Hobby time | Personal interests |
| `admin` | Administrative tasks | Planning, organization |

#### Status Values

| Status | Description | Transitions |
|--------|-------------|-------------|
| `scheduled` | Planned, not yet started | → in_progress, cancelled |
| `in_progress` | Currently active | → completed, missed |
| `completed` | Successfully finished | Terminal state |
| `missed` | Not completed on time | Terminal state |
| `cancelled` | Cancelled before start | Terminal state |

#### Source Values

| Source | Description | Created By |
|--------|-------------|-----------|
| `pulse` | PulsePlan system | Core application |
| `agent` | AI agent | LangGraph workflows |
| `scheduler` | Scheduling engine | OR-Tools optimizer |
| `manual` | User created | Direct user action |
| `external` | External system | Sync services |

### 4.2 Metadata Structure

The `metadata` JSONB field supports flexible storage for domain-specific data:

```json
{
  "priority": "high",
  "course": "CS101",
  "course_id": "uuid",
  "tags": ["important", "deadline"],
  "recurrence": {
    "pattern": "weekly",
    "days": ["Mon", "Wed", "Fri"],
    "until": "2025-12-31"
  },
  "performance": {
    "actual_duration_minutes": 90,
    "productivity_score": 0.85,
    "interruptions": 2
  }
}
```

### 4.3 Agent Reasoning Structure

The `agent_reasoning` JSONB field captures AI decision-making:

```json
{
  "rationale": "Scheduled during optimal focus time based on user history",
  "confidence": 0.89,
  "alternatives_considered": 3,
  "constraints_applied": ["deadline_proximity", "energy_level", "no_conflicts"],
  "model_version": "scheduler-v2.1",
  "timestamp": "2025-10-28T14:30:00Z"
}
```

---

## 5. Repository Layer

### 5.1 TimeblocksRepository

Located in: `backend/app/database/timeblocks_repository.py`

#### Core CRUD Operations

```python
class TimeblocksRepository:
    """Repository for unified timeblocks view and timeblocks table management"""

    # Read Operations
    async def fetch_timeblocks(user_id, dt_from, dt_to) -> List[Dict]
    async def get_timeblock(timeblock_id, user_id) -> Optional[Dict]
    async def get_timeblocks_for_task(task_id, user_id) -> List[Dict]
    async def get_timeblocks_by_status(user_id, status, limit) -> List[Dict]

    # Write Operations
    async def create_timeblock(...) -> Dict
    async def update_timeblock(timeblock_id, user_id, updates) -> Optional[Dict]
    async def delete_timeblock(timeblock_id, user_id) -> bool

    # Convenience Methods
    async def mark_timeblock_completed(timeblock_id, user_id) -> Optional[Dict]
    async def get_calendar_link(...) -> Optional[Dict]
```

#### Usage Example

```python
from app.database.timeblocks_repository import get_timeblocks_repository

repo = get_timeblocks_repository()

# Create a timeblock
timeblock = await repo.create_timeblock(
    user_id="user-uuid",
    title="Work on CS101 Assignment",
    start_time=datetime(2025, 10, 29, 14, 0, tzinfo=timezone.utc),
    end_time=datetime(2025, 10, 29, 16, 0, tzinfo=timezone.utc),
    task_id="task-uuid",
    type="assignment",
    source="agent",
    agent_reasoning={
        "rationale": "Optimal time based on productivity patterns",
        "confidence": 0.87
    }
)

# Query timeblocks for a date range
timeblocks = await repo.fetch_timeblocks(
    user_id="user-uuid",
    dt_from=datetime(2025, 10, 28, 0, 0, tzinfo=timezone.utc),
    dt_to=datetime(2025, 11, 4, 0, 0, tzinfo=timezone.utc)
)

# Mark completed
await repo.mark_timeblock_completed(
    timeblock_id="timeblock-uuid",
    user_id="user-uuid"
)
```

### 5.2 Pydantic Model

Located in: `backend/app/database/models.py`

```python
class TimeblockModel(BaseDBModel):
    """Timeblock model for normalized temporal scheduling data"""

    # Required fields
    user_id: str
    title: str
    start_time: datetime
    end_time: datetime

    # Optional fields with defaults
    task_id: Optional[str] = None
    type: str = "task_block"
    status: str = "scheduled"
    source: str = "pulse"
    agent_reasoning: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    all_day: bool = False
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('end_time')
    def validate_time_range(cls, v, values):
        """Ensure end_time is after start_time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
```

Registered in `MODEL_REGISTRY` for dynamic access:

```python
MODEL_REGISTRY = {
    'users': UserModel,
    'tasks': TaskModel,
    'timeblocks': TimeblockModel,  # New entry
    # ... other models
}
```

---

## 6. View Layer

### 6.1 v_timeblocks Unified View

The `v_timeblocks` view provides a **unified read interface** combining three sources:

```sql
CREATE OR REPLACE VIEW v_timeblocks AS

-- Source 1: Internal timeblocks (from timeblocks table)
SELECT
    tb.id::text AS id,
    'timeblock'::text AS source,
    NULL::text AS provider,
    tb.user_id,
    tb.title,
    tb.start_time AS start_at,
    tb.end_time AS end_at,
    tb.all_day AS is_all_day,
    false AS readonly,  -- Internal timeblocks are editable
    tb.task_id,
    tb.notes AS description,
    tb.location,
    tb.type,
    tb.status,
    tb.source AS timeblock_source,
    tb.agent_reasoning,
    tb.metadata,
    NULL::uuid AS calendar_id_ref
FROM timeblocks tb
WHERE tb.status != 'cancelled'

UNION ALL

-- Source 2: Legacy tasks (for backward compatibility)
SELECT
    t.id::text AS id,
    'task'::text AS source,
    NULL::text AS provider,
    t.user_id,
    t.title,
    t.start_date AS start_at,
    t.end_date AS end_at,
    COALESCE(t.all_day, false) AS is_all_day,
    false AS readonly,
    t.id AS task_id,
    t.description,
    t.location,
    -- Map task type to timeblock type
    CASE
      WHEN t.kind = 'study' THEN 'study'
      WHEN t.kind = 'assignment' THEN 'assignment'
      WHEN t.kind = 'exam' THEN 'exam'
      WHEN t.kind = 'project' THEN 'project'
      WHEN t.kind = 'hobby' THEN 'hobby'
      WHEN t.kind = 'admin' THEN 'admin'
      ELSE 'task_block'
    END AS type,
    -- Map task status to timeblock status
    CASE
      WHEN t.status = 'completed' THEN 'completed'
      WHEN t.status = 'cancelled' THEN 'cancelled'
      WHEN t.status = 'in_progress' THEN 'in_progress'
      ELSE 'scheduled'
    END AS status,
    CASE
      WHEN t.source IN ('canvas', 'google', 'microsoft', 'apple') THEN 'external'
      ELSE 'pulse'
    END AS timeblock_source,
    NULL::jsonb AS agent_reasoning,
    jsonb_build_object(
      'legacy_task', true,
      'task_type', t.task_type,
      'priority', t.priority
    ) AS metadata,
    NULL::uuid AS calendar_id_ref
FROM tasks t
WHERE
    t.start_date IS NOT NULL
    AND t.end_date IS NOT NULL
    AND t.status NOT IN ('cancelled')
    -- Avoid duplicates with timeblocks
    AND NOT EXISTS (
        SELECT 1 FROM timeblocks tb WHERE tb.task_id = t.id
    )

UNION ALL

-- Source 3: External calendar events (readonly)
SELECT
    ce.id::text AS id,
    'calendar'::text AS source,
    ce.provider,
    ce.user_id,
    ce.title,
    ce.start_time AS start_at,
    ce.end_time AS end_at,
    COALESCE(ce.is_all_day, false) AS is_all_day,
    true AS readonly,  -- External events readonly by default
    NULL::uuid AS task_id,
    ce.description,
    ce.location,
    'external'::text AS type,
    CASE
      WHEN ce.is_cancelled THEN 'cancelled'
      ELSE 'scheduled'
    END AS status,
    'external'::text AS timeblock_source,
    NULL::jsonb AS agent_reasoning,
    jsonb_build_object(
      'provider', ce.provider,
      'external_id', ce.external_id,
      'calendar_id', ce.calendar_id
    ) AS metadata,
    ce.calendar_id_ref
FROM calendar_events ce
WHERE NOT COALESCE(ce.is_cancelled, false);
```

### 6.2 RPC Function

Optimized query function with calendar filtering:

```sql
CREATE FUNCTION get_timeblocks_for_user(
    p_user_id UUID,
    p_from TIMESTAMPTZ,
    p_to TIMESTAMPTZ
)
RETURNS TABLE (...) AS $$
    SELECT *
    FROM v_timeblocks vt
    WHERE vt.user_id = p_user_id
        AND vt.start_at < p_to
        AND vt.end_at > p_from
        -- Only include events from active calendars
        AND (
            vt.source != 'calendar'
            OR EXISTS (
                SELECT 1
                FROM calendar_calendars cc
                WHERE cc.id = vt.calendar_id_ref
                    AND cc.user_id = p_user_id
                    AND cc.is_active = true
            )
        )
    ORDER BY vt.start_at ASC;
$$;
```

### 6.3 View Schema

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| `id` | TEXT | All | Unique identifier (cast from UUID) |
| `source` | TEXT | All | 'timeblock', 'task', or 'calendar' |
| `provider` | TEXT | Calendar | 'google', 'microsoft', 'apple', or NULL |
| `provider_event_id` | TEXT | Calendar | External event ID |
| `provider_calendar_id` | TEXT | Calendar | External calendar ID |
| `user_id` | UUID | All | Owner user ID |
| `title` | TEXT | All | Display title |
| `start_at` | TIMESTAMPTZ | All | Start time |
| `end_at` | TIMESTAMPTZ | All | End time |
| `is_all_day` | BOOLEAN | All | All-day flag |
| `readonly` | BOOLEAN | All | Whether user can edit |
| `task_id` | UUID | Timeblock/Task | Parent task ID |
| `description` | TEXT | All | Description/notes |
| `location` | TEXT | All | Location string |
| `type` | TEXT | All | Timeblock type enum |
| `status` | TEXT | All | Status enum |
| `timeblock_source` | TEXT | All | Source system |
| `agent_reasoning` | JSONB | Timeblock | AI reasoning data |
| `metadata` | JSONB | All | Flexible metadata |
| `calendar_id_ref` | UUID | Calendar | Calendar table FK |

---

## 7. Integration Points

### 7.1 API Endpoints

**Endpoint:** `/api/v1/timeblocks`

Currently reads from `v_timeblocks` view. Future enhancements will add CRUD endpoints for the timeblocks table.

```python
@router.get("", response_model=TimeblockResponse)
async def get_timeblocks(
    from_dt: str = Query(..., alias="from"),
    to_dt: str = Query(..., alias="to"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get unified timeblocks for time range"""
    repo = get_timeblocks_repository()
    rows = await repo.fetch_timeblocks(user_id, start_time, end_time)
    # ... transform to API response
```

### 7.2 Agent Integration

LangGraph agents can create and manage timeblocks:

```python
from app.database.timeblocks_repository import get_timeblocks_repository

async def schedule_task_sessions(task_id: str, user_id: str):
    """Agent tool: Break task into optimal work sessions"""
    repo = get_timeblocks_repository()

    # Agent determines optimal scheduling
    sessions = await planning_logic(task_id)

    # Create timeblocks
    for session in sessions:
        await repo.create_timeblock(
            user_id=user_id,
            task_id=task_id,
            title=f"{task.title} - Session {session.number}",
            start_time=session.start,
            end_time=session.end,
            type="assignment",
            source="agent",
            agent_reasoning={
                "rationale": session.reasoning,
                "confidence": session.confidence
            }
        )
```

### 7.3 Scheduler Integration

The OR-Tools scheduling engine can output directly to timeblocks:

```python
from app.scheduler.core import run_schedule
from app.database.timeblocks_repository import get_timeblocks_repository

async def execute_schedule(user_id: str, horizon_days: int):
    """Run scheduler and persist timeblocks"""

    # Run optimization
    schedule_result = await run_schedule(user_id, horizon_days)

    repo = get_timeblocks_repository()

    # Persist scheduled blocks
    for block in schedule_result.blocks:
        await repo.create_timeblock(
            user_id=user_id,
            task_id=block.task_id,
            title=block.title,
            start_time=block.start,
            end_time=block.end,
            type=block.type,
            source="scheduler",
            agent_reasoning={
                "objective_value": schedule_result.objective_value,
                "constraints_met": block.constraints,
                "utility_score": block.utility
            }
        )
```

### 7.4 Frontend Integration

The frontend queries the unified view through the API:

```typescript
// Fetch timeblocks for calendar display
const { data } = useQuery({
  queryKey: ['timeblocks', startDate, endDate],
  queryFn: () => fetchTimeblocks(startDate, endDate)
});

// Timeblocks from all sources are rendered identically
data.items.forEach(timeblock => {
  renderCalendarBlock(timeblock);
});
```

---

## 8. Migration Strategy

### 8.1 Migration Steps Executed

1. **Create timeblocks table** with indexes and constraints
2. **Populate from existing data** (tasks with start_date/end_date)
3. **Update v_timeblocks view** to include timeblocks table
4. **Add RLS policies** for security
5. **Create Pydantic model** and register in MODEL_REGISTRY
6. **Extend repository** with CRUD operations

### 8.2 Backward Compatibility

The system maintains **full backward compatibility**:

- Existing tasks with `start_date`/`end_date` continue to work
- View union ensures legacy data appears in queries
- Duplicate prevention: If a timeblock exists for a task, the task is excluded from the view
- Gradual migration path: New scheduling uses timeblocks, old data remains in tasks

### 8.3 Data Migration

Initial population query:

```sql
INSERT INTO timeblocks (
  user_id, task_id, title, start_time, end_time,
  type, status, source, location, all_day, notes, metadata
)
SELECT
  t.user_id,
  t.id AS task_id,
  t.title,
  t.start_date,
  t.end_date,
  CASE WHEN t.kind = 'study' THEN 'study' ... END,
  CASE WHEN t.status = 'completed' THEN 'completed' ... END,
  CASE WHEN t.source IN ('canvas', 'google', ...) THEN 'external' ... END,
  t.location,
  COALESCE(t.all_day, false),
  t.notes,
  jsonb_build_object('task_type', t.task_type, 'priority', t.priority)
FROM tasks t
WHERE t.start_date IS NOT NULL
  AND t.end_date IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM timeblocks tb WHERE tb.task_id = t.id);
```

### 8.4 Future Deprecation Path

When ready to fully deprecate `tasks.start_date` and `tasks.end_date`:

1. Verify all active scheduling uses timeblocks table
2. Remove legacy tasks from v_timeblocks view
3. Drop columns: `ALTER TABLE tasks DROP COLUMN start_date, DROP COLUMN end_date;`
4. Update application code to remove legacy paths

---

## 9. Future Enhancements

### 9.1 Recurring Timeblocks

Support for recurring patterns:

```json
{
  "recurrence": {
    "pattern": "weekly",
    "days": ["Mon", "Wed", "Fri"],
    "time": "14:00",
    "duration_minutes": 60,
    "until": "2025-12-31"
  }
}
```

Implementation approach:
- Generate timeblock instances on-the-fly or materialize in advance
- Use `parent_timeblock_id` to link recurring instances
- Handle exceptions (skip dates, time changes)

### 9.2 Completion Analytics

Track productivity metrics:

```json
{
  "performance": {
    "scheduled_duration": 120,
    "actual_duration": 95,
    "productivity_ratio": 0.79,
    "interruptions": 3,
    "focus_score": 0.82
  }
}
```

Applications:
- Machine learning features for scheduling
- User productivity insights
- Adaptive scheduling based on historical performance

### 9.3 Timeblock Templates

Reusable patterns:

```python
class TimeblockTemplate:
    name: str
    type: str
    default_duration: int
    default_metadata: Dict[str, Any]

# Example: "Morning Deep Work"
template = TimeblockTemplate(
    name="Morning Deep Work",
    type="focus",
    default_duration=120,
    default_metadata={"energy_level": "high"}
)
```

### 9.4 Multi-User Timeblocks

Support for shared/collaborative timeblocks:

```sql
CREATE TABLE timeblock_participants (
  timeblock_id UUID REFERENCES timeblocks(id),
  user_id UUID REFERENCES users(id),
  role TEXT,  -- 'owner', 'participant', 'viewer'
  PRIMARY KEY (timeblock_id, user_id)
);
```

### 9.5 Conflict Detection

Real-time conflict checking:

```python
async def check_conflicts(
    user_id: str,
    start_time: datetime,
    end_time: datetime
) -> List[Dict]:
    """Find overlapping timeblocks"""
    return await repo.fetch_timeblocks(
        user_id, start_time, end_time
    )
```

Applications:
- Prevent double-booking
- Suggest alternative times
- Flexible vs. hard conflicts

### 9.6 REST API Expansion

Full CRUD endpoints for timeblocks:

```
POST   /api/v1/timeblocks          Create timeblock
GET    /api/v1/timeblocks/:id      Get timeblock
PATCH  /api/v1/timeblocks/:id      Update timeblock
DELETE /api/v1/timeblocks/:id      Delete timeblock
GET    /api/v1/tasks/:id/timeblocks  Get task sessions
PATCH  /api/v1/timeblocks/:id/complete  Mark completed
```

---

## Appendix A: Related Documentation

- [CALENDAR_SYSTEM.md](./CALENDAR_SYSTEM.md) - External calendar integration
- [AGENT_IMPLEMENTATION.md](./AGENT_IMPLEMENTATION.md) - LangGraph agents
- [RULES.md](../../RULES.md) - Project architecture rules
- [CLAUDE.md](../../CLAUDE.md) - Development guidelines

## Appendix B: Database Migrations

All migrations are located in `backend/migrations/`:

1. `create_timeblocks_table.sql` - Initial table creation
2. `populate_timeblocks_from_tasks.sql` - Data backfill
3. `drop_and_recreate_v_timeblocks_view.sql` - View structure update
4. `add_rls_policies_to_timeblocks.sql` - Security policies

## Appendix C: Performance Considerations

### Query Performance

- **GiST index** on time range: O(log n) range queries
- **B-tree indexes** on user_id, task_id: Fast lookups
- **View materialization**: Consider if query performance degrades

### Scaling

- Current design supports **100K+ timeblocks per user**
- Partitioning strategy by date if needed:
  ```sql
  CREATE TABLE timeblocks_2025_q4 PARTITION OF timeblocks
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');
  ```

### Caching

- Frontend: TanStack Query with 5-minute stale time
- Backend: Redis cache for frequently accessed date ranges
- Invalidation: On timeblock create/update/delete

---

**Document Revision History:**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-28 | Initial documentation | Claude |
