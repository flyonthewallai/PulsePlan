"""
Main orchestration service for the scheduler subsystem.

This is a compatibility wrapper that delegates to the modular scheduler service.
The actual implementation has been split into modular components in the
scheduler_service/ package for better maintainability.

For new code, prefer importing directly from scheduler_service:
    from .scheduler_service import SchedulerService, get_scheduler_service

This wrapper maintains backward compatibility for existing imports.
"""

# Re-export everything from the modular implementation
from .scheduler_service import (
    SchedulerService,
    get_scheduler_service,
    ContextBuilder,
    ExplanationBuilder,
    UtilityCalculator,
    HealthMonitor,
)

__all__ = [
    'SchedulerService',
    'get_scheduler_service',
    'ContextBuilder',
    'ExplanationBuilder',
    'UtilityCalculator',
    'HealthMonitor',
]
