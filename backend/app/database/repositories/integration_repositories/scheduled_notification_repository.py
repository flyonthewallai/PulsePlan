"""
Scheduled Notification Repository
Handles database operations for scheduled_notifications table
"""
import logging
from typing import Dict, Any

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class ScheduledNotificationRepository(BaseRepository):
    """Repository for scheduled_notifications table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "scheduled_notifications"

    async def create(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a scheduled notification
        
        Args:
            notification_data: Notification data to save
        
        Returns:
            Created notification record
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .insert(notification_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to create scheduled notification",
                table=self.table_name,
                operation="create"
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error creating scheduled notification: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create",
                details={"notification_data": notification_data}
            )


def get_scheduled_notification_repository() -> ScheduledNotificationRepository:
    """Dependency injection function"""
    return ScheduledNotificationRepository()

