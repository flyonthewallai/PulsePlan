"""
Production Health Check System
Comprehensive health monitoring for all system dependencies
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check"""
    name: str
    status: HealthStatus
    response_time_ms: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class SystemHealthSummary:
    """Overall system health summary"""
    overall_status: HealthStatus
    healthy_checks: int
    degraded_checks: int
    unhealthy_checks: int
    total_checks: int
    timestamp: datetime
    uptime_seconds: float
    version: str = "1.0.0"


class BaseHealthCheck:
    """Base class for health checks"""
    
    def __init__(self, name: str, timeout_seconds: float = 5.0):
        self.name = name
        self.timeout_seconds = timeout_seconds
    
    async def check(self) -> HealthCheckResult:
        """Perform health check with timeout"""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self._perform_check(),
                timeout=self.timeout_seconds
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=result.get("status", HealthStatus.UNKNOWN),
                response_time_ms=response_time,
                message=result.get("message", "Check completed"),
                details=result.get("details", {}),
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Health check timed out after {self.timeout_seconds}s",
                details={},
                timestamp=datetime.utcnow(),
                error="timeout"
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Health check failed: {str(e)}",
                details={"exception_type": type(e).__name__},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Override this method in specific health checks"""
        raise NotImplementedError


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for database connectivity"""
    
    def __init__(self, todo_repository=None):
        super().__init__("database", timeout_seconds=10.0)
        self._todo_repository = todo_repository
    
    def _get_todo_repository(self):
        """Lazy-load todo repository"""
        if self._todo_repository is None:
            from app.database.repositories.task_repositories.todo_repository import TodoRepository
            self._todo_repository = TodoRepository()
        return self._todo_repository
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Use repository to test connectivity
            todo_repo = self._get_todo_repository()
            
            # Simple query to test connectivity using repository health check
            start_query_time = time.time()
            is_healthy = await todo_repo.health_check()
            query_time = (time.time() - start_query_time) * 1000
            
            if not is_healthy:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Database health check failed",
                    "details": {
                        "query_time_ms": round(query_time, 2)
                    },
                    "timestamp": datetime.utcnow()
                }
            
            # Determine status based on response time
            if query_time < 100:
                status = HealthStatus.HEALTHY
                message = "Database is healthy"
            elif query_time < 1000:
                status = HealthStatus.DEGRADED
                message = "Database is slow but operational"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Database is very slow"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "query_time_ms": round(query_time, 2),
                    "connection_pool_size": "unknown",  # Would need actual pool info
                    "active_connections": "unknown"
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database connection failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }


class RedisHealthCheck(BaseHealthCheck):
    """Health check for Redis connectivity"""
    
    def __init__(self, redis_client):
        super().__init__("redis", timeout_seconds=5.0)
        self.redis = redis_client
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            # Test basic connectivity
            start_time = time.time()
            await self.redis.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Test read/write
            test_key = f"health_check:{int(time.time())}"
            await self.redis.set(test_key, "test_value", ex=60)
            test_value = await self.redis.get(test_key)
            await self.redis.delete(test_key)
            
            if test_value != b"test_value":
                raise Exception("Redis read/write test failed")
            
            # Get Redis info
            info = await self.redis.info()
            memory_usage = info.get("used_memory_human", "unknown")
            connected_clients = info.get("connected_clients", "unknown")
            
            # Determine status
            if ping_time < 50:
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"
            elif ping_time < 200:
                status = HealthStatus.DEGRADED
                message = "Redis is slow but operational"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Redis is very slow"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "ping_time_ms": round(ping_time, 2),
                    "memory_usage": memory_usage,
                    "connected_clients": connected_clients,
                    "redis_version": info.get("redis_version", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Redis connection failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }


class LLMServiceHealthCheck(BaseHealthCheck):
    """Health check for LLM service (OpenAI)"""
    
    def __init__(self, llm_client):
        super().__init__("llm_service", timeout_seconds=30.0)
        self.llm = llm_client
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check LLM service availability and performance"""
        try:
            # Simple test query
            start_time = time.time()
            test_prompt = "Respond with exactly: OK"
            
            response = await self.llm.ainvoke(test_prompt)
            response_time = (time.time() - start_time) * 1000
            
            # Check if response is reasonable
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            if "OK" not in response_text:
                logger.warning(f"Unexpected LLM response: {response_text}")
            
            # Determine status based on response time
            if response_time < 5000:  # 5 seconds
                status = HealthStatus.HEALTHY
                message = "LLM service is healthy"
            elif response_time < 15000:  # 15 seconds
                status = HealthStatus.DEGRADED
                message = "LLM service is slow but operational"
            else:
                status = HealthStatus.UNHEALTHY
                message = "LLM service is very slow"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "response_time_ms": round(response_time, 2),
                    "model": getattr(self.llm, 'model_name', 'unknown'),
                    "response_length": len(response_text),
                    "response_preview": response_text[:50] + "..." if len(response_text) > 50 else response_text
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"LLM service failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }


class CircuitBreakerHealthCheck(BaseHealthCheck):
    """Health check for circuit breaker status"""
    
    def __init__(self, circuit_breakers: Dict):
        super().__init__("circuit_breakers", timeout_seconds=1.0)
        self.circuit_breakers = circuit_breakers
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check circuit breaker states"""
        try:
            breaker_states = {}
            unhealthy_count = 0
            degraded_count = 0
            
            for name, breaker in self.circuit_breakers.items():
                breaker_status = breaker.get_status()
                breaker_states[name] = breaker_status
                
                if breaker_status["state"] == "open":
                    unhealthy_count += 1
                elif breaker_status["state"] == "half_open":
                    degraded_count += 1
            
            total_breakers = len(self.circuit_breakers)
            
            # Determine overall status
            if unhealthy_count == 0 and degraded_count == 0:
                status = HealthStatus.HEALTHY
                message = "All circuit breakers are closed"
            elif unhealthy_count == 0:
                status = HealthStatus.DEGRADED
                message = f"{degraded_count} circuit breakers are half-open"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{unhealthy_count} circuit breakers are open, {degraded_count} are half-open"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_breakers": total_breakers,
                    "healthy_breakers": total_breakers - unhealthy_count - degraded_count,
                    "degraded_breakers": degraded_count,
                    "unhealthy_breakers": unhealthy_count,
                    "breaker_states": breaker_states
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Circuit breaker check failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }


class MemoryHealthCheck(BaseHealthCheck):
    """Health check for system memory usage"""
    
    def __init__(self):
        super().__init__("memory", timeout_seconds=2.0)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check system memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            
            # Determine status based on memory usage
            if memory_percent < 80:
                status = HealthStatus.HEALTHY
                message = "Memory usage is normal"
            elif memory_percent < 90:
                status = HealthStatus.DEGRADED
                message = "Memory usage is high"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Memory usage is critical"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "memory_percent": round(memory_percent, 1),
                    "memory_available_gb": round(memory_available_gb, 2),
                    "memory_total_gb": round(memory_total_gb, 2),
                    "memory_used_gb": round((memory_total_gb - memory_available_gb), 2)
                }
            }
            
        except ImportError:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "psutil not available for memory monitoring",
                "details": {}
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Memory check failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }


class HealthCheckManager:
    """Manages all health checks and provides comprehensive health reporting"""
    
    def __init__(self):
        self.health_checks: List[BaseHealthCheck] = []
        self.start_time = time.time()
        self.last_check_results: Dict[str, HealthCheckResult] = {}
    
    def register_health_check(self, health_check: BaseHealthCheck):
        """Register a health check"""
        self.health_checks.append(health_check)
        logger.info(f"Registered health check: {health_check.name}")
    
    async def check_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Perform all health checks and return comprehensive results"""
        
        # Run all health checks in parallel
        tasks = [check.check() for check in self.health_checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        check_results = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Health check itself failed
                check_result = HealthCheckResult(
                    name=self.health_checks[i].name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    message=f"Health check failed: {str(result)}",
                    details={},
                    timestamp=datetime.utcnow(),
                    error=str(result)
                )
            else:
                check_result = result
            
            check_results.append(check_result)
            self.last_check_results[check_result.name] = check_result
            
            # Count statuses
            if check_result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif check_result.status == HealthStatus.DEGRADED:
                degraded_count += 1
            else:
                unhealthy_count += 1
        
        # Determine overall status
        total_checks = len(check_results)
        if unhealthy_count == 0 and degraded_count == 0:
            overall_status = HealthStatus.HEALTHY
        elif unhealthy_count == 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        # Create summary
        summary = SystemHealthSummary(
            overall_status=overall_status,
            healthy_checks=healthy_count,
            degraded_checks=degraded_count,
            unhealthy_checks=unhealthy_count,
            total_checks=total_checks,
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - self.start_time
        )
        
        # Build response
        response = {
            "summary": asdict(summary),
            "status": overall_status.value
        }
        
        if include_details:
            response["checks"] = [
                {
                    "name": result.name,
                    "status": result.status.value,
                    "response_time_ms": result.response_time_ms,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat(),
                    "details": result.details,
                    "error": result.error
                }
                for result in check_results
            ]
        
        return response
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Check if system is ready to serve requests (critical checks only)"""
        critical_checks = ["database", "redis", "llm_service"]
        
        tasks = [
            check.check() for check in self.health_checks
            if check.name in critical_checks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if all critical services are healthy
        ready = True
        failed_services = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception) or result.status == HealthStatus.UNHEALTHY:
                ready = False
                service_name = [
                    check.name for check in self.health_checks 
                    if check.name in critical_checks
                ][i]
                failed_services.append(service_name)
        
        return {
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "failed_services": failed_services,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_last_check_results(self) -> Dict[str, Dict[str, Any]]:
        """Get results from last health check without running new checks"""
        return {
            name: {
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "error": result.error
            }
            for name, result in self.last_check_results.items()
        }