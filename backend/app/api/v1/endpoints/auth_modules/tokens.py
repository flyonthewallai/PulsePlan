from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.auth import get_current_user, CurrentUser
from app.services.auth.token_service import get_token_service

# Initialize token service instance
token_service = get_token_service()
from app.models.auth.oauth_tokens import (
    OAuthTokenResponse, OAuthTokenCreate, 
    UserTokens, ConnectionStatus, Provider
)
from app.observability.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/connections", response_model=List[OAuthTokenResponse])
async def get_user_connections(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user's OAuth connections (matches Node.js endpoint)"""
    try:
        connections = await token_service.get_user_connected_accounts(current_user.user_id)
        
        # Convert to response format (exclude sensitive token data)
        response_connections = []
        for conn in connections:
            response_conn = OAuthTokenResponse(
                id=conn.id,
                user_id=conn.user_id,
                provider=conn.provider,
                expires_at=conn.expires_at,
                scopes=conn.scopes,
                email=conn.email,
                created_at=conn.created_at,
                updated_at=conn.updated_at,
                is_expired=conn.expires_at and conn.expires_at <= conn.created_at  # Simple check
            )
            response_connections.append(response_conn)
        
        logger.info(
            f"Retrieved {len(response_connections)} connections for user", 
            context={"user_id": current_user.user_id, "connection_count": len(response_connections)}
        )
        
        return response_connections
        
    except Exception as e:
        logger.error(
            "Failed to retrieve user connections", 
            exception=e, 
            context={"user_id": current_user.user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connections"
        )

@router.get("/connections/status", response_model=ConnectionStatus)
async def get_connection_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get connection status for all providers (matches Node.js pattern)"""
    try:
        status_result = await token_service.get_user_connection_status(current_user.user_id)
        
        logger.info(
            "Retrieved connection status for user",
            context={"user_id": current_user.user_id, "status": status_result.dict()}
        )
        
        return status_result
        
    except Exception as e:
        logger.error(
            "Failed to retrieve connection status",
            exception=e,
            context={"user_id": current_user.user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection status"
        )

@router.get("/tokens", response_model=UserTokens)
async def get_user_tokens_for_agent(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user tokens formatted for agent use (matches Node.js getUserTokensForAgent)"""
    try:
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        # Log without exposing actual tokens
        provider_count = sum(1 for provider in [user_tokens.google, user_tokens.microsoft, user_tokens.canvas, user_tokens.notion] if provider)
        
        logger.info(
            "Retrieved user tokens for agent",
            context={"user_id": current_user.user_id, "provider_count": provider_count}
        )
        
        return user_tokens
        
    except Exception as e:
        logger.error(
            "Failed to retrieve user tokens for agent",
            exception=e,
            context={"user_id": current_user.user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tokens"
        )

@router.post("/connections/{provider}")
async def store_connection(
    provider: Provider,
    connection_data: OAuthTokenCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Store OAuth connection for provider (matches Node.js storeUserTokens)"""
    try:
        connection_id = await token_service.store_user_tokens(
            current_user.user_id,
            provider.value,
            connection_data
        )
        
        logger.info(
            f"Stored {provider.value} connection for user",
            context={
                "user_id": current_user.user_id, 
                "provider": provider.value,
                "connection_id": connection_id
            }
        )
        
        return {
            "message": f"{provider.value.title()} connection stored successfully",
            "connection_id": connection_id,
            "provider": provider.value
        }
        
    except Exception as e:
        logger.error(
            f"Failed to store {provider.value} connection",
            exception=e,
            context={"user_id": current_user.user_id, "provider": provider.value}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store {provider.value} connection"
        )

@router.delete("/connections/{provider}")
async def remove_connection(
    provider: Provider,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Remove OAuth connection for provider (matches Node.js removeUserTokens)"""
    try:
        success = await token_service.remove_user_tokens(
            current_user.user_id,
            provider.value
        )
        
        if success:
            logger.info(
                f"Removed {provider.value} connection for user",
                context={"user_id": current_user.user_id, "provider": provider.value}
            )
            
            return {
                "message": f"{provider.value.title()} connection removed successfully",
                "provider": provider.value
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{provider.value.title()} connection not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to remove {provider.value} connection",
            exception=e,
            context={"user_id": current_user.user_id, "provider": provider.value}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove {provider.value} connection"
        )

@router.get("/connections/{provider}/status")
async def check_provider_connection(
    provider: Provider,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Check if user has specific provider connected (matches Node.js hasProviderConnected)"""
    try:
        is_connected = await token_service.has_provider_connected(
            current_user.user_id,
            provider.value
        )
        
        return {
            "provider": provider.value,
            "connected": is_connected
        }
        
    except Exception as e:
        logger.error(
            f"Failed to check {provider.value} connection status",
            exception=e,
            context={"user_id": current_user.user_id, "provider": provider.value}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check {provider.value} connection status"
        )