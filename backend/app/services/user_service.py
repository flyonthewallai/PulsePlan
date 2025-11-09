"""
User Service
Business logic for user profile and data operations
"""
import logging
from typing import Dict, Any, Optional, List

from app.database.repositories.user_repositories.user_repository import UserRepository
from app.database.repositories.task_repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related operations"""
    
    def __init__(
        self,
        user_repository: Optional[UserRepository] = None,
        task_repository: Optional[TaskRepository] = None
    ):
        """Initialize with optional repositories for dependency injection"""
        self._user_repository = user_repository
        self._task_repository = task_repository
    
    @property
    def user_repository(self) -> UserRepository:
        """Lazy-load user repository"""
        if self._user_repository is None:
            from app.database.repositories.user_repositories.user_repository import get_user_repository
            self._user_repository = get_user_repository()
        return self._user_repository
    
    @property
    def task_repository(self) -> TaskRepository:
        """Lazy-load task repository"""
        if self._task_repository is None:
            from app.database.repositories.task_repositories.task_repository import get_task_repository
            self._task_repository = get_task_repository()
        return self._task_repository
    
    async def get_user_profile(
        self,
        user_id: str,
        fallback_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user profile from auth.users
        
        Args:
            user_id: User ID
            fallback_email: Fallback email if auth lookup fails
        
        Returns:
            User profile dictionary with keys: user_id, email, name, city, timezone, preferences
        """
        try:
            user_data = await self.user_repository.get_auth_user(user_id)
            
            if not user_data:
                logger.warning(f"User {user_id} not found in auth, using fallback")
                return {
                    "user_id": user_id,
                    "email": fallback_email or "unknown",
                    "name": "User",
                    "city": None,
                    "timezone": None,
                    "preferences": {
                        "theme": "light",
                        "notifications": True,
                        "language": "en"
                    }
                }
            
            # Extract user metadata
            metadata = user_data.get("user_metadata", {})
            
            return {
                "user_id": user_id,
                "email": user_data.get("email"),
                "name": metadata.get("full_name") or metadata.get("name") or "User",
                "city": metadata.get("city"),
                "timezone": metadata.get("timezone"),
                "preferences": metadata.get("preferences", {
                    "theme": "light",
                    "notifications": True,
                    "language": "en"
                })
            }
        
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}", exc_info=True)
            # Return fallback profile on error
            return {
                "user_id": user_id,
                "email": fallback_email or "unknown",
                "name": "User",
                "city": None,
                "timezone": None,
                "preferences": {
                    "theme": "light",
                    "notifications": True,
                    "language": "en"
                }
            }
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user record from users table

        Args:
            user_id: User ID

        Returns:
            User dictionary with fields including timezone, or None if not found
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            return user
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}", exc_info=True)
            return None

    async def get_user_tasks(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get all tasks for a user with course information

        Args:
            user_id: User ID
            filters: Optional filters for tasks

        Returns:
            Dictionary with tasks list and count
        """
        try:
            tasks = await self.task_repository.get_by_user(
                user_id=user_id,
                filters=filters,
                limit=None  # Get all tasks
            )

            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")

            return {
                "tasks": tasks,
                "count": len(tasks)
            }

        except Exception as e:
            logger.error(f"Error fetching tasks for user {user_id}: {e}", exc_info=True)
            # Return empty on error
            return {
                "tasks": [],
                "count": 0
            }


def get_user_service() -> UserService:
    """Dependency injection function"""
    return UserService()

