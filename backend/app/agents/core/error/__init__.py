"""
Error handling and recovery systems.

This module contains error-related components including:
- Error boundary system for workflow isolation
- Comprehensive error handling and validation
- Automated recovery mechanisms and circuit breaking
"""

from .error_boundary import (
    WorkflowErrorBoundary,
    ErrorSeverity,
    RecoveryStrategy,
    CircuitBreaker,
    ErrorBoundaryConfig,
    ErrorRecord,
    ErrorClassification
)

from .error_handling import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    AgentError,
    ValidationError,
    ExternalAPIError,
    DatabaseError,
    LLMError,
    RateLimitError
)

from .recovery_service import (
    WorkflowRecoveryService,
    RecoveryTrigger,
    RecoveryStatus,
    RecoveryAttempt
)

__all__ = [
    # Error boundary
    "WorkflowErrorBoundary",
    "ErrorSeverity",
    "RecoveryStrategy",
    "CircuitBreaker",
    "ErrorBoundaryConfig",
    "ErrorRecord",
    "ErrorClassification",
    
    # Error handling
    "ErrorHandler",
    "ErrorSeverity",  # Also in error_handling
    "ErrorCategory",
    "AgentError",
    "ValidationError",
    "ExternalAPIError",
    "DatabaseError",
    "LLMError",
    "RateLimitError",
    
    # Recovery service
    "WorkflowRecoveryService",
    "RecoveryTrigger",
    "RecoveryStatus",
    "RecoveryAttempt",
]
