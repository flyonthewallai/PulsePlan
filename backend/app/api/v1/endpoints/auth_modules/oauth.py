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
    service: str  # NEW: service type (calendar, gmail, contacts, etc.)
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
        redis_client = await get_redis_client()

        # Ensure Redis client is initialized
        if not redis_client._client:
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
            # NOTE: include_granted_scopes removed - each service gets separate token
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
        redis_client = await get_redis_client()

        # Ensure Redis client is initialized
        if not redis_client._client:
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
        redis_client = await get_redis_client()

        # Ensure Redis client is initialized
        if not redis_client._client:
            await redis_client.initialize()
        
        # Extract base state and service (format: "token:service")
        state_parts = state.split(":")
        base_state = state_parts[0]
        service_type = state_parts[1] if len(state_parts) > 1 else "default"

        state_data = await redis_client.get(f"oauth_state:{base_state}")

        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )

        # Decode if bytes (Redis sometimes returns bytes even with decode_responses=True)
        if isinstance(state_data, bytes):
            state_data = state_data.decode('utf-8')

        user_id, provider = state_data.split(":", 1)

        logger.info(f"OAuth callback for user {user_id}, provider {provider}, service {service_type}")

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
        from app.services.auth.token_service import get_token_service
        from app.models.auth.oauth_tokens import OAuthTokenCreate
        
        token_service = get_token_service()
        
        # Create connection data for secure storage
        from app.models.auth.oauth_tokens import Provider
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        connection_data = OAuthTokenCreate(
            provider=Provider.GOOGLE,
            service_type=service_type,  # Add service type
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scopes=token_data.get("scope", "").split() if token_data.get("scope") else [],
            email=user_info.get("email")  # Re-enabled after adding email column
        )
        
        try:
            # Store encrypted tokens via secure token service with service type
            connection_id = await token_service.store_user_tokens(
                user_id=user_id,
                provider="google",
                service_type=service_type,  # Pass extracted service type
                tokens=connection_data
            )

            # Clean up state
            await redis_client.delete(f"oauth_state:{base_state}")

            logger.info(f"Successfully stored encrypted Google OAuth tokens for user {user_id} (connection_id: {connection_id})")

            # Emit WebSocket event to notify frontend immediately
            try:
                from app.core.infrastructure.websocket import websocket_manager
                await websocket_manager.emit_to_user(user_id, 'oauth_connected', {
                    'provider': 'google',
                    'service': service_type,
                    'email': user_info.get('email'),
                    'connected': True,
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.info(f"Emitted oauth_connected WebSocket event for user {user_id}")
            except Exception as ws_error:
                logger.error(f"Failed to emit WebSocket event: {str(ws_error)}")
                # Don't fail OAuth flow if WebSocket fails

            # Trigger calendar discovery if calendar scopes are present
            scopes = connection_data.scopes or []
            if any("calendar" in scope for scope in scopes):
                try:
                    from app.jobs.calendar.calendar_sync_worker import CalendarSyncWorker

                    worker = CalendarSyncWorker()
                    discovery_result = await worker.discover_calendars(user_id=user_id, provider="google")
                    logger.info(f"Automatically triggered calendar discovery for user {user_id}")

                    # Immediately pull events from discovered calendars
                    if discovery_result.get("success"):
                        # Get the actual calendar_calendars records from database using repository
                        from app.database.repositories.calendar_repositories.calendar_repository import (
                            get_calendar_calendar_repository
                        )
                        
                        calendar_repo = get_calendar_calendar_repository()
                        calendars = await calendar_repo.get_active_by_provider(
                            user_id=user_id,
                            provider="google"
                        )

                        if calendars:
                            for calendar in calendars:
                                try:
                                    await worker.pull_incremental(calendar["id"])
                                    logger.info(f"Initial event pull completed for calendar {calendar['id']}")
                                    await worker.ensure_watch(calendar["id"])
                                    logger.info(f"Watch channel ensured for calendar {calendar['id']}")
                                except Exception as pull_error:
                                    logger.error(f"Failed to pull events for calendar {calendar['id']}: {str(pull_error)}")
                except Exception as discovery_error:
                    logger.error(f"Failed to auto-discover calendars for user {user_id}: {str(discovery_error)}")
                    # Don't fail the OAuth flow if discovery fails

            # Redirect to frontend success page
            redirect_url = f"{settings.CLIENT_URL}/oauth/success?provider=google&email={user_info.get('email', '')}"
            return RedirectResponse(url=redirect_url)
            
        except Exception as e:
            logger.error(f"Failed to store Google OAuth tokens: {str(e)}")
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error handling Google OAuth callback: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        redis_client = await get_redis_client()

        # Ensure Redis client is initialized
        if not redis_client._client:
            await redis_client.initialize()
        
        # Extract base state and service (format: "token:service")
        state_parts = state.split(":")
        base_state = state_parts[0]
        service_type = state_parts[1] if len(state_parts) > 1 else "default"

        state_data = await redis_client.get(f"oauth_state:{base_state}")

        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )

        # Decode if bytes (Redis sometimes returns bytes even with decode_responses=True)
        if isinstance(state_data, bytes):
            state_data = state_data.decode('utf-8')

        user_id, provider = state_data.split(":", 1)

        logger.info(f"OAuth callback for user {user_id}, provider {provider}, service {service_type}")

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
        from app.services.auth.token_service import get_token_service
        from app.models.auth.oauth_tokens import OAuthTokenCreate
        
        token_service = get_token_service()
        
        # Create connection data for secure storage
        from app.models.auth.oauth_tokens import Provider
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        connection_data = OAuthTokenCreate(
            provider=Provider.MICROSOFT,
            service_type=service_type,  # Add service type
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scopes=token_data.get("scope", "").split() if token_data.get("scope") else [],
            email=user_info.get('mail', user_info.get('userPrincipalName'))  # Re-enabled after adding email column
        )

        try:
            # Store encrypted tokens via secure token service with service type
            connection_id = await token_service.store_user_tokens(
                user_id=user_id,
                provider="microsoft",
                service_type=service_type,  # Pass extracted service type
                tokens=connection_data
            )

            # Clean up state
            await redis_client.delete(f"oauth_state:{base_state}")

            logger.info(f"Successfully stored encrypted Microsoft OAuth tokens for user {user_id} (connection_id: {connection_id})")

            # Emit WebSocket event to notify frontend immediately
            try:
                from app.core.infrastructure.websocket import websocket_manager
                await websocket_manager.emit_to_user(user_id, 'oauth_connected', {
                    'provider': 'microsoft',
                    'service': service_type,
                    'email': user_info.get('mail', user_info.get('userPrincipalName')),
                    'connected': True,
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.info(f"Emitted oauth_connected WebSocket event for user {user_id}")
            except Exception as ws_error:
                logger.error(f"Failed to emit WebSocket event: {str(ws_error)}")
                # Don't fail OAuth flow if WebSocket fails

            # Trigger calendar discovery if calendar scopes are present
            scopes = connection_data.scopes or []
            if any("calendar" in scope for scope in scopes):
                try:
                    from app.jobs.calendar.calendar_sync_worker import CalendarSyncWorker

                    worker = CalendarSyncWorker()
                    discovery_result = await worker.discover_calendars(user_id=user_id, provider="microsoft")
                    logger.info(f"Automatically triggered Microsoft calendar discovery for user {user_id}")

                    # Immediately pull events from discovered calendars
                    if discovery_result.get("success"):
                        # Get the actual calendar_calendars records from database using repository
                        from app.database.repositories.calendar_repositories.calendar_repository import (
                            get_calendar_calendar_repository
                        )
                        
                        calendar_repo = get_calendar_calendar_repository()
                        calendars = await calendar_repo.get_active_by_provider(
                            user_id=user_id,
                            provider="microsoft"
                        )

                        if calendars:
                            for calendar in calendars:
                                try:
                                    await worker.pull_incremental(calendar["id"])
                                    logger.info(f"Initial event pull completed for calendar {calendar['id']}")
                                except Exception as pull_error:
                                    logger.error(f"Failed to pull events for calendar {calendar['id']}: {str(pull_error)}")
                except Exception as discovery_error:
                    logger.error(f"Failed to auto-discover Microsoft calendars for user {user_id}: {str(discovery_error)}")
                    # Don't fail the OAuth flow if discovery fails

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
    Get all OAuth connections for the current user, separated by service
    """
    try:
        from app.services.auth.token_service import get_token_service

        token_service = get_token_service()

        # Get all connected accounts with actual scopes
        connected_accounts = await token_service.get_user_connected_accounts(current_user.user_id)

        connections = []

        # Return one connection per service
        for account in connected_accounts:
            connections.append(OAuthConnectionStatus(
                provider=account.provider.value,
                service=account.service_type,  # NEW: Include service type
                connected=True,
                user_email=account.email,
                expires_at=account.expires_at.isoformat() if account.expires_at else None,
                scopes=account.scopes
            ))

        return connections

    except Exception as e:
        logger.error(f"Error getting OAuth connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get OAuth connections: {str(e)}"
        )


@router.delete("/connections/{provider}/{service}")
async def disconnect_oauth_provider(
    provider: str,
    service: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Disconnect specific OAuth service for the current user
    """
    if provider not in ["google", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'microsoft'"
        )

    try:
        from app.services.auth.token_service import get_token_service

        token_service = get_token_service()

        # Remove tokens for specific service
        success = await token_service.remove_user_tokens(current_user.user_id, provider, service)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active {provider}/{service} connection found"
            )

        logger.info(f"Disconnected {provider}/{service} OAuth for user {current_user.user_id}")

        return {
            "message": f"Successfully disconnected {provider} {service}",
            "provider": provider,
            "service": service
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting OAuth provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect {provider}/{service}: {str(e)}"
        )
