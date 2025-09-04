"""
OAuth Service Classes
Handles OAuth token refresh for different providers
"""
import httpx
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from app.config.settings import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class BaseOAuthService(ABC):
    """Base class for OAuth service implementations"""
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh an OAuth token"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name"""
        pass
    
    @abstractmethod
    async def exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information using access token"""
        pass


class GoogleOAuthService(BaseOAuthService):
    """Google OAuth service for token refresh"""
    
    def __init__(self):
        self.token_url = "https://oauth2.googleapis.com/token"
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
    
    def get_provider_name(self) -> str:
        return "google"
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh Google OAuth token
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            Dict with new token data or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.error("Google OAuth credentials not configured")
            return None
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_url,
                    data=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully refreshed Google OAuth token")
                    return token_data
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", "Unknown error")
                    logger.error(f"Google token refresh failed: {error_msg} (status: {response.status_code})")
                    
                    # Check for revoked token
                    if error_msg == "invalid_grant":
                        raise Exception("Token has been revoked or expired")
                    
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Google token refresh timed out")
            return None
        except Exception as e:
            logger.error(f"Error refreshing Google token: {str(e)}")
            raise e
    
    async def exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange Google OAuth authorization code for tokens
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dict with token data or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.error("Google OAuth credentials not configured")
            return None
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URL
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_url,
                    data=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully exchanged Google authorization code for tokens")
                    return token_data
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", "Unknown error")
                    logger.error(f"Google code exchange failed: {error_msg} (status: {response.status_code})")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Google code exchange timed out")
            return None
        except Exception as e:
            logger.error(f"Error exchanging Google authorization code: {str(e)}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get Google user information using access token
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dict with user info or None if failed
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers=headers
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info("Successfully retrieved Google user information")
                    return user_info
                else:
                    logger.error(f"Failed to get Google user info (status: {response.status_code})")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Google user info request timed out")
            return None
        except Exception as e:
            logger.error(f"Error getting Google user info: {str(e)}")
            return None


class MicrosoftOAuthService(BaseOAuthService):
    """Microsoft OAuth service for token refresh"""
    
    def __init__(self):
        self.token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
    
    def get_provider_name(self) -> str:
        return "microsoft"
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh Microsoft OAuth token
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            Dict with new token data or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.error("Microsoft OAuth credentials not configured")
            return None
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "https://graph.microsoft.com/.default"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_url,
                    data=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully refreshed Microsoft OAuth token")
                    return token_data
                else:
                    error_data = response.json() if response.content else {}
                    error_code = error_data.get("error", "Unknown error")
                    error_description = error_data.get("error_description", "")
                    
                    logger.error(f"Microsoft token refresh failed: {error_code} - {error_description} (status: {response.status_code})")
                    
                    # Check for revoked token
                    if error_code in ["invalid_grant", "invalid_client"]:
                        raise Exception(f"Token has been revoked or expired: {error_description}")
                    
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Microsoft token refresh timed out")
            return None
        except Exception as e:
            logger.error(f"Error refreshing Microsoft token: {str(e)}")
            raise e
    
    async def exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange Microsoft OAuth authorization code for tokens
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dict with token data or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.error("Microsoft OAuth credentials not configured")
            return None
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.MICROSOFT_REDIRECT_URL,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_url,
                    data=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully exchanged Microsoft authorization code for tokens")
                    return token_data
                else:
                    error_data = response.json() if response.content else {}
                    error_code = error_data.get("error", "Unknown error")
                    error_description = error_data.get("error_description", "")
                    logger.error(f"Microsoft code exchange failed: {error_code} - {error_description} (status: {response.status_code})")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Microsoft code exchange timed out")
            return None
        except Exception as e:
            logger.error(f"Error exchanging Microsoft authorization code: {str(e)}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get Microsoft user information using access token
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dict with user info or None if failed
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers=headers
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info("Successfully retrieved Microsoft user information")
                    return user_info
                else:
                    logger.error(f"Failed to get Microsoft user info (status: {response.status_code})")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Microsoft user info request timed out")
            return None
        except Exception as e:
            logger.error(f"Error getting Microsoft user info: {str(e)}")
            return None


class OAuthServiceFactory:
    """Factory for creating OAuth service instances"""
    
    _services = {
        "google": GoogleOAuthService,
        "microsoft": MicrosoftOAuthService,
        "gmail": GoogleOAuthService,  # Gmail uses Google OAuth
        "outlook": MicrosoftOAuthService  # Outlook uses Microsoft OAuth
    }
    
    @classmethod
    def get_service(cls, provider: str) -> Optional[BaseOAuthService]:
        """Get OAuth service instance for provider"""
        service_class = cls._services.get(provider.lower())
        if service_class:
            return service_class()
        return None
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported providers"""
        return list(cls._services.keys())