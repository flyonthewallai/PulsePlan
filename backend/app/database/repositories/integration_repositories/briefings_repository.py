"""
Briefings repository for database operations
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
from uuid import UUID

from app.config.database.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class BriefingsRepository:
    """Repository for briefing database operations"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def get_briefing_for_date(
        self,
        user_id: UUID,
        briefing_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get briefing for a specific date

        Args:
            user_id: User ID
            briefing_date: Date to get briefing for

        Returns:
            Briefing data or None if not found
        """
        try:
            response = self.supabase.table("briefings").select("*").eq(
                "user_id", str(user_id)
            ).eq(
                "briefing_date", briefing_date.isoformat()
            ).maybe_single().execute()

            if response.data:
                logger.info(f"Retrieved briefing for user {user_id} on {briefing_date}")
                return response.data

            logger.info(f"No briefing found for user {user_id} on {briefing_date}")
            return None

        except Exception as e:
            logger.error(f"Error getting briefing for user {user_id} on {briefing_date}: {e}")
            return None

    async def get_todays_briefing(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get today's briefing for user

        Args:
            user_id: User ID

        Returns:
            Today's briefing data or None
        """
        today = date.today()
        return await self.get_briefing_for_date(user_id, today)

    async def save_briefing(
        self,
        user_id: UUID,
        briefing_date: date,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save or update briefing for a date

        Args:
            user_id: User ID
            briefing_date: Date of briefing
            content: Briefing content (JSONB)

        Returns:
            Saved briefing data
        """
        try:
            briefing_data = {
                "user_id": str(user_id),
                "briefing_date": briefing_date.isoformat(),
                "content": content,
                "generated_at": datetime.utcnow().isoformat()
            }

            # Use upsert to insert or update
            response = self.supabase.table("briefings").upsert(
                briefing_data,
                on_conflict="user_id,briefing_date"
            ).execute()

            if response.data:
                logger.info(f"Saved briefing for user {user_id} on {briefing_date}")
                return response.data[0] if isinstance(response.data, list) else response.data

            raise Exception("Failed to save briefing: No data returned")

        except Exception as e:
            logger.error(f"Error saving briefing for user {user_id} on {briefing_date}: {e}")
            raise

    async def get_recent_briefings(
        self,
        user_id: UUID,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get recent briefings for user

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of recent briefings
        """
        try:
            cutoff_date = date.today() - timedelta(days=days)

            response = self.supabase.table("briefings").select("*").eq(
                "user_id", str(user_id)
            ).gte(
                "briefing_date", cutoff_date.isoformat()
            ).order(
                "briefing_date", desc=True
            ).execute()

            logger.info(f"Retrieved {len(response.data)} recent briefings for user {user_id}")
            return response.data

        except Exception as e:
            logger.error(f"Error getting recent briefings for user {user_id}: {e}")
            return []

    async def delete_old_briefings(self, days: int = 30) -> int:
        """
        Delete briefings older than specified days (cleanup job)

        Args:
            days: Delete briefings older than this many days

        Returns:
            Number of briefings deleted
        """
        try:
            cutoff_date = date.today() - timedelta(days=days)

            response = self.supabase.table("briefings").delete().lt(
                "briefing_date", cutoff_date.isoformat()
            ).execute()

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Deleted {deleted_count} briefings older than {cutoff_date}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting old briefings: {e}")
            return 0

    async def delete_briefing(
        self,
        user_id: UUID,
        briefing_date: date
    ) -> bool:
        """
        Delete a specific briefing

        Args:
            user_id: User ID
            briefing_date: Date of briefing to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            response = self.supabase.table("briefings").delete().eq(
                "user_id", str(user_id)
            ).eq(
                "briefing_date", briefing_date.isoformat()
            ).execute()

            logger.info(f"Deleted briefing for user {user_id} on {briefing_date}")
            return True

        except Exception as e:
            logger.error(f"Error deleting briefing for user {user_id} on {briefing_date}: {e}")
            return False


# Global repository instance
_briefings_repository: Optional[BriefingsRepository] = None

def get_briefings_repository() -> BriefingsRepository:
    """Get global briefings repository instance"""
    global _briefings_repository
    if _briefings_repository is None:
        _briefings_repository = BriefingsRepository()
    return _briefings_repository
