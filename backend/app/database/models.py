"""
Database Models
Supabase-compatible ORM models with validation and type safety
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid


class BaseDBModel(BaseModel):
    """Base model for all database entities"""
    
    id: Optional[str] = Field(None, description="Primary key")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    
    class Config:
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def generate_id(self) -> str:
        """Generate a new UUID for the record"""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self.id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase operations"""
        return self.dict(exclude_none=True)
    
    def to_supabase_insert(self) -> Dict[str, Any]:
        """Format for Supabase insert operations"""
        data = self.to_dict()
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.utcnow().isoformat()
        return data
    
    def to_supabase_update(self) -> Dict[str, Any]:
        """Format for Supabase update operations"""
        data = self.to_dict()
        data['updated_at'] = datetime.utcnow().isoformat()
        # Remove id and created_at for updates
        data.pop('id', None)
        data.pop('created_at', None)
        return data


class UserModel(BaseDBModel):
    """User model matching Supabase auth.users structure"""
    
    email: Optional[str] = Field(None, description="User email")
    subscription_status: str = Field("free", description="Subscription status")
    apple_transaction_id: Optional[str] = Field(None, description="Apple transaction ID")
    subscription_expires_at: Optional[datetime] = Field(None, description="Subscription expiry")
    subscription_updated_at: Optional[datetime] = Field(None, description="Last subscription update")
    
    # User preferences
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    timezone: Optional[str] = Field(None, description="User timezone")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "subscription_status": "premium",
                "timezone": "America/New_York"
            }
        }


class TokenStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REFRESH_NEEDED = "refresh_needed"


class OAuthTokenModel(BaseDBModel):
    """OAuth token storage with encryption"""
    
    user_id: str = Field(..., description="User ID")
    provider: str = Field(..., description="OAuth provider (google, microsoft, etc.)")
    
    # Encrypted token data
    access_token: str = Field(..., description="Encrypted access token")
    refresh_token: Optional[str] = Field(None, description="Encrypted refresh token")
    token_type: str = Field("Bearer", description="Token type")
    scope: Optional[str] = Field(None, description="Token scope")
    
    # Token metadata
    expires_at: datetime = Field(..., description="Token expiration time")
    last_refreshed: Optional[datetime] = Field(None, description="Last refresh timestamp")
    status: TokenStatus = Field(TokenStatus.ACTIVE, description="Token status")
    
    # Encryption metadata
    encryption_key_version: int = Field(1, description="Encryption key version")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['google', 'microsoft', 'canvas']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() >= self.expires_at
    
    def expires_soon(self, minutes: int = 30) -> bool:
        """Check if token expires within specified minutes"""
        from datetime import timedelta
        expiry_threshold = datetime.utcnow() + timedelta(minutes=minutes)
        return self.expires_at <= expiry_threshold
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "provider": "google",
                "access_token": "encrypted_token_data",
                "expires_at": "2024-01-15T12:00:00Z",
                "status": "active"
            }
        }


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskModel(BaseDBModel):
    """Task model for user tasks"""
    
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    
    # Task properties
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    
    # Timing
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    actual_duration: Optional[int] = Field(None, description="Actual duration in minutes")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Task tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Completion tracking
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "title": "Complete project proposal",
                "description": "Write and review the Q1 project proposal",
                "status": "pending",
                "priority": "high",
                "due_date": "2024-01-20T17:00:00Z",
                "estimated_duration": 120,
                "tags": ["work", "urgent"]
            }
        }


class TodoStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"


class TodoModel(BaseDBModel):
    """Todo model for simple todos"""
    
    user_id: str = Field(..., description="User ID")
    text: str = Field(..., description="Todo text")
    status: TodoStatus = Field(TodoStatus.OPEN, description="Todo status")
    
    # Optional fields
    due_date: Optional[datetime] = Field(None, description="Due date")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Todo tags")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "text": "Buy groceries",
                "status": "open",
                "tags": ["personal", "shopping"]
            }
        }


class CalendarEventModel(BaseDBModel):
    """Calendar event model for synced events"""
    
    user_id: str = Field(..., description="User ID")
    provider: str = Field(..., description="Calendar provider")
    external_id: str = Field(..., description="External event ID")
    
    # Event details
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    
    # Timing
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    is_all_day: bool = Field(False, description="All-day event flag")
    
    # Location and attendees
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="Attendee email addresses")
    
    # Sync metadata
    last_synced: Optional[datetime] = Field(None, description="Last sync timestamp")
    sync_status: str = Field("synced", description="Sync status")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "provider": "google",
                "external_id": "google_event_123",
                "title": "Team Meeting",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:00:00Z",
                "location": "Conference Room A"
            }
        }


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    USER_PREFERENCE = "user_preference"
    TASK_CONTEXT = "task_context"
    SYSTEM_INSIGHT = "system_insight"


class MemoryModel(BaseDBModel):
    """Memory model for AI agent context storage"""
    
    user_id: str = Field(..., description="User ID")
    memory_type: MemoryType = Field(..., description="Type of memory")
    
    # Content
    content: str = Field(..., description="Memory content")
    summary: Optional[str] = Field(None, description="Memory summary")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Memory tags")
    importance_score: float = Field(0.0, description="Importance score (0.0-1.0)")
    
    # Vector embedding (for retrieval)
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
    # Expiration
    expires_at: Optional[datetime] = Field(None, description="Memory expiration")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "memory_type": "user_preference",
                "content": "User prefers morning meetings between 9-11 AM",
                "summary": "Morning meeting preference",
                "importance_score": 0.8,
                "tags": ["scheduling", "preference"]
            }
        }


class WorkflowExecutionModel(BaseDBModel):
    """Workflow execution tracking"""
    
    user_id: str = Field(..., description="User ID")
    workflow_type: str = Field(..., description="Workflow type")
    trace_id: str = Field(..., description="Trace ID")
    
    # Execution details
    status: str = Field("running", description="Execution status")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data")
    
    # Timing
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    
    # Error tracking
    error: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error info")
    
    # Metrics
    nodes_executed: Optional[List[str]] = Field(None, description="Executed workflow nodes")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Execution metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "workflow_type": "natural_language",
                "trace_id": "trace-123",
                "status": "completed",
                "input_data": {"query": "Create a task for tomorrow"},
                "started_at": "2024-01-15T10:00:00Z",
                "execution_time": 2.5
            }
        }


# Model registry for dynamic access
MODEL_REGISTRY = {
    'users': UserModel,
    'oauth_tokens': OAuthTokenModel,
    'tasks': TaskModel,
    'todos': TodoModel,
    'calendar_events': CalendarEventModel,
    'memories': MemoryModel,
    'workflow_executions': WorkflowExecutionModel
}


def get_model_class(table_name: str) -> Optional[BaseDBModel]:
    """Get model class by table name"""
    return MODEL_REGISTRY.get(table_name)


def validate_model_data(table_name: str, data: Dict[str, Any]) -> BaseDBModel:
    """Validate data against model schema"""
    model_class = get_model_class(table_name)
    if not model_class:
        raise ValueError(f"Unknown table: {table_name}")
    
    return model_class(**data)