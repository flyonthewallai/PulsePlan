"""
Hobbies Repository
Database operations for user hobbies
"""
import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)


class HobbyDB:
    """Database model for user hobby"""
    id: str
    user_id: str
    name: str
    icon: str
    preferred_time: str
    specific_time: Optional[dict]
    days: List[str]
    duration_min: int
    duration_max: int
    flexibility: str
    notes: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HobbiesRepository:
    """Repository for user hobbies CRUD operations"""

    def __init__(self):
        self.supabase = get_supabase()

    async def get_user_hobbies(
        self,
        user_id: str,
        include_inactive: bool = False
    ) -> List[HobbyDB]:
        """
        Get all hobbies for a user

        Args:
            user_id: User ID
            include_inactive: Whether to include inactive hobbies

        Returns:
            List of user hobbies
        """
        try:
            query = self.supabase.table('user_hobbies').select('*').eq('user_id', user_id)

            if not include_inactive:
                query = query.eq('is_active', True)

            result = query.order('created_at', desc=False).execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching hobbies for user {user_id}: {str(e)}")
            raise

    async def get_hobby_by_id(
        self,
        hobby_id: str,
        user_id: str
    ) -> Optional[HobbyDB]:
        """
        Get a specific hobby by ID

        Args:
            hobby_id: Hobby ID
            user_id: User ID (for security check)

        Returns:
            Hobby data or None
        """
        try:
            result = self.supabase.table('user_hobbies').select('*').eq('id', hobby_id).eq('user_id', user_id).single().execute()
            return result.data

        except Exception as e:
            logger.error(f"Error fetching hobby {hobby_id}: {str(e)}")
            return None

    async def create_hobby(
        self,
        user_id: str,
        name: str,
        icon: str,
        preferred_time: str,
        days: List[str],
        duration_min: int,
        duration_max: int,
        flexibility: str,
        specific_time: Optional[dict] = None,
        notes: str = ""
    ) -> HobbyDB:
        """
        Create a new hobby

        Args:
            user_id: User ID
            name: Hobby name
            icon: Icon identifier
            preferred_time: Preferred time of day
            days: List of days
            duration_min: Minimum duration in minutes
            duration_max: Maximum duration in minutes
            flexibility: Scheduling flexibility
            specific_time: Optional specific time window
            notes: Additional notes

        Returns:
            Created hobby data
        """
        try:
            hobby_data = {
                'user_id': user_id,
                'name': name,
                'icon': icon,
                'preferred_time': preferred_time,
                'specific_time': specific_time,
                'days': days,
                'duration_min': duration_min,
                'duration_max': duration_max,
                'flexibility': flexibility,
                'notes': notes,
                'is_active': True
            }

            result = self.supabase.table('user_hobbies').insert(hobby_data).execute()

            if not result.data:
                raise Exception("Failed to create hobby")

            return result.data[0]

        except Exception as e:
            logger.error(f"Error creating hobby for user {user_id}: {str(e)}")
            raise

    async def update_hobby(
        self,
        hobby_id: str,
        user_id: str,
        updates: dict
    ) -> HobbyDB:
        """
        Update a hobby

        Args:
            hobby_id: Hobby ID
            user_id: User ID (for security check)
            updates: Dictionary of fields to update

        Returns:
            Updated hobby data
        """
        try:
            # Only allow updating specific fields
            allowed_fields = {
                'name', 'icon', 'preferred_time', 'specific_time', 'days',
                'duration_min', 'duration_max', 'flexibility', 'notes', 'is_active'
            }
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

            result = self.supabase.table('user_hobbies').update(filtered_updates).eq('id', hobby_id).eq('user_id', user_id).execute()

            if not result.data:
                raise Exception("Hobby not found or update failed")

            return result.data[0]

        except Exception as e:
            logger.error(f"Error updating hobby {hobby_id}: {str(e)}")
            raise

    async def delete_hobby(
        self,
        hobby_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a hobby (soft or hard delete)

        Args:
            hobby_id: Hobby ID
            user_id: User ID (for security check)
            soft_delete: If True, mark as inactive; if False, permanently delete

        Returns:
            True if successful
        """
        try:
            if soft_delete:
                result = self.supabase.table('user_hobbies').update({'is_active': False}).eq('id', hobby_id).eq('user_id', user_id).execute()
            else:
                result = self.supabase.table('user_hobbies').delete().eq('id', hobby_id).eq('user_id', user_id).execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error deleting hobby {hobby_id}: {str(e)}")
            raise


# Singleton instance
_hobbies_repository: Optional[HobbiesRepository] = None


def get_hobbies_repository() -> HobbiesRepository:
    """Get or create the hobbies repository singleton"""
    global _hobbies_repository
    if _hobbies_repository is None:
        _hobbies_repository = HobbiesRepository()
    return _hobbies_repository
