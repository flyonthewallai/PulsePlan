"""
Canvas Integration Repository
Handles database operations for canvas_integrations table
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class CanvasIntegrationRepository(BaseRepository):
    """Repository for canvas_integrations table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "canvas_integrations"

    async def upsert_integration(
        self,
        integration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Insert or update Canvas integration record
        
        Args:
            integration_data: Integration data to save
        
        Returns:
            Saved integration record
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .upsert(integration_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to upsert Canvas integration",
                table=self.table_name,
                operation="upsert_integration"
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error upserting Canvas integration: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_integration",
                details={"integration_data": integration_data}
            )

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Canvas integration by user ID
        
        Args:
            user_id: User ID
        
        Returns:
            Integration record or None if not found
            
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
            logger.error(f"Error getting Canvas integration for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id}
            )


def get_canvas_integration_repository() -> CanvasIntegrationRepository:
    """Dependency injection function"""
    return CanvasIntegrationRepository()

