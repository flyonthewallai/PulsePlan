"""
Conversation Layer Service
Wraps structured workflow outputs in natural language responses using LLM
"""
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from ..models.workflow_output import (
    WorkflowOutput, ConversationResponse, SupervisionContext, 
    FeedbackRequest, WorkflowStatus
)
from ...core.llm import get_llm_client


class ConversationLayer:
    """
    Service that converts structured workflow outputs into natural language responses
    and handles conversation context for follow-up operations
    """
    
    def __init__(self):
        self.supervision_contexts: Dict[str, SupervisionContext] = {}
        self.llm_client = get_llm_client()
    
    async def wrap_workflow_output(
        self,
        user_query: str,
        workflow_output: WorkflowOutput,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationResponse:
        """
        Convert structured workflow output into natural language response
        """
        
        # Create supervision context for follow-ups
        supervision_context = SupervisionContext(
            trace_id=workflow_output.trace_id,
            user_id=user_context.get("user_id") if user_context else "unknown",
            workflow_type=workflow_output.workflow,
            last_output=workflow_output,
            conversation_history=conversation_history or [],
            expires_at=datetime.utcnow() + timedelta(hours=2)
        )
        
        # Store context for follow-up operations
        self.supervision_contexts[workflow_output.trace_id] = supervision_context
        
        # Generate natural language response
        natural_response = await self._generate_natural_response(
            user_query=user_query,
            workflow_output=workflow_output,
            user_context=user_context,
            conversation_history=conversation_history
        )
        
        # Determine if follow-up is likely needed
        requires_follow_up = self._requires_follow_up(workflow_output)
        
        # Generate suggested replies
        suggested_replies = self._generate_suggested_replies(workflow_output)
        
        return ConversationResponse(
            message=natural_response,
            workflow_output=workflow_output,
            supervision_context=supervision_context,
            requires_follow_up=requires_follow_up,
            suggested_replies=suggested_replies
        )
    
    async def handle_follow_up(
        self,
        user_message: str,
        trace_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle follow-up messages that reference previous workflow execution
        Returns routing information for the supervisor
        """
        supervision_context = self.supervision_contexts.get(trace_id)
        if not supervision_context:
            return None
        
        # Check if context has expired
        if datetime.utcnow() > supervision_context.expires_at:
            self.supervision_contexts.pop(trace_id, None)
            return None
        
        # Analyze user message to determine if it's actionable
        routing_info = await self._analyze_follow_up_message(
            user_message=user_message,
            supervision_context=supervision_context,
            user_context=user_context
        )
        
        return routing_info
    
    def get_supervision_context(self, trace_id: str) -> Optional[SupervisionContext]:
        """Get supervision context by trace ID"""
        return self.supervision_contexts.get(trace_id)
    
    def cleanup_expired_contexts(self):
        """Remove expired supervision contexts"""
        now = datetime.utcnow()
        expired_traces = [
            trace_id for trace_id, context in self.supervision_contexts.items()
            if now > context.expires_at
        ]
        for trace_id in expired_traces:
            self.supervision_contexts.pop(trace_id, None)
    
    async def _generate_natural_response(
        self,
        user_query: str,
        workflow_output: WorkflowOutput,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate natural language response using LLM"""
        
        # Create system prompt
        system_prompt = self._create_conversation_system_prompt()
        
        # Create user prompt with structured data
        user_prompt = self._create_conversation_user_prompt(
            user_query=user_query,
            workflow_output=workflow_output,
            user_context=user_context,
            conversation_history=conversation_history
        )
        
        try:
            response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=500
            )
            return response.strip()
        except Exception as e:
            # Fallback to template-based response
            return self._generate_fallback_response(workflow_output)
    
    def _create_conversation_system_prompt(self) -> str:
        """Create system prompt for conversation generation"""
        return """You are a helpful AI assistant that converts structured workflow results into natural, conversational responses.

Your role:
1. Take structured data from workflow execution and present it naturally to the user
2. Be concise but informative
3. Highlight key information and results
4. Suggest natural follow-up actions when appropriate
5. Handle errors gracefully with helpful guidance

Guidelines:
- Use a friendly, professional tone
- Present data in an easily digestible format
- For lists, use bullet points or natural enumeration
- For errors, provide constructive next steps
- For successful operations, confirm what was accomplished
- Keep responses focused and avoid unnecessary elaboration"""
    
    def _create_conversation_user_prompt(
        self,
        user_query: str,
        workflow_output: WorkflowOutput,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Create user prompt with structured data"""
        
        # Convert workflow output to JSON for LLM
        structured_data = workflow_output.model_dump(exclude_none=True)
        
        prompt = f"""User Query: "{user_query}"

Workflow Results:
{json.dumps(structured_data, indent=2, default=str)}

Please respond naturally to the user's query based on the structured workflow results above. 
Focus on what the user would find most relevant and helpful."""
        
        if conversation_history:
            prompt += f"\n\nConversation History:\n{json.dumps(conversation_history[-3:], indent=2)}"
        
        if user_context:
            prompt += f"\n\nUser Context:\n{json.dumps(user_context, indent=2, default=str)}"
        
        return prompt
    
    def _generate_fallback_response(self, workflow_output: WorkflowOutput) -> str:
        """Generate fallback response when LLM fails"""
        
        if workflow_output.status == WorkflowStatus.SUCCESS:
            return f"I've successfully completed your {workflow_output.workflow} request. The operation finished in {workflow_output.execution_time:.2f} seconds."
        
        elif workflow_output.status == WorkflowStatus.PARTIAL_SUCCESS:
            return f"I partially completed your {workflow_output.workflow} request. Some operations succeeded but there were issues with others."
        
        elif workflow_output.status == WorkflowStatus.FAILURE:
            error_msg = workflow_output.error or "An unknown error occurred"
            return f"I encountered an issue with your {workflow_output.workflow} request: {error_msg}"
        
        elif workflow_output.status == WorkflowStatus.NEEDS_INPUT:
            return f"I need more information to complete your {workflow_output.workflow} request. Could you provide additional details?"
        
        else:
            return "I've processed your request. Let me know if you need anything else!"
    
    def _requires_follow_up(self, workflow_output: WorkflowOutput) -> bool:
        """Determine if the workflow output likely requires follow-up"""
        
        # Always requires follow-up if needs input
        if workflow_output.status == WorkflowStatus.NEEDS_INPUT:
            return True
        
        # Check if there are suggested actions
        if workflow_output.suggested_actions:
            return True
        
        # Check workflow-specific conditions
        if workflow_output.workflow == "calendar":
            # Calendar operations might need follow-up for conflicts or scheduling
            return bool(workflow_output.data and getattr(workflow_output.data, 'conflicts', None))
        
        elif workflow_output.workflow == "scheduling":
            # Scheduling might need refinement
            return bool(workflow_output.data and getattr(workflow_output.data, 'conflicts', None))
        
        elif workflow_output.workflow == "task":
            # Task operations might need follow-up for related actions
            return workflow_output.status == WorkflowStatus.PARTIAL_SUCCESS
        
        return False
    
    def _generate_suggested_replies(self, workflow_output: WorkflowOutput) -> List[str]:
        """Generate suggested replies based on workflow output"""
        
        suggestions = []
        
        # Add workflow-specific suggestions
        if workflow_output.workflow == "calendar":
            if workflow_output.status == WorkflowStatus.SUCCESS:
                suggestions.extend([
                    "Create a new event",
                    "Show me my schedule for tomorrow",
                    "Are there any conflicts?"
                ])
        
        elif workflow_output.workflow == "task":
            if workflow_output.status == WorkflowStatus.SUCCESS:
                suggestions.extend([
                    "Add another task",
                    "Show me completed tasks",
                    "What's my progress?"
                ])
        
        elif workflow_output.workflow == "scheduling":
            if workflow_output.status == WorkflowStatus.SUCCESS:
                suggestions.extend([
                    "Adjust this schedule",
                    "Add more constraints",
                    "Show me alternatives"
                ])
        
        # Add general suggestions based on status
        if workflow_output.status == WorkflowStatus.FAILURE:
            suggestions.append("Try again")
            suggestions.append("Get help with this")
        
        # Add suggestions from workflow output
        if workflow_output.suggested_actions:
            suggestions.extend(workflow_output.suggested_actions[:3])  # Limit to 3
        
        return suggestions[:5]  # Limit total suggestions
    
    async def _analyze_follow_up_message(
        self,
        user_message: str,
        supervision_context: SupervisionContext,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Analyze follow-up message to determine routing"""
        
        # Use LLM to analyze if message is actionable and how to route it
        system_prompt = """You are analyzing a user's follow-up message to determine if it requires workflow execution.

Given the previous workflow execution context, determine:
1. Is this message actionable (requires a new workflow execution)?
2. If yes, which workflow should handle it?
3. What parameters should be passed?

Respond with JSON containing:
{
  "actionable": boolean,
  "workflow_type": string (if actionable),
  "operation": string (if actionable),
  "parameters": object (if actionable),
  "confidence": float (0-1)
}"""
        
        user_prompt = f"""Previous workflow execution:
Workflow Type: {supervision_context.workflow_type}
Last Output: {supervision_context.last_output.model_dump_json(exclude_none=True)}

User's follow-up message: "{user_message}"

Analyze if this requires a new workflow execution and how to route it."""
        
        try:
            response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=300
            )
            
            routing_info = json.loads(response)
            
            # Only return if confident and actionable
            if routing_info.get("actionable") and routing_info.get("confidence", 0) > 0.7:
                return routing_info
            
        except Exception as e:
            # Fallback analysis based on keywords
            return self._fallback_follow_up_analysis(user_message, supervision_context)
        
        return None
    
    def _fallback_follow_up_analysis(
        self, 
        user_message: str, 
        supervision_context: SupervisionContext
    ) -> Optional[Dict[str, Any]]:
        """Fallback follow-up analysis using keyword matching"""
        
        message_lower = user_message.lower()
        
        # Common follow-up patterns
        if any(word in message_lower for word in ["move", "reschedule", "change time"]):
            if supervision_context.workflow_type == "calendar":
                return {
                    "actionable": True,
                    "workflow_type": "calendar",
                    "operation": "update",
                    "confidence": 0.8
                }
        
        elif any(word in message_lower for word in ["add", "create", "new"]):
            return {
                "actionable": True,
                "workflow_type": supervision_context.workflow_type,
                "operation": "create", 
                "confidence": 0.7
            }
        
        elif any(word in message_lower for word in ["delete", "remove", "cancel"]):
            return {
                "actionable": True,
                "workflow_type": supervision_context.workflow_type,
                "operation": "delete",
                "confidence": 0.7
            }
        
        return None


# Global conversation layer instance
conversation_layer = ConversationLayer()


def get_conversation_layer() -> ConversationLayer:
    """Get the global conversation layer instance"""
    return conversation_layer