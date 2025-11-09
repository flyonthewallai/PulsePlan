"""
Course management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.course_service import CourseService, get_course_service
from app.core.utils.error_handlers import handle_endpoint_error

logger = logging.getLogger(__name__)

router = APIRouter()


class CourseUpdateRequest(BaseModel):
    """Request model for updating a course"""
    color: str


@router.get("/", response_model=List[Dict[str, Any]])
async def list_courses(
    current_user: CurrentUser = Depends(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    """List all courses for the current user"""
    try:
        courses = await service.list_user_courses(current_user.user_id)
        return courses
    except Exception as e:
        return handle_endpoint_error(e, logger, "list_courses")


@router.patch("/{course_id}", response_model=Dict[str, Any])
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    """Update a course (currently only color)"""
    try:
        updated_course = await service.update_course(
            course_id=course_id,
            user_id=current_user.user_id,
            updates={"color": request.color}
        )
        
        if not updated_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        return updated_course
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        return handle_endpoint_error(e, logger, "update_course")
