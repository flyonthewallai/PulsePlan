"""
User API endpoints
Basic user profile and management
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.user_service import UserService, get_user_service

logger = logging.getLogger(__name__)
router = APIRouter()

class UserProfile(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

@router.get("/auth/user/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user profile information from Supabase
    """
    # Check if user can access this profile
    if user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get profile using service
    profile_data = await user_service.get_user_profile(
        user_id=user_id,
        fallback_email=current_user.email
    )
    
    logger.info(f"Retrieved profile for user {user_id}")
    
    return UserProfile(**profile_data)

@router.get("/tasks")
async def get_tasks(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user tasks from Supabase
    """
    # Get tasks using service
    return await user_service.get_user_tasks(user_id=current_user.user_id)
