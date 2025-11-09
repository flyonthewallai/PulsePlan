"""
Main repository coordinator for scheduler data access.

Coordinates all sub-repositories and provides unified interface for data operations.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from .storage_backend import MemoryStorageBackend, DatabaseStorageBackend
from .task_repository import TaskRepository
from .event_repository import EventRepository
from .preferences_repository import PreferencesRepository
from .history_repository import HistoryRepository
from .schedule_repository import ScheduleRepository

from ...core.domain import (
    Task, BusyEvent, Preferences, CompletionEvent,
    ScheduleSolution, ScheduleBlock, SchedulerRun
)

logger = logging.getLogger(__name__)


class Repository:
    """
    Main repository coordinator for scheduler data access.

    Coordinates all sub-repositories and provides unified interface.
    """

    def __init__(self, backend: str = "memory"):
        """
        Initialize repository with sub-repositories.

        Args:
            backend: Storage backend ('memory', 'database', 'file')
        """
        self.backend = backend

        # Initialize storage backend
        if backend == "memory":
            self.storage = MemoryStorageBackend()
        elif backend == "database":
            self.storage = DatabaseStorageBackend()
        else:
            logger.warning(f"Unknown backend {backend}, defaulting to memory")
            self.storage = MemoryStorageBackend()

        # Initialize sub-repositories
        self.tasks = TaskRepository(self.storage)
        self.events = EventRepository(self.storage)
        self.preferences = PreferencesRepository(self.storage)
        self.history = HistoryRepository(self.storage)
        self.schedules = ScheduleRepository(self.storage)

    # Task operations
    async def load_tasks(self, user_id: str, horizon_days: int) -> List[Task]:
        """Load tasks for scheduling within the horizon."""
        return await self.tasks.load_tasks(user_id, horizon_days)

    async def update_task(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """Update task parameters."""
        return await self.tasks.update_task(user_id, task_id, updates)

    # Event operations
    async def load_calendar_busy(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """Load busy calendar events within the horizon."""
        return await self.events.load_calendar_busy(user_id, horizon_days)

    # Preferences operations
    async def load_preferences(self, user_id: str) -> Preferences:
        """Load user preferences for scheduling."""
        return await self.preferences.load_preferences(user_id)

    async def update_preferences(self, user_id: str, updates: Dict[str, Any]):
        """Update user preferences."""
        return await self.preferences.update_preferences(user_id, updates)

    async def get_window(self, user_id: str, horizon_days: int) -> Tuple[datetime, datetime]:
        """Get the time window for scheduling."""
        return await self.preferences.get_window(user_id, horizon_days)

    # History operations
    async def load_history(self, user_id: str, horizon_days: int = 60) -> List[CompletionEvent]:
        """Load historical completion data for learning."""
        return await self.history.load_history(user_id, horizon_days)

    async def record_completion(
        self, user_id: str, task_id: str, scheduled_slot: datetime,
        completed_at: Optional[datetime] = None, skipped: bool = False
    ):
        """Record task completion or miss for learning."""
        return await self.history.record_completion(
            user_id, task_id, scheduled_slot, completed_at, skipped
        )

    # Schedule operations
    async def persist_schedule(
        self,
        user_id: str,
        solution: ScheduleSolution,
        job_id: Optional[str] = None
    ):
        """Persist schedule blocks to storage."""
        return await self.schedules.persist_schedule(user_id, solution, job_id)

    async def persist_run_summary(
        self,
        user_id: str,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ):
        """Persist summary of scheduler run for analysis."""
        return await self.schedules.persist_run_summary(user_id, solution, weights, context)

    async def get_recent_schedules(
        self, user_id: str, days_back: int = 7
    ) -> List[ScheduleBlock]:
        """Get recently scheduled blocks for a user."""
        return await self.schedules.get_recent_schedules(user_id, days_back)


# Global repository instance
_repository = None


def get_repository(backend: str = "memory") -> Repository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = Repository(backend=backend)
    return _repository
