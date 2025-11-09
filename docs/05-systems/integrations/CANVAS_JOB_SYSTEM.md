# Canvas Job System

Canvas synchronization consists of reusable job modules orchestrated by `CanvasJobRunner` to support backfill, delta, and nightly sync scenarios.

## Components

1. **Canvas Job Runner** ([backend/app/services/workers/canvas_job_runner.py](../app/services/workers/canvas_job_runner.py))
   - Primary façade used by API endpoints and schedulers
   - Delegates to specialized job implementations and keeps orchestration logic centralized

2. **Backfill Job** ([backend/app/services/workers/canvas_backfill_job.py](../app/services/workers/canvas_backfill_job.py))
   - Performs the initial import of courses and assignments (idempotent)
   - Handles progress tracking and Supabase updates

3. **Delta Sync Job** ([backend/app/services/workers/canvas_delta_sync_job.py](../app/services/workers/canvas_delta_sync_job.py))
   - Incremental sync that processes assignments updated since the last cursor
   - Used for on-demand syncs during the day

4. **Nightly Sync Job** ([backend/app/services/workers/nightly_canvas_sync.py](../app/services/workers/nightly_canvas_sync.py))
   - Batches all active Canvas users nightly with concurrency limits

5. **Canvas Sync Tool** ([backend/app/jobs/canvas/canvas_sync.py](../app/jobs/canvas/canvas_sync.py))
   - General-purpose sync invoked by agents or manual commands (`sync_user_canvas_data`)

6. **Canvas Scheduler** ([backend/app/workers/canvas_scheduler.py](../app/workers/canvas_scheduler.py))
   - APScheduler wrapper that triggers delta sync cycles every 20 minutes and the nightly sweep at 02:30 UTC
   - Started/stopped in `backend/main.py` alongside calendar/timezone schedulers

## Runner API

| Method | Description |
| --- | --- |
| `run_backfill(user_id, force_restart=False)` | Executes the initial backfill for a user |
| `run_delta_sync(user_id)` | Runs the incremental sync window for a user |
| `run_nightly_sync(batch_size=50, max_concurrent=10)` | Processes all active Canvas accounts nightly |
| `sync_user_canvas_data(...kwargs)` | Exposes the general Canvas sync helper used by agents/manual triggers |

## Scheduler Cadence

| Job | Trigger | Source |
| --- | --- | --- |
| Delta Sync Cycle | Every 20 minutes | `CanvasScheduler.run_delta_cycle` -> `CanvasJobRunner.run_delta_sync(user)` |
| Nightly Sync | 02:30 UTC daily | `CanvasScheduler.run_nightly_sync` -> `CanvasJobRunner.run_nightly_sync(...)` |

## Usage

- API endpoints should import `get_canvas_job_runner()` and invoke the appropriate method instead of instantiating job classes directly.
- Existing helper functions (`get_canvas_backfill_job`, etc.) remain for backward compatibility in tests/tools.
- When adding new Canvas job types, extend the runner and expose a strongly typed method so schedulers remain thin.
