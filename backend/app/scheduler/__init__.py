"""
Production-grade scheduling subsystem for PulsePlan.

This module provides intelligent task scheduling with ML-driven optimization,
constraint satisfaction, and adaptive learning capabilities.
"""

from .core.service import SchedulerService
from .core.domain import Task, BusyEvent, Preferences
from .io.dto import ScheduleRequest, ScheduleResponse, ScheduleBlock

__all__ = [
    'SchedulerService',
    'Task',
    'BusyEvent',
    'Preferences',
    'ScheduleRequest',
    'ScheduleResponse',
    'ScheduleBlock'
]