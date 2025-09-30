"""
OAuth Authentication Endpoints
Handles OAuth flows for Google and Microsoft account connections
"""
import secrets
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx

from app.core.auth import get_current_user, CurrentUser
from app.config.core.settings import get_settings
from app.config.cache.redis_client import get_redis_client
from app.services.auth.oauth import GoogleOAuthService, MicrosoftOAuthService


logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


class OAuthInitiateResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    success: bool
    provider: str
    user_email: Optional[str] = None
    scopes: Optional[list] = None
    message: str


class OAuthConnectionStatus(BaseModel):
    provider: str
    connected: bool
    user_email: Optional[str] = None
    expires_at: Optional[str] = None
    last_refreshed: Optional[str] = None
    scopes: Optional[list] = None


@router.get("/google/authorize", response_model=OAuthInitiateResponse)
async def initiate_google_oauth(
    userId: str = None,  # Accept userId as query parameter for unauthenticated flow
    service: str = "calendar"  # Service-specific scopes: calendar, gmail, contacts
):
    """
    Initiate Google OAuth flow
    Returns authorization URL for user to visit
    """
    try:
        # Validate userId parameter
        if not userId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="userId parameter is required"
            )
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in Redis with user association
        redis_client = get_redis_client()
        
        # Ensure Redis client is initialized
        if not redis_client.client:
            await redis_client.initialize()
        
        await redis_client.set(
            f"oauth_state:{state}",
            f"{userId}:google",
            ex=600  # Expire in 10 minutes
        )
        
        # Define service-specific scopes (single service per OAuth flow)
        scope_sets = {
            "calendar": "openid email profile https://www.googleapis.com/auth/calendar",
            "gmail": "openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly", 
            "contacts": "openid email profile https://www.googleapis.com/auth/contacts.readonly"
        }
        
        selected_scope = scope_sets.get(service, scope_sets["calendar"])
        
        # Build authorization URL
        auth_params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URL,
            "scope": selected_scope,
            "response_type": "code",
            "state": f"{state}:{service}",  # Include service in state for callback handling
            "access_type": "offline",
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        authorization_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"
        
        logger.info(f"Initiated Google OAuth for user {userId}")
        
        return OAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Google OAuth: {str(e)}"
        )


@router.get("/microsoft/authorize", response_model=OAuthInitiateResponse)
async def initiate_microsoft_oauth(
    userId: str = None,  # Accept userId as query parameter for unauthenticated flow
    service: str = "calendar"  # Service-specific scopes: calendar, outlook, contacts
):
    """
    Initiate Microsoft OAuth flow
    Returns authorization URL for user to visit
    """
    try:
        # Validate userId parameter
        if not userId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="userId parameter is required"
            )
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in Redis with user association
        redis_client = get_redis_client()
        
        # Ensure Redis client is initialized
        if not redis_client.client:
            await redis_client.initialize()
        
        await redis_client.set(
            f"oauth_state:{state}",
            f"{userId}:microsoft",
            ex=600  # Expire in 10 minutes
        )
        
        # Define service-specific scopes for Microsoft
        scope_sets = {
            "calendar": "openid email profile https://graph.microsoft.com/calendars.readwrite",
            "outlook": "openid email profile https://graph.microsoft.com/mail.send https://graph.microsoft.com/mail.read", 
            "contacts": "openid email profile https://graph.microsoft.com/people.read"
        }
        
        selected_scope = scope_sets.get(service, scope_sets["calendar"])
        
        # Build authorization URL
        auth_params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URL,
            "scope": selected_scope,
            "response_type": "code",
            "state": f"{state}:{service}",  # Include service in state for callback handling
            "response_mode": "query"
        }
        
        authorization_url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(auth_params)}"
        
        logger.info(f"Initiated Microsoft OAuth for user {userId}")
        
        return OAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error initiating Microsoft OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Microsoft OAuth: {str(e)}"
        )


@router.get("/google/callback")
async def handle_google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Handle Google OAuth callback
    """
    if error:
        logger.warning(f"Google OAuth error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter"
        )
    
    try:
        # Verify state parameter
        redis_client = get_redis_client()
        
        # Ensure Redis client is initialized
        if not redis_client.client:
            await redis_client.initialize()
        
        state_data = await redis_client.get(f"oauth_state:{state}")
        
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )
        
        user_id, provider = state_data.split(":", 1)
        
        if provider != "google":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State parameter provider mismatch"
            )
        
        # Exchange code for tokens
        oauth_service = GoogleOAuthService()
        token_data = await oauth_service.exchange_code_for_tokens(code)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for tokens"
            )
        
        # Get user info
        user_info = await oauth_service.get_user_info(token_data["access_token"])
        
        # Store tokens securely using token service
        from app.services.token_service import get_token_service
        from app.models.oauth_tokens import OAuthTokenCreate
        
        token_service = get_token_service()
        
        # Create connection data for secure storage
        from app.models.oauth_tokens import Provider
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        connection_data = OAuthTokenCreate(
            provider=Provider.GOOGLE,  
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scopes=token_data.get("scope", "").split() if token_data.get("scope") else [],
            email=user_info.get("email")  # Re-enabled after adding email column
        )
        
        try:
            # Store encrypted tokens via secure token service
            connection_id = await token_service.store_user_tokens(
                user_id=user_id,
                provider="google",
                tokens=connection_data
            )
            
            # Clean up state
            await redis_client.delete(f"oauth_state:{state}")
            
            logger.info(f"Successfully stored encrypted Google OAuth tokens for user {user_id} (connection_id: {connection_id})")
            
            # Redirect to frontend success page
            redirect_url = f"{settings.CLIENT_URL}/oauth/success?provider=google&email={user_info.get('email', '')}"
            return RedirectResponse(url=redirect_url)
            
        except Exception as e:
            logger.error(f"Failed to store Google OAuth tokens: {str(e)}")
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Google OAuth callback: {str(e)}")
        # Redirect to frontend error page
        redirect_url = f"{settings.CLIENT_URL}/oauth/error?provider=google&error={str(e)}"
        return RedirectResponse(url=redirect_url)


@router.get("/microsoft/callback")
async def handle_microsoft_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    Handle Microsoft OAuth callback
    """
    if error:
        logger.warning(f"Microsoft OAuth error: {error} - {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error_description or error}"
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter"
        )
    
    try:
        # Verify state parameter
        redis_client = get_redis_client()
        
        # Ensure Redis client is initialized
        if not redis_client.client:
            await redis_client.initialize()
        
        state_data = await redis_client.get(f"oauth_state:{state}")
        
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )
        
        user_id, provider = state_data.split(":", 1)
        
        if provider != "microsoft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State parameter provider mismatch"
            )
        
        # Exchange code for tokens
        oauth_service = MicrosoftOAuthService()
        token_data = await oauth_service.exchange_code_for_tokens(code)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for tokens"
            )
        
        # Get user info
        user_info = await oauth_service.get_user_info(token_data["access_token"])
        
        # Store tokens securely using token service
        from app.services.token_service import get_token_service
        from app.models.oauth_tokens import OAuthTokenCreate
        
        token_service = get_token_service()
        
        # Create connection data for secure storage
        from app.models.oauth_tokens import Provider
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        connection_data = OAuthTokenCreate(
            provider=Provider.MICROSOFT,  
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scopes=token_data.get("scope", "").split() if token_data.get("scope") else [],
            email=user_info.get('mail', user_info.get('userPrincipalName'))  # Re-enabled after adding email column
        )
        
        try:
            # Store encrypted tokens via secure token service
            connection_id = await token_service.store_user_tokens(
                user_id=user_id,
                provider="microsoft",
                tokens=connection_data
            )
            
            # Clean up state
            await redis_client.delete(f"oauth_state:{state}")
            
            logger.info(f"Successfully stored encrypted Microsoft OAuth tokens for user {user_id} (connection_id: {connection_id})")
            
            # Redirect to frontend success page
            redirect_url = f"{settings.CLIENT_URL}/oauth/success?provider=microsoft&email={user_info.get('mail', user_info.get('userPrincipalName', ''))}"
            return RedirectResponse(url=redirect_url)
            
        except Exception as e:
            logger.error(f"Failed to store Microsoft OAuth tokens: {str(e)}")
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Microsoft OAuth callback: {str(e)}")
        # Redirect to frontend error page
        redirect_url = f"{settings.CLIENT_URL}/oauth/error?provider=microsoft&error={str(e)}"
        return RedirectResponse(url=redirect_url)


@router.get("/connections", response_model=list[OAuthConnectionStatus])
async def get_oauth_connections(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get all OAuth connections for the current user via secure token service
    """
    try:
        from app.services.token_service import get_token_service
        
        token_service = get_token_service()
        
        # Get connection status using secure token service
        connection_status = await token_service.get_user_connection_status(current_user.user_id)
        connections = []
        
        # Add Google connection status
        if connection_status.google:
            connections.append(OAuthConnectionStatus(
                provider="google",
                connected=True,
                scopes=["gmail.send", "gmail.readonly", "calendar", "contacts.readonly"]
            ))
        else:
            connections.append(OAuthConnectionStatus(
                provider="google", 
                connected=False
            ))
        
        # Add Microsoft connection status
        if connection_status.microsoft:
            connections.append(OAuthConnectionStatus(
                provider="microsoft",
                connected=True,
                scopes=["mail.send", "mail.read", "calendars.readwrite"]
            ))
        else:
            connections.append(OAuthConnectionStatus(
                provider="microsoft",
                connected=False
            ))
        
        return connections
        
    except Exception as e:
        logger.error(f"Error getting OAuth connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get OAuth connections: {str(e)}"
        )


@router.delete("/connections/{provider}")
async def disconnect_oauth_provider(
    provider: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Disconnect OAuth provider for the current user via secure token service
    """
    if provider not in ["google", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'microsoft'"
        )
    
    try:
        from app.services.token_service import get_token_service
        
        token_service = get_token_service()
        
        # Remove tokens using secure token service
        success = await token_service.remove_user_tokens(current_user.user_id, provider)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active {provider} connection found"
            )
        
        logger.info(f"Disconnected {provider} OAuth for user {current_user.user_id}")
        
        return {
            "message": f"Successfully disconnected {provider}",
            "provider": provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting OAuth provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect {provider}: {str(e)}"
        )
