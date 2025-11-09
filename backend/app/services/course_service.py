"""
Course Service
Business logic for course management
"""
import logging
from typing import Dict, Any, List, Optional

from app.database.repositories.user_repositories import CourseRepository, get_course_repository
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class CourseService:
    """
    Service layer for course operations
    
    Handles business logic for course management including:
    - Listing user courses
    - Updating course properties (color, etc.)
    - Validation and authorization
    """

    def __init__(self, repo: CourseRepository = None):
        """
        Initialize CourseService
        
        Args:
            repo: Optional CourseRepository instance (for dependency injection/testing)
        """
        self.repo = repo or CourseRepository()

    async def list_user_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all courses for a user, ordered by name
        
        Args:
            user_id: User ID
        
        Returns:
            List of course dictionaries
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            courses = await self.repo.get_by_user_id(user_id, order_by="name")
            logger.info(f"Listed {len(courses)} courses for user {user_id}")
            return courses
        
        except Exception as e:
            logger.error(f"Failed to list courses for user {user_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to list courses: {str(e)}",
                service="CourseService",
                operation="list_user_courses",
                details={"user_id": user_id}
            )

    async def update_course(
        self,
        course_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a course's properties
        
        Validates ownership and updates the course.
        Currently supports updating:
        - color: Course color for UI display
        
        Args:
            course_id: Course ID to update
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update
        
        Returns:
            Updated course dictionary or None if not found
            
        Raises:
            ServiceError: If operation fails
            ValueError: If course not found or user not authorized
        """
        try:
            # Check if course exists and belongs to user
            existing_course = await self.repo.get_by_id_and_user(course_id, user_id)
            
            if not existing_course:
                raise ValueError(f"Course {course_id} not found or not authorized")
            
            # Update the course
            updated_course = await self.repo.update_by_id_and_user(
                course_id,
                user_id,
                updates
            )
            
            if not updated_course:
                raise ValueError(f"Failed to update course {course_id}")
            
            logger.info(f"Updated course {course_id} for user {user_id}")
            return updated_course
        
        except ValueError:
            # Re-raise ValueError as-is (these are expected validation errors)
            raise
        except Exception as e:
            logger.error(f"Failed to update course {course_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to update course: {str(e)}",
                service="CourseService",
                operation="update_course",
                details={"course_id": course_id, "user_id": user_id, "updates": updates}
            )

    async def get_course(
        self,
        course_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single course by ID
        
        Validates ownership before returning.
        
        Args:
            course_id: Course ID
            user_id: User ID for ownership verification
        
        Returns:
            Course dictionary or None if not found/unauthorized
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            course = await self.repo.get_by_id_and_user(course_id, user_id)
            return course
        
        except Exception as e:
            logger.error(f"Failed to get course {course_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get course: {str(e)}",
                service="CourseService",
                operation="get_course",
                details={"course_id": course_id, "user_id": user_id}
            )

    async def find_course_by_name(
        self,
        course_name: str,
        user_id: str
    ) -> Optional[str]:
        """
        Find course ID by name (case-insensitive partial match)
        
        Tries exact match first, then partial match.
        
        Args:
            course_name: Course name to search for
            user_id: User ID for ownership verification
        
        Returns:
            Course ID if found, None otherwise
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            # Try to find by name
            course = await self.repo.find_by_name(course_name, user_id)
            
            if course:
                logger.info(f"Found course '{course_name}' for user {user_id}")
                return course.get("id")
            
            logger.debug(f"No course found with name '{course_name}' for user {user_id}")
            return None
        
        except Exception as e:
            logger.warning(f"Failed to find course by name '{course_name}': {e}")
            # Don't raise ServiceError for "not found" cases - just return None
            return None


def get_course_service() -> CourseService:
    """
    Dependency injection function for CourseService
    
    Returns:
        CourseService instance with default dependencies
    """
    return CourseService(repo=get_course_repository())

