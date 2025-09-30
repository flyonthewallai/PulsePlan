"""
Redis Configuration Module
Exports the Redis client for use throughout the application
"""
from .redis_client import RedisClient, get_redis_client, close_redis_client, get_redis

# Create a global redis client instance
redis_client = RedisClient()

# Export the main functions and client
__all__ = [
    'redis_client',
    'get_redis_client', 
    'close_redis_client',
    'get_redis',
    'RedisClient'
]
