"""
Production Error Handling Infrastructure
Circuit breakers, retry strategies, and error surfacing
"""
import asyncio
import time
import random
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    CLOSED = "closed"    # Normal operation
    OPEN = "open"       # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 2  # successes needed to close from half-open


class RetryableError(Exception):
    """Exception that should trigger retries"""
    pass


class NonRetryableError(Exception):
    """Exception that should NOT trigger retries"""
    pass


class CircuitBreaker:
    """Circuit breaker with proper state transitions"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0  # For half-open state
        self.last_failure_time = None
        self.next_attempt_time = None
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        # Check if we should reject the request
        if self._should_reject():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Next retry allowed at {self.next_attempt_time}"
            )
        
        # Try to execute the function
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise
    
    def _should_reject(self) -> bool:
        """Determine if request should be rejected"""
        now = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return False
        
        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout period has passed
            if self.next_attempt_time and now >= self.next_attempt_time:
                self._transition_to_half_open()
                return False
            return True
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited requests to test recovery
            return False
        
        return False
    
    def _record_success(self):
        """Record successful execution"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _record_failure(self, error: Exception):
        """Record failed execution and handle state transitions"""
        now = time.time()
        
        # Only count certain types of failures
        if isinstance(error, NonRetryableError):
            return  # Don't count towards circuit breaker
        
        self.failure_count += 1
        self.last_failure_time = now
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Single failure in half-open immediately goes back to open
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitBreakerState.OPEN
        self.next_attempt_time = time.time() + self.config.recovery_timeout
        logger.warning(
            f"Circuit breaker '{self.name}' OPEN. "
            f"Will retry at {datetime.fromtimestamp(self.next_attempt_time)}"
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' HALF_OPEN. Testing recovery...")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.next_attempt_time = None
        logger.info(f"Circuit breaker '{self.name}' CLOSED. Normal operation resumed.")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "next_attempt_time": self.next_attempt_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold
            }
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class RetryStrategy:
    """Exponential backoff with jitter and selective error handling"""
    
    def __init__(
        self, 
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
    
    async def execute_with_retry(
        self, 
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return await func(*args, **kwargs)
            
            except NonRetryableError:
                # Don't retry these errors
                raise
            
            except (RetryableError, asyncio.TimeoutError, ConnectionError) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    # Last attempt failed
                    break
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                # Add jitter to prevent thundering herd
                if self.jitter:
                    delay = delay * (0.5 + random.random() * 0.5)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
            
            except Exception as e:
                # Unknown error - treat as non-retryable for safety
                logger.error(f"Unknown error during retry: {e}")
                raise NonRetryableError(f"Unknown error: {e}") from e
        
        # All retries exhausted
        raise RetryableError(
            f"Max retries ({self.max_retries}) exhausted. Last error: {last_exception}"
        ) from last_exception


class ErrorSurfacer:
    """Surface errors clearly with actionable alternatives"""
    
    @staticmethod
    def surface_service_error(
        service_name: str, 
        error: Exception,
        retry_after_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create user-friendly error message with alternatives"""
        
        base_message = f"{service_name} is temporarily unavailable"
        
        # Add retry information
        if retry_after_seconds:
            retry_time = datetime.now() + timedelta(seconds=retry_after_seconds)
            base_message += f", retry after {retry_time.strftime('%H:%M')}"
        else:
            base_message += ", please try again in a few minutes"
        
        # Provide actionable alternatives
        alternatives = []
        
        if "calendar" in service_name.lower():
            alternatives = [
                "I can create a reminder to try this again later",
                "Would you like me to save this as a todo for manual scheduling?",
                "I can check your local calendar cache for basic availability"
            ]
        elif "email" in service_name.lower():
            alternatives = [
                "I can save this email as a draft for you to send later",
                "Would you like me to queue this email to send when service recovers?",
                "I can create a reminder to follow up on this email"
            ]
        elif "todo" in service_name.lower():
            alternatives = [
                "I can store this locally and sync when service recovers",
                "Would you like me to create a reminder about this todo?",
                "I can save this to a temporary list for now"
            ]
        else:
            alternatives = [
                "I can retry this in the background and notify you when it succeeds",
                "Would you like me to save this request and try again later?",
                "I can create a reminder to follow up on this"
            ]
        
        return {
            "type": "service_error",
            "message": base_message,
            "service": service_name,
            "alternatives": alternatives,
            "error_id": f"error_{int(time.time())}",
            "retry_after": retry_after_seconds,
            "can_queue_for_retry": True
        }
    
    @staticmethod
    def surface_validation_error(
        field_name: str,
        current_value: Any,
        allowed_values: Optional[List[Any]] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Surface validation errors with clear guidance"""
        
        message = f"Invalid {field_name.replace('_', ' ')}: {current_value}"
        
        suggestions = []
        if allowed_values:
            suggestions.append(f"Allowed values: {', '.join(map(str, allowed_values))}")
        elif pattern:
            suggestions.append(f"Expected format: {pattern}")
        
        return {
            "type": "validation_error",
            "message": message,
            "field": field_name,
            "current_value": current_value,
            "suggestions": suggestions,
            "can_fix_automatically": bool(allowed_values and len(allowed_values) == 1)
        }


# Global circuit breakers for common services
CIRCUIT_BREAKERS = {
    "llm_service": CircuitBreaker("llm_service", CircuitBreakerConfig(
        failure_threshold=3, recovery_timeout=30, success_threshold=1
    )),
    "database": CircuitBreaker("database", CircuitBreakerConfig(
        failure_threshold=5, recovery_timeout=60, success_threshold=2
    )),
    "calendar_service": CircuitBreaker("calendar_service", CircuitBreakerConfig(
        failure_threshold=3, recovery_timeout=45, success_threshold=1
    )),
    "email_service": CircuitBreaker("email_service", CircuitBreakerConfig(
        failure_threshold=3, recovery_timeout=45, success_threshold=1
    ))
}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get circuit breaker for a service"""
    return CIRCUIT_BREAKERS.get(service_name)


async def with_circuit_breaker(service_name: str, func: Callable, *args, **kwargs):
    """Execute function with circuit breaker protection"""
    circuit_breaker = get_circuit_breaker(service_name)
    if circuit_breaker:
        return await circuit_breaker.call(func, *args, **kwargs)
    else:
        return await func(*args, **kwargs)