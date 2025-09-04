"""
Cache service for Redis operations and data caching
Uses centralized Upstash Redis client
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..config.redis import get_redis_client

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache service using centralized Upstash Redis client"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
    
    async def _get_client(self):
        """Get centralized Redis client (Upstash)"""
        # Ensure Redis is initialized
        if not self.redis_client.client:
            await self.redis_client.initialize()
        return self.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int = 300
    ) -> bool:
        """Set value in cache with TTL"""
        try:
            client = await self._get_client()
            serialized_value = json.dumps(value, default=str)
            await client.set(key, serialized_value, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            client = await self._get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    # User-specific cache methods
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        return await self.get(f"user:profile:{user_id}")
    
    async def set_user_profile(
        self, 
        user_id: str, 
        profile_data: Dict[str, Any], 
        ttl_seconds: int = 300
    ) -> bool:
        """Cache user profile data"""
        return await self.set(f"user:profile:{user_id}", profile_data, ttl_seconds)
    
    async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user subscription data"""
        return await self.get(f"user:subscription:{user_id}")
    
    async def set_user_subscription(
        self, 
        user_id: str, 
        subscription_data: Dict[str, Any], 
        ttl_seconds: int = 600
    ) -> bool:
        """Cache user subscription data"""
        return await self.set(f"user:subscription:{user_id}", subscription_data, ttl_seconds)
    
    async def get_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user OAuth tokens"""
        return await self.get(f"user:tokens:{user_id}")
    
    async def set_user_tokens(
        self, 
        user_id: str, 
        tokens_data: Dict[str, Any], 
        ttl_seconds: int = 1800  # 30 minutes
    ) -> bool:
        """Cache user OAuth tokens"""
        return await self.set(f"user:tokens:{user_id}", tokens_data, ttl_seconds)
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user preferences"""
        return await self.get(f"user:preferences:{user_id}")
    
    async def set_user_preferences(
        self, 
        user_id: str, 
        preferences_data: Dict[str, Any], 
        ttl_seconds: int = 900  # 15 minutes
    ) -> bool:
        """Cache user preferences"""
        return await self.set(f"user:preferences:{user_id}", preferences_data, ttl_seconds)
    
    # Calendar and task cache methods
    
    async def get_user_calendar_events(
        self, 
        user_id: str, 
        date_key: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached calendar events for specific date range"""
        return await self.get(f"user:calendar:{user_id}:{date_key}")
    
    async def set_user_calendar_events(
        self,
        user_id: str,
        date_key: str,
        events_data: List[Dict[str, Any]],
        ttl_seconds: int = 300  # 5 minutes
    ) -> bool:
        """Cache calendar events"""
        return await self.set(f"user:calendar:{user_id}:{date_key}", events_data, ttl_seconds)
    
    async def get_user_tasks(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached user tasks"""
        return await self.get(f"user:tasks:{user_id}")
    
    async def set_user_tasks(
        self,
        user_id: str,
        tasks_data: List[Dict[str, Any]],
        ttl_seconds: int = 180  # 3 minutes
    ) -> bool:
        """Cache user tasks"""
        return await self.set(f"user:tasks:{user_id}", tasks_data, ttl_seconds)
    
    # Agent and briefing cache methods
    
    async def get_daily_briefing(self, user_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get cached daily briefing"""
        return await self.get(f"briefing:daily:{user_id}:{date}")
    
    async def set_daily_briefing(
        self,
        user_id: str,
        date: str,
        briefing_data: Dict[str, Any],
        ttl_seconds: int = 3600  # 1 hour
    ) -> bool:
        """Cache daily briefing"""
        return await self.set(f"briefing:daily:{user_id}:{date}", briefing_data, ttl_seconds)
    
    async def get_weekly_pulse(self, user_id: str, week: str) -> Optional[Dict[str, Any]]:
        """Get cached weekly pulse"""
        return await self.get(f"pulse:weekly:{user_id}:{week}")
    
    async def set_weekly_pulse(
        self,
        user_id: str,
        week: str,
        pulse_data: Dict[str, Any],
        ttl_seconds: int = 7200  # 2 hours
    ) -> bool:
        """Cache weekly pulse"""
        return await self.set(f"pulse:weekly:{user_id}:{week}", pulse_data, ttl_seconds)
    
    # Invalidation methods
    
    async def invalidate_user_data(self, user_id: str) -> int:
        """Invalidate all cached data for a user"""
        patterns = [
            f"user:*:{user_id}",
            f"user:*:{user_id}:*",
            f"briefing:*:{user_id}:*",
            f"pulse:*:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted_count = await self.delete_pattern(pattern)
            total_deleted += deleted_count
        
        if total_deleted > 0:
            logger.info(f"Invalidated {total_deleted} cache keys for user {user_id}")
        
        return total_deleted
    
    async def invalidate_user_profile(self, user_id: str) -> bool:
        """Invalidate user profile cache"""
        return await self.delete(f"user:profile:{user_id}")
    
    async def invalidate_user_subscription(self, user_id: str) -> bool:
        """Invalidate user subscription cache"""
        return await self.delete(f"user:subscription:{user_id}")
    
    async def invalidate_user_tokens(self, user_id: str) -> bool:
        """Invalidate user tokens cache"""
        return await self.delete(f"user:tokens:{user_id}")
    
    async def invalidate_user_calendar(self, user_id: str) -> int:
        """Invalidate user calendar cache"""
        return await self.delete_pattern(f"user:calendar:{user_id}:*")
    
    async def invalidate_user_tasks(self, user_id: str) -> bool:
        """Invalidate user tasks cache"""
        return await self.delete(f"user:tasks:{user_id}")
    
    # Health and statistics
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health info"""
        try:
            client = await self._get_client()
            # Use ping to test connection since Upstash may not support INFO
            await client.ping()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "provider": "Upstash Redis",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "status": "error",
                "redis_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            # Test basic operations
            test_key = f"health:check:{datetime.utcnow().timestamp()}"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            # Set test value
            await self.set(test_key, test_value, 10)
            
            # Get test value
            retrieved_value = await self.get(test_key)
            
            # Clean up
            await self.delete(test_key)
            
            if retrieved_value and retrieved_value.get("test"):
                return {"healthy": True, "provider": "Upstash Redis"}
            else:
                return {"healthy": False, "error": "Test operation failed"}
                
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        # The centralized Redis client handles its own cleanup
        logger.info("Cache service cleanup - using centralized Redis client")


# Global cache service instance
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service