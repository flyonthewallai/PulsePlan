"""
Observability core module.

This module contains all observability and error handling core functionality including:
- LLM client configuration and monitoring
- Error handlers and exception management
- Logging and tracing utilities
- Application monitoring and diagnostics
"""

from .llm import (
    LLMClient,
    LLMResponse,
    get_llm_client
)
from .error_handlers import (
    PulsePlanError,
    WorkflowError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ExternalServiceError,
    ValidationError,
    generate_error_id,
    format_error_response,
    setup_error_handlers,
    circuit_breaker_error_handler,
    database_error_handler
)

__all__ = [
    "LLMClient",
    "LLMResponse",
    "get_llm_client",
    "PulsePlanError",
    "WorkflowError",
    "AuthenticationError", 
    "AuthorizationError",
    "RateLimitError",
    "ExternalServiceError",
    "ValidationError",
    "generate_error_id",
    "format_error_response",
    "setup_error_handlers",
    "circuit_breaker_error_handler",
    "database_error_handler",
]
