"""
Schedule quality analysis system for comprehensive assessment.

Provides detailed quality metrics, identifies improvement opportunities,
and generates actionable insights for schedule optimization.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import defaultdict, Counter

from ..core.domain import Task, Todo, ScheduleBlock, BusyEvent
from ..io.dto import ScheduleRequest
from ..schemas.enhanced_results import (
    QualityMetrics, ScheduleQuality, ConstraintViolation, ConstraintType
)
from ...core.utils.timezone_utils import TimezoneManager


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


class QualityAnalyzer:
    """Comprehensive schedule quality analyzer."""

    def __init__(self):
        self.timezone_manager = TimezoneManager()

        # Quality factor weights (can be customized per user)
        self.dimension_weights = {
            QualityDimension.COVERAGE: 0.25,
            QualityDimension.EFFICIENCY: 0.20,
            QualityDimension.SATISFACTION: 0.20,
            QualityDimension.BALANCE: 0.15,
            QualityDimension.STABILITY: 0.10,
            QualityDimension.USABILITY: 0.10
        }

    def analyze_quality(
        self,
        blocks: List[ScheduleBlock],
        request: ScheduleRequest,
        unscheduled_tasks: List[str],
        busy_events: List[BusyEvent],
        preferences: Dict[str, Any],
        constraints_analysis: Optional[Dict[str, Any]] = None
    ) -> QualityBreakdown:
        """Perform comprehensive quality analysis."""

        all_tasks = self._get_all_tasks(request)

        # Analyze different quality dimensions
        coverage_factors = self._analyze_coverage(blocks, all_tasks, unscheduled_tasks)
        efficiency_factors = self._analyze_efficiency(blocks, busy_events, all_tasks)
        satisfaction_factors = self._analyze_satisfaction(blocks, all_tasks, preferences)
        balance_factors = self._analyze_balance(blocks, all_tasks)
        stability_factors = self._analyze_stability(blocks, all_tasks, busy_events)
        usability_factors = self._analyze_usability(blocks, busy_events)

        # Combine all factors
        all_factors = (
            coverage_factors + efficiency_factors + satisfaction_factors +
            balance_factors + stability_factors + usability_factors
        )

        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(all_factors)

        # Calculate overall score
        overall_score = self._calculate_overall_score(dimension_scores)

        # Generate insights
        strengths, weaknesses, critical_issues, quick_wins = self._generate_insights(
            all_factors, dimension_scores
        )

        # Calculate improvement potential
        improvement_potential = self._calculate_improvement_potential(all_factors)

        return QualityBreakdown(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            factor_scores=all_factors,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_issues=critical_issues,
            quick_wins=quick_wins,
            improvement_potential=improvement_potential
        )

    def analyze_time_distribution(
        self,
        blocks: List[ScheduleBlock],
        busy_events: List[BusyEvent]
    ) -> TimeDistributionAnalysis:
        """Analyze time distribution patterns."""

        if not blocks:
            return TimeDistributionAnalysis(
                total_scheduled_time=0,
                total_available_time=0,
                utilization_ratio=0.0,
                morning_allocation=0.0,
                afternoon_allocation=0.0,
                evening_allocation=0.0,
                number_of_blocks=0,
                average_block_size=0.0,
                block_size_variance=0.0,
                largest_continuous_block=0,
                total_gaps=0,
                average_gap_size=0.0,
                productive_gap_ratio=0.0,
                context_switches=0,
                similar_task_clustering=0.0,
                energy_level_alignment=0.0
            )

        # Basic time calculations
        total_scheduled_time = sum(block.duration_minutes for block in blocks)

        # Estimate available time (assuming 16-hour day)
        total_available_time = 16 * 60  # 16 hours in minutes
        busy_time = sum(int((event.end - event.start).total_seconds() / 60) for event in busy_events)
        effective_available_time = total_available_time - busy_time
        utilization_ratio = total_scheduled_time / max(1, effective_available_time)

        # Time of day distribution
        morning_time = sum(
            block.duration_minutes for block in blocks
            if 6 <= block.start_time.hour < 12
        )
        afternoon_time = sum(
            block.duration_minutes for block in blocks
            if 12 <= block.start_time.hour < 18
        )
        evening_time = sum(
            block.duration_minutes for block in blocks
            if 18 <= block.start_time.hour < 22
        )

        morning_allocation = morning_time / max(1, total_scheduled_time)
        afternoon_allocation = afternoon_time / max(1, total_scheduled_time)
        evening_allocation = evening_time / max(1, total_scheduled_time)

        # Block analysis
        block_sizes = [block.duration_minutes for block in blocks]
        average_block_size = statistics.mean(block_sizes) if block_sizes else 0.0
        block_size_variance = statistics.variance(block_sizes) if len(block_sizes) > 1 else 0.0
        largest_continuous_block = max(block_sizes) if block_sizes else 0

        # Gap analysis
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        gaps = []
        for i in range(len(sorted_blocks) - 1):
            gap_start = sorted_blocks[i].end_time
            gap_end = sorted_blocks[i + 1].start_time
            gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
            if gap_minutes > 0:
                gaps.append(gap_minutes)

        total_gaps = len(gaps)
        average_gap_size = statistics.mean(gaps) if gaps else 0.0
        productive_gap_ratio = len([g for g in gaps if g >= 30]) / max(1, len(gaps))

        # Context switches (simplified)
        context_switches = max(0, len(blocks) - 1)

        # Task clustering (simplified - would need task categories)
        similar_task_clustering = 0.7  # Default placeholder

        # Energy alignment (simplified - would need user energy patterns)
        energy_level_alignment = 0.6  # Default placeholder

        return TimeDistributionAnalysis(
            total_scheduled_time=total_scheduled_time,
            total_available_time=effective_available_time,
            utilization_ratio=utilization_ratio,
            morning_allocation=morning_allocation,
            afternoon_allocation=afternoon_allocation,
            evening_allocation=evening_allocation,
            number_of_blocks=len(blocks),
            average_block_size=average_block_size,
            block_size_variance=block_size_variance,
            largest_continuous_block=largest_continuous_block,
            total_gaps=total_gaps,
            average_gap_size=average_gap_size,
            productive_gap_ratio=productive_gap_ratio,
            context_switches=context_switches,
            similar_task_clustering=similar_task_clustering,
            energy_level_alignment=energy_level_alignment
        )

    def analyze_user_experience(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> UserExperienceAnalysis:
        """Analyze user experience aspects of the schedule."""

        # Cognitive load assessment
        cognitive_load = self._assess_cognitive_load(blocks, all_tasks)

        # Stress indicators
        stress_indicators = self._identify_stress_indicators(blocks, all_tasks, busy_events)

        # Flow opportunities
        flow_opportunities = len([b for b in blocks if b.duration_minutes >= 90])

        # Convenience factors
        travel_efficiency = 0.8  # Placeholder - would analyze location changes
        preparation_time = self._assess_preparation_time(blocks, busy_events)
        buffer_time = self._assess_buffer_time(blocks, busy_events)

        # Psychological factors
        variety_balance = self._assess_variety_balance(blocks, all_tasks)
        accomplishment_potential = self._assess_accomplishment_potential(blocks, all_tasks)
        flexibility_preservation = self._assess_flexibility_preservation(blocks, busy_events)

        # Practical considerations
        implementation_difficulty = self._assess_implementation_difficulty(blocks)
        discipline_level = self._assess_required_discipline(blocks, all_tasks)
        recovery_options = self._count_recovery_options(blocks, busy_events)

        return UserExperienceAnalysis(
            cognitive_load_score=cognitive_load,
            stress_indicators=stress_indicators,
            flow_opportunities=flow_opportunities,
            travel_efficiency=travel_efficiency,
            preparation_time_adequacy=preparation_time,
            buffer_time_adequacy=buffer_time,
            variety_balance=variety_balance,
            accomplishment_potential=accomplishment_potential,
            flexibility_preservation=flexibility_preservation,
            implementation_difficulty=implementation_difficulty,
            required_discipline_level=discipline_level,
            failure_recovery_options=recovery_options
        )

    def _analyze_coverage(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        unscheduled_tasks: List[str]
    ) -> List[QualityFactor]:
        """Analyze task coverage quality factors."""
        factors = []

        if not all_tasks:
            return factors

        # Task completion ratio
        scheduled_count = len(all_tasks) - len(unscheduled_tasks)
        completion_ratio = scheduled_count / len(all_tasks)

        coverage_factor = QualityFactor(
            name="task_completion_ratio",
            dimension=QualityDimension.COVERAGE,
            score=completion_ratio,
            description=f"{scheduled_count}/{len(all_tasks)} tasks scheduled",
            actual_value=completion_ratio,
            optimal_value=1.0
        )

        if completion_ratio < 0.8:
            coverage_factor.issues_identified.append("Significant number of unscheduled tasks")
            coverage_factor.improvement_suggestions.append("Consider extending schedule horizon or reducing task scope")

        factors.append(coverage_factor)

        # Priority coverage
        high_priority_tasks = [t for t in all_tasks if getattr(t, 'priority', 3) >= 4]
        if high_priority_tasks:
            scheduled_high_priority = [
                t for t in high_priority_tasks
                if t.id not in unscheduled_tasks
            ]
            priority_coverage = len(scheduled_high_priority) / len(high_priority_tasks)

            priority_factor = QualityFactor(
                name="priority_task_coverage",
                dimension=QualityDimension.COVERAGE,
                score=priority_coverage,
                weight=1.5,  # Higher weight for priority tasks
                description=f"{len(scheduled_high_priority)}/{len(high_priority_tasks)} high-priority tasks scheduled",
                actual_value=priority_coverage,
                optimal_value=1.0
            )

            if priority_coverage < 0.9:
                priority_factor.issues_identified.append("High-priority tasks not fully covered")
                priority_factor.improvement_suggestions.append("Prioritize high-importance tasks for scheduling")

            factors.append(priority_factor)

        return factors

    def _analyze_efficiency(
        self,
        blocks: List[ScheduleBlock],
        busy_events: List[BusyEvent],
        all_tasks: List[Task]
    ) -> List[QualityFactor]:
        """Analyze scheduling efficiency factors."""
        factors = []

        if not blocks:
            return factors

        # Time utilization
        total_scheduled = sum(block.duration_minutes for block in blocks)
        total_available = 8 * 60  # Assume 8-hour workday
        busy_time = sum(int((event.end - event.start).total_seconds() / 60) for event in busy_events)
        effective_available = total_available - busy_time

        utilization = total_scheduled / max(1, effective_available)
        utilization_score = min(1.0, utilization)  # Cap at 1.0

        utilization_factor = QualityFactor(
            name="time_utilization",
            dimension=QualityDimension.EFFICIENCY,
            score=utilization_score,
            description=f"{utilization:.1%} of available time utilized",
            actual_value=utilization,
            optimal_value=0.8  # 80% is often optimal
        )

        if utilization < 0.5:
            utilization_factor.issues_identified.append("Low time utilization")
            utilization_factor.improvement_suggestions.append("Consider scheduling more tasks or longer blocks")
        elif utilization > 0.9:
            utilization_factor.issues_identified.append("Very high utilization may cause stress")
            utilization_factor.improvement_suggestions.append("Consider adding buffer time")

        factors.append(utilization_factor)

        # Block size efficiency
        block_sizes = [block.duration_minutes for block in blocks]
        avg_block_size = statistics.mean(block_sizes) if block_sizes else 0

        # Optimal block size is typically 60-90 minutes for deep work
        optimal_size = 75
        size_efficiency = 1.0 - abs(avg_block_size - optimal_size) / optimal_size
        size_efficiency = max(0.0, min(1.0, size_efficiency))

        block_size_factor = QualityFactor(
            name="block_size_efficiency",
            dimension=QualityDimension.EFFICIENCY,
            score=size_efficiency,
            description=f"Average block size: {avg_block_size:.1f} minutes",
            actual_value=avg_block_size,
            optimal_value=optimal_size
        )

        if avg_block_size < 30:
            block_size_factor.issues_identified.append("Blocks may be too short for effective work")
            block_size_factor.improvement_suggestions.append("Consider consolidating into longer blocks")
        elif avg_block_size > 120:
            block_size_factor.issues_identified.append("Blocks may be too long and tiring")
            block_size_factor.improvement_suggestions.append("Consider breaking into shorter sessions")

        factors.append(block_size_factor)

        return factors

    def _analyze_satisfaction(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        preferences: Dict[str, Any]
    ) -> List[QualityFactor]:
        """Analyze preference satisfaction factors."""
        factors = []

        # Time preference satisfaction
        preferred_times = preferences.get('preferred_times', {})
        if preferred_times and blocks:
            satisfaction_score = 0.0
            total_weight = 0.0

            for block in blocks:
                hour = block.start_time.hour
                task_id = block.task_id

                # Simple preference matching (would be more sophisticated in practice)
                if 'morning' in preferred_times and 6 <= hour < 12:
                    satisfaction_score += 1.0
                    total_weight += 1.0
                elif 'afternoon' in preferred_times and 12 <= hour < 18:
                    satisfaction_score += 1.0
                    total_weight += 1.0
                elif 'evening' in preferred_times and 18 <= hour < 22:
                    satisfaction_score += 1.0
                    total_weight += 1.0
                else:
                    total_weight += 1.0

            preference_satisfaction = satisfaction_score / max(1, total_weight)

            preference_factor = QualityFactor(
                name="time_preference_satisfaction",
                dimension=QualityDimension.SATISFACTION,
                score=preference_satisfaction,
                description=f"{preference_satisfaction:.1%} of blocks match time preferences",
                actual_value=preference_satisfaction,
                optimal_value=0.8
            )

            if preference_satisfaction < 0.5:
                preference_factor.issues_identified.append("Many tasks scheduled outside preferred times")
                preference_factor.improvement_suggestions.append("Consider adjusting constraints to better match preferences")

            factors.append(preference_factor)

        # Deadline satisfaction
        deadline_tasks = [t for t in all_tasks if hasattr(t, 'deadline') and t.deadline]
        if deadline_tasks and blocks:
            scheduled_task_ids = {block.task_id for block in blocks}
            deadline_violations = 0

            for task in deadline_tasks:
                if task.id in scheduled_task_ids:
                    # Find the block for this task
                    task_blocks = [b for b in blocks if b.task_id == task.id]
                    if task_blocks:
                        latest_block = max(task_blocks, key=lambda b: b.end_time)
                        if latest_block.end_time > task.deadline:
                            deadline_violations += 1

            deadline_satisfaction = 1.0 - (deadline_violations / len(deadline_tasks))

            deadline_factor = QualityFactor(
                name="deadline_satisfaction",
                dimension=QualityDimension.SATISFACTION,
                score=deadline_satisfaction,
                description=f"{deadline_violations} deadline violations out of {len(deadline_tasks)} deadline tasks",
                actual_value=deadline_satisfaction,
                optimal_value=1.0
            )

            if deadline_violations > 0:
                deadline_factor.issues_identified.append(f"{deadline_violations} tasks scheduled past their deadlines")
                deadline_factor.improvement_suggestions.append("Reschedule tasks to meet deadlines or extend deadlines")

            factors.append(deadline_factor)

        return factors

    def _analyze_balance(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> List[QualityFactor]:
        """Analyze workload balance factors."""
        factors = []

        if not blocks:
            return factors

        # Daily workload distribution
        daily_workload = defaultdict(int)
        for block in blocks:
            day = block.start_time.date()
            daily_workload[day] += block.duration_minutes

        if len(daily_workload) > 1:
            workloads = list(daily_workload.values())
            avg_workload = statistics.mean(workloads)
            workload_variance = statistics.variance(workloads) if len(workloads) > 1 else 0

            # Lower variance indicates better balance
            balance_score = 1.0 - min(1.0, workload_variance / (avg_workload ** 2))

            balance_factor = QualityFactor(
                name="daily_workload_balance",
                dimension=QualityDimension.BALANCE,
                score=balance_score,
                description=f"Workload varies by {workload_variance**0.5:.1f} minutes across days",
                actual_value=workload_variance**0.5,
                optimal_value=0.0
            )

            if workload_variance > (avg_workload * 0.5) ** 2:
                balance_factor.issues_identified.append("Uneven workload distribution across days")
                balance_factor.improvement_suggestions.append("Redistribute tasks for more even daily workload")

            factors.append(balance_factor)

        # Task priority balance
        scheduled_task_ids = {block.task_id for block in blocks}
        priority_distribution = Counter()

        for task in all_tasks:
            if task.id in scheduled_task_ids:
                priority = getattr(task, 'priority', 3)
                priority_distribution[priority] += 1

        if priority_distribution:
            # Check if there's a good mix of priorities
            priority_variety = len(priority_distribution) / 5.0  # Assuming 5 priority levels

            priority_factor = QualityFactor(
                name="priority_balance",
                dimension=QualityDimension.BALANCE,
                score=priority_variety,
                description=f"Tasks span {len(priority_distribution)} priority levels",
                actual_value=len(priority_distribution),
                optimal_value=3
            )

            factors.append(priority_factor)

        return factors

    def _analyze_stability(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> List[QualityFactor]:
        """Analyze schedule stability factors."""
        factors = []

        # Buffer time analysis
        total_buffer = 0
        for i, block in enumerate(sorted(blocks, key=lambda b: b.start_time)):
            if i < len(blocks) - 1:
                next_block = sorted(blocks, key=lambda b: b.start_time)[i + 1]
                gap = (next_block.start_time - block.end_time).total_seconds() / 60
                if gap > 0:
                    total_buffer += gap

        avg_buffer = total_buffer / max(1, len(blocks) - 1)

        # Optimal buffer is 15-30 minutes between blocks
        if avg_buffer < 15:
            buffer_score = avg_buffer / 15
        elif avg_buffer > 30:
            buffer_score = 1.0 - min(1.0, (avg_buffer - 30) / 30)
        else:
            buffer_score = 1.0

        buffer_factor = QualityFactor(
            name="buffer_time_adequacy",
            dimension=QualityDimension.STABILITY,
            score=buffer_score,
            description=f"Average {avg_buffer:.1f} minutes buffer between blocks",
            actual_value=avg_buffer,
            optimal_value=22.5  # Midpoint of 15-30 range
        )

        if avg_buffer < 10:
            buffer_factor.issues_identified.append("Insufficient buffer time between tasks")
            buffer_factor.improvement_suggestions.append("Add more buffer time to handle delays")

        factors.append(buffer_factor)

        return factors

    def _analyze_usability(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> List[QualityFactor]:
        """Analyze schedule usability factors."""
        factors = []

        if not blocks:
            return factors

        # Implementation complexity
        complexity_score = 1.0
        complexity_issues = []

        # Too many context switches reduce usability
        if len(blocks) > 8:
            complexity_score *= 0.8
            complexity_issues.append("High number of scheduled blocks may be overwhelming")

        # Very short blocks are harder to implement
        short_blocks = [b for b in blocks if b.duration_minutes < 30]
        if len(short_blocks) > len(blocks) * 0.3:
            complexity_score *= 0.7
            complexity_issues.append("Many short blocks may be difficult to execute effectively")

        complexity_factor = QualityFactor(
            name="implementation_complexity",
            dimension=QualityDimension.USABILITY,
            score=complexity_score,
            description=f"Schedule has {len(blocks)} blocks, {len(short_blocks)} under 30 minutes",
            issues_identified=complexity_issues
        )

        if complexity_score < 0.7:
            complexity_factor.improvement_suggestions.append("Simplify schedule by consolidating blocks")

        factors.append(complexity_factor)

        return factors

    def _calculate_dimension_scores(self, factors: List[QualityFactor]) -> Dict[QualityDimension, float]:
        """Calculate scores for each quality dimension."""
        dimension_scores = {}

        for dimension in QualityDimension:
            dimension_factors = [f for f in factors if f.dimension == dimension]
            if dimension_factors:
                weighted_sum = sum(f.score * f.weight for f in dimension_factors)
                total_weight = sum(f.weight for f in dimension_factors)
                dimension_scores[dimension] = weighted_sum / total_weight
            else:
                dimension_scores[dimension] = 0.5  # Neutral score if no factors

        return dimension_scores

    def _calculate_overall_score(self, dimension_scores: Dict[QualityDimension, float]) -> float:
        """Calculate overall quality score from dimension scores."""
        weighted_sum = sum(
            score * self.dimension_weights.get(dimension, 0.0)
            for dimension, score in dimension_scores.items()
        )
        return weighted_sum

    def _generate_insights(
        self,
        factors: List[QualityFactor],
        dimension_scores: Dict[QualityDimension, float]
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Generate quality insights and recommendations."""

        strengths = []
        weaknesses = []
        critical_issues = []
        quick_wins = []

        # Identify strengths (high-scoring factors)
        for factor in factors:
            if factor.score >= 0.8:
                strengths.append(f"Good {factor.name}: {factor.description}")

        # Identify weaknesses (low-scoring factors)
        for factor in factors:
            if factor.score < 0.6:
                weaknesses.append(f"Poor {factor.name}: {factor.description}")

                # Critical issues are low-scoring high-weight factors
                if factor.weight >= 1.5 and factor.score < 0.4:
                    critical_issues.extend(factor.issues_identified)

                # Quick wins are easily improvable factors
                if factor.improvement_suggestions and factor.score > 0.3:
                    quick_wins.extend(factor.improvement_suggestions)

        # Add dimension-level insights
        for dimension, score in dimension_scores.items():
            if score >= 0.8:
                strengths.append(f"Strong {dimension.value} performance")
            elif score < 0.5:
                weaknesses.append(f"Weak {dimension.value} performance")

        return strengths[:5], weaknesses[:5], critical_issues[:3], quick_wins[:5]

    def _calculate_improvement_potential(self, factors: List[QualityFactor]) -> float:
        """Calculate how much the schedule quality could potentially improve."""

        total_gap = 0.0
        total_weight = 0.0

        for factor in factors:
            gap = 1.0 - factor.score  # How far from perfect
            total_gap += gap * factor.weight
            total_weight += factor.weight

        return total_gap / max(1, total_weight)

    def _get_all_tasks(self, request: ScheduleRequest) -> List[Task]:
        """Extract all tasks from the scheduling request."""
        all_tasks = []

        if hasattr(request, 'tasks') and request.tasks:
            all_tasks.extend(request.tasks)

        if hasattr(request, 'todos') and request.todos:
            for todo in request.todos:
                task = Task(
                    id=todo.id,
                    title=todo.title,
                    description=todo.description or "",
                    duration_minutes=getattr(todo, 'estimated_duration_minutes', 30),
                    deadline=getattr(todo, 'due_date', None),
                    priority=getattr(todo, 'priority', 3),
                    created_at=todo.created_at,
                    updated_at=todo.updated_at,
                    user_id=todo.user_id
                )
                all_tasks.append(task)

        return all_tasks

    # Helper methods for user experience analysis
    def _assess_cognitive_load(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess cognitive load of the schedule."""
        # More blocks = higher cognitive load
        block_load = min(1.0, len(blocks) / 10.0)

        # Frequent context switches = higher load
        context_switches = max(0, len(blocks) - 1)
        switch_load = min(1.0, context_switches / 8.0)

        return (block_load + switch_load) / 2

    def _identify_stress_indicators(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> List[str]:
        """Identify potential stress indicators in the schedule."""
        indicators = []

        # Back-to-back scheduling
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            if gap < 5:
                indicators.append("Back-to-back scheduling with no breaks")
                break

        # Overloaded days
        daily_load = defaultdict(int)
        for block in blocks:
            daily_load[block.start_time.date()] += block.duration_minutes

        for day, minutes in daily_load.items():
            if minutes > 8 * 60:  # More than 8 hours
                indicators.append(f"Overloaded day: {day}")

        # Late evening work
        late_blocks = [b for b in blocks if b.start_time.hour >= 20]
        if late_blocks:
            indicators.append("Work scheduled late in the evening")

        return indicators

    def _assess_preparation_time(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> float:
        """Assess adequacy of preparation time."""
        # Simplified assessment - would be more sophisticated in practice
        return 0.7

    def _assess_buffer_time(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> float:
        """Assess adequacy of buffer time between activities."""
        # Calculate average gap between blocks
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        gaps = []

        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            gaps.append(gap)

        if not gaps:
            return 1.0

        avg_gap = statistics.mean(gaps)
        # 15-30 minutes is ideal buffer
        if 15 <= avg_gap <= 30:
            return 1.0
        elif avg_gap < 15:
            return avg_gap / 15
        else:
            return max(0.0, 1.0 - (avg_gap - 30) / 60)

    def _assess_variety_balance(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess variety and balance in scheduled activities."""
        # Simplified - would categorize tasks by type in practice
        return 0.6

    def _assess_accomplishment_potential(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess potential for feeling accomplished."""
        # More completed tasks = higher accomplishment potential
        completion_score = len(blocks) / max(1, len(all_tasks))

        # Longer blocks allow for deeper work and accomplishment
        avg_duration = statistics.mean([b.duration_minutes for b in blocks]) if blocks else 0
        depth_score = min(1.0, avg_duration / 90)  # 90 minutes for deep work

        return (completion_score + depth_score) / 2

    def _assess_flexibility_preservation(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> float:
        """Assess how much flexibility remains in the schedule."""
        total_scheduled = sum(b.duration_minutes for b in blocks)
        total_busy = sum(int((e.end - e.start).total_seconds() / 60) for e in busy_events)
        total_committed = total_scheduled + total_busy

        # Assume 16-hour waking day
        available_time = 16 * 60
        flexibility_ratio = 1.0 - (total_committed / available_time)

        return max(0.0, flexibility_ratio)

    def _assess_implementation_difficulty(self, blocks: List[ScheduleBlock]) -> float:
        """Assess how difficult the schedule would be to implement."""
        difficulty = 0.0

        # More blocks = higher difficulty
        difficulty += min(0.3, len(blocks) / 20)

        # Very short blocks = higher difficulty
        short_blocks = len([b for b in blocks if b.duration_minutes < 30])
        difficulty += min(0.3, short_blocks / len(blocks)) if blocks else 0

        # Tight scheduling = higher difficulty
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        tight_gaps = 0
        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            if gap < 10:
                tight_gaps += 1

        if blocks:
            difficulty += min(0.4, tight_gaps / (len(blocks) - 1)) if len(blocks) > 1 else 0

        return difficulty

    def _assess_required_discipline(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess level of discipline required to follow the schedule."""
        # More precise timing = higher discipline required
        precision_requirement = len(blocks) / 10.0

        # Early morning starts = higher discipline
        early_blocks = len([b for b in blocks if b.start_time.hour < 7])
        early_discipline = early_blocks / max(1, len(blocks))

        return min(1.0, (precision_requirement + early_discipline) / 2)

    def _count_recovery_options(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> int:
        """Count options for recovering if schedule goes off track."""
        # Simplified - count gaps that could be used for catch-up
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        recovery_options = 0

        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            if gap >= 30:  # 30+ minute gaps can be used for recovery
                recovery_options += 1

        return recovery_options


