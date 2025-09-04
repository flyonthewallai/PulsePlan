from supabase import create_client, Client
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.client: Client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with timeout configurations"""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            logger.warning("Supabase URL or service key not configured. Database features will be disabled.")
            return
        
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def get_client(self) -> Client:
        """Get Supabase client for dependency injection"""
        if not self.client:
            raise RuntimeError("Supabase client not available")
        return self.client
    
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None

# Global Supabase client instance
supabase_client = SupabaseClient()

def get_supabase() -> Client:
    """Dependency function for FastAPI"""
    return supabase_client.get_client()

def get_supabase_client() -> Client:
    """Backward compatibility alias for get_supabase()"""
    return get_supabase()