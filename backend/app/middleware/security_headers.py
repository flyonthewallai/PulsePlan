"""
Security Headers Middleware
Adds security headers to all HTTP responses
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import logging

from app.core.auth.security import get_security_headers

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    async def dispatch(self, request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Get security headers configuration
        security_headers = get_security_headers()
        
        # Add security headers to response
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        return response

