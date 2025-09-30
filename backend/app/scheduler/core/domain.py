"""
Core domain models for the scheduler subsystem.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Literal
from enum import Enum


def _timezone_aware_now() -> datetime:
    """Get current time in timezone-aware format."""
    from ...core.utils.timezone_utils import get_timezone_manager
    return get_timezone_manager().ensure_timezone_aware(datetime.now())

Priority = Literal["low", "normal", "high", "critical"]
TaskKind = Literal["study", "assignment", "exam", "reading", "project", "hobby", "admin"]
EventSource = Literal["google", "microsoft", "pulse"]


@dataclass
class Task:
    """
    Represents a schedulable task with constraints and preferences.
    Tasks are atomic scheduling units (subtasks are flattened).
    """
    id: str
    user_id: str
    title: str
    kind: TaskKind
    estimated_minutes: int            # total effort required
    min_block_minutes: int            # minimal contiguous block
    max_block_minutes: int            # optional cap on long blocks
    deadline: Optional[datetime]
    earliest_start: Optional[datetime]
    preferred_windows: List[Dict] = field(default_factory=list)     # [{dow:0-6, start:"09:00", end:"12:00"}]
    avoid_windows: List[Dict] = field(default_factory=list)
    fixed: bool = False               # if true, must use provided window(s)
    parent_task_id: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)          # task ids that must complete first
    weight: float = 1.0               # value/importance baseline
    course_id: Optional[str] = None   # for fairness across courses
    must_finish_before: Optional[str] = None # "finish this before task_id"
    tags: List[str] = field(default_factory=list)                   # "deep_work", "shallow", etc.
    pinned_slots: List[Dict] = field(default_factory=list)          # hard assignment windows (rare)
    created_at: datetime = field(default_factory=_timezone_aware_now)
    updated_at: datetime = field(default_factory=_timezone_aware_now)

    def __post_init__(self):
        """Validate task constraints."""
        if self.min_block_minutes <= 0:
            raise ValueError("min_block_minutes must be positive")
        if self.estimated_minutes <= 0:
            raise ValueError("estimated_minutes must be positive")
        if self.max_block_minutes < self.min_block_minutes:
            raise ValueError("max_block_minutes cannot be less than min_block_minutes")
        if self.weight < 0:
            raise ValueError("weight cannot be negative")


@dataclass
class BusyEvent:
    """
    Represents an existing calendar event that constrains scheduling.
    """
    id: str
    source: EventSource
    start: datetime
    end: datetime
    title: str
    movable: bool = False             # pulse blocks may be movable within day
    hard: bool = True                 # hard = cannot overlap, ever
    location: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate event constraints."""
        if self.end <= self.start:
            raise ValueError("Event end must be after start")

    @property
    def duration_minutes(self) -> int:
        """Get event duration in minutes."""
        return int((self.end - self.start).total_seconds() / 60)


@dataclass
class Preferences:
    """
    User preferences for scheduling behavior and constraints.
    """
    timezone: str
    workday_start: str = "08:30"                # "HH:MM" format
    workday_end: str = "22:00"                  # "HH:MM" format
    break_every_minutes: int = 50               # Pomodoro-style breaks
    break_duration_minutes: int = 10
    deep_work_windows: List[Dict] = field(default_factory=list)     # high-focus windows
    no_study_windows: List[Dict] = field(default_factory=list)      # blocked time periods
    max_daily_effort_minutes: int = 480        # 8 hours default
    max_concurrent_courses: int = 3
    spacing_policy: Dict = field(default_factory=dict)              # e.g., {"exam":"2-3 spaced blocks/day"}
    latenight_penalty: float = 3.0
    morning_penalty: float = 1.0
    context_switch_penalty: float = 2.0
    min_gap_between_blocks: int = 15            # minutes to move between tasks/events
    session_granularity_minutes: int = 30      # 15 or 30 minute slots

    def __post_init__(self):
        """Validate preferences."""
        if self.break_every_minutes <= 0:
            raise ValueError("break_every_minutes must be positive")
        if self.break_duration_minutes <= 0:
            raise ValueError("break_duration_minutes must be positive")
        if self.max_daily_effort_minutes <= 0:
            raise ValueError("max_daily_effort_minutes must be positive")
        if self.session_granularity_minutes not in [15, 30]:
            raise ValueError("session_granularity_minutes must be 15 or 30")


@dataclass
class CompletionEvent:
    """
    Historical completion data for learning.
    """
    task_id: str
    scheduled_slot: datetime
    completed_at: Optional[datetime]
    skipped: bool = False
    delay_minutes: int = 0
    rescheduled_count: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ScheduleBlock:
    """
    A scheduled block of time assigned to a task.
    """
    task_id: str
    start: datetime
    end: datetime
    estimated_completion_probability: float = 0.0
    utility_score: float = 0.0
    penalties_applied: Dict = field(default_factory=dict)
    alternatives: List[Dict] = field(default_factory=list)  # top alternatives considered

    @property
    def duration_minutes(self) -> int:
        """Get block duration in minutes."""
        return int((self.end - self.start).total_seconds() / 60)


@dataclass
class ScheduleSolution:
    """
    Complete solution from the optimizer.
    """
    feasible: bool
    blocks: List[ScheduleBlock]
    objective_value: float = 0.0
    solve_time_ms: int = 0
    solver_status: str = "unknown"
    total_scheduled_minutes: int = 0
    unscheduled_tasks: List[str] = field(default_factory=list)
    diagnostics: Dict = field(default_factory=dict)
    explanations: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Calculate derived metrics."""
        self.total_scheduled_minutes = sum(block.duration_minutes for block in self.blocks)


class SchedulerStatus(Enum):
    """Scheduler execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class SchedulerRun:
    """
    Metadata about a scheduler execution.
    """
    id: str
    user_id: str
    horizon_days: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: SchedulerStatus = SchedulerStatus.PENDING
    feasible: bool = False
    objective_value: float = 0.0
    config: Dict = field(default_factory=dict)
    weights: Dict = field(default_factory=dict)
    diagnostics: Dict = field(default_factory=dict)
    error_message: Optional[str] = None


TodoPriority = Literal["low", "medium", "high"]
TodoStatus = Literal["pending", "completed", "archived"]


@dataclass
class Todo:
    """
    Represents a lightweight todo item for quick task capture.
    Simpler than Task with focus on rapid CRUD operations.
    """
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: TodoPriority = "medium"
    status: TodoStatus = "pending"
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_timezone_aware_now)
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_timezone_aware_now)

    def __post_init__(self):
        """Validate todo constraints."""
        if not self.title or not self.title.strip():
            raise ValueError("Todo title cannot be empty")
        if len(self.title) > 500:
            raise ValueError("Todo title cannot exceed 500 characters")
        if self.description and len(self.description) > 2000:
            raise ValueError("Todo description cannot exceed 2000 characters")
        
        # Auto-set completed_at when marking as completed
        if self.completed and not self.completed_at:
            self.completed_at = _timezone_aware_now()
        elif not self.completed:
            self.completed_at = None
            
        # Auto-update status based on completed flag
        if self.completed and self.status == "pending":
            self.status = "completed"
        elif not self.completed and self.status == "completed":
            self.status = "pending"

    def mark_completed(self) -> None:
        """Mark todo as completed with timestamp."""
        self.completed = True
        self.status = "completed"
        self.completed_at = _timezone_aware_now()
        self.updated_at = _timezone_aware_now()

    def mark_pending(self) -> None:
        """Mark todo as pending."""
        self.completed = False
        self.status = "pending"
        self.completed_at = None
        self.updated_at = _timezone_aware_now()

    def archive(self) -> None:
        """Archive the todo."""
        self.status = "archived"
        self.updated_at = _timezone_aware_now()

    def to_dict(self) -> Dict:
        """Convert todo to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat()
        }
