"""
Calendar Sync Status Repository
Handles database operations for calendar_sync_status table
"""
import logging
from typing import Dict, Any, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class CalendarSyncStatusRepository(BaseRepository):
    """Repository for calendar_sync_status table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "calendar_sync_status"

    async def upsert(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert calendar sync status
        
        Args:
            status_data: Status data to save
        
        Returns:
            Saved status record
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .upsert(status_data, on_conflict="user_id")\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to upsert calendar sync status",
                table=self.table_name,
                operation="upsert"
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error upserting calendar sync status: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert",
                details={"status_data": status_data}
            )

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get calendar sync status by user ID
        
        Args:
            user_id: User ID
        
        Returns:
            Status record or None if not found
            
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
            logger.error(f"Error getting calendar sync status for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id}
            )

    async def delete_old_records(self, cutoff_datetime: str) -> bool:
        """
        Delete old sync status records
        
        Args:
            cutoff_datetime: ISO datetime string for cutoff
        
        Returns:
            True if successful
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .lt("last_sync_at", cutoff_datetime)\
                .execute()
            
            return bool(response.data is not None)
        
        except Exception as e:
            logger.error(f"Error deleting old sync status records: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_old_records",
                details={"cutoff_datetime": cutoff_datetime}
            )


def get_calendar_sync_status_repository() -> CalendarSyncStatusRepository:
    """Dependency injection function"""
    return CalendarSyncStatusRepository()

