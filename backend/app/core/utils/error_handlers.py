"""
Shared Error Handlers
Standardized error handling utilities for API endpoints and services
"""
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def handle_endpoint_error(
    error: Exception,
    log: logging.Logger,
    operation: str,
    status_code: int = 500,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Standardized error handler for API endpoints

    Args:
        error: The exception that occurred
        log: Logger instance for logging
        operation: Name of the operation that failed
        status_code: HTTP status code to return
        include_details: Whether to include error details in response (development only)

    Returns:
        Error response dictionary

    Raises:
        HTTPException: With appropriate status code and message
    """
    # If it's already an HTTPException, re-raise it
    if isinstance(error, HTTPException):
        raise error

    # Log the error with full traceback
    log.error(f"Error in {operation}: {str(error)}", exc_info=True)

    # Prepare error response
    error_message = f"Operation '{operation}' failed"

    # In development, include more details
    if include_details:
        error_message = f"{error_message}: {str(error)}"

    # Raise HTTPException with sanitized message
    raise HTTPException(
        status_code=status_code,
        detail=error_message
    )


def handle_service_error(
    error: Exception,
    log: logging.Logger,
    operation: str,
    default_message: str = "Service operation failed"
) -> None:
    """
    Standardized error handler for service layer

    Args:
        error: The exception that occurred
        log: Logger instance for logging
        operation: Name of the operation that failed
        default_message: Default error message

    Raises:
        Exception: Re-raises the original exception after logging
    """
    # Log the error with full context
    log.error(
        f"Service error in {operation}: {str(error)}",
        exc_info=True,
        extra={"operation": operation}
    )

    # Re-raise the exception for upper layers to handle
    raise


class ServiceError(Exception):
    """Base exception for service layer errors"""

    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.operation = operation
        self.details = details or {}
        super().__init__(f"{operation}: {message}")


class RepositoryError(Exception):
    """Base exception for repository layer errors"""

    def __init__(self, message: str, table: str, operation: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.table = table
        self.operation = operation
        self.details = details or {}
        super().__init__(f"{operation} on {table}: {message}")


def safe_execute(func):
    """
    Decorator for safe execution with error logging

    Usage:
        @safe_execute
        async def my_function():
            ...
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper
