"""
Focus Session Repository
Handles database operations for focus sessions
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class FocusSessionRepository(BaseRepository):
    """Repository for focus_sessions table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "focus_sessions"

    async def create_session(
        self,
        session_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new focus session
        
        Args:
            session_data: Session data dictionary
        
        Returns:
            Created session dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .insert(session_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error creating focus session: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create_session",
                details={"session_data": session_data}
            )

    async def get_by_id_and_user(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a focus session by ID and user
        
        Args:
            session_id: Session ID
            user_id: User ID
        
        Returns:
            Session dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        
        except Exception as e:
            logger.error(f"Error fetching session {session_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_and_user",
                details={"session_id": session_id, "user_id": user_id}
            )

    async def update_session(
        self,
        session_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a focus session
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            update_data: Fields to update
        
        Returns:
            Updated session dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_session",
                details={"session_id": session_id, "user_id": user_id}
            )

    async def get_by_user(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get focus sessions for a user with optional filters
        
        Args:
            user_id: User ID
            filters: Optional filters (date ranges, session_type, etc.)
            limit: Result limit
        
        Returns:
            List of session dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)
            
            # Apply filters if provided
            if filters:
                if filters.get("start_date"):
                    query = query.gte("start_time", filters["start_date"])
                if filters.get("end_date"):
                    query = query.lte("start_time", filters["end_date"])
                if filters.get("session_type"):
                    query = query.eq("session_type", filters["session_type"])
                if filters.get("was_completed") is not None:
                    query = query.eq("was_completed", filters["was_completed"])
            
            # Order and limit
            query = query.order("start_time", desc=True).limit(limit)
            
            response = query.execute()
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching sessions for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id, "filters": filters}
            )

    async def get_session_count(self, user_id: str) -> int:
        """
        Get count of focus sessions for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Number of sessions
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            
            return response.count if hasattr(response, "count") else 0
        
        except Exception as e:
            logger.error(f"Error getting session count for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_session_count",
                details={"user_id": user_id}
            )

    async def get_user_ids_with_recent_sessions(
        self,
        cutoff_datetime: datetime,
        limit: int = 100
    ) -> List[str]:
        """
        Get user IDs who have sessions created after cutoff time
        
        Args:
            cutoff_datetime: Cutoff datetime
            limit: Maximum number of user IDs to return
        
        Returns:
            List of unique user IDs
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("user_id")\
                .gte("created_at", cutoff_datetime.isoformat())\
                .execute()
            
            if not response.data:
                return []
            
            # Deduplicate user_ids
            user_ids = list(set(row["user_id"] for row in response.data))
            return user_ids[:limit]
        
        except Exception as e:
            logger.error(f"Error getting users with recent sessions: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_user_ids_with_recent_sessions",
                details={"cutoff_datetime": cutoff_datetime.isoformat()}
            )

    async def delete_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a focus session
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
        
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_session",
                details={"session_id": session_id, "user_id": user_id}
            )


class UserFocusProfileRepository(BaseRepository):
    """Repository for user_focus_profiles table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "user_focus_profiles"

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get focus profile for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Focus profile dictionary or None
            
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
            logger.error(f"Error fetching focus profile for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id}
            )

    async def get_users_with_stale_profiles(
        self,
        cutoff_datetime: datetime,
        limit: int = 100
    ) -> List[str]:
        """
        Get user IDs who have recent sessions but stale or missing profiles
        
        Args:
            cutoff_datetime: Cutoff datetime for considering profiles stale
            limit: Maximum number of user IDs to return
        
        Returns:
            List of user IDs
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Use RPC for complex join query
            query = f"""
                SELECT DISTINCT fs.user_id
                FROM focus_sessions fs
                LEFT JOIN user_focus_profiles ufp ON fs.user_id = ufp.user_id
                WHERE fs.created_at > '{cutoff_datetime.isoformat()}'
                AND (
                    ufp.last_computed_at IS NULL 
                    OR ufp.last_computed_at < '{cutoff_datetime.isoformat()}'
                )
                LIMIT {limit}
            """
            
            response = self.supabase.rpc("execute_sql", {"query": query}).execute()
            
            if response.data:
                return [row["user_id"] for row in response.data]
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting users with stale profiles: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_users_with_stale_profiles",
                details={"cutoff_datetime": cutoff_datetime.isoformat()}
            )


def get_focus_session_repository() -> FocusSessionRepository:
    """Dependency injection function"""
    return FocusSessionRepository()


def get_user_focus_profile_repository() -> UserFocusProfileRepository:
    """Dependency injection function"""
    return UserFocusProfileRepository()

