"""
iOS notification tool for PulsePlan agents.
Handles contextual, agent-triggered notifications for conflicts, reschedules, and urgent items.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from ..core.base import BaseTool, ToolResult, ToolError
from app.services.notifications.ios_notification_service import get_ios_notification_service
from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)


class ContextualNotificationType(Enum):
    CONFLICT_DETECTED = "conflict_detected"
    SCHEDULE_CHANGED = "schedule_changed"
    URGENT_DEADLINE = "urgent_deadline"
    TASK_OVERDUE = "task_overdue"
    CALENDAR_SYNC_ISSUE = "calendar_sync_issue"
    SMART_SUGGESTION = "smart_suggestion"
    WORKLOAD_WARNING = "workload_warning"
    FOCUS_TIME_REMINDER = "focus_time_reminder"


class NotificationUrgency(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationManagerTool(BaseTool):
    """
    Contextual notification tool for agent-triggered alerts.
    
    Used by agents to send intelligent, context-aware notifications when they detect:
    - Calendar conflicts that need user attention
    - Automatic reschedules that have occurred
    - Urgent items requiring immediate action
    - Smart suggestions for optimization
    """
    
    def __init__(self):
        super().__init__(
            name="notification_manager",
            description="Send contextual iOS notifications based on agent intelligence and detected conditions"
        )
        
        self.ios_service = get_ios_notification_service()
        self.supabase = get_supabase()
    
    def get_required_tokens(self) -> List[str]:
        """No OAuth tokens required for notifications"""
        return []
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate notification input data"""
        required_fields = ["user_id", "notification_type", "title", "message"]
        
        for field in required_fields:
            if not input_data.get(field):
                return False
        
        # Validate notification type
        notification_type = input_data.get("notification_type")
        if notification_type not in [t.value for t in ContextualNotificationType]:
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute contextual notification sending"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid notification input data", self.name)
            
            user_id = input_data["user_id"]
            notification_type = input_data["notification_type"]
            title = input_data["title"]
            message = input_data["message"]
            urgency = input_data.get("urgency", NotificationUrgency.MEDIUM.value)
            
            # Check if user has notifications enabled for this type
            if not await self._should_send_notification(user_id, notification_type):
                return ToolResult(
                    success=True,
                    data={"status": "skipped", "reason": "user_preferences"},
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            # Route to specific notification handler based on type
            if notification_type == ContextualNotificationType.CONFLICT_DETECTED.value:
                result = await self._send_conflict_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.SCHEDULE_CHANGED.value:
                result = await self._send_schedule_change_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.URGENT_DEADLINE.value:
                result = await self._send_urgent_deadline_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.TASK_OVERDUE.value:
                result = await self._send_overdue_task_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.CALENDAR_SYNC_ISSUE.value:
                result = await self._send_sync_issue_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.SMART_SUGGESTION.value:
                result = await self._send_smart_suggestion_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.WORKLOAD_WARNING.value:
                result = await self._send_workload_warning_notification(user_id, input_data, context)
            elif notification_type == ContextualNotificationType.FOCUS_TIME_REMINDER.value:
                result = await self._send_focus_time_notification(user_id, input_data, context)
            else:
                result = await self._send_generic_notification(user_id, input_data, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            tool_result = ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "notification_type": notification_type,
                    "user_id": user_id,
                    "urgency": urgency
                }
            )
            
            self.log_execution(input_data, tool_result, context)
            return tool_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Notification tool execution failed: {e}")
            
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "notification_type": input_data.get("notification_type"),
                    "user_id": input_data.get("user_id")
                }
            )
    
    async def _send_conflict_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about detected calendar conflicts"""
        conflict_data = input_data.get("conflict_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "conflict",
            "priority": "high",
            "data": {
                "type": "conflict_detected",
                "user_id": user_id,
                "conflict_type": conflict_data.get("conflict_type", "calendar_overlap"),
                "affected_tasks": conflict_data.get("affected_tasks", []),
                "suggested_action": conflict_data.get("suggested_action"),
                "deep_link": "pulseplan://schedule/conflicts",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        
        # Log the conflict notification
        await self._log_notification(user_id, "conflict_detected", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "conflict_detected",
            "user_id": user_id,
            "conflict_data": conflict_data
        }
    
    async def _send_schedule_change_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about automatic schedule changes"""
        change_data = input_data.get("change_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "schedule_update",
            "priority": "normal",
            "data": {
                "type": "schedule_changed",
                "user_id": user_id,
                "change_type": change_data.get("change_type", "reschedule"),
                "affected_items": change_data.get("affected_items", []),
                "reason": change_data.get("reason"),
                "deep_link": "pulseplan://schedule/recent-changes",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "schedule_changed", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "schedule_changed",
            "user_id": user_id,
            "change_data": change_data
        }
    
    async def _send_urgent_deadline_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about urgent deadlines requiring immediate attention"""
        deadline_data = input_data.get("deadline_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "urgent_deadline",
            "priority": "critical",
            "data": {
                "type": "urgent_deadline",
                "user_id": user_id,
                "assignment_id": deadline_data.get("assignment_id"),
                "assignment_name": deadline_data.get("assignment_name"),
                "due_at": deadline_data.get("due_at"),
                "hours_remaining": deadline_data.get("hours_remaining"),
                "completion_status": deadline_data.get("completion_status", "not_started"),
                "deep_link": f"pulseplan://assignment/{deadline_data.get('assignment_id')}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "urgent_deadline", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "urgent_deadline",
            "user_id": user_id,
            "deadline_data": deadline_data
        }
    
    async def _send_overdue_task_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about overdue tasks"""
        task_data = input_data.get("task_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "overdue",
            "priority": "high",
            "data": {
                "type": "task_overdue",
                "user_id": user_id,
                "task_id": task_data.get("task_id"),
                "task_name": task_data.get("task_name"),
                "overdue_by_hours": task_data.get("overdue_by_hours"),
                "suggested_reschedule": task_data.get("suggested_reschedule"),
                "deep_link": f"pulseplan://task/{task_data.get('task_id')}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "task_overdue", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "task_overdue",
            "user_id": user_id,
            "task_data": task_data
        }
    
    async def _send_sync_issue_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about calendar sync issues"""
        sync_data = input_data.get("sync_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "sync_issue",
            "priority": "normal",
            "data": {
                "type": "calendar_sync_issue",
                "user_id": user_id,
                "provider": sync_data.get("provider", "unknown"),
                "issue_type": sync_data.get("issue_type", "authentication"),
                "last_successful_sync": sync_data.get("last_successful_sync"),
                "deep_link": "pulseplan://settings/integrations",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "calendar_sync_issue", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "calendar_sync_issue",
            "user_id": user_id,
            "sync_data": sync_data
        }
    
    async def _send_smart_suggestion_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification with smart AI suggestions"""
        suggestion_data = input_data.get("suggestion_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "suggestion",
            "priority": "low",
            "data": {
                "type": "smart_suggestion",
                "user_id": user_id,
                "suggestion_type": suggestion_data.get("suggestion_type", "optimization"),
                "suggestion_content": suggestion_data.get("suggestion_content"),
                "potential_benefit": suggestion_data.get("potential_benefit"),
                "action_required": suggestion_data.get("action_required", False),
                "deep_link": "pulseplan://suggestions",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "smart_suggestion", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "smart_suggestion",
            "user_id": user_id,
            "suggestion_data": suggestion_data
        }
    
    async def _send_workload_warning_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about workload concerns"""
        workload_data = input_data.get("workload_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "workload_warning",
            "priority": "normal",
            "data": {
                "type": "workload_warning",
                "user_id": user_id,
                "warning_type": workload_data.get("warning_type", "overloaded"),
                "period": workload_data.get("period", "this_week"),
                "current_load": workload_data.get("current_load"),
                "recommended_load": workload_data.get("recommended_load"),
                "suggested_adjustments": workload_data.get("suggested_adjustments", []),
                "deep_link": "pulseplan://analytics/workload",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "workload_warning", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "workload_warning",
            "user_id": user_id,
            "workload_data": workload_data
        }
    
    async def _send_focus_time_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about upcoming focus time"""
        focus_data = input_data.get("focus_data", {})
        
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "focus_time",
            "priority": "normal",
            "data": {
                "type": "focus_time_reminder",
                "user_id": user_id,
                "task_name": focus_data.get("task_name"),
                "start_time": focus_data.get("start_time"),
                "duration_minutes": focus_data.get("duration_minutes"),
                "focus_type": focus_data.get("focus_type", "deep_work"),
                "preparation_tips": focus_data.get("preparation_tips", []),
                "deep_link": f"pulseplan://focus/{focus_data.get('task_id')}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, "focus_time_reminder", notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": "focus_time_reminder",
            "user_id": user_id,
            "focus_data": focus_data
        }
    
    async def _send_generic_notification(self, user_id: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send a generic contextual notification"""
        notification = {
            "title": input_data["title"],
            "body": input_data["message"],
            "category": "general",
            "priority": input_data.get("urgency", "normal"),
            "data": {
                "type": input_data["notification_type"],
                "user_id": user_id,
                "context_data": input_data.get("context_data", {}),
                "deep_link": input_data.get("deep_link", "pulseplan://"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        success = await self.ios_service.send_notification(user_id, notification)
        await self._log_notification(user_id, input_data["notification_type"], notification, success)
        
        return {
            "notification_sent": success,
            "notification_type": input_data["notification_type"],
            "user_id": user_id
        }
    
    async def _should_send_notification(self, user_id: str, notification_type: str) -> bool:
        """Check if user has notifications enabled for this type"""
        try:
            # Get user notification preferences
            response = await self.supabase.table("user_preferences").select(
                "contextual_notifications_enabled, notification_types_enabled"
            ).eq("user_id", user_id).single().execute()
            
            if not response.data:
                return True  # Default to enabled if no preferences found
            
            preferences = response.data
            
            # Check if contextual notifications are enabled
            if not preferences.get("contextual_notifications_enabled", True):
                return False
            
            # Check if this specific notification type is enabled
            enabled_types = preferences.get("notification_types_enabled", [])
            if enabled_types and notification_type not in enabled_types:
                return False
            
            # Check rate limiting - don't spam users
            from app.services.cache_service import get_cache_service
            cache_service = get_cache_service()
            cache_key = f"notification_rate_limit:{user_id}:{notification_type}"
            recent_count = await cache_service.get(cache_key) or 0
            
            # Limit to 3 notifications of the same type per hour
            if recent_count >= 3:
                return False
            
            # Increment rate limit counter
            await cache_service.set(cache_key, recent_count + 1, 3600)  # 1 hour TTL
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking notification preferences for user {user_id}: {e}")
            return True  # Default to enabled on error
    
    async def _log_notification(self, user_id: str, notification_type: str, notification: Dict[str, Any], success: bool):
        """Log notification sending for analytics and debugging"""
        try:
            log_entry = {
                "user_id": user_id,
                "notification_type": notification_type,
                "title": notification["title"],
                "success": success,
                "sent_at": datetime.utcnow().isoformat(),
                "priority": notification.get("priority", "normal"),
                "category": notification.get("category", "general")
            }
            
            await self.supabase.table("notification_logs").insert(log_entry).execute()
            
        except Exception as e:
            logger.warning(f"Failed to log notification: {e}")


# Create global instance
notification_manager_tool = NotificationManagerTool()
