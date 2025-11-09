"""
Data models and enums for schedule quality analysis.

Defines quality dimensions, factors, and analysis result structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from ...schemas.enhanced_results import ConstraintViolation, ConstraintType


class QualityDimension(Enum):
    """Different dimensions of schedule quality assessment."""
    COVERAGE = "coverage"                   # How many tasks get scheduled
    EFFICIENCY = "efficiency"               # Time utilization and productivity
    SATISFACTION = "satisfaction"           # Meeting preferences and constraints
    BALANCE = "balance"                     # Workload distribution and sustainability
    STABILITY = "stability"                 # Robustness to changes
    USABILITY = "usability"                 # Practical implementation ease


@dataclass
class QualityFactor:
    """Individual quality factor with detailed assessment."""
    name: str
    dimension: QualityDimension
    score: float  # 0.0 to 1.0
    weight: float = 1.0
    description: str = ""

    # Detailed breakdown
    contributing_elements: Dict[str, float] = field(default_factory=dict)
    issues_identified: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

    # Context
    optimal_value: Optional[float] = None
    actual_value: Optional[float] = None
    benchmark_comparison: Optional[str] = None


@dataclass
class QualityBreakdown:
    """Detailed breakdown of quality assessment."""
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    factor_scores: List[QualityFactor]

    # Key insights
    strengths: List[str]
    weaknesses: List[str]
    critical_issues: List[str]
    quick_wins: List[str]

    # Benchmarking
    percentile_ranking: Optional[float] = None  # Compared to historical schedules
    improvement_potential: float = 0.0  # How much better this could be


@dataclass
class TimeDistributionAnalysis:
    """Analysis of how time is distributed across the schedule."""
    total_scheduled_time: int  # minutes
    total_available_time: int  # minutes
    utilization_ratio: float

    # Time distribution patterns
    morning_allocation: float   # 0.0 to 1.0
    afternoon_allocation: float
    evening_allocation: float

    # Fragmentation analysis
    number_of_blocks: int
    average_block_size: float
    block_size_variance: float
    largest_continuous_block: int

    # Gap analysis
    total_gaps: int
    average_gap_size: float
    productive_gap_ratio: float  # Gaps that could be used productively

    # Rhythm analysis
    context_switches: int
    similar_task_clustering: float  # How well similar tasks are grouped
    energy_level_alignment: float  # How well tasks match energy patterns


@dataclass
class ConstraintComplianceAnalysis:
    """Analysis of constraint satisfaction and violations."""
    total_constraints: int
    satisfied_constraints: int
    violation_summary: Dict[ConstraintType, int]

    # Severity analysis
    critical_violations: List[ConstraintViolation]
    moderate_violations: List[ConstraintViolation]
    minor_violations: List[ConstraintViolation]

    # Impact assessment
    user_impact_score: float  # How much violations affect user experience
    feasibility_impact: float  # How much violations affect feasibility

    # Resolution analysis
    easily_resolvable: List[str]  # Violation IDs that are easy to fix
    requires_tradeoffs: List[str]  # Violations requiring significant changes


@dataclass
class UserExperienceAnalysis:
    """Analysis of user experience aspects of the schedule."""
    cognitive_load_score: float  # 0.0 (low) to 1.0 (high)
    stress_indicators: List[str]
    flow_opportunities: int  # Number of potential flow states

    # Convenience factors
    travel_efficiency: float
    preparation_time_adequacy: float
    buffer_time_adequacy: float

    # Psychological factors
    variety_balance: float  # Mix of different types of activities
    accomplishment_potential: float  # Likelihood of feeling accomplished
    flexibility_preservation: float  # How much flexibility remains

    # Practical considerations
    implementation_difficulty: float
    required_discipline_level: float
    failure_recovery_options: int
