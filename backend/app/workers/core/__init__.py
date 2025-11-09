"""
Core worker infrastructure and types.

This module contains core worker functionality including:
- Worker types and data structures
- Shared interfaces and base classes
- Common utilities for all workers
"""

from .types import (
    JobStatus,
    JobResult,
    EmailData,
    BriefingData,
    WeeklyPulseData
)

from .main import (
    WorkerManager
)

__all__ = [
    # Worker types
    "JobStatus",
    "JobResult",
    "EmailData",
    "BriefingData",
    "WeeklyPulseData",

    # Worker management
    "WorkerManager",
]


