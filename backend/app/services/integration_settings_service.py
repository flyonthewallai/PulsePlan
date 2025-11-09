from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
import os

from app.models.integrations import (
    UserIntegrationSettings,
    UserIntegrationSettingsCreate,
    UserIntegrationSettingsUpdate
)
import logging

logger = logging.getLogger(__name__)


class IntegrationSettingsService:
    """Service for managing user integration settings"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
    
    async def get_user_settings(
        self, 
        user_id: UUID, 
        integration_id: Optional[str] = None
    ) -> List[UserIntegrationSettings]:
        """Get all integration settings for a user, optionally filtered by integration_id"""
        try:
            query = self.supabase.table('user_integration_settings').select('*').eq('user_id', str(user_id))
            
            if integration_id:
                query = query.eq('integration_id', integration_id)
            
            result = query.execute()
            
            return [
                UserIntegrationSettings(
                    id=row['id'],
                    user_id=row['user_id'],
                    integration_id=row['integration_id'],
                    account_email=row['account_email'],
                    instructions=row['instructions'],
                    signature=row['signature'],
                    settings=row['settings'] or {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in result.data
            ]
            
        except Exception as e:
            logger.error(
                "Failed to get user integration settings",
                exception=e,
                context={"user_id": str(user_id), "integration_id": integration_id}
            )
            raise
    
    async def get_integration_setting(
        self, 
        user_id: UUID, 
        integration_id: str, 
        account_email: Optional[str] = None
    ) -> Optional[UserIntegrationSettings]:
        """Get specific integration setting for a user"""
        try:
            query = self.supabase.table('user_integration_settings').select('*').eq('user_id', str(user_id)).eq('integration_id', integration_id)
            
            if account_email:
                query = query.eq('account_email', account_email)
            else:
                query = query.is_('account_email', 'null')
            
            result = query.execute()
            
            if not result.data:
                return None
            
            row = result.data[0]
            return UserIntegrationSettings(
                id=row['id'],
                user_id=row['user_id'],
                integration_id=row['integration_id'],
                account_email=row['account_email'],
                instructions=row['instructions'],
                signature=row['signature'],
                settings=row['settings'] or {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
        except Exception as e:
            logger.error(
                "Failed to get integration setting",
                exception=e,
                context={
                    "user_id": str(user_id),
                    "integration_id": integration_id,
                    "account_email": account_email
                }
            )
            raise
    
    async def create_or_update_settings(
        self, 
        user_id: UUID, 
        settings_data: UserIntegrationSettingsCreate
    ) -> UserIntegrationSettings:
        """Create or update integration settings (upsert)"""
        try:
            # Check if settings already exist
            existing = await self.get_integration_setting(
                user_id=user_id,
                integration_id=settings_data.integration_id,
                account_email=settings_data.account_email
            )
            
            if existing:
                # Update existing settings
                update_data = {
                    'instructions': settings_data.instructions,
                    'signature': settings_data.signature,
                    'settings': settings_data.settings
                }
                
                result = self.supabase.table('user_integration_settings').update(update_data).eq('id', str(existing.id)).execute()
                
                if not result.data:
                    raise Exception("Failed to update integration settings")
                
                row = result.data[0]
            else:
                # Create new settings
                insert_data = {
                    'user_id': str(user_id),
                    'integration_id': settings_data.integration_id,
                    'account_email': settings_data.account_email,
                    'instructions': settings_data.instructions,
                    'signature': settings_data.signature,
                    'settings': settings_data.settings
                }
                
                result = self.supabase.table('user_integration_settings').insert(insert_data).execute()
                
                if not result.data:
                    raise Exception("Failed to create integration settings")
                
                row = result.data[0]
            
            return UserIntegrationSettings(
                id=row['id'],
                user_id=row['user_id'],
                integration_id=row['integration_id'],
                account_email=row['account_email'],
                instructions=row['instructions'],
                signature=row['signature'],
                settings=row['settings'] or {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
        except Exception as e:
            logger.error(
                "Failed to create/update integration settings",
                exception=e,
                context={
                    "user_id": str(user_id),
                    "integration_id": settings_data.integration_id
                }
            )
            raise
    
    async def update_settings(
        self, 
        user_id: UUID, 
        integration_id: str, 
        settings_data: UserIntegrationSettingsUpdate,
        account_email: Optional[str] = None
    ) -> Optional[UserIntegrationSettings]:
        """Update specific integration settings"""
        try:
            # Get existing settings
            existing = await self.get_integration_setting(
                user_id=user_id,
                integration_id=integration_id,
                account_email=account_email
            )
            
            if not existing:
                return None
            
            # Prepare update data (only include non-None values)
            update_data = {}
            if settings_data.instructions is not None:
                update_data['instructions'] = settings_data.instructions
            if settings_data.signature is not None:
                update_data['signature'] = settings_data.signature
            if settings_data.settings is not None:
                update_data['settings'] = settings_data.settings
            
            if not update_data:
                return existing
            
            result = self.supabase.table('user_integration_settings').update(update_data).eq('id', str(existing.id)).execute()
            
            if not result.data:
                raise Exception("Failed to update integration settings")
            
            row = result.data[0]
            return UserIntegrationSettings(
                id=row['id'],
                user_id=row['user_id'],
                integration_id=row['integration_id'],
                account_email=row['account_email'],
                instructions=row['instructions'],
                signature=row['signature'],
                settings=row['settings'] or {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
        except Exception as e:
            logger.error(
                "Failed to update integration settings",
                exception=e,
                context={
                    "user_id": str(user_id),
                    "integration_id": integration_id,
                    "account_email": account_email
                }
            )
            raise
    
    async def delete_settings(
        self, 
        user_id: UUID, 
        integration_id: str, 
        account_email: Optional[str] = None
    ) -> bool:
        """Delete integration settings"""
        try:
            query = self.supabase.table('user_integration_settings').delete().eq('user_id', str(user_id)).eq('integration_id', integration_id)
            
            if account_email:
                query = query.eq('account_email', account_email)
            else:
                query = query.is_('account_email', 'null')
            
            result = query.execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(
                "Failed to delete integration settings",
                exception=e,
                context={
                    "user_id": str(user_id),
                    "integration_id": integration_id,
                    "account_email": account_email
                }
            )
            raise
