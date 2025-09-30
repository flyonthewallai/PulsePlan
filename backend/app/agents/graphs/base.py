"""
Base workflow classes and state management for LangGraph workflows
"""
from typing import TypedDict, Optional, Any, List, Dict
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import uuid

from langgraph.graph import StateGraph, END


class WorkflowType(str, Enum):
    # NATURAL_LANGUAGE removed - handled by unified agent system
    CALENDAR = "calendar"
    TASK = "task"
    DATABASE = "database"
    BRIEFING = "briefing"
    SCHEDULING = "scheduling"
    EMAIL = "email"
    SEARCH = "search"


class WorkflowError(Exception):
    """Base workflow error with context and recovery information"""
    
    def __init__(self, message: str, context: Dict[str, Any], recoverable: bool = False):
        self.message = message
        self.context = context
        self.recoverable = recoverable
        super().__init__(message)


class WorkflowState(TypedDict):
    """
    Base state structure for all LangGraph workflows
    Following the design from LANGGRAPH_AGENT_WORKFLOWS.md
    """
    # Core state
    user_id: str
    request_id: str
    workflow_type: str
    
    # Input/Output
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    
    # Context
    user_context: Dict[str, Any]
    connected_accounts: Dict[str, Any]
    
    # Execution tracking
    current_node: str
    visited_nodes: List[str]
    execution_start: datetime
    
    # Error handling
    error: Optional[Dict[str, Any]]  # Serializable error info
    retry_count: int
    
    # Observability
    trace_id: str
    metrics: Dict[str, Any]
    
    # Workflow-specific data
    search_data: Optional[Dict[str, Any]]  # For SearchGraph workflow
    email_data: Optional[List[Dict[str, Any]]]  # For EmailGraph workflow
    
    # New fields for structured output and feedback loops
    structured_output: Optional[Dict[str, Any]]  # Structured machine-readable output
    requires_feedback: bool  # Whether workflow needs user feedback
    feedback_request: Optional[Dict[str, Any]]  # Details about what feedback is needed
    follow_up_context: Optional[Dict[str, Any]]  # Context for follow-up operations


class BaseWorkflow(ABC):
    """
    Abstract base class for all LangGraph workflows
    Implements the standard workflow pattern from the design document
    """
    
    def __init__(self, workflow_type: WorkflowType):
        self.workflow_type = workflow_type
        self.graph = None
        
    @abstractmethod
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for this workflow"""
        pass
    
    @abstractmethod
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        pass
    
    def build_graph(self) -> Any:
        """Build and compile the LangGraph workflow"""
        if self.graph is not None:
            return self.graph
            
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        nodes = self.define_nodes()
        for name, func in nodes.items():
            workflow.add_node(name, func)
            
        # Add edges
        edges = self.define_edges()
        for edge in edges:
            if len(edge) == 2:
                # Simple edge
                workflow.add_edge(edge[0], edge[1])
            elif len(edge) == 3:
                # Conditional edge
                workflow.add_conditional_edges(edge[0], edge[1], edge[2])
        
        # Set entry point (first node)
        entry_nodes = self.get_entry_nodes()
        if entry_nodes:
            workflow.set_entry_point(entry_nodes[0])
        
        # Compile graph
        self.graph = workflow.compile()
        return self.graph
    
    def get_entry_nodes(self) -> List[str]:
        """Get entry point nodes for this workflow"""
        return ["input_validator"]
    
    async def execute(self, initial_state: WorkflowState) -> WorkflowState:
        """Execute the workflow with observability and error handling"""
        try:
            # Initialize execution tracking
            initial_state.update({
                "execution_start": datetime.utcnow(),
                "current_node": "starting",
                "visited_nodes": [],
                "retry_count": 0,
                "trace_id": initial_state.get("trace_id", str(uuid.uuid4())),  # Preserve existing trace_id
                "metrics": {}
            })
            
            # Build and execute graph
            graph = self.build_graph()
            result = await graph.ainvoke(initial_state)
            
            return result
            
        except Exception as e:
            # Handle workflow errors
            error_context = {
                "workflow_type": self.workflow_type.value,
                "user_id": initial_state.get("user_id"),
                "current_node": initial_state.get("current_node"),
                "trace_id": initial_state.get("trace_id")
            }
            
            raise WorkflowError(
                message=f"Workflow execution failed: {str(e)}",
                context=error_context,
                recoverable=isinstance(e, (TimeoutError, ConnectionError))
            )
    
    # Standard workflow nodes that all workflows can use
    
    def input_validator_node(self, state: WorkflowState) -> WorkflowState:
        """Validate and sanitize inputs - Step 1 of standard pattern"""
        state["current_node"] = "input_validator"
        state["visited_nodes"].append("input_validator")
        
        # Basic input validation
        if not state.get("user_id"):
            raise WorkflowError("Missing user_id", {"state": state})
        
        if not state.get("input_data"):
            raise WorkflowError("Missing input_data", {"state": state})
            
        return state
    
    def policy_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Check permissions and scopes - Step 2 of standard pattern"""
        state["current_node"] = "policy_gate"
        state["visited_nodes"].append("policy_gate")
        
        # TODO: Implement policy engine integration
        # For now, simple admin check from user context
        user_context = state.get("user_context", {})
        if not user_context.get("permissions", {}).get("can_execute_workflows", True):
            raise WorkflowError("Permission denied", {"user_id": state["user_id"]})
            
        return state
    
    def rate_limiter_node(self, state: WorkflowState) -> WorkflowState:
        """Apply rate limiting - Step 3 of standard pattern"""
        state["current_node"] = "rate_limiter"  
        state["visited_nodes"].append("rate_limiter")
        
        # TODO: Implement hierarchical rate limiting
        # For now, simple check
        user_id = state["user_id"]
        workflow_type = state["workflow_type"]
        
        # Log for observability
        state["metrics"]["rate_limit_check"] = {
            "user_id": user_id,
            "workflow_type": workflow_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return state
    
    def idempotency_checker_node(self, state: WorkflowState) -> WorkflowState:
        """Ensure exactly-once execution - Step 5 of standard pattern"""
        state["current_node"] = "idempotency_checker"
        state["visited_nodes"].append("idempotency_checker")
        
        # TODO: Implement idempotency checking with Redis
        # For now, just track in metrics
        state["metrics"]["idempotency_check"] = {
            "request_id": state["request_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return state
    
    def result_processor_node(self, state: WorkflowState) -> WorkflowState:
        """Format and validate outputs - Step 6 of standard pattern"""
        state["current_node"] = "result_processor"
        state["visited_nodes"].append("result_processor")
        
        # Ensure output_data exists
        if not state.get("output_data"):
            state["output_data"] = {}
            
        # Add metadata
        state["output_data"]["metadata"] = {
            "workflow_type": state["workflow_type"],
            "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
            "nodes_visited": len(state.get("visited_nodes", []))
        }
        
        return state
    
    def trace_updater_node(self, state: WorkflowState) -> WorkflowState:
        """Record traces and metrics - Step 7 of standard pattern"""
        state["current_node"] = "trace_updater"
        state["visited_nodes"].append("trace_updater")
        
        # TODO: Implement OpenTelemetry integration
        # For now, add to metrics
        state["metrics"]["execution_summary"] = {
            "workflow_type": state["workflow_type"],
            "user_id": state["user_id"],
            "trace_id": state["trace_id"],
            "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
            "nodes_visited": state["visited_nodes"],
            "success": state.get("error") is None
        }
        
        return state
    
    def error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and determine recovery strategy"""
        state["current_node"] = "error_handler"
        state["visited_nodes"].append("error_handler")
        
        error = state.get("error")
        if error and error.get("recoverable") and state["retry_count"] < 3:
            # Retry recoverable errors
            state["retry_count"] += 1
            state["metrics"]["retry_attempt"] = state["retry_count"]
            return state
        else:
            # Fail gracefully
            state["output_data"] = {
                "error": "Workflow execution failed",
                "recoverable": False,
                "context": error
            }
            return state
    
    def structured_output_node(self, state: WorkflowState) -> WorkflowState:
        """Generate structured machine-readable output - New feedback loop step"""
        state["current_node"] = "structured_output"
        state["visited_nodes"].append("structured_output")
        
        # Create structured output based on workflow results
        structured_data = self._create_structured_output(state)
        state["structured_output"] = structured_data
        
        # Determine if feedback is needed
        state["requires_feedback"] = self._requires_user_feedback(state)
        
        if state["requires_feedback"]:
            state["feedback_request"] = self._create_feedback_request(state)
        
        # Set follow-up context for supervisor
        state["follow_up_context"] = self._create_follow_up_context(state)
        
        return state
    
    def feedback_loop_node(self, state: WorkflowState) -> WorkflowState:
        """Handle feedback collection and processing - New feedback loop step"""
        state["current_node"] = "feedback_loop"
        state["visited_nodes"].append("feedback_loop")
        
        # Check if we have pending feedback that needs to be processed
        if state.get("requires_feedback") and not state.get("feedback_received"):
            # Workflow is waiting for user feedback
            state["output_data"]["status"] = "awaiting_feedback"
            state["output_data"]["feedback_request"] = state.get("feedback_request")
        else:
            # Process received feedback or continue if no feedback needed
            if state.get("feedback_received"):
                self._process_user_feedback(state)
            
            state["output_data"]["status"] = "completed"
        
        return state
    
    def response_node(self, state: WorkflowState) -> WorkflowState:
        """Final response node that prepares output for conversation layer"""
        state["current_node"] = "response"
        state["visited_nodes"].append("response")
        
        # Ensure structured output exists
        if not state.get("structured_output"):
            state["structured_output"] = self._create_structured_output(state)
        
        # Prepare final output with structured data and metadata
        final_output = {
            "structured_data": state["structured_output"],
            "success": state.get("error") is None,
            "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
            "trace_id": state["trace_id"],
            "workflow_type": state["workflow_type"],
            "requires_feedback": state.get("requires_feedback", False),
            "feedback_request": state.get("feedback_request"),
            "follow_up_context": state.get("follow_up_context"),
            "suggested_actions": self._get_suggested_actions(state)
        }
        
        # Merge with existing output_data
        if state.get("output_data"):
            final_output.update(state["output_data"])
        
        state["output_data"] = final_output
        
        return state
    
    def _create_structured_output(self, state: WorkflowState) -> Dict[str, Any]:
        """Create structured machine-readable output - override in subclasses"""
        return {
            "workflow_type": state["workflow_type"],
            "status": "success" if not state.get("error") else "failure",
            "data": state.get("output_data", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _requires_user_feedback(self, state: WorkflowState) -> bool:
        """Determine if workflow output requires user feedback - override in subclasses"""
        # Default: require feedback if there are errors or missing required information
        if state.get("error"):
            error_info = state["error"]
            if isinstance(error_info, dict) and error_info.get("recoverable"):
                return True
        
        # Check for incomplete operations that might need user input
        output_data = state.get("output_data", {})
        if output_data.get("partial_success") or output_data.get("needs_clarification"):
            return True
        
        return False
    
    def _create_feedback_request(self, state: WorkflowState) -> Dict[str, Any]:
        """Create feedback request details - override in subclasses"""
        return {
            "message": "I need more information to complete this request.",
            "required_info": ["clarification"],
            "context": {
                "workflow_type": state["workflow_type"],
                "current_operation": state["input_data"].get("operation", "unknown")
            }
        }
    
    def _create_follow_up_context(self, state: WorkflowState) -> Dict[str, Any]:
        """Create context for follow-up operations - override in subclasses"""
        return {
            "workflow_type": state["workflow_type"],
            "last_operation": state["input_data"].get("operation"),
            "output_summary": state.get("structured_output", {}),
            "user_context": state.get("user_context", {}),
            "connected_accounts": state.get("connected_accounts", {})
        }
    
    def _get_suggested_actions(self, state: WorkflowState) -> List[str]:
        """Get suggested follow-up actions - override in subclasses"""
        actions = []
        
        # Add workflow-specific suggestions based on success/failure
        if state.get("error"):
            actions.append("Try again")
            actions.append("Get help")
        else:
            workflow_type = state["workflow_type"]
            if workflow_type == "calendar":
                actions.extend(["Create event", "View schedule", "Sync calendars"])
            elif workflow_type == "task":
                actions.extend(["Add task", "Mark complete", "View progress"])
            elif workflow_type == "scheduling":
                actions.extend(["Adjust schedule", "Add constraints", "Optimize"])
        
        return actions[:5]  # Limit to 5 suggestions
    
    def _process_user_feedback(self, state: WorkflowState) -> None:
        """Process user feedback and update state - override in subclasses"""
        feedback_data = state.get("feedback_received", {})
        
        # Log feedback processing
        state["metrics"]["feedback_processed"] = {
            "feedback_type": feedback_data.get("type", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Default processing - subclasses should override for specific behavior


def create_initial_state(
    user_id: str,
    workflow_type: WorkflowType,
    input_data: Dict[str, Any],
    user_context: Optional[Dict[str, Any]] = None,
    connected_accounts: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> WorkflowState:
    """Helper function to create initial workflow state"""
    return WorkflowState(
        user_id=user_id,
        request_id=str(uuid.uuid4()),
        workflow_type=workflow_type.value,
        input_data=input_data,
        output_data=None,
        user_context=user_context or {},
        connected_accounts=connected_accounts or {},
        current_node="",
        visited_nodes=[],
        execution_start=datetime.utcnow(),
        error=None,
        retry_count=0,
        trace_id=trace_id or str(uuid.uuid4()),
        metrics={},
        search_data=None,
        email_data=None,
        structured_output=None,
        requires_feedback=False,
        feedback_request=None,
        follow_up_context=None
    )