"""
Type definitions for the memory system.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel

# Namespace types for organizing memory content
Namespace = Literal[
    "task",           # atomic actionable (assignment, study block candidate, project step)
    "doc",            # syllabi, PDFs, study guides, Notion pages (chunked)
    "email",          # instructor/TA threads (rolled-up action briefs)
    "calendar",       # event briefs and constraints
    "course",         # course-level policy/grading/exam windows
    "chat_summary",   # durable summaries of prior chats
    "profile_snapshot",  # weekly behavior stats (pace, typical start times)
    "web"             # clipped rubric/spec pages that matter to current work
]

@dataclass
class VecMemoryRow:
    """Represents a row in the vec_memory table"""
    user_id: str
    namespace: Namespace
    doc_id: str
    chunk_id: int = 0
    content: Optional[str] = None
    summary: Optional[str] = None
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class VecMemoryCreate(BaseModel):
    """Pydantic model for creating vector memory entries"""
    user_id: str
    namespace: Namespace
    doc_id: str
    chunk_id: int = 0
    content: Optional[str] = None
    summary: Optional[str] = None
    text_for_embedding: Optional[str] = None  # Text to embed if embedding not provided
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}

class VecMemoryUpdate(BaseModel):
    """Pydantic model for updating vector memory entries"""
    content: Optional[str] = None
    summary: Optional[str] = None
    text_for_embedding: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Result from vector memory search"""
    id: str
    user_id: str
    namespace: Namespace
    doc_id: str
    chunk_id: int
    content: Optional[str]
    summary: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    similarity: float
    urgency: float
    final_score: float

class SearchOptions(BaseModel):
    """Options for vector memory search"""
    user_id: str
    namespaces: List[Namespace]
    query: str
    limit: int = 60
    course: Optional[str] = None
    due_start: Optional[str] = None  # ISO datetime string
    due_end: Optional[str] = None    # ISO datetime string
    min_similarity: float = 0.0

class MemoryStats(BaseModel):
    """Statistics about a user's memory system"""
    total_entries: int
    entries_by_namespace: Dict[str, int]
    oldest_entry: Optional[datetime]
    newest_entry: Optional[datetime]
    total_size_bytes: int

# Ingestion-specific types

@dataclass
class Assignment:
    """Canvas assignment for ingestion"""
    id: str
    title: str
    description: str
    course: str
    due_at: str
    effort_min: Optional[int] = None
    priority: Optional[int] = None
    url: Optional[str] = None

@dataclass
class CalendarEvent:
    """Calendar event for ingestion"""
    id: str
    title: str
    description: Optional[str]
    start_time: str
    end_time: str
    location: Optional[str] = None
    calendar_source: str = "google"

@dataclass
class EmailThread:
    """Email thread for ingestion"""
    id: str
    subject: str
    participants: List[str]
    messages: List[Dict[str, Any]]
    action_items: List[str] = field(default_factory=list)
    
@dataclass
class Document:
    """Document for ingestion (PDF, Notion page, etc.)"""
    id: str
    title: str
    content: str
    source: str
    course: Optional[str] = None
    url: Optional[str] = None

@dataclass
class UserPreference:
    """User preference for ingestion"""
    id: str
    category: str
    setting: str
    value: Union[str, int, bool, Dict[str, Any]]
    description: Optional[str] = None

@dataclass
class WeeklyProfileSnapshot:
    """Weekly behavior profile for ingestion"""
    user_id: str
    week_start: str
    on_time_rate: float
    avg_study_block_min: int
    preferred_start_local: str
    preferred_days: List[str]
    total_study_minutes: int
    tasks_completed: int
    tasks_planned: int