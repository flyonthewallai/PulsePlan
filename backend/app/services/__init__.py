"""
Services module - Modular service architecture.

This module provides organized access to all service components grouped by domain:
- auth: Authentication and token management services
- integrations: Third-party integration services (Canvas, Calendar, etc.)
- notifications: Notification and communication services
- infrastructure: Core infrastructure services (cache, rate limiting, etc.)
- workers: Background worker services
"""

# Re-export from modules for backward compatibility
from .auth import *
from .integrations import *
from .notifications import *
from .infrastructure import *
from .workers import *

__all__ = [
    # Auth services
    "GoogleOAuthProvider",
    "MicrosoftOAuthProvider",
    "oauth_service",
    "get_token_service",
    "TokenService",
    "TokenRefreshService",
    
    # Integration services
    "CanvasService",
    "get_canvas_service",
    "CanvasTokenService", 
    "CalendarSyncService",
    "get_calendar_sync_service",
    
    # Notification services
    "IOSNotificationService",
    "get_ios_notification_service",
    
    # Infrastructure services
    "get_cache_service",
    "CacheService",
    "RateLimitService",
    "PreferencesService",
    "UserPreferencesService",
    
    # Worker services
    "CalendarBackgroundWorker",
]


