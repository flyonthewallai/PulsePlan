import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')

class StructuredLogger:
    """Structured logger with JSON output and correlation IDs"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.service_name = "pulseplan-fastapi"
    
    def _create_log_entry(
        self, 
        level: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create structured log entry with correlation IDs"""
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "service": self.service_name,
            "logger": self.logger.name,
        }
        
        # Add correlation IDs
        req_id = request_id or request_id_var.get()
        if req_id:
            entry["request_id"] = req_id
        
        usr_id = user_id or user_id_var.get()
        if usr_id:
            entry["user_id"] = usr_id
        
        # Add context data
        if context:
            entry["context"] = self._sanitize_log_data(context)
        
        return entry
    
    def _sanitize_log_data(self, data: Any) -> Any:
        """Remove sensitive information from logs"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = [
                'password', 'token', 'secret', 'key', 'credential', 
                'access_token', 'refresh_token', 'authorization'
            ]
            
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_log_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_log_data(item) for item in data]
        return data
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        entry = self._create_log_entry("INFO", message, context, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def error(self, message: str, exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        entry = self._create_log_entry("ERROR", message, context, **kwargs)
        
        if exception:
            entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }
        
        self.logger.error(json.dumps(entry))
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        entry = self._create_log_entry("WARNING", message, context, **kwargs)
        self.logger.warning(json.dumps(entry))
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        entry = self._create_log_entry("DEBUG", message, context, **kwargs)
        self.logger.debug(json.dumps(entry))


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request IDs and user context to logs"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # Set request ID in context
        request_id_var.set(request_id)
        
        # Set user ID in context if available from auth middleware
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            user_id_var.set(user_id)
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["x-request-id"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = StructuredLogger("http")
        self.skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        start_time = datetime.utcnow()
        
        # Log request
        request_context = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": self._get_client_ip(request)
        }
        
        self.logger.info("HTTP request started", context=request_context)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log response
            response_context = {
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "response_size": response.headers.get("content-length")
            }
            
            log_level = "error" if response.status_code >= 500 else "warning" if response.status_code >= 400 else "info"
            
            if log_level == "error":
                self.logger.error("HTTP request completed with error", context=response_context)
            elif log_level == "warning":
                self.logger.warning("HTTP request completed with warning", context=response_context)
            else:
                self.logger.info("HTTP request completed successfully", context=response_context)
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            error_context = {
                "duration_ms": round(duration_ms, 2),
                "error_type": type(e).__name__
            }
            
            self.logger.error("HTTP request failed", exception=e, context=error_context)
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


def setup_logging():
    """Setup structured JSON logging"""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # JSON will be the message content
        handlers=[logging.StreamHandler()]
    )
    
    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)