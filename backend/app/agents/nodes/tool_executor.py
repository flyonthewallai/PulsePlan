"""
Tool executor node for LangGraph workflows
Provides a standardized way to execute tools within workflow nodes
"""
from typing import Dict, Any, Type
from datetime import datetime

from ..base import WorkflowState, WorkflowError
from ...tools.base import BaseTool, ToolError, ToolResult
from ...tools.calendar import GoogleCalendarTool, MicrosoftCalendarTool
from ...tools.tasks import TaskCRUDTool, TaskSchedulingTool
from ...tools.email import EmailManagerTool, GmailUserTool, OutlookUserTool, SystemEmailTool
from ...tools.briefing import DataAggregatorTool, ContentSynthesizerTool


class ToolExecutorNode:
    """
    Node that executes tools in LangGraph workflows
    Provides tool registration, execution, and error handling
    """
    
    def __init__(self):
        # Register available tools
        self.tools: Dict[str, BaseTool] = {
            # Calendar tools
            "google_calendar": GoogleCalendarTool(),
            "microsoft_calendar": MicrosoftCalendarTool(),
            
            # Task tools
            "task_crud": TaskCRUDTool(),
            "task_scheduling": TaskSchedulingTool(),
            
            # Email tools
            "email_manager": EmailManagerTool(),
            "gmail_user": GmailUserTool(),
            "outlook_user": OutlookUserTool(),
            "system_email": SystemEmailTool(),
            
            # Briefing tools
            "data_aggregator": DataAggregatorTool(),
            "content_synthesizer": ContentSynthesizerTool(),
        }
    
    async def execute_tool(self, state: WorkflowState, tool_name: str, tool_input: Dict[str, Any]) -> WorkflowState:
        """
        Execute a specific tool and update workflow state
        
        Args:
            state: Current workflow state
            tool_name: Name of tool to execute
            tool_input: Input data for the tool
            
        Returns:
            Updated workflow state with tool results
        """
        state["current_node"] = f"tool_executor_{tool_name}"
        state["visited_nodes"].append(f"tool_executor_{tool_name}")
        
        try:
            # Get tool instance
            tool = self.tools.get(tool_name)
            if not tool:
                raise WorkflowError(
                    f"Unknown tool: {tool_name}",
                    {"available_tools": list(self.tools.keys())}
                )
            
            # Prepare execution context
            context = {
                "user_id": state["user_id"],
                "connected_accounts": state.get("connected_accounts", {}),
                "user_context": state.get("user_context", {}),
                "request_id": state["request_id"],
                "trace_id": state["trace_id"]
            }
            
            # Check tool health
            if not await tool.health_check(context):
                raise WorkflowError(
                    f"Tool {tool_name} failed health check",
                    {"tool_name": tool_name, "required_tokens": tool.get_required_tokens()}
                )
            
            # Execute tool
            result = await tool.execute(tool_input, context)
            
            # Update state with results
            if result.success:
                state["output_data"] = result.to_dict()
                
                # Add structured tool execution data for frontend
                if "tool_executions" not in state:
                    state["tool_executions"] = []
                    
                tool_execution_data = {
                    "id": f"{tool_name}_{datetime.utcnow().timestamp()}",
                    "name": tool_name,
                    "description": f"Executed {tool.name}: {tool.description[:100]}",
                    "parameters": tool_input,
                    "status": "completed",
                    "result": result.data if hasattr(result, 'data') else str(result),
                    "execution_time": result.execution_time if hasattr(result, 'execution_time') else None,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                state["tool_executions"].append(tool_execution_data)
                
                # Add tool execution metadata
                state["metrics"][f"tool_{tool_name}"] = {
                    "success": True,
                    "execution_time": result.execution_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Handle tool failure
                error_context = {
                    "tool_name": tool_name,
                    "error": result.error,
                    "input_data": tool_input
                }
                
                # Check if error is recoverable
                if isinstance(result.error, str) and "recoverable" in result.error.lower():
                    raise WorkflowError(result.error, error_context, recoverable=True)
                else:
                    raise WorkflowError(result.error, error_context, recoverable=False)
            
            return state
            
        except ToolError as e:
            # Handle tool-specific errors
            error_context = {
                "tool_name": tool_name,
                "tool_error": e.message,
                "recoverable": e.recoverable,
                "context": e.context
            }
            
            state["error"] = error_context
            state["metrics"][f"tool_{tool_name}"] = {
                "success": False,
                "error": e.message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            raise WorkflowError(f"Tool execution failed: {e.message}", error_context, e.recoverable)
        
        except Exception as e:
            # Handle unexpected errors
            error_context = {
                "tool_name": tool_name,
                "unexpected_error": str(e),
                "input_data": tool_input
            }
            
            state["error"] = error_context
            state["metrics"][f"tool_{tool_name}"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            raise WorkflowError(f"Unexpected tool error: {str(e)}", error_context, recoverable=False)
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools and their descriptions"""
        return {name: tool.description for name, tool in self.tools.items()}
    
    def get_tool_requirements(self, tool_name: str) -> Dict[str, Any]:
        """Get requirements for a specific tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {}
        
        return {
            "name": tool.name,
            "description": tool.description,
            "required_permissions": tool.get_required_permissions(),
            "required_tokens": tool.get_required_tokens()
        }
    
    def generate_task_response(self, state: WorkflowState, task_description: str) -> Dict[str, Any]:
        """
        Generate a structured response for the frontend that includes
        the task description and tool calls information
        
        Args:
            state: Current workflow state with tool executions
            task_description: Human-readable description of the task
            
        Returns:
            Structured response with task and tool calls data
        """
        tool_executions = state.get("tool_executions", [])
        
        # Determine overall task status
        task_status = "completed"
        if any(execution.get("status") == "failed" for execution in tool_executions):
            task_status = "partially_completed"
        elif any(execution.get("status") == "executing" for execution in tool_executions):
            task_status = "executing"
        elif any(execution.get("status") == "pending" for execution in tool_executions):
            task_status = "pending"
        
        # Generate response text based on task status
        if task_status == "completed":
            response_text = f"I've successfully completed the task: {task_description}"
        elif task_status == "partially_completed":
            response_text = f"I've partially completed the task: {task_description}. Some steps encountered issues."
        elif task_status == "executing":
            response_text = f"I'm currently working on: {task_description}"
        else:
            response_text = f"I've planned the task: {task_description}. Ready to execute when you're ready."
        
        return {
            "success": True,
            "data": {
                "response": response_text,
                "task": task_description,
                "toolCalls": tool_executions,
                "status": task_status,
                "summary": f"Task involves {len(tool_executions)} tool operations"
            }
        }


# Global tool executor instance
tool_executor = ToolExecutorNode()