"""
Data Transfer Objects (DTOs) for scheduler API boundaries.

Defines Pydantic schemas for request/response validation and serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ScheduleRequest(BaseModel):
    """Request schema for scheduling operations."""
    
    user_id: str = Field(..., description="User identifier")
    horizon_days: int = Field(default=7, ge=1, le=30, description="Scheduling horizon in days")
    dry_run: bool = Field(default=False, description="Preview mode without persistence")
    lock_existing: bool = Field(default=True, description="Preserve existing schedule blocks")
    job_id: Optional[str] = Field(None, description="Optional job identifier for tracking")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")
    
    @validator('horizon_days')
    def validate_horizon(cls, v):
        """Validate horizon is reasonable."""
        if v < 1 or v > 30:
            raise ValueError("Horizon must be between 1 and 30 days")
        return v


class ScheduleBlock(BaseModel):
    """Schema for a scheduled time block."""
    
    task_id: str = Field(..., description="Task identifier")
    title: str = Field(..., description="Task title for display")
    start: str = Field(..., description="Start time (ISO format)")
    end: str = Field(..., description="End time (ISO format)")
    provider: str = Field(default="pulse", description="Scheduling provider")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('start', 'end')
    def validate_datetime_format(cls, v):
        """Validate datetime strings are ISO format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("DateTime must be in ISO format")
        return v
    
    @property
    def duration_minutes(self) -> int:
        """Calculate block duration in minutes."""
        start_dt = datetime.fromisoformat(self.start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(self.end.replace('Z', '+00:00'))
        return int((end_dt - start_dt).total_seconds() / 60)


class ScheduleAlternative(BaseModel):
    """Alternative schedule option."""
    
    blocks: List[ScheduleBlock] = Field(..., description="Alternative schedule blocks")
    score: float = Field(..., description="Quality score for this alternative")
    description: str = Field(..., description="Human-readable description")


class ScheduleResponse(BaseModel):
    """Response schema for scheduling operations."""
    
    job_id: Optional[str] = Field(None, description="Job identifier")
    feasible: bool = Field(..., description="Whether a feasible schedule was found")
    blocks: List[ScheduleBlock] = Field(..., description="Scheduled time blocks")
    alternatives: Optional[List[ScheduleAlternative]] = Field(
        None, description="Alternative schedule options"
    )
    metrics: Dict[str, Any] = Field(..., description="Scheduling metrics and diagnostics")
    explanations: Dict[str, str] = Field(..., description="Human-readable explanations")
    
    @property
    def total_scheduled_minutes(self) -> int:
        """Calculate total scheduled time."""
        return sum(block.duration_minutes for block in self.blocks)
    
    @property
    def success(self) -> bool:
        """Whether scheduling was successful."""
        return self.feasible and len(self.blocks) > 0


class TaskUpdateRequest(BaseModel):
    """Request schema for updating task scheduling parameters."""
    
    task_id: str = Field(..., description="Task identifier")
    estimated_minutes: Optional[int] = Field(None, ge=1, description="Updated time estimate")
    min_block_minutes: Optional[int] = Field(None, ge=1, description="Updated minimum block size")
    max_block_minutes: Optional[int] = Field(None, ge=1, description="Updated maximum block size")
    deadline: Optional[datetime] = Field(None, description="Updated deadline")
    preferred_windows: Optional[List[Dict]] = Field(None, description="Updated preferred windows")
    avoid_windows: Optional[List[Dict]] = Field(None, description="Updated avoid windows")
    weight: Optional[float] = Field(None, ge=0, description="Updated importance weight")
    
    @validator('max_block_minutes')
    def validate_max_block(cls, v, values):
        """Ensure max block is at least min block."""
        min_block = values.get('min_block_minutes')
        if v is not None and min_block is not None and v < min_block:
            raise ValueError("max_block_minutes cannot be less than min_block_minutes")
        return v


class PreferencesUpdateRequest(BaseModel):
    """Request schema for updating user preferences."""
    
    user_id: str = Field(..., description="User identifier")
    workday_start: Optional[str] = Field(None, description="Workday start time (HH:MM)")
    workday_end: Optional[str] = Field(None, description="Workday end time (HH:MM)")
    max_daily_effort_minutes: Optional[int] = Field(None, ge=60, description="Daily effort limit")
    deep_work_windows: Optional[List[Dict]] = Field(None, description="Deep work time windows")
    no_study_windows: Optional[List[Dict]] = Field(None, description="Blocked time windows")
    session_granularity_minutes: Optional[int] = Field(None, description="Scheduling granularity")
    
    @validator('workday_start', 'workday_end')
    def validate_time_format(cls, v):
        """Validate time format."""
        if v is not None:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError("Time must be in HH:MM format")
        return v
    
    @validator('session_granularity_minutes')
    def validate_granularity(cls, v):
        """Validate granularity options."""
        if v is not None and v not in [15, 30]:
            raise ValueError("session_granularity_minutes must be 15 or 30")
        return v


class ScheduleJobStatus(BaseModel):
    """Status of a background scheduling job."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Job progress (0-1)")
    result: Optional[ScheduleResponse] = Field(None, description="Job result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class FeedbackRequest(BaseModel):
    """Request schema for user feedback on schedules."""
    
    user_id: str = Field(..., description="User identifier")
    schedule_job_id: Optional[str] = Field(None, description="Related schedule job")
    satisfaction_score: float = Field(..., ge=-1.0, le=1.0, description="Satisfaction (-1 to 1)")
    completed_tasks: List[str] = Field(default_factory=list, description="Completed task IDs")
    missed_tasks: List[str] = Field(default_factory=list, description="Missed task IDs")
    rescheduled_tasks: List[str] = Field(default_factory=list, description="User-rescheduled task IDs")
    comments: Optional[str] = Field(None, description="Optional feedback text")
    
    @validator('satisfaction_score')
    def validate_satisfaction(cls, v):
        """Validate satisfaction score range."""
        if v < -1.0 or v > 1.0:
            raise ValueError("satisfaction_score must be between -1.0 and 1.0")
        return v


class ModelMetrics(BaseModel):
    """Metrics for ML model performance."""
    
    model_type: str = Field(..., description="Type of model (completion, bandit)")
    user_id: str = Field(..., description="User identifier")
    accuracy: Optional[float] = Field(None, description="Model accuracy")
    precision: Optional[float] = Field(None, description="Model precision")
    recall: Optional[float] = Field(None, description="Model recall")
    training_samples: int = Field(default=0, description="Number of training samples")
    last_updated: datetime = Field(..., description="Last model update time")
    feature_importance: Optional[Dict[str, float]] = Field(
        None, description="Feature importance scores"
    )


class SchedulerHealth(BaseModel):
    """Health status of scheduler components."""
    
    status: str = Field(..., description="Overall status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component statuses")
    version: str = Field(..., description="Scheduler version")
    uptime_seconds: float = Field(..., description="Service uptime")
    last_schedule_time: Optional[datetime] = Field(None, description="Last successful schedule")
    
    @property
    def is_healthy(self) -> bool:
        """Whether all components are healthy."""
        return self.status == "healthy"


class DiagnosticsRequest(BaseModel):
    """Request for scheduler diagnostics."""
    
    user_id: str = Field(..., description="User identifier")
    include_model_metrics: bool = Field(default=False, description="Include ML model metrics")
    include_recent_runs: bool = Field(default=True, description="Include recent scheduling runs")
    days_back: int = Field(default=7, ge=1, le=30, description="Days of history to include")


class DiagnosticsResponse(BaseModel):
    """Response with scheduler diagnostics."""
    
    user_id: str = Field(..., description="User identifier")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    recent_runs: List[Dict[str, Any]] = Field(..., description="Recent scheduling runs")
    model_metrics: Optional[List[ModelMetrics]] = Field(None, description="ML model metrics")
    recommendations: List[str] = Field(..., description="Optimization recommendations")


class ConfigUpdateRequest(BaseModel):
    """Request to update scheduler configuration."""
    
    solver_time_limit_seconds: Optional[int] = Field(None, ge=1, le=300, description="Solver time limit")
    bandit_exploration_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Bandit exploration")
    default_weights: Optional[Dict[str, float]] = Field(None, description="Default penalty weights")
    feature_config: Optional[Dict[str, Any]] = Field(None, description="Feature extraction config")
    
    @validator('solver_time_limit_seconds')
    def validate_time_limit(cls, v):
        """Validate solver time limit."""
        if v is not None and (v < 1 or v > 300):
            raise ValueError("solver_time_limit_seconds must be between 1 and 300")
        return v
    
    @validator('bandit_exploration_rate')
    def validate_exploration_rate(cls, v):
        """Validate exploration rate."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("bandit_exploration_rate must be between 0.0 and 1.0")
        return v


# Utility functions for DTO validation and conversion

def validate_time_window(window: Dict) -> Dict:
    """Validate and normalize time window specification."""
    if not isinstance(window, dict):
        raise ValueError("Time window must be a dictionary")
    
    # Validate day of week
    dow = window.get('dow')
    if dow is not None:
        if not isinstance(dow, int) or dow < 0 or dow > 6:
            raise ValueError("dow must be an integer between 0 (Monday) and 6 (Sunday)")
    
    # Validate start/end times
    start_time = window.get('start')
    end_time = window.get('end')
    
    if start_time is not None:
        try:
            datetime.strptime(start_time, '%H:%M')
        except ValueError:
            raise ValueError("start time must be in HH:MM format")
    
    if end_time is not None:
        try:
            datetime.strptime(end_time, '%H:%M')
        except ValueError:
            raise ValueError("end time must be in HH:MM format")
    
    return window


def convert_schedule_blocks_to_response(
    blocks: List, task_lookup: Dict[str, Any]
) -> List[ScheduleBlock]:
    """Convert internal schedule blocks to response DTOs."""
    response_blocks = []
    
    for block in blocks:
        task = task_lookup.get(block.task_id, {})
        
        response_block = ScheduleBlock(
            task_id=block.task_id,
            title=task.get('title', 'Unknown Task'),
            start=block.start.isoformat(),
            end=block.end.isoformat(),
            metadata={
                'utility_score': getattr(block, 'utility_score', 0.0),
                'completion_probability': getattr(block, 'estimated_completion_probability', 0.7),
                'duration_minutes': block.duration_minutes,
                'task_kind': task.get('kind', 'unknown'),
                'course_id': task.get('course_id')
            }
        )
        response_blocks.append(response_block)
    
    return response_blocks


def normalize_datetime_strings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize datetime strings in API responses."""
    normalized = data.copy()
    
    for key, value in normalized.items():
        if isinstance(value, datetime):
            normalized[key] = value.isoformat()
        elif isinstance(value, dict):
            normalized[key] = normalize_datetime_strings(value)
        elif isinstance(value, list):
            normalized[key] = [
                normalize_datetime_strings(item) if isinstance(item, dict) else item
                for item in value
            ]
    
    return normalized