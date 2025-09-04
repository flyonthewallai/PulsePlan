"""
Structured workflow output models for clean separation between workflow execution and conversation layer
"""
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    NEEDS_INPUT = "needs_input"


class WorkflowOutputBase(BaseModel):
    """Base structured output for all workflows"""
    workflow: str = Field(..., description="The workflow type that generated this output")
    status: WorkflowStatus = Field(..., description="The execution status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this output was generated")
    execution_time: float = Field(..., description="Execution time in seconds")
    trace_id: str = Field(..., description="Unique trace identifier for this execution")
    
    # Core data returned by workflow
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data returned by workflow")
    
    # Error information
    error: Optional[str] = Field(None, description="Error message if workflow failed")
    error_code: Optional[str] = Field(None, description="Structured error code")
    
    # Context for follow-up operations
    follow_up_context: Optional[Dict[str, Any]] = Field(None, description="Context needed for follow-up operations")
    
    # Suggested next actions
    suggested_actions: List[str] = Field(default_factory=list, description="Actions user might want to take next")


class CalendarWorkflowOutput(WorkflowOutputBase):
    """Structured output for calendar operations"""
    workflow: Literal["calendar"] = "calendar"
    
    class CalendarData(BaseModel):
        provider: str = Field(..., description="Calendar provider (google, microsoft)")
        operation: str = Field(..., description="Operation performed")
        events: Optional[List[Dict[str, Any]]] = Field(None, description="List of calendar events")
        event_count: Optional[int] = Field(None, description="Total number of events")
        conflicts: Optional[List[Dict[str, Any]]] = Field(None, description="Any conflicts detected")
        sync_results: Optional[Dict[str, Any]] = Field(None, description="Sync operation results")
    
    data: Optional[CalendarData] = None


class TaskWorkflowOutput(WorkflowOutputBase):
    """Structured output for task operations"""
    workflow: Literal["task"] = "task"
    
    class TaskData(BaseModel):
        operation: str = Field(..., description="Operation performed (create, update, delete, list)")
        tasks: Optional[List[Dict[str, Any]]] = Field(None, description="List of tasks")
        task_count: Optional[int] = Field(None, description="Total number of tasks")
        completed_tasks: Optional[int] = Field(None, description="Number of completed tasks")
        categories: Optional[List[str]] = Field(None, description="Task categories")
    
    data: Optional[TaskData] = None


class SchedulingWorkflowOutput(WorkflowOutputBase):
    """Structured output for scheduling operations"""
    workflow: Literal["scheduling"] = "scheduling"
    
    class SchedulingData(BaseModel):
        schedule_created: bool = Field(..., description="Whether schedule was successfully created")
        scheduled_tasks: Optional[List[Dict[str, Any]]] = Field(None, description="Tasks that were scheduled")
        conflicts: Optional[List[Dict[str, Any]]] = Field(None, description="Scheduling conflicts found")
        optimization_score: Optional[float] = Field(None, description="Optimization score (0-1)")
        time_slots: Optional[List[Dict[str, Any]]] = Field(None, description="Available time slots")
    
    data: Optional[SchedulingData] = None


class BriefingWorkflowOutput(WorkflowOutputBase):
    """Structured output for briefing generation"""
    workflow: Literal["briefing"] = "briefing"
    
    class BriefingData(BaseModel):
        date: str = Field(..., description="Briefing date")
        summary: str = Field(..., description="Brief summary")
        agenda_items: List[Dict[str, Any]] = Field(default_factory=list, description="Agenda items")
        task_summary: Dict[str, Any] = Field(default_factory=dict, description="Task completion summary")
        calendar_summary: Dict[str, Any] = Field(default_factory=dict, description="Calendar summary")
        recommendations: List[str] = Field(default_factory=list, description="AI recommendations")
    
    data: Optional[BriefingData] = None


class SearchWorkflowOutput(WorkflowOutputBase):
    """Structured output for search operations"""
    workflow: Literal["search"] = "search"
    
    class SearchData(BaseModel):
        query: str = Field(..., description="Original search query")
        results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
        result_count: int = Field(default=0, description="Number of results found")
        sources: List[str] = Field(default_factory=list, description="Data sources searched")
    
    data: Optional[SearchData] = None


class DatabaseWorkflowOutput(WorkflowOutputBase):
    """Structured output for database operations"""
    workflow: Literal["database"] = "database"
    
    class DatabaseData(BaseModel):
        entity_type: str = Field(..., description="Type of entity operated on")
        operation: str = Field(..., description="Database operation performed")
        affected_count: int = Field(default=0, description="Number of records affected")
        records: Optional[List[Dict[str, Any]]] = Field(None, description="Records returned/affected")
    
    data: Optional[DatabaseData] = None


class ChatWorkflowOutput(WorkflowOutputBase):
    """Structured output for chat/natural language processing"""
    workflow: Literal["natural_language"] = "natural_language"
    
    class ChatData(BaseModel):
        user_intent: str = Field(..., description="Detected user intent")
        entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
        confidence_score: float = Field(default=0.0, description="Confidence in understanding (0-1)")
        workflow_routed_to: Optional[str] = Field(None, description="Which workflow the request was routed to")
        requires_clarification: bool = Field(default=False, description="Whether more info is needed from user")
    
    data: Optional[ChatData] = None


# Union type for all workflow outputs
WorkflowOutput = Union[
    CalendarWorkflowOutput,
    TaskWorkflowOutput, 
    SchedulingWorkflowOutput,
    BriefingWorkflowOutput,
    SearchWorkflowOutput,
    DatabaseWorkflowOutput,
    ChatWorkflowOutput
]


class SupervisionContext(BaseModel):
    """Context maintained by the supervisor for follow-up operations"""
    trace_id: str = Field(..., description="Workflow trace ID")
    user_id: str = Field(..., description="User ID")
    workflow_type: str = Field(..., description="Type of workflow executed")
    last_output: WorkflowOutput = Field(..., description="Last structured output from workflow")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation turns")
    pending_operations: List[Dict[str, Any]] = Field(default_factory=list, description="Operations waiting for user input")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="When this context expires")


class ConversationResponse(BaseModel):
    """Response from the conversation layer that wraps structured workflow output"""
    message: str = Field(..., description="Natural language response to user")
    workflow_output: WorkflowOutput = Field(..., description="Underlying structured workflow output") 
    supervision_context: Optional[SupervisionContext] = Field(None, description="Context for follow-up operations")
    requires_follow_up: bool = Field(default=False, description="Whether this requires user follow-up")
    suggested_replies: List[str] = Field(default_factory=list, description="Suggested user replies")


class FeedbackRequest(BaseModel):
    """Request for user feedback on workflow output"""
    message: str = Field(..., description="Question or request for clarification")
    options: Optional[List[str]] = Field(None, description="Predefined options for user to choose from")
    required_info: List[str] = Field(default_factory=list, description="Types of information needed")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context for the feedback request")


def create_workflow_output(
    workflow_type: str,
    status: WorkflowStatus,
    execution_time: float,
    trace_id: str,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
    follow_up_context: Optional[Dict[str, Any]] = None,
    suggested_actions: Optional[List[str]] = None
) -> WorkflowOutput:
    """Factory function to create the appropriate workflow output type"""
    
    base_kwargs = {
        "status": status,
        "execution_time": execution_time,
        "trace_id": trace_id,
        "error": error,
        "error_code": error_code,
        "follow_up_context": follow_up_context,
        "suggested_actions": suggested_actions or []
    }
    
    if workflow_type == "calendar":
        return CalendarWorkflowOutput(
            data=CalendarWorkflowOutput.CalendarData(**data) if data else None,
            **base_kwargs
        )
    elif workflow_type == "task":
        return TaskWorkflowOutput(
            data=TaskWorkflowOutput.TaskData(**data) if data else None,
            **base_kwargs
        )
    elif workflow_type == "scheduling":
        return SchedulingWorkflowOutput(
            data=SchedulingWorkflowOutput.SchedulingData(**data) if data else None,
            **base_kwargs
        )
    elif workflow_type == "briefing":
        return BriefingWorkflowOutput(
            data=BriefingWorkflowOutput.BriefingData(**data) if data else None,
            **base_kwargs
        )
    elif workflow_type == "search":
        return SearchWorkflowOutput(
            data=SearchWorkflowOutput.SearchData(**data) if data else None,
            **base_kwargs
        )
    elif workflow_type == "database":
        return DatabaseWorkflowOutput(
            data=DatabaseWorkflowOutput.DatabaseData(**data) if data else None,
            **base_kwargs
        )
    elif workflow_type == "natural_language":
        return ChatWorkflowOutput(
            data=ChatWorkflowOutput.ChatData(**data) if data else None,
            **base_kwargs
        )
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")