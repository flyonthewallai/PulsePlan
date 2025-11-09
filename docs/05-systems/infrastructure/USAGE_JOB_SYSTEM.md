# Usage Job System

Usage aggregation resets quotas and computes platform stats through a dedicated job runner and APScheduler triggers.

## Components

1. **Usage Job Runner** ([backend/app/services/workers/usage_job_runner.py](../app/services/workers/usage_job_runner.py))
   - Provides `run_monthly_aggregation` and `run_daily_quota_check`
   - Handles repository interaction so schedulers remain slim

2. **Usage Job Scheduler** ([backend/app/jobs/usage_aggregation.py](../app/jobs/usage_aggregation.py))
   - Compatibility module that exposes coroutine helpers and registers Cron jobs
   - Imports the job runner singleton and delegates execution

3. **Usage Repository** (`app/database/repositories/integration_repositories`) 
   - Supplies aggregation, quota reset, and stats queries used by the runner

## Schedule

| Job | Trigger | Description |
| --- | --- | --- |
| Monthly Aggregation | `cron: day=1, hour=2` | Aggregates prior month usage and resets quotas |
| Daily Quota Check | `cron: hour=1` | Logs per-day usage stats for monitoring |

## Developer Notes

- Add new quota/usage jobs by extending `UsageJobRunner` with strongly typed methods, then register them via APScheduler or future Celery workers.
- Testing: call runner methods directly to avoid scheduler wiring.
- Ensure repository changes remain async-friendly; the runner simply awaits repository methods and logs outcomes.

