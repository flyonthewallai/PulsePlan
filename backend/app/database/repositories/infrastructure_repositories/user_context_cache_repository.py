"""
User Context Cache Repository
Handles database operations for user context cache table
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class UserContextCacheRepository(BaseRepository):
    """Repository for user context cache operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "user_context_cache"

    async def get_valid_cache(
        self,
        user_id: str,
        expires_after: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get valid cached context for a user
        
        Args:
            user_id: User ID
            expires_after: Only return cache if expires_at is after this time
        
        Returns:
            Cache record dictionary or None if not found/expired
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)
            
            if expires_after:
                query = query.gte("expires_at", expires_after.isoformat())
            
            response = query.single().execute()
            
            if response.data:
                return response.data
            return None
        
        except Exception as e:
            # If no record found, single() raises an error - this is expected
            if "No rows" in str(e) or "PGRST116" in str(e):
                return None
            logger.error(f"Error fetching cache for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_valid_cache",
                details={"user_id": user_id}
            )

    async def upsert_cache(
        self,
        user_id: str,
        context_data: Dict[str, Any],
        expires_at: datetime,
        preferences_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upsert cache record for a user
        
        Args:
            user_id: User ID
            context_data: Context data to cache
            expires_at: Expiration datetime
            preferences_hash: Optional hash of preferences for invalidation
        
        Returns:
            Upserted cache record
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            cache_record = {
                "user_id": user_id,
                "context_data": context_data,
                "expires_at": expires_at.isoformat()
            }
            
            if preferences_hash:
                cache_record["preferences_hash"] = preferences_hash
            
            response = self.supabase.table(self.table_name)\
                .upsert(cache_record)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="No data returned after upsert",
                table=self.table_name,
                operation="upsert_cache"
            )
        
        except Exception as e:
            logger.error(f"Error upserting cache for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_cache",
                details={"user_id": user_id}
            )

    async def delete_by_user(self, user_id: str) -> bool:
        """
        Delete cache records for a user
        
        Args:
            user_id: User ID
        
        Returns:
            True if deletion succeeded
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("user_id", user_id)\
                .execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting cache for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_user",
                details={"user_id": user_id}
            )


def get_user_context_cache_repository() -> UserContextCacheRepository:
    """Dependency injection function"""
    return UserContextCacheRepository()

