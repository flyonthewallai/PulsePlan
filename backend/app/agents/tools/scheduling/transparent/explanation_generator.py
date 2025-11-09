"""
Explanation generation for scheduling decisions
"""
from typing import Dict, List, Any
from datetime import datetime
import logging

from .models import ScheduleBlock, UserPreferences

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """Generates human-readable explanations for scheduling decisions"""

    def generate_overall_explanation(
        self,
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[Dict[str, Any]],
        user_preferences: UserPreferences
    ) -> str:
        """Generate comprehensive explanation of scheduling decisions"""
        from .models import SchedulingDecision

        total_tasks = len(scheduled_blocks) + len(unscheduled_tasks)
        scheduled_count = len(scheduled_blocks)

        if scheduled_count == 0:
            return "No tasks could be scheduled due to insufficient available time or constraint conflicts."

        explanation_parts = [
            f"Successfully scheduled {scheduled_count} of {total_tasks} tasks."
        ]

        # Analyze scheduling patterns
        morning_blocks = sum(1 for block in scheduled_blocks if block.start_time.hour < 12)
        afternoon_blocks = scheduled_count - morning_blocks

        if morning_blocks > afternoon_blocks:
            explanation_parts.append(
                f"Prioritized morning scheduling ({morning_blocks} morning, {afternoon_blocks} afternoon) "
                "based on your preference for early productivity."
            )

        # Mention conflicts resolved
        conflict_resolutions = sum(1 for block in scheduled_blocks
                                  if block.explanation.decision_type == SchedulingDecision.CONFLICT_RESOLVED)

        if conflict_resolutions > 0:
            explanation_parts.append(
                f"Resolved {conflict_resolutions} scheduling conflicts by prioritizing higher-priority tasks."
            )

        # Mention preference flexing
        preferences_flexed = sum(1 for block in scheduled_blocks
                                if len(block.explanation.preferences_flexed) > 0)

        if preferences_flexed > 0:
            explanation_parts.append(
                f"Adjusted {preferences_flexed} time slots to accommodate all tasks while respecting critical constraints."
            )

        # Mention unscheduled tasks
        if unscheduled_tasks:
            high_priority_unscheduled = sum(1 for task in unscheduled_tasks
                                           if task.get('priority', 'medium') in ['urgent', 'high'])
            if high_priority_unscheduled > 0:
                explanation_parts.append(
                    f"{high_priority_unscheduled} high-priority tasks could not be scheduled. "
                    "Consider extending work hours or rescheduling lower-priority items."
                )

        return " ".join(explanation_parts)

    def generate_slot_selection_reason(
        self,
        slot: Dict[str, datetime],
        task: Dict[str, Any],
        score: float
    ) -> str:
        """Generate human-readable reason for slot selection"""
        time_str = f"{slot['start'].strftime('%H:%M')}-{slot['end'].strftime('%H:%M')}"

        if score >= 0.8:
            return f"Optimal time slot at {time_str} - aligns perfectly with your preferences and work patterns"
        elif score >= 0.6:
            return f"Good time slot at {time_str} - balances task requirements with your preferences"
        elif score >= 0.4:
            return f"Acceptable time slot at {time_str} - some preference compromises made to fit schedule"
        else:
            return f"Suboptimal time slot at {time_str} - significant preference adjustments required"

    def identify_tradeoffs(self, selected_slot: Dict[str, datetime], alternatives: List[str]) -> List[str]:
        """Identify what tradeoffs were made in slot selection"""
        tradeoffs = []

        selected_time = selected_slot['start'].strftime('%H:%M')

        # Analyze if we picked a non-preferred time
        hour = selected_slot['start'].hour
        if hour < 9:
            tradeoffs.append("Scheduled before typical work hours for better availability")
        elif hour >= 17:
            tradeoffs.append("Extended work day to accommodate task")

        if len(alternatives) > 1:
            tradeoffs.append(f"Chose {selected_time} over {len(alternatives)} other options for optimal fit")

        return tradeoffs

    def get_applied_constraints(self, user_preferences: UserPreferences) -> List[str]:
        """Get list of constraints that were applied"""
        constraints = []

        hard_constraints = user_preferences.hard_constraints

        if 'work_start' in hard_constraints and 'work_end' in hard_constraints:
            constraints.append(
                f"Working hours: {hard_constraints['work_start']}-{hard_constraints['work_end']}"
            )

        if 'max_meetings_per_day' in hard_constraints:
            constraints.append(f"Max meetings per day: {hard_constraints['max_meetings_per_day']}")

        if 'min_break_duration' in hard_constraints:
            constraints.append(f"Minimum break: {hard_constraints['min_break_duration']} minutes")

        return constraints

    def get_honored_preferences(
        self,
        slot: Dict[str, datetime],
        user_preferences: UserPreferences
    ) -> List[str]:
        """Get list of preferences that were honored"""
        honored = []

        hour = slot['start'].hour

        # Morning preference
        if 9 <= hour < 12 and user_preferences.behavioral_weights.get('morning_preference', 0) > 0.6:
            honored.append("Preferred morning scheduling")

        # Focus time protection
        if self._is_focus_time(slot['start'], user_preferences):
            honored.append("Protected focus time slot")

        return honored

    def calculate_overall_confidence(self, scheduled_blocks: List[ScheduleBlock]) -> float:
        """Calculate overall confidence score for the schedule"""
        if not scheduled_blocks:
            return 0.0

        individual_scores = [block.explanation.confidence_score for block in scheduled_blocks]
        return sum(individual_scores) / len(individual_scores)

    def _is_focus_time(self, start_time: datetime, user_preferences: UserPreferences) -> bool:
        """Check if time slot is in user's focus time periods"""
        focus_blocks = user_preferences.soft_preferences.get('focus_blocks', [])

        time_str = start_time.strftime('%H:%M')

        for focus_block in focus_blocks:
            focus_start = focus_block.split('-')[0]
            focus_end = focus_block.split('-')[1]

            if focus_start <= time_str < focus_end:
                return True

        return False
