"""
Agent Task Repository
Handles database operations for agent tasks
"""
import logging
from typing import Dict, Any, Optional, List

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class AgentTaskRepository(BaseRepository):
    """Repository for agent_tasks table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "agent_tasks"

    async def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", task_id)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching agent task {task_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id",
                details={"task_id": task_id}
            )

    async def list_by_user(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List agent tasks for a user
        
        Args:
            user_id: User ID
            status_filter: Optional status filter
            limit: Maximum number of tasks to return
            
        Returns:
            List of task dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)
            
            if status_filter:
                query = query.eq("status", status_filter)
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error listing agent tasks for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="list_by_user",
                details={"user_id": user_id, "status_filter": status_filter}
            )

    async def upsert(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert agent task
        
        Args:
            task_data: Task data dictionary
            
        Returns:
            Upserted task dictionary
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .upsert(task_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise RepositoryError(
                message="Failed to upsert agent task",
                table=self.table_name,
                operation="upsert"
            )
        
        except Exception as e:
            logger.error(f"Error upserting agent task: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert",
                details=task_data
            )


def get_agent_task_repository() -> AgentTaskRepository:
    """Dependency injection function"""
    return AgentTaskRepository()

