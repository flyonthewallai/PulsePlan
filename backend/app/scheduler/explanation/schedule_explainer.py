"""
Schedule explanation system for transparent scheduling decisions.

Provides human-readable explanations of why scheduling decisions were made,
helping users understand and trust the scheduling algorithm.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.domain import Task, ScheduleBlock, BusyEvent, Preferences
from ..schemas.enhanced_results import (
    ScheduleExplanations, SchedulingDecision, QualityMetrics,
    DecisionReason, ConstraintViolation, ConstraintType
)
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class ExplanationLevel(Enum):
    """Level of detail for explanations."""
    BRIEF = "brief"        # High-level summary only
    DETAILED = "detailed"  # Detailed reasoning with key factors
    TECHNICAL = "technical" # Full technical details with scores


@dataclass
class DecisionContext:
    """Context information for scheduling decisions."""
    task: Task
    available_slots: List[Tuple[datetime, datetime]]
    conflicts: List[BusyEvent]
    constraints_active: List[str]
    preferences_applied: List[str]
    ml_predictions: Dict[str, float]
    optimization_scores: Dict[str, float]


class ScheduleExplainer:
    """
    Generates human-readable explanations for scheduling decisions.

    Analyzes the scheduling process and provides insights into why
    specific decisions were made, helping users understand the system.
    """

    def __init__(self):
        """Initialize schedule explainer."""
        self.timezone_manager = get_timezone_manager()

    def explain_schedule(
        self,
        tasks: List[Task],
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[str],
        busy_events: List[BusyEvent],
        preferences: Preferences,
        context: Dict[str, Any],
        level: ExplanationLevel = ExplanationLevel.DETAILED
    ) -> ScheduleExplanations:
        """
        Generate comprehensive explanations for a schedule.

        Args:
            tasks: All tasks that were considered
            scheduled_blocks: Successfully scheduled blocks
            unscheduled_tasks: Tasks that couldn't be scheduled
            busy_events: Existing calendar events
            preferences: User preferences
            context: Additional scheduling context
            level: Level of detail for explanations

        Returns:
            Comprehensive schedule explanations
        """
        # Build task mapping
        task_map = {task.id: task for task in tasks}
        scheduled_task_ids = {block.task_id for block in scheduled_blocks}

        # Generate key decisions
        key_decisions = self._analyze_key_decisions(
            scheduled_blocks, task_map, busy_events, preferences, context
        )

        # Generate scheduling rationale
        scheduling_rationale = self._explain_scheduling_choices(
            scheduled_blocks, task_map, busy_events, preferences, level
        )

        # Explain unscheduled tasks
        unscheduled_reasons = self._explain_unscheduled_tasks(
            unscheduled_tasks, task_map, busy_events, preferences, context
        )

        # Identify dominant factors
        dominant_factors = self._identify_dominant_factors(
            tasks, scheduled_blocks, unscheduled_tasks, context
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            tasks, scheduled_blocks, unscheduled_tasks, preferences, context
        )

        # Generate warnings
        warnings = self._identify_warnings(
            scheduled_blocks, task_map, preferences, context
        )

        # Create summary
        summary = self._create_summary(
            tasks, scheduled_blocks, unscheduled_tasks, dominant_factors, level
        )

        return ScheduleExplanations(
            summary=summary,
            key_decisions=key_decisions,
            scheduling_rationale=scheduling_rationale,
            unscheduled_reasons=unscheduled_reasons,
            dominant_factors=dominant_factors,
            recommendations=recommendations,
            warnings=warnings
        )

    def _analyze_key_decisions(
        self,
        scheduled_blocks: List[ScheduleBlock],
        task_map: Dict[str, Task],
        busy_events: List[BusyEvent],
        preferences: Preferences,
        context: Dict[str, Any]
    ) -> List[SchedulingDecision]:
        """Analyze and explain key scheduling decisions."""
        decisions = []

        # Sort blocks by importance/complexity of decision
        sorted_blocks = sorted(
            scheduled_blocks,
            key=lambda b: self._calculate_decision_complexity(b, task_map.get(b.task_id)),
            reverse=True
        )

        # Analyze top decisions
        for block in sorted_blocks[:5]:  # Top 5 most significant decisions
            task = task_map.get(block.task_id)
            if not task:
                continue

            decision = self._analyze_single_decision(
                block, task, busy_events, preferences, context
            )
            decisions.append(decision)

        return decisions

    def _analyze_single_decision(
        self,
        block: ScheduleBlock,
        task: Task,
        busy_events: List[BusyEvent],
        preferences: Preferences,
        context: Dict[str, Any]
    ) -> SchedulingDecision:
        """Analyze a single scheduling decision in detail."""
        # Determine primary reason for this timing
        reason, explanation = self._determine_primary_reason(block, task, busy_events, preferences)

        # Calculate confidence based on multiple factors
        confidence = self._calculate_decision_confidence(block, task, context)

        # Count alternatives that were considered
        alternatives_considered = self._estimate_alternatives_considered(task, busy_events, preferences)

        # Extract contributing factors from context
        factors = self._extract_decision_factors(block, task, context)

        # Identify trade-offs made
        trade_offs = self._identify_trade_offs(block, task, context)

        return SchedulingDecision(
            task_id=task.id,
            decision_type="scheduled",
            reason=reason,
            confidence=confidence,
            alternatives_considered=alternatives_considered,
            explanation=explanation,
            factors=factors,
            trade_offs=trade_offs
        )

    def _determine_primary_reason(
        self,
        block: ScheduleBlock,
        task: Task,
        busy_events: List[BusyEvent],
        preferences: Preferences
    ) -> Tuple[DecisionReason, str]:
        """Determine the primary reason for scheduling at this time."""
        # Check deadline pressure
        if task.deadline:
            time_to_deadline = (task.deadline - block.end).total_seconds() / 3600
            if time_to_deadline < 24:  # Less than 24 hours
                return DecisionReason.DEADLINE_PRESSURE, (
                    f"Scheduled just before deadline (due {task.deadline.strftime('%m/%d %H:%M')})"
                )

        # Check if this matches preferred windows
        if self._matches_preferred_windows(block, task):
            return DecisionReason.PREFERENCE_MATCH, (
                "Scheduled during preferred time window"
            )

        # Check if avoiding conflicts
        conflicts_avoided = self._count_nearby_conflicts(block, busy_events)
        if conflicts_avoided > 0:
            return DecisionReason.CONFLICT_AVOIDANCE, (
                f"Scheduled to avoid {conflicts_avoided} calendar conflicts"
            )

        # Check if limited by availability
        if self._is_in_limited_availability(block, preferences):
            return DecisionReason.AVAILABILITY_LIMITED, (
                "Scheduled during one of few available time slots"
            )

        # Default to optimal timing
        return DecisionReason.OPTIMAL_TIMING, (
            "Scheduled at optimal time based on preferences and availability"
        )

    def _explain_scheduling_choices(
        self,
        scheduled_blocks: List[ScheduleBlock],
        task_map: Dict[str, Task],
        busy_events: List[BusyEvent],
        preferences: Preferences,
        level: ExplanationLevel
    ) -> Dict[str, str]:
        """Generate explanations for each scheduled task."""
        explanations = {}

        for block in scheduled_blocks:
            task = task_map.get(block.task_id)
            if not task:
                continue

            if level == ExplanationLevel.BRIEF:
                explanation = self._create_brief_explanation(block, task)
            elif level == ExplanationLevel.TECHNICAL:
                explanation = self._create_technical_explanation(block, task, busy_events, preferences)
            else:  # DETAILED
                explanation = self._create_detailed_explanation(block, task, busy_events, preferences)

            explanations[task.id] = explanation

        return explanations

    def _create_detailed_explanation(
        self,
        block: ScheduleBlock,
        task: Task,
        busy_events: List[BusyEvent],
        preferences: Preferences
    ) -> str:
        """Create detailed explanation for a scheduling decision."""
        parts = []

        # Basic timing info
        start_time = block.start.strftime("%m/%d %H:%M")
        duration = block.duration_minutes
        parts.append(f"Scheduled for {duration} minutes starting {start_time}")

        # Deadline consideration
        if task.deadline:
            time_to_deadline = (task.deadline - block.end).total_seconds() / 3600
            if time_to_deadline < 48:
                urgency = "urgent" if time_to_deadline < 24 else "soon"
                parts.append(f"due {urgency} ({task.deadline.strftime('%m/%d %H:%M')})")

        # Preference alignment
        if self._matches_preferred_windows(block, task):
            parts.append("during preferred time window")

        # Workday consideration
        hour = block.start.hour
        if 9 <= hour <= 17:
            parts.append("during core work hours")
        elif 18 <= hour <= 20:
            parts.append("during extended work hours")
        elif hour < 9:
            parts.append("during early morning (less preferred)")

        # Conflicts avoided
        conflicts = self._count_nearby_conflicts(block, busy_events)
        if conflicts > 0:
            parts.append(f"avoiding {conflicts} calendar conflicts")

        return f"{task.title}: " + ", ".join(parts) + "."

    def _explain_unscheduled_tasks(
        self,
        unscheduled_task_ids: List[str],
        task_map: Dict[str, Task],
        busy_events: List[BusyEvent],
        preferences: Preferences,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Explain why tasks couldn't be scheduled."""
        explanations = {}

        for task_id in unscheduled_task_ids:
            task = task_map.get(task_id)
            if not task:
                continue

            reason = self._diagnose_unscheduled_reason(task, busy_events, preferences, context)
            explanations[task_id] = reason

        return explanations

    def _diagnose_unscheduled_reason(
        self,
        task: Task,
        busy_events: List[BusyEvent],
        preferences: Preferences,
        context: Dict[str, Any]
    ) -> str:
        """Diagnose why a specific task couldn't be scheduled."""
        # Check if deadline has passed
        if task.deadline and task.deadline < datetime.now():
            return f"Deadline has already passed ({task.deadline.strftime('%m/%d %H:%M')})"

        # Check if deadline is too soon
        if task.deadline:
            hours_until_deadline = (task.deadline - datetime.now()).total_seconds() / 3600
            if hours_until_deadline < task.estimated_minutes / 60:
                return "Not enough time remaining before deadline"

        # Check for insufficient availability
        available_hours = self._calculate_available_hours(busy_events, preferences)
        required_hours = task.estimated_minutes / 60
        if available_hours < required_hours:
            return f"Insufficient available time ({available_hours:.1f}h available, {required_hours:.1f}h needed)"

        # Check for conflicting prerequisites
        if task.prerequisites:
            return f"Waiting for {len(task.prerequisites)} prerequisite tasks to be completed"

        # Check minimum block size constraints
        if task.min_block_minutes > 60:  # Large minimum block
            return f"No continuous {task.min_block_minutes}-minute blocks available"

        # Check for resource conflicts
        if context.get('resource_conflicts'):
            return "Resource conflicts with other scheduled tasks"

        # Default reason
        return "No suitable time slots found that satisfy all constraints"

    def _identify_dominant_factors(
        self,
        tasks: List[Task],
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[str],
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify the dominant factors that influenced the schedule."""
        factors = []

        # Deadline pressure
        urgent_tasks = sum(1 for task in tasks if task.deadline and
                          (task.deadline - datetime.now()).total_seconds() < 86400)
        if urgent_tasks > 0:
            factors.append(f"Deadline pressure ({urgent_tasks} urgent tasks)")

        # Availability constraints
        if len(unscheduled_tasks) > len(scheduled_blocks) * 0.3:
            factors.append("Limited availability windows")

        # Calendar conflicts
        total_conflicts = context.get('calendar_conflicts', 0)
        if total_conflicts > 5:
            factors.append(f"Heavy calendar schedule ({total_conflicts} existing events)")

        # Task complexity
        complex_tasks = sum(1 for task in tasks if task.estimated_minutes > 120)
        if complex_tasks > 0:
            factors.append(f"Complex tasks requiring long blocks ({complex_tasks} tasks)")

        # Preference optimization
        if context.get('preference_weight', 0) > 0.5:
            factors.append("User preference optimization")

        return factors[:3]  # Return top 3 factors

    def _generate_recommendations(
        self,
        tasks: List[Task],
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[str],
        preferences: Preferences,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for schedule improvement."""
        recommendations = []

        # Too many unscheduled tasks
        if len(unscheduled_tasks) > 3:
            recommendations.append(
                "Consider extending available work hours or reducing task scope to fit more tasks"
            )

        # Tight deadlines
        urgent_count = sum(1 for task_id in unscheduled_tasks
                          for task in tasks if task.id == task_id and task.deadline and
                          (task.deadline - datetime.now()).total_seconds() < 86400)
        if urgent_count > 0:
            recommendations.append(
                "Some urgent tasks couldn't be scheduled - consider rescheduling other commitments"
            )

        # Fragmented schedule
        if len(scheduled_blocks) > 8:  # Many small blocks
            recommendations.append(
                "Schedule is fragmented - consider consolidating similar tasks"
            )

        # Poor time utilization
        scheduled_minutes = sum(block.duration_minutes for block in scheduled_blocks)
        workday_minutes = 8 * 60  # Assume 8-hour workday
        utilization = scheduled_minutes / workday_minutes
        if utilization < 0.6:
            recommendations.append(
                "Low time utilization - consider adding more tasks or adjusting preferences"
            )

        # Suboptimal timing
        late_blocks = sum(1 for block in scheduled_blocks if block.start.hour > 18)
        if late_blocks > 2:
            recommendations.append(
                "Several tasks scheduled for evening - consider extending earlier availability"
            )

        return recommendations

    def _identify_warnings(
        self,
        scheduled_blocks: List[ScheduleBlock],
        task_map: Dict[str, Task],
        preferences: Preferences,
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify potential issues and warnings."""
        warnings = []

        # Back-to-back scheduling
        sorted_blocks = sorted(scheduled_blocks, key=lambda b: b.start)
        for i in range(len(sorted_blocks) - 1):
            current_end = sorted_blocks[i].end
            next_start = sorted_blocks[i + 1].start
            if (next_start - current_end).total_seconds() < 900:  # Less than 15 minutes
                warnings.append("Some tasks are scheduled back-to-back with minimal break time")
                break

        # Late evening work
        late_tasks = [block for block in scheduled_blocks if block.start.hour >= 20]
        if late_tasks:
            warnings.append(f"{len(late_tasks)} tasks scheduled for late evening")

        # Long continuous work periods
        for block in scheduled_blocks:
            if block.duration_minutes > 180:  # More than 3 hours
                task = task_map.get(block.task_id)
                if task:
                    warnings.append(f"Long work session scheduled for '{task.title}' ({block.duration_minutes} min)")

        # Weekend scheduling
        weekend_tasks = [block for block in scheduled_blocks if block.start.weekday() >= 5]
        if weekend_tasks:
            warnings.append(f"{len(weekend_tasks)} tasks scheduled for weekend")

        return warnings

    def _create_summary(
        self,
        tasks: List[Task],
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[str],
        dominant_factors: List[str],
        level: ExplanationLevel
    ) -> str:
        """Create a high-level summary of the schedule."""
        total_tasks = len(tasks)
        scheduled_count = len(scheduled_blocks)
        scheduled_minutes = sum(block.duration_minutes for block in scheduled_blocks)

        if level == ExplanationLevel.BRIEF:
            return f"Scheduled {scheduled_count}/{total_tasks} tasks ({scheduled_minutes} minutes total)."

        success_rate = scheduled_count / total_tasks if total_tasks > 0 else 0

        if success_rate >= 0.9:
            quality = "excellent"
        elif success_rate >= 0.8:
            quality = "good"
        elif success_rate >= 0.7:
            quality = "acceptable"
        else:
            quality = "challenging"

        summary_parts = [
            f"Successfully scheduled {scheduled_count} of {total_tasks} tasks",
            f"({scheduled_minutes} minutes total)",
            f"with {quality} results."
        ]

        if dominant_factors:
            summary_parts.append(f"Key factors: {', '.join(dominant_factors[:2])}.")

        if unscheduled_tasks:
            summary_parts.append(f"{len(unscheduled_tasks)} tasks couldn't be scheduled due to constraints.")

        return " ".join(summary_parts)

    # Helper methods

    def _calculate_decision_complexity(self, block: ScheduleBlock, task: Optional[Task]) -> float:
        """Calculate complexity score for scheduling decision."""
        if not task:
            return 0.0

        complexity = 0.0

        # Deadline pressure adds complexity
        if task.deadline:
            hours_to_deadline = (task.deadline - block.start).total_seconds() / 3600
            if hours_to_deadline < 48:
                complexity += 0.5

        # Large tasks add complexity
        if task.estimated_minutes > 120:
            complexity += 0.3

        # High priority adds complexity
        if task.weight > 2.0:
            complexity += 0.2

        return complexity

    def _calculate_decision_confidence(self, block: ScheduleBlock, task: Task, context: Dict[str, Any]) -> float:
        """Calculate confidence score for a scheduling decision."""
        confidence = 0.7  # Base confidence

        # High utility scores increase confidence
        utility_score = getattr(block, 'utility_score', 0.5)
        confidence += (utility_score - 0.5) * 0.4

        # Good completion probability increases confidence
        completion_prob = getattr(block, 'estimated_completion_probability', 0.5)
        confidence += (completion_prob - 0.5) * 0.2

        # Clamp to valid range
        return max(0.0, min(1.0, confidence))

    def _estimate_alternatives_considered(self, task: Task, busy_events: List[BusyEvent], preferences: Preferences) -> int:
        """Estimate how many alternative time slots were considered."""
        # Simple heuristic based on task flexibility and constraints
        base_alternatives = 10

        if task.min_block_minutes > 60:
            base_alternatives //= 2  # Fewer options for large blocks

        if task.deadline:
            hours_to_deadline = (task.deadline - datetime.now()).total_seconds() / 3600
            if hours_to_deadline < 24:
                base_alternatives //= 2  # Fewer options near deadline

        return max(1, base_alternatives)

    def _extract_decision_factors(self, block: ScheduleBlock, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract factors that contributed to scheduling decision."""
        factors = {}

        # Timing factors
        hour = block.start.hour
        if 9 <= hour <= 17:
            factors['core_hours'] = 1.0
        elif 18 <= hour <= 20:
            factors['extended_hours'] = 0.7
        else:
            factors['off_hours'] = 0.3

        # Deadline factor
        if task.deadline:
            hours_to_deadline = (task.deadline - block.start).total_seconds() / 3600
            urgency = max(0.0, min(1.0, (72 - hours_to_deadline) / 72))
            factors['deadline_urgency'] = urgency

        # Utility score
        if hasattr(block, 'utility_score'):
            factors['utility_score'] = block.utility_score

        return factors

    def _identify_trade_offs(self, block: ScheduleBlock, task: Task, context: Dict[str, Any]) -> List[str]:
        """Identify trade-offs made in scheduling decision."""
        trade_offs = []

        # Time of day trade-offs
        hour = block.start.hour
        if hour < 9:
            trade_offs.append("Scheduled early to fit before other commitments")
        elif hour > 18:
            trade_offs.append("Scheduled late due to limited daytime availability")

        # Duration trade-offs
        if hasattr(task, 'max_block_minutes') and block.duration_minutes < task.estimated_minutes:
            trade_offs.append("Split into multiple sessions due to time constraints")

        return trade_offs

    def _matches_preferred_windows(self, block: ScheduleBlock, task: Task) -> bool:
        """Check if block timing matches task's preferred windows."""
        if not task.preferred_windows:
            return False

        block_dow = block.start.weekday()
        block_time = block.start.time()

        for window in task.preferred_windows:
            if window.get('dow') == block_dow:
                start_time = datetime.strptime(window.get('start', '00:00'), '%H:%M').time()
                end_time = datetime.strptime(window.get('end', '23:59'), '%H:%M').time()
                if start_time <= block_time <= end_time:
                    return True

        return False

    def _count_nearby_conflicts(self, block: ScheduleBlock, busy_events: List[BusyEvent]) -> int:
        """Count calendar conflicts near the scheduled block."""
        conflicts = 0
        buffer = timedelta(minutes=30)

        for event in busy_events:
            if (event.start <= block.end + buffer and
                event.end >= block.start - buffer):
                conflicts += 1

        return conflicts

    def _is_in_limited_availability(self, block: ScheduleBlock, preferences: Preferences) -> bool:
        """Check if block is scheduled during limited availability."""
        # Simple heuristic: consider late hours as limited availability
        hour = block.start.hour
        return hour < 8 or hour > 19

    def _create_brief_explanation(self, block: ScheduleBlock, task: Task) -> str:
        """Create brief explanation for a scheduling decision."""
        start_time = block.start.strftime("%m/%d %H:%M")
        return f"{task.title}: {start_time} ({block.duration_minutes}min)"

    def _create_technical_explanation(
        self, block: ScheduleBlock, task: Task, busy_events: List[BusyEvent], preferences: Preferences
    ) -> str:
        """Create technical explanation with scores and metrics."""
        explanation = self._create_detailed_explanation(block, task, busy_events, preferences)

        # Add technical details
        technical_parts = []
        if hasattr(block, 'utility_score'):
            technical_parts.append(f"utility={block.utility_score:.3f}")
        if hasattr(block, 'estimated_completion_probability'):
            technical_parts.append(f"completion_prob={block.estimated_completion_probability:.3f}")

        if technical_parts:
            explanation += f" [{', '.join(technical_parts)}]"

        return explanation

    def _calculate_available_hours(self, busy_events: List[BusyEvent], preferences: Preferences) -> float:
        """Calculate total available hours based on busy events and preferences."""
        # Simplified calculation - would be more sophisticated in practice
        workday_hours = 8  # Default 8-hour workday
        busy_hours = sum((event.end - event.start).total_seconds() / 3600 for event in busy_events)
        return max(0, workday_hours - busy_hours)

