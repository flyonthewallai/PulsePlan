"""
Todo Repository
Data access layer for todos (lightweight tasks)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class TodoRepository(BaseRepository):
    """Repository for todo data access"""

    @property
    def table_name(self) -> str:
        return "todos"

    async def get_by_user(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all todos for a specific user with optional filters

        Args:
            user_id: User ID
            filters: Optional filters (completed, priority, etc.)

        Returns:
            List of todo dictionaries

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name).select("*").eq("user_id", user_id)

            # Apply filters if provided
            if filters:
                if filters.get("completed") is not None:
                    query = query.eq("completed", filters["completed"])
                if filters.get("priority"):
                    query = query.eq("priority", filters["priority"])
                if filters.get("status"):
                    query = query.eq("status", filters["status"])

            # Order by creation date (newest first)
            query = query.order("created_at", desc=True)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching todos for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id, "filters": filters}
            )

    async def search_by_title(
        self,
        user_id: str,
        title: str,
        exact_match: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search todos by title for a specific user

        Args:
            user_id: User ID
            title: Title to search for
            exact_match: If True, search for exact match; if False, partial match

        Returns:
            List of matching todo dictionaries

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
            logger.error(f"Error searching todos by title for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="search_by_title",
                details={"user_id": user_id, "title": title}
            )

    async def get_by_id_and_user(self, todo_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a todo by ID for a specific user

        Args:
            todo_id: Todo ID
            user_id: User ID

        Returns:
            Todo dictionary or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("id", todo_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching todo {todo_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_and_user",
                details={"todo_id": todo_id, "user_id": user_id}
            )

    async def update_by_user(
        self,
        todo_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a todo for a specific user

        Args:
            todo_id: Todo ID
            user_id: User ID
            data: Update data

        Returns:
            Updated todo dictionary or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Add updated_at timestamp
            data["updated_at"] = datetime.utcnow().isoformat()

            response = (
                self.supabase.table(self.table_name)
                .update(data)
                .eq("id", todo_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating todo {todo_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_by_user",
                details={"todo_id": todo_id, "user_id": user_id, "data": data}
            )

    async def delete_by_user(self, todo_id: str, user_id: str) -> bool:
        """
        Delete a todo for a specific user

        Args:
            todo_id: Todo ID
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
                .eq("id", todo_id)
                .eq("user_id", user_id)
                .execute()
            )

            return response.data is not None and len(response.data) > 0

        except Exception as e:
            logger.error(f"Error deleting todo {todo_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_user",
                details={"todo_id": todo_id, "user_id": user_id}
            )

    async def bulk_update(
        self,
        todo_ids: List[str],
        user_id: str,
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Bulk update multiple todos for a specific user

        Args:
            todo_ids: List of todo IDs
            user_id: User ID
            data: Update data

        Returns:
            List of updated todo dictionaries

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Add updated_at timestamp
            data["updated_at"] = datetime.utcnow().isoformat()

            response = (
                self.supabase.table(self.table_name)
                .update(data)
                .in_("id", todo_ids)
                .eq("user_id", user_id)
                .execute()
            )

            return response.data or []

        except Exception as e:
            logger.error(f"Error bulk updating todos for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="bulk_update",
                details={"todo_ids": todo_ids, "user_id": user_id, "data": data}
            )


class TodoTagRepository(BaseRepository):
    """Repository for todo tag junction table"""

    @property
    def table_name(self) -> str:
        return "todo_tags"

    async def get_tags_for_todo(self, todo_id: str) -> List[str]:
        """
        Get all tags for a specific todo

        Args:
            todo_id: Todo ID

        Returns:
            List of tag names

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = (
                self.supabase.table(self.table_name)
                .select("tag_name")
                .eq("todo_id", todo_id)
                .execute()
            )

            return [row["tag_name"] for row in response.data]

        except Exception as e:
            logger.error(f"Error fetching tags for todo {todo_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_tags_for_todo",
                details={"todo_id": todo_id}
            )

    async def update_tags_for_todo(self, todo_id: str, tag_names: List[str]) -> None:
        """
        Update tags for a todo (delete existing and insert new)

        Args:
            todo_id: Todo ID
            tag_names: List of tag names

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Delete existing tags
            self.supabase.table(self.table_name).delete().eq("todo_id", todo_id).execute()

            # Insert new tags
            if tag_names:
                tag_records = [
                    {"todo_id": todo_id, "tag_name": tag_name}
                    for tag_name in tag_names
                ]
                self.supabase.table(self.table_name).insert(tag_records).execute()

        except Exception as e:
            logger.error(f"Error updating tags for todo {todo_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_tags_for_todo",
                details={"todo_id": todo_id, "tag_names": tag_names}
            )

    async def get_todos_by_tags(
        self,
        tag_names: List[str],
        todo_ids: List[str]
    ) -> List[str]:
        """
        Get todo IDs that have any of the specified tags

        Args:
            tag_names: List of tag names to filter by
            todo_ids: List of todo IDs to search within

        Returns:
            List of todo IDs that have matching tags

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            if not todo_ids or not tag_names:
                return []

            response = (
                self.supabase.table(self.table_name)
                .select("todo_id")
                .in_("todo_id", todo_ids)
                .in_("tag_name", tag_names)
                .execute()
            )

            # Return unique todo IDs
            return list(set(row["todo_id"] for row in response.data))

        except Exception as e:
            logger.error(f"Error getting todos by tags: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_todos_by_tags",
                details={"tag_names": tag_names, "todo_ids_count": len(todo_ids)}
            )

