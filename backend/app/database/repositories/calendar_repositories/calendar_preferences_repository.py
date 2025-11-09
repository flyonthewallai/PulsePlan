"""
Calendar Preferences Repository
Handles database operations for calendar_preferences table
"""
import logging
from typing import Dict, Any, List, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class CalendarPreferencesRepository(BaseRepository):
    """Repository for calendar_preferences table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "calendar_preferences"

    async def upsert(self, preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert calendar preferences
        
        Args:
            preferences_data: Preferences data to save
        
        Returns:
            Saved preferences record
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .upsert(preferences_data, on_conflict="user_id")\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to upsert calendar preferences",
                table=self.table_name,
                operation="upsert"
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error upserting calendar preferences: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert",
                details={"preferences_data": preferences_data}
            )

    async def get_users_with_auto_sync(self) -> List[Dict[str, Any]]:
        """
        Get users with auto-sync enabled
        
        Returns:
            List of user preference records with auto-sync enabled
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("user_id, sync_frequency_minutes, updated_at")\
                .eq("auto_sync_enabled", True)\
                .execute()
            
            return response.data if response.data else []
        
        except Exception as e:
            logger.error(f"Error getting users with auto-sync: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_users_with_auto_sync"
            )


def get_calendar_preferences_repository() -> CalendarPreferencesRepository:
    """Dependency injection function"""
    return CalendarPreferencesRepository()

