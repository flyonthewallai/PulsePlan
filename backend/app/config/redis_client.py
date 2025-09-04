"""
Redis Client
Unified Redis client with support for both standard Redis and Upstash
"""
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from typing import Optional, Dict, Any, List, Union
import json
import logging
import asyncio
import time
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Unified Redis client that handles both standard Redis and Upstash connections
    with proper error handling and connection management
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        try:
            # Try to connect using the available configuration
            if self.settings.REDIS_URL:
                await self._init_from_url()
            elif self.settings.UPSTASH_REDIS_REST_URL and self.settings.UPSTASH_REDIS_REST_TOKEN:
                await self._init_from_upstash_url()
            else:
                raise ValueError(
                    "Redis configuration missing! Please set REDIS_URL or both "
                    "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN"
                )
            
            # Test connection
            await self.ping()
            self._initialized = True
            logger.info("✅ Redis client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis client: {e}")
            raise
    
    async def _init_from_url(self):
        """Initialize using REDIS_URL"""
        logger.info(f"Connecting to Redis via URL: {self.settings.REDIS_URL[:20]}...")
        
        pool_kwargs = {
            "max_connections": self.settings.REDIS_MAX_CONNECTIONS,
            "socket_timeout": self.settings.REDIS_TIMEOUT,
            "socket_connect_timeout": self.settings.REDIS_TIMEOUT,
            "retry_on_timeout": self.settings.REDIS_RETRY_ON_TIMEOUT,
            "health_check_interval": self.settings.REDIS_HEALTH_CHECK_INTERVAL,
            "socket_keepalive": self.settings.REDIS_SOCKET_KEEPALIVE,
        }
        
        # Add SSL configuration for secure connections (Upstash typically uses SSL)
        if self.settings.REDIS_URL.startswith("rediss://") or "upstash" in self.settings.REDIS_URL.lower():
            pool_kwargs.update({
                "connection_class": redis.SSLConnection,
                "ssl_cert_reqs": self.settings.REDIS_SSL_CERT_REQS,
                "ssl_check_hostname": self.settings.REDIS_SSL_CHECK_HOSTNAME,
            })
            
            if self.settings.REDIS_SSL_CA_CERTS:
                pool_kwargs["ssl_ca_certs"] = self.settings.REDIS_SSL_CA_CERTS
        
        self._pool = redis.ConnectionPool.from_url(
            self.settings.REDIS_URL,
            **pool_kwargs
        )
        
        self._client = redis.Redis(
            connection_pool=self._pool,
            decode_responses=True,
            socket_timeout=self.settings.REDIS_TIMEOUT
        )
    
    async def _init_from_upstash_url(self):
        """Initialize using Upstash REST URL (converted to Redis URL format)"""
        # Convert REST URL to Redis URL format if needed
        rest_url = self.settings.UPSTASH_REDIS_REST_URL
        token = self.settings.UPSTASH_REDIS_REST_TOKEN
        
        # Extract host and port from REST URL
        if rest_url.startswith("https://"):
            host_part = rest_url.replace("https://", "")
            # Construct Redis URL with authentication
            redis_url = f"rediss://:{token}@{host_part}:6379"
        else:
            raise ValueError("Upstash REST URL must start with https://")
        
        logger.info(f"Converting Upstash REST URL to Redis URL format")
        
        pool_kwargs = {
            "connection_class": redis.SSLConnection,
            "max_connections": self.settings.REDIS_MAX_CONNECTIONS,
            "socket_timeout": self.settings.REDIS_TIMEOUT,
            "socket_connect_timeout": self.settings.REDIS_TIMEOUT,
            "retry_on_timeout": self.settings.REDIS_RETRY_ON_TIMEOUT,
            "health_check_interval": self.settings.REDIS_HEALTH_CHECK_INTERVAL,
            "socket_keepalive": self.settings.REDIS_SOCKET_KEEPALIVE,
            "ssl_cert_reqs": self.settings.REDIS_SSL_CERT_REQS,
            "ssl_check_hostname": self.settings.REDIS_SSL_CHECK_HOSTNAME,
        }
        
        self._pool = redis.ConnectionPool.from_url(redis_url, **pool_kwargs)
        
        self._client = redis.Redis(
            connection_pool=self._pool,
            decode_responses=True,
            socket_timeout=self.settings.REDIS_TIMEOUT
        )
    
    async def close(self):
        """Close Redis connections"""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        if self._pool:
            await self._pool.aclose()
            self._pool = None
        
        self._initialized = False
        logger.info("✅ Redis client closed")
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        if not self._client:
            return False
        
        try:
            result = await self._client.ping()
            return result is True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            if not self._client:
                return {"status": "unhealthy", "error": "Client not initialized"}
            
            # Test ping
            ping_start = time.time()
            ping_result = await self._client.ping()
            ping_duration = (time.time() - ping_start) * 1000
            
            if not ping_result:
                return {
                    "status": "unhealthy", 
                    "error": "Ping failed",
                    "ping_duration_ms": ping_duration
                }
            
            # Test read/write operations
            test_key = f"health_check:{int(time.time())}"
            test_value = "health_check_value"
            
            await self._client.set(test_key, test_value, ex=60)
            retrieved_value = await self._client.get(test_key)
            await self._client.delete(test_key)
            
            read_write_success = retrieved_value == test_value
            
            return {
                "status": "healthy",
                "ping_duration_ms": round(ping_duration, 2),
                "read_write_test": "passed" if read_write_success else "failed",
                "connection_pool_size": self.settings.REDIS_MAX_CONNECTIONS if self._pool else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    # Basic Redis operations
    async def get(self, key: str) -> Optional[str]:
        """Get string value"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        """Set string value with optional expiration"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.set(key, value, ex=ex, nx=nx)
    
    async def delete(self, *keys: str) -> int:
        """Delete keys"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        result = await self._client.exists(key)
        return bool(result)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.incr(key, amount)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.ttl(key)
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.keys(pattern)
    
    def pipeline(self):
        """Get pipeline for batch operations"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return self._client.pipeline()
    
    # JSON operations
    async def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """Set JSON value with optional expiration"""
        try:
            json_str = json.dumps(value, default=str)  # default=str handles datetime objects
            return await self.set(key, json_str, ex=ex)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {e}")
            return None
    
    # List operations
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to left of list"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.lpush(key, *values)
    
    async def rpush(self, key: str, *values: str) -> int:
        """Push values to right of list"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.rpush(key, *values)
    
    async def lpop(self, key: str) -> Optional[str]:
        """Pop value from left of list"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.lpop(key)
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop value from right of list"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.rpop(key)
    
    async def llen(self, key: str) -> int:
        """Get length of list"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.llen(key)
    
    # Set operations
    async def sadd(self, key: str, *values: str) -> int:
        """Add values to set"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.sadd(key, *values)
    
    async def smembers(self, key: str) -> set:
        """Get all members of set"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.smembers(key)
    
    async def sismember(self, key: str, value: str) -> bool:
        """Check if value is member of set"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.sismember(key, value)
    
    # Hash operations
    async def hset(self, key: str, mapping: Dict[str, str]) -> int:
        """Set hash fields"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.hset(key, mapping=mapping)
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.hget(key, field)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields and values"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.hgetall(key)
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.hdel(key, *fields)
    
    # Sorted set operations
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add members to sorted set"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.zadd(key, mapping)
    
    async def zcard(self, key: str) -> int:
        """Get cardinality of sorted set"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.zcard(key)
    
    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove members by score range"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return await self._client.zremrangebyscore(key, min_score, max_score)
    
    # Application-specific cache operations
    async def cache_user_data(self, user_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Cache user data with TTL"""
        cache_key = f"user_data:{user_id}"
        await self.set_json(cache_key, data, ex=ttl)
        logger.debug(f"Cached user data for {user_id} with TTL {ttl}s")
    
    async def get_cached_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user data"""
        cache_key = f"user_data:{user_id}"
        return await self.get_json(cache_key)
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all user-related cache entries"""
        patterns = [
            f"user_data:{user_id}",
            f"user_tokens:{user_id}",
            f"user_profile:{user_id}",
            f"user_connections:{user_id}",
            f"calendar_events:{user_id}:*",
            f"rate_limit:{user_id}*",
            f"workflow_cache:{user_id}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns:
            try:
                if '*' in pattern:
                    # For patterns with wildcards, get keys first then delete
                    keys = await self.keys(pattern)
                    if keys:
                        deleted = await self.delete(*keys)
                        total_deleted += deleted
                else:
                    # Direct delete for specific keys
                    deleted = await self.delete(pattern)
                    total_deleted += deleted
            except Exception as e:
                logger.warning(f"Error deleting cache pattern {pattern}: {e}")
        
        logger.info(f"Cache invalidation for user {user_id}: {total_deleted} keys deleted")
        return total_deleted
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int,
        increment: int = 1
    ) -> Dict[str, Any]:
        """
        Rate limiting using sliding window with sorted sets
        Returns dict with allowed status and current count
        """
        key = f"rate_limit:{identifier}"
        now = time.time()
        
        try:
            pipeline = self.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, now - window_seconds)
            
            # Count current entries
            pipeline.zcard(key)
            
            # Add current request(s)
            for i in range(increment):
                pipeline.zadd(key, {f"{now}:{i}": now})
            
            # Set expiration
            pipeline.expire(key, window_seconds + 1)
            
            results = await pipeline.execute()
            current_count = results[1] + increment  # Count after adding new entries
            
            allowed = current_count <= limit
            
            return {
                "allowed": allowed,
                "current_count": current_count,
                "limit": limit,
                "window_seconds": window_seconds,
                "reset_at": now + window_seconds
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error for {identifier}: {e}")
            # Fail open on Redis errors
            return {
                "allowed": True,
                "current_count": 0,
                "limit": limit,
                "window_seconds": window_seconds,
                "error": str(e)
            }


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get the global Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.initialize()
    
    return _redis_client


async def close_redis_client():
    """Close the global Redis client"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# FastAPI dependency
async def get_redis() -> RedisClient:
    """FastAPI dependency for Redis client"""
    return await get_redis_client()