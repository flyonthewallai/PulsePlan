"""
Database session management
Since we're using Supabase, this is a compatibility layer
"""
from typing import Generator, Optional
import logging

logger = logging.getLogger(__name__)

class MockSession:
    """Mock session for Supabase compatibility"""
    
    def __init__(self):
        self.is_active = True
    
    def close(self):
        self.is_active = False
    
    def commit(self):
        pass
    
    def rollback(self):
        pass

def get_db() -> Generator[MockSession, None, None]:
    """
    Dependency function for database session
    Returns mock session since we're using Supabase
    """
    session = MockSession()
    try:
        yield session
    finally:
        session.close()

def get_supabase_db():
    """
    Get Supabase client for database operations
    """
    from app.config.database.supabase import get_supabase
    return get_supabase()
