# Calendar Auto-Sync System

The calendar auto-sync system keeps Google and Microsoft calendars synchronized with PulsePlan using APScheduler-driven jobs and a reusable job runner service.

## Architecture Overview

### Components

1. **Calendar Job Runner** ([backend/app/services/workers/calendar_background_worker.py](../app/services/workers/calendar_background_worker.py))
   - Provides single-run methods (`run_auto_sync_cycle`, `process_webhook_queue`, `run_conflict_resolution`, `cleanup_calendar_data`)
   - Uses `CalendarSyncService`, `CalendarWebhookService`, Redis queues, and calendar repositories
   - Enforces batching, idempotency, and structured logging for each job

2. **APScheduler Orchestrator** ([backend/app/workers/calendar_scheduler.py](../app/workers/calendar_scheduler.py))
   - Schedules auto-sync, webhook processing, conflict resolution, cleanup, incremental pulls, and watch renewals
   - Runs within FastAPI lifespan so jobs share the same dependency context
   - Guards each job with error logging to keep the scheduler healthy

3. **Calendar Sync Worker** ([backend/app/services/workers/calendar_sync_worker.py](../app/services/workers/calendar_sync_worker.py))
   - Handles provider-specific operations (discover calendars, incremental pulls, push tasks, ensure/renew watch channels)
   - `ensure_watch` provisions or refreshes webhook channels with the configured callback URL

4. **API/Webhooks** ([backend/app/api/v1/endpoints/integrations_modules/calendar.py](../app/api/v1/endpoints/integrations_modules/calendar.py))
   - `POST /integrations/calendar/sync/schedule` stores user preferences for background sync cadence
   - `POST /integrations/calendar/webhooks/*` validates incoming webhook headers, enqueues messages in Redis via `queue_webhook`

5. **Repositories & Storage**
   - `CalendarPreferencesRepository`: stores `auto_sync_enabled` and `sync_frequency_minutes`
   - `CalendarSyncStatusRepository`: tracks last successful sync per user
   - Redis list keys `calendar_webhooks:{provider}` buffer webhook notifications for the job runner
   - Supabase tables `calendar_events` and `calendar_sync_conflicts` support cleanup routines

## Job Schedule

| Job | Trigger | Handler | Purpose |
| --- | --- | --- | --- |
| Auto Sync | Every 10 minutes | `CalendarJobRunner.run_auto_sync_cycle` | Syncs users whose preferences indicate they are due |
| Webhook Processor | Every 30 seconds | `CalendarJobRunner.process_webhook_queue` | Drains Redis queues and triggers incremental syncs per notification |
| Conflict Resolution | Every 30 minutes | `CalendarJobRunner.run_conflict_resolution` | Resolves unresolved conflicts in `calendar_sync_conflicts` |
| Cleanup | Daily at 03:00 UTC | `CalendarJobRunner.cleanup_calendar_data` | Removes stale cached events, resolved conflicts, and old sync status rows |
| Incremental Pull | Every 20 minutes | `CalendarScheduler.run_incremental_pulls` | Uses sync tokens to pull active calendars during user working hours |
| Watch Renewal | Hourly | `CalendarScheduler.run_watch_renewals` | Forces watch renewal for calendars expiring within 12 hours |

All jobs log structured summaries and allow future migration to a distributed task queue because the job runner methods are pure async functions without scheduler-specific dependencies.

## Webhook Flow

1. **Provider Notification**
   - Google sends signed HTTP requests with `X-Goog-Channel-Id`, `X-Goog-Resource-Id`, `X-Goog-Resource-State`
   - Microsoft sends batched JSON payloads with `subscriptionId`, `changeType`, and resource metadata

2. **API Validation**
   - `handle_google_calendar_webhook` ensures `channel_id` follows `user_{id}` convention, then enqueues `{user_id, resource_id, resource_state}` with provider metadata
   - `handle_microsoft_calendar_webhook` resolves `user_id` via `webhook_subscriptions` repository before enqueueing

3. **Redis Queue**
   - Payloads are stored in `calendar_webhooks:google` or `calendar_webhooks:microsoft` until the scheduler fires `process_webhook_queue`

4. **Job Runner Processing**
   - Drains both lists atomically and calls `CalendarWebhookService` per item
   - `CalendarWebhookService` forces a short-range sync (`days_ahead=7`, `force_refresh=True`) and conflict reconciliation

## Watch Channel Provisioning

- During OAuth callback, after calendars are discovered and the first incremental pull finishes, `CalendarSyncWorker.ensure_watch` is executed for each active calendar to guarantee webhook coverage.
- `ensure_watch` checks `watch_channel_id` and `watch_expiration_at`:
  - If valid for >1 hour, the method logs and returns without recreating the channel
  - Otherwise it stops the previous channel (if any) and provisions a new watch against `API_BASE_URL/webhooks/google/calendar`
- Hourly renewal job calls `renew_watch`, which is now a thin wrapper around `ensure_watch(force=True)`

## Auto-Sync Preferences

1. Users enable background sync via `POST /integrations/calendar/sync/schedule`.
2. `CalendarSyncService.schedule_background_sync` upserts preferences:
   - `auto_sync_enabled`
   - `sync_frequency_minutes`
   - Conflict strategy and write permissions
3. `CalendarJobRunner._get_users_for_auto_sync` reads preferences, joins with `CalendarSyncStatusRepository`, and yields only the users whose `last_sync_at` exceeds the desired interval.

## Operations & Monitoring

- **Logs**: Each job logs both start/end markers and aggregated statistics (scheduled, synced, failed). Monitor `calendar_auto_sync`, `calendar_webhook_processor`, and `calendar_conflict_resolution` log streams.
- **Redis Backlog**: If `calendar_webhooks:*` lists grow, scale scheduling frequency or inspect webhook headers for errors.
- **API Base URL**: Ensure `API_BASE_URL` matches the public domain reachable by Google webhooks in each environment.
- **Graceful Degradation**: If Redis or Supabase are unavailable, job runner methods log the failure but do not crash APScheduler. Alerts should be triggered from centralized logging.

## Developer Workflow

1. **Add New Provider**
   - Implement provider client + mapping utilities under `app/integrations/providers/{provider}`
   - Extend repositories if additional metadata is needed
   - Update job runner to enqueue/process new Redis keys

2. **Create New Job**
   - Add a method to `CalendarJobRunner` containing the core logic (pure async, idempotent)
   - Register a CronTrigger in `CalendarScheduler.start`
   - Document the job in this file and ensure tests cover success + failure paths

3. **Local Testing**
   ```bash
   # Run API & scheduler
   uvicorn backend.app.main:app --reload

   # Trigger a manual auto-sync cycle
   python -m asyncio -c "from app.services.workers.calendar_background_worker import get_calendar_job_runner; import asyncio; asyncio.run(get_calendar_job_runner().run_auto_sync_cycle())"
   ```

This document is the authoritative reference for how background calendar synchronization operates post-refactor; update it whenever job cadence, storage, or orchestration strategies change.
