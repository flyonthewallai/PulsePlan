"""
Transparent Scheduling and Rescheduling Tools
Implements intelligent scheduling with full transparency and user preference handling
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .models import (
    Priority,
    SchedulingDecision,
    ScheduleExplanation,
    ScheduleBlock,
    UserPreferences,
    SchedulingResult
)
from .decision_maker import DecisionMaker
from .explanation_generator import ExplanationGenerator
from .block_allocator import BlockAllocator

logger = logging.getLogger(__name__)


class TransparentScheduler:
    """
    Intelligent scheduler that provides full transparency on all decisions
    Follows the transparency guidelines for explainable scheduling
    """

    def __init__(self):
        self.decision_log: List[Dict[str, Any]] = []
        self.preference_violations: List[str] = []
        self.decision_maker = DecisionMaker()
        self.explanation_generator = ExplanationGenerator()
        self.block_allocator = BlockAllocator(self.decision_log)

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
        prioritized_tasks = self.decision_maker.prioritize_tasks(tasks, user_preferences)

        # Step 2: Find optimal time slots for each task
        scheduled_blocks = []
        unscheduled_tasks = []

        for task in prioritized_tasks:
            result = self.block_allocator.find_optimal_slot(
                task, availability, user_preferences, scheduled_blocks, self.explanation_generator
            )

            if result:
                scheduled_blocks.append(result)
                # Update availability
                self.block_allocator.remove_from_availability(availability, result)
            else:
                unscheduled_tasks.append(task)

        # Step 3: Generate overall explanation and metrics
        overall_explanation = self.explanation_generator.generate_overall_explanation(
            scheduled_blocks, unscheduled_tasks, user_preferences
        )

        # Step 4: Calculate confidence and determine if confirmation needed
        confidence_score = self.explanation_generator.calculate_overall_confidence(scheduled_blocks)
        requires_confirmation = self.decision_maker.requires_user_confirmation(
            scheduled_blocks, user_preferences, self.explanation_generator.calculate_overall_confidence
        )

        # Step 5: Generate metrics and suggestions
        metrics = self.decision_maker.generate_metrics(
            scheduled_blocks, unscheduled_tasks, tasks, self.explanation_generator.calculate_overall_confidence
        )
        suggestions = self.decision_maker.generate_preference_suggestions(user_preferences)

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

    # Private helper methods for rescheduling

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
        next_slot = self.block_allocator.find_next_available_slot(missed_task, availability)
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

    def _reschedule_to_next_slot(
        self,
        missed_task: Dict[str, Any],
        current_schedule: List[ScheduleBlock],
        availability: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> SchedulingResult:
        """Reschedule missed task to next available slot"""

        next_slot = self.block_allocator.find_next_available_slot(missed_task, availability)

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
            priority=Priority(self.decision_maker._get_priority_value(missed_task.get('priority', 'medium'))),
            start_time=next_slot['start'],
            end_time=next_slot['end'],
            duration_minutes=missed_task.get('estimated_minutes', 60),
            explanation=ScheduleExplanation(
                decision_type=SchedulingDecision.OPTIMAL_PLACEMENT,
                reason=f"Rescheduled to next available slot: {next_slot['start'].strftime('%A, %B %d at %H:%M')}",
                confidence_score=0.8,
                tradeoffs=["Moved to accommodate missed task"],
                alternatives_considered=["Skip task", "Reprioritize week"],
                constraints_applied=self.explanation_generator.get_applied_constraints(user_preferences),
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
