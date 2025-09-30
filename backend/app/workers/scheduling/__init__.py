"""
Schedule management and scheduling workers.

This module contains all scheduling-related worker functionality including:
- Background task scheduling using APScheduler
- Timezone-aware scheduling for efficient resource usage
- Job orchestration and management
"""

from .scheduler import (
    WorkerScheduler,
    get_worker_scheduler,
    schedule_daily_briefings,
    schedule_weekly_pulses,
    schedule_health_checks
)

from .timezone_scheduler import (
    TimezoneScheduler,
    get_timezone_scheduler,
    create_timezone_aware_jobs,
    optimize_scheduling_for_timezone,
    analyze_user_timezones
)

__all__ = [
    # Core scheduling
    "WorkerScheduler",
    "get_worker_scheduler",
    "schedule_daily_briefings",
    "schedule_weekly_pulses", 
    "schedule_health_checks",
    
    # Timezone-aware scheduling
    "TimezoneScheduler",
    "get_timezone_scheduler",
    "create_timezone_aware_jobs",
    "optimize_scheduling_for_timezone",
    "analyze_user_timezones",
]


