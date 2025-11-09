# Briefing & Pulse Job System

The briefing job system generates daily briefings and weekly pulse updates, coordinating both fixed interval jobs and timezone-targeted scheduling.

## Architecture Overview

### Components

1. **Briefing Job Runner** ([backend/app/services/workers/briefing_job_runner.py](../app/services/workers/briefing_job_runner.py))
   - Core business logic for fetching eligible users, invoking agent workflows, and sending emails
   - Provides idempotent methods used by schedulers and tests
   - Handles cache deduplication to avoid duplicate daily briefings

2. **Worker Scheduler** ([backend/app/workers/scheduling/scheduler.py](../app/workers/scheduling/scheduler.py))
   - APScheduler wrapper that triggers `run_daily_briefings` every 15 minutes and `run_weekly_pulse` hourly
   - Contains no business logic—only schedules and forwards to the job runner

3. **Timezone-Aware Scheduler** ([backend/app/workers/scheduling/timezone_scheduler.py](../app/workers/scheduling/timezone_scheduler.py))
   - Analyzes user briefing preferences to generate timezone-specific Cron jobs
   - Uses the same job runner to process targeted batches for both daily briefings and weekly pulse emails

4. **Email Service** ([backend/app/workers/communication/email_service.py](../app/workers/communication/email_service.py))
   - Renders HTML templates for daily briefings and weekly pulse messages
   - Injected into the job runner for sending emails via Resend

## Job Schedule

| Job | Trigger | Source | Handler |
| --- | --- | --- | --- |
| Daily Briefings | Every 15 minutes | WorkerScheduler | `BriefingJobRunner.run_daily_briefings` |
| Weekly Pulse | Hourly | WorkerScheduler | `BriefingJobRunner.run_weekly_pulse` |
| Timezone Briefings | Cron per timezone | TimezoneAwareScheduler | `BriefingJobRunner.process_briefings_for_users` |
| Timezone Weekly Pulse | Cron per timezone | TimezoneAwareScheduler | `BriefingJobRunner.process_weekly_pulse_for_users` |
| Timezone Analysis Refresh | Daily 00:00 UTC | TimezoneAwareScheduler | `_analyze_and_schedule_timezones` (scheduler only) |

## Data Flow

1. Job runner loads candidate users from `user_preferences` and validates the current time in each user’s timezone (via `TimezoneManager`).
2. Agent workflows generate briefing or pulse content; failures are captured in `JobResult` objects.
3. Email service renders and sends HTML emails. Successful sends are cached (daily briefings use a 24h Redis key to prevent duplicates).
4. Timezone-aware jobs call `process_*_for_users`, which reuses the same processing logic for pre-filtered user sets.

## Failure Handling

- Job runner returns per-user `JobResult` structs; schedulers aggregate success vs failure.
- Email and agent errors are logged and surfaced through `JobResult.error`.
- Daily briefings mark successful sends in Redis to avoid duplicates when jobs overlap.

## Developer Workflow

- Extend the job runner when adding new briefing or pulse variants; keep schedulers thin.
- Use `BriefingJobRunner` directly in tests to bypass APScheduler.
- When adding new schedules, prefer calling the runner methods rather than reimplementing logic.
