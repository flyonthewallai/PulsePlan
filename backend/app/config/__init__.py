"""
Configuration module - Application configuration organized by domain.

This module provides organized access to all configuration grouped by domain:
- core: Core application settings and environment configuration
- database: Database connection and Supabase configuration
- cache: Redis and caching configuration
"""

# Re-export from modules for backward compatibility
from .core import *
from .database import *
from .cache import *

__all__ = [
    # Core settings
    "Settings",
    "settings",
    "get_settings",
    "Environment",
    
    # Database configuration
    "SupabaseClient",
    "get_supabase",
    "get_supabase_client",
    
    # Cache configuration
    "RedisClient",
    "get_redis_client",
    "close_redis_client",
    "get_redis",
    "redis_client",
    "UpstashRestClient",
]
