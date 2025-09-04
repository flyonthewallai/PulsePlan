"""
User preferences models for PulsePlan
Handles user settings for various features including contact management and briefings
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, time
from enum import Enum


class ContactManagementMode(str, Enum):
    """Contact management preferences"""
    NEVER_SUGGEST = "never_suggest"      # Never suggest adding contacts
    ASK_TO_ADD = "ask_to_add"           # Ask user before adding (default)
    AUTO_ADD_ALL = "auto_add_all"       # Automatically add all new recipients
    AUTO_ADD_DOMAIN = "auto_add_domain" # Only auto-add from specific domains


class EmailPreferences(BaseModel):
    """Email-related user preferences"""
    contact_management_mode: ContactManagementMode = ContactManagementMode.ASK_TO_ADD
    auto_add_domains: list[str] = Field(default_factory=list)  # Domains to auto-add contacts from
    sync_contacts_on_compose: bool = True   # Sync contacts when composing emails
    only_email_contacts: bool = False       # Only allow emailing people in contacts
    suggest_frequent_recipients: bool = True # Suggest frequently emailed people
    

class NotificationPreferences(BaseModel):
    """Notification preferences"""
    email_suggestions: bool = True
    contact_suggestions: bool = True
    task_reminders: bool = True
    calendar_reminders: bool = True


class BriefingPreferences(BaseModel):
    """Daily briefing and weekly pulse preferences"""
    daily_briefing_enabled: bool = True
    daily_briefing_time: time = Field(default_factory=lambda: time(8, 0))  # 8:00 AM
    daily_briefing_timezone: str = "UTC"
    daily_briefing_email_enabled: bool = True
    daily_briefing_notification_enabled: bool = True
    
    weekly_pulse_enabled: bool = True
    weekly_pulse_day: int = 0  # 0 = Sunday, 6 = Saturday
    weekly_pulse_time: time = Field(default_factory=lambda: time(18, 0))  # 6:00 PM
    weekly_pulse_email_enabled: bool = True
    weekly_pulse_notification_enabled: bool = True
    
    # Content customization from frontend
    briefing_content_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            time: lambda v: v.strftime("%H:%M:%S")
        }


class UserPreferences(BaseModel):
    """Complete user preferences model"""
    user_id: str
    email: EmailPreferences = Field(default_factory=EmailPreferences)
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    briefings: BriefingPreferences = Field(default_factory=BriefingPreferences)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    email: Optional[EmailPreferences] = None
    notifications: Optional[NotificationPreferences] = None
    briefings: Optional[BriefingPreferences] = None


class UserPreferencesResponse(BaseModel):
    """Response schema for user preferences"""
    user_id: str
    email: EmailPreferences
    notifications: NotificationPreferences
    briefings: BriefingPreferences
    updated_at: datetime