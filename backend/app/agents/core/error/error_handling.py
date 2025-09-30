"""
Comprehensive Error Handling System
Production-grade error handling with user-friendly messages and recovery mechanisms
"""
import logging
import traceback
from typing import Dict, Any, Optional, Type, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from app.core.infrastructure.websocket import websocket_manager

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for better handling"""
    USER_INPUT = "user_input"
    SYSTEM = "system"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    LLM = "llm"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    NETWORK = "network"
    PERMISSION = "permission"


class AgentError(Exception):
    """Base exception for agent operations"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recoverable: bool = True,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or self._generate_user_message(category, message)
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.context = context or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow()

    def _generate_user_message(self, category: ErrorCategory, technical_message: str) -> str:
        """Generate user-friendly message based on error category"""
        user_messages = {
            ErrorCategory.USER_INPUT: "Please check your input and try again.",
            ErrorCategory.SYSTEM: "I encountered a technical issue. Please try again in a moment.",
            ErrorCategory.EXTERNAL_API: "I'm having trouble connecting to external services. Please try again later.",
            ErrorCategory.DATABASE: "I'm having trouble accessing data. Please try again in a moment.",
            ErrorCategory.LLM: "I'm having trouble processing your request. Please try rephrasing it.",
            ErrorCategory.AUTHENTICATION: "There's an issue with your authentication. Please log in again.",
            ErrorCategory.RATE_LIMIT: "You're making requests too quickly. Please wait a moment and try again.",
            ErrorCategory.VALIDATION: "The information provided doesn't meet the required format.",
            ErrorCategory.NETWORK: "I'm having network connectivity issues. Please try again later.",
            ErrorCategory.PERMISSION: "You don't have permission to perform this action."
        }
        return user_messages.get(category, "An unexpected error occurred. Please try again.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/transmission"""
        return {
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_error) if self.original_error else None
        }


class ValidationError(AgentError):
    """Error for validation failures"""

    def __init__(self, message: str, field: str = None, **kwargs):
        kwargs.setdefault("category", ErrorCategory.VALIDATION)
        kwargs.setdefault("severity", ErrorSeverity.LOW)
        if field:
            kwargs.setdefault("context", {}).update({"field": field})
        super().__init__(message, **kwargs)


class ExternalAPIError(AgentError):
    """Error for external API failures"""

    def __init__(self, service: str, status_code: int = None, **kwargs):
        kwargs.setdefault("category", ErrorCategory.EXTERNAL_API)
        kwargs.setdefault("severity", ErrorSeverity.MEDIUM)
        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("retry_after", 30)
        kwargs.setdefault("context", {}).update({
            "service": service,
            "status_code": status_code
        })
        super().__init__(f"External API error: {service}", **kwargs)


class DatabaseError(AgentError):
    """Error for database operations"""

    def __init__(self, operation: str, **kwargs):
        kwargs.setdefault("category", ErrorCategory.DATABASE)
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("retry_after", 5)
        kwargs.setdefault("context", {}).update({"operation": operation})
        super().__init__(f"Database error during {operation}", **kwargs)


class LLMError(AgentError):
    """Error for LLM operations"""

    def __init__(self, operation: str, **kwargs):
        kwargs.setdefault("category", ErrorCategory.LLM)
        kwargs.setdefault("severity", ErrorSeverity.MEDIUM)
        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("retry_after", 10)
        kwargs.setdefault("context", {}).update({"operation": operation})
        super().__init__(f"LLM error during {operation}", **kwargs)


class RateLimitError(AgentError):
    """Error for rate limiting"""

    def __init__(self, retry_after: int = 60, **kwargs):
        kwargs.setdefault("category", ErrorCategory.RATE_LIMIT)
        kwargs.setdefault("severity", ErrorSeverity.LOW)
        kwargs.setdefault("recoverable", True)
        kwargs["retry_after"] = retry_after
        super().__init__(f"Rate limit exceeded, retry after {retry_after} seconds", **kwargs)


class ErrorHandler:
    """
    Centralized error handling with logging, user notifications, and recovery
    """

    def __init__(self):
        self.error_counts = {}
        self.circuit_breakers = {}

    async def handle_error(
        self,
        error: Exception,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentError:
        """
        Handle any error with comprehensive logging and user notification
        """
        try:
            # Convert to AgentError if needed
            if isinstance(error, AgentError):
                agent_error = error
            else:
                agent_error = self._convert_to_agent_error(error, context)

            # Add additional context
            if context:
                agent_error.context.update(context)
            agent_error.context.update({
                "user_id": user_id,
                "task_id": task_id,
                "conversation_id": conversation_id
            })

            # Log error appropriately
            await self._log_error(agent_error)

            # Update error tracking
            self._track_error(agent_error)

            # Notify user if needed
            if user_id:
                await self._notify_user(user_id, agent_error, task_id, conversation_id)

            # Update task status if task_id provided
            if task_id:
                await self._update_task_status(task_id, agent_error)

            return agent_error

        except Exception as e:
            # Fallback error handling
            logger.critical(f"Error handler itself failed: {e}")
            fallback_error = AgentError(
                "Critical system error occurred",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                recoverable=False
            )
            return fallback_error

    def _convert_to_agent_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> AgentError:
        """Convert standard exception to AgentError"""
        error_type = type(error).__name__
        error_message = str(error)

        # Map common error types to categories
        category_mapping = {
            "ConnectionError": ErrorCategory.NETWORK,
            "TimeoutError": ErrorCategory.NETWORK,
            "ValidationError": ErrorCategory.VALIDATION,
            "PermissionError": ErrorCategory.PERMISSION,
            "FileNotFoundError": ErrorCategory.SYSTEM,
            "KeyError": ErrorCategory.SYSTEM,
            "ValueError": ErrorCategory.VALIDATION,
            "TypeError": ErrorCategory.SYSTEM
        }

        category = category_mapping.get(error_type, ErrorCategory.SYSTEM)

        # Determine severity
        severity = ErrorSeverity.HIGH if "critical" in error_message.lower() else ErrorSeverity.MEDIUM

        return AgentError(
            message=f"{error_type}: {error_message}",
            category=category,
            severity=severity,
            context=context,
            original_error=error
        )

    async def _log_error(self, error: AgentError) -> None:
        """Log error with appropriate level"""
        log_data = {
            "error_data": error.to_dict(),
            "traceback": traceback.format_exc() if error.original_error else None
        }

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {error.message}", extra=log_data)

    def _track_error(self, error: AgentError) -> None:
        """Track error frequency for circuit breaking"""
        error_key = f"{error.category}:{error.context.get('user_id', 'unknown')}"
        current_count = self.error_counts.get(error_key, 0)
        self.error_counts[error_key] = current_count + 1

        # Simple circuit breaker logic
        if current_count > 10:  # Threshold
            self.circuit_breakers[error_key] = datetime.utcnow()
            logger.warning(f"Circuit breaker activated for {error_key}")

    async def _notify_user(
        self,
        user_id: str,
        error: AgentError,
        task_id: Optional[str],
        conversation_id: Optional[str]
    ) -> None:
        """Notify user of error via WebSocket"""
        try:
            error_notification = {
                "type": "error",
                "message": error.user_message,
                "severity": error.severity.value,
                "recoverable": error.recoverable,
                "retry_after": error.retry_after,
                "task_id": task_id,
                "conversation_id": conversation_id,
                "timestamp": error.timestamp.isoformat()
            }

            await websocket_manager.emit_to_user(user_id, "agent_error", error_notification)

        except Exception as e:
            logger.error(f"Failed to notify user of error: {e}")

    async def _update_task_status(self, task_id: str, error: AgentError) -> None:
        """Update task status to reflect error"""
        try:
            from .agent_task_manager import get_agent_task_manager

            task_manager = get_agent_task_manager()
            await task_manager.fail_task(
                task_id=task_id,
                error_message=error.user_message,
                error_details=error.to_dict()
            )

        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

    def should_retry(self, error: AgentError, attempt: int = 1) -> bool:
        """Determine if operation should be retried"""
        if not error.recoverable:
            return False

        if attempt >= 3:  # Max retries
            return False

        # Check circuit breaker
        error_key = f"{error.category}:{error.context.get('user_id', 'unknown')}"
        if error_key in self.circuit_breakers:
            circuit_time = self.circuit_breakers[error_key]
            if (datetime.utcnow() - circuit_time).seconds < 300:  # 5 minute circuit
                return False

        return True

    async def create_user_friendly_response(
        self,
        error: AgentError,
        include_suggestions: bool = True
    ) -> Dict[str, Any]:
        """Create user-friendly error response"""
        response = {
            "success": False,
            "error": {
                "message": error.user_message,
                "severity": error.severity.value,
                "recoverable": error.recoverable
            }
        }

        if error.retry_after:
            response["error"]["retry_after"] = error.retry_after

        if include_suggestions:
            suggestions = self._get_error_suggestions(error)
            if suggestions:
                response["error"]["suggestions"] = suggestions

        return response

    def _get_error_suggestions(self, error: AgentError) -> List[str]:
        """Get helpful suggestions based on error type"""
        suggestions = {
            ErrorCategory.USER_INPUT: [
                "Check your input for typos or formatting issues",
                "Try rephrasing your request",
                "Make sure all required information is provided"
            ],
            ErrorCategory.LLM: [
                "Try rephrasing your request in simpler terms",
                "Break complex requests into smaller parts",
                "Try again in a few moments"
            ],
            ErrorCategory.EXTERNAL_API: [
                "Check your internet connection",
                "Try again in a few minutes",
                "Contact support if the issue persists"
            ],
            ErrorCategory.RATE_LIMIT: [
                "Wait a moment before making another request",
                "Try combining multiple actions into one request"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Try logging out and logging back in",
                "Check if your session has expired",
                "Contact support if login issues persist"
            ]
        }

        return suggestions.get(error.category, [
            "Try again in a few moments",
            "Contact support if the issue persists"
        ])


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get global ErrorHandler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Decorator for error handling
def handle_errors(
    user_id_key: str = "user_id",
    task_id_key: str = "task_id",
    conversation_id_key: str = "conversation_id"
):
    """Decorator to automatically handle errors in agent functions"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as error:
                error_handler = get_error_handler()

                # Extract context from kwargs
                context = {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }

                user_id = kwargs.get(user_id_key)
                task_id = kwargs.get(task_id_key)
                conversation_id = kwargs.get(conversation_id_key)

                # Handle the error
                agent_error = await error_handler.handle_error(
                    error=error,
                    user_id=user_id,
                    task_id=task_id,
                    conversation_id=conversation_id,
                    context=context
                )

                # Re-raise as AgentError for proper handling upstream
                raise agent_error

        return wrapper

    return decorator