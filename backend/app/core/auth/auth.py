from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config.core.settings import settings
from app.config.database.supabase import get_supabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class CurrentUser:
    def __init__(self, user_id: str, email: Optional[str] = None, is_admin: bool = False):
        self.user_id = user_id
        self.email = email
        self.is_admin = is_admin

def verify_supabase_token(token: str) -> dict:
    """
    Verify JWT token using Supabase client
    """
    try:
        supabase = get_supabase()
        
        # Use Supabase to verify the JWT token
        response = supabase.auth.get_user(jwt=token)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - no user found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = response.user
        
        # Return payload in expected format
        return {
            "sub": user.id,
            "email": user.email,
            "role": user.role if hasattr(user, 'role') else "authenticated"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Extract current user from token using Supabase authentication
    """
    try:
        payload = verify_supabase_token(credentials.credentials)
        
        # Extract user info from payload
        user_id = payload.get("sub")
        email = payload.get("email")
                
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload - missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check for admin role (can be extended later)
        is_admin = payload.get("role") == "admin"
        
        current_user = CurrentUser(
            user_id=user_id,
            email=email,
            is_admin=is_admin
        )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Log detailed error for debugging, but return generic message to client
        # to prevent information disclosure
        logger.error(f"Authentication failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require admin role"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def check_user_access(resource_user_id: str, current_user: CurrentUser):
    """Check if user can access resource (owns it or is admin)"""
    if resource_user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - you can only access your own data"
        )