"""
History repository for scheduler data access.

Handles loading and recording task completion history from various storage backends.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from .base_repository import BaseHistoryRepository
from ...core.domain import CompletionEvent

logger = logging.getLogger(__name__)


class HistoryRepository(BaseHistoryRepository):
    """Repository for completion history data access operations."""

    def __init__(self, storage_backend):
        """
        Initialize history repository.

        Args:
            storage_backend: Storage backend instance
        """
        self.storage = storage_backend

    async def load_history(self, user_id: str, horizon_days: int = 60) -> List[CompletionEvent]:
        """
        Load historical completion data for learning.

        Args:
            user_id: User identifier
            horizon_days: Days back to load history

        Returns:
            List of completion events
        """
        try:
            if self.storage.backend_type == "memory":
                return await self._load_history_from_memory(user_id, horizon_days)
            elif self.storage.backend_type == "database":
                return await self._load_history_from_db(user_id, horizon_days)
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to load history for user {user_id}: {e}")
            return []

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
        try:
            completion_event = CompletionEvent(
                task_id=task_id,
                scheduled_slot=scheduled_slot,
                completed_at=completed_at,
                skipped=skipped
            )

            if self.storage.backend_type == "memory":
                await self._record_completion_in_memory(user_id, completion_event)
            elif self.storage.backend_type == "database":
                await self._record_completion_in_db(completion_event)

            logger.debug(f"Recorded completion for task {task_id}, user {user_id}")

        except Exception as e:
            logger.error(f"Failed to record completion for task {task_id}, user {user_id}: {e}")

    async def _load_history_from_memory(self, user_id: str, horizon_days: int) -> List[CompletionEvent]:
        """Load history from memory storage."""
        history = self.storage.get_history(user_id)

        # Filter to recent history
        cutoff_date = datetime.now() - timedelta(days=horizon_days)
        recent_history = [
            event for event in history
            if event.scheduled_slot >= cutoff_date
        ]

        logger.debug(f"Loaded {len(recent_history)} history events for user {user_id}")
        return recent_history

    async def _load_history_from_db(self, user_id: str, horizon_days: int) -> List[CompletionEvent]:
        """Load history from database."""
        try:
            from app.config.database.supabase import get_supabase

            supabase = get_supabase()

            # Calculate date range (look back from current time)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=horizon_days)

            # Query completed tasks/task completions from database
            response = supabase.table("task_completions").select("*").eq(
                "user_id", user_id
            ).gte("completed_at", start_date.isoformat()).lte(
                "completed_at", end_date.isoformat()
            ).execute()

            history = []
            for completion_data in response.data:
                # Convert database completion to scheduler CompletionEvent
                completion_time = datetime.fromisoformat(
                    completion_data["completed_at"].replace('Z', '+00:00')
                )

                completion = CompletionEvent(
                    task_id=completion_data["task_id"],
                    title=completion_data.get("task_title", "Completed Task"),
                    completed_at=completion_time,
                    actual_minutes=completion_data.get("actual_minutes", 60),
                    planned_minutes=completion_data.get("planned_minutes", 60),
                    quality_rating=completion_data.get("quality_rating", 5),
                    focus_rating=completion_data.get("focus_rating", 5),
                    difficulty_rating=completion_data.get("difficulty_rating", 3),
                    notes=completion_data.get("notes", "")
                )
                history.append(completion)

            logger.info(f"Loaded {len(history)} completion events from database for user {user_id}")
            return history

        except Exception as e:
            logger.error(f"Failed to load history from database: {e}")
            return []

    async def _record_completion_in_memory(self, user_id: str, event: CompletionEvent):
        """Record completion in memory storage."""
        history = self.storage.get_history(user_id)
        history.append(event)

        # Keep only recent history
        cutoff_date = datetime.now() - timedelta(days=90)
        history = [
            e for e in history
            if e.scheduled_slot >= cutoff_date
        ]

        self.storage.set_history(user_id, history)

    async def _record_completion_in_db(self, event: CompletionEvent):
        """Record completion in database."""
        # TODO: Implement database persistence
        logger.warning("Database backend not implemented")
