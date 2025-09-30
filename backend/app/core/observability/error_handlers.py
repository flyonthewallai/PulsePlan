"""
Global Error Handlers
Comprehensive error handling with structured logging and user-friendly responses
"""
import traceback
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
import uuid

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from ..infrastructure.circuit_breaker import CircuitBreakerError
from ...database.repository import DatabaseError

logger = logging.getLogger(__name__)


class PulsePlanError(Exception):
    """Base exception for PulsePlan application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        user_message: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        self.user_message = user_message or message
        super().__init__(message)


class WorkflowError(PulsePlanError):
    """Workflow execution errors"""
    def __init__(self, message: str, workflow_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            details={**(details or {}), "workflow_type": workflow_type},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            user_message="There was an issue processing your request. Please try again."
        )


class AuthenticationError(PulsePlanError):
    """Authentication related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR", 
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_message="Authentication required. Please log in and try again."
        )


class AuthorizationError(PulsePlanError):
    """Authorization related errors"""
    def __init__(self, message: str, required_permission: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details={"required_permission": required_permission} if required_permission else {},
            status_code=status.HTTP_403_FORBIDDEN,
            user_message="You don't have permission to access this resource."
        )


class RateLimitError(PulsePlanError):
    """Rate limiting errors"""
    def __init__(self, message: str, retry_after: int, limit_info: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={**(limit_info or {}), "retry_after": retry_after},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            user_message=f"Too many requests. Please try again in {retry_after} seconds."
        )


class ExternalServiceError(PulsePlanError):
    """External service integration errors"""
    def __init__(self, service_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={**(details or {}), "service": service_name},
            status_code=status.HTTP_502_BAD_GATEWAY,
            user_message=f"There's an issue with {service_name}. Please try again later."
        )


class ValidationError(PulsePlanError):
    """Data validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={**(details or {}), "field": field} if field else details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            user_message="Please check your input and try again."
        )


def generate_error_id() -> str:
    """Generate unique error ID for tracking"""
    return str(uuid.uuid4())[:8]


def format_error_response(
    error_id: str,
    error_code: str,
    message: str,
    user_message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> Dict[str, Any]:
    """Format standardized error response"""
    response = {
        "error": {
            "id": error_id,
            "code": error_code,
            "message": user_message,  # User-facing message
            "timestamp": datetime.utcnow().isoformat(),
            "status": status_code
        }
    }
    
    # Add details in development/debug mode
    from ..config.settings import get_settings
    settings = get_settings()
    
    if settings.DEBUG or settings.is_development():
        response["error"]["debug"] = {
            "internal_message": message,
            "details": details or {},
        }
        
        if request:
            response["error"]["debug"]["request"] = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
            }
    
    return response


async def log_error(
    error: Exception,
    error_id: str,
    request: Optional[Request] = None,
    extra_context: Optional[Dict[str, Any]] = None
):
    """Log error with structured information"""
    context = {
        "error_id": error_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        **(extra_context or {})
    }
    
    if request:
        context.update({
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "user_id": getattr(request.state, "user_id", None)
        })
    
    # Add stack trace for unexpected errors
    if not isinstance(error, (PulsePlanError, HTTPException, RequestValidationError)):
        context["traceback"] = traceback.format_exc()
        logger.error(f"Unexpected error {error_id}: {str(error)}", extra=context)
    else:
        logger.warning(f"Application error {error_id}: {str(error)}", extra=context)


# FastAPI Exception Handlers

async def pulseplan_error_handler(request: Request, exc: PulsePlanError) -> JSONResponse:
    """Handle PulsePlan application errors"""
    error_id = generate_error_id()
    
    await log_error(exc, error_id, request)
    
    response_data = format_error_response(
        error_id=error_id,
        error_code=exc.error_code,
        message=exc.message,
        user_message=exc.user_message,
        status_code=exc.status_code,
        details=exc.details,
        request=request
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def circuit_breaker_error_handler(request: Request, exc: CircuitBreakerError) -> JSONResponse:
    """Handle circuitBreaker errors"""
    error_id = generate_error_id()
    
    await log_error(exc, error_id, request, {
        "service_name": exc.service_name,
        "circuit_stats": exc.stats.__dict__
    })
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="CIRCUIT_BREAKER_OPEN",
        message=str(exc),
        user_message="Service temporarily unavailable. Please try again later.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        details={"service": exc.service_name},
        request=request
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response_data,
        headers={"Retry-After": "60"}
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors"""
    error_id = generate_error_id()
    
    await log_error(exc, error_id, request, {
        "operation": exc.operation,
        "table": exc.table,
        "details": exc.details
    })
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="DATABASE_ERROR",
        message=exc.message,
        user_message="There was an issue saving your data. Please try again.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"operation": exc.operation, "table": exc.table},
        request=request
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    error_id = generate_error_id()
    
    await log_error(exc, error_id, request)
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="HTTP_ERROR",
        message=exc.detail,
        user_message=exc.detail,
        status_code=exc.status_code,
        request=request
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=getattr(exc, "headers", None)
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette HTTP exceptions"""
    error_id = generate_error_id()
    
    await log_error(exc, error_id, request)
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="HTTP_ERROR",
        message=exc.detail,
        user_message=exc.detail,
        status_code=exc.status_code,
        request=request
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    error_id = generate_error_id()
    
    # Enhanced logging for debugging
    logger.error(f"Request validation error {error_id}: {exc.errors()}")
    logger.error(f"Request body: {await request.body()}")
    logger.error(f"Request headers: {dict(request.headers)}")
    
    await log_error(exc, error_id, request, {"validation_errors": exc.errors()})
    
    # Extract field-specific errors
    field_errors = {}
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        field_errors[field_path] = error["msg"]
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        user_message="Please check your input data and try again.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"field_errors": field_errors},
        request=request
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    error_id = generate_error_id()
    
    await log_error(exc, error_id, request, {"validation_errors": exc.errors()})
    
    # Extract field-specific errors
    field_errors = {}
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        field_errors[field_path] = error["msg"]
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="VALIDATION_ERROR",
        message="Data validation failed",
        user_message="Please check your input data and try again.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"field_errors": field_errors},
        request=request
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    error_id = generate_error_id()
    
    # Enhanced logging for debugging parsing errors
    if "parsing" in str(exc).lower() or "body" in str(exc).lower():
        logger.error(f"Parsing error {error_id}: {str(exc)}")
        try:
            body = await request.body()
            logger.error(f"Request body: {body}")
        except Exception as body_error:
            logger.error(f"Could not read request body: {body_error}")
        logger.error(f"Request headers: {dict(request.headers)}")
        logger.error(f"Request method: {request.method}")
        logger.error(f"Request URL: {request.url}")
    
    await log_error(exc, error_id, request)
    
    response_data = format_error_response(
        error_id=error_id,
        error_code="INTERNAL_ERROR",
        message=str(exc),
        user_message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request=request
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def setup_error_handlers(app):
    """Setup all error handlers for the FastAPI app"""
    
    # Custom application errors
    app.add_exception_handler(PulsePlanError, pulseplan_error_handler)
    app.add_exception_handler(CircuitBreakerError, circuit_breaker_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    
    # FastAPI/Starlette errors
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_error_handler)
    
    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Global error handlers configured")