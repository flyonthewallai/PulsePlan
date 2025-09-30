"""
Core scheduler components - domain models, configuration, and main service.
"""

from .domain import Task, BusyEvent, Preferences, ScheduleSolution, ScheduleBlock
from .service import SchedulerService
from .config import *
from .features import build_utilities

__all__ = [
    'Task',
    'BusyEvent',
    'Preferences',
    'ScheduleSolution',
    'ScheduleBlock',
    'SchedulerService',
    'build_utilities'
]