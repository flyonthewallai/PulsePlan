"""
Conversation State Manager
Manages persistent conversation state, clarifications, and workflow switching
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.config.cache.redis_client import get_redis_client
from app.agents.core.orchestration.agent_task_manager import AgentTaskCard

logger = logging.getLogger(__name__)


class ClarificationRequest(BaseModel):
    """Request for user clarification"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)
    expected_response_type: str
    timeout: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """Persistent conversation state"""
    conversation_id: str
    user_id: str
    
    # Active workflow context
    active_workflow: Optional[str] = None
    workflow_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Pending clarifications
    pending_clarifications: List[ClarificationRequest] = Field(default_factory=list)
    
    # Task queue for long-running workflows
    task_queue: List[AgentTaskCard] = Field(default_factory=list)
    
    # Context switching
    can_switch: bool = True
    switch_context: Optional[Dict[str, Any]] = None
    
    # Conversation metadata
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationStateManager:
    """Manages persistent conversation state across sessions"""
    
    def __init__(self):
        self.redis_client = None
        self.state_ttl = 3600  # 1 hour
    
    async def _get_redis(self):
        """Get Redis client, initializing if needed"""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def get_conversation_state(
        self, 
        conversation_id: str, 
        user_id: str
    ) -> ConversationState:
        """Get or create conversation state"""
        try:
            # Try to get existing state from Redis
            redis = await self._get_redis()
            state_key = f"conversation_state:{conversation_id}"
            state_data = await redis.get(state_key)
            
            if state_data:
                import json
                try:
                    state_dict = json.loads(state_data)
                    return ConversationState(**state_dict)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse conversation state JSON: {e}, data: {state_data[:100]}...")
                    # Create new state if parsing fails
                    pass
            
            # Create new state
            state = ConversationState(
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            await self._save_state(state)
            return state
            
        except Exception as e:
            logger.error(f"Failed to get conversation state: {e}")
            return ConversationState(conversation_id=conversation_id, user_id=user_id)
    
    async def update_conversation_state(
        self, 
        state: ConversationState
    ) -> None:
        """Update conversation state"""
        try:
            state.last_activity = datetime.utcnow()
            await self._save_state(state)
        except Exception as e:
            logger.error(f"Failed to update conversation state: {e}")
    
    async def add_clarification_request(
        self,
        conversation_id: str,
        user_id: str,
        question: str,
        context: Dict[str, Any],
        expected_response_type: str = "text"
    ) -> ClarificationRequest:
        """Add a clarification request to the conversation state"""
        try:
            state = await self.get_conversation_state(conversation_id, user_id)
            
            clarification = ClarificationRequest(
                question=question,
                context=context,
                expected_response_type=expected_response_type,
                timeout=datetime.utcnow() + timedelta(minutes=5)
            )
            
            state.pending_clarifications.append(clarification)
            await self.update_conversation_state(state)
            
            logger.info(f"Added clarification request: {question}")
            return clarification
            
        except Exception as e:
            logger.error(f"Failed to add clarification request: {e}")
            return ClarificationRequest(question=question, context=context)
    
    async def resolve_clarification(
        self,
        conversation_id: str,
        user_id: str,
        clarification_id: str,
        user_response: str
    ) -> Optional[ClarificationRequest]:
        """Resolve a clarification request with user response"""
        try:
            state = await self.get_conversation_state(conversation_id, user_id)
            
            # Find and remove the clarification
            for i, clarification in enumerate(state.pending_clarifications):
                if clarification.id == clarification_id:
                    resolved_clarification = state.pending_clarifications.pop(i)
                    await self.update_conversation_state(state)
                    
                    logger.info(f"Resolved clarification: {resolved_clarification.question}")
                    return resolved_clarification
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to resolve clarification: {e}")
            return None
    
    async def add_task_to_queue(
        self,
        conversation_id: str,
        user_id: str,
        task_card: AgentTaskCard
    ) -> None:
        """Add a task to the conversation's task queue"""
        try:
            state = await self.get_conversation_state(conversation_id, user_id)
            state.task_queue.append(task_card)
            await self.update_conversation_state(state)
            
            logger.info(f"Added task to queue: {task_card.title}")
            
        except Exception as e:
            logger.error(f"Failed to add task to queue: {e}")
    
    async def update_task_status(
        self,
        conversation_id: str,
        user_id: str,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update task status in the conversation state"""
        try:
            from app.agents.core.agent_task_manager import TaskStatus
            
            state = await self.get_conversation_state(conversation_id, user_id)
            
            # Convert string status to TaskStatus enum
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                logger.warning(f"Invalid status '{status}', using PENDING")
                status_enum = TaskStatus.PENDING
            
            for task in state.task_queue:
                if task.id == task_id:
                    task.status = status_enum
                    if result:
                        task.result = result
                    break
            
            await self.update_conversation_state(state)
            logger.info(f"Updated task status: {task_id} -> {status_enum.value}")
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    async def switch_workflow(
        self,
        conversation_id: str,
        user_id: str,
        new_workflow: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Switch to a different workflow"""
        try:
            state = await self.get_conversation_state(conversation_id, user_id)
            
            # Clear pending clarifications when switching
            state.pending_clarifications.clear()
            
            # Update workflow context
            state.active_workflow = new_workflow
            if context:
                state.workflow_context.update(context)
            
            await self.update_conversation_state(state)
            logger.info(f"Switched workflow to: {new_workflow}")
            
        except Exception as e:
            logger.error(f"Failed to switch workflow: {e}")
    
    async def get_pending_clarifications(
        self,
        conversation_id: str,
        user_id: str
    ) -> List[ClarificationRequest]:
        """Get pending clarifications for the conversation"""
        try:
            state = await self.get_conversation_state(conversation_id, user_id)
            
            # Filter out expired clarifications
            now = datetime.utcnow()
            active_clarifications = [
                c for c in state.pending_clarifications 
                if not c.timeout or c.timeout > now
            ]
            
            # Update state if clarifications were filtered
            if len(active_clarifications) != len(state.pending_clarifications):
                state.pending_clarifications = active_clarifications
                await self.update_conversation_state(state)
            
            return active_clarifications
            
        except Exception as e:
            logger.error(f"Failed to get pending clarifications: {e}")
            return []
    
    async def _save_state(self, state: ConversationState) -> None:
        """Save state to Redis"""
        try:
            import json
            redis = await self._get_redis()
            state_key = f"conversation_state:{state.conversation_id}"
            state_dict = state.dict()
            
            # Convert datetime objects to strings for serialization
            for key, value in state_dict.items():
                if isinstance(value, datetime):
                    state_dict[key] = value.isoformat()
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            for sub_key, sub_value in item.items():
                                if isinstance(sub_value, datetime):
                                    state_dict[key][i][sub_key] = sub_value.isoformat()
            
            await redis.setex(
                state_key, 
                self.state_ttl, 
                json.dumps(state_dict, default=str)
            )
            
        except Exception as e:
            logger.error(f"Failed to save conversation state: {e}")


# Global instance
_conversation_state_manager = None


def get_conversation_state_manager() -> ConversationStateManager:
    """Get the global conversation state manager instance"""
    global _conversation_state_manager
    if _conversation_state_manager is None:
        _conversation_state_manager = ConversationStateManager()
    return _conversation_state_manager

