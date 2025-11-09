"""
LLM Cache Repository
Handles database operations for LLM response caching
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class LLMCacheRepository(BaseRepository):
    """Repository for llm_cache table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "llm_cache"

    async def get_by_cache_key(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response by cache key
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cache record dictionary or None if not found or expired
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("response")\
                .eq("cache_key", cache_key)\
                .gte("expires_at", datetime.utcnow().isoformat())\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching LLM cache for key {cache_key}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_cache_key",
                details={"cache_key": cache_key}
            )

    async def upsert(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert cache record
        
        Args:
            cache_data: Cache data dictionary
            
        Returns:
            Upserted cache record dictionary
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .upsert(cache_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise RepositoryError(
                message="Failed to upsert LLM cache",
                table=self.table_name,
                operation="upsert"
            )
        
        except Exception as e:
            logger.error(f"Error upserting LLM cache: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert",
                details=cache_data
            )


def get_llm_cache_repository() -> LLMCacheRepository:
    """Dependency injection function"""
    return LLMCacheRepository()

