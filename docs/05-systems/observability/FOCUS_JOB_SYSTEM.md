# Focus Profile Job System

The focus profile job system computes and updates user focus profiles periodically using APScheduler-driven jobs and a reusable job runner service.

## Architecture Overview

### Components

1. **Focus Job Runner** ([backend/app/services/workers/focus_job_runner.py](../app/services/workers/focus_job_runner.py))
   - Provides single-run method (`run_profile_updates`) for processing pending profile updates
   - Uses `FocusSessionService` to compute profiles and `CacheService` for Redis flags
   - Enforces batching, structured logging, and error handling for each job

2. **Focus Profile Worker** ([backend/app/workers/focus_profile_worker.py](../app/services/workers/focus_profile_worker.py))
   - Thin wrapper maintaining backward compatibility with legacy worker pattern
   - Delegates all business logic to `FocusJobRunner`
   - Supports both APScheduler integration and legacy polling loop pattern

3. **Focus Session Service** ([backend/app/services/focus/focus_session_service.py](../app/services/focus/focus_session_service.py))
   - Core service for computing user focus profiles from session data
   - Handles profile computation, storage, and retrieval

4. **Repositories & Storage**
   - `focus_sessions` table: stores individual focus session records
   - `user_focus_profiles` table: stores computed profile summaries
   - Redis keys `focus:needs_update:{user_id}` flag users needing profile updates

## Job Schedule

| Job | Trigger (recommended) | Runner Method | Purpose |
| --- | --- | --- | --- |
| Profile Updates | Every 5-15 minutes | `FocusJobRunner.run_profile_updates` | Processes users flagged for profile updates |

## Update Detection

The job runner identifies users needing profile updates through two methods:

1. **Redis Cache Flags**: Users are flagged via `focus:needs_update:{user_id}` keys when:
   - New focus sessions are created
   - User manually requests profile update
   - Profile computation fails and needs retry

2. **Database Staleness Check**: Users with:
   - Recent focus sessions (within last 24 hours)
   - Stale profiles (older than 24 hours) or no profile
   - Are automatically included in the update batch

## Profile Computation

- **Minimum Session Requirement**: Users must have at least 3 focus sessions before a profile is computed
- **Profile Contents**: Includes total sessions count, average focus duration, preferred focus times, productivity patterns
- **Update Flag Clearing**: After successful computation, the Redis flag is automatically cleared

## Data Flow

1. **Flagging**: When a focus session is created or updated, the system sets `focus:needs_update:{user_id}` in Redis
2. **Job Execution**: APScheduler triggers `run_profile_updates` at configured intervals
3. **User Discovery**: Runner queries both Redis flags and database for users needing updates
4. **Batch Processing**: Users are processed in batches (default: 50) to prevent overload
5. **Profile Computation**: For each user, `FocusSessionService.compute_user_profile` is called
6. **Flag Clearing**: Successful updates clear the Redis flag; failures are logged for retry

## Operations & Monitoring

- **Logs**: Each job logs start/end markers and aggregated statistics (success, failed, skipped). Monitor `focus_profile_update` log streams.
- **Redis Backlog**: If `focus:needs_update:*` keys accumulate, consider increasing job frequency or investigating computation failures.
- **Database Load**: Profile computation queries can be expensive; batch size limits prevent overload.
- **Graceful Degradation**: If Redis or Supabase are unavailable, job runner methods log the failure but do not crash APScheduler.

## Developer Workflow

1. **Add New Profile Metrics**
   - Extend `FocusSessionService.compute_user_profile` to include new metrics
   - Update `user_focus_profiles` table schema if needed
   - Ensure backward compatibility with existing profiles

2. **Create New Job**
   - Add a method to `FocusJobRunner` containing the core logic (pure async, idempotent)
   - Register a CronTrigger in your scheduler
   - Document the job in this file and ensure tests cover success + failure paths

3. **Local Testing**
   ```bash
   # Run API & scheduler
   uvicorn backend.app.main:app --reload

   # Trigger a manual profile update cycle
   python -m asyncio -c "from app.services.workers.focus_job_runner import get_focus_job_runner; import asyncio; asyncio.run(get_focus_job_runner().run_profile_updates())"
   ```

4. **Flagging Users for Update**
   ```python
   from app.services.infrastructure.cache_service import get_cache_service
   
   cache = get_cache_service()
   await cache.set(f"focus:needs_update:{user_id}", "1", ttl=86400)
   ```

## Backward Compatibility

The legacy `FocusProfileWorker` class is maintained for backward compatibility:
- Old imports (`from app.workers.focus_profile_worker import get_focus_profile_worker`) still work
- The worker class now delegates to `FocusJobRunner` internally
- The polling loop pattern (`start()`/`stop()`) is preserved for legacy integrations

New code should prefer:
```python
from app.services.workers.focus_job_runner import get_focus_job_runner

runner = get_focus_job_runner()
await runner.run_profile_updates()
```

This document is the authoritative reference for how focus profile computation operates post-refactor; update it whenever job cadence, storage, or orchestration strategies change.

