"""
Hobbies API Endpoints
Handles hobby parsing using LLM and CRUD operations for user hobbies
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user, CurrentUser
from app.models.user.hobby import HobbyParseRequest, HobbyParseResponse, ParsedHobby, SpecificTime
from app.services.user.hobby_parser import get_hobby_parser_service
from app.database.repositories.user_repositories import get_hobbies_repository

logger = logging.getLogger(__name__)
router = APIRouter()


# Response models
class HobbyResponse(BaseModel):
    """Response model for hobby data"""
    id: str
    name: str
    icon: str
    preferred_time: str
    specific_time: dict | None
    days: List[str]
    duration_min: int
    duration_max: int
    flexibility: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


class CreateHobbyRequest(BaseModel):
    """Request to create a new hobby"""
    name: str
    icon: str
    preferred_time: str
    specific_time: SpecificTime | None = None
    days: List[str]
    duration_min: int
    duration_max: int
    flexibility: str
    notes: str = ""


class UpdateHobbyRequest(BaseModel):
    """Request to update an existing hobby"""
    name: str | None = None
    icon: str | None = None
    preferred_time: str | None = None
    specific_time: SpecificTime | None = None
    days: List[str] | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    flexibility: str | None = None
    notes: str | None = None
    is_active: bool | None = None


@router.post("/parse", response_model=HobbyParseResponse)
async def parse_hobby(
    request: HobbyParseRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Parse natural language hobby description into structured data

    This endpoint uses LLM to extract structured information from conversational
    hobby descriptions, making it easy for users to add hobbies naturally.

    Example descriptions:
    - "I like to go to the gym in the morning, Monday-Friday, usually 45-60 minutes"
    - "I play guitar for about an hour in the evening, 3-4 times a week"
    - "I enjoy photography on weekends, usually afternoon for 1-2 hours"
    """
    try:
        hobby_parser = get_hobby_parser_service()
        result = await hobby_parser.parse_hobby_description(request)

        if not result.success:
            logger.warning(
                f"Failed to parse hobby for user {current_user.user_id}: {result.error}"
            )

        return result

    except Exception as e:
        logger.error(f"Error in parse_hobby endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse hobby description: {str(e)}"
        )


@router.get("/", response_model=List[HobbyResponse])
async def get_hobbies(
    include_inactive: bool = False,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all hobbies for the current user"""
    try:
        repo = get_hobbies_repository()
        hobbies = await repo.get_user_hobbies(current_user.user_id, include_inactive)
        return hobbies

    except Exception as e:
        logger.error(f"Error fetching hobbies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch hobbies: {str(e)}"
        )


@router.get("/{hobby_id}", response_model=HobbyResponse)
async def get_hobby(
    hobby_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific hobby by ID"""
    try:
        repo = get_hobbies_repository()
        hobby = await repo.get_hobby_by_id(hobby_id, current_user.user_id)

        if not hobby:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hobby not found"
            )

        return hobby

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching hobby {hobby_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch hobby: {str(e)}"
        )


@router.post("/", response_model=HobbyResponse, status_code=status.HTTP_201_CREATED)
async def create_hobby(
    request: CreateHobbyRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new hobby"""
    try:
        repo = get_hobbies_repository()

        # Convert specific_time to dict if present
        specific_time_dict = None
        if request.specific_time:
            specific_time_dict = {
                "start": request.specific_time.start,
                "end": request.specific_time.end
            }

        hobby = await repo.create_hobby(
            user_id=current_user.user_id,
            name=request.name,
            icon=request.icon,
            preferred_time=request.preferred_time,
            days=request.days,
            duration_min=request.duration_min,
            duration_max=request.duration_max,
            flexibility=request.flexibility,
            specific_time=specific_time_dict,
            notes=request.notes
        )

        return hobby

    except Exception as e:
        logger.error(f"Error creating hobby: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hobby: {str(e)}"
        )


@router.patch("/{hobby_id}", response_model=HobbyResponse)
async def update_hobby(
    hobby_id: str,
    request: UpdateHobbyRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an existing hobby"""
    try:
        repo = get_hobbies_repository()

        # Convert request to dict and filter None values
        updates = request.dict(exclude_unset=True)

        # Convert specific_time to dict if present
        if 'specific_time' in updates and updates['specific_time']:
            updates['specific_time'] = {
                "start": updates['specific_time'].start,
                "end": updates['specific_time'].end
            }

        hobby = await repo.update_hobby(hobby_id, current_user.user_id, updates)
        return hobby

    except Exception as e:
        logger.error(f"Error updating hobby {hobby_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update hobby: {str(e)}"
        )


@router.delete("/{hobby_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hobby(
    hobby_id: str,
    permanent: bool = False,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a hobby (soft delete by default, permanent if specified)"""
    try:
        repo = get_hobbies_repository()
        success = await repo.delete_hobby(hobby_id, current_user.user_id, soft_delete=not permanent)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hobby not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting hobby {hobby_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete hobby: {str(e)}"
        )
