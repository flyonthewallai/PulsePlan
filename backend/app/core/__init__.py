"""
Core module - Essential application core functionality.

This module provides organized access to all core components grouped by domain:
- auth: Authentication, authorization, and security utilities
- infrastructure: Caching, circuit breakers, WebSocket management
- observability: LLM clients, error handling, and monitoring
"""

# Re-export from modules for backward compatibility
from .auth import *  # Fixed security functions
from .infrastructure import *  # Fixed imports
from .observability import *  # Test if observability imports work now

# Core utilities available to all modules
from .utils import get_timezone_manager, TimezoneManager, ensure_timezone_aware

# Direct import to avoid infrastructure module issues
from .infrastructure.websocket import websocket_manager

__all__ = [
    # Auth services
    "verify_supabase_token",
    "require_admin",
    "check_user_access",
    "generate_secret_key",
    "validate_email",
    "sanitize_input",
    "check_password_strength",
    
    # Infrastructure services
    "MockRedisClient",
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerStats",
    "CircuitBreakerError", 
    "CircuitBreakerManager",
    "get_circuit_breaker_manager",
    "circuit_breaker",
    "WebSocketManager",
    
    # Observability services
    "LLMClient",
    "LLMConfig",
    "GPTClient", 
    "OpenAI",
    "Anthropic",
    "get_llm_client",
    "log_llm_request",
    "log_llm_response",
    "global_exception_handler",
    "validation_error_handler",
    "http_error_handler",
    "log_error_with_context",
    "ErrorContext",
    
    # Core timezone utilities
    "get_timezone_manager",
    "TimezoneManager",
    "ensure_timezone_aware",
    
    # WebSocket manager
    "websocket_manager",
]
