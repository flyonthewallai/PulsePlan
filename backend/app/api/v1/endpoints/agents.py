"""
Workflow API endpoints
Provides REST API access to LangGraph workflows
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, CurrentUser
from app.agents.orchestrator import get_agent_orchestrator, AgentOrchestrator
from app.agents.models import AgentError


router = APIRouter()


# Request/Response models
class NaturalLanguageRequest(BaseModel):
    query: str = Field(..., description="Natural language query to process")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class CalendarOperationRequest(BaseModel):
    provider: str = Field(..., description="Calendar provider (google, microsoft)")
    operation: str = Field(..., description="Operation type (list, create, update, delete)")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event data for create/update")
    event_id: Optional[str] = Field(None, description="Event ID for update/delete")


class TaskOperationRequest(BaseModel):
    operation: str = Field(..., description="Operation type (create, update, delete, get, list)")
    task_data: Optional[Dict[str, Any]] = Field(None, description="Task data for create/update")
    task_id: Optional[str] = Field(None, description="Task ID for update/delete/get")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters for list operation")


class BriefingRequest(BaseModel):
    date: Optional[str] = Field(None, description="Date for briefing (YYYY-MM-DD)")
    delivery_method: str = Field("api", description="Delivery method (api, email, notification)")


class SchedulingRequest(BaseModel):
    tasks: List[Dict[str, Any]] = Field(..., description="Tasks to schedule")
    start_date: Optional[str] = Field(None, description="Start date for scheduling")
    end_date: Optional[str] = Field(None, description="End date for scheduling")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Scheduling constraints")


class DatabaseOperationRequest(BaseModel):
    entity_type: str = Field(..., description="Entity type (task or todo)")
    operation: str = Field(..., description="Operation type (create, update, delete, get, list, bulk_toggle, etc.)")
    data: Optional[Dict[str, Any]] = Field(None, description="Entity data for create/update")
    entity_id: Optional[str] = Field(None, description="Entity ID for update/delete/get")
    entity_ids: Optional[List[str]] = Field(None, description="Entity IDs for bulk operations")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters for list operation")


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_type: str
    status: str
    result: Dict[str, Any]
    execution_time: float
    nodes_executed: int
    completed_at: str


@router.post("/natural-language", response_model=WorkflowResponse)
async def process_natural_language_query(
    request: NaturalLanguageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Process natural language query and route to appropriate workflow
    """
    try:
        # TODO: Get user context and connected accounts from database
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        # Mock connected accounts (TODO: get from database)
        connected_accounts = {
            "google": {"expires_at": "2024-12-31T23:59:59Z"},
            "microsoft": {"expires_at": "2024-12-31T23:59:59Z"}
        }
        
        result = await agent_orchestrator.execute_natural_language_query(
            user_id=current_user.user_id,
            query=request.query,
            user_context=user_context,
            connected_accounts=connected_accounts
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/calendar", response_model=WorkflowResponse)
async def execute_calendar_operation(
    request: CalendarOperationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Execute calendar operations directly
    """
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        connected_accounts = {
            "google": {"expires_at": "2024-12-31T23:59:59Z"},
            "microsoft": {"expires_at": "2024-12-31T23:59:59Z"}
        }
        
        # Prepare operation data
        operation_data = {}
        if request.event_data:
            operation_data["event"] = request.event_data
        if request.event_id:
            operation_data["event_id"] = request.event_id
        
        result = await agent_orchestrator.execute_calendar_operation(
            user_id=current_user.user_id,
            provider=request.provider,
            operation=request.operation,
            operation_data=operation_data,
            user_context=user_context,
            connected_accounts=connected_accounts
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calendar workflow error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/tasks", response_model=WorkflowResponse)
async def execute_task_operation(
    request: TaskOperationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Execute task management operations
    """
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        result = await agent_orchestrator.execute_task_operation(
            user_id=current_user.user_id,
            operation=request.operation,
            task_data=request.task_data,
            task_id=request.task_id,
            user_context=user_context
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task workflow error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/briefing", response_model=WorkflowResponse)
async def generate_daily_briefing(
    request: BriefingRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Generate daily briefing
    """
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        connected_accounts = {
            "gmail": {"expires_at": "2024-12-31T23:59:59Z"},
            "google": {"expires_at": "2024-12-31T23:59:59Z"},
            "microsoft": {"expires_at": "2024-12-31T23:59:59Z"}
        }
        
        result = await agent_orchestrator.generate_daily_briefing(
            user_id=current_user.user_id,
            briefing_date=request.date,
            delivery_method=request.delivery_method,
            user_context=user_context,
            connected_accounts=connected_accounts
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Briefing workflow error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/scheduling", response_model=WorkflowResponse)
async def create_intelligent_schedule(
    request: SchedulingRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Create intelligent schedule
    """
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        connected_accounts = {
            "google": {"expires_at": "2024-12-31T23:59:59Z"},
            "microsoft": {"expires_at": "2024-12-31T23:59:59Z"}
        }
        
        scheduling_request = {
            "tasks": request.tasks,
            "start_date": request.start_date,
            "end_date": request.end_date,
            **(request.constraints or {})
        }
        
        result = await agent_orchestrator.create_intelligent_schedule(
            user_id=current_user.user_id,
            scheduling_request=scheduling_request,
            user_context=user_context,
            connected_accounts=connected_accounts
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scheduling workflow error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/database", response_model=WorkflowResponse)
async def execute_database_operation(
    request: DatabaseOperationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Execute database operations for tasks and todos
    """
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        result = await agent_orchestrator.execute_database_operation(
            user_id=current_user.user_id,
            entity_type=request.entity_type,
            operation=request.operation,
            data=request.data,
            entity_id=request.entity_id,
            entity_ids=request.entity_ids,
            filters=request.filters,
            user_context=user_context
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database workflow error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# Convenience endpoints for specific database operations
@router.post("/todos", response_model=WorkflowResponse)
async def execute_todo_operation(
    request: dict,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Execute todo operations (convenience endpoint)
    """
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        result = await agent_orchestrator.execute_database_operation(
            user_id=current_user.user_id,
            entity_type="todo",
            operation=request.get("operation"),
            data=request.get("data"),
            entity_id=request.get("todo_id"),
            entity_ids=request.get("todo_ids"),
            filters=request.get("filters"),
            user_context=user_context
        )
        
        return WorkflowResponse(**result)
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Todo operation error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Get status of a specific workflow
    """
    status = agent_orchestrator.get_workflow_status(workflow_id)
    
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Check if user owns this workflow
    if status.get("user_id") != current_user.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return status


@router.get("/active")
async def get_active_workflows(
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Get all active workflows for current user
    """
    if current_user.is_admin:
        # Admins can see all workflows
        workflows = agent_orchestrator.get_active_workflows()
    else:
        # Regular users only see their own workflows
        workflows = agent_orchestrator.get_active_workflows(current_user.user_id)
    
    return {
        "active_workflows": workflows,
        "count": len(workflows)
    }


@router.get("/metrics")
async def get_workflow_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Get workflow execution metrics (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    metrics = agent_orchestrator.get_workflow_metrics()
    return metrics


# Frontend compatibility endpoints
@router.post("/query")
async def query_agent(
    request: NaturalLanguageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Process agent query with immediate response + background task execution
    New workflow: Every query gets immediate response, non-chat intents continue with background processing
    """
    import logging
    import time
    import asyncio
    
    logger = logging.getLogger(__name__)
    request_start = time.time()
    
    logger.info(
        f"📨 Agent query request received: '{request.query}'",
        extra={
            "user_id": current_user.user_id,
            "query": request.query,
            "query_length": len(request.query),
            "user_email": current_user.email,
            "event": "agent_query_start"
        }
    )
    print(f"📨 [API REQUEST] User: {current_user.user_id} | Query: '{request.query}' | Length: {len(request.query)}")
    
    try:
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        connected_accounts = {
            "google": {"expires_at": "2024-12-31T23:59:59Z"},
            "microsoft": {"expires_at": "2024-12-31T23:59:59Z"}
        }
        
        # STEP 1: Always get immediate response from LLM (classification + natural response)
        immediate_start = time.time()
        logger.info(
            "Starting immediate response generation",
            extra={
                "user_id": current_user.user_id,
                "query": request.query,
                "event": "immediate_response_start"
            }
        )
        
        from app.agents.graphs.chat_graph import ChatGraph
        chat_workflow = ChatGraph()
        
        # Run just the intent classification to get immediate response
        from app.agents.graphs.base import create_initial_state, WorkflowType
        temp_state = create_initial_state(
            user_id=current_user.user_id,
            workflow_type=WorkflowType.NATURAL_LANGUAGE,
            input_data={"query": request.query},
            user_context=user_context,
            connected_accounts=connected_accounts
        )
        
        # Run intent classification node to get immediate response + classification
        temp_state = await chat_workflow.intent_classifier.execute(temp_state)
        immediate_response = temp_state["input_data"].get("immediate_response", {})
        classified_intent = temp_state["input_data"].get("classified_intent", "unknown")
        immediate_time = time.time() - immediate_start
        
        logger.info(
            "Immediate response generated",
            extra={
                "user_id": current_user.user_id,
                "trace_id": temp_state["trace_id"],
                "intent": classified_intent,
                "response_type": immediate_response.get("conversation_type"),
                "has_task_preview": bool(immediate_response.get("task_preview")),
                "immediate_response_time": immediate_time,
                "event": "immediate_response_complete"
            }
        )
        
        # STEP 2: Branching Logic
        print(f"🔀 [API BRANCHING] Intent: {classified_intent} | Needs LLM: {immediate_response.get('needs_llm', False)}")
        
        if classified_intent == "chat":
            # For chat, either return immediately or continue with LLM processing
            if immediate_response.get("needs_llm"):
                print(f"💬 [CHAT FLOW] Complex chat detected - continuing to full LLM workflow")
                # Continue to full workflow execution for complex chat
                result = await agent_orchestrator.execute_natural_language_query(
                    user_id=current_user.user_id,
                    query=request.query,
                    user_context=user_context,
                    connected_accounts=connected_accounts
                )
                
                result_data = result.get("result", {})
                total_time = time.time() - request_start
                
                return {
                    "success": True,
                    "data": result_data,
                    "message": result_data.get("message") or result_data.get("response", "Task completed successfully"),
                    "conversationId": result.get("workflow_id"),
                    "timestamp": result.get("completed_at"),
                    "type": "chat",
                    "execution": {
                        "workflow_type": "chat",
                        "execution_time": total_time,
                        "nodes_executed": result.get("nodes_executed", 0),
                        "tool_calls": [],
                        "execution_details": result_data.get("execution_details", {})
                    }
                }
            else:
                # Simple chat - return immediately
                print(f"💬 [CHAT FLOW] Simple chat - returning immediate response only")
                total_time = time.time() - request_start
                logger.info(
                    "Simple chat completed immediately",
                    extra={
                        "user_id": current_user.user_id,
                        "trace_id": temp_state["trace_id"],
                        "total_request_time": total_time,
                        "response_type": immediate_response.get("conversation_type"),
                        "event": "simple_chat_complete"
                    }
                )
                
                return {
                    "success": True,
                    "data": immediate_response,
                    "message": immediate_response.get("response", ""),
                    "conversationId": temp_state["trace_id"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "chat",
                    "execution": {
                        "workflow_type": "chat",
                        "execution_time": total_time,
                        "nodes_executed": 1,
                        "tool_calls": [],
                        "execution_details": {
                            "immediate_response": True,
                            "classification": temp_state["input_data"].get("classification_details", {})
                        }
                    }
                }
        
        elif classified_intent in ["task", "todo"]:
            # For task/todo intents: return immediate starting task card, then execute database operations
            print(f"📝 [TASK/TODO FLOW] {classified_intent.title()} intent detected - returning immediate task card")
            task_preview = immediate_response.get("task_preview", {})
            conversation_id = temp_state["trace_id"]
            
            # Start background database execution with WebSocket updates
            async def database_execution():
                from app.core.websocket import websocket_manager
                
                try:
                    print(f"📝 [DATABASE BACKGROUND] Starting database execution for {classified_intent}")
                    print(f"📝 [DATABASE BACKGROUND] Using conversation_id: {conversation_id}")
                    
                    # Emit starting status
                    await websocket_manager.emit_node_update(
                        conversation_id, 
                        f"{classified_intent}_creator", 
                        "executing",
                        {"message": f"Creating {classified_intent}..."}
                    )
                    
                    # Execute database workflow directly
                    # Use the extracted title from the immediate response, fallback to query
                    extracted_title = immediate_response.get("actual_title", request.query)
                    print(f"📝 [DATABASE BACKGROUND] Using extracted title: '{extracted_title}' (from query: '{request.query}')")
                    
                    db_result = await agent_orchestrator.execute_database_operation(
                        user_id=current_user.user_id,
                        entity_type=classified_intent,  # "task" or "todo"
                        operation="create",  # Default to create for new intents
                        data={"title": extracted_title},  # Use extracted title
                        user_context=user_context
                    )
                    
                    print(f"📝 [DATABASE BACKGROUND] {classified_intent.title()} operation completed")
                    print(f"📝 [DATABASE BACKGROUND] Result: {db_result}")
                    
                    # Emit completion status with created item data
                    if db_result and db_result.get("result", {}).get("success"):
                        created_item = db_result.get("result", {}).get("data", {})
                        
                        print(f"📝 [WEBSOCKET DEBUG] About to emit task_created for {classified_intent}")
                        print(f"📝 [WEBSOCKET DEBUG] Conversation ID: {conversation_id}")
                        print(f"📝 [WEBSOCKET DEBUG] Title: {extracted_title}")
                        
                        # Emit task/todo creation success
                        await websocket_manager.emit_task_created(conversation_id, {
                            "type": classified_intent,
                            "title": extracted_title,
                            "created_item": created_item,
                            "success": True,
                            "message": f"{classified_intent.title()} created successfully"
                        })
                        
                        print(f"📝 [WEBSOCKET DEBUG] task_created event emitted successfully")
                        
                        await websocket_manager.emit_node_update(
                            conversation_id, 
                            f"{classified_intent}_creator", 
                            "completed",
                            {
                                "created_item": created_item,
                                "title": extracted_title,
                                "message": f"{classified_intent.title()} '{extracted_title}' created successfully"
                            }
                        )
                    else:
                        await websocket_manager.emit_node_update(
                            conversation_id, 
                            f"{classified_intent}_creator", 
                            "failed",
                            {"error": "Failed to create item in database"}
                        )
                    
                except Exception as e:
                    print(f"❌ [DATABASE BACKGROUND] Database execution failed: {str(e)}")
                    
                    # Emit failure status
                    await websocket_manager.emit_node_update(
                        conversation_id, 
                        f"{classified_intent}_creator", 
                        "failed",
                        {"error": str(e)}
                    )
            
            # Start database operation in background
            asyncio.create_task(database_execution())
            
            # Return immediate task card (database operation happens in background)
            total_time = time.time() - request_start
            
            return {
                "success": True,
                "data": {
                    "response": immediate_response.get("response", f"Starting {classified_intent}..."),
                    "conversation_type": "task_initiated",
                    "task_preview": task_preview,
                    "immediate": True,
                    "actual_title": immediate_response.get("actual_title"),  # Include the extracted title from immediate response
                    "background_processing": True  # Processing in background with WebSocket updates
                },
                "message": immediate_response.get("response", f"Starting {classified_intent}..."),
                "conversationId": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "task",
                "intent": classified_intent,
                "execution": {
                    "workflow_type": classified_intent,
                    "execution_time": total_time,
                    "nodes_executed": 1,
                    "tool_calls": task_preview.get("estimated_tools", []),
                    "execution_details": {
                        "immediate_response": True,
                        "task_preview": task_preview,
                        "background_execution": True
                    }
                }
            }
        
        elif classified_intent == "search":
            # For search intents: return immediate starting task card, then execute search
            print(f"🔍 [SEARCH FLOW] Search intent detected - returning immediate task card")
            task_preview = immediate_response.get("task_preview", {})
            conversation_id = temp_state["trace_id"]
            
            # Start background search execution (non-blocking)
            async def search_execution():
                try:
                    print(f"🔍 [SEARCH BACKGROUND] Starting search execution")
                    print(f"🔍 [SEARCH BACKGROUND] Using conversation_id: {conversation_id}")
                    
                    # Create a new state with the same conversation_id for WebSocket consistency
                    from app.agents.graphs.base import create_initial_state, WorkflowType
                    print(f"🔍 [DEBUG] API - Creating search state with conversation_id: {conversation_id}")
                    search_state = create_initial_state(
                        user_id=current_user.user_id,
                        workflow_type=WorkflowType.SEARCH,
                        input_data={"query": request.query},
                        user_context=user_context,
                        connected_accounts=connected_accounts,
                        trace_id=conversation_id  # Use the same conversation_id for WebSocket consistency
                    )
                    print(f"🔍 [DEBUG] API - Search state created with trace_id: {search_state.get('trace_id')}")
                    
                    # Execute search workflow directly with the correct trace_id
                    from app.agents.graphs.search_graph import SearchGraph
                    search_workflow = SearchGraph()
                    search_result = await search_workflow.execute(search_state)
                    
                    # Extract results from the search workflow state
                    search_data = search_result.get("output_data", {})
                    print(f"🔍 [SEARCH BACKGROUND] Search completed with {len(search_data.get('search_results', []))} results")
                    
                    # Store results in global cache for frontend to retrieve (fallback)
                    _search_results_cache[conversation_id] = {
                        "status": "completed",
                        "search_results": search_data.get("search_results", []),
                        "search_answer": search_data.get("search_answer", ""),
                        "message": search_data.get("message", ""),
                        "follow_up_questions": search_data.get("follow_up_questions", []),
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    print(f"🔍 [SEARCH BACKGROUND] Results stored for conversation {conversation_id}")
                    
                except Exception as e:
                    print(f"❌ [SEARCH BACKGROUND] Search execution failed: {str(e)}")
                    # Store failure status
                    _search_results_cache[conversation_id] = {
                        "status": "failed",
                        "error": str(e),
                        "completed_at": datetime.utcnow().isoformat()
                    }
            
            # Start search in background
            asyncio.create_task(search_execution())
            
            # Return immediate starting task card
            total_time = time.time() - request_start
            return {
                "success": True,
                "data": {
                    "response": immediate_response.get("response", "Starting search..."),
                    "conversation_type": "task_initiated",
                    "task_preview": task_preview,
                    "immediate": True,
                    "background_processing": True
                },
                "message": immediate_response.get("response", "Starting search..."),
                "conversationId": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "task",
                "intent": classified_intent,
                "execution": {
                    "workflow_type": classified_intent,
                    "execution_time": total_time,
                    "nodes_executed": 1,
                    "tool_calls": task_preview.get("estimated_tools", []),
                    "execution_details": {
                        "immediate_response": True,
                        "task_preview": task_preview,
                        "background_execution": True
                    }
                }
            }
        
        else:
            # For other non-chat intents: return immediate response + task preview + start background processing
            print(f"🔧 [TASK FLOW] Non-chat intent detected - starting background processing")
            task_preview = immediate_response.get("task_preview", {})
            total_time = time.time() - request_start
            
            # Start background workflow execution (fire and forget) with consistent trace_id
            conversation_id = temp_state["trace_id"]
            async def background_execution():
                try:
                    print(f"🚀 [BACKGROUND] Starting background workflow execution for {classified_intent}")
                    print(f"🚀 [BACKGROUND] Using conversation_id: {conversation_id}")
                    await agent_orchestrator.execute_natural_language_query(
                        user_id=current_user.user_id,
                        query=request.query,
                        user_context=user_context,
                        connected_accounts=connected_accounts,
                        trace_id=conversation_id  # Use the same conversation_id for WebSocket consistency
                    )
                    print(f"🚀 [BACKGROUND] Background workflow completed for {classified_intent}")
                except Exception as e:
                    print(f"❌ [BACKGROUND] Background workflow failed: {str(e)}")
            
            # Start background task (non-blocking)
            asyncio.create_task(background_execution())
            
            # Return immediate response with task preview
            return {
                "success": True,
                "data": {
                    "response": immediate_response.get("response", "Task started"),
                    "conversation_type": immediate_response.get("conversation_type", "task_initiated"),
                    "task_preview": task_preview,
                    "immediate": True,
                    "background_processing": True
                },
                "message": immediate_response.get("response", "Task started"),
                "conversationId": temp_state["trace_id"],
                "timestamp": datetime.utcnow().isoformat(),
                "type": "task",
                "intent": classified_intent,
                "execution": {
                    "workflow_type": classified_intent,
                    "execution_time": total_time,
                    "nodes_executed": 1,
                    "tool_calls": task_preview.get("estimated_tools", []),
                    "execution_details": {
                        "immediate_response": True,
                        "task_preview": task_preview,
                        "background_execution": True
                    }
                }
            }
        
    except AgentError as e:
        total_time = time.time() - request_start
        logger.error(
            "Agent error in query endpoint",
            extra={
                "user_id": current_user.user_id,
                "query": request.query,
                "error_message": e.message,
                "error_context": getattr(e, 'context', {}),
                "total_request_time": total_time,
                "event": "agent_query_error"
            }
        )
        return {
            "success": False,
            "error": f"Agent error: {e.message}"
        }
    except Exception as e:
        total_time = time.time() - request_start
        logger.error(
            "Internal server error in query endpoint",
            extra={
                "user_id": current_user.user_id,
                "query": request.query,
                "error_message": str(e),
                "error_type": type(e).__name__,
                "total_request_time": total_time,
                "event": "agent_query_internal_error"
            },
            exc_info=True
        )
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }


@router.post("/chat")
async def chat_with_agent(
    request: dict,
    current_user: CurrentUser = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Chat with agent (frontend compatibility endpoint)
    """
    try:
        message = request.get("message", "")
        conversation_id = request.get("conversationId")
        context = request.get("context", {})
        
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "permissions": {"can_execute_workflows": True}
        }
        
        connected_accounts = {
            "google": {"expires_at": "2024-12-31T23:59:59Z"},
            "microsoft": {"expires_at": "2024-12-31T23:59:59Z"}
        }
        
        # Use natural language query for chat messages
        result = await agent_orchestrator.execute_natural_language_query(
            user_id=current_user.user_id,
            query=message,
            user_context={**user_context, **context},
            connected_accounts=connected_accounts
        )
        
        result_data = result.get("result", {})
        
        return {
            "success": True,
            "data": result_data,
            "message": result_data.get("message") or result_data.get("response", "Task completed successfully"),
            "conversationId": result.get("workflow_id"),
            "timestamp": result.get("completed_at"),
            "execution": {
                "workflow_type": result.get("workflow_type"),
                "execution_time": result.get("execution_time", 0),
                "nodes_executed": result.get("nodes_executed", 0),
                "tool_calls": result_data.get("tool_calls", []),
                "execution_details": result_data.get("execution_details", {})
            }
        }
        
    except AgentError as e:
        return {
            "success": False,
            "error": f"Agent error: {e.message}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }


# Global cache for search results (in production, use Redis)
_search_results_cache = {}


@router.get("/search-results/{conversation_id}")
async def get_search_results(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get search results for a conversation ID"""
    try:
        # Check if results are available
        if conversation_id in _search_results_cache:
            results = _search_results_cache[conversation_id]
            print(f"🔍 [SEARCH RESULTS] Retrieved results for conversation {conversation_id}")
            return {
                "success": True,
                "data": results
            }
        else:
            # Results not ready yet
            return {
                "success": True,
                "data": {
                    "status": "pending",
                    "message": "Search still in progress"
                }
            }
    except Exception as e:
        logger.error(f"Error retrieving search results: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving search results")


@router.get("/health")
async def agent_health():
    """
    Agent health check endpoint
    """
    return {"healthy": True, "status": "running"}