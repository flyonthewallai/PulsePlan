"""
Circuit Breaker Implementation
Provides circuit breaker pattern for external service calls with configurable thresholds
"""
import asyncio
import time
from enum import Enum
from typing import Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
import logging
from app.config.core.settings import get_settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    total_requests: int = 0
    failed_requests: int = 0
    successful_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changed_at: float = field(default_factory=time.time)


class CircuitBreakerError(Exception):
    """Circuit breaker is open"""
    def __init__(self, service_name: str, stats: CircuitBreakerStats):
        self.service_name = service_name
        self.stats = stats
        super().__init__(f"Circuit breaker is OPEN for {service_name}")


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls
    """
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        timeout: int = 30,
        expected_exception: type = Exception
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.lock = asyncio.Lock()
        
        # Consecutive successes in HALF_OPEN state
        self._consecutive_successes = 0
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Call function through circuit breaker
        """
        async with self.lock:
            await self._update_state()
            
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError(self.service_name, self.stats)
        
        # Execute the function with timeout
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )
            await self._on_success()
            return result
            
        except asyncio.TimeoutError:
            await self._on_failure(f"Timeout after {self.timeout}s")
            raise
        except self.expected_exception as e:
            await self._on_failure(str(e))
            raise
        except Exception as e:
            await self._on_failure(f"Unexpected error: {str(e)}")
            raise
    
    async def _update_state(self):
        """Update circuit breaker state based on current conditions"""
        now = time.time()
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.stats.last_failure_time and 
                now - self.stats.last_failure_time >= self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.stats.state_changed_at = now
                self._consecutive_successes = 0
                logger.info(f"Circuit breaker {self.service_name} moved to HALF_OPEN state")
        
        elif self.state == CircuitState.HALF_OPEN:
            # Check if we should move to CLOSED (enough successes)
            if self._consecutive_successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.stats.state_changed_at = now
                self._consecutive_successes = 0
                logger.info(f"Circuit breaker {self.service_name} moved to CLOSED state")
    
    async def _on_success(self):
        """Handle successful call"""
        async with self.lock:
            self.stats.successful_requests += 1
            self.stats.total_requests += 1
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
            
            logger.debug(f"Circuit breaker {self.service_name}: Success recorded")
    
    async def _on_failure(self, error: str):
        """Handle failed call"""
        async with self.lock:
            self.stats.failed_requests += 1
            self.stats.total_requests += 1
            self.stats.last_failure_time = time.time()
            
            # Reset consecutive successes on failure
            self._consecutive_successes = 0
            
            # Check if we should open the circuit
            if (self.state == CircuitState.CLOSED and 
                self.stats.failed_requests >= self.failure_threshold):
                self.state = CircuitState.OPEN
                self.stats.state_changed_at = time.time()
                logger.warning(f"Circuit breaker {self.service_name} OPENED due to {self.failure_threshold} failures")
            
            elif self.state == CircuitState.HALF_OPEN:
                # Single failure in HALF_OPEN moves back to OPEN
                self.state = CircuitState.OPEN
                self.stats.state_changed_at = time.time()
                logger.warning(f"Circuit breaker {self.service_name} moved back to OPEN from HALF_OPEN")
            
            logger.debug(f"Circuit breaker {self.service_name}: Failure recorded - {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "stats": {
                "total_requests": self.stats.total_requests,
                "failed_requests": self.stats.failed_requests,
                "successful_requests": self.stats.successful_requests,
                "failure_rate": (self.stats.failed_requests / self.stats.total_requests * 100) 
                               if self.stats.total_requests > 0 else 0,
                "last_failure_time": self.stats.last_failure_time,
                "last_success_time": self.stats.last_success_time,
                "state_changed_at": self.stats.state_changed_at
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold,
                "timeout": self.timeout
            }
        }
    
    async def reset(self):
        """Reset circuit breaker to initial state"""
        async with self.lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitBreakerStats()
            self._consecutive_successes = 0
            logger.info(f"Circuit breaker {self.service_name} reset to CLOSED state")


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, service_type: str, service_name: Optional[str] = None) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        breaker_key = f"{service_type}:{service_name}" if service_name else service_type
        
        if breaker_key not in self._breakers:
            config = self.settings.get_circuit_breaker_config(service_type)
            
            self._breakers[breaker_key] = CircuitBreaker(
                service_name=breaker_key,
                failure_threshold=config["failure_threshold"],
                recovery_timeout=config["recovery_timeout"],
                success_threshold=config["success_threshold"]
            )
            
            logger.info(f"Created circuit breaker for {breaker_key}")
        
        return self._breakers[breaker_key]
    
    async def call_with_breaker(
        self,
        service_type: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        service_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Call function through appropriate circuit breaker"""
        breaker = self.get_breaker(service_type, service_name)
        return await breaker.call(func, *args, **kwargs)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            await breaker.reset()
        logger.info("All circuit breakers reset")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all circuit breakers"""
        stats = self.get_all_stats()
        
        # Count breakers by state
        open_count = sum(1 for s in stats.values() if s["state"] == "open")
        half_open_count = sum(1 for s in stats.values() if s["state"] == "half_open")
        closed_count = sum(1 for s in stats.values() if s["state"] == "closed")
        
        return {
            "status": "healthy" if open_count == 0 else "degraded",
            "total_breakers": len(stats),
            "open_breakers": open_count,
            "half_open_breakers": half_open_count,
            "closed_breakers": closed_count,
            "breakers": stats
        }


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    global _circuit_breaker_manager
    
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
        logger.info("Circuit breaker manager initialized")
    
    return _circuit_breaker_manager


async def call_with_circuit_breaker(
    service_type: str,
    func: Callable[..., Awaitable[Any]],
    *args,
    service_name: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Convenience function to call any async function through circuit breaker
    """
    manager = get_circuit_breaker_manager()
    return await manager.call_with_breaker(service_type, func, *args, service_name=service_name, **kwargs)


# Decorator for circuit breaker
def circuit_breaker(service_type: str, service_name: Optional[str] = None):
    """
    Decorator to add circuit breaker to async functions
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        async def wrapper(*args, **kwargs):
            return await call_with_circuit_breaker(
                service_type, func, *args, service_name=service_name, **kwargs
            )
        return wrapper
    return decorator