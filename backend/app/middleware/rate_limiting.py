"""
Rate limiting middleware for FastAPI
Uses hierarchical rate limiting service
"""
from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import jwt
import logging

from app.config.settings import settings
from app.services.rate_limiting import hierarchical_rate_limiter


logger = logging.getLogger(__name__)


class HierarchicalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware using hierarchical rate limiter
    Supports user, provider, workflow, and global level rate limits
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.enabled = settings.ENABLE_RATE_LIMITING
        self.rate_limiter = hierarchical_rate_limiter
        
        # Exempted paths that don't count towards rate limits
        self.exempt_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/health",
            "/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        if not self.enabled or self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        try:
            # Extract user information from request
            user_id = await self._get_user_id(request)
            provider = self._extract_provider(request)
            workflow_type = self._extract_workflow_type(request)
            
            # Skip rate limiting for unauthenticated requests (let auth middleware handle)
            if not user_id:
                return await call_next(request)
            
            # Check all applicable rate limits
            rate_limit_status = await self.rate_limiter.check_rate_limits(
                user_id=user_id,
                provider=provider,
                workflow_type=workflow_type
            )
            
            # If rate limit exceeded, return 429 error
            if not rate_limit_status.allowed:
                violation = rate_limit_status.violations[0]  # Get first violation
                
                retry_after = int(violation.reset_time.timestamp() - violation.violation_time.timestamp())
                
                logger.warning(f"Rate limit exceeded for user {user_id}: {violation.level.value} level")
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"{violation.level.value} level rate limit exceeded",
                        "level": violation.level.value,
                        "limit": violation.limit,
                        "current": violation.current_count,
                        "reset_time": violation.reset_time.isoformat()
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Level": violation.level.value,
                        "X-RateLimit-Limit": str(violation.limit),
                        "X-RateLimit-Remaining": str(max(0, violation.limit - violation.current_count)),
                        "X-RateLimit-Reset": str(int(violation.reset_time.timestamp()))
                    }
                )
            
            # Process the request
            response = await call_next(request)
            
            # Record successful request for rate limiting
            await self.rate_limiter.record_request(
                user_id=user_id,
                provider=provider,
                workflow_type=workflow_type
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limiting middleware: {str(e)}")
            # On error, allow request to proceed (fail open)
            return await call_next(request)
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from rate limiting"""
        return any(path.startswith(exempt_path) for exempt_path in self.exempt_paths)
    
    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token"""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None
            
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != "bearer":
                return None
            
            # Decode JWT token to get user ID
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False}  # Simplified - proper verification should be done elsewhere
            )
            
            return payload.get("sub") or payload.get("user_id")
            
        except Exception:
            return None
    
    def _extract_provider(self, request: Request) -> Optional[str]:
        """Extract provider from request path or body"""
        path = request.url.path.lower()
        
        # Check if path indicates specific provider
        if "google" in path or "gmail" in path:
            return "google"
        elif "microsoft" in path or "outlook" in path:
            return "microsoft"
        
        # Could also check request body or query params for provider
        return None
    
    def _extract_workflow_type(self, request: Request) -> Optional[str]:
        """Extract workflow type from request path"""
        path = request.url.path
        
        if "/agents/calendar" in path:
            return "calendar"
        elif "/agents/tasks" in path:
            return "task"
        elif "/agents/briefing" in path:
            return "briefing"
        elif "/agents/scheduling" in path:
            return "scheduling"
        elif "/agents/natural-language" in path:
            return "chat"
        
        return None


# Legacy simple rate limiter for backwards compatibility
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware using Redis sliding window
    Kept for backwards compatibility
    """
    
    def __init__(self, app, limit: int = None, window: int = 60):
        super().__init__(app)
        self.limit = limit or settings.USER_RATE_LIMIT
        self.window = window
        self.exempt_paths = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        
        if not user_id:
            # No user context - use IP address for rate limiting
            user_id = self._get_client_ip(request)
        
        if user_id:
            try:
                from app.config.redis import redis_client
                
                # Check rate limit
                allowed = await redis_client.check_rate_limit(
                    user_id, 
                    limit=self.limit, 
                    window=self.window
                )
                
                if not allowed:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "message": f"Maximum {self.limit} requests per {self.window} seconds"
                        },
                        headers={
                            "Retry-After": str(self.window),
                            "X-RateLimit-Limit": str(self.limit),
                            "X-RateLimit-Window": str(self.window)
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Fail open on Redis errors
                pass
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        if user_id:
            try:
                # Get current usage (approximate)
                remaining = max(0, self.limit - 1)  # Simplified calculation
                response.headers["X-RateLimit-Limit"] = str(self.limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Window"] = str(self.window)
            except Exception:
                pass
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


def setup_rate_limiting(app):
    """Setup hierarchical rate limiting middleware"""
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(HierarchicalRateLimitMiddleware)
        logger.info("Hierarchical rate limiting middleware enabled")
    else:
        logger.info("Rate limiting disabled")