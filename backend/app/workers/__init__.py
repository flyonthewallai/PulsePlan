"""
Workers module - Background task processing organized by domain.

This module provides organized access to all worker functionality grouped by domain:
- core: Core worker infrastructure, types, and management
- scheduling: Task scheduling and timezone-aware job management
- communication: Email services and notification delivery
"""

# Re-export from modules for backward compatibility
from .core import *
from .scheduling import *
from .communication import *

__all__ = [
    # Core worker infrastructure
    "JobStatus",
    "JobResult",
    "EmailData", 
    "BriefingData",
    "WeeklyPulseData",
    "WorkerManager",
    "create_worker_manager",
    "run_workers",
    "shutdown_workers",
    
    # Scheduling workers
    "WorkerScheduler",
    "get_worker_scheduler",
    "schedule_daily_briefings",
    "schedule_weekly_pulses", 
    "schedule_health_checks",
    "TimezoneScheduler",
    "get_timezone_scheduler",
    "create_timezone_aware_jobs",
    "optimize_scheduling_for_timezone",
    "analyze_user_timezones",
    
    # Communication workers
    "EmailService",
    "get_email_service",
    "send_briefing_email", 
    "send_notification_email",
    "send_weekly_pulse_email",
    "validate_email_delivery",
]