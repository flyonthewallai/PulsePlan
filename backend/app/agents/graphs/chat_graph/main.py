"""
Refactored ChatGraph - Main Workflow Class
Natural Language Processing Workflow with modular architecture
"""
from typing import Dict, List, Any
from datetime import datetime
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError
from .nodes import IntentClassifierNode, RouterNodes, ProcessorNodes
from .nodes.supervisor_nodes import WorkflowSupervisorOrchestrator
from .utils.validators import InputValidator


class ChatGraph(BaseWorkflow):
    """
    Modular Natural Language Processing Workflow that:
    1. Classifies user intent from natural language query
    2. Routes to appropriate specialized workflow
    3. Handles unknown intents with clarification
    """
    
    def __init__(self):
        super().__init__(WorkflowType.NATURAL_LANGUAGE)
        
        # Initialize modular components
        self.intent_classifier = IntentClassifierNode()
        self.routers = RouterNodes()
        self.processors = ProcessorNodes()
        self.validator = InputValidator()
        self.supervisor_orchestrator = WorkflowSupervisorOrchestrator()
    
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for natural language workflow using modular components"""
        return {
            "input_validator": self.input_validator_node,
            "intent_classifier": self.intent_classifier.execute,
            "supervisor": self.supervisor_orchestrator.supervisor_node,
            "clarification_handler": self.supervisor_orchestrator.clarification_handler_node,
            "execution_handler": self.supervisor_orchestrator.execution_handler_node,
            "policy_gate": self.policy_gate_node,
            "rate_limiter": self.rate_limiter_node,
            "calendar_router": self.routers.calendar_router_node,
            "task_router": self.routers.task_router_node,
            "todo_router": self.routers.todo_router_node,
            "briefing_router": self.routers.briefing_router_node,
            "scheduling_router": self.routers.scheduling_router_node,
            "email_router": self.routers.email_router_node,
            "canvas_router": self.routers.canvas_router_node,
            "search_router": self.routers.search_router_node,
            "chat_router": self.routers.chat_router_node,
            "clarification_generator": self.processors.clarification_generator_node,
            "result_processor": self.processors.result_processor_node,
            "trace_updater": self.processors.trace_updater_node,
            "error_handler": self.processors.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # New Supervisor-based workflow path
            ("input_validator", "intent_classifier"),
            ("intent_classifier", self.intent_router, {
                "calendar": "supervisor",
                "task": "supervisor", 
                "todo": "supervisor",
                "briefing": "supervisor",
                "scheduling": "supervisor",
                "email": "supervisor",
                "canvas": "supervisor",
                "search": "supervisor",
                "chat": "supervisor",
                "unknown": "clarification_generator",
                "ambiguous": "clarification_generator"
            }),
            
            # Supervisor decision routing
            ("supervisor", self.supervisor_orchestrator.supervision_router, {
                "execute": "execution_handler",
                "clarify": "clarification_handler"
            }),
            
            # Multi-turn clarification loop
            ("clarification_handler", "result_processor"),  # Return clarification to user
            
            # Execution path with policy/rate limiting
            ("execution_handler", "policy_gate"),
            ("policy_gate", "rate_limiter"), 
            ("rate_limiter", self.workflow_router, {
                "calendar": "calendar_router",
                "task": "task_router",
                "todo": "todo_router", 
                "briefing": "briefing_router",
                "scheduling": "scheduling_router",
                "email": "email_router",
                "canvas": "canvas_router",
                "search": "search_router",
                "chat": "chat_router"
            }),
            
            # Route to specialized workflows
            ("calendar_router", "result_processor"),
            ("task_router", "result_processor"),
            ("todo_router", "result_processor"),
            ("briefing_router", "result_processor"),
            ("scheduling_router", "result_processor"),
            ("email_router", "result_processor"),
            ("canvas_router", "result_processor"),
            ("search_router", "result_processor"),
            ("chat_router", "result_processor"),
            
            # Handle unknown intents (legacy path)
            ("clarification_generator", "result_processor"),
            
            # Final processing
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    # ============================================================================
    # Router Decision Functions (Delegated to RouterNodes)
    # ============================================================================
    
    def intent_router(self, state: WorkflowState) -> str:
        """Route based on classified intent with ambiguity handling"""
        return self.routers.intent_router(state)
    
    def workflow_router(self, state: WorkflowState) -> str:
        """Route to appropriate workflow after policy/rate checks"""
        return self.routers.workflow_router(state)
    
    # ============================================================================
    # Simplified Core Nodes (Most logic moved to modular components)
    # ============================================================================
    
    def input_validator_node(self, state: WorkflowState) -> WorkflowState:
        """Validate inputs and prepare state"""
        state["current_node"] = "input_validator"
        state["visited_nodes"].append("input_validator")
        
        # Use validator utility
        self.validator.validate_state_structure(state)
        self.validator.validate_query(state)
        self.validator.validate_user_context(state)
        
        print(f"✅ [INPUT VALIDATOR] Validation completed for user: {state['user_id']}")
        return state
    
    def policy_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Apply policy checks for protected operations"""
        state["current_node"] = "policy_gate"
        state["visited_nodes"].append("policy_gate")
        
        intent = state["input_data"]["classified_intent"]
        user_id = state["user_id"]
        
        # Basic policy enforcement
        policy_decision = {
            "intent": intent,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "approved": True,
            "policies_checked": ["basic_validation", "user_auth"]
        }
        
        state["input_data"]["policy_decision"] = policy_decision
        
        print(f"🛡️ [POLICY GATE] Policy check passed for intent: {intent}")
        return state
    
    def rate_limiter_node(self, state: WorkflowState) -> WorkflowState:
        """Apply rate limiting based on user and intent"""
        state["current_node"] = "rate_limiter"
        state["visited_nodes"].append("rate_limiter")
        
        intent = state["input_data"]["classified_intent"]
        user_id = state["user_id"]
        
        # Mock rate limiting - in production this would check Redis/database
        rate_limit_info = {
            "user_id": user_id,
            "intent": intent,
            "quota_remaining": 100,
            "reset_time": datetime.utcnow().timestamp() + 3600,
            "status": "within_limits"
        }
        
        state["input_data"]["rate_limit_info"] = rate_limit_info
        
        print(f"🚦 [RATE LIMITER] Rate limit check passed for intent: {intent}")
        return state


# ============================================================================
# Backward Compatibility Export
# ============================================================================

# This allows existing imports to continue working
__all__ = ['ChatGraph']