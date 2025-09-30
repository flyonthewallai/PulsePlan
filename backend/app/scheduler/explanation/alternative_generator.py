"""
Alternative solution generator for what-if scenario analysis.

Generates alternative scheduling solutions with different trade-offs
to help users understand scheduling options and make informed decisions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import copy
from collections import defaultdict

from ..core.domain import Task, Todo, ScheduleBlock, BusyEvent
from ..io.dto import ScheduleRequest
from ..schemas.enhanced_results import AlternativeSolution, QualityMetrics, ScheduleQuality
from ...core.utils.timezone_utils import TimezoneManager


class AlternativeStrategy(Enum):
    """Different strategies for generating alternative solutions."""
    DEADLINE_RELAXED = "deadline_relaxed"           # Relax some deadline constraints
    PREFERENCE_IGNORED = "preference_ignored"       # Ignore time preferences
    SHORTER_BLOCKS = "shorter_blocks"               # Use shorter time blocks
    LONGER_BLOCKS = "longer_blocks"                 # Use longer time blocks
    EARLY_BIRD = "early_bird"                       # Schedule everything earlier
    NIGHT_OWL = "night_owl"                         # Schedule everything later
    WEEKEND_INCLUDED = "weekend_included"           # Include weekend scheduling
    MINIMAL_FRAGMENTATION = "minimal_fragmentation" # Minimize context switching
    MAX_PRODUCTIVITY = "max_productivity"           # Schedule during peak hours
    FLEXIBLE_DURATION = "flexible_duration"         # Allow flexible task durations


@dataclass
class AlternativeParameters:
    """Parameters for generating an alternative solution."""
    strategy: AlternativeStrategy
    modifications: Dict[str, Any] = field(default_factory=dict)
    constraints_relaxed: List[str] = field(default_factory=list)
    constraints_added: List[str] = field(default_factory=list)
    optimization_weights: Dict[str, float] = field(default_factory=dict)

    # Strategy-specific parameters
    deadline_extension_days: int = 0
    time_block_size_modifier: float = 1.0  # Multiplier for block sizes
    time_shift_hours: int = 0
    include_weekends: bool = False
    max_context_switches: Optional[int] = None
    peak_hours: List[Tuple[int, int]] = field(default_factory=list)  # [(start_hour, end_hour)]


@dataclass
class AlternativeComparison:
    """Comparison between the main solution and an alternative."""
    # Required fields first
    main_solution_score: float
    alternative_solution_score: float
    improvement_areas: List[str]
    degradation_areas: List[str]
    trade_off_summary: str
    user_impact_rating: float  # -1.0 (much worse) to 1.0 (much better)
    effort_required: float     # 0.0 (no effort) to 1.0 (high effort)

    # Fields with defaults last
    metrics_comparison: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # metric -> (main, alt)


class AlternativeGenerator:
    """Generates alternative scheduling solutions with different trade-offs."""

    def __init__(self):
        self.timezone_manager = TimezoneManager()

    def generate_alternatives(
        self,
        main_solution: Any,  # EnhancedScheduleSolution
        request: ScheduleRequest,
        busy_events: List[BusyEvent],
        preferences: Dict[str, Any],
        max_alternatives: int = 3
    ) -> List[AlternativeSolution]:
        """Generate alternative solutions with different trade-offs."""

        alternatives = []

        # Define strategies to try
        strategies_to_try = self._select_strategies(main_solution, request, preferences)

        for strategy in strategies_to_try[:max_alternatives]:
            alternative = self._generate_alternative_with_strategy(
                main_solution, request, busy_events, preferences, strategy
            )
            if alternative:
                alternatives.append(alternative)

        return alternatives

    def _select_strategies(
        self,
        main_solution: Any,
        request: ScheduleRequest,
        preferences: Dict[str, Any]
    ) -> List[AlternativeStrategy]:
        """Select which alternative strategies to try based on the main solution."""
        strategies = []

        # Analyze main solution to determine best alternatives
        if hasattr(main_solution, 'quality_metrics'):
            quality = main_solution.quality_metrics

            # If deadline satisfaction is low, try deadline relaxation
            if quality.deadline_satisfaction_ratio < 0.8:
                strategies.append(AlternativeStrategy.DEADLINE_RELAXED)

            # If preference satisfaction is low, try ignoring preferences
            if quality.preference_satisfaction_ratio < 0.6:
                strategies.append(AlternativeStrategy.PREFERENCE_IGNORED)

            # If schedule is fragmented, try consolidation
            if quality.schedule_fragmentation > 0.6:
                strategies.append(AlternativeStrategy.MINIMAL_FRAGMENTATION)

            # If utilization is low, try different block sizes
            if quality.time_utilization_ratio < 0.5:
                strategies.append(AlternativeStrategy.SHORTER_BLOCKS)

        # Default strategies if none selected
        if not strategies:
            strategies = [
                AlternativeStrategy.PREFERENCE_IGNORED,
                AlternativeStrategy.SHORTER_BLOCKS,
                AlternativeStrategy.MINIMAL_FRAGMENTATION
            ]

        return strategies

    def _generate_alternative_with_strategy(
        self,
        main_solution: Any,
        request: ScheduleRequest,
        busy_events: List[BusyEvent],
        preferences: Dict[str, Any],
        strategy: AlternativeStrategy
    ) -> Optional[AlternativeSolution]:
        """Generate an alternative solution using a specific strategy."""

        # Create modified request and preferences based on strategy
        modified_request = copy.deepcopy(request)
        modified_preferences = copy.deepcopy(preferences)
        parameters = self._get_strategy_parameters(strategy, main_solution)

        # Apply strategy modifications
        self._apply_strategy_modifications(
            modified_request, modified_preferences, busy_events, parameters
        )

        # Generate alternative solution (simplified simulation)
        alternative_blocks = self._simulate_alternative_scheduling(
            modified_request, busy_events, modified_preferences, parameters
        )

        if not alternative_blocks:
            return None

        # Calculate quality metrics for alternative
        alternative_quality = self._calculate_alternative_quality(
            alternative_blocks, modified_request, parameters
        )

        # Compare with main solution
        comparison = self._compare_solutions(main_solution, alternative_blocks, alternative_quality)

        # Generate trade-off description
        trade_off_description = self._generate_trade_off_description(strategy, comparison)

        # Determine scenarios where this alternative is better
        better_scenarios = self._identify_better_scenarios(strategy, comparison)

        return AlternativeSolution(
            solution_id=f"alt_{strategy.value}",
            blocks=alternative_blocks,
            quality_metrics=alternative_quality,
            trade_off_description=trade_off_description,
            scenarios=better_scenarios,
            better_at=comparison.improvement_areas,
            worse_at=comparison.degradation_areas
        )

    def _get_strategy_parameters(self, strategy: AlternativeStrategy, main_solution: Any) -> AlternativeParameters:
        """Get parameters for a specific alternative strategy."""

        base_params = AlternativeParameters(strategy=strategy)

        if strategy == AlternativeStrategy.DEADLINE_RELAXED:
            base_params.deadline_extension_days = 2
            base_params.constraints_relaxed = ["strict_deadlines"]
            base_params.modifications = {"deadline_flexibility": 0.2}

        elif strategy == AlternativeStrategy.PREFERENCE_IGNORED:
            base_params.constraints_relaxed = ["time_preferences"]
            base_params.modifications = {"ignore_preferences": True}

        elif strategy == AlternativeStrategy.SHORTER_BLOCKS:
            base_params.time_block_size_modifier = 0.5
            base_params.modifications = {"min_block_size": 15}

        elif strategy == AlternativeStrategy.LONGER_BLOCKS:
            base_params.time_block_size_modifier = 2.0
            base_params.modifications = {"min_block_size": 60}

        elif strategy == AlternativeStrategy.EARLY_BIRD:
            base_params.time_shift_hours = -2
            base_params.peak_hours = [(6, 10), (14, 16)]

        elif strategy == AlternativeStrategy.NIGHT_OWL:
            base_params.time_shift_hours = 3
            base_params.peak_hours = [(18, 22)]

        elif strategy == AlternativeStrategy.WEEKEND_INCLUDED:
            base_params.include_weekends = True
            base_params.modifications = {"weekend_scheduling": True}

        elif strategy == AlternativeStrategy.MINIMAL_FRAGMENTATION:
            base_params.max_context_switches = 3
            base_params.optimization_weights = {"fragmentation_penalty": 2.0}

        elif strategy == AlternativeStrategy.MAX_PRODUCTIVITY:
            base_params.peak_hours = [(9, 11), (14, 16)]
            base_params.optimization_weights = {"peak_time_bonus": 1.5}

        elif strategy == AlternativeStrategy.FLEXIBLE_DURATION:
            base_params.modifications = {"duration_flexibility": 0.3}

        return base_params

    def _apply_strategy_modifications(
        self,
        request: ScheduleRequest,
        preferences: Dict[str, Any],
        busy_events: List[BusyEvent],
        parameters: AlternativeParameters
    ):
        """Apply strategy-specific modifications to the scheduling request."""

        if parameters.strategy == AlternativeStrategy.DEADLINE_RELAXED:
            # Extend deadlines for tasks
            for task in self._get_all_tasks(request):
                if task.deadline:
                    task.deadline += timedelta(days=parameters.deadline_extension_days)

        elif parameters.strategy == AlternativeStrategy.PREFERENCE_IGNORED:
            # Clear time preferences
            preferences.pop('preferred_times', None)
            preferences.pop('avoid_times', None)

        elif parameters.strategy == AlternativeStrategy.SHORTER_BLOCKS:
            # Modify task durations to prefer shorter blocks
            for task in self._get_all_tasks(request):
                if hasattr(task, 'max_block_minutes'):
                    task.max_block_minutes = min(
                        task.max_block_minutes or 120,
                        int(60 * parameters.time_block_size_modifier)
                    )

        elif parameters.strategy == AlternativeStrategy.WEEKEND_INCLUDED:
            # Remove weekend restrictions from busy events (conceptually)
            # In practice, this would be handled by the scheduler
            preferences['include_weekends'] = True

        # Apply other modifications as needed

    def _simulate_alternative_scheduling(
        self,
        request: ScheduleRequest,
        busy_events: List[BusyEvent],
        preferences: Dict[str, Any],
        parameters: AlternativeParameters
    ) -> List[ScheduleBlock]:
        """Simulate alternative scheduling (simplified for demonstration)."""

        tasks = self._get_all_tasks(request)
        if not tasks:
            return []

        # Simplified alternative scheduling simulation
        alternative_blocks = []
        current_time = self.timezone_manager.get_user_now().replace(hour=9, minute=0, second=0, microsecond=0)

        for i, task in enumerate(tasks[:5]):  # Limit for simulation
            # Calculate block duration based on strategy
            duration = task.duration_minutes
            if parameters.time_block_size_modifier != 1.0:
                duration = int(duration * parameters.time_block_size_modifier)
                duration = max(15, min(240, duration))  # Clamp to reasonable range

            # Apply time shift
            if parameters.time_shift_hours != 0:
                current_time += timedelta(hours=parameters.time_shift_hours)

            # Create block
            end_time = current_time + timedelta(minutes=duration)

            block = ScheduleBlock(
                task_id=task.id,
                start_time=current_time,
                end_time=end_time,
                duration_minutes=duration,
                block_type="work",
                metadata={
                    "alternative_strategy": parameters.strategy.value,
                    "original_duration": task.duration_minutes
                }
            )

            alternative_blocks.append(block)

            # Move to next time slot (with some gap)
            gap_minutes = 30 if parameters.strategy == AlternativeStrategy.MINIMAL_FRAGMENTATION else 15
            current_time = end_time + timedelta(minutes=gap_minutes)

        return alternative_blocks

    def _calculate_alternative_quality(
        self,
        blocks: List[ScheduleBlock],
        request: ScheduleRequest,
        parameters: AlternativeParameters
    ) -> QualityMetrics:
        """Calculate quality metrics for an alternative solution."""

        tasks = self._get_all_tasks(request)
        scheduled_task_ids = {block.task_id for block in blocks}

        # Basic metrics calculation
        tasks_scheduled_ratio = len(scheduled_task_ids) / max(1, len(tasks))
        total_scheduled_minutes = sum(block.duration_minutes for block in blocks)

        # Estimate other metrics based on strategy
        deadline_satisfaction = 0.8  # Default
        preference_satisfaction = 0.5  # Default

        if parameters.strategy == AlternativeStrategy.DEADLINE_RELAXED:
            deadline_satisfaction = 0.95
        elif parameters.strategy == AlternativeStrategy.PREFERENCE_IGNORED:
            preference_satisfaction = 0.1

        # Calculate fragmentation
        fragmentation = len(blocks) / max(1, len(blocks)) * 0.1  # Simplified

        if parameters.strategy == AlternativeStrategy.MINIMAL_FRAGMENTATION:
            fragmentation *= 0.3  # Much lower fragmentation

        # Determine overall quality
        quality_score = (
            tasks_scheduled_ratio * 0.4 +
            deadline_satisfaction * 0.3 +
            preference_satisfaction * 0.2 +
            (1.0 - fragmentation) * 0.1
        )

        if quality_score >= 0.9:
            overall_quality = ScheduleQuality.EXCELLENT
        elif quality_score >= 0.8:
            overall_quality = ScheduleQuality.GOOD
        elif quality_score >= 0.7:
            overall_quality = ScheduleQuality.ACCEPTABLE
        elif quality_score >= 0.5:
            overall_quality = ScheduleQuality.POOR
        else:
            overall_quality = ScheduleQuality.FAILED

        return QualityMetrics(
            overall_quality=overall_quality,
            quality_score=quality_score,
            tasks_scheduled_ratio=tasks_scheduled_ratio,
            time_utilization_ratio=min(1.0, total_scheduled_minutes / (8 * 60)),  # 8 hours
            preference_satisfaction_ratio=preference_satisfaction,
            deadline_satisfaction_ratio=deadline_satisfaction,
            hard_constraint_violations=0,
            soft_constraint_violations=0,
            objective_value=quality_score * 100,
            optimization_efficiency=0.8,
            schedule_fragmentation=fragmentation,
            context_switch_penalty=fragmentation * 0.2,
            workload_balance_score=0.8,
            solution_confidence=0.7,
            stability_score=0.8
        )

    def _compare_solutions(
        self,
        main_solution: Any,
        alternative_blocks: List[ScheduleBlock],
        alternative_quality: QualityMetrics
    ) -> AlternativeComparison:
        """Compare main solution with alternative."""

        main_quality = getattr(main_solution, 'quality_metrics', None)
        if not main_quality:
            # Create dummy metrics for comparison
            main_quality = QualityMetrics(
                overall_quality=ScheduleQuality.GOOD,
                quality_score=0.7,
                tasks_scheduled_ratio=0.6,
                time_utilization_ratio=0.5,
                preference_satisfaction_ratio=0.8,
                deadline_satisfaction_ratio=0.9,
                hard_constraint_violations=0,
                soft_constraint_violations=2,
                objective_value=70,
                optimization_efficiency=0.8,
                schedule_fragmentation=0.6,
                context_switch_penalty=0.1,
                workload_balance_score=0.7,
                solution_confidence=0.8,
                stability_score=0.9
            )

        # Compare key metrics
        improvements = []
        degradations = []

        metrics_comparison = {
            "tasks_scheduled": (main_quality.tasks_scheduled_ratio, alternative_quality.tasks_scheduled_ratio),
            "deadline_satisfaction": (main_quality.deadline_satisfaction_ratio, alternative_quality.deadline_satisfaction_ratio),
            "preference_satisfaction": (main_quality.preference_satisfaction_ratio, alternative_quality.preference_satisfaction_ratio),
            "fragmentation": (main_quality.schedule_fragmentation, alternative_quality.schedule_fragmentation),
            "quality_score": (main_quality.quality_score, alternative_quality.quality_score)
        }

        for metric, (main_val, alt_val) in metrics_comparison.items():
            if metric == "fragmentation":  # Lower is better for fragmentation
                if alt_val < main_val * 0.9:
                    improvements.append(f"reduced {metric}")
                elif alt_val > main_val * 1.1:
                    degradations.append(f"increased {metric}")
            else:  # Higher is better for other metrics
                if alt_val > main_val * 1.05:
                    improvements.append(f"improved {metric}")
                elif alt_val < main_val * 0.95:
                    degradations.append(f"reduced {metric}")

        # Generate trade-off summary
        if improvements and not degradations:
            trade_off_summary = f"Clear improvement: {', '.join(improvements)}"
        elif degradations and not improvements:
            trade_off_summary = f"Trade-off required: {', '.join(degradations)}"
        elif improvements and degradations:
            trade_off_summary = f"Mixed trade-off: gains in {improvements[0]}, losses in {degradations[0]}"
        else:
            trade_off_summary = "Similar overall performance with different characteristics"

        # Calculate user impact
        user_impact = (alternative_quality.quality_score - main_quality.quality_score) * 2  # Scale to -2 to 2 range
        user_impact = max(-1.0, min(1.0, user_impact))  # Clamp to -1 to 1

        return AlternativeComparison(
            main_solution_score=main_quality.quality_score,
            alternative_solution_score=alternative_quality.quality_score,
            improvement_areas=improvements,
            degradation_areas=degradations,
            trade_off_summary=trade_off_summary,
            metrics_comparison=metrics_comparison,
            user_impact_rating=user_impact,
            effort_required=0.3  # Moderate effort to switch
        )

    def _generate_trade_off_description(self, strategy: AlternativeStrategy, comparison: AlternativeComparison) -> str:
        """Generate a human-readable trade-off description."""

        strategy_descriptions = {
            AlternativeStrategy.DEADLINE_RELAXED: "Extends deadlines to improve scheduling flexibility",
            AlternativeStrategy.PREFERENCE_IGNORED: "Ignores time preferences to maximize task completion",
            AlternativeStrategy.SHORTER_BLOCKS: "Uses shorter time blocks for better calendar integration",
            AlternativeStrategy.LONGER_BLOCKS: "Uses longer blocks to reduce context switching",
            AlternativeStrategy.EARLY_BIRD: "Schedules tasks earlier in the day",
            AlternativeStrategy.NIGHT_OWL: "Schedules tasks later in the day",
            AlternativeStrategy.WEEKEND_INCLUDED: "Includes weekend time for additional scheduling options",
            AlternativeStrategy.MINIMAL_FRAGMENTATION: "Minimizes context switching by consolidating work",
            AlternativeStrategy.MAX_PRODUCTIVITY: "Prioritizes peak productivity hours",
            AlternativeStrategy.FLEXIBLE_DURATION: "Allows flexible task durations for better fitting"
        }

        base_description = strategy_descriptions.get(strategy, "Alternative scheduling approach")

        if comparison.improvement_areas:
            base_description += f". This improves {', '.join(comparison.improvement_areas[:2])}"

        if comparison.degradation_areas:
            base_description += f" but may reduce {', '.join(comparison.degradation_areas[:2])}"

        return base_description + "."

    def _identify_better_scenarios(self, strategy: AlternativeStrategy, comparison: AlternativeComparison) -> List[str]:
        """Identify scenarios where this alternative would be better."""

        scenarios = []

        strategy_scenarios = {
            AlternativeStrategy.DEADLINE_RELAXED: [
                "When deadlines are flexible",
                "When task completion is more important than timing",
                "When you have control over due dates"
            ],
            AlternativeStrategy.PREFERENCE_IGNORED: [
                "When you have limited available time",
                "When task completion is urgent",
                "When you need maximum scheduling efficiency"
            ],
            AlternativeStrategy.SHORTER_BLOCKS: [
                "When you have many short gaps in your calendar",
                "When you prefer frequent task switching",
                "When working around many existing commitments"
            ],
            AlternativeStrategy.LONGER_BLOCKS: [
                "When you prefer deep work sessions",
                "When you want to minimize context switching",
                "When tasks benefit from extended focus time"
            ],
            AlternativeStrategy.EARLY_BIRD: [
                "When you're most productive in the morning",
                "When afternoons tend to get busy",
                "When you want to finish work early"
            ],
            AlternativeStrategy.NIGHT_OWL: [
                "When you're most productive in the evening",
                "When mornings are typically busy",
                "When you prefer working later hours"
            ],
            AlternativeStrategy.WEEKEND_INCLUDED: [
                "When weekday time is severely limited",
                "When you don't mind working weekends",
                "When deadlines are approaching quickly"
            ],
            AlternativeStrategy.MINIMAL_FRAGMENTATION: [
                "When focus and flow state are critical",
                "When context switching is costly",
                "When you prefer consolidated work blocks"
            ],
            AlternativeStrategy.MAX_PRODUCTIVITY: [
                "When you have clear peak performance hours",
                "When task quality is more important than convenience",
                "When you want to optimize for best outcomes"
            ],
            AlternativeStrategy.FLEXIBLE_DURATION: [
                "When task durations are estimates",
                "When you prefer adaptive scheduling",
                "When calendar integration is challenging"
            ]
        }

        return strategy_scenarios.get(strategy, ["When you want to try a different approach"])

    def _get_all_tasks(self, request: ScheduleRequest) -> List[Task]:
        """Extract all tasks from the scheduling request."""
        all_tasks = []

        # Add regular tasks
        if hasattr(request, 'tasks') and request.tasks:
            all_tasks.extend(request.tasks)

        # Add todos converted to tasks
        if hasattr(request, 'todos') and request.todos:
            for todo in request.todos:
                # Convert todo to task-like object for analysis
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

