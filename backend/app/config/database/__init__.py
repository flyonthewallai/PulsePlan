"""
Database configuration and connection management.

This module contains database-related configuration including:
- Supabase database client initialization
- Database connection management and health checks
- Database-specific settings and configurations
"""

from .supabase import (
    SupabaseClient,
    get_supabase,
    get_supabase_client
)

__all__ = [
    "SupabaseClient",
    "get_supabase",
    "get_supabase_client",
]
