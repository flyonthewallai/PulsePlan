"""
Routing Service
Centralized routing logic and decision management
"""
from typing import Dict, Any
from ..base import WorkflowState


class RoutingService:
    """Service for managing workflow routing decisions"""
    
    @staticmethod
    def determine_next_node(state: WorkflowState) -> str:
        """Determine the next node based on current state and intent"""
        intent = state["input_data"].get("classified_intent")
        confidence = state["input_data"].get("confidence", 0.0)
        
        # Handle low confidence cases
        if intent in ["ambiguous", "unknown"] or confidence < 0.4:
            return "clarification_generator"
        
        # Route to appropriate workflow
        intent_to_router = {
            "calendar": "calendar_router",
            "task": "task_router", 
            "todo": "todo_router",
            "briefing": "briefing_router",
            "scheduling": "scheduling_router",
            "email": "email_router",
            "search": "search_router",
            "chat": "chat_router"
        }
        
        return intent_to_router.get(intent, "clarification_generator")
    
    @staticmethod
    def should_apply_policy_gate(state: WorkflowState) -> bool:
        """Determine if policy gate should be applied"""
        intent = state["input_data"].get("classified_intent")
        
        # Apply policy gate for actions that modify data or external systems
        policy_required_intents = ["calendar", "task", "todo", "email", "scheduling"]
        
        return intent in policy_required_intents
    
    @staticmethod
    def should_apply_rate_limiting(state: WorkflowState) -> bool:
        """Determine if rate limiting should be applied"""
        intent = state["input_data"].get("classified_intent")
        
        # Apply rate limiting for resource-intensive operations
        rate_limited_intents = ["email", "search", "briefing"]
        
        return intent in rate_limited_intents
    
    @staticmethod
    def get_workflow_metadata(state: WorkflowState) -> Dict[str, Any]:
        """Get metadata for the current workflow routing decision"""
        return {
            "intent": state["input_data"].get("classified_intent"),
            "confidence": state["input_data"].get("confidence", 0.0),
            "query": state["input_data"].get("query", ""),
            "user_id": state.get("user_id"),
            "trace_id": state.get("trace_id"),
            "needs_clarification": state["input_data"].get("needs_clarification", False),
            "has_task_preview": bool(state["input_data"].get("immediate_response", {}).get("task_preview")),
            "conversation_type": state["input_data"].get("immediate_response", {}).get("conversation_type")
        }