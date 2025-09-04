"""
User API endpoints
Basic user profile and management
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import logging

from app.core.auth import get_current_user, CurrentUser
from app.config.supabase import get_supabase

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
    supabase = Depends(get_supabase)
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
    
    try:
        # Get user profile from Supabase auth.users
        auth_response = supabase.auth.admin.get_user_by_id(user_id)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = auth_response.user
        
        # Try to get additional profile data from profiles table
        profile_data = {}
        try:
            profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
            if profile_response.data:
                profile_data = profile_response.data[0]
        except Exception as profile_error:
            logger.warning(f"Could not fetch profile data for user {user_id}: {profile_error}")
            # Continue without profile data
        
        logger.info(f"Retrieved profile for user {user_id}")
        
        return UserProfile(
            user_id=user_id,
            email=user_data.email,
            name=profile_data.get("full_name") or user_data.user_metadata.get("full_name"),
            city=profile_data.get("city"),
            timezone=profile_data.get("timezone"),
            preferences=profile_data.get("preferences", {
                "theme": "light",
                "notifications": True,
                "language": "en"
            })
        )
        
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        # Fallback to basic user data from JWT
        return UserProfile(
            user_id=user_id,
            email=current_user.email,
            name="User",
            preferences={"theme": "light", "notifications": True, "language": "en"}
        )

@router.get("/tasks")
async def get_tasks(
    current_user: CurrentUser = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get user tasks from Supabase
    """
    try:
        # Get tasks from Supabase
        response = supabase.table("tasks").select("*").eq("user_id", current_user.user_id).execute()
        
        tasks = response.data if response.data else []
        logger.info(f"Retrieved {len(tasks)} tasks for user {current_user.user_id}")
        
        return {
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        # Return empty tasks on error
        return {
            "tasks": [],
            "count": 0
        }