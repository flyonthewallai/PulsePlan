"""
OAuth Token Models
Database models for storing encrypted OAuth tokens
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class OAuthToken(Base):
    """
    OAuth token storage with encryption support
    Stores access tokens, refresh tokens, and metadata for various providers
    """
    __tablename__ = "oauth_tokens"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)  # google, microsoft, etc.
    
    # Encrypted token data
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted, can be null
    token_type = Column(String, default="Bearer")
    scope = Column(String, nullable=True)
    
    # Token metadata
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_refreshed = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Encryption metadata
    encryption_key_version = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<OAuthToken(user_id='{self.user_id}', provider='{self.provider}', expires_at='{self.expires_at}')>"
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() >= self.expires_at
    
    def expires_soon(self, minutes: int = 30) -> bool:
        """Check if token expires within specified minutes"""
        from datetime import timedelta
        expiry_threshold = datetime.utcnow() + timedelta(minutes=minutes)
        return self.expires_at <= expiry_threshold