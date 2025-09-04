"""
Workflow Supervisor Service
Maintains workflow execution context and handles follow-up operations
"""
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta

from ..models.workflow_output import (
    SupervisionContext, WorkflowOutput, ConversationResponse,
    WorkflowStatus, create_workflow_output
)
from .conversation_layer import get_conversation_layer
from ...core.cache import get_redis_client


class WorkflowSupervisor:
    """
    Manages workflow supervision, context persistence, and follow-up operations
    """
    
    def __init__(self):
        self.conversation_layer = get_conversation_layer()
        self.redis_client = None
        self._context_cache: Dict[str, SupervisionContext] = {}
    
    async def initialize(self):
        """Initialize supervisor with Redis connection"""
        try:
            self.redis_client = await get_redis_client()
        except Exception:
            # Fallback to in-memory storage if Redis unavailable
            self.redis_client = None
    
    async def supervise_workflow_execution(
        self,
        user_query: str,
        workflow_output: WorkflowOutput,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationResponse:
        """
        Supervise workflow execution by wrapping output in conversation layer
        and maintaining context for follow-ups
        """
        
        # Wrap workflow output in natural language
        conversation_response = await self.conversation_layer.wrap_workflow_output(
            user_query=user_query,
            workflow_output=workflow_output,
            user_context=user_context,
            conversation_history=conversation_history
        )
        
        # Persist supervision context
        if conversation_response.supervision_context:
            await self._persist_supervision_context(conversation_response.supervision_context)
        
        return conversation_response
    
    async def handle_follow_up_message(
        self,
        user_message: str,
        trace_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationResponse]:
        """
        Handle follow-up messages that reference previous workflow executions
        """
        
        # Load supervision context
        supervision_context = await self._load_supervision_context(trace_id)
        if not supervision_context:
            return None
        
        # Check if context has expired
        if datetime.utcnow() > supervision_context.expires_at:
            await self._cleanup_supervision_context(trace_id)
            return None
        
        # Analyze follow-up message
        routing_info = await self.conversation_layer.handle_follow_up(
            user_message=user_message,
            trace_id=trace_id,
            user_context=user_context
        )
        
        if not routing_info or not routing_info.get("actionable"):
            # Not actionable, just return conversational response
            return await self._generate_conversational_follow_up(
                user_message, supervision_context, user_context
            )
        
        # Execute new workflow based on routing
        new_workflow_output = await self._execute_follow_up_workflow(
            routing_info=routing_info,
            supervision_context=supervision_context,
            user_message=user_message,
            user_context=user_context
        )
        
        if new_workflow_output:
            # Update conversation history
            updated_history = supervision_context.conversation_history + [
                {"role": "user", "message": user_message, "timestamp": datetime.utcnow()},
            ]
            
            # Supervise new workflow execution
            return await self.supervise_workflow_execution(
                user_query=user_message,
                workflow_output=new_workflow_output,
                user_context=user_context,
                conversation_history=updated_history
            )
        
        return None
    
    async def get_active_contexts(self, user_id: str) -> List[SupervisionContext]:
        """Get all active supervision contexts for a user"""
        contexts = []
        
        if self.redis_client:
            # Load from Redis
            pattern = f"supervision_context:*:{user_id}"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                context_data = await self.redis_client.get(key)
                if context_data:
                    try:
                        context = SupervisionContext.model_validate_json(context_data)
                        if datetime.utcnow() <= context.expires_at:
                            contexts.append(context)
                        else:
                            # Cleanup expired context
                            await self.redis_client.delete(key)
                    except Exception:
                        continue
        else:
            # Use in-memory cache
            for context in self._context_cache.values():
                if (context.user_id == user_id and 
                    datetime.utcnow() <= context.expires_at):
                    contexts.append(context)
        
        # Sort by creation time (newest first)
        return sorted(contexts, key=lambda x: x.created_at, reverse=True)
    
    async def cleanup_expired_contexts(self):
        """Cleanup expired supervision contexts"""
        now = datetime.utcnow()
        
        if self.redis_client:
            # Cleanup Redis contexts
            pattern = "supervision_context:*"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                context_data = await self.redis_client.get(key)
                if context_data:
                    try:
                        context = SupervisionContext.model_validate_json(context_data)
                        if now > context.expires_at:
                            await self.redis_client.delete(key)
                    except Exception:
                        # Delete corrupted data
                        await self.redis_client.delete(key)
        else:
            # Cleanup in-memory cache
            expired_traces = [
                trace_id for trace_id, context in self._context_cache.items()
                if now > context.expires_at
            ]
            for trace_id in expired_traces:
                self._context_cache.pop(trace_id, None)
    
    async def _persist_supervision_context(self, context: SupervisionContext):
        """Persist supervision context for follow-up operations"""
        
        if self.redis_client:
            # Store in Redis with TTL
            key = f"supervision_context:{context.trace_id}:{context.user_id}"
            ttl_seconds = int((context.expires_at - datetime.utcnow()).total_seconds())
            
            await self.redis_client.setex(
                key,
                ttl_seconds,
                context.model_dump_json()
            )
        else:
            # Store in memory
            self._context_cache[context.trace_id] = context
    
    async def _load_supervision_context(self, trace_id: str) -> Optional[SupervisionContext]:
        """Load supervision context by trace ID"""
        
        if self.redis_client:
            # Try to load from Redis first
            pattern = f"supervision_context:{trace_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                context_data = await self.redis_client.get(keys[0])
                if context_data:
                    try:
                        return SupervisionContext.model_validate_json(context_data)
                    except Exception:
                        # Delete corrupted data
                        await self.redis_client.delete(keys[0])
                        return None
        
        # Fallback to in-memory cache
        return self._context_cache.get(trace_id)
    
    async def _cleanup_supervision_context(self, trace_id: str):
        """Cleanup specific supervision context"""
        
        if self.redis_client:
            pattern = f"supervision_context:{trace_id}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        
        self._context_cache.pop(trace_id, None)
    
    async def _execute_follow_up_workflow(
        self,
        routing_info: Dict[str, Any],
        supervision_context: SupervisionContext,
        user_message: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowOutput]:
        """Execute workflow based on follow-up routing information"""
        
        try:
            # Import here to avoid circular import
            from ..orchestrator import get_agent_orchestrator
            orchestrator = await get_agent_orchestrator()
            workflow_type = routing_info["workflow_type"]
            operation = routing_info["operation"]
            parameters = routing_info.get("parameters", {})
            
            # Prepare input data based on previous context and new parameters
            input_data = {
                "operation": operation,
                **parameters
            }
            
            # Add context from previous workflow if relevant
            if supervision_context.last_output.follow_up_context:
                input_data.update(supervision_context.last_output.follow_up_context)
            
            # Execute workflow
            result = await orchestrator.execute_workflow(
                workflow_type=getattr(orchestrator.workflows.keys().__iter__().__next__().__class__, workflow_type.upper()),
                user_id=supervision_context.user_id,
                input_data=input_data,
                user_context=user_context,
                connected_accounts=user_context.get("connected_accounts") if user_context else None,
                trace_id=None  # Generate new trace ID for follow-up
            )
            
            # Convert orchestrator result to WorkflowOutput
            return self._convert_orchestrator_result_to_workflow_output(
                result, workflow_type
            )
            
        except Exception as e:
            # Return error workflow output
            return create_workflow_output(
                workflow_type=routing_info["workflow_type"],
                status=WorkflowStatus.FAILURE,
                execution_time=0.0,
                trace_id=supervision_context.trace_id,
                error=f"Follow-up execution failed: {str(e)}",
                error_code="FOLLOW_UP_EXECUTION_ERROR"
            )
    
    def _convert_orchestrator_result_to_workflow_output(
        self, 
        orchestrator_result: Dict[str, Any], 
        workflow_type: str
    ) -> WorkflowOutput:
        """Convert orchestrator result to structured WorkflowOutput"""
        
        # Determine status
        if orchestrator_result.get("status") == "completed":
            if orchestrator_result.get("result", {}).get("success", True):
                status = WorkflowStatus.SUCCESS
            else:
                status = WorkflowStatus.PARTIAL_SUCCESS
        else:
            status = WorkflowStatus.FAILURE
        
        # Extract data
        result_data = orchestrator_result.get("result", {})
        error = result_data.get("error") if not result_data.get("success", True) else None
        
        return create_workflow_output(
            workflow_type=workflow_type,
            status=status,
            execution_time=orchestrator_result.get("execution_time", 0.0),
            trace_id=orchestrator_result.get("workflow_id", "unknown"),
            data=result_data,
            error=error
        )
    
    async def _generate_conversational_follow_up(
        self,
        user_message: str,
        supervision_context: SupervisionContext,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ConversationResponse:
        """Generate conversational response for non-actionable follow-ups"""
        
        # Create a simple workflow output for the conversation
        chat_output = create_workflow_output(
            workflow_type="natural_language",
            status=WorkflowStatus.SUCCESS,
            execution_time=0.1,
            trace_id=supervision_context.trace_id,
            data={
                "user_intent": "clarification",
                "entities": {},
                "confidence_score": 0.5,
                "requires_clarification": False
            }
        )
        
        # Wrap in conversation layer
        return await self.conversation_layer.wrap_workflow_output(
            user_query=user_message,
            workflow_output=chat_output,
            user_context=user_context,
            conversation_history=supervision_context.conversation_history
        )


# Global supervisor instance
workflow_supervisor = WorkflowSupervisor()


async def get_workflow_supervisor() -> WorkflowSupervisor:
    """Get the global workflow supervisor instance"""
    if workflow_supervisor.redis_client is None:
        await workflow_supervisor.initialize()
    return workflow_supervisor