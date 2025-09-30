"""
User Preferences API Endpoints
Handles user settings for contact management, notifications, etc.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user, CurrentUser
from app.services.infrastructure.user_preferences import get_user_preferences_service
from app.models.user.user_preferences import (
    UserPreferences, UserPreferencesUpdate, UserPreferencesResponse,
    EmailPreferences, NotificationPreferences, BriefingPreferences, ContactManagementMode
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ContactManagementSettingsUpdate(BaseModel):
    """Specific update for contact management settings"""
    contact_management_mode: ContactManagementMode
    auto_add_domains: list[str] = []
    sync_contacts_on_compose: bool = True
    only_email_contacts: bool = False


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current user's preferences"""
    try:
        preferences_service = get_user_preferences_service()
        preferences = await preferences_service.get_user_preferences(current_user.user_id)
        
        return UserPreferencesResponse(
            user_id=preferences.user_id,
            email=preferences.email,
            notifications=preferences.notifications,
            briefings=preferences.briefings,
            updated_at=preferences.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user preferences: {str(e)}"
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    updates: UserPreferencesUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        preferences_service = get_user_preferences_service()
        updated_preferences = await preferences_service.update_user_preferences(
            current_user.user_id, updates
        )
        
        return UserPreferencesResponse(
            user_id=updated_preferences.user_id,
            email=updated_preferences.email,
            notifications=updated_preferences.notifications,
            briefings=updated_preferences.briefings,
            updated_at=updated_preferences.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )


@router.put("/preferences/contact-management")
async def update_contact_management_settings(
    settings: ContactManagementSettingsUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update contact management settings specifically"""
    try:
        preferences_service = get_user_preferences_service()
        
        # Create email preferences update
        email_update = EmailPreferences(
            contact_management_mode=settings.contact_management_mode,
            auto_add_domains=settings.auto_add_domains,
            sync_contacts_on_compose=settings.sync_contacts_on_compose,
            only_email_contacts=settings.only_email_contacts
        )
        
        updates = UserPreferencesUpdate(email=email_update)
        updated_preferences = await preferences_service.update_user_preferences(
            current_user.user_id, updates
        )
        
        return {
            "success": True,
            "message": "Contact management settings updated successfully",
            "settings": updated_preferences.email.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating contact management settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact management settings: {str(e)}"
        )


@router.get("/preferences/contact-management")
async def get_contact_management_settings(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current contact management settings"""
    try:
        preferences_service = get_user_preferences_service()
        preferences = await preferences_service.get_user_preferences(current_user.user_id)
        
        return {
            "contact_management_mode": preferences.email.contact_management_mode,
            "auto_add_domains": preferences.email.auto_add_domains,
            "sync_contacts_on_compose": preferences.email.sync_contacts_on_compose,
            "only_email_contacts": preferences.email.only_email_contacts,
            "suggest_frequent_recipients": preferences.email.suggest_frequent_recipients
        }
        
    except Exception as e:
        logger.error(f"Error getting contact management settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contact management settings: {str(e)}"
        )


@router.post("/preferences/reset")
async def reset_user_preferences(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Reset user preferences to defaults"""
    try:
        preferences_service = get_user_preferences_service()
        
        # Create default preferences
        default_preferences = UserPreferences(user_id=current_user.user_id)
        await preferences_service.save_user_preferences(default_preferences)
        
        return {
            "success": True,
            "message": "Preferences reset to defaults",
            "preferences": {
                "email": default_preferences.email.dict(),
                "notifications": default_preferences.notifications.dict(),
                "briefings": default_preferences.briefings.dict()
            }
        }
        
    except Exception as e:
        logger.error(f"Error resetting user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset user preferences: {str(e)}"
        )


@router.get("/preferences/briefings")
async def get_briefing_preferences(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current briefing preferences"""
    try:
        preferences_service = get_user_preferences_service()
        preferences = await preferences_service.get_user_preferences(current_user.user_id)
        
        return preferences.briefings.dict()
        
    except Exception as e:
        logger.error(f"Error getting briefing preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get briefing preferences: {str(e)}"
        )


@router.put("/preferences/briefings")
async def update_briefing_preferences(
    briefing_settings: BriefingPreferences,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update briefing preferences specifically"""
    try:
        preferences_service = get_user_preferences_service()
        
        updates = UserPreferencesUpdate(briefings=briefing_settings)
        updated_preferences = await preferences_service.update_user_preferences(
            current_user.user_id, updates
        )
        
        return {
            "success": True,
            "message": "Briefing preferences updated successfully",
            "briefings": updated_preferences.briefings.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating briefing preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update briefing preferences: {str(e)}"
        )


@router.post("/preferences/briefings/test")
async def test_briefing_delivery(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Send a test briefing to verify settings"""
    try:
        from app.agents.orchestrator import get_agent_orchestrator
        from app.workers.communication.email_service import get_email_service
        
        # Get user preferences
        preferences_service = get_user_preferences_service()
        preferences = await preferences_service.get_user_preferences(current_user.user_id)
        
        if not preferences.briefings.daily_briefing_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily briefings are not enabled"
            )
        
        # Generate test briefing
        orchestrator = await get_agent_orchestrator()
        briefing_result = await orchestrator.generate_daily_briefing(
            user_id=current_user.user_id,
            briefing_date=None,  # Use current date
            delivery_method="test",
            user_context={
                "user_id": current_user.user_id,
                "email": current_user.email,
                "name": current_user.email.split("@")[0] if current_user.email else "User",
                "permissions": {"can_execute_workflows": True}
            },
            connected_accounts={
                "gmail": {"expires_at": "2024-12-31T23:59:59Z"},
                "google": {"expires_at": "2024-12-31T23:59:59Z"}
            }
        )
        
        response = {"success": True, "message": "Test briefing generated"}
        
        # Send email if enabled
        if preferences.briefings.daily_briefing_email_enabled and briefing_result.get("success"):
            email_service = get_email_service()
            email_result = await email_service.send_daily_briefing(
                to=current_user.email,
                user_name=current_user.email.split("@")[0] if current_user.email else "User",
                briefing_data=briefing_result.get("data", {})
            )
            
            if email_result.get("success"):
                response["email_sent"] = True
                response["message"] += " and sent via email"
            else:
                response["email_error"] = email_result.get("error")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending test briefing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test briefing: {str(e)}"
        )