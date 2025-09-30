"""
Caching configuration and Redis client management.

This module contains cache-related configuration including:
- Redis client initialization and connection management
- Upstash REST API client for cloud Redis
- Cache utilities and connection pooling
"""

from .redis_client import (
    RedisClient,
    get_redis_client,
    close_redis_client,
    get_redis
)

from .redis import (
    redis_client
)

from .upstash_rest import (
    UpstashRestClient
)

__all__ = [
    # Redis client management
    "RedisClient",
    "get_redis_client",
    "close_redis_client",
    "get_redis",
    
    # Redis utilities
    "redis_client",
    
    # Upstash REST client
    "UpstashRestClient",
]
