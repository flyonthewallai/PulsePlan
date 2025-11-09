"""
Course Repository
Handles all database operations for courses
"""
import logging
from typing import Dict, Any, List, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class CourseRepository(BaseRepository):
    """
    Repository for course database operations
    
    Handles CRUD operations and queries for courses table.
    Courses represent academic courses that users are enrolled in.
    """

    @property
    def table_name(self) -> str:
        """Return the table name for courses"""
        return "courses"

    async def get_by_user_id(
        self,
        user_id: str,
        order_by: str = "name"
    ) -> List[Dict[str, Any]]:
        """
        Get all courses for a specific user, ordered by name
        
        Args:
            user_id: User ID to filter by
            order_by: Field to order by (default: "name")
        
        Returns:
            List of course dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .order(order_by)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching courses for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user_id",
                details={"user_id": user_id, "order_by": order_by}
            )

    async def get_by_id_and_user(
        self,
        course_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a course by ID, ensuring it belongs to the specified user
        
        Args:
            course_id: Course ID
            user_id: User ID for ownership verification
        
        Returns:
            Course dictionary or None if not found/unauthorized
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", course_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching course {course_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_and_user",
                details={"course_id": course_id, "user_id": user_id}
            )

    async def update_by_id_and_user(
        self,
        course_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a course by ID, ensuring it belongs to the specified user
        
        Args:
            course_id: Course ID
            user_id: User ID for ownership verification
            data: Update data dictionary
        
        Returns:
            Updated course dictionary or None if not found/unauthorized
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(data)\
                .eq("id", course_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating course {course_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_by_id_and_user",
                details={"course_id": course_id, "user_id": user_id, "data": data}
            )

    async def find_by_name(
        self,
        course_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a course by name (case-insensitive partial match)
        
        Tries exact match first, then partial match.
        
        Args:
            course_name: Course name to search for
            user_id: User ID for ownership verification
        
        Returns:
            Course dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            # Try exact match first (case-insensitive)
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .ilike("name", course_name)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            # Try partial match
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .ilike("name", f"%{course_name}%")\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding course by name '{course_name}' for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="find_by_name",
                details={"course_name": course_name, "user_id": user_id}
            )


def get_course_repository() -> CourseRepository:
    """
    Dependency injection function for CourseRepository
    
    Returns:
        CourseRepository instance
    """
    return CourseRepository()

