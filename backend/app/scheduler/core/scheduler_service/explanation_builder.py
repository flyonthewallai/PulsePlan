"""
Explanation building for schedule results.

Generates human-readable explanations for scheduling decisions, constraints,
and outcomes to improve transparency and debuggability.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from ..domain import ScheduleSolution, Task, BusyEvent, Preferences
from ...schemas.enhanced_results import ScheduleExplanations
from ...explanation.schedule_explainer import ScheduleExplainer

logger = logging.getLogger(__name__)


class ExplanationBuilder:
    """Builds human-readable explanations for schedules."""

    def __init__(self):
        """Initialize explanation builder."""
        self.schedule_explainer = ScheduleExplainer()

    def build_basic_explanations(
        self,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        penalty_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Build basic human-readable explanations for the schedule.

        Args:
            solution: Scheduling solution to explain
            weights: Penalty weights used
            penalty_context: Additional context about penalties

        Returns:
            Dictionary of explanation strings
        """
        explanations = {}

        if solution.feasible:
            explanations['summary'] = (
                f"Successfully scheduled {len(solution.blocks)} blocks "
                f"across {solution.total_scheduled_minutes} minutes."
            )

            if solution.unscheduled_tasks:
                explanations['unscheduled'] = (
                    f"{len(solution.unscheduled_tasks)} tasks could not be scheduled. "
                    "This may be due to insufficient time or conflicting constraints."
                )

            # Explain key weights used
            key_weights = {k: v for k, v in weights.items() if v > 1.5}
            if key_weights:
                weight_desc = ", ".join(f"{k}={v:.1f}" for k, v in key_weights.items())
                explanations['optimization'] = f"Optimization emphasized: {weight_desc}"

        else:
            explanations['summary'] = "Could not generate a feasible schedule."

            # Try to explain why
            if 'infeasible_reason' in solution.diagnostics:
                explanations['reason'] = solution.diagnostics['infeasible_reason']
            elif solution.solver_status == "timeout":
                explanations['reason'] = "Optimization timed out before finding a solution."
            elif solution.solver_status == "no_solver":
                explanations['reason'] = "Constraint solver not available."
            else:
                explanations['reason'] = "Unknown scheduling failure."

        return explanations

    async def generate_detailed_explanations(
        self,
        solution: ScheduleSolution,
        tasks: List[Task],
        events: List[BusyEvent],
        prefs: Preferences,
        penalty_context: Dict[str, Any]
    ) -> ScheduleExplanations:
        """
        Generate detailed explanations for the schedule.

        Args:
            solution: Scheduling solution
            tasks: List of all tasks
            events: List of busy events
            prefs: User preferences
            penalty_context: Context about penalties and constraints

        Returns:
            Structured explanations object
        """
        # Use the schedule explainer
        explanations = self.schedule_explainer.explain_schedule(
            tasks=tasks,
            scheduled_blocks=solution.blocks,
            unscheduled_tasks=solution.unscheduled_tasks,
            busy_events=events,
            preferences=prefs.__dict__ if hasattr(prefs, '__dict__') else {},
            context=penalty_context,
            level="detailed"
        )

        logger.debug(
            f"Generated detailed explanations: "
            f"{len(explanations.key_decisions)} key decisions, "
            f"{len(explanations.recommendations)} recommendations"
        )

        return explanations

    def explain_unscheduled_tasks(
        self,
        unscheduled_tasks: List[str],
        tasks: List[Task],
        events: List[BusyEvent],
        prefs: Preferences
    ) -> List[str]:
        """
        Generate explanations for why tasks were not scheduled.

        Args:
            unscheduled_tasks: IDs of tasks that couldn't be scheduled
            tasks: All tasks
            events: Busy events
            prefs: User preferences

        Returns:
            List of explanation strings
        """
        explanations = []

        # Create task lookup
        task_map = {task.id: task for task in tasks}

        for task_id in unscheduled_tasks:
            task = task_map.get(task_id)
            if not task:
                continue

            reasons = []

            # Check deadline constraints
            if task.deadline:
                reasons.append(f"deadline: {task.deadline.isoformat()}")

            # Check duration
            if task.remaining_minutes > prefs.max_daily_effort_minutes:
                reasons.append(
                    f"duration ({task.remaining_minutes}m) exceeds "
                    f"daily limit ({prefs.max_daily_effort_minutes}m)"
                )

            # Check dependencies
            if hasattr(task, 'dependencies') and task.dependencies:
                reasons.append(f"{len(task.dependencies)} dependencies")

            reason_str = ", ".join(reasons) if reasons else "unknown constraints"
            explanations.append(
                f"Task '{task.title}' (ID: {task_id}): {reason_str}"
            )

        return explanations

    def explain_weight_selection(
        self,
        weights: Dict[str, float],
        context: Dict[str, Any]
    ) -> str:
        """
        Explain why specific weights were selected.

        Args:
            weights: Selected penalty weights
            context: Context used for weight selection

        Returns:
            Explanation string
        """
        # Identify emphasized weights
        emphasized = {k: v for k, v in weights.items() if v > 1.5}
        de_emphasized = {k: v for k, v in weights.items() if v < 1.0}

        parts = []

        if emphasized:
            emphasis_list = ", ".join(f"{k} ({v:.1f})" for k, v in emphasized.items())
            parts.append(f"Emphasized: {emphasis_list}")

        if de_emphasized:
            de_emphasis_list = ", ".join(f"{k} ({v:.1f})" for k, v in de_emphasized.items())
            parts.append(f"De-emphasized: {de_emphasis_list}")

        # Add context information
        if 'dow' in context:
            dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_name = dow_names[context['dow']]
            parts.append(f"Day: {day_name}")

        if 'hour' in context:
            parts.append(f"Hour: {context['hour']}:00")

        return " | ".join(parts) if parts else "Default weights used"

    def summarize_solution_quality(
        self,
        solution: ScheduleSolution,
        tasks: List[Task]
    ) -> str:
        """
        Generate a quality summary for the solution.

        Args:
            solution: Scheduling solution
            tasks: All tasks

        Returns:
            Quality summary string
        """
        if not solution.feasible:
            return "No feasible solution found"

        total_tasks = len(tasks)
        scheduled_tasks = len(solution.blocks)
        unscheduled_tasks = len(solution.unscheduled_tasks)

        completion_rate = scheduled_tasks / max(1, total_tasks) * 100

        quality_parts = [
            f"Scheduled {scheduled_tasks}/{total_tasks} tasks ({completion_rate:.1f}%)",
            f"{solution.total_scheduled_minutes} minutes planned"
        ]

        if solution.objective_value is not None:
            quality_parts.append(f"Quality score: {solution.objective_value:.2f}")

        if unscheduled_tasks > 0:
            quality_parts.append(f"⚠️ {unscheduled_tasks} tasks unscheduled")

        return " | ".join(quality_parts)


def get_explanation_builder() -> ExplanationBuilder:
    """Get an explanation builder instance."""
    return ExplanationBuilder()
