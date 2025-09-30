"""
Worker types and data structures
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Result of job execution"""
    success: bool
    user_id: str
    email: str
    timestamp: datetime
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None


@dataclass
class BriefingData:
    """Daily briefing data structure"""
    summary: str
    todays_tasks: list
    upcoming_events: list
    recommendations: list
    weather: Optional[Dict[str, Any]] = None
    generated_at: Optional[datetime] = None


@dataclass
class WeeklyPulseData:
    """Weekly pulse data structure"""
    completed_tasks: int
    total_tasks: int
    productivity_score: float
    weekly_goals: list
    achievements: list
    next_week_recommendations: list
    weekly_stats: Optional[Dict[str, Any]] = None
    generated_at: Optional[datetime] = None


@dataclass
class EmailData:
    """Email data structure"""
    to: str
    subject: str
    html: str
    from_email: Optional[str] = None
    template_id: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None