from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.auth import verify_supabase_token
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for FastAPI (matching Node.js authenticate pattern)
    Automatically adds user context to requests when valid JWT is present
    """
    
    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/auth"  # Auth endpoints don't require existing auth
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            # For routes that require auth, this will be handled by FastAPI dependencies
            # This middleware just adds user context when available
            return await call_next(request)
        
        try:
            # Extract token
            token = auth_header.split(" ")[1]
            payload = verify_supabase_token(token)
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.is_admin = payload.get("role") == "admin"
            request.state.authenticated = True
            
        except HTTPException:
            # Invalid token - continue without user context
            request.state.authenticated = False
            pass
        except Exception as e:
            logger.error(f"Error in auth middleware: {e}")
            request.state.authenticated = False
        
        response = await call_next(request)
        return response


class RequireAuthMiddleware(BaseHTTPMiddleware):
    """
    Strict authentication middleware that blocks unauthenticated requests
    Similar to Node.js authenticate middleware behavior
    """
    
    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/auth"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content='{"error": "Missing or invalid Authorization header"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        try:
            # Extract and verify token
            token = auth_header.split(" ")[1]
            payload = verify_supabase_token(token)
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.is_admin = payload.get("role") == "admin"
            request.state.authenticated = True
            
        except HTTPException as e:
            return Response(
                content=f'{{"error": "{e.detail}"}}',
                status_code=e.status_code,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"Error in require auth middleware: {e}")
            return Response(
                content='{"error": "Authentication failed"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        response = await call_next(request)
        return response


# FastAPI dependency models
class CurrentUser(BaseModel):
    user_id: str
    email: str
    is_admin: bool = False


async def get_current_user(request: Request) -> CurrentUser:
    """
    FastAPI dependency to get current user from request state
    """
    if not getattr(request.state, 'authenticated', False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return CurrentUser(
        user_id=request.state.user_id,
        email=request.state.user_email,
        is_admin=getattr(request.state, 'is_admin', False)
    )