"""
Transparent Scheduling API
High-level API that integrates transparent scheduling with preview and confirmation
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .transparent_scheduler import (
    TransparentScheduler,
    UserPreferences,
    SchedulingResult,
    ScheduleBlock
)
from .scheduling_preview_system import SchedulingPreviewSystem, PreviewResponse

logger = logging.getLogger(__name__)


class TransparentSchedulingAPI:
    """
    Main API for transparent scheduling and rescheduling operations
    Implements all transparency guidelines and user interaction patterns
    """
    
    def __init__(self):
        self.scheduler = TransparentScheduler()
        self.preview_system = SchedulingPreviewSystem(self.scheduler)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_schedule_preview(
        self,
        user_id: str,
        tasks: List[Dict[str, Any]],
        availability: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
        auto_commit_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """
        Create a scheduling preview with full transparency
        
        Args:
            user_id: Unique identifier for the user
            tasks: List of tasks to schedule
            availability: Available time slots
            user_preferences: User preferences and constraints
            auto_commit_threshold: Confidence threshold for auto-commit
            
        Returns:
            Interactive preview with explanations and options
        """
        logger.info(f"Creating schedule preview for user {user_id} with {len(tasks)} tasks")
        
        # Convert preferences to internal format
        preferences = self._convert_user_preferences(user_preferences or {})
        
        # Generate preview
        preview = self.preview_system.generate_preview(
            tasks=tasks,
            availability=availability,
            user_preferences=preferences,
            auto_commit_threshold=auto_commit_threshold
        )
        
        # Store session data
        self.user_sessions[user_id] = {
            'last_preview_id': preview['preview_id'],
            'preferences': preferences,
            'tasks': tasks,
            'availability': availability
        }
        
        return {
            'success': True,
            'preview': preview,
            'user_instructions': self._generate_user_instructions(preview),
            'api_endpoints': self._get_api_endpoints()
        }
    
    def confirm_schedule(
        self,
        user_id: str,
        preview_id: str,
        user_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user confirmation or modification of schedule
        
        Args:
            user_id: User identifier
            preview_id: Preview being responded to
            user_response: User's response and feedback
            
        Returns:
            Final scheduling result or new preview if modifications needed
        """
        logger.info(f"Processing schedule confirmation for user {user_id}, preview {preview_id}")
        
        try:
            response = self.preview_system.process_user_response(
                preview_id=preview_id,
                user_response=user_response
            )
            
            if response.approved:
                # Schedule is approved - commit if requested
                result = {
                    'success': True,
                    'approved': True,
                    'schedule': [self._serialize_block(block) for block in response.final_schedule],
                    'commit_status': 'pending'
                }
                
                if response.commit_to_calendar:
                    commit_result = self._commit_to_calendar(user_id, response.final_schedule)
                    result['commit_status'] = 'completed' if commit_result else 'failed'
                
                return result
            else:
                # Schedule needs modification - handle based on feedback
                return self._handle_schedule_modification(user_id, response)
        
        except Exception as e:
            logger.error(f"Error processing schedule confirmation: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process schedule confirmation'
            }
    
    def reschedule_missed_task(
        self,
        user_id: str,
        missed_task: Dict[str, Any],
        current_schedule: Optional[List[Dict[str, Any]]] = None,
        availability: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle rescheduling of a missed task with user interaction
        
        Args:
            user_id: User identifier
            missed_task: The task that was missed
            current_schedule: Current schedule (optional, will fetch if not provided)
            availability: Updated availability (optional, will fetch if not provided)
            
        Returns:
            Interactive reschedule options
        """
        logger.info(f"Handling missed task reschedule for user {user_id}: {missed_task.get('title', 'Unknown')}")
        
        # Get user data
        session_data = self.user_sessions.get(user_id, {})
        preferences = session_data.get('preferences')
        
        if not preferences:
            return {
                'success': False,
                'error': 'User preferences not found',
                'message': 'Please create a schedule first to establish preferences'
            }
        
        # Use provided data or defaults
        if current_schedule is None:
            current_schedule = []  # Would fetch from database
        
        if availability is None:
            availability = session_data.get('availability', {})
        
        # Convert current schedule to internal format
        schedule_blocks = [self._deserialize_block(block) for block in current_schedule]
        
        # Generate reschedule options
        reschedule_preview = self.preview_system.handle_missed_task_reschedule(
            missed_task=missed_task,
            current_schedule=schedule_blocks,
            availability=availability,
            user_preferences=preferences
        )
        
        return {
            'success': True,
            'reschedule_preview': reschedule_preview,
            'user_instructions': self._generate_reschedule_instructions(reschedule_preview),
            'api_endpoints': self._get_api_endpoints()
        }
    
    def update_preferences(
        self,
        user_id: str,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user preferences based on feedback
        
        Args:
            user_id: User identifier
            feedback: User feedback on scheduling decisions
            
        Returns:
            Updated preferences and confirmation
        """
        logger.info(f"Updating preferences for user {user_id}")
        
        session_data = self.user_sessions.get(user_id, {})
        current_preferences = session_data.get('preferences')
        
        if not current_preferences:
            return {
                'success': False,
                'error': 'No existing preferences found',
                'message': 'Please create a schedule first to establish preferences'
            }
        
        # Update preferences
        updated_preferences = self.scheduler.update_preferences(
            user_preferences=current_preferences,
            feedback=feedback
        )
        
        # Store updated preferences
        session_data['preferences'] = updated_preferences
        self.user_sessions[user_id] = session_data
        
        return {
            'success': True,
            'updated_preferences': self._serialize_preferences(updated_preferences),
            'changes_summary': self._summarize_preference_changes(current_preferences, updated_preferences),
            'recommendation': 'Consider regenerating your schedule with updated preferences'
        }
    
    def get_scheduling_insights(
        self,
        user_id: str,
        time_period: str = 'week'
    ) -> Dict[str, Any]:
        """
        Get insights about scheduling patterns and suggestions
        
        Args:
            user_id: User identifier
            time_period: Time period for analysis ('day', 'week', 'month')
            
        Returns:
            Scheduling insights and recommendations
        """
        logger.info(f"Generating scheduling insights for user {user_id}")
        
        # This would analyze historical scheduling data
        # For now, return mock insights
        
        return {
            'success': True,
            'time_period': time_period,
            'insights': {
                'productivity_patterns': {
                    'peak_hours': ['09:00-11:00', '14:00-16:00'],
                    'low_energy_periods': ['13:00-14:00', '16:00-17:00'],
                    'preferred_task_types_by_hour': {
                        'morning': ['focus_work', 'important_tasks'],
                        'afternoon': ['meetings', 'collaborative_work']
                    }
                },
                'scheduling_effectiveness': {
                    'average_confidence': 0.82,
                    'tasks_completed_on_time': 0.85,
                    'preference_adherence': 0.75,
                    'common_conflicts': ['lunch_meetings', 'back_to_back_meetings']
                },
                'recommendations': [
                    'Consider blocking 13:00-14:00 for lunch to avoid scheduling conflicts',
                    'Your morning productivity is high - prioritize important tasks then',
                    'Meeting clustering works well for you - continue this pattern'
                ]
            }
        }
    
    # Private helper methods
    
    def _convert_user_preferences(self, prefs: Dict[str, Any]) -> UserPreferences:
        """Convert API preferences to internal UserPreferences format"""
        hard_constraints = prefs.get('hard_constraints', {})
        soft_preferences = prefs.get('soft_preferences', {})
        
        # Set defaults
        if 'work_start' not in hard_constraints:
            hard_constraints['work_start'] = '09:00'
        if 'work_end' not in hard_constraints:
            hard_constraints['work_end'] = '17:00'
        
        behavioral_weights = prefs.get('behavioral_weights', {
            'morning_preference': 0.7,
            'afternoon_preference': 0.5,
            'meeting_clustering': 0.6,
            'focus_time_protection': 0.8
        })
        
        return UserPreferences(
            hard_constraints=hard_constraints,
            soft_preferences=soft_preferences,
            behavioral_weights=behavioral_weights
        )
    
    def _serialize_block(self, block: ScheduleBlock) -> Dict[str, Any]:
        """Serialize a ScheduleBlock for API response"""
        return {
            'id': block.id,
            'title': block.title,
            'type': block.type,
            'priority': block.priority.name.lower(),
            'start_time': block.start_time.isoformat(),
            'end_time': block.end_time.isoformat(),
            'duration_minutes': block.duration_minutes,
            'explanation': {
                'reason': block.explanation.reason,
                'confidence_score': block.explanation.confidence_score,
                'tradeoffs': block.explanation.tradeoffs,
                'preferences_honored': block.explanation.preferences_honored,
                'preferences_flexed': block.explanation.preferences_flexed
            },
            'editable': block.user_editable,
            'auto_reschedulable': block.auto_reschedulable
        }
    
    def _deserialize_block(self, data: Dict[str, Any]) -> ScheduleBlock:
        """Deserialize block data to ScheduleBlock (simplified for example)"""
        # This would be a full implementation to reconstruct ScheduleBlock
        # For now, return a minimal implementation
        pass
    
    def _serialize_preferences(self, preferences: UserPreferences) -> Dict[str, Any]:
        """Serialize UserPreferences for API response"""
        return {
            'hard_constraints': preferences.hard_constraints,
            'soft_preferences': preferences.soft_preferences,
            'behavioral_weights': preferences.behavioral_weights
        }
    
    def _commit_to_calendar(self, user_id: str, schedule: List[ScheduleBlock]) -> bool:
        """Commit schedule to external calendar (mock implementation)"""
        logger.info(f"Committing {len(schedule)} blocks to calendar for user {user_id}")
        
        # This would integrate with calendar APIs (Google Calendar, Outlook, etc.)
        # For now, return success
        return True
    
    def _generate_user_instructions(self, preview: Dict[str, Any]) -> Dict[str, Any]:
        """Generate instructions for interacting with the preview"""
        return {
            'how_to_approve': 'Send POST to /api/scheduling/confirm with action: "approve"',
            'how_to_modify': 'Send POST to /api/scheduling/confirm with action: "modify" and specific changes',
            'how_to_reject': 'Send POST to /api/scheduling/confirm with action: "reject" and reason',
            'available_actions': [opt['action'] for opt in preview.get('user_options', [])],
            'confidence_explanation': f"Confidence score: {preview['scheduling_result']['confidence_score']:.1f}/1.0 - " +
                                   ("High confidence, safe to auto-approve" if preview['scheduling_result']['confidence_score'] >= 0.8 
                                    else "Review recommended due to compromises made")
        }
    
    def _generate_reschedule_instructions(self, reschedule_preview: Dict[str, Any]) -> Dict[str, Any]:
        """Generate instructions for reschedule options"""
        return {
            'how_to_select_option': 'Send POST to /api/scheduling/reschedule/confirm with selected strategy',
            'available_strategies': [opt['strategy'] for opt in reschedule_preview.get('options', [])],
            'recommended_strategy': reschedule_preview.get('recommendation', {}).get('recommended_strategy', 'next_available'),
            'impact_summary': {
                opt['strategy']: opt['impact'] for opt in reschedule_preview.get('options', [])
            }
        }
    
    def _get_api_endpoints(self) -> Dict[str, str]:
        """Get available API endpoints"""
        return {
            'confirm_schedule': 'POST /api/scheduling/confirm',
            'update_preferences': 'POST /api/scheduling/preferences',
            'reschedule_task': 'POST /api/scheduling/reschedule',
            'get_insights': 'GET /api/scheduling/insights',
            'create_preview': 'POST /api/scheduling/preview'
        }
    
    def _handle_schedule_modification(self, user_id: str, response: PreviewResponse) -> Dict[str, Any]:
        """Handle schedule modification requests"""
        # This would regenerate the schedule with modifications
        # For now, return a placeholder
        return {
            'success': True,
            'action_required': 'regenerate_preview',
            'message': 'Schedule modifications received. Please regenerate preview.',
            'feedback_recorded': True,
            'next_step': 'Create new preview with updated constraints'
        }
    
    def _summarize_preference_changes(
        self,
        old_prefs: UserPreferences,
        new_prefs: UserPreferences
    ) -> List[str]:
        """Summarize changes made to preferences"""
        changes = []
        
        for key in new_prefs.behavioral_weights:
            old_value = old_prefs.behavioral_weights.get(key, 0.5)
            new_value = new_prefs.behavioral_weights[key]
            
            if abs(old_value - new_value) > 0.05:  # Significant change
                direction = "increased" if new_value > old_value else "decreased"
                changes.append(f"{key.replace('_', ' ').title()}: {direction} to {new_value:.2f}")
        
        return changes if changes else ["No significant changes made"]


# Convenience functions for common operations

def create_default_preferences() -> Dict[str, Any]:
    """Create default user preferences"""
    return {
        'hard_constraints': {
            'work_start': '09:00',
            'work_end': '17:00',
            'max_meetings_per_day': 6,
            'min_break_duration': 15,
            'blocked_times': []
        },
        'soft_preferences': {
            'focus_blocks': ['09:00-11:00', '14:00-16:00'],
            'preferred_meeting_duration': 30,
            'buffer_between_meetings': 10
        },
        'behavioral_weights': {
            'morning_preference': 0.7,
            'afternoon_preference': 0.5,
            'meeting_clustering': 0.6,
            'focus_time_protection': 0.8,
            'deep_work_protection': 0.9
        }
    }


def create_sample_tasks() -> List[Dict[str, Any]]:
    """Create sample tasks for testing"""
    return [
        {
            'id': 'task_1',
            'title': 'Review quarterly reports',
            'type': 'focus',
            'priority': 'high',
            'estimated_minutes': 90,
            'due_date': '2024-01-20T17:00:00Z'
        },
        {
            'id': 'task_2',
            'title': 'Team standup meeting',
            'type': 'meeting',
            'priority': 'medium',
            'estimated_minutes': 30,
            'due_date': '2024-01-16T10:00:00Z'
        },
        {
            'id': 'task_3',
            'title': 'Code review',
            'type': 'task',
            'priority': 'medium',
            'estimated_minutes': 45,
            'due_date': '2024-01-17T15:00:00Z'
        }
    ]


def create_sample_availability() -> Dict[str, Any]:
    """Create sample availability for testing"""
    return {
        'date_range': {
            'start': '2024-01-15',
            'end': '2024-01-21'
        },
        'free_blocks': [
            {
                'start': '2024-01-15T09:00:00Z',
                'end': '2024-01-15T12:00:00Z',
                'duration': 180
            },
            {
                'start': '2024-01-15T13:00:00Z',
                'end': '2024-01-15T17:00:00Z',
                'duration': 240
            },
            {
                'start': '2024-01-16T09:00:00Z',
                'end': '2024-01-16T11:00:00Z',
                'duration': 120
            },
            {
                'start': '2024-01-16T14:00:00Z',
                'end': '2024-01-16T17:00:00Z',
                'duration': 180
            }
        ],
        'busy_times': [
            {
                'start': '2024-01-15T12:00:00Z',
                'end': '2024-01-15T13:00:00Z',
                'title': 'Lunch'
            }
        ],
        'total_free_minutes': 720
    }