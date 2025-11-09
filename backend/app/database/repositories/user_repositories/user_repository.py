"""
User Repository
Handles all database operations for users
"""
import logging
from typing import Dict, Any, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for user database operations
    
    Handles CRUD operations and queries for users table.
    """

    @property
    def table_name(self) -> str:
        """Return the table name for users"""
        return "users"

    async def get_subscription_status(self, user_id: str) -> Optional[str]:
        """
        Get user subscription status
        
        Args:
            user_id: User ID
        
        Returns:
            Subscription status string or None if user not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("subscription_status")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if response.data:
                return response.data.get("subscription_status")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching subscription status for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_subscription_status",
                details={"user_id": user_id}
            )

    async def is_premium(self, user_id: str) -> bool:
        """
        Check if user has premium subscription
        
        Args:
            user_id: User ID
        
        Returns:
            True if user has premium subscription, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            status = await self.get_subscription_status(user_id)
            return status in ["active", "premium"]
        
        except Exception as e:
            logger.error(f"Error checking premium status for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="is_premium",
                details={"user_id": user_id}
            )
    
    async def get_auth_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from Supabase auth.users
        
        Args:
            user_id: User ID
        
        Returns:
            User auth data dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            auth_response = self.supabase.auth.admin.get_user_by_id(user_id)
            
            if not auth_response.user:
                return None
            
            user = auth_response.user
            return {
                "id": user.id,
                "email": user.email,
                "user_metadata": user.user_metadata or {},
                "created_at": user.created_at
            }
        
        except Exception as e:
            logger.error(f"Error fetching auth user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table="auth.users",
                operation="get_auth_user",
                details={"user_id": user_id}
            )
    
    async def update_subscription(
        self,
        user_id: str,
        subscription_data: Dict[str, Any]
    ) -> bool:
        """
        Update user subscription information
        
        Args:
            user_id: User ID
            subscription_data: Dictionary with subscription fields to update
        
        Returns:
            True if update successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(subscription_data)\
                .eq("id", user_id)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error updating subscription for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_subscription",
                details={"user_id": user_id, "data": subscription_data}
            )
    
    async def get_subscription_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription data for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Subscription data dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("subscription_status, apple_transaction_id, subscription_expires_at")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        
        except Exception as e:
            logger.error(f"Error fetching subscription for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_subscription_data",
                details={"user_id": user_id}
            )
    
    async def get_full_name(self, user_id: str) -> Optional[str]:
        """
        Get user's full name from users table
        
        Args:
            user_id: User ID
        
        Returns:
            Full name string or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("full_name")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if response.data:
                return response.data.get("full_name")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching full name for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_full_name",
                details={"user_id": user_id}
            )

    async def get_timezone_and_working_hours(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's timezone and working hours
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with 'timezone' and 'working_hours' keys, or None if user not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("timezone, working_hours")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if response.data:
                return {
                    "timezone": response.data.get("timezone", "UTC"),
                    "working_hours": response.data.get("working_hours")
                }
            return None
        
        except Exception as e:
            logger.error(f"Error fetching timezone and working hours for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_timezone_and_working_hours",
                details={"user_id": user_id}
            )


def get_user_repository() -> UserRepository:
    """
    Dependency injection function for UserRepository
    
    Returns:
        UserRepository instance
    """
    return UserRepository()

