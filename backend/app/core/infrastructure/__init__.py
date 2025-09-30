"""
Infrastructure core module.

This module contains all infrastructure-related core functionality including:
- Caching services and utilities
- Circuit breaker pattern implementation
- WebSocket connection management
- Infrastructure resilience patterns
"""

from .cache import (
    MockRedisClient
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerStats,
    CircuitBreakerError,
    CircuitBreakerManager,
    get_circuit_breaker_manager,
    circuit_breaker
)
from .websocket import (
    WebSocketManager,
    websocket_manager
)

__all__ = [
    # Cache
    "MockRedisClient",
    
    # Circuit breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerStats", 
    "CircuitBreakerError",
    "CircuitBreakerManager",
    "get_circuit_breaker_manager",
    "circuit_breaker",
    
    # WebSocket
    "WebSocketManager",
    "websocket_manager",
]
