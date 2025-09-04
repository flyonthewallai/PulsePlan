"""
User preferences service for managing user settings
Handles storage and retrieval of user preferences from Supabase
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.config.supabase import get_supabase
from app.models.user_preferences import (
    UserPreferences, UserPreferencesUpdate, UserPreferencesResponse,
    EmailPreferences, NotificationPreferences, BriefingPreferences, ContactManagementMode
)

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """Service for managing user preferences"""
    
    def __init__(self):
        self.supabase = None
    
    def _get_supabase(self):
        """Get Supabase client"""
        if not self.supabase:
            self.supabase = get_supabase()
        return self.supabase
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences, creating defaults if none exist"""
        try:
            supabase = self._get_supabase()
            result = supabase.table('user_preferences').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                # Parse existing preferences
                data = result.data[0]
                # Parse briefing preferences from database columns
                briefing_data = {
                    'daily_briefing_enabled': data.get('daily_briefing_enabled', True),
                    'daily_briefing_time': data.get('daily_briefing_time', '08:00:00'),
                    'daily_briefing_timezone': data.get('daily_briefing_timezone', 'UTC'),
                    'daily_briefing_email_enabled': data.get('daily_briefing_email_enabled', True),
                    'daily_briefing_notification_enabled': data.get('daily_briefing_notification_enabled', True),
                    'weekly_pulse_enabled': data.get('weekly_pulse_enabled', True),
                    'weekly_pulse_day': data.get('weekly_pulse_day', 0),
                    'weekly_pulse_time': data.get('weekly_pulse_time', '18:00:00'),
                    'weekly_pulse_email_enabled': data.get('weekly_pulse_email_enabled', True),
                    'weekly_pulse_notification_enabled': data.get('weekly_pulse_notification_enabled', True),
                    'briefing_content_preferences': data.get('briefing_content_preferences', {})
                }
                
                return UserPreferences(
                    user_id=data['user_id'],
                    email=EmailPreferences(**data.get('email_preferences', {})),
                    notifications=NotificationPreferences(**data.get('notification_preferences', {})),
                    briefings=BriefingPreferences(**briefing_data),
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at'])
                )
            else:
                # Create default preferences
                defaults = UserPreferences(user_id=user_id)
                await self.save_user_preferences(defaults)
                return defaults
                
        except Exception as e:
            logger.error(f"Error getting user preferences for {user_id}: {str(e)}")
            # Return defaults on error
            return UserPreferences(user_id=user_id)
    
    async def save_user_preferences(self, preferences: UserPreferences) -> bool:
        """Save user preferences to database"""
        try:
            supabase = self._get_supabase()
            preferences.updated_at = datetime.utcnow()
            
            # Convert briefings to individual columns for database storage
            briefings_dict = preferences.briefings.dict()
            
            # Convert time objects to strings for JSON serialization
            daily_time = briefings_dict['daily_briefing_time']
            weekly_time = briefings_dict['weekly_pulse_time']
            
            if hasattr(daily_time, 'strftime'):
                daily_time_str = daily_time.strftime('%H:%M:%S')
            else:
                daily_time_str = str(daily_time)
                
            if hasattr(weekly_time, 'strftime'):
                weekly_time_str = weekly_time.strftime('%H:%M:%S')
            else:
                weekly_time_str = str(weekly_time)
            
            data = {
                'user_id': preferences.user_id,
                'email_preferences': preferences.email.dict(),
                'notification_preferences': preferences.notifications.dict(),
                'daily_briefing_enabled': briefings_dict['daily_briefing_enabled'],
                'daily_briefing_time': daily_time_str,
                'daily_briefing_timezone': briefings_dict['daily_briefing_timezone'],
                'daily_briefing_email_enabled': briefings_dict['daily_briefing_email_enabled'],
                'daily_briefing_notification_enabled': briefings_dict['daily_briefing_notification_enabled'],
                'weekly_pulse_enabled': briefings_dict['weekly_pulse_enabled'],
                'weekly_pulse_day': briefings_dict['weekly_pulse_day'],
                'weekly_pulse_time': weekly_time_str,
                'weekly_pulse_email_enabled': briefings_dict['weekly_pulse_email_enabled'],
                'weekly_pulse_notification_enabled': briefings_dict['weekly_pulse_notification_enabled'],
                'briefing_content_preferences': briefings_dict['briefing_content_preferences'],
                'updated_at': preferences.updated_at.isoformat()
            }
            
            # Check if preferences exist
            existing = supabase.table('user_preferences').select('user_id').eq('user_id', preferences.user_id).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('user_preferences').update(data).eq('user_id', preferences.user_id).execute()
            else:
                # Create new
                data['created_at'] = preferences.created_at.isoformat()
                result = supabase.table('user_preferences').insert(data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving user preferences for {preferences.user_id}: {str(e)}")
            return False
    
    async def update_user_preferences(self, user_id: str, updates: UserPreferencesUpdate) -> UserPreferences:
        """Update specific user preferences"""
        try:
            # Get current preferences
            current = await self.get_user_preferences(user_id)
            
            # Apply updates
            if updates.email:
                current.email = updates.email
            if updates.notifications:
                current.notifications = updates.notifications
            if updates.briefings:
                current.briefings = updates.briefings
            
            # Save updated preferences
            await self.save_user_preferences(current)
            return current
            
        except Exception as e:
            logger.error(f"Error updating user preferences for {user_id}: {str(e)}")
            raise e
    
    async def get_contact_management_mode(self, user_id: str) -> ContactManagementMode:
        """Get user's contact management preference"""
        try:
            preferences = await self.get_user_preferences(user_id)
            return preferences.email.contact_management_mode
        except Exception as e:
            logger.warning(f"Error getting contact management mode for {user_id}: {str(e)}")
            return ContactManagementMode.ASK_TO_ADD  # Safe default
    
    async def should_suggest_contacts(self, user_id: str) -> bool:
        """Check if we should suggest adding contacts for this user"""
        try:
            mode = await self.get_contact_management_mode(user_id)
            return mode in [ContactManagementMode.ASK_TO_ADD, ContactManagementMode.AUTO_ADD_ALL]
        except Exception as e:
            logger.warning(f"Error checking contact suggestions for {user_id}: {str(e)}")
            return True  # Safe default - suggest contacts
    
    async def should_auto_add_contacts(self, user_id: str, email_domain: Optional[str] = None) -> bool:
        """Check if we should automatically add contacts for this user"""
        try:
            preferences = await self.get_user_preferences(user_id)
            mode = preferences.email.contact_management_mode
            
            if mode == ContactManagementMode.AUTO_ADD_ALL:
                return True
            elif mode == ContactManagementMode.AUTO_ADD_DOMAIN and email_domain:
                return email_domain in preferences.email.auto_add_domains
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking auto-add contacts for {user_id}: {str(e)}")
            return False  # Safe default - don't auto-add


# Global service instance
user_preferences_service = UserPreferencesService()

def get_user_preferences_service() -> UserPreferencesService:
    """Get the global user preferences service instance"""
    return user_preferences_service