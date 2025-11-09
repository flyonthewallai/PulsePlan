# PITFALLS.md - Common Mistakes & Known Issues

**Last Updated:** 11/05/25
**Purpose:** Document discovered edge cases and bugs to prevent regeneration

> This is a living document. Every time you discover an edge case, bug, or anti-pattern, add it here so Claude (and other developers) don't repeat the same mistakes.

---

## How to Use This Document

**Before implementing ANY feature:**
1. Read the relevant section below
2. Check for known issues in that domain
3. Apply the documented solutions
4. Add new discoveries as you find them

**When adding entries:**
- Use ❌ for the mistake
- Use ✅ for the solution
- Include date and description

---

## Table of Contents

1. [Intent Classification](#intent-classification)
2. [OR-Tools Constraints](#or-tools-constraints)
3. [Context Fetching](#context-fetching)
4. [Database Operations](#database-operations)
5. [Calendar Sync](#calendar-sync)
6. [Authentication & Security](#authentication--security)
7. [Agent Workflows](#agent-workflows)
8. [Frontend/API Integration](#frontendapi-integration)
9. [Known Bugs Fixed](#known-bugs-fixed)

---

## Intent Classification

### Ambiguous Intent Detection

❌ **Don't:** Assume "schedule" always means "create new schedule"
```python
if "schedule" in prompt:
    return Intent.CREATE_SCHEDULE  # WRONG - could be reschedule
```

✅ **Do:** Check for "reschedule" indicators first
```python
if any(kw in prompt.lower() for kw in ["reschedule", "change", "move"]):
    return Intent.RESCHEDULE
elif "schedule" in prompt.lower():
    return Intent.CREATE_SCHEDULE
```

### Cancel vs Delete Confusion

❌ **Don't:** Treat "cancel" and "delete" as the same intent
```python
# WRONG - "cancel meeting" != "delete task"
if "cancel" in prompt or "delete" in prompt:
    return Intent.DELETE
```

✅ **Do:** Distinguish between canceling events and deleting tasks
```python
# Cancel = set status to cancelled (preserves history)
# Delete = permanent removal
if "cancel" in prompt:
    return Intent.CANCEL_EVENT
elif "delete" in prompt:
    return Intent.DELETE_TASK
```

**Added:** 11/05/25

### Confidence Threshold Issues

❌ **Don't:** Use LLM for every classification (expensive, slow)
```python
return await llm_classify(prompt)  # Always hits API
```

✅ **Do:** Use rule-based classification for high-confidence cases
```python
# Check explicit keywords first (instant, free)
if exact_match := check_keywords(prompt):
    return IntentResponse(intent=exact_match, confidence=1.0)

# Use LLM only for ambiguous cases
return await llm_classify(prompt)
```

**Added:** 11/05/25

---

## OR-Tools Constraints

### Overlapping Hard Constraints

❌ **Don't:** Define contradictory hard constraints
```python
solver.Add(start[task] >= 14 * 60)  # Must start after 2pm
solver.Add(end[task] <= 14 * 60)    # Must end before 2pm
# Results in INFEASIBLE
```

✅ **Do:** Use soft constraints with priority weights
```python
# Prefer to start after 2pm (soft constraint)
solver.Minimize(
    max(0, 14 * 60 - start[task]) * MEDIUM_PRIORITY
)
```

**Added:** 11/05/25

### Timeout Handling

❌ **Don't:** Assume solver always finds optimal solution
```python
status = solver.Solve(model)
return extract_schedule(solver)  # May be None if timeout
```

✅ **Do:** Handle timeout and infeasible cases
```python
status = solver.Solve(model)
if status == cp_model.OPTIMAL:
    return extract_optimal_schedule(solver)
elif status == cp_model.FEASIBLE:
    logger.warning("Partial solution found (timeout)")
    return extract_partial_schedule(solver)
else:
    raise SchedulingError("No feasible schedule found")
```

**Added:** 11/05/25

### Timezone Issues in Scheduling

❌ **Don't:** Mix timezone-aware and naive datetimes
```python
# WRONG - comparing UTC with local time
deadline_utc = datetime.now(timezone.utc)
user_deadline = datetime(2025, 1, 10, 17, 0)  # Naive
if deadline_utc > user_deadline:  # TypeError or wrong comparison
```

✅ **Do:** Convert all times to UTC internally
```python
from app.core.utils.timezone_utils import to_utc, from_utc

deadline_utc = to_utc(user_deadline, user_timezone)
# All comparisons in UTC
```

**Added:** 11/05/25

---

## Context Fetching

### N+1 Query Problem

❌ **Don't:** Fetch user data in a loop
```python
for task in tasks:
    user = await get_user(task.user_id)  # N+1 queries
    # Process with user data
```

✅ **Do:** Batch fetch or use eager loading
```python
user_ids = {task.user_id for task in tasks}
users = await get_users_by_ids(list(user_ids))
users_map = {u.id: u for u in users}

for task in tasks:
    user = users_map[task.user_id]
```

**Added:** 11/05/25

### Caching Full User History

❌ **Don't:** Fetch full user history on every request (slow)
```python
# WRONG - fetches all tasks/events for user
user_context = await get_complete_user_history(user_id)
```

✅ **Do:** Implement caching layer, fetch only recent data
```python
# Check cache first
cached = await redis.get(f"user_context:{user_id}")
if cached:
    return json.loads(cached)

# Fetch only recent data (last 30 days)
user_context = await get_recent_user_context(user_id, days=30)
await redis.setex(f"user_context:{user_id}", 300, json.dumps(user_context))
```

**Added:** 11/05/25

---

## Database Operations

### SQL Injection via String Concatenation

❌ **Don't:** Use raw SQL string concatenation
```python
# WRONG - SQL injection vulnerability
query = f"SELECT * FROM tasks WHERE user_id = '{user_id}'"
db.execute(query)
```

✅ **Do:** Use parameterized queries via Supabase client
```python
# Supabase client handles parameterization automatically
response = supabase.table("tasks")\
    .select("*")\
    .eq("user_id", user_id)\
    .execute()
```

**Added:** 11/05/25

### RLS Policy Bypass

❌ **Don't:** Use service key for user queries
```python
# WRONG - bypasses RLS, returns all users' data
supabase_admin = get_supabase_admin()
tasks = supabase_admin.table("tasks").select("*").execute()
```

✅ **Do:** Use user-scoped client with RLS
```python
# RLS automatically filters by authenticated user
supabase_user = get_supabase_user(user_token)
tasks = supabase_user.table("tasks").select("*").execute()
```

**Added:** 11/05/25

### Missing Transaction Handling

❌ **Don't:** Perform multi-step operations without transactions
```python
# WRONG - partial updates if second call fails
await create_task(task_data)
await create_calendar_event(event_data)  # Fails - task created but no event
```

✅ **Do:** Use transactions or idempotency keys
```python
async with db.transaction():
    task = await create_task(task_data)
    event = await create_calendar_event(event_data, task_id=task.id)
```

**Added:** 11/05/25

---

## Calendar Sync

### Race Condition on Sync

❌ **Don't:** Allow concurrent syncs for same user
```python
# WRONG - two sync jobs running simultaneously
async def sync_calendar(user_id):
    events = await fetch_from_google(user_id)
    await update_local_events(events)  # Conflicts if running twice
```

✅ **Do:** Use distributed locks
```python
async def sync_calendar(user_id):
    lock_key = f"sync_lock:{user_id}"
    async with redis_lock(lock_key, timeout=60):
        events = await fetch_from_google(user_id)
        await update_local_events(events)
```

**Added:** 11/05/25

### Source of Truth Conflicts

❌ **Don't:** Assume calendar is always source of truth
```python
# WRONG - overwrites user's manual task updates
if calendar_event.updated_at > task.updated_at:
    await update_task_from_event(task, calendar_event)
```

✅ **Do:** Check `source_of_truth` field in calendar_links
```python
link = await get_calendar_link(task_id, event_id)
if link.source_of_truth == "calendar":
    await update_task_from_event(task, event)
elif link.source_of_truth == "task":
    await update_event_from_task(event, task)
else:  # latest_update
    if calendar_event.updated_at > task.updated_at:
        await update_task_from_event(task, event)
```

**Added:** 11/05/25

---

## Authentication & Security

### Token Not Refreshed

❌ **Don't:** Use expired OAuth tokens
```python
# WRONG - token may have expired
access_token = user.google_access_token
response = requests.get(GOOGLE_API, headers={"Authorization": f"Bearer {access_token}"})
```

✅ **Do:** Check expiration and refresh if needed
```python
from app.services.auth.token_refresh import ensure_token_valid

access_token = await ensure_token_valid(user_id, provider="google")
response = requests.get(GOOGLE_API, headers={"Authorization": f"Bearer {access_token}"})
```

**Added:** 11/05/25

### Logging Sensitive Data

❌ **Don't:** Log tokens, PII, or sensitive data
```python
# WRONG - logs access token
logger.info(f"Using token: {access_token}")
logger.debug(f"User email: {user.email}")
```

✅ **Do:** Redact sensitive fields
```python
logger.info(f"Using token: {access_token[:10]}...")  # Only log prefix
logger.debug(f"User ID: {user.id}")  # Log ID, not email
```

**Added:** 11/05/25

---

## Agent Workflows

### Missing Error Boundaries

❌ **Don't:** Let errors crash entire workflow
```python
async def workflow_node(state):
    result = await risky_operation()  # May raise exception
    return {"result": result}
```

✅ **Do:** Wrap risky operations in try/except
```python
async def workflow_node(state):
    try:
        result = await risky_operation()
        return {"result": result, "error": None}
    except Exception as e:
        logger.error(f"Node failed: {e}", exc_info=True)
        return {"result": None, "error": str(e)}
```

**Added:** 11/05/25

### State Mutation Issues

❌ **Don't:** Mutate workflow state in place
```python
async def workflow_node(state):
    state["results"].append(new_result)  # Mutates shared state
    return state
```

✅ **Do:** Return new state objects
```python
async def workflow_node(state):
    return {
        **state,
        "results": [*state["results"], new_result]
    }
```

**Added:** 11/05/25

---

## Frontend/API Integration

### Assuming Success Response

❌ **Don't:** Assume API calls always succeed
```typescript
// WRONG - no error handling
const data = await api.createTask(taskData);
updateUI(data);  // May fail if API returned error
```

✅ **Do:** Check success field and handle errors
```typescript
const response = await api.createTask(taskData);
if (response.success) {
    updateUI(response.data);
} else {
    showError(response.error.message);
}
```

**Added:** 11/05/25

### Missing Loading States

❌ **Don't:** Update UI immediately (causes flashing)
```typescript
// WRONG - UI jumps
const tasks = await fetchTasks();
setTasks(tasks);
```

✅ **Do:** Show loading state
```typescript
setLoading(true);
try {
    const tasks = await fetchTasks();
    setTasks(tasks);
} finally {
    setLoading(false);
}
```

**Added:** 11/05/25

---

## Known Bugs Fixed

### 11/05/25: Repository Import Path Changes

**Bug:** Old repository imports stopped working after reorganization

**Solution:** Updated all imports to new domain-based structure
```python
# Before (broken)
from app.database.task_repository import TaskRepository

# After (fixed)
from app.database.repositories.task_repositories import TaskRepository
```

**Affected Files:** 20+ service, agent, and API files

---

### 11/05/25: Missing Factory Functions

**Bug:** Some repositories were importing non-existent factory functions

**Solution:** Removed references to `get_task_repository()` and `get_todo_repository()` which don't exist. These repositories are instantiated directly.

**Correct Usage:**
```python
# TaskRepository and TodoRepository don't have factory functions
repo = TaskRepository()  # Direct instantiation

# Other repositories have factory functions
repo = get_user_repository()  # Has factory function
```

---

### Example Template (for future bugs)

**Bug:** Brief description of the issue

**Root Cause:** Why it happened

**Solution:** How it was fixed

**Prevention:** How to avoid in future

**Added:** YYYY-MM-DD

---

## Contributing to This Document

**When you discover a bug or edge case:**

1. Add entry to appropriate section
2. Use ❌/✅ format for clarity
3. Include date and brief explanation
4. Add code examples showing wrong/right way
5. Cross-reference related issues

**Format:**
```markdown
### Descriptive Title

❌ **Don't:** Bad pattern explanation
```code example```

✅ **Do:** Good pattern explanation
```code example```

**Added:** YYYY-MM-DD
```

---

## Questions?

- **How to fix an issue?** See solution in relevant section
- **Need code example?** See [EXAMPLES.md](./EXAMPLES.md)
- **Understanding architecture?** See [ARCHITECTURE.md](../ARCHITECTURE.md)

**Remember:** This document grows with the project. Every bug fixed is a lesson documented.
