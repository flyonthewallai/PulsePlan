import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
from app.config.cache.redis_client import get_redis_client
from app.config.database.supabase import get_supabase_client
from app.security.encryption import encryption_service

logger = logging.getLogger(__name__)

class HealthManager:
    """Health check manager for monitoring service dependencies"""
    
    def __init__(self):
        self.startup_time = datetime.now(timezone.utc)
        self.checks = {}
    
    async def initialize(self):
        """Initialize health check manager"""
        logger.info("Health check manager initialized")
    
    async def basic_health(self) -> Dict[str, Any]:
        """Basic health check - service is running"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "pulseplan-fastapi",
            "version": "2.0.0",
            "uptime_seconds": self._get_uptime_seconds()
        }
    
    async def detailed_health(self) -> Dict[str, Any]:
        """Detailed health check with dependency status"""
        health_status = await self.basic_health()
        
        # Check all dependencies in parallel
        checks = await asyncio.gather(
            self._check_redis(),
            self._check_supabase(),
            self._check_encryption(),
            return_exceptions=True
        )
        
        redis_check, supabase_check, encryption_check = checks
        
        # Aggregate results
        health_status["checks"] = {
            "redis": redis_check if not isinstance(redis_check, Exception) else {"status": "error", "error": str(redis_check)},
            "supabase": supabase_check if not isinstance(supabase_check, Exception) else {"status": "error", "error": str(supabase_check)},
            "encryption": encryption_check if not isinstance(encryption_check, Exception) else {"status": "error", "error": str(encryption_check)}
        }
        
        # Determine overall health
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in health_status["checks"].values() 
            if isinstance(check, dict)
        )
        
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
    
    async def readiness_check(self) -> bool:
        """Kubernetes-style readiness check"""
        try:
            health = await self.detailed_health()
            return health["status"] == "healthy"
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return False
    
    async def liveness_check(self) -> bool:
        """Kubernetes-style liveness check"""
        try:
            # Basic check - service is responding
            basic = await self.basic_health()
            return basic["status"] == "healthy"
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return False
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            if not redis_client.client:
                return {"status": "unavailable", "message": "Redis client not initialized"}
            
            # Test basic operation with timeout
            result = await asyncio.wait_for(redis_client.ping(), timeout=3.0)
            
            if result:
                return {"status": "healthy", "message": "Redis connection OK"}
            else:
                return {"status": "unhealthy", "message": "Redis ping failed"}
                
        except asyncio.TimeoutError:
            return {"status": "unhealthy", "message": "Redis timeout"}
        except Exception as e:
            return {"status": "error", "message": f"Redis error: {str(e)}"}
    
    async def _check_supabase(self) -> Dict[str, Any]:
        """Check Supabase connectivity"""
        try:
            if not supabase_client.is_available():
                return {"status": "unavailable", "message": "Supabase client not available"}
            
            # Test basic query with timeout
            supabase = supabase_client.get_client()
            
            # Simple query to test connection
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: supabase.table('calendar_connections').select("count", count="exact").limit(1).execute()
                ),
                timeout=5.0
            )
            
            if result:
                return {"status": "healthy", "message": "Supabase connection OK"}
            else:
                return {"status": "unhealthy", "message": "Supabase query failed"}
                
        except asyncio.TimeoutError:
            return {"status": "unhealthy", "message": "Supabase timeout"}
        except Exception as e:
            return {"status": "error", "message": f"Supabase error: {str(e)}"}
    
    async def _check_encryption(self) -> Dict[str, Any]:
        """Check encryption service"""
        try:
            # Test encryption/decryption cycle
            if encryption_service.health_check():
                return {"status": "healthy", "message": "Encryption service OK"}
            else:
                return {"status": "unhealthy", "message": "Encryption health check failed"}
                
        except Exception as e:
            return {"status": "error", "message": f"Encryption error: {str(e)}"}
    
    def _get_uptime_seconds(self) -> float:
        """Get service uptime in seconds"""
        uptime = datetime.now(timezone.utc) - self.startup_time
        return uptime.total_seconds()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Health check manager cleanup complete")

# Global health manager instance
health_manager = HealthManager()
