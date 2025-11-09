# Notification Job System

Predictable iOS/email notifications run through a dedicated job runner that batches daily briefings, weekly summaries, due date reminders, and achievement nudges.

## Architecture

### Components

1. **Notification Job Runner** ([backend/app/services/workers/notification_job_runner.py](../app/services/workers/notification_job_runner.py))
   - Encapsulates notification batching logic and concurrency controls
   - Provides async entry points (`send_daily_briefings`, `send_weekly_summaries`, etc.)
   - Handles Redis/cache lookups, Supabase queries, and Resend/Push delivery services

2. **Legacy Job Module Wrapper** ([backend/app/jobs/notifications/notifications.py](../app/jobs/notifications/notifications.py))
   - Thin compatibility layer so existing imports (`app.jobs.notifications`) still resolve
   - Re-exports enums, getters, and coroutine helpers for schedulers

3. **iOS Notification Service** ([backend/app/services/notifications/ios_notification_service.py](../app/services/notifications/ios_notification_service.py))
   - Sends push payloads to APNs via the iOS bridge
   - Injected into the job runner

## Job Portfolio

| Job | Trigger (recommended) | Runner Method | Purpose |
| --- | --- | --- | --- |
| Daily Briefing Notifications | Morning per timezone | `send_daily_briefings` | Push summary of today’s agenda |
| Weekly Summaries | Weekly (Sun/Mon) | `send_weekly_summaries` | Highlight productivity metrics |
| Due Date Reminders | 3–4× per day | `send_due_date_reminders` | Nudge users about upcoming assignments |
| Achievement Notifications | Daily evening | `send_achievement_notifications` | Celebrate streaks/goals |

Schedulers (APScheduler, worker queues, or CRON-based lambdas) should import the wrapper helpers (`run_daily_briefings`, etc.) which simply call the job runner.

## Data Flow

1. Runner queries Supabase for eligible users/tasks and caches user/global preferences via `CacheService`.
2. Jobs are processed in batches using `asyncio.gather`, respecting batch sizes and short delays to prevent spikes.
3. Each notification record is appended to the result summary with success/failure counts for observability.

## Developer Workflow

- Add new notification types by extending the job runner and updating the wrapper module’s exports.
- Keep delivery services (push/email/SMS) injected so unit tests can stub them.
- When wiring new schedules, prefer the helper coroutines in the wrapper module to avoid duplicating instantiation logic.

