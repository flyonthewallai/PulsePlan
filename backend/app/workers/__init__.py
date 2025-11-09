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

    # Scheduling workers
    "WorkerScheduler",
    "get_worker_scheduler",
    "TimezoneAwareScheduler",
    "get_timezone_scheduler",

    # Communication workers
    "EmailService",
    "get_email_service",
]