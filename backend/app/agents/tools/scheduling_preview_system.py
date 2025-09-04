"""
Scheduling Preview and Confirmation System
Implements preview-before-commit functionality with user interaction hooks
"""
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

from .transparent_scheduler import (
    TransparentScheduler, 
    SchedulingResult, 
    ScheduleBlock, 
    UserPreferences,
    ScheduleExplanation,
    SchedulingDecision
)

logger = logging.getLogger(__name__)


class PreviewAction(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    RESCHEDULE = "reschedule"
    REQUEST_CHANGES = "request_changes"


@dataclass
class PreviewFeedback:
    """User feedback on a scheduling preview"""
    action: PreviewAction
    block_modifications: List[Dict[str, Any]]
    preference_updates: List[Dict[str, Any]]
    comments: str
    confidence_threshold: Optional[float] = None


@dataclass 
class PreviewResponse:
    """Response to a scheduling preview"""
    approved: bool
    feedback: Optional[PreviewFeedback]
    final_schedule: Optional[List[ScheduleBlock]]
    commit_to_calendar: bool = False


class SchedulingPreviewSystem:
    """
    Manages preview-before-commit scheduling workflow
    Implements transparency guidelines for user interaction
    """
    
    def __init__(self, scheduler: Optional[TransparentScheduler] = None):
        self.scheduler = scheduler or TransparentScheduler()
        self.preview_history: List[Dict[str, Any]] = []
        
    def generate_preview(
        self,
        tasks: List[Dict[str, Any]],
        availability: Dict[str, Any],
        user_preferences: UserPreferences,
        auto_commit_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """
        Generate scheduling preview with interactive options
        
        Args:
            tasks: Tasks to schedule
            availability: Available time slots
            user_preferences: User preferences and constraints
            auto_commit_threshold: Confidence threshold for auto-commit
            
        Returns:
            Interactive preview with options for user
        """
        logger.info(f"Generating scheduling preview for {len(tasks)} tasks")
        
        # Generate initial schedule
        scheduling_result = self.scheduler.schedule_tasks(
            tasks=tasks,
            availability=availability,
            user_preferences=user_preferences,
            preview_mode=True
        )
        
        # Create interactive preview
        preview = {
            'preview_id': f"preview_{datetime.now().timestamp()}",
            'generated_at': datetime.now().isoformat(),
            'scheduling_result': self._serialize_scheduling_result(scheduling_result),
            'interactive_elements': self._create_interactive_elements(scheduling_result),
            'user_options': self._generate_user_options(scheduling_result, user_preferences),
            'auto_commit_eligible': scheduling_result.confidence_score >= auto_commit_threshold,
            'explanation_summary': self._create_explanation_summary(scheduling_result),
            'actionable_insights': self._generate_actionable_insights(scheduling_result)
        }
        
        # Store preview in history
        self.preview_history.append({
            'preview_id': preview['preview_id'],
            'timestamp': datetime.now().isoformat(),
            'result': scheduling_result,
            'user_preferences': user_preferences
        })
        
        return preview
    
    def process_user_response(
        self,
        preview_id: str,
        user_response: Dict[str, Any]
    ) -> PreviewResponse:
        """
        Process user response to scheduling preview
        
        Args:
            preview_id: ID of the preview being responded to
            user_response: User's response and feedback
            
        Returns:
            Preview response with final schedule if approved
        """
        logger.info(f"Processing user response for preview {preview_id}")
        
        # Find the preview in history
        preview_data = next(
            (p for p in self.preview_history if p['preview_id'] == preview_id),
            None
        )
        
        if not preview_data:
            raise ValueError(f"Preview {preview_id} not found")
        
        # Parse user response
        action = PreviewAction(user_response.get('action', 'approve'))
        
        if action == PreviewAction.APPROVE:
            return self._handle_approval(preview_data, user_response)
        elif action == PreviewAction.REJECT:
            return self._handle_rejection(preview_data, user_response)
        elif action == PreviewAction.MODIFY:
            return self._handle_modifications(preview_data, user_response)
        elif action == PreviewAction.RESCHEDULE:
            return self._handle_reschedule_request(preview_data, user_response)
        elif action == PreviewAction.REQUEST_CHANGES:
            return self._handle_change_request(preview_data, user_response)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def handle_missed_task_reschedule(
        self,
        missed_task: Dict[str, Any],
        current_schedule: List[ScheduleBlock],
        availability: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """
        Handle rescheduling of missed task with user interaction
        
        Args:
            missed_task: The task that was missed
            current_schedule: Current schedule blocks
            availability: Updated availability
            user_preferences: User preferences
            
        Returns:
            Interactive reschedule options
        """
        logger.info(f"Handling missed task reschedule: {missed_task.get('title', 'Unknown')}")
        
        # Generate reschedule options
        reschedule_preview = {
            'missed_task': missed_task,
            'reschedule_id': f"reschedule_{datetime.now().timestamp()}",
            'generated_at': datetime.now().isoformat(),
            'options': []
        }
        
        # Option 1: Next available slot
        next_slot_result = self.scheduler.reschedule_missed_task(
            missed_task=missed_task,
            current_schedule=current_schedule,
            availability=availability,
            user_preferences=user_preferences,
            reschedule_strategy="next_available"
        )
        
        reschedule_preview['options'].append({
            'strategy': 'next_available',
            'title': 'Move to Next Available Slot',
            'description': 'Schedule this task at the next available time that fits your constraints',
            'result': self._serialize_scheduling_result(next_slot_result),
            'impact': 'No changes to existing schedule',
            'confidence': next_slot_result.confidence_score
        })
        
        # Option 2: Reprioritize week
        reprioritize_result = self.scheduler.reschedule_missed_task(
            missed_task=missed_task,
            current_schedule=current_schedule,
            availability=availability,
            user_preferences=user_preferences,
            reschedule_strategy="reprioritize_week"
        )
        
        reschedule_preview['options'].append({
            'strategy': 'reprioritize_week',
            'title': 'Reorganize Entire Week',
            'description': 'Reschedule all flexible tasks for optimal week-long organization',
            'result': self._serialize_scheduling_result(reprioritize_result),
            'impact': f'May reschedule {len(current_schedule)} existing tasks',
            'confidence': reprioritize_result.confidence_score
        })
        
        # Option 3: Skip this time
        reschedule_preview['options'].append({
            'strategy': 'skip_once',
            'title': 'Skip This Time',
            'description': 'Do not reschedule this occurrence, keep future instances',
            'result': None,
            'impact': 'Task will be marked as skipped',
            'confidence': 1.0
        })
        
        # Add recommendation
        reschedule_preview['recommendation'] = self._get_reschedule_recommendation(
            reschedule_preview['options'], missed_task, user_preferences
        )
        
        return reschedule_preview
    
    def update_user_preferences_from_feedback(
        self,
        user_preferences: UserPreferences,
        feedback_history: List[Dict[str, Any]]
    ) -> UserPreferences:
        """
        Update user preferences based on historical feedback
        
        Args:
            user_preferences: Current preferences
            feedback_history: History of user feedback and corrections
            
        Returns:
            Updated preferences
        """
        logger.info("Updating user preferences from feedback history")
        
        updated_preferences = user_preferences
        
        # Analyze feedback patterns
        preference_adjustments = {}
        
        for feedback in feedback_history:
            # Process block modifications
            for modification in feedback.get('block_modifications', []):
                if modification['type'] == 'time_change':
                    # User prefers different times
                    old_hour = datetime.fromisoformat(modification['old_time']).hour
                    new_hour = datetime.fromisoformat(modification['new_time']).hour
                    
                    if new_hour < 12 and old_hour >= 12:
                        preference_adjustments['morning_preference'] = (
                            preference_adjustments.get('morning_preference', 0) + 0.1
                        )
                    elif new_hour >= 12 and old_hour < 12:
                        preference_adjustments['afternoon_preference'] = (
                            preference_adjustments.get('afternoon_preference', 0) + 0.1
                        )
            
            # Process explicit preference updates
            for pref_update in feedback.get('preference_updates', []):
                pref_type = pref_update['type']
                pref_adjustment = pref_update['adjustment']
                
                preference_adjustments[pref_type] = (
                    preference_adjustments.get(pref_type, 0) + pref_adjustment
                )
        
        # Apply adjustments
        for pref_type, adjustment in preference_adjustments.items():
            if pref_type in updated_preferences.behavioral_weights:
                current_weight = updated_preferences.behavioral_weights[pref_type]
                new_weight = max(0.0, min(1.0, current_weight + adjustment))
                updated_preferences.behavioral_weights[pref_type] = new_weight
                
                logger.info(f"Updated preference: {pref_type} = {new_weight:.3f}")
        
        return updated_preferences
    
    # Private helper methods
    
    def _serialize_scheduling_result(self, result: SchedulingResult) -> Dict[str, Any]:
        """Serialize SchedulingResult for JSON transmission"""
        return {
            'success': result.success,
            'schedule': [self._serialize_schedule_block(block) for block in result.schedule],
            'overall_explanation': result.overall_explanation,
            'confidence_score': result.confidence_score,
            'preview_mode': result.preview_mode,
            'requires_user_confirmation': result.requires_user_confirmation,
            'unscheduled_tasks': result.unscheduled_tasks,
            'scheduling_metrics': result.scheduling_metrics,
            'suggested_preference_updates': result.suggested_preference_updates
        }
    
    def _serialize_schedule_block(self, block: ScheduleBlock) -> Dict[str, Any]:
        """Serialize ScheduleBlock for JSON transmission"""
        return {
            'id': block.id,
            'title': block.title,
            'type': block.type,
            'priority': block.priority.name.lower(),
            'start_time': block.start_time.isoformat(),
            'end_time': block.end_time.isoformat(),
            'duration_minutes': block.duration_minutes,
            'explanation': self._serialize_explanation(block.explanation),
            'user_editable': block.user_editable,
            'auto_reschedulable': block.auto_reschedulable
        }
    
    def _serialize_explanation(self, explanation: ScheduleExplanation) -> Dict[str, Any]:
        """Serialize ScheduleExplanation for JSON transmission"""
        return {
            'decision_type': explanation.decision_type.value,
            'reason': explanation.reason,
            'confidence_score': explanation.confidence_score,
            'tradeoffs': explanation.tradeoffs,
            'alternatives_considered': explanation.alternatives_considered,
            'constraints_applied': explanation.constraints_applied,
            'preferences_honored': explanation.preferences_honored,
            'preferences_flexed': explanation.preferences_flexed
        }
    
    def _create_interactive_elements(self, result: SchedulingResult) -> Dict[str, Any]:
        """Create interactive UI elements for the preview"""
        elements = {
            'schedule_timeline': self._create_timeline_data(result.schedule),
            'editable_blocks': [
                {
                    'block_id': block.id,
                    'editable_fields': ['start_time', 'duration_minutes'] if block.user_editable else [],
                    'drag_drop_enabled': block.user_editable,
                    'alternative_slots': self._get_alternative_slots(block)
                }
                for block in result.schedule
            ],
            'preference_sliders': self._create_preference_sliders(),
            'constraint_toggles': self._create_constraint_toggles(),
            'feedback_prompts': self._create_feedback_prompts(result)
        }
        
        return elements
    
    def _generate_user_options(
        self, 
        result: SchedulingResult, 
        user_preferences: UserPreferences
    ) -> List[Dict[str, Any]]:
        """Generate actionable options for the user"""
        options = []
        
        # Always provide approval/rejection options
        options.extend([
            {
                'action': 'approve',
                'label': 'Accept Schedule',
                'description': 'Approve and commit this schedule to your calendar',
                'primary': True,
                'enabled': True
            },
            {
                'action': 'reject',
                'label': 'Reject Schedule',
                'description': 'Reject this schedule and start over',
                'primary': False,
                'enabled': True
            }
        ])
        
        # Conditional modification options
        if any(block.user_editable for block in result.schedule):
            options.append({
                'action': 'modify',
                'label': 'Make Changes',
                'description': 'Adjust specific time slots or preferences',
                'primary': False,
                'enabled': True
            })
        
        # Rescheduling option if confidence is low
        if result.confidence_score < 0.7:
            options.append({
                'action': 'reschedule',
                'label': 'Try Different Approach',
                'description': 'Generate alternative schedule with different priorities',
                'primary': False,
                'enabled': True
            })
        
        # Preference update option if many preferences were flexed
        preferences_flexed = sum(
            len(block.explanation.preferences_flexed) for block in result.schedule
        )
        
        if preferences_flexed > len(result.schedule) * 0.3:
            options.append({
                'action': 'request_changes',
                'label': 'Update Preferences',
                'description': 'Adjust your preferences to better match this scheduling pattern',
                'primary': False,
                'enabled': True
            })
        
        return options
    
    def _create_explanation_summary(self, result: SchedulingResult) -> Dict[str, Any]:
        """Create a structured summary of scheduling explanations"""
        return {
            'main_explanation': result.overall_explanation,
            'key_decisions': [
                {
                    'block_title': block.title,
                    'decision': block.explanation.reason,
                    'confidence': block.explanation.confidence_score,
                    'tradeoffs': block.explanation.tradeoffs
                }
                for block in result.schedule[:3]  # Top 3 most important decisions
            ],
            'constraint_summary': self._summarize_constraints(result.schedule),
            'preference_summary': self._summarize_preferences(result.schedule),
            'metrics_summary': {
                'success_rate': f"{result.scheduling_metrics.get('success_rate', 0) * 100:.0f}%",
                'average_confidence': f"{result.confidence_score:.1f}/1.0",
                'total_time_scheduled': f"{result.scheduling_metrics.get('total_scheduled_minutes', 0)} minutes"
            }
        }
    
    def _generate_actionable_insights(self, result: SchedulingResult) -> List[Dict[str, Any]]:
        """Generate actionable insights from the scheduling result"""
        insights = []
        
        # Low confidence insight
        if result.confidence_score < 0.6:
            insights.append({
                'type': 'warning',
                'title': 'Low Confidence Schedule',
                'message': 'This schedule required significant compromises. Consider adjusting your preferences or reducing task load.',
                'actions': ['Update preferences', 'Remove low-priority tasks']
            })
        
        # Unscheduled tasks insight
        if result.unscheduled_tasks:
            high_priority_unscheduled = sum(
                1 for task in result.unscheduled_tasks 
                if task.get('priority', 'medium') in ['urgent', 'high']
            )
            
            if high_priority_unscheduled > 0:
                insights.append({
                    'type': 'error',
                    'title': 'High-Priority Tasks Unscheduled',
                    'message': f'{high_priority_unscheduled} high-priority tasks could not be scheduled.',
                    'actions': ['Extend working hours', 'Reschedule lower-priority tasks', 'Delegate tasks']
                })
        
        # Preference violation insight
        preferences_violated = sum(
            len(block.explanation.preferences_flexed) for block in result.schedule
        )
        
        if preferences_violated > len(result.schedule) * 0.4:
            insights.append({
                'type': 'info',
                'title': 'Many Preferences Adjusted',
                'message': 'We had to adjust many of your preferences to fit everything in.',
                'actions': ['Review and update preferences', 'Consider longer time blocks']
            })
        
        return insights
    
    def _handle_approval(self, preview_data: Dict[str, Any], user_response: Dict[str, Any]) -> PreviewResponse:
        """Handle user approval of schedule"""
        result = preview_data['result']
        
        return PreviewResponse(
            approved=True,
            feedback=None,
            final_schedule=result.schedule,
            commit_to_calendar=user_response.get('commit_to_calendar', True)
        )
    
    def _handle_rejection(self, preview_data: Dict[str, Any], user_response: Dict[str, Any]) -> PreviewResponse:
        """Handle user rejection of schedule"""
        return PreviewResponse(
            approved=False,
            feedback=PreviewFeedback(
                action=PreviewAction.REJECT,
                block_modifications=[],
                preference_updates=[],
                comments=user_response.get('rejection_reason', 'User rejected the schedule')
            ),
            final_schedule=None,
            commit_to_calendar=False
        )
    
    def _handle_modifications(self, preview_data: Dict[str, Any], user_response: Dict[str, Any]) -> PreviewResponse:
        """Handle user modifications to schedule"""
        modifications = user_response.get('modifications', [])
        
        # Apply modifications to create new schedule
        # This would involve re-running the scheduler with user constraints
        
        feedback = PreviewFeedback(
            action=PreviewAction.MODIFY,
            block_modifications=modifications,
            preference_updates=[],
            comments=user_response.get('comments', 'User requested modifications')
        )
        
        return PreviewResponse(
            approved=False,  # Requires re-preview after modifications
            feedback=feedback,
            final_schedule=None,
            commit_to_calendar=False
        )
    
    # Additional helper methods...
    
    def _create_timeline_data(self, schedule: List[ScheduleBlock]) -> Dict[str, Any]:
        """Create timeline visualization data"""
        return {
            'blocks': [
                {
                    'id': block.id,
                    'title': block.title,
                    'start': block.start_time.isoformat(),
                    'end': block.end_time.isoformat(),
                    'type': block.type,
                    'priority': block.priority.name.lower(),
                    'confidence': block.explanation.confidence_score
                }
                for block in sorted(schedule, key=lambda b: b.start_time)
            ]
        }
    
    def _get_alternative_slots(self, block: ScheduleBlock) -> List[Dict[str, Any]]:
        """Get alternative time slots for a block"""
        # This would generate alternative slots based on availability
        # For now, return empty list
        return []
    
    def _create_preference_sliders(self) -> List[Dict[str, Any]]:
        """Create preference adjustment sliders"""
        return [
            {
                'id': 'morning_preference',
                'label': 'Morning Preference',
                'description': 'How much you prefer morning time slots',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1
            },
            {
                'id': 'meeting_clustering',
                'label': 'Meeting Clustering',
                'description': 'Prefer meetings grouped together',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1
            },
            {
                'id': 'focus_time_protection',
                'label': 'Focus Time Protection',
                'description': 'Protect dedicated focus time blocks',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1
            }
        ]
    
    def _get_reschedule_recommendation(
        self,
        options: List[Dict[str, Any]],
        missed_task: Dict[str, Any],
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """Get recommendation for reschedule strategy"""
        
        # Recommend based on confidence scores and impact
        best_option = max(options, key=lambda o: o.get('confidence', 0))
        
        return {
            'recommended_strategy': best_option['strategy'],
            'reason': f"Highest confidence option ({best_option.get('confidence', 0):.1f}) with {best_option.get('impact', 'minimal impact')}",
            'alternative': f"Consider '{options[1]['strategy']}' if you prefer different trade-offs"
        }