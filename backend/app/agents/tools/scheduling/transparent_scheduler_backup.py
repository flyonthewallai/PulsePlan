"""
Transparent Scheduling and Rescheduling Tools
Implements intelligent scheduling with full transparency and user preference handling
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Priority(Enum):
    URGENT = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class SchedulingDecision(Enum):
    OPTIMAL_PLACEMENT = "optimal_placement"
    CONFLICT_RESOLVED = "conflict_resolved"
    PREFERENCE_FLEXED = "preference_flexed"
    CONSTRAINT_VIOLATED = "constraint_violated"
    NO_SLOT_FOUND = "no_slot_found"


@dataclass
class ScheduleExplanation:
    """Detailed explanation of scheduling decisions"""
    decision_type: SchedulingDecision
    reason: str
    confidence_score: float  # 0.0 to 1.0
    tradeoffs: List[str]
    alternatives_considered: List[str]
    constraints_applied: List[str]
    preferences_honored: List[str]
    preferences_flexed: List[str]


@dataclass
class ScheduleBlock:
    """A scheduled time block with full transparency"""
    id: str
    title: str
    type: str  # 'task', 'meeting', 'focus', 'break'
    priority: Priority
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    explanation: ScheduleExplanation
    user_editable: bool = True
    auto_reschedulable: bool = True


@dataclass
class UserPreferences:
    """Comprehensive user preferences with hard/soft distinction"""
    # Hard constraints - never violate without explicit user override
    hard_constraints: Dict[str, Any]
    
    # Soft preferences - can be flexed with explanation
    soft_preferences: Dict[str, Any]
    
    # Learning weights from historical behavior
    behavioral_weights: Dict[str, float]


@dataclass
class SchedulingResult:
    """Complete scheduling result with transparency"""
    success: bool
    schedule: List[ScheduleBlock]
    overall_explanation: str
    confidence_score: float
    preview_mode: bool
    requires_user_confirmation: bool
    unscheduled_tasks: List[Dict[str, Any]]
    scheduling_metrics: Dict[str, Any]
    suggested_preference_updates: List[str]


class TransparentScheduler:
    """
    Intelligent scheduler that provides full transparency on all decisions
    Follows the transparency guidelines for explainable scheduling
    """
    
    def __init__(self):
        self.decision_log: List[Dict[str, Any]] = []
        self.preference_violations: List[str] = []
        
    def schedule_tasks(
        self,
        tasks: List[Dict[str, Any]],
        availability: Dict[str, Any],
        user_preferences: UserPreferences,
        preview_mode: bool = True
    ) -> SchedulingResult:
        """
        Main scheduling function with full transparency
        
        Args:
            tasks: List of tasks to schedule
            availability: Available time slots
            user_preferences: User preferences and constraints
            preview_mode: Generate preview without committing
            
        Returns:
            SchedulingResult with detailed explanations
        """
        self.decision_log.clear()
        self.preference_violations.clear()
        
        logger.info(f"Starting transparent scheduling for {len(tasks)} tasks")
        
        # Step 1: Analyze and prioritize tasks
        prioritized_tasks = self._prioritize_tasks(tasks, user_preferences)
        
        # Step 2: Find optimal time slots for each task
        scheduled_blocks = []
        unscheduled_tasks = []
        
        for task in prioritized_tasks:
            result = self._find_optimal_slot(
                task, availability, user_preferences, scheduled_blocks
            )
            
            if result:
                scheduled_blocks.append(result)
                # Update availability
                self._remove_from_availability(availability, result)
            else:
                unscheduled_tasks.append(task)
        
        # Step 3: Generate overall explanation and metrics
        overall_explanation = self._generate_overall_explanation(
            scheduled_blocks, unscheduled_tasks, user_preferences
        )
        
        # Step 4: Calculate confidence and determine if confirmation needed
        confidence_score = self._calculate_overall_confidence(scheduled_blocks)
        requires_confirmation = self._requires_user_confirmation(
            scheduled_blocks, user_preferences
        )
        
        # Step 5: Generate metrics and suggestions
        metrics = self._generate_metrics(scheduled_blocks, unscheduled_tasks, tasks)
        suggestions = self._generate_preference_suggestions(user_preferences)
        
        return SchedulingResult(
            success=len(scheduled_blocks) > 0,
            schedule=scheduled_blocks,
            overall_explanation=overall_explanation,
            confidence_score=confidence_score,
            preview_mode=preview_mode,
            requires_user_confirmation=requires_confirmation,
            unscheduled_tasks=unscheduled_tasks,
            scheduling_metrics=metrics,
            suggested_preference_updates=suggestions
        )
    
    def reschedule_missed_task(
        self,
        missed_task: Dict[str, Any],
        current_schedule: List[ScheduleBlock],
        availability: Dict[str, Any],
        user_preferences: UserPreferences,
        reschedule_strategy: str = "prompt_user"
    ) -> SchedulingResult:
        """
        Reschedule a missed task with full transparency
        
        Args:
            missed_task: The task that was missed
            current_schedule: Current schedule blocks
            availability: Updated availability
            user_preferences: User preferences
            reschedule_strategy: How to handle the reschedule
            
        Returns:
            SchedulingResult with rescheduling explanation
        """
        logger.info(f"Rescheduling missed task: {missed_task.get('title', 'Unknown')}")
        
        if reschedule_strategy == "prompt_user":
            return self._prompt_reschedule_options(
                missed_task, current_schedule, availability, user_preferences
            )
        elif reschedule_strategy == "next_available":
            return self._reschedule_to_next_slot(
                missed_task, current_schedule, availability, user_preferences
            )
        elif reschedule_strategy == "reprioritize_week":
            return self._reprioritize_entire_week(
                missed_task, current_schedule, availability, user_preferences
            )
        else:
            raise ValueError(f"Unknown reschedule strategy: {reschedule_strategy}")
    
    def update_preferences(
        self,
        user_preferences: UserPreferences,
        feedback: Dict[str, Any]
    ) -> UserPreferences:
        """
        Update user preferences based on feedback
        
        Args:
            user_preferences: Current preferences
            feedback: User feedback on scheduling decisions
            
        Returns:
            Updated preferences
        """
        updated_preferences = user_preferences
        
        # Process feedback and update weights
        for feedback_item in feedback.get('items', []):
            preference_type = feedback_item.get('type')
            preference_value = feedback_item.get('value')
            weight_adjustment = feedback_item.get('weight_change', 0.1)
            
            if preference_type in updated_preferences.behavioral_weights:
                current_weight = updated_preferences.behavioral_weights[preference_type]
                new_weight = max(0.0, min(1.0, current_weight + weight_adjustment))
                updated_preferences.behavioral_weights[preference_type] = new_weight
                
                logger.info(f"Updated preference weight: {preference_type} = {new_weight}")
        
        return updated_preferences
    
    # Private helper methods
    
    def _prioritize_tasks(
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
    
    def _find_optimal_slot(
        self,
        task: Dict[str, Any],
        availability: Dict[str, Any],
        user_preferences: UserPreferences,
        existing_blocks: List[ScheduleBlock]
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
            reason=self._generate_slot_selection_reason(best_slot, task, best_score),
            confidence_score=min(1.0, best_score),
            tradeoffs=self._identify_tradeoffs(best_slot, alternatives_considered[:3]),
            alternatives_considered=alternatives_considered,
            constraints_applied=self._get_applied_constraints(user_preferences),
            preferences_honored=self._get_honored_preferences(best_slot, user_preferences),
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
    
    def _generate_overall_explanation(
        self,
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[Dict[str, Any]],
        user_preferences: UserPreferences
    ) -> str:
        """Generate comprehensive explanation of scheduling decisions"""
        
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
    
    def _calculate_overall_confidence(self, scheduled_blocks: List[ScheduleBlock]) -> float:
        """Calculate overall confidence score for the schedule"""
        if not scheduled_blocks:
            return 0.0
        
        individual_scores = [block.explanation.confidence_score for block in scheduled_blocks]
        return sum(individual_scores) / len(individual_scores)
    
    def _requires_user_confirmation(
        self,
        scheduled_blocks: List[ScheduleBlock],
        user_preferences: UserPreferences
    ) -> bool:
        """Determine if user confirmation is required"""
        
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
        overall_confidence = self._calculate_overall_confidence(scheduled_blocks)
        low_confidence = overall_confidence < 0.7
        
        return hard_constraint_violations or significant_preference_flexing or low_confidence
    
    def _prompt_reschedule_options(
        self,
        missed_task: Dict[str, Any],
        current_schedule: List[ScheduleBlock],
        availability: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> SchedulingResult:
        """Generate reschedule options for user to choose from"""
        
        options = []
        
        # Option 1: Next available slot
        next_slot = self._find_next_available_slot(missed_task, availability)
        if next_slot:
            options.append({
                'option': 'next_available',
                'description': f"Schedule for {next_slot['start'].strftime('%A %H:%M')}",
                'impact': 'No changes to existing schedule'
            })
        
        # Option 2: Optimize entire week
        options.append({
            'option': 'reprioritize_week',
            'description': 'Reorganize entire week for better fit',
            'impact': 'May move other tasks for optimal scheduling'
        })
        
        # Option 3: Skip this time
        options.append({
            'option': 'skip_once',
            'description': 'Skip this occurrence, keep future schedule',
            'impact': 'Task will not be rescheduled'
        })
        
        explanation = (
            f"Task '{missed_task.get('title', 'Unknown')}' was missed. "
            f"Please choose how you'd like to reschedule:"
        )
        
        return SchedulingResult(
            success=False,  # Requires user input
            schedule=[],
            overall_explanation=explanation,
            confidence_score=0.0,
            preview_mode=True,
            requires_user_confirmation=True,
            unscheduled_tasks=[missed_task],
            scheduling_metrics={'reschedule_options': options},
            suggested_preference_updates=[]
        )
    
    # Additional helper methods would continue...
    
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
    
    def _generate_slot_selection_reason(
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
    
    def _identify_tradeoffs(self, selected_slot: Dict[str, datetime], alternatives: List[str]) -> List[str]:
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
    
    def _get_applied_constraints(self, user_preferences: UserPreferences) -> List[str]:
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
    
    def _get_honored_preferences(
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
    
    def _remove_from_availability(self, availability: Dict[str, Any], scheduled_block: ScheduleBlock):
        """Remove scheduled time from availability"""
        # This would update the availability dict to reflect the newly scheduled block
        # Implementation would depend on the specific availability data structure
        pass
    
    def _generate_metrics(
        self,
        scheduled_blocks: List[ScheduleBlock],
        unscheduled_tasks: List[Dict[str, Any]],
        original_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive scheduling metrics"""
        return {
            'total_tasks': len(original_tasks),
            'scheduled_tasks': len(scheduled_blocks),
            'unscheduled_tasks': len(unscheduled_tasks),
            'success_rate': len(scheduled_blocks) / len(original_tasks) if original_tasks else 0,
            'average_confidence': self._calculate_overall_confidence(scheduled_blocks),
            'preferences_honored': sum(
                len(block.explanation.preferences_honored) for block in scheduled_blocks
            ),
            'preferences_flexed': sum(
                len(block.explanation.preferences_flexed) for block in scheduled_blocks
            ),
            'total_scheduled_minutes': sum(block.duration_minutes for block in scheduled_blocks)
        }
    
    def _generate_preference_suggestions(self, user_preferences: UserPreferences) -> List[str]:
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
    
    def _reschedule_to_next_slot(
        self,
        missed_task: Dict[str, Any],
        current_schedule: List[ScheduleBlock],
        availability: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> SchedulingResult:
        """Reschedule missed task to next available slot"""
        
        next_slot = self._find_next_available_slot(missed_task, availability)
        
        if not next_slot:
            return SchedulingResult(
                success=False,
                schedule=[],
                overall_explanation="No available slots found for rescheduling",
                confidence_score=0.0,
                preview_mode=True,
                requires_user_confirmation=False,
                unscheduled_tasks=[missed_task],
                scheduling_metrics={},
                suggested_preference_updates=[]
            )
        
        # Create rescheduled block
        rescheduled_block = ScheduleBlock(
            id=f"rescheduled_{missed_task.get('id', 'unknown')}_{datetime.now().timestamp()}",
            title=missed_task.get('title', 'Rescheduled Task'),
            type=missed_task.get('type', 'task'),
            priority=Priority(self._get_priority_value(missed_task.get('priority', 'medium'))),
            start_time=next_slot['start'],
            end_time=next_slot['end'],
            duration_minutes=missed_task.get('estimated_minutes', 60),
            explanation=ScheduleExplanation(
                decision_type=SchedulingDecision.OPTIMAL_PLACEMENT,
                reason=f"Rescheduled to next available slot: {next_slot['start'].strftime('%A, %B %d at %H:%M')}",
                confidence_score=0.8,
                tradeoffs=["Moved to accommodate missed task"],
                alternatives_considered=["Skip task", "Reprioritize week"],
                constraints_applied=self._get_applied_constraints(user_preferences),
                preferences_honored=[],
                preferences_flexed=[]
            )
        )
        
        explanation = (
            f"Rescheduled '{missed_task.get('title', 'Unknown')}' to "
            f"{next_slot['start'].strftime('%A, %B %d at %H:%M')}. "
            f"This was the next available slot that fits your constraints."
        )
        
        return SchedulingResult(
            success=True,
            schedule=[rescheduled_block],
            overall_explanation=explanation,
            confidence_score=0.8,
            preview_mode=True,
            requires_user_confirmation=True,
            unscheduled_tasks=[],
            scheduling_metrics={'reschedule_strategy': 'next_available'},
            suggested_preference_updates=[]
        )
    
    def _reprioritize_entire_week(
        self,
        missed_task: Dict[str, Any],
        current_schedule: List[ScheduleBlock],
        availability: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> SchedulingResult:
        """Reprioritize entire week to optimally fit the missed task"""
        
        # Convert current schedule back to tasks
        all_tasks = [missed_task]  # Start with missed task
        
        for block in current_schedule:
            if block.auto_reschedulable:
                task = {
                    'id': block.id,
                    'title': block.title,
                    'type': block.type,
                    'priority': block.priority.name.lower(),
                    'estimated_minutes': block.duration_minutes
                }
                all_tasks.append(task)
        
        # Reschedule everything
        return self.schedule_tasks(all_tasks, availability, user_preferences, preview_mode=True)
    
    def _find_next_available_slot(
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
    
    # Helper methods for scoring
    
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