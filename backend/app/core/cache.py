"""
Redis cache client for supervision context storage
"""
from typing import Optional
import redis.asyncio as redis
import logging
import os

logger = logging.getLogger(__name__)


class MockRedisClient:
    """Mock Redis client for development/testing when Redis is not available"""
    
    def __init__(self):
        self.data = {}
    
    async def get(self, key: str) -> Optional[str]:
        return self.data.get(key)
    
    async def setex(self, key: str, seconds: int, value: str) -> None:
        self.data[key] = value
        # In a real implementation, we'd need to handle TTL
    
    async def delete(self, *keys: str) -> None:
        for key in keys:
            self.data.pop(key, None)
    
    async def keys(self, pattern: str) -> list:
        # Simple pattern matching for mock
        import fnmatch
        return [key for key in self.data.keys() if fnmatch.fnmatch(key, pattern)]


# Global Redis client
_redis_client: Optional[redis.Redis] = None
_mock_redis_client: Optional[MockRedisClient] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    global _redis_client, _mock_redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    # Try to connect to Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url)
        
        # Test connection
        await _redis_client.ping()
        logger.info("Connected to Redis")
        return _redis_client
        
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Using mock client.")
        
        # Fallback to mock client
        if _mock_redis_client is None:
            _mock_redis_client = MockRedisClient()
        
        return _mock_redis_client