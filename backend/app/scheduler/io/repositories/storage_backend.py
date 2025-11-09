"""
Storage backend implementations for scheduler repositories.

Provides in-memory and database storage backends for scheduler data.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ...core.domain import (
    Task, BusyEvent, Preferences, CompletionEvent,
    ScheduleBlock, SchedulerRun
)

logger = logging.getLogger(__name__)


class StorageBackend:
    """Base storage backend interface."""

    def __init__(self, backend_type: str = "memory"):
        """
        Initialize storage backend.

        Args:
            backend_type: Type of backend ('memory' or 'database')
        """
        self.backend_type = backend_type


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend for development and testing."""

    def __init__(self):
        """Initialize memory storage backend."""
        super().__init__(backend_type="memory")

        # In-memory storage
        self._store = {
            'tasks': {},           # user_id -> List[Task]
            'events': {},          # user_id -> List[BusyEvent]
            'preferences': {},     # user_id -> Preferences
            'history': {},         # user_id -> List[CompletionEvent]
            'schedules': {},       # user_id -> List[ScheduleBlock]
            'runs': {},           # user_id -> List[SchedulerRun]
        }

        # Initialize with sample data for development
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample data for development."""
        sample_user = "user_123"

        # Sample preferences
        self._store['preferences'][sample_user] = Preferences(
            timezone="America/New_York",
            workday_start="09:00",
            workday_end="18:00",
            max_daily_effort_minutes=480,
            session_granularity_minutes=30
        )

        # Sample tasks
        now = datetime.now()
        self._store['tasks'][sample_user] = [
            Task(
                id="task_1",
                user_id=sample_user,
                title="Study Machine Learning",
                kind="study",
                estimated_minutes=120,
                min_block_minutes=60,
                max_block_minutes=120,
                deadline=now + timedelta(days=7),
                weight=2.0,
                course_id="cs_ml_101"
            ),
            Task(
                id="task_2",
                user_id=sample_user,
                title="Complete Assignment 1",
                kind="assignment",
                estimated_minutes=90,
                min_block_minutes=45,
                max_block_minutes=90,
                deadline=now + timedelta(days=3),
                weight=3.0,
                course_id="cs_ml_101"
            ),
            Task(
                id="task_3",
                user_id=sample_user,
                title="Read Chapter 5",
                kind="reading",
                estimated_minutes=60,
                min_block_minutes=30,
                max_block_minutes=60,
                weight=1.0,
                course_id="cs_ml_101"
            )
        ]

        # Sample busy events
        self._store['events'][sample_user] = [
            BusyEvent(
                id="event_1",
                source="google",
                start=now.replace(hour=10, minute=0),
                end=now.replace(hour=11, minute=0),
                title="Team Meeting",
                hard=True
            ),
            BusyEvent(
                id="event_2",
                source="google",
                start=now.replace(hour=14, minute=0),
                end=now.replace(hour=15, minute=30),
                title="Doctor Appointment",
                hard=True
            )
        ]

        # Sample completion history
        self._store['history'][sample_user] = [
            CompletionEvent(
                task_id="task_old_1",
                scheduled_slot=now - timedelta(hours=24),
                completed_at=now - timedelta(hours=23, minutes=45)
            ),
            CompletionEvent(
                task_id="task_old_2",
                scheduled_slot=now - timedelta(hours=48),
                completed_at=None,  # Missed
                skipped=True
            )
        ]

    # Task storage methods
    def get_tasks(self, user_id: str) -> List[Task]:
        """Get tasks for user."""
        return self._store['tasks'].get(user_id, [])

    def set_tasks(self, user_id: str, tasks: List[Task]):
        """Set tasks for user."""
        self._store['tasks'][user_id] = tasks

    # Event storage methods
    def get_events(self, user_id: str) -> List[BusyEvent]:
        """Get events for user."""
        return self._store['events'].get(user_id, [])

    def set_events(self, user_id: str, events: List[BusyEvent]):
        """Set events for user."""
        self._store['events'][user_id] = events

    # Preferences storage methods
    def get_preferences(self, user_id: str) -> Optional[Preferences]:
        """Get preferences for user."""
        return self._store['preferences'].get(user_id)

    def set_preferences(self, user_id: str, preferences: Preferences):
        """Set preferences for user."""
        self._store['preferences'][user_id] = preferences

    # History storage methods
    def get_history(self, user_id: str) -> List[CompletionEvent]:
        """Get history for user."""
        return self._store['history'].get(user_id, [])

    def set_history(self, user_id: str, history: List[CompletionEvent]):
        """Set history for user."""
        self._store['history'][user_id] = history

    # Schedule storage methods
    def get_schedules(self, user_id: str) -> List[ScheduleBlock]:
        """Get schedules for user."""
        return self._store['schedules'].get(user_id, [])

    def set_schedules(self, user_id: str, schedules: List[ScheduleBlock]):
        """Set schedules for user."""
        self._store['schedules'][user_id] = schedules

    # Run storage methods
    def get_runs(self, user_id: str) -> List[SchedulerRun]:
        """Get runs for user."""
        return self._store['runs'].get(user_id, [])

    def set_runs(self, user_id: str, runs: List[SchedulerRun]):
        """Set runs for user."""
        self._store['runs'][user_id] = runs


class DatabaseStorageBackend(StorageBackend):
    """Database storage backend for production use."""

    def __init__(self):
        """Initialize database storage backend."""
        super().__init__(backend_type="database")
        # Database connection would be initialized here

    # Database-specific methods would be implemented here
    # For now, these are handled in individual repository classes
