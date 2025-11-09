"""
Scheduling decision logic and task prioritization
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .models import Priority, UserPreferences

logger = logging.getLogger(__name__)


class DecisionMaker:
    """Handles scheduling decisions and task prioritization"""

    def __init__(self):
        self.decision_log: List[Dict[str, Any]] = []

    def prioritize_tasks(
        self,
        tasks: List[Dict[str, Any]],
        user_preferences: UserPreferences
    ) -> List[Dict[str, Any]]:
        """Prioritize tasks based on multiple factors with explanation"""

        def priority_score(task):
            base_priority = self._get_priority_value(task.get('priority', 'medium'))

            # Factor in due date urgency
            due_date_factor = self._calculate_due_date_urgency(task.get('due_date'))

            # Factor in user behavioral preferences
            type_preference = user_preferences.behavioral_weights.get(
                task.get('type', 'task'), 0.5
            )

            # Factor in estimated effort vs available time
            effort_factor = self._calculate_effort_factor(
                task.get('estimated_minutes', 60)
            )

            total_score = (
                base_priority * 0.4 +
                due_date_factor * 0.3 +
                type_preference * 0.2 +
                effort_factor * 0.1
            )

            # Log the decision
            self.decision_log.append({
                'action': 'task_prioritization',
                'task_id': task.get('id'),
                'factors': {
                    'base_priority': base_priority,
                    'due_date_factor': due_date_factor,
                    'type_preference': type_preference,
                    'effort_factor': effort_factor
                },
                'total_score': total_score
            })

            return total_score

        return sorted(tasks, key=priority_score, reverse=True)

    def requires_user_confirmation(
        self,
        scheduled_blocks: List,
        user_preferences: UserPreferences,
        calculate_confidence_func
    ) -> bool:
        """Determine if user confirmation is required"""
        from .models import SchedulingDecision

        # Require confirmation if any hard constraints were violated
        hard_constraint_violations = any(
            block.explanation.decision_type == SchedulingDecision.CONSTRAINT_VIOLATED
            for block in scheduled_blocks
        )

        # Require confirmation if many preferences were flexed
        significant_preference_flexing = sum(
            len(block.explanation.preferences_flexed) for block in scheduled_blocks
        ) > len(scheduled_blocks) * 0.5

        # Require confirmation if confidence is low
        overall_confidence = calculate_confidence_func(scheduled_blocks)
        low_confidence = overall_confidence < 0.7

        return hard_constraint_violations or significant_preference_flexing or low_confidence

    def _get_priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value"""
        return {
            'urgent': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }.get(priority.lower(), 2)

    def _calculate_due_date_urgency(self, due_date: Optional[str]) -> float:
        """Calculate urgency factor based on due date"""
        if not due_date:
            return 0.5

        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            now = datetime.now(due.tzinfo)
            days_until = (due - now).days

            if days_until <= 0:
                return 1.0  # Overdue
            elif days_until <= 1:
                return 0.9  # Due tomorrow
            elif days_until <= 3:
                return 0.7  # Due this week
            elif days_until <= 7:
                return 0.5  # Due next week
            else:
                return 0.3  # Due later
        except:
            return 0.5

    def _calculate_effort_factor(self, estimated_minutes: int) -> float:
        """Calculate effort factor for task scheduling"""
        if estimated_minutes <= 30:
            return 0.8  # Quick tasks
        elif estimated_minutes <= 90:
            return 1.0  # Normal tasks
        elif estimated_minutes <= 180:
            return 0.6  # Long tasks
        else:
            return 0.4  # Very long tasks

    def generate_metrics(
        self,
        scheduled_blocks: List,
        unscheduled_tasks: List[Dict[str, Any]],
        original_tasks: List[Dict[str, Any]],
        calculate_confidence_func
    ) -> Dict[str, Any]:
        """Generate comprehensive scheduling metrics"""
        return {
            'total_tasks': len(original_tasks),
            'scheduled_tasks': len(scheduled_blocks),
            'unscheduled_tasks': len(unscheduled_tasks),
            'success_rate': len(scheduled_blocks) / len(original_tasks) if original_tasks else 0,
            'average_confidence': calculate_confidence_func(scheduled_blocks),
            'preferences_honored': sum(
                len(block.explanation.preferences_honored) for block in scheduled_blocks
            ),
            'preferences_flexed': sum(
                len(block.explanation.preferences_flexed) for block in scheduled_blocks
            ),
            'total_scheduled_minutes': sum(block.duration_minutes for block in scheduled_blocks)
        }

    def generate_preference_suggestions(self, user_preferences: UserPreferences) -> List[str]:
        """Generate suggestions for preference updates based on scheduling patterns"""
        suggestions = []

        # Analyze violation patterns from decision log
        frequent_violations = []
        for decision in self.decision_log:
            if decision.get('preferences_flexed'):
                frequent_violations.append(decision)

        if len(frequent_violations) > len(self.decision_log) * 0.3:
            suggestions.append(
                "Consider adjusting your preferred working hours - we often need to schedule outside them"
            )

        return suggestions
