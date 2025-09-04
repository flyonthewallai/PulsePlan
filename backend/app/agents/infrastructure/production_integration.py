"""
Production Infrastructure Integration
Wires together all production components for the supervisor system
"""
import os
import asyncio
from typing import Dict, Any
import logging

from .error_handling import (
    CircuitBreaker, CircuitBreakerConfig, RetryStrategy,
    ErrorSurfacer, get_circuit_breaker, CIRCUIT_BREAKERS
)
from .rate_limiting import ProductionRateLimiter, RateLimitMiddleware
from .security import SecurityValidator, SecurityConfig, PayloadSigner, SecurityMiddleware
from .health_checks import (
    HealthCheckManager, DatabaseHealthCheck, RedisHealthCheck,
    LLMServiceHealthCheck, CircuitBreakerHealthCheck, MemoryHealthCheck
)
from ...config.redis_upstash import get_redis_client, test_redis_connection
from ...config.production_config import get_config, ProductionConfig

logger = logging.getLogger(__name__)


class ProductionInfrastructureManager:
    """Manages all production infrastructure components"""
    
    def __init__(self):
        self.config = None
        self.redis_client = None
        self.rate_limiter = None
        self.security_validator = None
        self.security_middleware = None
        self.health_manager = None
        self.payload_signer = None
        self.retry_strategy = None
        self.error_surfacer = None
        
    async def initialize(self, config: ProductionConfig = None):
        """Initialize all infrastructure components"""
        
        # Load or use provided configuration
        if config is None:
            config = get_config()
        self.config = config
        
        # Initialize Upstash Redis
        self.redis_client = await get_redis_client()
        
        # Test Redis connection
        connection_test = await test_redis_connection()
        if connection_test["status"] == "connected":
            logger.info(f"✅ Upstash Redis connection established (ping: {connection_test['ping_duration_ms']}ms)")
        else:
            logger.error(f"❌ Upstash Redis connection failed: {connection_test.get('error', 'Unknown error')}")
            raise ConnectionError(f"Redis connection failed: {connection_test.get('error')}")
        
        # Initialize Rate Limiter with environment config
        self.rate_limiter = ProductionRateLimiter(self.redis_client, self.config)
        logger.info("✅ Rate limiter initialized with environment configuration")
        
        # Initialize Security Components with environment config
        security_config = self.config.security
        
        self.security_validator = SecurityValidator(security_config)
        
        if security_config.hmac_secret_key:
            self.payload_signer = PayloadSigner(
                security_config.hmac_secret_key,
                security_config.signature_ttl_seconds
            )
        
        self.security_middleware = SecurityMiddleware(
            self.security_validator,
            self.payload_signer
        )
        logger.info("✅ Security components initialized with environment configuration")
        
        # Initialize Error Handling Components with environment config
        retry_config = self.config.retry
        self.retry_strategy = RetryStrategy(
            max_retries=retry_config.max_retries,
            base_delay=retry_config.base_delay,
            max_delay=retry_config.max_delay,
            jitter=retry_config.jitter
        )
        
        self.error_surfacer = ErrorSurfacer()
        logger.info("✅ Error handling components initialized")
        
        # Initialize Health Check Manager
        await self._setup_health_checks()
        logger.info("✅ Health check system initialized")
        
        # Update circuit breakers with environment configuration
        await self._configure_circuit_breakers()
        
        logger.info("🚀 Production infrastructure fully initialized")
    
    async def _setup_health_checks(self):
        """Setup health check system"""
        self.health_manager = HealthCheckManager()
        
        health_config = self.config.health_check
        
        # Database health check
        try:
            from ...config.supabase import get_supabase
            db_check = DatabaseHealthCheck(get_supabase)
            db_check.timeout_seconds = health_config.database_health_timeout
            self.health_manager.register_health_check(db_check)
        except ImportError:
            logger.warning("Database health check skipped - supabase config not found")
        
        # Upstash Redis health check
        redis_check = RedisHealthCheck(self.redis_client)
        redis_check.timeout_seconds = health_config.redis_health_timeout
        self.health_manager.register_health_check(redis_check)
        
        # LLM service health check
        try:
            from langchain_openai import ChatOpenAI
            llm_client = ChatOpenAI(
                model=self.config.llm.openai_model,
                temperature=self.config.llm.openai_temperature,
                timeout=self.config.llm.openai_timeout
            )
            llm_check = LLMServiceHealthCheck(llm_client)
            llm_check.timeout_seconds = health_config.llm_health_timeout
            self.health_manager.register_health_check(llm_check)
        except Exception as e:
            logger.warning(f"LLM health check skipped: {e}")
        
        # Circuit breaker health check
        circuit_breaker_check = CircuitBreakerHealthCheck(CIRCUIT_BREAKERS)
        circuit_breaker_check.timeout_seconds = health_config.health_check_timeout_seconds
        self.health_manager.register_health_check(circuit_breaker_check)
        
        # Memory health check
        memory_check = MemoryHealthCheck()
        memory_check.timeout_seconds = health_config.health_check_timeout_seconds
        self.health_manager.register_health_check(memory_check)
    
    async def _configure_circuit_breakers(self):
        """Configure circuit breakers with environment settings"""
        cb_config = self.config.circuit_breaker
        
        # Update circuit breaker configurations
        CIRCUIT_BREAKERS["llm_service"] = CircuitBreaker(
            "llm_service", 
            CircuitBreakerConfig(
                failure_threshold=cb_config.llm_failure_threshold,
                recovery_timeout=cb_config.llm_recovery_timeout,
                success_threshold=cb_config.default_success_threshold
            )
        )
        
        CIRCUIT_BREAKERS["database"] = CircuitBreaker(
            "database",
            CircuitBreakerConfig(
                failure_threshold=cb_config.database_failure_threshold,
                recovery_timeout=cb_config.database_recovery_timeout,
                success_threshold=cb_config.default_success_threshold
            )
        )
        
        CIRCUIT_BREAKERS["calendar_service"] = CircuitBreaker(
            "calendar_service",
            CircuitBreakerConfig(
                failure_threshold=cb_config.calendar_failure_threshold,
                recovery_timeout=cb_config.calendar_recovery_timeout,
                success_threshold=cb_config.default_success_threshold
            )
        )
        
        CIRCUIT_BREAKERS["email_service"] = CircuitBreaker(
            "email_service",
            CircuitBreakerConfig(
                failure_threshold=cb_config.email_failure_threshold,
                recovery_timeout=cb_config.email_recovery_timeout,
                success_threshold=cb_config.default_success_threshold
            )
        )
        
        logger.info("✅ Circuit breakers configured with environment settings")
    
    async def validate_and_rate_limit_request(
        self,
        user_id: str,
        workflow_type: str,
        query: str,
        parameters: Dict[str, Any],
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Comprehensive request validation and rate limiting
        Returns {"allowed": True} if valid, error dict if invalid
        """
        
        # Step 1: Security validation
        security_result = await self.security_middleware.validate_request(
            query, parameters, user_id, client_ip
        )
        
        if security_result:  # Security validation failed
            return {
                "allowed": False,
                "reason": "security_validation_failed",
                **security_result
            }
        
        # Step 2: Rate limiting
        rate_limit_middleware = RateLimitMiddleware(self.rate_limiter)
        rate_limit_result = await rate_limit_middleware.check_and_apply_rate_limit(
            user_id, workflow_type
        )
        
        if rate_limit_result:  # Rate limit exceeded
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                **rate_limit_result
            }
        
        # All checks passed
        return {"allowed": True}
    
    async def execute_with_resilience(
        self,
        service_name: str,
        func,
        *args,
        use_retry: bool = True,
        use_circuit_breaker: bool = True,
        **kwargs
    ):
        """Execute function with full resilience patterns"""
        
        try:
            # Wrap with circuit breaker if enabled
            if use_circuit_breaker:
                circuit_breaker = get_circuit_breaker(service_name)
                if circuit_breaker:
                    if use_retry:
                        # Combine circuit breaker + retry
                        return await circuit_breaker.call(
                            self.retry_strategy.execute_with_retry,
                            func, *args, **kwargs
                        )
                    else:
                        # Circuit breaker only
                        return await circuit_breaker.call(func, *args, **kwargs)
            
            # Retry only (no circuit breaker)
            if use_retry:
                return await self.retry_strategy.execute_with_retry(func, *args, **kwargs)
            
            # Direct execution (no resilience patterns)
            return await func(*args, **kwargs)
            
        except Exception as e:
            # Surface error appropriately
            error_response = self.error_surfacer.surface_service_error(
                service_name, e, retry_after_seconds=60
            )
            
            logger.error(f"Service {service_name} failed: {e}")
            return {"error": True, **error_response}
    
    async def get_system_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        if not self.health_manager:
            return {"error": "Health manager not initialized"}
        
        return await self.health_manager.check_health(include_details)
    
    async def get_system_readiness(self) -> Dict[str, Any]:
        """Check if system is ready to serve requests"""
        if not self.health_manager:
            return {"ready": False, "reason": "Health manager not initialized"}
        
        return await self.health_manager.check_readiness()
    
    async def get_rate_limit_stats(self, user_id: str, workflow_type: str) -> Dict[str, Any]:
        """Get rate limiting statistics for monitoring"""
        if not self.rate_limiter:
            return {"error": "Rate limiter not initialized"}
        
        user_stats = await self.rate_limiter.get_user_usage_stats(user_id, workflow_type)
        global_stats = await self.rate_limiter.get_global_usage_stats(workflow_type)
        
        return {
            "user_stats": user_stats,
            "global_stats": global_stats
        }
    
    async def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all services"""
        return {
            name: breaker.get_status()
            for name, breaker in CIRCUIT_BREAKERS.items()
        }
    
    async def shutdown(self):
        """Gracefully shutdown all components"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Redis connection closed")
        
        logger.info("🔌 Production infrastructure shutdown complete")


# Global infrastructure manager instance
_infrastructure_manager = None


async def get_infrastructure_manager() -> ProductionInfrastructureManager:
    """Get or create global infrastructure manager"""
    global _infrastructure_manager
    
    if _infrastructure_manager is None:
        _infrastructure_manager = ProductionInfrastructureManager()
        
        # Configuration is now loaded automatically from environment variables
        # via the get_config() function in production_config.py
        await _infrastructure_manager.initialize()
    
    return _infrastructure_manager


# Integration helpers for supervisor system
async def validate_supervisor_request(
    user_id: str,
    workflow_type: str, 
    query: str,
    parameters: Dict[str, Any] = None,
    client_ip: str = "127.0.0.1"
) -> Dict[str, Any]:
    """Validate supervisor request with full production checks"""
    infrastructure = await get_infrastructure_manager()
    
    return await infrastructure.validate_and_rate_limit_request(
        user_id, workflow_type, query, parameters or {}, client_ip
    )


async def execute_supervisor_with_resilience(
    service_name: str,
    supervisor_func,
    *args,
    **kwargs
):
    """Execute supervisor function with full resilience patterns"""
    infrastructure = await get_infrastructure_manager()
    
    return await infrastructure.execute_with_resilience(
        service_name, supervisor_func, *args, **kwargs
    )


# FastAPI integration endpoints
async def health_check_endpoint():
    """FastAPI health check endpoint"""
    infrastructure = await get_infrastructure_manager()
    return await infrastructure.get_system_health(include_details=True)


async def readiness_check_endpoint():
    """FastAPI readiness check endpoint"""
    infrastructure = await get_infrastructure_manager()
    return await infrastructure.get_system_readiness()


async def metrics_endpoint():
    """FastAPI metrics endpoint"""
    infrastructure = await get_infrastructure_manager()
    
    # Get various metrics
    circuit_breaker_status = await infrastructure.get_circuit_breaker_status()
    health_summary = await infrastructure.get_system_health(include_details=False)
    
    return {
        "circuit_breakers": circuit_breaker_status,
        "health_summary": health_summary,
        "timestamp": health_summary["summary"]["timestamp"]
    }