"""
Agent API Models
Pydantic models for agent endpoint requests and responses
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UnifiedAgentRequest(BaseModel):
    """Request for unified agent processing"""
    query: str = Field(description="User query text")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    force_new_conversation: bool = Field(False, description="Force creation of new conversation")
    include_history: bool = Field(True, description="Include conversation history in processing")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UnifiedAgentResponse(BaseModel):
    """Response from unified agent processing"""
    success: bool
    conversation_id: str
    task_id: Optional[str] = None
    immediate_response: Optional[str] = None
    intent: str
    action: str
    confidence: float
    requires_followup: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskStatusRequest(BaseModel):
    """Request for task status"""
    task_id: str


class TaskCancelRequest(BaseModel):
    """Request to cancel task"""
    task_id: str
    reason: Optional[str] = "Cancelled by user"
