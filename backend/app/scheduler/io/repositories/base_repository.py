"""
Base repository interface for scheduler data access.

Defines abstract interfaces for data persistence operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from ...core.domain import (
    Task, BusyEvent, Preferences, CompletionEvent,
    ScheduleSolution, ScheduleBlock, SchedulerRun
)

logger = logging.getLogger(__name__)


class BaseTaskRepository(ABC):
    """Abstract interface for task data access."""

    @abstractmethod
    async def load_tasks(self, user_id: str, horizon_days: int) -> List[Task]:
        """
        Load tasks for scheduling within the horizon.

        Args:
            user_id: User identifier
            horizon_days: Days ahead to consider

        Returns:
            List of tasks to schedule
        """
        pass

    @abstractmethod
    async def update_task(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """
        Update task parameters.

        Args:
            user_id: User identifier
            task_id: Task identifier
            updates: Dictionary of field updates
        """
        pass


class BaseEventRepository(ABC):
    """Abstract interface for event data access."""

    @abstractmethod
    async def load_calendar_busy(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """
        Load busy calendar events within the horizon.

        Args:
            user_id: User identifier
            horizon_days: Days ahead to consider

        Returns:
            List of busy events
        """
        pass


class BasePreferencesRepository(ABC):
    """Abstract interface for preferences data access."""

    @abstractmethod
    async def load_preferences(self, user_id: str) -> Preferences:
        """
        Load user preferences for scheduling.

        Args:
            user_id: User identifier

        Returns:
            User preferences with defaults if not found
        """
        pass

    @abstractmethod
    async def update_preferences(self, user_id: str, updates: Dict[str, Any]):
        """
        Update user preferences.

        Args:
            user_id: User identifier
            updates: Dictionary of preference updates
        """
        pass

    @abstractmethod
    async def get_window(self, user_id: str, horizon_days: int) -> Tuple[datetime, datetime]:
        """
        Get the time window for scheduling.

        Args:
            user_id: User identifier
            horizon_days: Days ahead to schedule

        Returns:
            (start_datetime, end_datetime) for scheduling
        """
        pass


class BaseHistoryRepository(ABC):
    """Abstract interface for completion history data access."""

    @abstractmethod
    async def load_history(self, user_id: str, horizon_days: int = 60) -> List[CompletionEvent]:
        """
        Load historical completion data for learning.

        Args:
            user_id: User identifier
            horizon_days: Days back to load history

        Returns:
            List of completion events
        """
        pass

    @abstractmethod
    async def record_completion(
        self, user_id: str, task_id: str, scheduled_slot: datetime,
        completed_at: Optional[datetime] = None, skipped: bool = False
    ):
        """
        Record task completion or miss for learning.

        Args:
            user_id: User identifier
            task_id: Task identifier
            scheduled_slot: When task was scheduled
            completed_at: When task was completed (None if missed)
            skipped: Whether task was explicitly skipped
        """
        pass


class BaseScheduleRepository(ABC):
    """Abstract interface for schedule data access."""

    @abstractmethod
    async def persist_schedule(
        self,
        user_id: str,
        solution: ScheduleSolution,
        job_id: Optional[str] = None
    ):
        """
        Persist schedule blocks to storage.

        Args:
            user_id: User identifier
            solution: Schedule solution with blocks
            job_id: Optional job identifier
        """
        pass

    @abstractmethod
    async def persist_run_summary(
        self,
        user_id: str,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Persist summary of scheduler run for analysis.

        Args:
            user_id: User identifier
            solution: Schedule solution
            weights: Penalty weights used
            context: Additional context
        """
        pass

    @abstractmethod
    async def get_recent_schedules(
        self, user_id: str, days_back: int = 7
    ) -> List[ScheduleBlock]:
        """
        Get recently scheduled blocks for a user.

        Args:
            user_id: User identifier
            days_back: Days back to retrieve

        Returns:
            List of recent schedule blocks
        """
        pass
