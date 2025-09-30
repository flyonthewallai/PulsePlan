"""
Authentication models.

This module contains all authentication and authorization related models including:
- OAuth token models for various providers (Google, Microsoft, Canvas, Notion)
- Access token and refresh token management
- Provider-specific authentication schemas
"""

from .oauth_tokens import (
    Provider,
    OAuthToken,
    OAuthTokenCreate,
    OAuthTokenUpdate,
    OAuthTokenResponse,
    TokenPair,
    UserTokens,
    TokenRefreshResult,
    TokenValidationResult,
    ConnectionStatus
)

__all__ = [
    "Provider",
    "OAuthToken",
    "OAuthTokenCreate", 
    "OAuthTokenUpdate",
    "OAuthTokenResponse",
    "TokenPair",
    "UserTokens",
    "TokenRefreshResult",
    "TokenValidationResult",
    "ConnectionStatus",
]
