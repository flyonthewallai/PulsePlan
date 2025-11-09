"""
Notification Log Repository
Handles database operations for notification logs
"""
import logging
from typing import Dict, Any

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class NotificationLogRepository(BaseRepository):
    """Repository for notification_logs table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "notification_logs"

    async def create_log(
        self,
        log_data: Dict[str, Any]
    ) -> bool:
        """
        Create a notification log entry
        
        Args:
            log_data: Log entry data
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .insert(log_data)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error creating notification log: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create_log",
                details={"log_data": log_data}
            )


def get_notification_log_repository() -> NotificationLogRepository:
    """Dependency injection function"""
    return NotificationLogRepository()

