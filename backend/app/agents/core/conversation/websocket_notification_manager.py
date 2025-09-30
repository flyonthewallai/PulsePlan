"""
WebSocket Notification Manager
Handles real-time notifications for task completion and conversation updates
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImmediateResponse(BaseModel):
    """Immediate response sent via WebSocket"""
    type: str = "immediate_response"
    message: str
    action: str
    status: str = "processing"
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    can_switch: bool = False
    suggested_workflows: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskCompletionResponse(BaseModel):
    """Task completion notification sent via WebSocket"""
    type: str = "task_completed"
    task_id: str
    task_title: str
    status: str  # "success", "failed", "partial"
    message: str
    follow_up_question: Optional[str] = None
    workflow_type: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ClarificationResponse(BaseModel):
    """Clarification request sent via WebSocket"""
    type: str = "clarification_request"
    clarification_id: str
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = 300  # 5 minutes in seconds
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WorkflowSwitchResponse(BaseModel):
    """Workflow switch notification sent via WebSocket"""
    type: str = "workflow_switch"
    from_workflow: Optional[str] = None
    to_workflow: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WebSocketNotificationManager:
    """Manages WebSocket notifications for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}  # user_id -> socket connection
    
    def register_connection(self, user_id: str, socket_connection: Any) -> None:
        """Register a WebSocket connection for a user"""
        self.active_connections[user_id] = socket_connection
        logger.info(f"Registered WebSocket connection for user {user_id}")
    
    def unregister_connection(self, user_id: str) -> None:
        """Unregister a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"Unregistered WebSocket connection for user {user_id}")
    
    async def send_immediate_response(
        self,
        user_id: str,
        message: str,
        action: str,
        requires_clarification: bool = False,
        clarification_question: Optional[str] = None,
        can_switch: bool = False,
        suggested_workflows: Optional[List[str]] = None
    ) -> bool:
        """Send immediate response to user"""
        try:
            response = ImmediateResponse(
                message=message,
                action=action,
                requires_clarification=requires_clarification,
                clarification_question=clarification_question,
                can_switch=can_switch,
                suggested_workflows=suggested_workflows or []
            )
            
            return await self._send_to_user(user_id, response.dict())
            
        except Exception as e:
            logger.error(f"Failed to send immediate response: {e}")
            return False
    
    async def send_task_completion(
        self,
        user_id: str,
        task_id: str,
        task_title: str,
        status: str,
        message: str,
        follow_up_question: Optional[str] = None,
        workflow_type: Optional[str] = None
    ) -> bool:
        """Send task completion notification"""
        try:
            response = TaskCompletionResponse(
                task_id=task_id,
                task_title=task_title,
                status=status,
                message=message,
                follow_up_question=follow_up_question,
                workflow_type=workflow_type
            )
            
            return await self._send_to_user(user_id, response.dict())
            
        except Exception as e:
            logger.error(f"Failed to send task completion: {e}")
            return False
    
    async def send_clarification_request(
        self,
        user_id: str,
        clarification_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> bool:
        """Send clarification request to user"""
        try:
            response = ClarificationResponse(
                clarification_id=clarification_id,
                question=question,
                context=context or {},
                timeout=timeout
            )
            
            return await self._send_to_user(user_id, response.dict())
            
        except Exception as e:
            logger.error(f"Failed to send clarification request: {e}")
            return False
    
    async def send_workflow_switch(
        self,
        user_id: str,
        to_workflow: str,
        message: str,
        from_workflow: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send workflow switch notification"""
        try:
            response = WorkflowSwitchResponse(
                from_workflow=from_workflow,
                to_workflow=to_workflow,
                message=message,
                context=context or {}
            )
            
            return await self._send_to_user(user_id, response.dict())
            
        except Exception as e:
            logger.error(f"Failed to send workflow switch: {e}")
            return False
    
    async def _send_to_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Send data to user via WebSocket"""
        try:
            if user_id not in self.active_connections:
                logger.warning(f"No active WebSocket connection for user {user_id}")
                return False
            
            socket_connection = self.active_connections[user_id]
            
            # Send the data (implementation depends on your WebSocket library)
            # This is a placeholder - you'll need to implement based on your WebSocket setup
            await socket_connection.send(json.dumps(data))
            
            logger.debug(f"Sent WebSocket message to user {user_id}: {data['type']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket message to user {user_id}: {e}")
            return False
    
    def get_active_users(self) -> List[str]:
        """Get list of users with active WebSocket connections"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has an active WebSocket connection"""
        return user_id in self.active_connections


# Global instance
_websocket_manager = None


def get_websocket_manager() -> WebSocketNotificationManager:
    """Get the global WebSocket notification manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketNotificationManager()
    return _websocket_manager

