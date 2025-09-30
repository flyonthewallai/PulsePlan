"""
Models module - Core data models organized by domain.

This module provides organized access to all application models grouped by functionality:
- auth: Authentication and authorization models (OAuth tokens, providers)
- user: User preferences and configuration models
"""

# Re-export from modules for backward compatibility
from .auth import *
from .user import *

__all__ = [
    # Auth models
    "Provider",
    "OAuthToken",
    "OAuthTokenCreate", 
    "OAuthTokenUpdate",
    "TokenStatus",
    "ProviderStatus",
    
    # User models
    "ContactManagementMode",
    "EmailPreferences",
    "BriefingPreferences", 
    "UserPreferences",
    "UserPreferencesUpdate",
    "UserPreferencesCreate",
    "PreferenceKeys",
]
