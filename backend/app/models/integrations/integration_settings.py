from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UserIntegrationSettings(BaseModel):
    """Model for user integration settings"""
    
    id: UUID
    user_id: UUID
    integration_id: str = Field(..., description="Integration identifier (e.g., 'gmail', 'google-calendar')")
    account_email: Optional[str] = Field(None, description="Specific account email for this integration")
    instructions: Optional[str] = Field(None, description="User's custom instructions for this integration")
    signature: Optional[str] = Field(None, description="User's custom signature for this integration")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional integration-specific settings")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserIntegrationSettingsCreate(BaseModel):
    """Schema for creating user integration settings"""
    
    integration_id: str = Field(..., description="Integration identifier")
    account_email: Optional[str] = Field(None, description="Account email")
    instructions: Optional[str] = Field(None, description="Custom instructions")
    signature: Optional[str] = Field(None, description="Custom signature")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")


class UserIntegrationSettingsUpdate(BaseModel):
    """Schema for updating user integration settings"""
    
    instructions: Optional[str] = Field(None, description="Custom instructions")
    signature: Optional[str] = Field(None, description="Custom signature")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional settings")


class UserIntegrationSettingsResponse(BaseModel):
    """Response model for user integration settings"""
    
    id: UUID
    integration_id: str
    account_email: Optional[str]
    instructions: Optional[str]
    signature: Optional[str]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
