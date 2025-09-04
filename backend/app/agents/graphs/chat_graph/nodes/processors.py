"""
Processor Nodes
Handles result processing, clarification generation, and final workflow steps
"""
import logging
from datetime import datetime
from typing import Dict, Any

from ..base import WorkflowState, WorkflowError
from ..services.response_service import ResponseGenerationService
from ..utils.websocket_helpers import WebSocketHelper


class ProcessorNodes:
    """Collection of processor nodes for workflow finalization"""
    
    def __init__(self):
        self.response_service = ResponseGenerationService()
        self.websocket_helper = WebSocketHelper()
        self.logger = logging.getLogger(__name__)
    
    async def clarification_generator_node(self, state: WorkflowState) -> WorkflowState:
        """Generate LLM-powered clarification for ambiguous or unknown intents"""
        state["current_node"] = "clarification_generator"
        state["visited_nodes"].append("clarification_generator")
        
        user_query = state["input_data"]["query"]
        intent = state["input_data"]["classified_intent"]
        
        if intent == "ambiguous" and state["input_data"].get("needs_clarification"):
            # Handle ambiguous cases with LLM-generated clarification
            clarification_context = state["input_data"]["clarification_context"]
            clarification_response = self.response_service.generate_llm_clarification(
                user_query, 
                "ambiguous", 
                clarification_context
            )
        else:
            # Handle completely unknown intents with LLM
            clarification_response = self.response_service.generate_llm_clarification(
                user_query, 
                "unknown"
            )
        
        state["output_data"] = clarification_response
        
        # Log clarification request for improvement
        self.logger.info(
            "LLM clarification generated",
            extra={
                "user_id": state["user_id"],
                "query": user_query,
                "clarification_type": clarification_response["clarification_type"],
                "confidence": state["input_data"].get("confidence", 0.0),
                "llm_reasoning": clarification_response.get("llm_reasoning", "No reasoning available")
            }
        )
        
        return state
    
    async def result_processor_node(self, state: WorkflowState) -> WorkflowState:
        """Format and validate outputs with WebSocket emission"""
        state["current_node"] = "result_processor"
        state["visited_nodes"].append("result_processor")
        
        # Ensure output_data exists
        if not state.get("output_data"):
            state["output_data"] = {}
            
        # Add metadata
        state["output_data"]["metadata"] = {
            "workflow_type": state["workflow_type"],
            "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
            "nodes_visited": len(state["visited_nodes"])
        }
        
        # Emit WebSocket completion event
        workflow_id = state.get("trace_id")
        if workflow_id:
            await self.websocket_helper.emit_workflow_completion(workflow_id, state.get("output_data"))
        
        return state
    
    async def trace_updater_node(self, state: WorkflowState) -> WorkflowState:
        """Store execution trace for transparency and debugging"""
        state["current_node"] = "trace_updater"
        state["visited_nodes"].append("trace_updater")
        
        try:
            # Create decision trace
            decision_trace = {
                "workflow_type": "natural_language",
                "user_id": state["user_id"],
                "trace_id": state["trace_id"],
                "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
                "nodes_visited": state["visited_nodes"],
                "decisions": {
                    "classified_intent": state["input_data"].get("classified_intent"),
                    "confidence": state["input_data"].get("confidence"),
                    "reasoning": state["input_data"].get("classification_details", {}).get("reasoning"),
                    "needs_clarification": state["input_data"].get("needs_clarification", False),
                    "conversation_type": state["input_data"].get("immediate_response", {}).get("conversation_type"),
                    "has_task_preview": bool(state["input_data"].get("immediate_response", {}).get("task_preview"))
                },
                "success": state.get("error") is None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store trace (TODO: implement actual storage)
            print(f"📋 [CHAT TRACE] {decision_trace}")
            
            # Add to metrics
            state["metrics"]["decision_trace"] = decision_trace
            
            return state
            
        except Exception as e:
            print(f"❌ [TRACE] Failed to update trace: {str(e)}")
            return state
    
    async def error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle ChatGraph workflow specific errors"""
        state["current_node"] = "error_handler"
        state["visited_nodes"].append("error_handler")
        
        workflow_id = state.get("trace_id")
        await self.websocket_helper.emit_node_status(workflow_id, "error_handler", "executing")
        
        try:
            error = state.get("error")
            if error and error.get("recoverable") and state["retry_count"] < 3:
                # Retry recoverable errors
                state["retry_count"] += 1
                state["metrics"]["retry_attempt"] = state["retry_count"]
                await self.websocket_helper.emit_node_status(workflow_id, "error_handler", "retrying", {
                    "retry_count": state["retry_count"]
                })
                return state
            else:
                # Fail gracefully with chat-specific error handling
                error_message = "Natural language workflow failed"
                if error:
                    error_message = f"Natural language workflow failed: {error.get('message', str(error))}"
                
                state["output_data"] = {
                    "workflow_type": "chat",
                    "error": error_message,
                    "recoverable": False,
                    "context": error,
                    "message": "I encountered an error while processing your request. Please try rephrasing your question or contact support if the issue persists.",
                    "helpful_actions": [
                        {"action": "chat", "description": "Try rephrasing your request", "example_query": "Can you help me with..."},
                        {"action": "calendar", "description": "Schedule something specific", "example_query": "Schedule a meeting tomorrow"},
                        {"action": "task", "description": "Create a task", "example_query": "Add finish report to my tasks"}
                    ]
                }
                
                await self.websocket_helper.emit_node_status(workflow_id, "error_handler", "completed", {
                    "error": error_message
                })
                
                return state
                
        except Exception as e:
            # Fallback error handling
            state["output_data"] = {
                "workflow_type": "chat",
                "error": f"Critical error in error handler: {str(e)}",
                "recoverable": False,
                "message": "A critical error occurred. Please try again later."
            }
            return state