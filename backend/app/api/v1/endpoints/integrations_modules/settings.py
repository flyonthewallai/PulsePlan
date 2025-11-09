from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID

from app.core.auth import get_current_user, CurrentUser
from app.models.integrations import (
    UserIntegrationSettings,
    UserIntegrationSettingsCreate,
    UserIntegrationSettingsUpdate,
    UserIntegrationSettingsResponse
)
from app.services.integration_settings_service import IntegrationSettingsService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[UserIntegrationSettingsResponse])
async def get_user_integration_settings(
    integration_id: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user's integration settings, optionally filtered by integration_id"""
    try:
        service = IntegrationSettingsService()
        settings = await service.get_user_settings(
            user_id=current_user.user_id,
            integration_id=integration_id
        )
        
        return [
            UserIntegrationSettingsResponse(
                id=setting.id,
                integration_id=setting.integration_id,
                account_email=setting.account_email,
                instructions=setting.instructions,
                signature=setting.signature,
                settings=setting.settings,
                created_at=setting.created_at,
                updated_at=setting.updated_at
            )
            for setting in settings
        ]
        
    except Exception as e:
        logger.error(
            "Failed to get user integration settings",
            exception=e,
            context={"user_id": current_user.user_id, "integration_id": integration_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integration settings"
        )


@router.get("/{integration_id}", response_model=UserIntegrationSettingsResponse)
async def get_integration_settings(
    integration_id: str,
    account_email: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get specific integration settings for a user, auto-creating if not exists"""
    try:
        service = IntegrationSettingsService()
        setting = await service.get_integration_setting(
            user_id=current_user.user_id,
            integration_id=integration_id,
            account_email=account_email
        )

        # Auto-create empty settings if they don't exist
        if not setting:
            create_data = UserIntegrationSettingsCreate(
                integration_id=integration_id,
                account_email=account_email,
                instructions=None,
                signature=None,
                settings={}
            )
            setting = await service.create_or_update_settings(
                user_id=current_user.user_id,
                settings_data=create_data
            )

        return UserIntegrationSettingsResponse(
            id=setting.id,
            integration_id=setting.integration_id,
            account_email=setting.account_email,
            instructions=setting.instructions,
            signature=setting.signature,
            settings=setting.settings,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get integration settings",
            exception=e,
            context={
                "user_id": current_user.user_id,
                "integration_id": integration_id,
                "account_email": account_email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integration settings"
        )


@router.post("/", response_model=UserIntegrationSettingsResponse)
async def create_integration_settings(
    settings_data: UserIntegrationSettingsCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create or update integration settings for a user"""
    try:
        service = IntegrationSettingsService()
        setting = await service.create_or_update_settings(
            user_id=current_user.user_id,
            settings_data=settings_data
        )
        
        return UserIntegrationSettingsResponse(
            id=setting.id,
            integration_id=setting.integration_id,
            account_email=setting.account_email,
            instructions=setting.instructions,
            signature=setting.signature,
            settings=setting.settings,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )
        
    except Exception as e:
        logger.error(
            "Failed to create/update integration settings",
            exception=e,
            context={
                "user_id": current_user.user_id,
                "integration_id": settings_data.integration_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save integration settings"
        )


@router.put("/{integration_id}", response_model=UserIntegrationSettingsResponse)
async def update_integration_settings(
    integration_id: str,
    settings_data: UserIntegrationSettingsUpdate,
    account_email: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update specific integration settings"""
    try:
        service = IntegrationSettingsService()
        setting = await service.update_settings(
            user_id=current_user.user_id,
            integration_id=integration_id,
            account_email=account_email,
            settings_data=settings_data
        )
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration settings not found"
            )
        
        return UserIntegrationSettingsResponse(
            id=setting.id,
            integration_id=setting.integration_id,
            account_email=setting.account_email,
            instructions=setting.instructions,
            signature=setting.signature,
            settings=setting.settings,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update integration settings",
            exception=e,
            context={
                "user_id": current_user.user_id,
                "integration_id": integration_id,
                "account_email": account_email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update integration settings"
        )


@router.delete("/{integration_id}")
async def delete_integration_settings(
    integration_id: str,
    account_email: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete integration settings"""
    try:
        service = IntegrationSettingsService()
        success = await service.delete_settings(
            user_id=current_user.user_id,
            integration_id=integration_id,
            account_email=account_email
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration settings not found"
            )
        
        return {"message": "Integration settings deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete integration settings",
            exception=e,
            context={
                "user_id": current_user.user_id,
                "integration_id": integration_id,
                "account_email": account_email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete integration settings"
        )
