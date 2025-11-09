"""
Task Service
Business logic layer for task operations
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.repositories.task_repositories import TaskRepository
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task business logic"""

    def __init__(self, repository: TaskRepository = None):
        """Initialize service with repository"""
        self.repo = repository or TaskRepository()

    async def create_task(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new task

        Args:
            user_id: User ID
            task_data: Task data

        Returns:
            Created task dictionary

        Raises:
            ServiceError: If validation or creation fails
        """
        try:
            # Validate required fields
            if not task_data.get("title"):
                raise ServiceError("Task title is required", "task", "create")

            # Validate prerequisites if provided
            prerequisites = task_data.get("prerequisites", [])
            if prerequisites:
                missing_ids = await self.repo.validate_prerequisites_exist(prerequisites, user_id)
                if missing_ids:
                    raise ServiceError(
                        f"Prerequisite tasks not found: {', '.join(missing_ids)}",
                        "task",
                        "create"
                    )

            # Validate scheduling constraints
            self._validate_scheduling_constraints(task_data)

            # Create task record
            task_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": task_data["title"],
                "description": task_data.get("description", ""),
                "task_type": task_data.get("task_type", "assignment"),
                "kind": task_data.get("kind", "admin"),
                "estimated_minutes": task_data.get("estimated_minutes", 60),
                "min_block_minutes": task_data.get("min_block_minutes", 30),
                "max_block_minutes": task_data.get("max_block_minutes"),
                "deadline": task_data.get("deadline") or task_data.get("due_date"),
                "due_date": task_data.get("due_date") or task_data.get("deadline"),
                "earliest_start": task_data.get("earliest_start"),
                "preferred_windows": task_data.get("preferred_windows", []),
                "avoid_windows": task_data.get("avoid_windows", []),
                "fixed": task_data.get("fixed", False),
                "parent_task_id": task_data.get("parent_task_id"),
                "prerequisites": prerequisites,
                "weight": task_data.get("weight", 1.0),
                "course_id": task_data.get("course_id"),
                "course": task_data.get("course"),
                "must_finish_before": task_data.get("must_finish_before"),
                "tags": task_data.get("tags", []),
                "pinned_slots": task_data.get("pinned_slots", []),
                "status": task_data.get("status", "pending"),
                "priority": task_data.get("priority", "medium"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Create task in database
            created_task = await self.repo.create(task_record)

            logger.info(f"Created task {created_task['id']} for user {user_id}")
            return created_task

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            raise ServiceError(str(e), "task", "create")

    async def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            Task dictionary or None if not found

        Raises:
            ServiceError: If retrieval fails
        """
        try:
            task = await self.repo.get_by_id_and_user(task_id, user_id)

            if not task:
                return None

            return task

        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}", exc_info=True)
            raise ServiceError(str(e), "task", "get")

    async def list_tasks(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List tasks with optional filters

        Args:
            user_id: User ID
            filters: Optional filters

        Returns:
            Dictionary with tasks list and metadata

        Raises:
            ServiceError: If listing fails
        """
        try:
            tasks = await self.repo.get_by_user(user_id, filters)

            return {
                "tasks": tasks,
                "total": len(tasks),
                "filters_applied": filters or {}
            }

        except Exception as e:
            logger.error(f"Error listing tasks: {e}", exc_info=True)
            raise ServiceError(str(e), "task", "list")

    async def update_task(
        self,
        task_id: str,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a task

        Args:
            task_id: Task ID
            user_id: User ID
            task_data: Update data

        Returns:
            Updated task dictionary

        Raises:
            ServiceError: If validation or update fails
        """
        try:
            # Prepare update data
            update_data = {}

            # Only include fields that were provided
            allowed_fields = [
                "title", "description", "status", "priority", "due_date", "deadline",
                "tags", "estimated_minutes", "estimated_hours", "actual_hours",
                "project_id", "course_id", "course", "dependencies", "prerequisites",
                "progress_percentage", "metadata", "pinned_slots", "completed_at",
                "task_type", "kind", "min_block_minutes", "max_block_minutes",
                "earliest_start", "preferred_windows", "avoid_windows", "fixed",
                "parent_task_id", "weight", "must_finish_before"
            ]

            for field in allowed_fields:
                if field in task_data:
                    update_data[field] = task_data[field]

            # Handle completed_at based on status field
            if "status" in task_data and "completed_at" not in task_data:
                if task_data["status"] == "completed":
                    update_data["completed_at"] = datetime.utcnow().isoformat()
                else:
                    update_data["completed_at"] = None

            # Update in database
            updated_task = await self.repo.update_by_user(task_id, user_id, update_data)

            if not updated_task:
                raise ServiceError("Task not found", "task", "update")

            logger.info(f"Updated task {task_id} for user {user_id}")
            return updated_task

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
            raise ServiceError(str(e), "task", "update")

    async def delete_task(self, task_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete a task

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            Deletion confirmation dictionary

        Raises:
            ServiceError: If deletion fails
        """
        try:
            deleted = await self.repo.delete_by_user(task_id, user_id)

            if not deleted:
                raise ServiceError("Task not found", "task", "delete")

            logger.info(f"Deleted task {task_id} for user {user_id}")

            return {
                "deleted_task_id": task_id,
                "deleted_at": datetime.utcnow().isoformat(),
                "deleted_by": user_id
            }

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}", exc_info=True)
            raise ServiceError(str(e), "task", "delete")

    async def search_by_title(
        self,
        user_id: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Search tasks by title

        Args:
            user_id: User ID
            title: Title to search for

        Returns:
            Dictionary with search results

        Raises:
            ServiceError: If search fails
        """
        try:
            # Try exact match first
            exact_tasks = await self.repo.search_by_title(user_id, title, exact_match=True)

            if exact_tasks:
                tasks = exact_tasks
                match_type = "exact"
            else:
                # Fall back to partial match
                tasks = await self.repo.search_by_title(user_id, title, exact_match=False)
                match_type = "partial"

            return {
                "tasks": tasks,
                "total": len(tasks),
                "search_term": title.strip(),
                "match_type": match_type
            }

        except Exception as e:
            logger.error(f"Error searching tasks by title: {e}", exc_info=True)
            raise ServiceError(str(e), "task", "search_by_title")

    def _validate_scheduling_constraints(self, task_data: Dict[str, Any]) -> None:
        """
        Validate task scheduling constraints

        Args:
            task_data: Task data

        Raises:
            ServiceError: If validation fails
        """
        estimated_minutes = task_data.get("estimated_minutes", 60)
        min_block_minutes = task_data.get("min_block_minutes", 30)
        max_block_minutes = task_data.get("max_block_minutes")

        # Validate positive values
        if estimated_minutes <= 0:
            raise ServiceError("Estimated minutes must be positive", "task", "validate")
        if min_block_minutes <= 0:
            raise ServiceError("Minimum block minutes must be positive", "task", "validate")

        # Validate block constraints
        if max_block_minutes and max_block_minutes < min_block_minutes:
            raise ServiceError(
                "Maximum block minutes cannot be less than minimum",
                "task",
                "validate"
            )

        # Validate weight
        weight = task_data.get("weight", 1.0)
        if weight < 0:
            raise ServiceError("Task weight cannot be negative", "task", "validate")


def get_task_service() -> TaskService:
    """Dependency injection helper for TaskService"""
    return TaskService()

