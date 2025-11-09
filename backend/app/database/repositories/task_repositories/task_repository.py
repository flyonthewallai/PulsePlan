"""
Task Repository
Data access layer for tasks (assignments, quizzes, exams)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository):
    """Repository for task data access"""

    @property
    def table_name(self) -> str:
        return "tasks"

    async def bulk_create(self, tasks: List[Dict[str, Any]]) -> bool:
        """
        Insert multiple task records in a single operation

        Args:
            tasks: List of task dictionaries

        Returns:
            True if inserted
        """
        try:
            if not tasks:
                return True
            response = self.supabase.table(self.table_name).insert(tasks).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error bulk inserting tasks: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="bulk_create",
                details={"count": len(tasks)}
            )

    async def get_by_user(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific user with optional filters

        Args:
            user_id: User ID
            filters: Optional filters (status, priority, task_type, course, etc.)
            limit: Result limit

        Returns:
            List of task dictionaries

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Build query with course information
            select_query = "*,courses(id,name,color,icon,canvas_course_code)"
            query = self.supabase.table(self.table_name).select(select_query).eq("user_id", user_id)

            # Apply filters if provided
            if filters:
                if filters.get("status"):
                    query = query.eq("status", filters["status"])
                if filters.get("priority"):
                    query = query.eq("priority", filters["priority"])
                if filters.get("task_type"):
                    query = query.eq("task_type", filters["task_type"])
                if filters.get("course"):
                    query = query.eq("course", filters["course"])
                if filters.get("project_id"):
                    query = query.eq("project_id", filters["project_id"])
                if filters.get("start_date"):
                    query = query.gte("due_date", filters["start_date"])
                if filters.get("end_date"):
                    query = query.lte("due_date", filters["end_date"])
                if filters.get("due_before"):
                    query = query.lte("due_date", filters["due_before"])
                if filters.get("due_after"):
                    query = query.gte("due_date", filters["due_after"])
                if filters.get("tags"):
                    query = query.contains("tags", filters["tags"])
                if filters.get("external_source"):
                    query = query.eq("external_source", filters["external_source"])
                if filters.get("completed") is not None:
                    query = query.eq("completed", filters["completed"])

                # Apply ordering
                order_by = filters.get("order_by", "due_date")
                order_desc = filters.get("order_desc", False)
                query = query.order(order_by, desc=order_desc, nullsfirst=False)

            # Apply limit
            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching tasks for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id, "filters": filters}
            )
    
    async def count_by_filters(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count tasks for a user with optional filters

        Args:
            user_id: User ID
            filters: Optional filters (external_source, status, etc.)

        Returns:
            Count of matching tasks

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name).select("id", count="exact").eq("user_id", user_id)

            # Apply filters if provided
            if filters:
                if filters.get("external_source"):
                    query = query.eq("external_source", filters["external_source"])
                if filters.get("status"):
                    query = query.eq("status", filters["status"])
                if filters.get("completed") is not None:
                    query = query.eq("completed", filters["completed"])

            response = query.execute()
            return response.count if hasattr(response, 'count') and response.count is not None else 0

        except Exception as e:
            logger.error(f"Error counting tasks for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="count_by_filters",
                details={"user_id": user_id, "filters": filters}
            )

    async def search_by_title(
        self,
        user_id: str,
        title: str,
        exact_match: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search tasks by title for a specific user

        Args:
            user_id: User ID
            title: Title to search for
            exact_match: If True, search for exact match; if False, partial match

        Returns:
            List of matching task dictionaries

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            title_trimmed = title.strip()

            if exact_match:
                # Exact case-insensitive match
                response = (
                    self.supabase.table(self.table_name)
                    .select("*")
                    .eq("user_id", user_id)
                    .ilike("title", title_trimmed)
                    .execute()
                )
            else:
                # Partial case-insensitive match
                response = (
                    self.supabase.table(self.table_name)
                    .select("*")
                    .eq("user_id", user_id)
                    .ilike("title", f"%{title_trimmed}%")
                    .execute()
                )

            return response.data or []

        except Exception as e:
            logger.error(f"Error searching tasks by title for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="search_by_title",
                details={"user_id": user_id, "title": title}
            )

    async def get_by_id_and_user(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID for a specific user

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            Task dictionary or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("id", task_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching task {task_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_and_user",
                details={"task_id": task_id, "user_id": user_id}
            )

    async def get_by_id_with_course(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID with course information included

        Args:
            task_id: Task ID

        Returns:
            Task dictionary with nested course data or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            select_query = "*,courses(id,name,color,icon,canvas_course_code)"
            response = (
                self.supabase.table(self.table_name)
                .select(select_query)
                .eq("id", task_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching task {task_id} with course: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_with_course",
                details={"task_id": task_id}
            )

    async def update_by_user(
        self,
        task_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a task for a specific user

        Args:
            task_id: Task ID
            user_id: User ID
            data: Update data

        Returns:
            Updated task dictionary or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Add updated_at timestamp
            data["updated_at"] = datetime.utcnow().isoformat()

            response = (
                self.supabase.table(self.table_name)
                .update(data)
                .eq("id", task_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating task {task_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_by_user",
                details={"task_id": task_id, "user_id": user_id, "data": data}
            )

    async def delete_by_user(self, task_id: str, user_id: str) -> bool:
        """
        Delete a task for a specific user

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = (
                self.supabase.table(self.table_name)
                .delete()
                .eq("id", task_id)
                .eq("user_id", user_id)
                .execute()
            )

            return response.data is not None and len(response.data) > 0

        except Exception as e:
            logger.error(f"Error deleting task {task_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_user",
                details={"task_id": task_id, "user_id": user_id}
            )

    async def validate_prerequisites_exist(
        self,
        prerequisite_ids: List[str],
        user_id: str
    ) -> List[str]:
        """
        Validate that prerequisite tasks exist

        Args:
            prerequisite_ids: List of prerequisite task IDs
            user_id: User ID

        Returns:
            List of missing prerequisite IDs

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            if not prerequisite_ids:
                return []

            response = (
                self.supabase.table(self.table_name)
                .select("id")
                .in_("id", prerequisite_ids)
                .eq("user_id", user_id)
                .execute()
            )

            found_ids = {task["id"] for task in response.data}
            missing_ids = [pid for pid in prerequisite_ids if pid not in found_ids]

            return missing_ids

        except Exception as e:
            logger.error(f"Error validating prerequisites for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="validate_prerequisites_exist",
                details={"prerequisite_ids": prerequisite_ids, "user_id": user_id}
            )


def get_task_repository() -> TaskRepository:
    """Dependency injection factory"""
    return TaskRepository()

