"""
Production Connection Pooling
Optimized database connections with Supabase compatibility and pool tuning
"""
import asyncio
import asyncpg
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """Connection pool statistics"""
    size: int
    used: int
    free: int
    max_size: int
    min_size: int
    created_connections: int
    closed_connections: int
    avg_acquire_time: float
    total_acquired: int
    total_released: int


@dataclass
class ConnectionHealth:
    """Individual connection health status"""
    connection_id: str
    created_at: datetime
    last_used: datetime
    query_count: int
    error_count: int
    is_healthy: bool
    last_error: Optional[str] = None


class SupabaseConnectionPool:
    """Production connection pool optimized for Supabase"""
    
    def __init__(
        self,
        database_url: str = None,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: float = 60.0,
        server_settings: Dict[str, str] = None,
        init_hooks: List[callable] = None
    ):
        self.database_url = database_url or os.getenv("DATABASE_URL") or self._build_supabase_url()
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self.server_settings = server_settings or {}
        self.init_hooks = init_hooks or []
        
        # Pool instance
        self.pool: Optional[asyncpg.Pool] = None
        
        # Statistics tracking
        self.acquire_times: List[float] = []
        self.total_acquired = 0
        self.total_released = 0
        self.created_connections = 0
        self.closed_connections = 0
        
        # Health tracking
        self.connection_health: Dict[str, ConnectionHealth] = {}
        self.last_health_check = None
        
    def _build_supabase_url(self) -> str:
        """Build Supabase connection URL from environment variables"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required for database connection")
        
        # Extract project ref from Supabase URL
        # Format: https://project-ref.supabase.co
        project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
        
        # Build Postgres connection URL
        # Supabase uses port 5432 for direct Postgres connections
        database_url = f"postgresql://postgres:{supabase_service_key}@db.{project_ref}.supabase.co:5432/postgres"
        
        logger.info(f"Built Supabase connection URL for project: {project_ref}")
        return database_url
    
    async def initialize(self) -> asyncpg.Pool:
        """Initialize connection pool with Supabase optimizations"""
        if self.pool:
            return self.pool
        
        try:
            # Supabase-specific server settings
            default_server_settings = {
                "application_name": "pulseplan_backend",
                "jit": "off",  # Disable JIT for better connection reuse
                "shared_preload_libraries": "",  # Don't override Supabase settings
            }
            default_server_settings.update(self.server_settings)
            
            logger.info(f"Creating Supabase connection pool (min:{self.min_size}, max:{self.max_size})")
            
            self.pool = await asyncpg.create_pool(
                dsn=self.database_url,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.command_timeout,
                server_settings=default_server_settings,
                init=self._init_connection,
                setup=self._setup_connection
            )
            
            # Test pool with a simple query
            await self._test_pool_health()
            
            logger.info(f"✅ Supabase connection pool initialized successfully")
            return self.pool
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase connection pool: {e}")
            raise
    
    async def _init_connection(self, connection: asyncpg.Connection):
        """Initialize new connection with custom settings"""
        try:
            # Set connection-level settings for Supabase
            await connection.execute("SET timezone = 'UTC'")
            await connection.execute("SET statement_timeout = '30s'")  # Prevent long-running queries
            await connection.execute("SET lock_timeout = '10s'")      # Prevent lock waits
            
            # Run custom init hooks
            for hook in self.init_hooks:
                await hook(connection)
            
            # Track connection creation
            self.created_connections += 1
            
            # Add to health tracking
            conn_id = str(id(connection))
            self.connection_health[conn_id] = ConnectionHealth(
                connection_id=conn_id,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                query_count=0,
                error_count=0,
                is_healthy=True
            )
            
            logger.debug(f"Initialized new Supabase connection: {conn_id}")
            
        except Exception as e:
            logger.error(f"Connection initialization failed: {e}")
            raise
    
    async def _setup_connection(self, connection: asyncpg.Connection):
        """Setup connection for each acquire (runs every time)"""
        # This runs each time a connection is acquired from the pool
        # Useful for setting session-specific variables
        pass
    
    async def _test_pool_health(self):
        """Test pool health with a simple query"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    raise Exception("Pool health check failed")
            logger.debug("Pool health check passed")
        except Exception as e:
            logger.error(f"Pool health check failed: {e}")
            raise
    
    async def acquire_connection(self) -> asyncpg.Connection:
        """Acquire connection with timing and error tracking"""
        if not self.pool:
            await self.initialize()
        
        start_time = time.time()
        try:
            connection = await self.pool.acquire()
            
            # Track acquire time
            acquire_time = time.time() - start_time
            self.acquire_times.append(acquire_time)
            self.total_acquired += 1
            
            # Limit acquire_times list size
            if len(self.acquire_times) > 1000:
                self.acquire_times = self.acquire_times[-500:]
            
            # Update connection health
            conn_id = str(id(connection))
            if conn_id in self.connection_health:
                self.connection_health[conn_id].last_used = datetime.utcnow()
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to acquire connection: {e}")
            raise
    
    async def release_connection(self, connection: asyncpg.Connection, error: Exception = None):
        """Release connection back to pool"""
        if not self.pool:
            return
        
        try:
            # Update connection health
            conn_id = str(id(connection))
            if conn_id in self.connection_health:
                health = self.connection_health[conn_id]
                health.query_count += 1
                
                if error:
                    health.error_count += 1
                    health.last_error = str(error)
                    health.is_healthy = health.error_count < 5  # Mark unhealthy after 5 errors
            
            await self.pool.release(connection)
            self.total_released += 1
            
        except Exception as e:
            logger.error(f"Failed to release connection: {e}")
    
    async def execute_query(
        self, 
        query: str, 
        *args, 
        timeout: float = None
    ) -> Any:
        """Execute query with connection management and error handling"""
        timeout = timeout or self.command_timeout
        connection = None
        error = None
        
        try:
            connection = await self.acquire_connection()
            
            # Execute query with timeout
            result = await asyncio.wait_for(
                connection.fetch(query, *args),
                timeout=timeout
            )
            
            return result
            
        except Exception as e:
            error = e
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if connection:
                await self.release_connection(connection, error)
    
    async def execute_transaction(
        self, 
        queries: List[tuple], 
        timeout: float = None
    ) -> List[Any]:
        """Execute multiple queries in a transaction"""
        timeout = timeout or self.command_timeout
        connection = None
        error = None
        
        try:
            connection = await self.acquire_connection()
            
            async with connection.transaction():
                results = []
                for query, args in queries:
                    result = await asyncio.wait_for(
                        connection.fetch(query, *args),
                        timeout=timeout
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            error = e
            logger.error(f"Transaction execution failed: {e}")
            raise
        finally:
            if connection:
                await self.release_connection(connection, error)
    
    async def get_pool_stats(self) -> PoolStats:
        """Get detailed pool statistics"""
        if not self.pool:
            return PoolStats(0, 0, 0, self.max_size, self.min_size, 0, 0, 0.0, 0, 0)
        
        avg_acquire_time = sum(self.acquire_times) / len(self.acquire_times) if self.acquire_times else 0.0
        
        return PoolStats(
            size=self.pool.get_size(),
            used=self.pool.get_size() - self.pool.get_idle_size(),
            free=self.pool.get_idle_size(),
            max_size=self.max_size,
            min_size=self.min_size,
            created_connections=self.created_connections,
            closed_connections=self.closed_connections,
            avg_acquire_time=avg_acquire_time,
            total_acquired=self.total_acquired,
            total_released=self.total_released
        )
    
    async def get_connection_health(self) -> List[ConnectionHealth]:
        """Get health status of all connections"""
        return list(self.connection_health.values())
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Comprehensive pool health check"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            response_time = time.time() - start_time
            stats = await self.get_pool_stats()
            
            # Check if pool is getting saturated
            pool_utilization = stats.used / stats.max_size if stats.max_size > 0 else 0
            
            health_status = "healthy"
            if pool_utilization > 0.9:
                health_status = "saturated"
            elif response_time > 1.0:
                health_status = "slow"
            elif stats.used == 0:
                health_status = "idle"
            
            self.last_health_check = datetime.utcnow()
            
            return {
                "status": health_status,
                "response_time_ms": round(response_time * 1000, 2),
                "pool_utilization": round(pool_utilization, 2),
                "stats": {
                    "size": stats.size,
                    "used": stats.used,
                    "free": stats.free,
                    "avg_acquire_time_ms": round(stats.avg_acquire_time * 1000, 2)
                },
                "last_check": self.last_health_check.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Gracefully close the connection pool"""
        if self.pool:
            await self.pool.close()
            self.closed_connections += self.created_connections
            logger.info(f"✅ Supabase connection pool closed (handled {self.total_acquired} connections)")


# Global connection pool instance
_connection_pool: Optional[SupabaseConnectionPool] = None


async def get_connection_pool() -> SupabaseConnectionPool:
    """Get or create global connection pool"""
    global _connection_pool
    
    if _connection_pool is None:
        from ...config.production_config import get_config
        config = get_config()
        
        # Configure pool based on environment
        if config.is_production():
            min_size, max_size = 10, 50  # Production settings
        else:
            min_size, max_size = 5, 20   # Development settings
        
        _connection_pool = SupabaseConnectionPool(
            min_size=min_size,
            max_size=max_size,
            command_timeout=30.0
        )
        
        await _connection_pool.initialize()
    
    return _connection_pool


async def close_connection_pool():
    """Close global connection pool"""
    global _connection_pool
    
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None