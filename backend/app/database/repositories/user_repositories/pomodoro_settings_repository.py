"""
Pomodoro Settings Repository
Handles database operations for user Pomodoro settings
"""
import logging
from typing import Dict, Any, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class PomodoroSettingsRepository(BaseRepository):
    """Repository for user_pomodoro_settings table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "user_pomodoro_settings"

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Pomodoro settings for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Settings dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        
        except Exception as e:
            logger.error(f"Error fetching pomodoro settings for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id}
            )

    async def upsert_settings(
        self,
        user_id: str,
        settings_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Insert or update Pomodoro settings for a user
        
        Args:
            user_id: User ID
            settings_data: Settings fields
        
        Returns:
            Updated settings dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            data = {**settings_data, "user_id": user_id}
            response = self.supabase.table(self.table_name)\
                .upsert(data, on_conflict="user_id")\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error upserting pomodoro settings for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_settings",
                details={"user_id": user_id, "settings": settings_data}
            )


def get_pomodoro_settings_repository() -> PomodoroSettingsRepository:
    """Dependency injection function"""
    return PomodoroSettingsRepository()

