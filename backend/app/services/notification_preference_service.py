"""
Notification Preference Service
Business logic for user notification preferences and logging
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.repositories.user_repositories import (
    UserPreferenceRepository,
    get_user_preference_repository
)
from app.database.repositories.integration_repositories import (
    NotificationLogRepository,
    get_notification_log_repository
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class NotificationPreferenceService:
    """
    Service layer for notification preference management
    
    Handles business logic for:
    - Checking user notification preferences
    - Rate limiting notifications
    - Logging notification sends
    """

    def __init__(
        self,
        user_preference_repository: Optional[UserPreferenceRepository] = None,
        notification_log_repository: Optional[NotificationLogRepository] = None
    ):
        """Initialize NotificationPreferenceService"""
        self._user_preference_repository = user_preference_repository
        self._notification_log_repository = notification_log_repository
    
    @property
    def user_preference_repository(self) -> UserPreferenceRepository:
        """Lazy-load user preference repository"""
        if self._user_preference_repository is None:
            self._user_preference_repository = get_user_preference_repository()
        return self._user_preference_repository
    
    @property
    def notification_log_repository(self) -> NotificationLogRepository:
        """Lazy-load notification log repository"""
        if self._notification_log_repository is None:
            self._notification_log_repository = get_notification_log_repository()
        return self._notification_log_repository

    async def should_send_notification(
        self,
        user_id: str,
        notification_type: str
    ) -> bool:
        """
        Check if user has notifications enabled for this type and respects rate limits
        
        Args:
            user_id: User ID
            notification_type: Type of notification
        
        Returns:
            True if notification should be sent, False otherwise
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            # Get user notification preferences using repository
            try:
                # Get notification-related preferences
                user_prefs = await self.user_preference_repository.get_all_by_user(user_id)
                
                # Extract notification preferences
                preferences = {}
                for pref in user_prefs:
                    if pref.get("preference_key") == "contextual_notifications_enabled":
                        preferences["contextual_notifications_enabled"] = pref.get("value", True)
                    elif pref.get("preference_key") == "notification_types_enabled":
                        preferences["notification_types_enabled"] = pref.get("value", [])
                
                # Set defaults if not found
                if "contextual_notifications_enabled" not in preferences:
                    preferences["contextual_notifications_enabled"] = True
                if "notification_types_enabled" not in preferences:
                    preferences["notification_types_enabled"] = []
                    
            except Exception as e:
                logger.warning(f"No preferences found for user {user_id}, defaulting to enabled: {e}")
                preferences = {
                    "contextual_notifications_enabled": True,
                    "notification_types_enabled": []
                }
            
            # Check if contextual notifications are enabled
            if not preferences.get("contextual_notifications_enabled", True):
                return False
            
            # Check if this specific notification type is enabled
            enabled_types = preferences.get("notification_types_enabled", [])
            if enabled_types and notification_type not in enabled_types:
                return False
            
            # Check rate limiting - don't spam users
            try:
                from app.services.infrastructure.cache_service import get_cache_service
                
                cache_service = get_cache_service()
                cache_key = f"notification_rate_limit:{user_id}:{notification_type}"
                recent_count = await cache_service.get(cache_key) or 0
                
                # Limit to 3 notifications of the same type per hour
                if recent_count >= 3:
                    logger.info(f"Rate limit exceeded for user {user_id}, notification type {notification_type}")
                    return False
                
                # Increment rate limit counter
                await cache_service.set(cache_key, recent_count + 1, 3600)  # 1 hour TTL
            except Exception as e:
                logger.warning(f"Rate limiting check failed, allowing notification: {e}")
            
            return True
        
        except Exception as e:
            logger.warning(f"Error checking notification preferences for user {user_id}: {e}")
            return True  # Default to enabled on error

    async def log_notification(
        self,
        user_id: str,
        notification_type: str,
        notification: Dict[str, Any],
        success: bool
    ) -> None:
        """
        Log notification sending for analytics and debugging
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            notification: Notification data
            success: Whether send was successful
            
        Raises:
            ServiceError: If operation fails (non-fatal)
        """
        try:
            log_entry = {
                "user_id": user_id,
                "notification_type": notification_type,
                "title": notification.get("title", ""),
                "success": success,
                "sent_at": datetime.utcnow().isoformat(),
                "priority": notification.get("priority", "normal"),
                "category": notification.get("category", "general")
            }
            
            await self.notification_log_repository.create_log(log_entry)
        
        except Exception as e:
            # Log but don't raise - logging failures shouldn't block notifications
            logger.warning(f"Failed to log notification for user {user_id}: {e}")


def get_notification_preference_service() -> NotificationPreferenceService:
    """
    Dependency injection function for NotificationPreferenceService
    
    Returns:
        NotificationPreferenceService instance
    """
    return NotificationPreferenceService()

