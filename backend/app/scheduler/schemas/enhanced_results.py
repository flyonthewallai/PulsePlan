"""
Enhanced result schemas for comprehensive scheduling observability.

Provides rich scheduling insights, explanations, and quality metrics
for improved user understanding and debugging capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from ..core.domain import ScheduleBlock, ScheduleSolution


class ScheduleQuality(Enum):
    """Schedule quality assessment levels."""
    EXCELLENT = "excellent"    # 90%+ tasks scheduled, optimal timing
    GOOD = "good"             # 80%+ tasks scheduled, good timing
    ACCEPTABLE = "acceptable"  # 70%+ tasks scheduled, reasonable timing
    POOR = "poor"             # 50%+ tasks scheduled, suboptimal timing
    FAILED = "failed"         # <50% tasks scheduled


class ConstraintType(Enum):
    """Types of scheduling constraints."""
    DEADLINE = "deadline"
    AVAILABILITY = "availability"
    PREREQUISITE = "prerequisite"
    RESOURCE = "resource"
    PREFERENCE = "preference"
    CONFLICT = "conflict"


class DecisionReason(Enum):
    """Reasons for scheduling decisions."""
    OPTIMAL_TIMING = "optimal_timing"
    DEADLINE_PRESSURE = "deadline_pressure"
    AVAILABILITY_LIMITED = "availability_limited"
    PREREQUISITE_BLOCKING = "prerequisite_blocking"
    PREFERENCE_MATCH = "preference_match"
    CONFLICT_AVOIDANCE = "conflict_avoidance"
    RESOURCE_CONSTRAINT = "resource_constraint"
    FALLBACK_CHOICE = "fallback_choice"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation in the schedule."""
    constraint_type: ConstraintType
    task_id: str
    severity: float  # 0.0 to 1.0
    description: str
    suggested_fix: Optional[str] = None
    impact_score: float = 0.0


@dataclass
class SchedulingDecision:
    """Detailed information about a scheduling decision."""
    task_id: str
    decision_type: str  # "scheduled", "unscheduled", "moved"
    reason: DecisionReason
    confidence: float  # 0.0 to 1.0
    alternatives_considered: int
    explanation: str
    factors: Dict[str, float] = field(default_factory=dict)  # Contributing factors
    trade_offs: List[str] = field(default_factory=list)


@dataclass
class QualityMetrics:
    """Comprehensive quality assessment of the schedule."""
    overall_quality: ScheduleQuality
    quality_score: float  # 0.0 to 1.0

    # Coverage metrics
    tasks_scheduled_ratio: float
    time_utilization_ratio: float
    preference_satisfaction_ratio: float

    # Constraint satisfaction
    deadline_satisfaction_ratio: float
    hard_constraint_violations: int
    soft_constraint_violations: int

    # Optimization metrics
    objective_value: float
    optimization_efficiency: float  # How close to theoretical optimum

    # User experience metrics
    schedule_fragmentation: float  # 0.0 = well consolidated, 1.0 = highly fragmented
    context_switch_penalty: float
    workload_balance_score: float

    # Confidence and reliability
    solution_confidence: float
    stability_score: float  # How likely the schedule is to remain stable

    # Detailed breakdowns
    constraint_violations: List[ConstraintViolation] = field(default_factory=list)
    quality_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class AlternativeSolution:
    """Alternative scheduling solution with trade-offs."""
    solution_id: str
    blocks: List[ScheduleBlock]
    quality_metrics: QualityMetrics
    trade_off_description: str
    scenarios: List[str] = field(default_factory=list)  # When this might be better

    # Comparison with main solution
    better_at: List[str] = field(default_factory=list)  # Areas where this is better
    worse_at: List[str] = field(default_factory=list)   # Areas where this is worse


@dataclass
class ScheduleExplanations:
    """Human-readable explanations for scheduling decisions."""
    summary: str
    key_decisions: List[SchedulingDecision]

    # Why certain tasks were scheduled when/where they were
    scheduling_rationale: Dict[str, str]  # task_id -> explanation

    # Why certain tasks couldn't be scheduled
    unscheduled_reasons: Dict[str, str]   # task_id -> reason

    # Key factors that influenced the schedule
    dominant_factors: List[str]

    # Recommendations for improvement
    recommendations: List[str]

    # Potential issues and warnings
    warnings: List[str] = field(default_factory=list)


@dataclass
class OptimizationInsights:
    """Insights into the optimization process."""
    solver_used: str
    solve_time_ms: int
    iterations: int
    convergence_status: str

    # Search space exploration
    solutions_explored: int
    local_optima_found: int

    # Constraint analysis
    active_constraints: List[str]
    binding_constraints: List[str]  # Constraints that limit optimization
    relaxable_constraints: List[str]  # Constraints that could be relaxed for better solutions

    # Performance bottlenecks
    optimization_bottlenecks: List[str]

    # Model statistics
    variables_count: int
    constraints_count: int
    model_complexity_score: float


@dataclass
class PerformanceSummary:
    """Summary of scheduling performance metrics."""
    total_time_ms: int
    phase_timings: Dict[str, int]  # phase_name -> time_ms

    # Component performance
    data_loading_ms: int
    ml_inference_ms: int
    optimization_ms: int
    post_processing_ms: int

    # Resource usage
    peak_memory_mb: float
    cpu_utilization: float

    # Efficiency metrics
    throughput_tasks_per_second: float
    latency_per_task_ms: float


@dataclass
class DetailedDiagnostics:
    """Comprehensive diagnostic information."""
    optimization_insights: OptimizationInsights
    performance_summary: PerformanceSummary

    # Data quality
    input_data_quality: Dict[str, float]  # Completeness, accuracy, etc.
    feature_importance: Dict[str, float]  # ML feature importance scores

    # Model performance
    ml_model_accuracy: Optional[float]
    prediction_confidence: Dict[str, float]  # task_id -> confidence

    # System state
    system_load: float
    concurrent_requests: int
    cache_hit_rate: float

    # Debug information
    debug_logs: List[str] = field(default_factory=list)
    intermediate_solutions: List[Dict] = field(default_factory=list)


@dataclass
class EnhancedScheduleSolution:
    """
    Comprehensive scheduling solution with full observability.

    Extends the basic ScheduleSolution with detailed insights,
    explanations, alternatives, and quality metrics.
    """
    # Core solution (from existing ScheduleSolution) - no defaults
    feasible: bool
    blocks: List[ScheduleBlock]
    objective_value: float
    solve_time_ms: int
    solver_status: str
    total_scheduled_minutes: int
    unscheduled_tasks: List[str]

    # Enhanced observability - no defaults
    trace_id: str
    quality_metrics: QualityMetrics
    explanations: ScheduleExplanations
    diagnostics: DetailedDiagnostics

    # Fields with defaults come last
    solution_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    alternatives: List[AlternativeSolution] = field(default_factory=list)
    user_preferences_applied: Dict[str, Any] = field(default_factory=dict)
    customizations: Dict[str, Any] = field(default_factory=dict)

    def to_basic_solution(self) -> ScheduleSolution:
        """Convert to basic ScheduleSolution for backwards compatibility."""
        return ScheduleSolution(
            feasible=self.feasible,
            blocks=self.blocks,
            objective_value=self.objective_value,
            solve_time_ms=self.solve_time_ms,
            solver_status=self.solver_status,
            total_scheduled_minutes=self.total_scheduled_minutes,
            unscheduled_tasks=self.unscheduled_tasks,
            diagnostics={"trace_id": self.trace_id}
        )

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get concise quality summary for API responses."""
        return {
            "overall_quality": self.quality_metrics.overall_quality.value,
            "quality_score": self.quality_metrics.quality_score,
            "tasks_scheduled": f"{self.quality_metrics.tasks_scheduled_ratio:.1%}",
            "deadline_satisfaction": f"{self.quality_metrics.deadline_satisfaction_ratio:.1%}",
            "confidence": self.quality_metrics.solution_confidence,
            "warnings_count": len(self.explanations.warnings)
        }

    def get_explanation_summary(self) -> Dict[str, Any]:
        """Get concise explanation for API responses."""
        return {
            "summary": self.explanations.summary,
            "key_decisions_count": len(self.explanations.key_decisions),
            "unscheduled_count": len(self.explanations.unscheduled_reasons),
            "recommendations_count": len(self.explanations.recommendations),
            "dominant_factors": self.explanations.dominant_factors[:3]  # Top 3
        }


@dataclass
class SchedulingInsightReport:
    """
    Comprehensive report for scheduling analysis and debugging.

    Provides detailed insights across multiple scheduling runs
    for trend analysis and system optimization.
    """
    # Required fields first
    user_id: str
    report_period: str
    solutions_analyzed: List[EnhancedScheduleSolution]
    average_quality_score: float
    quality_trend: str  # "improving", "stable", "declining"
    frequent_constraints: List[str]
    common_bottlenecks: List[str]
    recurring_issues: List[str]
    performance_trend: Dict[str, List[float]]  # metric -> values over time
    system_recommendations: List[str]
    user_recommendations: List[str]
    key_insights: List[str]
    optimization_opportunities: List[str]

    # Fields with defaults last
    generated_at: datetime = field(default_factory=datetime.now)


# Type aliases for complex nested structures
SchedulingContext = Dict[str, Any]
QualityBreakdown = Dict[str, Union[float, str, List[str]]]
DecisionMatrix = Dict[str, Dict[str, float]]