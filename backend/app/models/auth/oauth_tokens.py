from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Provider(str, Enum):
    """OAuth provider types (matching existing Node.js backend)"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    CANVAS = "canvas"
    NOTION = "notion"

class OAuthToken(BaseModel):
    """
    OAuth token model matching existing Supabase schema
    Corresponds to oauth_tokens table
    """
    id: str
    user_id: str
    provider: Provider
    access_token: str  # Will be encrypted in storage
    refresh_token: Optional[str] = None  # Will be encrypted in storage
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OAuthTokenCreate(BaseModel):
    """Schema for creating OAuth tokens"""
    provider: Provider
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
    email: Optional[str] = None

class OAuthTokenUpdate(BaseModel):
    """Schema for updating OAuth tokens"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: Optional[List[str]] = None
    email: Optional[str] = None

class OAuthTokenResponse(BaseModel):
    """Response schema (excludes sensitive token data)"""
    id: str
    user_id: str
    provider: Provider
    expires_at: Optional[datetime] = None
    scopes: List[str]
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_expired: bool = False

class TokenPair(BaseModel):
    """Token pair for OAuth operations (matching Node.js types)"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)

class UserTokens(BaseModel):
    """User's tokens across all providers (matching Node.js UserTokens)"""
    user_id: str
    google: Optional[TokenPair] = None
    microsoft: Optional[TokenPair] = None
    canvas: Optional[TokenPair] = None
    notion: Optional[TokenPair] = None

class TokenRefreshResult(BaseModel):
    """Result of token refresh operation"""
    success: bool
    tokens: Optional[TokenPair] = None
    error: Optional[str] = None

class TokenValidationResult(BaseModel):
    """Result of token validation"""
    is_valid: bool
    needs_refresh: bool
    error: Optional[str] = None

class ConnectionStatus(BaseModel):
    """Connection status for all providers"""
    google: bool = False
    microsoft: bool = False
    canvas: bool = False
    notion: bool = False