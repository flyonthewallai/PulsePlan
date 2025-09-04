"""
Agent data models and state management
"""
from typing import TypedDict, Optional, Any, List, Dict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    """Available workflow types"""
    NATURAL_LANGUAGE = "natural_language"
    CALENDAR = "calendar" 
    TASK = "task"
    BRIEFING = "briefing"
    SCHEDULING = "scheduling"
    CHAT = "chat"
    SEARCH = "search"


class AgentRequest(BaseModel):
    """Incoming agent request"""
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="User query or command")
    workflow_type: Optional[WorkflowType] = Field(None, description="Specific workflow to execute")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Request metadata")


class AgentResponse(BaseModel):
    """Agent response"""
    success: bool = Field(..., description="Whether the request was successful")
    workflow_type: str = Field(..., description="Workflow that was executed")
    result: Dict[str, Any] = Field(..., description="Workflow execution result")
    execution_time: float = Field(..., description="Execution time in seconds")
    trace_id: str = Field(..., description="Request trace identifier")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Response metadata")


class WorkflowState(TypedDict):
    """
    LangGraph workflow state - matches your original WorkflowState
    but organized under agents structure
    """
    # Core identifiers
    user_id: str
    request_id: str
    workflow_type: str
    
    # Input/Output data
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    
    # User context and connections
    user_context: Dict[str, Any]
    connected_accounts: Dict[str, Any]
    
    # Execution tracking
    current_node: str
    visited_nodes: List[str]
    execution_start: datetime
    
    # Error handling
    error: Optional[Dict[str, Any]]
    retry_count: int
    
    # Observability
    trace_id: str
    metrics: Dict[str, Any]


class AgentError(Exception):
    """Base agent error"""
    def __init__(self, message: str, context: Dict[str, Any], recoverable: bool = False):
        self.message = message
        self.context = context
        self.recoverable = recoverable
        super().__init__(message)


class ToolResult(BaseModel):
    """Tool execution result"""
    success: bool = Field(..., description="Whether tool execution succeeded")
    data: Dict[str, Any] = Field(..., description="Tool output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for workflow state"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }


def create_workflow_state(
    user_id: str,
    workflow_type: WorkflowType,
    input_data: Dict[str, Any],
    user_context: Optional[Dict[str, Any]] = None,
    connected_accounts: Optional[Dict[str, Any]] = None
) -> WorkflowState:
    """Create initial workflow state"""
    import uuid
    
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
        trace_id=str(uuid.uuid4()),
        metrics={}
    )