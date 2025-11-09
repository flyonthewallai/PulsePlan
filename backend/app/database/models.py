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
        data = self.dict(exclude_none=True)
        # Convert datetime objects to ISO strings for Supabase
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
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

    # Role-based access control
    role: str = Field("user", description="User role: 'user' or 'admin'")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "subscription_status": "premium",
                "timezone": "America/New_York",
                "role": "user"
            }
        }


class TokenStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REFRESH_NEEDED = "refresh_needed"


class IntegrationStatus(str, Enum):
    OK = "ok"
    NEEDS_REAUTH = "needs_reauth"
    ERROR = "error"


# Standard course colors - matches color picker palette (darker, blue-tinted rainbow spectrum)
STANDARD_COURSE_COLORS = [
    '#B91C1C', '#DC2626', '#BE185D', '#EC4899',  # Reds & Pinks
    '#D97706', '#F59E0B', '#CA8A04', '#A3A3A3',  # Oranges & Yellows
    '#166534', '#059669', '#0D9488', '#0F766E',  # Greens & Teals
    '#0369A1', '#1E40AF', '#3730A3', '#6B21A8',  # Blues & Purples
]


class CourseModel(BaseDBModel):
    """Course model for organizing tasks by subject/class"""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Course name")
    color: str = Field(..., description="Course color (hex code)")

    # Canvas integration fields
    canvas_id: Optional[int] = Field(None, description="Canvas course ID")
    canvas_name: Optional[str] = Field(None, description="Canvas course name")
    canvas_course_code: Optional[str] = Field(None, description="Canvas course code")
    external_source: str = Field("manual", description="Source of the course (manual, canvas)")

    # Optional fields
    icon: Optional[str] = Field(None, description="Course icon/emoji")

    @classmethod
    def get_next_color(cls, existing_colors: List[str]) -> str:
        """Get the next available color from the standard palette"""
        used_colors = set(existing_colors)
        for color in STANDARD_COURSE_COLORS:
            if color not in used_colors:
                return color
        # If all colors are used, cycle through them again
        return STANDARD_COURSE_COLORS[len(existing_colors) % len(STANDARD_COURSE_COLORS)]

    @classmethod
    def from_canvas_course(cls, user_id: str, canvas_course: Dict[str, Any], color: str) -> 'CourseModel':
        """Create a CourseModel from Canvas course data"""
        return cls(
            user_id=user_id,
            name=canvas_course.get("name", "Untitled Course"),
            color=color,
            canvas_id=canvas_course.get("id"),
            canvas_name=canvas_course.get("name"),
            canvas_course_code=canvas_course.get("course_code"),
            external_source="canvas"
        )


class CanvasIntegrationModel(BaseDBModel):
    """Canvas integration model with secure token storage"""

    user_id: str = Field(..., description="User ID")
    base_url: str = Field(..., description="Canvas base URL")

    # Encrypted token storage
    token_ciphertext: str = Field(..., description="Encrypted Canvas API token")
    kms_key_id: str = Field(..., description="KMS key ID for token encryption")

    # Integration status
    status: IntegrationStatus = Field(IntegrationStatus.OK, description="Integration status")
    last_full_sync_at: Optional[datetime] = Field(None, description="Last full sync timestamp")
    last_delta_at: Optional[datetime] = Field(None, description="Last delta sync timestamp")
    last_error_code: Optional[str] = Field(None, description="Last error code if any")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "base_url": "https://canvas.university.edu",
                "status": "ok"
            }
        }


class ExternalCursorModel(BaseDBModel):
    """External system cursor for tracking sync state"""

    user_id: str = Field(..., description="User ID")
    source: str = Field(..., description="External source (canvas, google_calendar, etc.)")
    cursor_type: str = Field(..., description="Type of cursor (assignments, events, etc.)")
    cursor_value: str = Field(..., description="Cursor value (etag, updated_at, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "source": "canvas",
                "cursor_type": "assignments",
                "cursor_value": "2023-10-01T12:00:00Z"
            }
        }


class ExternalSource(str, Enum):
    CANVAS = "canvas"
    MANUAL = "manual"
    CALENDAR = "calendar"


class TaskType(str, Enum):
    TASK = "task"
    ASSIGNMENT = "assignment"
    TODO = "todo"
    EVENT = "event"
    EXAM = "exam"
    QUIZ = "quiz"
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    DEADLINE = "deadline"
    CLASS = "class"
    SOCIAL = "social"
    PERSONAL = "personal"
    WORK = "work"
    STUDY = "study"
    READING = "reading"
    PROJECT = "project"
    HOBBY = "hobby"
    ADMIN = "admin"


class TaskModel(BaseDBModel):
    """Comprehensive task model supporting all database fields including Canvas integration"""

    # Core task fields
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Task metadata
    task_type: TaskType = Field(..., description="Academic task type (assignment, quiz, exam)")
    subject: Optional[str] = Field(None, description="Subject/course")
    tags: Optional[List[str]] = Field(None, description="Task tags")

    # Status and completion
    status: str = Field("pending", description="Task status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Priority and scheduling
    priority: str = Field("medium", description="Task priority")
    difficulty: Optional[str] = Field(None, description="Task difficulty")
    weight: Optional[float] = Field(1.0, description="Task weight")

    # Timing fields
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_minutes: Optional[int] = Field(None, description="Estimated duration")
    actual_minutes: Optional[int] = Field(None, description="Actual duration")
    min_block_minutes: Optional[int] = Field(None, description="Minimum block size")
    max_block_minutes: Optional[int] = Field(None, description="Maximum block size")
    preparation_time_minutes: Optional[int] = Field(0, description="Preparation time")

    # Scheduling constraints
    earliest_start: Optional[datetime] = Field(None, description="Earliest start time")
    deadline: Optional[datetime] = Field(None, description="Hard deadline")
    preferred_windows: Optional[Dict[str, Any]] = Field(None, description="Preferred time windows")
    avoid_windows: Optional[Dict[str, Any]] = Field(None, description="Windows to avoid")
    pinned_slots: Optional[Dict[str, Any]] = Field(None, description="Pinned time slots")
    fixed: Optional[bool] = Field(False, description="Fixed scheduling")

    # Calendar-style fields
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    all_day: Optional[bool] = Field(False, description="All-day event")
    location: Optional[str] = Field(None, description="Location")
    location_type: Optional[str] = Field(None, description="Location type")
    meeting_url: Optional[str] = Field(None, description="Meeting URL")
    reminder_minutes: Optional[List[int]] = Field(None, description="Reminder minutes")
    attendees: Optional[List[str]] = Field(None, description="Attendees")

    # Recurrence
    is_recurring: Optional[bool] = Field(False, description="Is recurring")
    recurrence_pattern: Optional[str] = Field(None, description="Recurrence pattern")
    recurrence_interval: Optional[int] = Field(1, description="Recurrence interval")
    recurrence_end_date: Optional[datetime] = Field(None, description="Recurrence end date")

    # Task relationships
    parent_task_id: Optional[str] = Field(None, description="Parent task ID")
    must_finish_before: Optional[str] = Field(None, description="Task that must finish before this")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisites")

    # External source tracking (legacy)
    source: Optional[str] = Field("manual", description="Source system")
    external_id: Optional[str] = Field(None, description="External ID")

    # Canvas-specific fields
    canvas_id: Optional[int] = Field(None, description="Canvas assignment ID")
    canvas_url: Optional[str] = Field(None, description="Canvas assignment URL")
    canvas_course_id: Optional[int] = Field(None, description="Canvas course ID")
    canvas_grade: Optional[Dict[str, Any]] = Field(None, description="Canvas grade info")
    canvas_points: Optional[float] = Field(None, description="Canvas points possible")
    canvas_max_points: Optional[float] = Field(None, description="Canvas max points")
    submission_type: Optional[str] = Field(None, description="Submission type")
    html_url: Optional[str] = Field(None, description="Canvas HTML URL")

    # Calendar integration
    external_calendar_id: Optional[str] = Field(None, description="External calendar ID")
    external_event_id: Optional[str] = Field(None, description="External event ID")
    sync_source: Optional[str] = Field("manual", description="Sync source")
    last_synced_at: Optional[datetime] = Field(None, description="Last sync timestamp")

    # Additional metadata
    kind: Optional[str] = Field(None, description="Task kind")
    course_id: Optional[str] = Field(None, description="Course ID")
    color: Optional[str] = Field(None, description="Color")

    # External source tracking (new schema)
    external_source: Optional[str] = Field("manual", description="External source")
    external_course_id: Optional[str] = Field(None, description="External course ID")
    external_updated_at: Optional[datetime] = Field(None, description="External update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Complete assignment",
                "external_source": "canvas",
                "canvas_id": 12345
            }
        }


class AssignmentImportModel(BaseDBModel):
    """Staging table for raw Canvas assignment payloads"""

    user_id: str = Field(..., description="User ID")
    canvas_id: str = Field(..., description="Canvas assignment ID")
    course_id: str = Field(..., description="Canvas course ID")

    # Raw Canvas payload
    raw_payload: Dict[str, Any] = Field(..., description="Raw Canvas assignment data")
    processed: bool = Field(False, description="Processing flag")

    # Processing metadata
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    processing_error: Optional[str] = Field(None, description="Processing error if any")

    class Config:
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "canvas_id": "12345",
                "course_id": "67890",
                "processed": False
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



class TodoPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PredefinedTagModel(BaseDBModel):
    """Predefined tag model for system tags"""

    name: str = Field(..., description="Tag name")
    category: Optional[str] = Field(None, description="Tag category")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "fitness",
                "category": "health"
            }
        }


class UserTagModel(BaseDBModel):
    """User custom tag model"""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Tag name")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "name": "meal prep"
            }
        }


class TodoModel(BaseDBModel):
    """Todo model for lightweight task management"""

    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Core todo fields
    completed: bool = Field(False, description="Completion flag")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    priority: TodoPriority = Field(TodoPriority.MEDIUM, description="Todo priority")

    # Timing
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_minutes: Optional[int] = Field(None, description="Estimated duration")
    actual_minutes: Optional[int] = Field(None, description="Actual duration")
    reminder_minutes: Optional[List[int]] = Field(None, description="Reminder times")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "title": "Buy groceries",
                "priority": "medium",
                "description": "Need to get milk, eggs, and bread"
            }
        }


class CalendarEventModel(BaseDBModel):
    """Calendar event model for synced events"""

    user_id: str = Field(..., description="User ID")
    calendar_id_ref: Optional[str] = Field(None, description="Reference to calendar_calendars table")
    provider: Optional[str] = Field(None, description="Calendar provider")
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

    # Status flags
    is_cancelled: bool = Field(False, description="Event cancelled flag")

    # Sync metadata
    last_synced: Optional[datetime] = Field(None, description="Last sync timestamp")
    sync_status: str = Field("synced", description="Sync status")
    etag: Optional[str] = Field(None, description="Provider etag for concurrency control")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "calendar_id_ref": "calendar-uuid",
                "provider": "google",
                "external_id": "google_event_123",
                "title": "Team Meeting",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:00:00Z",
                "location": "Conference Room A",
                "is_cancelled": False
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
        json_schema_extra = {
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
        json_schema_extra = {
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


class CalendarProvider(str, Enum):
    """Calendar provider types"""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"


class CalendarCalendarModel(BaseDBModel):
    """Calendar calendars - discovered calendars per provider account"""

    user_id: str = Field(..., description="User ID")
    oauth_token_id: str = Field(..., description="OAuth token ID reference")
    provider: CalendarProvider = Field(..., description="Calendar provider")
    provider_calendar_id: str = Field(..., description="Provider's calendar ID")
    summary: Optional[str] = Field(None, description="Calendar name/summary")
    timezone: Optional[str] = Field("UTC", description="Calendar timezone")
    is_active: bool = Field(True, description="Show in PulsePlan central view")
    is_primary_write: bool = Field(False, description="Is primary write calendar")

    # Google incremental sync + webhook channel
    sync_token: Optional[str] = Field(None, description="Incremental sync token")
    watch_channel_id: Optional[str] = Field(None, description="Watch channel ID")
    watch_resource_id: Optional[str] = Field(None, description="Watch resource ID")
    watch_expiration_at: Optional[datetime] = Field(None, description="Watch expiration timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "oauth_token_id": "token-uuid",
                "provider": "google",
                "provider_calendar_id": "primary",
                "summary": "Personal Calendar",
                "timezone": "America/New_York",
                "is_active": True,
                "is_primary_write": True
            }
        }


class SourceOfTruth(str, Enum):
    """Source of truth for calendar links"""
    TASK = "task"
    CALENDAR = "calendar"
    LATEST_UPDATE = "latest_update"


class CalendarLinkModel(BaseDBModel):
    """Links PulsePlan tasks to provider calendar events for two-way sync"""

    user_id: str = Field(..., description="User ID")
    task_id: str = Field(..., description="Task ID reference")
    calendar_id: str = Field(..., description="Calendar calendar ID reference")
    provider: CalendarProvider = Field(..., description="Calendar provider")
    provider_event_id: str = Field(..., description="Provider's event ID")
    last_pushed_at: Optional[datetime] = Field(None, description="Last pushed to provider timestamp")
    last_pulled_at: Optional[datetime] = Field(None, description="Last pulled from provider timestamp")
    source_of_truth: SourceOfTruth = Field(SourceOfTruth.LATEST_UPDATE, description="Source of truth for conflicts")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "task_id": "task-uuid",
                "calendar_id": "calendar-uuid",
                "provider": "google",
                "provider_event_id": "google_event_123",
                "source_of_truth": "latest_update"
            }
        }


class NLUPromptLogModel(BaseDBModel):
    """NLU prompt log for capturing and refining intent classification"""

    user_id: str = Field(..., description="User ID")
    prompt: str = Field(..., description="Raw user input")
    predicted_intent: str = Field(..., description="Model's predicted intent")
    confidence: float = Field(..., description="Prediction confidence (similarity score)")

    # Multi-intent support
    secondary_intents: Optional[List[Dict[str, Any]]] = Field(None, description="Secondary intents with scores")

    # Human-in-the-loop corrections
    corrected_intent: Optional[str] = Field(None, description="Manual correction if prediction was wrong")
    correction_notes: Optional[str] = Field(None, description="Notes on why correction was needed")

    # Workflow feedback
    was_successful: Optional[bool] = Field(None, description="Whether the workflow succeeded")
    workflow_type: Optional[str] = Field(None, description="The workflow that was executed")
    execution_error: Optional[str] = Field(None, description="Error message if workflow failed")

    # Context
    conversation_id: Optional[str] = Field(None, description="Conversation/session ID")
    message_index: Optional[int] = Field(None, description="Message index in conversation")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "prompt": "schedule time to work on the assignment tomorrow",
                "predicted_intent": "scheduling",
                "confidence": 0.89,
                "secondary_intents": [{"intent": "task_management", "score": 0.65}],
                "was_successful": True,
                "workflow_type": "scheduling"
            }
        }


class TimeblockModel(BaseDBModel):
    """Timeblock model for normalized temporal scheduling data"""

    # Core fields
    user_id: str = Field(..., description="User ID")
    task_id: Optional[str] = Field(None, description="Optional link to parent task")
    title: str = Field(..., description="Timeblock title")
    start_time: datetime = Field(..., description="Start time (timezone-aware)")
    end_time: datetime = Field(..., description="End time (timezone-aware)")

    # Timeblock metadata
    type: str = Field("task_block", description="Timeblock type: task_block, habit, focus, break, meeting, class, study, exam, assignment, project, hobby, admin")
    status: str = Field("scheduled", description="Status: scheduled, completed, missed, cancelled, in_progress")
    source: str = Field("pulse", description="Source: pulse, external, manual, agent, scheduler")

    # Optional fields
    agent_reasoning: Optional[Dict[str, Any]] = Field(None, description="AI agent reasoning for this scheduling decision")
    location: Optional[str] = Field(None, description="Location")
    all_day: bool = Field(False, description="All-day timeblock")
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional flexible metadata (recurrence, preferences, etc.)")

    @validator('end_time')
    def validate_time_range(cls, v, values):
        """Ensure end_time is after start_time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "223e4567-e89b-12d3-a456-426614174000",
                "title": "Work on assignment - Part 1",
                "start_time": "2025-10-28T14:00:00Z",
                "end_time": "2025-10-28T16:00:00Z",
                "type": "assignment",
                "status": "scheduled",
                "source": "agent",
                "agent_reasoning": {
                    "rationale": "Scheduled during optimal focus time",
                    "confidence": 0.85,
                    "alternatives_considered": 2
                },
                "metadata": {
                    "priority": "high",
                    "course": "CS101"
                }
            }
        }


# Model registry for dynamic access
MODEL_REGISTRY = {
    'users': UserModel,
    'tasks': TaskModel,
    'todos': TodoModel,
    'timeblocks': TimeblockModel,
    'predefined_tags': PredefinedTagModel,
    'user_tags': UserTagModel,
    'todo_tags': None,  # Junction table - no specific model needed
    'calendar_events': CalendarEventModel,
    'calendar_calendars': CalendarCalendarModel,
    'calendar_links': CalendarLinkModel,
    'memories': MemoryModel,
    'workflow_executions': WorkflowExecutionModel,
    'nlu_prompt_logs': NLUPromptLogModel
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