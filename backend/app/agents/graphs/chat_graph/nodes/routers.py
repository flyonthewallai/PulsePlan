"""
Router Nodes
Handles routing to specialized workflows and database operations
"""
from typing import Dict, Any
from datetime import datetime

from ..base import WorkflowState, WorkflowError
from ..utils.websocket_helpers import WebSocketHelper


class RouterNodes:
    """Collection of router nodes for different workflow types"""
    
    def __init__(self):
        self.websocket_helper = WebSocketHelper()
    
    # ============================================================================
    # Router Decision Functions
    # ============================================================================
    
    def intent_router(self, state: WorkflowState) -> str:
        """Route based on classified intent with ambiguity handling"""
        intent = state["input_data"].get("classified_intent")
        query = state["input_data"].get("query", "")
        
        if intent in ["calendar", "task", "briefing", "scheduling", "email", "canvas", "search", "chat"]:
            print(f"🚀 [ROUTING] Query: '{query}' -> Intent: {intent} -> Route: {intent}_router")
            return intent
        elif intent == "ambiguous":
            print(f"❓ [ROUTING] Query: '{query}' -> Intent: {intent} -> Route: clarification_generator")
            return "ambiguous"
        else:
            print(f"❓ [ROUTING] Query: '{query}' -> Intent: {intent} -> Route: clarification_generator (unknown)")
            return "unknown"
    
    def workflow_router(self, state: WorkflowState) -> str:
        """Route to appropriate workflow after policy/rate checks"""
        return state["input_data"]["classified_intent"]
    
    # ============================================================================
    # Specialized Workflow Router Nodes
    # ============================================================================
    
    async def calendar_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to calendar workflow"""
        state["current_node"] = "calendar_router"
        state["visited_nodes"].append("calendar_router")
        
        query = state["input_data"]["query"]
        workflow_id = state.get("trace_id")
        print(f"📅 [CALENDAR ROUTER] Executing calendar workflow for: '{query}'")
        
        # Emit WebSocket node update
        await self.websocket_helper.emit_node_status(workflow_id, "calendar_router", "executing")
        
        # TODO: Execute calendar workflow
        # For now, mock response
        state["output_data"] = {
            "workflow_type": "calendar",
            "message": "Calendar workflow executed",
            "query": query,
            "intent": state["input_data"]["classified_intent"]
        }
        
        # Emit completion event
        await self.websocket_helper.emit_node_status(workflow_id, "calendar_router", "completed")
        
        print(f"📅 [CALENDAR ROUTER] Calendar workflow completed")
        return state
    
    async def task_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to complex task workflow"""
        state["current_node"] = "task_router"
        state["visited_nodes"].append("task_router")
        
        try:
            # Execute database workflow for tasks
            from ....orchestrator import get_agent_orchestrator
            
            orchestrator = get_agent_orchestrator()
            user_id = state["user_id"]
            query = state["input_data"]["query"]
            
            # Get the actual title from the immediate response (LLM already extracted it)
            immediate_response = state["input_data"].get("immediate_response", {})
            task_title = immediate_response.get("actual_title", query)
            
            print(f"📋 [TASK ROUTER] Query: '{query}' -> Extracted title: '{task_title}'")
            
            # Execute database operation to create task
            result = await orchestrator.execute_database_operation(
                user_id=user_id,
                entity_type="task",
                operation="create",
                data={"title": task_title},
                user_context=state.get("user_context", {})
            )
            
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "task",
                "message": "Complex task created successfully", 
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "result": result.get("result", {})
            }
            
            # Emit task_created WebSocket event
            workflow_id = state.get("trace_id")
            await self.websocket_helper.emit_task_created(workflow_id, {
                "type": "task",
                "title": task_title,
                "created_item": result.get("result", {}),
                "success": True,
                "message": "Complex task created successfully"
            })
            
        except Exception as e:
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "task",
                "message": f"Task creation failed: {str(e)}", 
                "query": state["input_data"]["query"],
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def todo_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to simple todo workflow"""
        state["current_node"] = "todo_router"
        state["visited_nodes"].append("todo_router")
        
        try:
            # Execute database workflow for todos
            from ....orchestrator import get_agent_orchestrator
            
            orchestrator = get_agent_orchestrator()
            user_id = state["user_id"]
            query = state["input_data"]["query"]
            
            # Get the actual title from the immediate response (LLM already extracted it)
            immediate_response = state["input_data"].get("immediate_response", {})
            todo_title = immediate_response.get("actual_title", query)
            
            print(f"📝 [TODO ROUTER] Query: '{query}' -> Extracted title: '{todo_title}'")
            
            # Execute database operation to create todo
            result = await orchestrator.execute_database_operation(
                user_id=user_id,
                entity_type="todo",
                operation="create",
                data={"title": todo_title},
                user_context=state.get("user_context", {})
            )
            
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "todo",
                "message": "Simple todo created successfully", 
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "result": result.get("result", {})
            }
            
            # Emit task_created WebSocket event
            workflow_id = state.get("trace_id")
            await self.websocket_helper.emit_task_created(workflow_id, {
                "type": "todo",
                "title": todo_title,
                "created_item": result.get("result", {}),
                "success": True,
                "message": "Simple todo created successfully"
            })
            
        except Exception as e:
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "todo",
                "message": f"Todo creation failed: {str(e)}", 
                "query": state["input_data"]["query"],
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def briefing_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to briefing workflow"""
        state["current_node"] = "briefing_router"
        state["visited_nodes"].append("briefing_router")
        
        query = state["input_data"]["query"]
        workflow_id = state.get("trace_id")
        print(f"📊 [BRIEFING ROUTER] Executing briefing workflow for: '{query}'")
        
        # Emit WebSocket node update
        await self.websocket_helper.emit_node_status(workflow_id, "briefing_router", "executing")
        
        # TODO: Execute briefing workflow
        # For now, mock response
        state["output_data"] = {
            "workflow_type": "briefing",
            "message": "Briefing workflow executed",
            "query": query,
            "intent": state["input_data"]["classified_intent"]
        }
        
        # Emit completion event
        await self.websocket_helper.emit_node_status(workflow_id, "briefing_router", "completed")
        
        print(f"📊 [BRIEFING ROUTER] Briefing workflow completed")
        return state
    
    async def scheduling_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to scheduling workflow"""
        state["current_node"] = "scheduling_router"
        state["visited_nodes"].append("scheduling_router")
        
        query = state["input_data"]["query"]
        workflow_id = state.get("trace_id")
        print(f"⏰ [SCHEDULING ROUTER] Executing scheduling workflow for: '{query}'")
        
        # Emit WebSocket node update
        await self.websocket_helper.emit_node_status(workflow_id, "scheduling_router", "executing")
        
        # TODO: Execute scheduling workflow
        # For now, mock response
        state["output_data"] = {
            "workflow_type": "scheduling",
            "message": "Scheduling workflow executed",
            "query": query,
            "intent": state["input_data"]["classified_intent"]
        }
        
        # Emit completion event
        await self.websocket_helper.emit_node_status(workflow_id, "scheduling_router", "completed")
        
        print(f"⏰ [SCHEDULING ROUTER] Scheduling workflow completed")
        return state
    
    async def email_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to dedicated EmailGraph workflow"""
        state["current_node"] = "email_router"
        state["visited_nodes"].append("email_router")
        
        query = state["input_data"]["query"]
        user_id = state.get("user_id", "unknown")
        print(f"📧 [EMAIL ROUTER] Routing to EmailGraph for: '{query}'")
        
        try:
            # Import and execute EmailGraph
            from ...email_graph import EmailGraph
            from ...base import create_initial_state, WorkflowType
            import re
            
            # Extract email count limit from query
            def extract_email_limit(query: str) -> int:
                """Extract number limit from natural language query"""
                query_lower = query.lower()
                
                # Look for numbers in the query
                numbers = re.findall(r'\d+', query)
                if numbers:
                    try:
                        return min(int(numbers[0]), 50)  # Cap at 50 for performance
                    except (ValueError, IndexError):
                        pass
                
                # Default limits based on context
                if "recent" in query_lower or "latest" in query_lower:
                    return 10
                
                return 20  # Default
            
            limit = extract_email_limit(query)
            print(f"📧 [EMAIL ROUTER] Extracted limit: {limit} from query: '{query}'")
            
            # Create email workflow state
            email_state = create_initial_state(
                user_id=user_id,
                workflow_type=WorkflowType.EMAIL,
                input_data={"query": query, "limit": limit},
                user_context=state.get("user_context", {}),
                connected_accounts=state.get("connected_accounts", {}),
                trace_id=state.get("trace_id")  # Preserve original trace_id for WebSocket consistency
            )
            
            # Execute EmailGraph workflow
            email_graph = EmailGraph()
            email_result_state = await email_graph.execute(email_state)
            
            # Extract results from EmailGraph
            if email_result_state.get("output_data"):
                state["output_data"] = email_result_state["output_data"]
                state["output_data"]["intent"] = state["input_data"]["classified_intent"]
                print(f"📧 [EMAIL ROUTER] EmailGraph completed successfully")
            else:
                # Handle case where EmailGraph didn't produce output
                state["output_data"] = {
                    "workflow_type": "email",
                    "message": f"I encountered an issue while processing the email request '{query}'. Please try again.",
                    "query": query,
                    "intent": state["input_data"]["classified_intent"],
                    "error": "EmailGraph did not produce output"
                }
                print(f"❌ [EMAIL ROUTER] EmailGraph did not produce output")
            
        except Exception as e:
            print(f"❌ [EMAIL ROUTER] Exception during EmailGraph execution: {str(e)}")
            state["output_data"] = {
                "workflow_type": "email", 
                "message": f"I encountered an unexpected error while processing the email request '{query}'. Please try again.",
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def canvas_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to Canvas LMS integration"""
        state["current_node"] = "canvas_router"
        state["visited_nodes"].append("canvas_router")
        
        query = state["input_data"]["query"]
        user_id = state.get("user_id", "unknown")
        workflow_id = state.get("trace_id")
        print(f"📚 [CANVAS ROUTER] Executing Canvas workflow for: '{query}'")
        
        try:
            # Import Canvas tool directly
            from app.agents.tools.canvas import canvas_lms_tool
            
            # Determine Canvas operation from query
            query_lower = query.lower()
            operation = "sync_canvas_data"  # Default operation
            
            if "upcoming" in query_lower or "assignments" in query_lower:
                operation = "get_upcoming_assignments"
            elif "sync" in query_lower or "update" in query_lower or "refresh" in query_lower:
                operation = "sync_canvas_data"
            elif "force" in query_lower:
                operation = "force_sync"
            
            print(f"📚 [CANVAS ROUTER] Determined operation: {operation}")
            
            # Execute Canvas tool
            input_data = {"operation": operation}
            context = {
                "user_id": user_id,
                "canvas_config": state.get("connected_accounts", {}).get("canvas", {}),
                "user_context": state.get("user_context", {})
            }
            
            # Emit WebSocket node update
            from ..utils.websocket_helpers import WebSocketHelper
            websocket_helper = WebSocketHelper()
            await websocket_helper.emit_node_status(workflow_id, "canvas_router", "executing")
            
            canvas_result = await canvas_lms_tool.execute(input_data, context)
            
            if canvas_result.success:
                state["output_data"] = {
                    "workflow_type": "canvas",
                    "message": f"Canvas operation '{operation}' completed successfully",
                    "query": query,
                    "intent": state["input_data"]["classified_intent"],
                    "canvas_data": canvas_result.data,
                    "operation": operation,
                    "execution_time": canvas_result.execution_time,
                    "metadata": canvas_result.metadata
                }
                print(f"📚 [CANVAS ROUTER] Canvas operation completed successfully")
            else:
                state["output_data"] = {
                    "workflow_type": "canvas",
                    "message": f"Canvas operation failed: {canvas_result.error}",
                    "query": query,
                    "intent": state["input_data"]["classified_intent"],
                    "error": canvas_result.error,
                    "operation": operation
                }
                print(f"❌ [CANVAS ROUTER] Canvas operation failed: {canvas_result.error}")
            
            # Emit completion event
            await websocket_helper.emit_node_status(workflow_id, "canvas_router", "completed")
            
        except Exception as e:
            print(f"❌ [CANVAS ROUTER] Exception during Canvas execution: {str(e)}")
            state["output_data"] = {
                "workflow_type": "canvas", 
                "message": f"I encountered an unexpected error while processing the Canvas request '{query}'. Please try again.",
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def search_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to dedicated SearchGraph workflow"""
        state["current_node"] = "search_router"
        state["visited_nodes"].append("search_router")
        
        query = state["input_data"]["query"]
        user_id = state.get("user_id", "unknown")
        print(f"🔍 [SEARCH ROUTER] Routing to SearchGraph for: '{query}'")
        
        try:
            # Import and execute SearchGraph
            from ...search_graph import SearchGraph
            from ...base import create_initial_state, WorkflowType
            
            # Create search workflow state
            search_state = create_initial_state(
                user_id=user_id,
                workflow_type=WorkflowType.SEARCH,
                input_data={"query": query},
                user_context=state.get("user_context", {}),
                connected_accounts=state.get("connected_accounts", {}),
                trace_id=state.get("trace_id")  # Preserve original trace_id for WebSocket consistency
            )
            
            # Execute SearchGraph workflow
            search_graph = SearchGraph()
            search_result_state = await search_graph.execute(search_state)
            
            # Extract results from SearchGraph
            if search_result_state.get("output_data"):
                state["output_data"] = search_result_state["output_data"]
                state["output_data"]["intent"] = state["input_data"]["classified_intent"]
                print(f"🔍 [SEARCH ROUTER] SearchGraph completed successfully")
            else:
                # Handle case where SearchGraph didn't produce output
                state["output_data"] = {
                    "workflow_type": "search",
                    "message": f"I encountered an issue while processing the search for '{query}'. Please try again.",
                    "search_results": [],
                    "query": query,
                    "intent": state["input_data"]["classified_intent"],
                    "error": "SearchGraph did not produce output"
                }
                print(f"❌ [SEARCH ROUTER] SearchGraph did not produce output")
            
        except Exception as e:
            print(f"❌ [SEARCH ROUTER] Exception during SearchGraph execution: {str(e)}")
            state["output_data"] = {
                "workflow_type": "search", 
                "message": f"I encountered an unexpected error while searching for '{query}'. Please try again.",
                "search_results": [],
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def chat_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to LLM-powered chat workflow"""
        state["current_node"] = "chat_router"
        state["visited_nodes"].append("chat_router")
        
        user_query = state["input_data"]["query"]
        
        # Import response service for chat generation
        from ..services.response_service import ResponseGenerationService
        response_service = ResponseGenerationService()
        
        # Generate response - use lightweight LLM for natural chat
        classification = state["input_data"].get("classification_details", {})
        immediate_response = state["input_data"].get("immediate_response", {})
        
        # Generate full LLM response for complex chat/help queries
        chat_response = response_service.generate_llm_chat_response(user_query, state.get("user_context", {}))
        
        state["output_data"] = {
            "workflow_type": "chat",
            "message": chat_response["response"],  # Main response message
            "response": chat_response["response"],  # Keep for compatibility
            "conversation_type": chat_response["conversation_type"],
            "helpful_actions": chat_response.get("helpful_actions", []),
            "follow_up_questions": chat_response.get("follow_up_questions", []),
            "query": user_query,
            "intent": state["input_data"]["classified_intent"],
            "tool_calls": [],  # No tool calls for simple chat
            "execution_details": {
                "nodes_visited": state.get("visited_nodes", []),
                "classification": {
                    "intent": state["input_data"]["classified_intent"],
                    "confidence": state["input_data"].get("confidence", 0.0),
                    "reasoning": state["input_data"].get("classification_details", {}).get("reasoning", "")
                },
                "llm_reasoning": chat_response.get("reasoning", "")
            }
        }
        
        return state