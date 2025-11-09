"""
Scheduler repository module.

Provides modular data access components for scheduler persistence.
"""

from .repository import Repository, get_repository
from .base_repository import (
    BaseTaskRepository,
    BaseEventRepository,
    BasePreferencesRepository,
    BaseHistoryRepository,
    BaseScheduleRepository
)
from .task_repository import TaskRepository
from .event_repository import EventRepository
from .preferences_repository import PreferencesRepository
from .history_repository import HistoryRepository
from .schedule_repository import ScheduleRepository
from .storage_backend import (
    StorageBackend,
    MemoryStorageBackend,
    DatabaseStorageBackend
)

__all__ = [
    # Main repository interface
    'Repository',
    'get_repository',

    # Base interfaces
    'BaseTaskRepository',
    'BaseEventRepository',
    'BasePreferencesRepository',
    'BaseHistoryRepository',
    'BaseScheduleRepository',

    # Concrete implementations
    'TaskRepository',
    'EventRepository',
    'PreferencesRepository',
    'HistoryRepository',
    'ScheduleRepository',

    # Storage backends
    'StorageBackend',
    'MemoryStorageBackend',
    'DatabaseStorageBackend',
]
