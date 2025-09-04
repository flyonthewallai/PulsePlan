"""
Production-grade scheduling subsystem for PulsePlan.

This module provides intelligent task scheduling with ML-driven optimization,
constraint satisfaction, and adaptive learning capabilities.
"""

from .service import SchedulerService
from .domain import Task, BusyEvent, Preferences
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