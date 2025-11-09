"""
Modular scheduler service package.

This package provides a modularized version of the scheduler service,
split into logical components for better maintainability and testing.

Components:
- scheduler_service: Main orchestration service (primary API)
- context_builder: Context building for bandit weight selection
- explanation_builder: Human-readable explanations for schedules
- utility_calculator: Utility calculation (ML-based and simplified)
- health_monitor: Health monitoring and status reporting

Usage:
    from backend.app.scheduler.core.scheduler_service import (
        SchedulerService,
        get_scheduler_service
    )

    # Get global instance
    scheduler = get_scheduler_service()

    # Or create custom instance
    scheduler = SchedulerService(
        enable_safety_rails=True,
        safety_level=SafetyLevel.STANDARD
    )
"""

from .scheduler_service import SchedulerService, get_scheduler_service
from .context_builder import ContextBuilder, get_context_builder
from .explanation_builder import ExplanationBuilder, get_explanation_builder
from .utility_calculator import UtilityCalculator, get_utility_calculator
from .health_monitor import HealthMonitor, get_health_monitor

__all__ = [
    # Main service
    'SchedulerService',
    'get_scheduler_service',

    # Component classes
    'ContextBuilder',
    'ExplanationBuilder',
    'UtilityCalculator',
    'HealthMonitor',

    # Component factories
    'get_context_builder',
    'get_explanation_builder',
    'get_utility_calculator',
    'get_health_monitor',
]
