"""
Supervisor Integration Nodes
Handles workflow supervision with multi-turn conversations
"""
from typing import Dict, Any
import uuid
from datetime import datetime

from ..base import WorkflowState
from ..supervisors.todo_supervisor import TodoSupervisorAgent
from ..supervisors.base import SupervisionResult


class WorkflowSupervisorOrchestrator:
    """Orchestrates workflow supervisors with multi-turn conversation support"""
    
    def __init__(self):
        # Initialize supervisors for each workflow type
        self.supervisors = {
            "todo": TodoSupervisorAgent(),
            # Add other supervisors as they're implemented
            # "task": TaskSupervisorAgent(),
            # "calendar": CalendarSupervisorAgent(),
            # "email": EmailSupervisorAgent(),
        }
        
        # Track ongoing conversations
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
    
    def supervisor_node(self, state: WorkflowState) -> WorkflowState:
        """Main supervisor node - routes to appropriate supervisor"""
        state["current_node"] = "supervisor"
        state["visited_nodes"].append("supervisor")
        
        intent = state["input_data"]["classified_intent"]
        query = state["input_data"]["query"]
        user_id = state["user_id"]
        
        # Check if this is a continuing conversation
        conversation_id = state["input_data"].get("conversation_id")
        
        try:
            if intent in self.supervisors:
                supervisor = self.supervisors[intent]
                
                # Build context
                context = {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "intent": intent,
                    "user_context": state.get("user_context", {})
                }
                
                # Get supervision result (this is async, but we'll simulate sync for now)
                # In real implementation, this would be awaited
                supervision_result = self._simulate_supervision(
                    supervisor, query, context, conversation_id
                )
                
                # Store result in state
                state["input_data"]["supervision_result"] = supervision_result.__dict__
                
                # Handle conversation tracking
                if not supervision_result.ready_to_execute:
                    # Start or continue conversation
                    if not conversation_id:
                        conversation_id = str(uuid.uuid4())
                        state["input_data"]["conversation_id"] = conversation_id
                    
                    # Store conversation state
                    self.active_conversations[conversation_id] = {
                        "intent": intent,
                        "user_id": user_id,
                        "started_at": datetime.utcnow().isoformat(),
                        "turn_count": self.active_conversations.get(conversation_id, {}).get("turn_count", 0) + 1,
                        "last_query": query,
                        "supervision_result": supervision_result.__dict__
                    }
                else:
                    # Conversation complete, clean up if needed
                    if conversation_id and conversation_id in self.active_conversations:
                        del self.active_conversations[conversation_id]
                
                print(f"🤖 [SUPERVISOR] {intent.upper()} supervision complete")
                print(f"    Ready to execute: {supervision_result.ready_to_execute}")
                print(f"    Operation: {supervision_result.operation_type}")
                print(f"    Parameters: {supervision_result.parameters}")
                if supervision_result.clarification_message:
                    print(f"    Clarification: {supervision_result.clarification_message}")
                
            else:
                # No supervisor available for this intent
                state["input_data"]["supervision_result"] = {
                    "operation_type": "unknown",
                    "parameters": {},
                    "ready_to_execute": False,
                    "clarification_message": f"No supervisor available for intent: {intent}",
                    "missing_context": ["supervisor"],
                    "confidence": 0.0,
                    "policy_violations": [],
                    "conversation_id": None
                }
                print(f"❌ [SUPERVISOR] No supervisor found for intent: {intent}")
            
        except Exception as e:
            # Error handling
            state["input_data"]["supervision_result"] = {
                "operation_type": "error",
                "parameters": {},
                "ready_to_execute": False,
                "clarification_message": f"Supervision failed: {str(e)}",
                "missing_context": ["error_recovery"],
                "confidence": 0.0,
                "policy_violations": [f"Supervision error: {str(e)}"],
                "conversation_id": None
            }
            print(f"💥 [SUPERVISOR] Error: {e}")
        
        return state
    
    def supervision_router(self, state: WorkflowState) -> str:
        """Route based on supervision result"""
        supervision_result = state["input_data"].get("supervision_result", {})
        ready_to_execute = supervision_result.get("ready_to_execute", False)
        
        if ready_to_execute:
            return "execute"
        else:
            return "clarify"
    
    def clarification_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle clarification requests and prepare response"""
        state["current_node"] = "clarification_handler"
        state["visited_nodes"].append("clarification_handler")
        
        supervision_result = state["input_data"].get("supervision_result", {})
        
        # Prepare clarification response
        clarification_response = {
            "type": "clarification_request",
            "message": supervision_result.get("clarification_message", "I need more information."),
            "missing_context": supervision_result.get("missing_context", []),
            "conversation_id": supervision_result.get("conversation_id"),
            "intent": state["input_data"]["classified_intent"],
            "suggestions": self._get_clarification_suggestions(
                state["input_data"]["classified_intent"],
                supervision_result.get("missing_context", [])
            )
        }
        
        # Store in result data
        state["result_data"] = clarification_response
        
        print(f"❓ [CLARIFICATION] Requesting more info: {clarification_response['message']}")
        return state
    
    def execution_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle execution when ready"""
        state["current_node"] = "execution_handler"  
        state["visited_nodes"].append("execution_handler")
        
        supervision_result = state["input_data"].get("supervision_result", {})
        intent = state["input_data"]["classified_intent"]
        
        # Prepare execution payload
        execution_payload = {
            "workflow_type": intent,
            "operation_type": supervision_result.get("operation_type"),
            "parameters": supervision_result.get("parameters", {}),
            "user_id": state["user_id"],
            "context": state.get("user_context", {}),
            "supervision_metadata": {
                "confidence": supervision_result.get("confidence", 0.0),
                "policy_validated": len(supervision_result.get("policy_violations", [])) == 0
            }
        }
        
        state["input_data"]["execution_payload"] = execution_payload
        
        print(f"🚀 [EXECUTION] Ready to execute {intent} workflow")
        print(f"    Operation: {execution_payload['operation_type']}")
        print(f"    Parameters: {execution_payload['parameters']}")
        
        return state
    
    def _simulate_supervision(
        self, 
        supervisor, 
        query: str, 
        context: Dict[str, Any], 
        conversation_id: str = None
    ) -> SupervisionResult:
        """Simulate async supervision call (in real implementation this would be awaited)"""
        
        # This is a simplified synchronous version
        # In real implementation, you'd await supervisor.supervise()
        
        # For demonstration, let's handle common todo patterns
        if isinstance(supervisor, TodoSupervisorAgent):
            return self._simulate_todo_supervision(query, context, conversation_id)
        
        # Default fallback
        return SupervisionResult(
            operation_type="unknown",
            parameters={},
            ready_to_execute=False,
            clarification_message="Supervision not implemented for this workflow type",
            missing_context=["implementation"],
            confidence=0.0
        )
    
    def _simulate_todo_supervision(
        self, 
        query: str, 
        context: Dict[str, Any], 
        conversation_id: str = None
    ) -> SupervisionResult:
        """Simulate todo supervision logic"""
        
        query_lower = query.lower().strip()
        
        # Simple pattern matching for demonstration
        if any(phrase in query_lower for phrase in ["add todo", "create todo", "new todo"]):
            if len(query.split()) <= 2:  # Very vague request
                return SupervisionResult(
                    operation_type="create",
                    parameters={},
                    ready_to_execute=False,
                    clarification_message="What would you like to add to your todo list?",
                    missing_context=["title"],
                    confidence=0.3
                )
            else:
                # Extract title from query
                title = query_lower.replace("add todo", "").replace("create todo", "").replace("new todo", "").strip()
                if title:
                    return SupervisionResult(
                        operation_type="create",
                        parameters={"title": title},
                        ready_to_execute=True,
                        confidence=0.8
                    )
        
        elif "list" in query_lower or "show" in query_lower:
            return SupervisionResult(
                operation_type="list",
                parameters={"filters": {}},
                ready_to_execute=True,
                confidence=0.9
            )
        
        # Default - need clarification
        return SupervisionResult(
            operation_type="unknown",
            parameters={},
            ready_to_execute=False,
            clarification_message="I'm not sure what you'd like me to do with your todos. Could you be more specific?",
            missing_context=["operation_type"],
            confidence=0.1
        )
    
    def _get_clarification_suggestions(self, intent: str, missing_context: list) -> list:
        """Get helpful suggestions for clarification"""
        
        suggestions = {
            "todo": [
                "Try: 'Add buy groceries to my todo list'",
                "Try: 'Show me my pending todos'",
                "Try: 'Create urgent todo for project deadline'"
            ],
            "task": [
                "Try: 'Create task for website redesign'", 
                "Try: 'Show me my high priority tasks'"
            ],
            "calendar": [
                "Try: 'Schedule meeting with John tomorrow at 2pm'",
                "Try: 'Show me my calendar for this week'"
            ]
        }
        
        return suggestions.get(intent, ["Please provide more specific details about what you'd like me to do."])