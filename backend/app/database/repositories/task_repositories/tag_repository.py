"""
Tag Repository
Database access layer for tag operations
"""
import logging
from typing import Dict, Any, List, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class PredefinedTagRepository(BaseRepository):
    """Repository for predefined_tags table"""

    @property
    def table_name(self) -> str:
        return "predefined_tags"

    async def get_all_predefined(self) -> List[Dict[str, Any]]:
        """
        Get all predefined tags

        Returns:
            List of predefined tag dictionaries
        """
        return await self.get_all()

    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get predefined tags by category

        Args:
            category: Tag category

        Returns:
            List of predefined tag dictionaries
        """
        return await self.get_all(filters={"category": category})


class UserTagRepository(BaseRepository):
    """Repository for user_tags table"""

    @property
    def table_name(self) -> str:
        return "user_tags"

    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all tags for a specific user

        Args:
            user_id: User ID

        Returns:
            List of user tag dictionaries
        """
        return await self.get_all(filters={"user_id": user_id})

    async def get_by_name(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a user tag by name

        Args:
            user_id: User ID
            name: Tag name (case-insensitive)

        Returns:
            Tag dictionary or None if not found
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).eq("name", name.lower()).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching user tag by name: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_name",
                details={"user_id": user_id, "name": name}
            )

    async def create_user_tag(self, user_id: str, name: str) -> Dict[str, Any]:
        """
        Create a new user tag

        Args:
            user_id: User ID
            name: Tag name

        Returns:
            Created tag dictionary
        """
        tag_data = {
            "user_id": user_id,
            "name": name.lower()
        }
        return await self.create(tag_data)

    async def delete_user_tag(self, user_id: str, tag_id: str) -> bool:
        """
        Delete a user tag (with user ownership check)

        Args:
            user_id: User ID
            tag_id: Tag ID

        Returns:
            True if deleted, False if not found
        """
        try:
            response = self.supabase.table(self.table_name).delete().eq("id", tag_id).eq("user_id", user_id).execute()

            return response.data is not None and len(response.data) > 0

        except Exception as e:
            logger.error(f"Error deleting user tag: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_user_tag",
                details={"user_id": user_id, "tag_id": tag_id}
            )


class TodoTagRepository(BaseRepository):
    """Repository for todo_tags junction table"""

    @property
    def table_name(self) -> str:
        return "todo_tags"

    async def get_tags_for_todo(self, todo_id: str) -> List[Dict[str, Any]]:
        """
        Get all tags associated with a todo

        Args:
            todo_id: Todo ID

        Returns:
            List of tag associations
        """
        return await self.get_all(filters={"todo_id": todo_id})

    async def get_tag_usage_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get tag usage statistics for a user

        Args:
            user_id: User ID

        Returns:
            List of tag usage records
        """
        try:
            # First get user's todo IDs
            user_todos_response = self.supabase.table("todos").select("id").eq("user_id", user_id).execute()
            todo_ids = [todo["id"] for todo in (user_todos_response.data or [])]

            if not todo_ids:
                return []

            # Query junction table for tag usage
            response = self.supabase.table(self.table_name).select("tag_name").in_("todo_id", todo_ids).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching tag usage: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_tag_usage_for_user",
                details={"user_id": user_id}
            )


def get_predefined_tag_repository() -> PredefinedTagRepository:
    """Factory function for predefined tag repository"""
    return PredefinedTagRepository()


def get_user_tag_repository() -> UserTagRepository:
    """Factory function for user tag repository"""
    return UserTagRepository()


def get_todo_tag_repository() -> TodoTagRepository:
    """Factory function for todo tag repository"""
    return TodoTagRepository()
