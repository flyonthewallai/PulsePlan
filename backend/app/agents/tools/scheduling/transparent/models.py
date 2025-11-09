"""
Data models and enums for transparent scheduling system
"""
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    """Task priority levels"""
    URGENT = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class SchedulingDecision(Enum):
    """Types of scheduling decisions that can be made"""
    OPTIMAL_PLACEMENT = "optimal_placement"
    CONFLICT_RESOLVED = "conflict_resolved"
    PREFERENCE_FLEXED = "preference_flexed"
    CONSTRAINT_VIOLATED = "constraint_violated"
    NO_SLOT_FOUND = "no_slot_found"


@dataclass
class ScheduleExplanation:
    """Detailed explanation of scheduling decisions"""
    decision_type: SchedulingDecision
    reason: str
    confidence_score: float  # 0.0 to 1.0
    tradeoffs: List[str]
    alternatives_considered: List[str]
    constraints_applied: List[str]
    preferences_honored: List[str]
    preferences_flexed: List[str]


@dataclass
class ScheduleBlock:
    """A scheduled time block with full transparency"""
    id: str
    title: str
    type: str  # 'task', 'meeting', 'focus', 'break'
    priority: Priority
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    explanation: ScheduleExplanation
    user_editable: bool = True
    auto_reschedulable: bool = True


@dataclass
class UserPreferences:
    """Comprehensive user preferences with hard/soft distinction"""
    # Hard constraints - never violate without explicit user override
    hard_constraints: Dict[str, Any]

    # Soft preferences - can be flexed with explanation
    soft_preferences: Dict[str, Any]

    # Learning weights from historical behavior
    behavioral_weights: Dict[str, float]


@dataclass
class SchedulingResult:
    """Complete scheduling result with transparency"""
    success: bool
    schedule: List[ScheduleBlock]
    overall_explanation: str
    confidence_score: float
    preview_mode: bool
    requires_user_confirmation: bool
    unscheduled_tasks: List[Dict[str, Any]]
    scheduling_metrics: Dict[str, Any]
    suggested_preference_updates: List[str]
