"""
User Context Service
Provides comprehensive user context from users table, preferences, and activity data
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.config.database.supabase import get_supabase
from app.config.cache.redis_client import get_redis_client
from .llm_service import UserContext

logger = logging.getLogger(__name__)


class UserActivity(BaseModel):
    """User activity record"""
    activity_type: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class UserStats(BaseModel):
    """User statistics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    active_conversations: int = 0
    recent_activity_count: int = 0
    avg_response_time: Optional[float] = None
    preferred_interaction_style: str = "balanced"


class EnhancedUserContext(UserContext):
    """Enhanced user context with additional data"""
    stats: UserStats = UserStats()
    recent_tasks: List[Dict[str, Any]] = []
    active_workflows: List[Dict[str, Any]] = []
    notification_preferences: Dict[str, Any] = {}
    integration_status: Dict[str, Any] = {}


class UserContextService:
    """
    Service for retrieving and caching comprehensive user context
    """

    def __init__(self, cache_ttl: int = 1800):  # 30 minutes default cache
        self.cache_ttl = cache_ttl
        self.redis_client = None

    async def get_user_context(
        self,
        user_id: str,
        include_activity: bool = True,
        include_stats: bool = True,
        force_refresh: bool = False
    ) -> EnhancedUserContext:
        """
        Get comprehensive user context with caching
        """
        try:
            # Check cache first unless force refresh
            if not force_refresh:
                cached_context = await self._get_cached_context(user_id)
                if cached_context:
                    logger.debug(f"Using cached context for user {user_id}")
                    return cached_context

            logger.info(f"Building fresh context for user {user_id}")

            # Get base user data
            base_context = await self._build_base_context(user_id)

            # Get additional data in parallel
            tasks = []
            if include_activity:
                tasks.append(self._get_recent_activity(user_id))
            if include_stats:
                tasks.append(self._get_user_stats(user_id))

            # Execute additional queries
            additional_data = {}
            if tasks:
                import asyncio
                results = await asyncio.gather(*tasks, return_exceptions=True)

                if include_activity and len(results) > 0 and not isinstance(results[0], Exception):
                    additional_data['recent_activity'] = results[0]
                if include_stats and len(results) > (1 if include_activity else 0) and not isinstance(results[-1], Exception):
                    additional_data['stats'] = results[-1]

            # Build enhanced context
            enhanced_context = self._build_enhanced_context(base_context, additional_data)

            # Cache the result
            await self._cache_context(user_id, enhanced_context)

            return enhanced_context

        except Exception as e:
            logger.error(f"Failed to get user context for {user_id}: {e}")
            return self._create_fallback_context(user_id)

    async def _build_base_context(self, user_id: str) -> UserContext:
        """Build base user context from users table only"""
        try:
            supabase = get_supabase()

            # Get user data from users table
            user_response = supabase.table("users").select("*").eq("id", user_id).execute()
            if not user_response.data or len(user_response.data) == 0:
                logger.warning(f"No user found in users table for {user_id}")
                raise ValueError(f"User {user_id} not found")

            user_data = user_response.data[0]
            logger.info(f"Got user data for {user_id}")

            # Extract user name with proper fallback chain
            user_name = "User"  # Default fallback
            if user_data.get("full_name"):
                user_name = user_data.get("full_name")
            elif user_data.get("name"):
                user_name = user_data.get("name")
            elif user_data.get("email"):
                user_name = user_data.get("email").split("@")[0]

            # Get timezone with fallback to UTC
            timezone = user_data.get("timezone", "UTC")

            return UserContext(
                user_id=user_id,
                name=user_name,
                email=user_data.get("email"),
                timezone=timezone,
                preferences=user_data.get("preferences", {}),
                working_hours=user_data.get("working_hours", {"startHour": 9, "endHour": 17}),
                user_type=user_data.get("user_type"),
                recent_activity=[]
            )

        except Exception as e:
            logger.error(f"Failed to build base context for {user_id}: {e}")
            raise

    async def _get_recent_activity(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent user activity"""
        try:
            supabase = get_supabase()

            activities = []

            # Get recent tasks
            tasks_response = supabase.table("tasks").select("id, title, status, created_at, updated_at").eq("user_id", user_id).order("updated_at", desc=True).limit(5).execute()

            for task in tasks_response.data or []:
                activities.append({
                    "type": "task",
                    "action": "updated" if task["updated_at"] != task["created_at"] else "created",
                    "title": task["title"],
                    "timestamp": task["updated_at"],
                    "metadata": {"task_id": task["id"], "status": task["status"]}
                })

            # Get recent conversations
            conversations_response = supabase.table("conversations").select("id, title, last_message_at").eq("user_id", user_id).order("last_message_at", desc=True).limit(3).execute()

            for conv in conversations_response.data or []:
                activities.append({
                    "type": "conversation",
                    "action": "message",
                    "title": conv.get("title", "Chat"),
                    "timestamp": conv["last_message_at"],
                    "metadata": {"conversation_id": conv["id"]}
                })

            # Sort by timestamp and return most recent
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:limit]

        except Exception as e:
            logger.warning(f"Failed to get recent activity for {user_id}: {e}")
            return []

    async def _get_user_stats(self, user_id: str) -> UserStats:
        """Get user statistics"""
        try:
            supabase = get_supabase()

            stats = UserStats()

            # Get task stats
            tasks_response = supabase.table("tasks").select("status").eq("user_id", user_id).execute()
            tasks = tasks_response.data or []

            stats.total_tasks = len(tasks)
            stats.completed_tasks = len([t for t in tasks if t.get("status") == "completed"])

            # Get conversation stats
            conversations_response = supabase.table("conversations").select("id").eq("user_id", user_id).eq("is_active", True).execute()
            stats.active_conversations = len(conversations_response.data or [])

            # Get recent activity count (last 7 days)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            recent_tasks = supabase.table("tasks").select("id").eq("user_id", user_id).gte("created_at", week_ago).execute()
            stats.recent_activity_count = len(recent_tasks.data or [])

            # Determine interaction style based on activity
            if stats.recent_activity_count > 20:
                stats.preferred_interaction_style = "power_user"
            elif stats.recent_activity_count > 5:
                stats.preferred_interaction_style = "active"
            else:
                stats.preferred_interaction_style = "casual"

            return stats

        except Exception as e:
            logger.warning(f"Failed to get user stats for {user_id}: {e}")
            return UserStats()

    def _build_enhanced_context(
        self,
        base_context: UserContext,
        additional_data: Dict[str, Any]
    ) -> EnhancedUserContext:
        """Build enhanced context from base context and additional data"""

        enhanced_data = base_context.dict()
        enhanced_data.update({
            'stats': additional_data.get('stats', UserStats()),
            'recent_tasks': self._extract_recent_tasks(additional_data.get('recent_activity', [])),
            'active_workflows': [],  # Will be populated by workflow service
            'notification_preferences': base_context.preferences.get('notifications', {}),
            'integration_status': self._get_integration_status(base_context)
        })

        return EnhancedUserContext(**enhanced_data)

    def _extract_recent_tasks(self, recent_activity: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract task-related activities"""
        return [
            activity for activity in recent_activity
            if activity.get("type") == "task"
        ][:5]  # Last 5 task activities

    def _get_integration_status(self, context: UserContext) -> Dict[str, Any]:
        """Get integration status from user preferences"""
        preferences = context.preferences
        return {
            "calendar_connected": bool(preferences.get("calendar_provider")),
            "email_connected": bool(preferences.get("email_provider")),
            "canvas_connected": bool(preferences.get("canvas_connected")),
            "notifications_enabled": preferences.get("notifications", {}).get("enabled", True)
        }

    async def _get_cached_context(self, user_id: str) -> Optional[EnhancedUserContext]:
        """Get cached user context"""
        try:
            # Check database cache first (more persistent)
            supabase = get_supabase()
            result = supabase.table("user_context_cache").select("context_data").eq("user_id", user_id).gte("expires_at", datetime.utcnow().isoformat()).single().execute()

            if result.data and isinstance(result.data, dict):
                return EnhancedUserContext(**result.data["context_data"])

            # Check Redis cache
            if self.redis_client is None:
                self.redis_client = await get_redis_client()
            cache_key = f"user_context:{user_id}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data and isinstance(cached_data, str):
                context_data = json.loads(cached_data)
                return EnhancedUserContext(**context_data)

        except Exception as e:
            logger.debug(f"Failed to get cached context for {user_id}: {e}")

        return None

    async def _cache_context(self, user_id: str, context: EnhancedUserContext) -> None:
        """Cache user context in Redis and database"""
        try:
            context_data = context.dict()

            # Cache in Redis
            if self.redis_client is None:
                self.redis_client = await get_redis_client()
            cache_key = f"user_context:{user_id}"
            await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(context_data, default=str))

            # Cache in database
            supabase = get_supabase()
            cache_record = {
                "user_id": user_id,
                "context_data": context_data,
                "preferences_hash": self._hash_preferences(context.preferences),
                "expires_at": (datetime.utcnow() + timedelta(seconds=self.cache_ttl)).isoformat()
            }
            supabase.table("user_context_cache").upsert(cache_record).execute()

            logger.debug(f"Cached context for user {user_id}")

        except Exception as e:
            logger.warning(f"Failed to cache context for {user_id}: {e}")

    def _hash_preferences(self, preferences: Dict[str, Any]) -> str:
        """Generate hash of preferences for cache invalidation"""
        import hashlib
        pref_str = json.dumps(preferences, sort_keys=True)
        return hashlib.md5(pref_str.encode()).hexdigest()

    def _create_fallback_context(self, user_id: str) -> EnhancedUserContext:
        """Create fallback context when retrieval fails"""
        return EnhancedUserContext(
            user_id=user_id,
            name="User",
            timezone="UTC",
            preferences={},
            working_hours={"startHour": 9, "endHour": 17},
            recent_activity=[],
            stats=UserStats(),
            recent_tasks=[],
            active_workflows=[],
            notification_preferences={},
            integration_status={}
        )

    async def invalidate_cache(self, user_id: str) -> None:
        """Invalidate cached user context"""
        try:
            # Remove from Redis
            redis_client = await get_redis_client()
            cache_key = f"user_context:{user_id}"
            await redis_client.delete(cache_key)

            # Remove from database
            supabase = get_supabase()
            supabase.table("user_context_cache").delete().eq("user_id", user_id).execute()

            logger.info(f"Invalidated cache for user {user_id}")

        except Exception as e:
            logger.warning(f"Failed to invalidate cache for {user_id}: {e}")

    async def update_user_activity(
        self,
        user_id: str,
        activity_type: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Update user activity and potentially invalidate cache"""
        try:
            # For now, just invalidate cache when significant activity occurs
            significant_activities = ["task_created", "task_completed", "conversation_started"]
            if activity_type in significant_activities:
                await self.invalidate_cache(user_id)

        except Exception as e:
            logger.warning(f"Failed to update activity for {user_id}: {e}")


# Global service instance
_user_context_service = None

def get_user_context_service() -> UserContextService:
    """Get global UserContextService instance"""
    global _user_context_service
    if _user_context_service is None:
        _user_context_service = UserContextService()
    return _user_context_service

