"""
Schedule block allocation and optimization
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .models import (
    Priority,
    SchedulingDecision,
    ScheduleExplanation,
    ScheduleBlock,
    UserPreferences
)

logger = logging.getLogger(__name__)


class BlockAllocator:
    """Handles time slot finding, scoring, and block allocation"""

    def __init__(self, decision_log: List[Dict[str, Any]]):
        self.decision_log = decision_log

    def find_optimal_slot(
        self,
        task: Dict[str, Any],
        availability: Dict[str, Any],
        user_preferences: UserPreferences,
        existing_blocks: List[ScheduleBlock],
        explanation_generator
    ) -> Optional[ScheduleBlock]:
        """Find optimal time slot with detailed explanation"""

        duration = task.get('estimated_minutes', 60)
        task_type = task.get('type', 'task')
        priority = Priority(self._get_priority_value(task.get('priority', 'medium')))

        # Find all possible slots
        possible_slots = self._find_available_slots(availability, duration)

        if not possible_slots:
            explanation = ScheduleExplanation(
                decision_type=SchedulingDecision.NO_SLOT_FOUND,
                reason=f"No available {duration}-minute slots found",
                confidence_score=0.0,
                tradeoffs=[],
                alternatives_considered=[],
                constraints_applied=[
                    f"Required duration: {duration} minutes",
                    "Working hours constraint",
                    "Existing meeting conflicts"
                ],
                preferences_honored=[],
                preferences_flexed=[]
            )
            return None

        # Score each slot based on preferences
        best_slot = None
        best_score = -1
        alternatives_considered = []

        for slot in possible_slots:
            score, slot_explanation = self._score_time_slot(
                slot, task, user_preferences, existing_blocks
            )

            alternatives_considered.append(
                f"{slot['start'].strftime('%H:%M')}-{slot['end'].strftime('%H:%M')}: score {score:.2f}"
            )

            if score > best_score:
                best_score = score
                best_slot = slot

        if not best_slot:
            return None

        # Determine if we had to flex any preferences
        preferences_flexed = self._check_preference_violations(
            best_slot, task, user_preferences
        )

        # Create explanation
        explanation = ScheduleExplanation(
            decision_type=SchedulingDecision.OPTIMAL_PLACEMENT if not preferences_flexed
                         else SchedulingDecision.PREFERENCE_FLEXED,
            reason=explanation_generator.generate_slot_selection_reason(best_slot, task, best_score),
            confidence_score=min(1.0, best_score),
            tradeoffs=explanation_generator.identify_tradeoffs(best_slot, alternatives_considered[:3]),
            alternatives_considered=alternatives_considered,
            constraints_applied=explanation_generator.get_applied_constraints(user_preferences),
            preferences_honored=explanation_generator.get_honored_preferences(best_slot, user_preferences),
            preferences_flexed=preferences_flexed
        )

        # Log the decision
        self.decision_log.append({
            'action': 'slot_selection',
            'task_id': task.get('id'),
            'selected_slot': {
                'start': best_slot['start'].isoformat(),
                'end': best_slot['end'].isoformat(),
                'score': best_score
            },
            'alternatives_count': len(possible_slots),
            'preferences_flexed': len(preferences_flexed) > 0
        })

        return ScheduleBlock(
            id=f"block_{task.get('id', 'unknown')}_{datetime.now().timestamp()}",
            title=task.get('title', 'Scheduled Task'),
            type=task_type,
            priority=priority,
            start_time=best_slot['start'],
            end_time=best_slot['end'],
            duration_minutes=duration,
            explanation=explanation
        )

    def find_available_slots(self, availability: Dict[str, Any], duration: int) -> List[Dict[str, datetime]]:
        """Find all available time slots that can fit the duration"""
        return self._find_available_slots(availability, duration)

    def find_next_available_slot(
        self,
        task: Dict[str, Any],
        availability: Dict[str, Any]
    ) -> Optional[Dict[str, datetime]]:
        """Find the next available time slot for a task"""
        duration = task.get('estimated_minutes', 60)
        slots = self._find_available_slots(availability, duration)

        # Return the earliest available slot
        if slots:
            return min(slots, key=lambda s: s['start'])

        return None

    def remove_from_availability(self, availability: Dict[str, Any], scheduled_block: ScheduleBlock):
        """Remove scheduled time from availability"""
        # This would update the availability dict to reflect the newly scheduled block
        # Implementation would depend on the specific availability data structure
        pass

    def _find_available_slots(self, availability: Dict[str, Any], duration: int) -> List[Dict[str, datetime]]:
        """Find all available time slots that can fit the duration"""
        slots = []

        for free_block in availability.get('free_blocks', []):
            start_time = datetime.fromisoformat(free_block['start'])
            end_time = datetime.fromisoformat(free_block['end'])

            # Find all possible slots within this free block
            current_time = start_time
            while current_time + timedelta(minutes=duration) <= end_time:
                slots.append({
                    'start': current_time,
                    'end': current_time + timedelta(minutes=duration)
                })
                current_time += timedelta(minutes=30)  # 30-minute increments

        return slots

    def _score_time_slot(
        self,
        slot: Dict[str, datetime],
        task: Dict[str, Any],
        user_preferences: UserPreferences,
        existing_blocks: List[ScheduleBlock]
    ) -> Tuple[float, str]:
        """Score a time slot based on user preferences and task requirements"""
        score = 0.0
        explanation_parts = []

        # Time of day preference
        hour = slot['start'].hour
        if 9 <= hour < 12:  # Morning
            morning_weight = user_preferences.behavioral_weights.get('morning_preference', 0.5)
            score += morning_weight * 0.3
            explanation_parts.append(f"Morning slot (weight: {morning_weight:.2f})")
        elif 13 <= hour < 17:  # Afternoon
            afternoon_weight = user_preferences.behavioral_weights.get('afternoon_preference', 0.5)
            score += afternoon_weight * 0.3
            explanation_parts.append(f"Afternoon slot (weight: {afternoon_weight:.2f})")

        # Focus time protection
        if task.get('type') == 'focus' and self._is_focus_time(slot['start'], user_preferences):
            score += 0.4
            explanation_parts.append("Protected focus time")

        # Meeting clustering preference
        if task.get('type') == 'meeting':
            nearby_meetings = self._count_nearby_meetings(slot, existing_blocks)
            if nearby_meetings > 0:
                clustering_weight = user_preferences.behavioral_weights.get('meeting_clustering', 0.5)
                score += clustering_weight * 0.2
                explanation_parts.append(f"Near other meetings (clustering: {clustering_weight:.2f})")

        # Buffer time consideration
        buffer_score = self._calculate_buffer_score(slot, existing_blocks)
        score += buffer_score * 0.1
        explanation_parts.append(f"Buffer score: {buffer_score:.2f}")

        return score, "; ".join(explanation_parts)

    def _check_preference_violations(
        self,
        slot: Dict[str, datetime],
        task: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> List[str]:
        """Check what preferences were violated/flexed for this slot"""
        violations = []

        # Check working hours
        work_start = user_preferences.hard_constraints.get('work_start', '09:00')
        work_end = user_preferences.hard_constraints.get('work_end', '17:00')

        slot_start_time = slot['start'].time()
        work_start_time = datetime.strptime(work_start, '%H:%M').time()
        work_end_time = datetime.strptime(work_end, '%H:%M').time()

        if slot_start_time < work_start_time:
            violations.append(f"Scheduled before preferred work start ({work_start})")

        if slot['end'].time() > work_end_time:
            violations.append(f"Scheduled after preferred work end ({work_end})")

        # Check blocked times
        blocked_times = user_preferences.hard_constraints.get('blocked_times', [])
        for blocked in blocked_times:
            blocked_start = datetime.strptime(blocked['start'], '%H:%M').time()
            blocked_end = datetime.strptime(blocked['end'], '%H:%M').time()

            if (slot_start_time < blocked_end and slot['end'].time() > blocked_start):
                violations.append(f"Conflicts with blocked time {blocked['start']}-{blocked['end']}")

        return violations

    def _get_priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value"""
        return {
            'urgent': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }.get(priority.lower(), 2)

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

    def _count_nearby_meetings(self, slot: Dict[str, datetime], existing_blocks: List[ScheduleBlock]) -> int:
        """Count meetings near this time slot"""
        count = 0
        slot_start = slot['start']

        for block in existing_blocks:
            if block.type == 'meeting':
                time_diff = abs((block.start_time - slot_start).total_seconds() / 3600)  # Hours
                if time_diff <= 2:  # Within 2 hours
                    count += 1

        return count

    def _calculate_buffer_score(self, slot: Dict[str, datetime], existing_blocks: List[ScheduleBlock]) -> float:
        """Calculate score based on buffer time around this slot"""
        buffer_score = 1.0
        slot_start = slot['start']
        slot_end = slot['end']

        for block in existing_blocks:
            # Check time before this slot
            if block.end_time <= slot_start:
                gap = (slot_start - block.end_time).total_seconds() / 60  # Minutes
                if gap < 15:  # Less than 15 minutes buffer
                    buffer_score -= 0.2

            # Check time after this slot
            elif block.start_time >= slot_end:
                gap = (block.start_time - slot_end).total_seconds() / 60  # Minutes
                if gap < 15:  # Less than 15 minutes buffer
                    buffer_score -= 0.2

        return max(0.0, buffer_score)
