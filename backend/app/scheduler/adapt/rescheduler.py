"""
Rescheduling logic for missed tasks and schedule adjustments.

Handles adaptive rescheduling when tasks are missed, user preferences change,
or calendar conflicts arise.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta

from ..core.domain import Task, BusyEvent, Preferences, ScheduleBlock
from ..io.dto import ScheduleRequest, ScheduleResponse
from ..io.repository import Repository
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class ReschedulingStrategy:
    """
    Base class for rescheduling strategies.
    
    Different strategies handle various rescheduling scenarios
    (missed tasks, conflicts, preference changes, etc.).
    """
    
    def __init__(self, name: str):
        """Initialize strategy with name."""
        self.name = name
        self.timezone_manager = get_timezone_manager()
    
    async def should_reschedule(
        self, 
        tasks: List[Task], 
        current_schedule: List[ScheduleBlock],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Determine if rescheduling is needed.
        
        Args:
            tasks: Current tasks
            current_schedule: Existing schedule
            context: Contextual information
            
        Returns:
            (should_reschedule, reason) tuple
        """
        raise NotImplementedError
    
    async def adjust_tasks(
        self, 
        tasks: List[Task], 
        context: Dict[str, Any]
    ) -> List[Task]:
        """
        Adjust task parameters for rescheduling.
        
        Args:
            tasks: Original tasks
            context: Contextual information
            
        Returns:
            Adjusted tasks
        """
        return tasks  # Default: no adjustment


class MissedTaskStrategy(ReschedulingStrategy):
    """Strategy for rescheduling missed tasks."""
    
    def __init__(self):
        super().__init__("missed_tasks")
    
    async def should_reschedule(
        self, 
        tasks: List[Task], 
        current_schedule: List[ScheduleBlock],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check for missed tasks that need rescheduling."""
        missed_tasks = context.get('missed_tasks', [])
        
        if missed_tasks:
            return True, f"Found {len(missed_tasks)} missed tasks requiring rescheduling"
        
        # Check for overdue scheduled blocks
        now = datetime.now()
        overdue_blocks = [
            block for block in current_schedule
            if block.end < now and not self._is_completed(block, context)
        ]
        
        if overdue_blocks:
            return True, f"Found {len(overdue_blocks)} overdue blocks"
        
        return False, "No missed tasks detected"
    
    async def adjust_tasks(
        self, 
        tasks: List[Task], 
        context: Dict[str, Any]
    ) -> List[Task]:
        """Adjust missed tasks with higher urgency."""
        missed_task_ids = set(context.get('missed_tasks', []))
        adjusted_tasks = []
        
        for task in tasks:
            if task.id in missed_task_ids:
                # Increase weight for missed tasks
                adjusted_task = task.__class__(
                    **{**task.__dict__, 
                       'weight': task.weight * 1.5,
                       'updated_at': datetime.now()}
                )
                adjusted_tasks.append(adjusted_task)
                logger.debug(f"Increased weight for missed task {task.title}")
            else:
                adjusted_tasks.append(task)
        
        return adjusted_tasks
    
    def _is_completed(self, block: ScheduleBlock, context: Dict[str, Any]) -> bool:
        """Check if a scheduled block was completed."""
        completed_tasks = context.get('completed_tasks', [])
        return block.task_id in completed_tasks


class ConflictResolutionStrategy(ReschedulingStrategy):
    """Strategy for resolving calendar conflicts."""
    
    def __init__(self):
        super().__init__("conflict_resolution")
    
    async def should_reschedule(
        self, 
        tasks: List[Task], 
        current_schedule: List[ScheduleBlock],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check for calendar conflicts."""
        new_events = context.get('new_calendar_events', [])
        
        if not new_events:
            return False, "No new calendar events"
        
        # Check for conflicts with existing schedule
        conflicts = []
        for block in current_schedule:
            for event in new_events:
                if self._blocks_overlap(block, event):
                    conflicts.append((block, event))
        
        if conflicts:
            return True, f"Found {len(conflicts)} calendar conflicts"
        
        return False, "No calendar conflicts detected"
    
    def _blocks_overlap(self, block: ScheduleBlock, event: BusyEvent) -> bool:
        """Check if a schedule block overlaps with a calendar event."""
        return (
            block.start < event.end and 
            block.end > event.start
        )


class DeadlineUrgencyStrategy(ReschedulingStrategy):
    """Strategy for handling approaching deadlines."""
    
    def __init__(self, urgency_threshold_hours: int = 48):
        super().__init__("deadline_urgency")
        self.urgency_threshold_hours = urgency_threshold_hours
    
    async def should_reschedule(
        self, 
        tasks: List[Task], 
        current_schedule: List[ScheduleBlock],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check for approaching deadlines."""
        now = datetime.now()
        threshold = now + timedelta(hours=self.urgency_threshold_hours)
        
        urgent_tasks = [
            task for task in tasks
            if task.deadline and task.deadline <= threshold
        ]
        
        if urgent_tasks:
            return True, f"Found {len(urgent_tasks)} tasks with approaching deadlines"
        
        return False, "No urgent deadlines detected"
    
    async def adjust_tasks(
        self, 
        tasks: List[Task], 
        context: Dict[str, Any]
    ) -> List[Task]:
        """Increase urgency for tasks with approaching deadlines."""
        now = datetime.now()
        threshold = now + timedelta(hours=self.urgency_threshold_hours)
        adjusted_tasks = []
        
        for task in tasks:
            if task.deadline and task.deadline <= threshold:
                # Calculate urgency multiplier based on time remaining
                time_remaining = (task.deadline - now).total_seconds() / 3600  # hours
                urgency_multiplier = max(1.5, 3.0 - (time_remaining / 24))  # 1.5x to 3x
                
                adjusted_task = task.__class__(
                    **{**task.__dict__, 
                       'weight': task.weight * urgency_multiplier,
                       'updated_at': datetime.now()}
                )
                adjusted_tasks.append(adjusted_task)
                logger.debug(f"Applied {urgency_multiplier:.1f}x urgency to {task.title}")
            else:
                adjusted_tasks.append(task)
        
        return adjusted_tasks


class AdaptiveRescheduler:
    """
    Main rescheduling coordinator.
    
    Uses multiple strategies to detect rescheduling needs and
    coordinate with the main scheduler service.
    """
    
    def __init__(self, repo: Optional[Repository] = None):
        """
        Initialize adaptive rescheduler.
        
        Args:
            repo: Data repository
        """
        from ..io.repository import get_repository
        self.repo = repo or get_repository()
        
        # Initialize rescheduling strategies
        self.strategies = [
            MissedTaskStrategy(),
            ConflictResolutionStrategy(),
            DeadlineUrgencyStrategy()
        ]
    
    async def analyze_reschedule_need(
        self, 
        user_id: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Analyze if rescheduling is needed for a user.
        
        Args:
            user_id: User identifier
            context: Optional context information
            
        Returns:
            (needs_reschedule, reasons, analysis_context) tuple
        """
        if context is None:
            context = await self._build_analysis_context(user_id)
        
        # Load current state
        tasks = await self.repo.load_tasks(user_id, horizon_days=7)
        current_schedule = await self.repo.get_recent_schedules(user_id, days_back=1)
        
        needs_reschedule = False
        reasons = []
        
        # Apply all strategies
        for strategy in self.strategies:
            should_reschedule, reason = await strategy.should_reschedule(
                tasks, current_schedule, context
            )
            
            if should_reschedule:
                needs_reschedule = True
                reasons.append(f"{strategy.name}: {reason}")
        
        logger.debug(
            f"Reschedule analysis for {user_id}: "
            f"needed={needs_reschedule}, reasons={len(reasons)}"
        )
        
        return needs_reschedule, reasons, context
    
    async def _build_analysis_context(self, user_id: str) -> Dict[str, Any]:
        """Build context for rescheduling analysis."""
        # In a real implementation, this would gather:
        # - Recently missed tasks
        # - New calendar events
        # - Completed tasks
        # - User feedback
        
        return {
            'user_id': user_id,
            'analysis_time': datetime.now(),
            'missed_tasks': [],  # Would be populated from actual data
            'completed_tasks': [],
            'new_calendar_events': [],
            'user_feedback': {}
        }
    
    async def prepare_reschedule_request(
        self, 
        user_id: str, 
        horizon_days: int,
        context: Dict[str, Any]
    ) -> ScheduleRequest:
        """
        Prepare a rescheduling request with adjusted parameters.
        
        Args:
            user_id: User identifier
            horizon_days: Rescheduling horizon
            context: Analysis context
            
        Returns:
            Schedule request for rescheduling
        """
        # Load and adjust tasks using applicable strategies
        tasks = await self.repo.load_tasks(user_id, horizon_days)
        current_schedule = await self.repo.get_recent_schedules(user_id, days_back=1)
        
        # Apply task adjustments from strategies
        for strategy in self.strategies:
            should_reschedule, _ = await strategy.should_reschedule(
                tasks, current_schedule, context
            )
            
            if should_reschedule:
                tasks = await strategy.adjust_tasks(tasks, context)
        
        # Update tasks in repository with adjustments
        for task in tasks:
            if task.updated_at and task.updated_at > datetime.now() - timedelta(minutes=5):
                # Task was recently adjusted, update in storage
                await self.repo.update_task(
                    user_id, task.id, {'weight': task.weight, 'updated_at': task.updated_at}
                )
        
        # Create reschedule request
        request = ScheduleRequest(
            user_id=user_id,
            horizon_days=horizon_days,
            dry_run=False,
            lock_existing=False,  # Allow rescheduling of existing blocks
            options={
                'reschedule': True,
                'context': context,
                'strategies_applied': [s.name for s in self.strategies]
            }
        )
        
        return request


async def reschedule_backlog(
    user_id: str, 
    horizon_days: int,
    scheduler_service
) -> ScheduleResponse:
    """
    Main entry point for rescheduling missed/problematic tasks.
    
    Args:
        user_id: User identifier
        horizon_days: Days ahead to reschedule
        scheduler_service: Main scheduler service instance
        
    Returns:
        New schedule response
    """
    try:
        rescheduler = AdaptiveRescheduler()
        
        # Analyze reschedule need
        needs_reschedule, reasons, context = await rescheduler.analyze_reschedule_need(user_id)
        
        if not needs_reschedule:
            logger.info(f"No rescheduling needed for user {user_id}")
            return ScheduleResponse(
                job_id=None,
                feasible=True,
                blocks=[],
                metrics={'message': 'No rescheduling needed'},
                explanations={'summary': 'Current schedule is optimal'}
            )
        
        logger.info(f"Rescheduling needed for user {user_id}: {', '.join(reasons)}")
        
        # Prepare reschedule request
        request = await rescheduler.prepare_reschedule_request(
            user_id, horizon_days, context
        )
        
        # Execute rescheduling
        response = await scheduler_service.schedule(request)
        
        # Update response to indicate this was a reschedule
        if hasattr(response, 'explanations'):
            response.explanations['reschedule_reasons'] = '; '.join(reasons)
            response.explanations['reschedule_type'] = 'adaptive_backlog'
        
        return response
        
    except Exception as e:
        logger.error(f"Reschedule backlog failed for user {user_id}: {e}", exc_info=True)
        
        return ScheduleResponse(
            job_id=None,
            feasible=False,
            blocks=[],
            metrics={'error': str(e)},
            explanations={'error': f"Rescheduling failed: {str(e)}"}
        )


async def handle_calendar_change(
    user_id: str,
    new_events: List[BusyEvent],
    scheduler_service
) -> Optional[ScheduleResponse]:
    """
    Handle calendar changes that may require rescheduling.
    
    Args:
        user_id: User identifier
        new_events: New calendar events that may conflict
        scheduler_service: Main scheduler service
        
    Returns:
        New schedule if rescheduling was needed, None otherwise
    """
    try:
        rescheduler = AdaptiveRescheduler()
        
        # Build context with new events
        context = {
            'user_id': user_id,
            'analysis_time': datetime.now(),
            'new_calendar_events': new_events,
            'missed_tasks': [],
            'completed_tasks': [],
            'user_feedback': {}
        }
        
        # Check if rescheduling is needed
        needs_reschedule, reasons, _ = await rescheduler.analyze_reschedule_need(
            user_id, context
        )
        
        if not needs_reschedule:
            return None
        
        logger.info(f"Calendar change requires rescheduling for user {user_id}")
        
        # Prepare and execute reschedule
        request = await rescheduler.prepare_reschedule_request(user_id, 3, context)
        response = await scheduler_service.schedule(request)
        
        if hasattr(response, 'explanations'):
            response.explanations['reschedule_trigger'] = 'calendar_change'
            response.explanations['affected_events'] = len(new_events)
        
        return response
        
    except Exception as e:
        logger.error(f"Calendar change handling failed for user {user_id}: {e}")
        return None


async def handle_user_feedback(
    user_id: str,
    feedback: Dict[str, Any],
    scheduler_service
) -> Optional[ScheduleResponse]:
    """
    Handle user feedback that may trigger rescheduling.
    
    Args:
        user_id: User identifier
        feedback: User feedback data
        scheduler_service: Main scheduler service
        
    Returns:
        New schedule if rescheduling was needed, None otherwise
    """
    try:
        # Extract feedback information
        missed_tasks = feedback.get('missed_tasks', [])
        satisfaction_score = feedback.get('satisfaction_score', 0)
        rescheduled_tasks = feedback.get('rescheduled_tasks', [])
        
        # Determine if rescheduling is warranted
        should_reschedule = (
            len(missed_tasks) > 0 or  # User missed tasks
            satisfaction_score < -0.3 or  # Low satisfaction
            len(rescheduled_tasks) > 2  # User made many manual changes
        )
        
        if not should_reschedule:
            return None
        
        logger.info(f"User feedback triggers rescheduling for user {user_id}")
        
        # Build context
        context = {
            'user_id': user_id,
            'analysis_time': datetime.now(),
            'missed_tasks': missed_tasks,
            'completed_tasks': feedback.get('completed_tasks', []),
            'user_feedback': feedback,
            'new_calendar_events': []
        }
        
        rescheduler = AdaptiveRescheduler()
        request = await rescheduler.prepare_reschedule_request(user_id, 5, context)
        response = await scheduler_service.schedule(request)
        
        if hasattr(response, 'explanations'):
            response.explanations['reschedule_trigger'] = 'user_feedback'
            response.explanations['satisfaction_score'] = satisfaction_score
            response.explanations['missed_count'] = len(missed_tasks)
        
        return response
        
    except Exception as e:
        logger.error(f"User feedback handling failed for user {user_id}: {e}")
        return None


class ReschedulingMetrics:
    """Track rescheduling metrics for analysis."""
    
    def __init__(self):
        """Initialize metrics tracking."""
        self.reschedule_events = []
    
    def record_reschedule(
        self,
        user_id: str,
        trigger: str,
        reason: str,
        success: bool,
        blocks_changed: int = 0
    ):
        """Record a rescheduling event."""
        event = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'trigger': trigger,
            'reason': reason,
            'success': success,
            'blocks_changed': blocks_changed
        }
        
        self.reschedule_events.append(event)
        
        # Keep only recent events
        cutoff = datetime.now() - timedelta(days=30)
        self.reschedule_events = [
            e for e in self.reschedule_events
            if e['timestamp'] >= cutoff
        ]
    
    def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get rescheduling statistics."""
        events = self.reschedule_events
        if user_id:
            events = [e for e in events if e['user_id'] == user_id]
        
        if not events:
            return {'total_reschedules': 0}
        
        total = len(events)
        successful = sum(1 for e in events if e['success'])
        
        # Group by trigger
        by_trigger = {}
        for event in events:
            trigger = event['trigger']
            by_trigger.setdefault(trigger, 0)
            by_trigger[trigger] += 1
        
        return {
            'total_reschedules': total,
            'successful_reschedules': successful,
            'success_rate': successful / total if total > 0 else 0,
            'by_trigger': by_trigger,
            'recent_events': events[-10:]  # Last 10 events
        }


# Global metrics instance
_reschedule_metrics = ReschedulingMetrics()

def get_reschedule_metrics() -> ReschedulingMetrics:
    """Get global rescheduling metrics instance."""
    return _reschedule_metrics


