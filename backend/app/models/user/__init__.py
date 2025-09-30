"""
User preferences and configuration models.

This module contains all user-related models including:
- Email preferences and notification settings
- Contact management modes and configurations
- Briefing preferences and scheduling
- User-specific feature toggles and behaviors
"""

from .user_preferences import (
    ContactManagementMode,
    EmailPreferences,
    NotificationPreferences,
    BriefingPreferences,
    UserPreferences,
    UserPreferencesUpdate,
    UserPreferencesResponse
)

__all__ = [
    "ContactManagementMode",
    "EmailPreferences",
    "NotificationPreferences",
    "BriefingPreferences", 
    "UserPreferences",
    "UserPreferencesUpdate",
    "UserPreferencesResponse",
]
