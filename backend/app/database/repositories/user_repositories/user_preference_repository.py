"""
User Preference Repository
Handles database operations for user preferences
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class UserPreferenceRepository(BaseRepository):
    """Repository for user_preferences table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "user_preferences"

    async def get_by_category_and_key(
        self,
        user_id: str,
        category: str,
        preference_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific preference by category and key
        
        Args:
            user_id: User ID
            category: Preference category
            preference_key: Preference key
        
        Returns:
            Preference dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.from_(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("category", category)\
                .eq("preference_key", preference_key)\
                .eq("is_active", True)\
                .order("priority", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(
                f"Error fetching preference {category}.{preference_key} for user {user_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_category_and_key",
                details={"user_id": user_id, "category": category, "key": preference_key}
            )

    async def get_preference_value_rpc(
        self,
        user_id: str,
        category: str,
        preference_key: str
    ) -> Optional[Any]:
        """
        Get preference value using RPC function
        
        Args:
            user_id: User ID
            category: Preference category
            preference_key: Preference key
        
        Returns:
            Preference value or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.rpc("get_preference_value", {
                "p_user_id": user_id,
                "p_category": category,
                "p_preference_key": preference_key
            }).execute()
            
            return response.data if response.data else None
        
        except Exception as e:
            logger.error(
                f"Error fetching preference value via RPC for user {user_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_preference_value_rpc",
                details={"user_id": user_id, "category": category, "key": preference_key}
            )

    async def get_all_by_category(
        self,
        user_id: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Get all preferences in a category
        
        Args:
            user_id: User ID
            category: Preference category
        
        Returns:
            List of preference dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.from_(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("category", category)\
                .eq("is_active", True)\
                .order("priority", desc=True)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching preferences for category {category}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_all_by_category",
                details={"user_id": user_id, "category": category}
            )

    async def get_all_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all preferences for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of all preference dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.from_(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .order("category, priority", desc=False)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching all preferences for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_all_by_user",
                details={"user_id": user_id}
            )

    async def upsert_preference(
        self,
        user_id: str,
        category: str,
        preference_key: str,
        preference_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Insert or update a preference
        
        Args:
            user_id: User ID
            category: Preference category
            preference_key: Preference key
            preference_data: Preference fields
        
        Returns:
            Created/updated preference dictionary or None
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Check if exists
            existing = await self.get_by_category_and_key(user_id, category, preference_key)
            
            if existing:
                # Update
                update_data = {**preference_data, "updated_at": datetime.utcnow().isoformat()}
                response = self.supabase.from_(self.table_name)\
                    .update(update_data)\
                    .eq("id", existing["id"])\
                    .execute()
            else:
                # Insert
                full_data = {
                    "user_id": user_id,
                    "category": category,
                    "preference_key": preference_key,
                    **preference_data
                }
                response = self.supabase.from_(self.table_name)\
                    .insert(full_data)\
                    .execute()
            
            return response.data[0] if response.data else None
        
        except Exception as e:
            logger.error(
                f"Error upserting preference {category}.{preference_key}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_preference",
                details={"user_id": user_id, "category": category, "key": preference_key}
            )

    async def delete_preference(
        self,
        user_id: str,
        category: str,
        preference_key: str
    ) -> bool:
        """
        Delete a preference (soft delete by setting is_active=False)
        
        Args:
            user_id: User ID
            category: Preference category
            preference_key: Preference key
        
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.from_(self.table_name)\
                .update({"is_active": False, "updated_at": datetime.utcnow().isoformat()})\
                .eq("user_id", user_id)\
                .eq("category", category)\
                .eq("preference_key", preference_key)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(
                f"Error deleting preference {category}.{preference_key}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_preference",
                details={"user_id": user_id, "category": category, "key": preference_key}
            )

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences record by user ID (for structured preferences table)
        
        Args:
            user_id: User ID
        
        Returns:
            User preferences dict or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error getting user preferences for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user",
                details={"user_id": user_id}
            )

    async def check_exists(self, user_id: str) -> bool:
        """
        Check if user preferences exist
        
        Args:
            user_id: User ID
        
        Returns:
            True if preferences exist, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("user_id")\
                .eq("user_id", user_id)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error checking user preferences existence for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="check_exists",
                details={"user_id": user_id}
            )

    async def upsert_preferences(
        self,
        user_id: str,
        preferences_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Insert or update user preferences (for structured preferences table)
        
        Args:
            user_id: User ID
            preferences_data: Preferences data to save
        
        Returns:
            Saved preferences data
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Check if preferences exist
            existing = await self.check_exists(user_id)
            
            if existing:
                # Update existing
                response = self.supabase.table(self.table_name)\
                    .update(preferences_data)\
                    .eq("user_id", user_id)\
                    .execute()
            else:
                # Create new
                response = self.supabase.table(self.table_name)\
                    .insert(preferences_data)\
                    .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to upsert user preferences",
                table=self.table_name,
                operation="upsert_preferences",
                details={"user_id": user_id}
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error upserting user preferences for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="upsert_preferences",
                details={"user_id": user_id}
            )


def get_user_preference_repository() -> UserPreferenceRepository:
    """Dependency injection function"""
    return UserPreferenceRepository()

