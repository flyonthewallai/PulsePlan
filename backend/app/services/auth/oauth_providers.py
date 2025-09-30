import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from app.config.core.settings import settings

logger = logging.getLogger(__name__)

class GoogleOAuthProvider:
    """Google OAuth token refresh implementation"""
    
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Google OAuth token"""
        try:
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.TOKEN_URL, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Calculate expiration time
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    
                    return {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data.get("refresh_token", refresh_token),
                        "expires_at": expires_at.isoformat(),
                        "scopes": token_data.get("scope", "").split()
                    }
                else:
                    logger.error(f"Google token refresh failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error refreshing Google token: {e}")
            return None


class MicrosoftOAuthProvider:
    """Microsoft OAuth token refresh implementation"""
    
    def __init__(self):
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Microsoft OAuth token"""
        try:
            data = {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": "https://graph.microsoft.com/.default"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Calculate expiration time
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    
                    return {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data.get("refresh_token", refresh_token),
                        "expires_at": expires_at.isoformat(),
                        "scopes": token_data.get("scope", "").split()
                    }
                else:
                    logger.error(f"Microsoft token refresh failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error refreshing Microsoft token: {e}")
            return None


class CanvasOAuthProvider:
    """Canvas LMS OAuth provider (tokens typically don't expire)"""
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Canvas tokens typically don't expire, but validate if needed"""
        logger.info("Canvas tokens typically don't require refresh")
        return None


class NotionOAuthProvider:
    """Notion OAuth provider"""
    
    TOKEN_URL = "https://api.notion.com/v1/oauth/token"
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Notion OAuth token"""
        try:
            # Note: As of 2024, Notion tokens don't expire but this is a placeholder
            # for when they implement token refresh
            logger.info("Notion token refresh not currently required")
            return None
            
        except Exception as e:
            logger.error(f"Error refreshing Notion token: {e}")
            return None


class OAuthProviderFactory:
    """Factory for OAuth providers"""
    
    _providers = {
        "google": GoogleOAuthProvider,
        "microsoft": MicrosoftOAuthProvider,
        "canvas": CanvasOAuthProvider,
        "notion": NotionOAuthProvider
    }
    
    @classmethod
    def get_provider(cls, provider_name: str):
        """Get OAuth provider instance"""
        provider_class = cls._providers.get(provider_name.lower())
        if provider_class:
            return provider_class()
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider_name}")
    
    @classmethod
    def refresh_token(cls, provider_name: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh token for any provider"""
        provider = cls.get_provider(provider_name)
        return provider.refresh_token(refresh_token)
