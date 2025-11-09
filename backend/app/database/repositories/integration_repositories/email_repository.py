"""
Email Repository
Handles database operations for emails
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class EmailRepository(BaseRepository):
    """Repository for emails table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "emails"

    async def get_by_user_since_date(
        self,
        user_id: str,
        since_date: datetime,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get emails for a user since a specific date
        
        Args:
            user_id: User ID
            since_date: Start date for filtering
            limit: Optional result limit
        
        Returns:
            List of email dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("subject, sender, priority, received_at, is_unread")\
                .eq("user_id", user_id)\
                .gte("received_at", since_date.isoformat())
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching emails for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user_since_date",
                details={"user_id": user_id, "since_date": since_date}
            )


def get_email_repository() -> EmailRepository:
    """Dependency injection function"""
    return EmailRepository()

