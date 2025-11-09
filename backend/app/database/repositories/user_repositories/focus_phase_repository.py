"""
Focus Phase Repository
Handles database operations for focus session phases
"""
import logging
from typing import Dict, Any, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class FocusPhaseRepository(BaseRepository):
    """Repository for focus_session_phases table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "focus_session_phases"

    async def create_phase(
        self,
        phase_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new focus phase
        
        Args:
            phase_data: Phase data including session_id, user_id, phase_type, etc.
        
        Returns:
            Created phase dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .insert(phase_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error creating focus phase: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create_phase",
                details={"phase_data": phase_data}
            )

    async def update_phase(
        self,
        phase_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a focus phase
        
        Args:
            phase_id: Phase ID
            user_id: User ID (for authorization)
            update_data: Fields to update
        
        Returns:
            Updated phase dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("id", phase_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating focus phase {phase_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_phase",
                details={"phase_id": phase_id, "user_id": user_id}
            )


def get_focus_phase_repository() -> FocusPhaseRepository:
    """Dependency injection function"""
    return FocusPhaseRepository()

