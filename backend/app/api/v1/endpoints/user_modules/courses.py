"""
Course management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from app.core.auth import get_current_user, CurrentUser
from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


class CourseUpdateRequest(BaseModel):
    """Request model for updating a course"""
    color: str


@router.get("/", response_model=List[Dict[str, Any]])
async def list_courses(
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all courses for the current user"""
    try:
        supabase = get_supabase()

        result = supabase.table("courses")\
            .select("*")\
            .eq("user_id", current_user.user_id)\
            .order("name")\
            .execute()

        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list courses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list courses: {str(e)}")


@router.patch("/{course_id}", response_model=Dict[str, Any])
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update a course (currently only color)"""
    try:
        supabase = get_supabase()

        # Verify the course belongs to the user
        course_check = supabase.table("courses")\
            .select("id")\
            .eq("id", course_id)\
            .eq("user_id", current_user.user_id)\
            .execute()

        if not course_check.data:
            raise HTTPException(status_code=404, detail="Course not found")

        # Update the course
        result = supabase.table("courses")\
            .update({"color": request.color})\
            .eq("id", course_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update course")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update course: {str(e)}")
