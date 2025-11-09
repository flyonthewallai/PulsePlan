"""
Main quality analyzer orchestrating all quality assessment components.

Coordinates time, constraint, and UX analysis to produce comprehensive
quality assessments of schedules.
"""

from typing import Dict, List, Optional, Tuple, Any

from ...core.domain import Task, Todo, ScheduleBlock, BusyEvent
from ...io.dto import ScheduleRequest
from ....core.utils.timezone_utils import TimezoneManager

from .models import (
    QualityDimension, QualityFactor, QualityBreakdown,
    TimeDistributionAnalysis, UserExperienceAnalysis
)
from .time_analyzer import TimeAnalyzer
from .constraint_analyzer import ConstraintAnalyzer
from .ux_analyzer import UXAnalyzer


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

        # Initialize component analyzers
        self.time_analyzer = TimeAnalyzer()
        self.constraint_analyzer = ConstraintAnalyzer()
        self.ux_analyzer = UXAnalyzer()

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

        # Analyze different quality dimensions using component analyzers
        coverage_factors = self.constraint_analyzer.analyze_coverage(
            blocks, all_tasks, unscheduled_tasks
        )
        efficiency_factors = self.constraint_analyzer.analyze_efficiency(
            blocks, busy_events, all_tasks
        )
        satisfaction_factors = self.constraint_analyzer.analyze_satisfaction(
            blocks, all_tasks, preferences
        )
        balance_factors = self.constraint_analyzer.analyze_balance(blocks, all_tasks)
        stability_factors = self.constraint_analyzer.analyze_stability(
            blocks, all_tasks, busy_events
        )
        usability_factors = self.ux_analyzer.analyze_usability(blocks, busy_events)

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
        return self.time_analyzer.analyze_time_distribution(blocks, busy_events)

    def analyze_user_experience(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> UserExperienceAnalysis:
        """Analyze user experience aspects of the schedule."""
        return self.ux_analyzer.analyze_user_experience(blocks, all_tasks, busy_events)

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
