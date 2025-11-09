"""
Task repository for scheduler data access.

Handles loading and updating tasks from various storage backends.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from .base_repository import BaseTaskRepository
from ...core.domain import Task

logger = logging.getLogger(__name__)


class TaskRepository(BaseTaskRepository):
    """Repository for task data access operations."""

    def __init__(self, storage_backend):
        """
        Initialize task repository.

        Args:
            storage_backend: Storage backend instance
        """
        self.storage = storage_backend

    async def load_tasks(self, user_id: str, horizon_days: int) -> List[Task]:
        """
        Load tasks for scheduling within the horizon.

        Args:
            user_id: User identifier
            horizon_days: Days ahead to consider

        Returns:
            List of tasks to schedule
        """
        try:
            if self.storage.backend_type == "memory":
                return await self._load_tasks_from_memory(user_id, horizon_days)
            elif self.storage.backend_type == "database":
                return await self._load_tasks_from_db(user_id, horizon_days)
            else:
                logger.warning(f"Unknown backend {self.storage.backend_type}, returning empty tasks")
                return []

        except Exception as e:
            logger.error(f"Failed to load tasks for user {user_id}: {e}")
            return []

    async def update_task(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """
        Update task parameters.

        Args:
            user_id: User identifier
            task_id: Task identifier
            updates: Dictionary of field updates
        """
        try:
            if self.storage.backend_type == "memory":
                await self._update_task_in_memory(user_id, task_id, updates)
            elif self.storage.backend_type == "database":
                await self._update_task_in_db(user_id, task_id, updates)

            logger.debug(f"Updated task {task_id} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to update task {task_id} for user {user_id}: {e}")

    async def _load_tasks_from_memory(self, user_id: str, horizon_days: int) -> List[Task]:
        """Load tasks from memory storage."""
        tasks = self.storage.get_tasks(user_id)

        # Filter tasks relevant to horizon
        horizon_end = datetime.now() + timedelta(days=horizon_days)
        relevant_tasks = []

        for task in tasks:
            # Include if no deadline or deadline within extended horizon
            if task.deadline is None or task.deadline <= horizon_end + timedelta(days=7):
                relevant_tasks.append(task)

        logger.debug(f"Loaded {len(relevant_tasks)} tasks for user {user_id}")
        return relevant_tasks

    async def _load_tasks_from_db(self, user_id: str, horizon_days: int) -> List[Task]:
        """Load tasks from database."""
        try:
            from app.config.database.supabase import get_supabase

            supabase = get_supabase()

            # Calculate date range
            end_date = datetime.utcnow() + timedelta(days=horizon_days)

            # Query tasks from database
            response = supabase.table("tasks").select("*").eq(
                "user_id", user_id
            ).eq("status", "pending").lte(
                "due_date", end_date.isoformat()
            ).execute()

            tasks = []
            for task_data in response.data:
                # Convert database task to scheduler Task
                task = Task(
                    id=task_data["id"],
                    user_id=task_data["user_id"],
                    title=task_data["title"],
                    kind=task_data.get("kind", "task"),
                    estimated_minutes=task_data.get("estimated_minutes", 60),
                    min_block_minutes=task_data.get("min_block_minutes", 30),
                    max_block_minutes=task_data.get("max_block_minutes", 120),
                    deadline=datetime.fromisoformat(
                        task_data["due_date"].replace('Z', '+00:00')
                    ) if task_data.get("due_date") else None,
                    earliest_start=datetime.fromisoformat(
                        task_data["earliest_start"].replace('Z', '+00:00')
                    ) if task_data.get("earliest_start") else None,
                    preferred_windows=task_data.get("preferred_windows", []),
                    avoid_windows=task_data.get("avoid_windows", []),
                    fixed=task_data.get("fixed", False),
                    parent_task_id=task_data.get("parent_task_id"),
                    prerequisites=task_data.get("prerequisites", []),
                    weight=task_data.get("weight", 1.0),
                    course_id=task_data.get("course_id"),
                    must_finish_before=task_data.get("must_finish_before"),
                    tags=task_data.get("tags", []),
                    pinned_slots=task_data.get("pinned_slots", [])
                )
                tasks.append(task)

            logger.info(f"Loaded {len(tasks)} tasks from database for user {user_id}")
            return tasks

        except Exception as e:
            logger.error(f"Failed to load tasks from database: {e}")
            return []

    async def _update_task_in_memory(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """Update task in memory storage."""
        tasks = self.storage.get_tasks(user_id)

        for i, task in enumerate(tasks):
            if task.id == task_id:
                # Create updated task
                task_dict = asdict(task)
                task_dict.update(updates)
                task_dict['updated_at'] = datetime.now()

                # Replace in list
                tasks[i] = Task(**task_dict)
                self.storage.set_tasks(user_id, tasks)
                break

    async def _update_task_in_db(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """Update task in database."""
        # TODO: Implement database update
        logger.warning("Database backend not implemented")
