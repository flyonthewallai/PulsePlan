"""
Database utilities for the memory system.
Provides Supabase client and database operations.
"""

import logging
from typing import Optional
from supabase import Client

from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)

class MemoryDatabase:
    """Database client wrapper for memory operations"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.client = supabase_client or get_supabase()
    
    def get_client(self) -> Client:
        """Get the Supabase client"""
        return self.client
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            # Simple query to check connection
            result = self.client.from_("vec_memory").select("count").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def execute_rpc(self, function_name: str, params: dict = None):
        """Execute a stored procedure"""
        try:
            if params:
                result = self.client.rpc(function_name, params).execute()
            else:
                result = self.client.rpc(function_name).execute()
            
            if result.data:
                return result.data
            else:
                logger.warning(f"RPC {function_name} returned no data")
                return []
                
        except Exception as e:
            logger.error(f"Failed to execute RPC {function_name}: {e}")
            raise
    
    async def execute_function(self, sql: str, params: list = None):
        """Execute raw SQL (for advanced queries)"""
        try:
            # Note: This is a simplified approach. In production,
            # you might want to use a more sophisticated SQL execution method
            result = self.client.postgrest.rpc('exec_sql', {
                'sql': sql,
                'params': params or []
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            raise

# Global database instance
memory_db = MemoryDatabase()

def get_memory_database() -> MemoryDatabase:
    """Get the global memory database instance"""
    return memory_db
