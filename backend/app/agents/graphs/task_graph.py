"""
Task Management Workflow
Implements task CRUD operations with intelligent scheduling
Based on LANGGRAPH_AGENT_WORKFLOWS.md
"""
from typing import Dict, List, Any
from datetime import datetime
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError


class TaskGraph(BaseWorkflow):
    """
    Task Management Workflow that:
    1. Detects task operation type (create/update/delete/list)
    2. Validates task data and permissions
    3. Executes database operations
    4. Recalculates intelligent scheduling
    5. Sends notifications
    """
    
    def __init__(self):
        super().__init__(WorkflowType.TASK)
        
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for task workflow"""
        return {
            "input_validator": self.input_validator_node,
            "task_type_detector": self.task_type_detector_node,
            "validation_gate": self.validation_gate_node,
            "policy_gate": self.policy_gate_node,
            "rate_limiter": self.rate_limiter_node,
            "idempotency_checker": self.idempotency_checker_node,
            "database_executor": self.database_executor_node,
            "schedule_recalculator": self.schedule_recalculator_node,
            "notification_service": self.notification_service_node,
            "result_processor": self.result_processor_node,
            "trace_updater": self.trace_updater_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # Initial processing
            ("input_validator", "task_type_detector"),
            ("task_type_detector", "validation_gate"),
            ("validation_gate", "policy_gate"),
            
            # Standard workflow checks
            ("policy_gate", "rate_limiter"),
            ("rate_limiter", "idempotency_checker"),
            
            # Core execution
            ("idempotency_checker", "database_executor"),
            ("database_executor", "schedule_recalculator"),
            ("schedule_recalculator", "notification_service"),
            
            # Final processing
            ("notification_service", "result_processor"),
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    def task_type_detector_node(self, state: WorkflowState) -> WorkflowState:
        """Determine task operation type"""
        state["current_node"] = "task_type_detector"
        state["visited_nodes"].append("task_type_detector")
        
        # Get operation from input data
        operation = state["input_data"].get("operation")
        
        # If not explicitly provided, try to infer from data
        if not operation:
            if state["input_data"].get("task_id"):
                if state["input_data"].get("delete", False):
                    operation = "delete"
                elif state["input_data"].get("task_data"):
                    operation = "update"
                else:
                    operation = "get"
            elif state["input_data"].get("task_data"):
                operation = "create"
            else:
                operation = "list"
        
        # Validate operation
        valid_operations = ["create", "update", "delete", "get", "list"]
        if operation not in valid_operations:
            raise WorkflowError(
                f"Invalid task operation: {operation}",
                {"valid_operations": valid_operations}
            )
        
        state["input_data"]["detected_operation"] = operation
        
        return state
    
    def validation_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Validate task data and permissions"""
        state["current_node"] = "validation_gate"
        state["visited_nodes"].append("validation_gate")
        
        operation = state["input_data"]["detected_operation"]
        
        # Validate based on operation type
        if operation == "create":
            self._validate_create_data(state)
        elif operation == "update":
            self._validate_update_data(state)
        elif operation == "delete":
            self._validate_delete_data(state)
        elif operation == "get":
            self._validate_get_data(state)
        # list operation requires no additional validation
        
        return state
    
    def _validate_create_data(self, state: WorkflowState):
        """Validate data for task creation"""
        task_data = state["input_data"].get("task_data", {})
        
        if not task_data.get("title"):
            raise WorkflowError("Task title is required", {"operation": "create"})
        
        # Set defaults
        task_data.setdefault("status", "pending")
        task_data.setdefault("priority", "medium")
        task_data.setdefault("created_by", state["user_id"])
        
        state["input_data"]["task_data"] = task_data
    
    def _validate_update_data(self, state: WorkflowState):
        """Validate data for task update"""
        if not state["input_data"].get("task_id"):
            raise WorkflowError("Task ID is required for update", {"operation": "update"})
        
        task_data = state["input_data"].get("task_data", {})
        if not task_data:
            raise WorkflowError("Task data is required for update", {"operation": "update"})
    
    def _validate_delete_data(self, state: WorkflowState):
        """Validate data for task deletion"""
        if not state["input_data"].get("task_id"):
            raise WorkflowError("Task ID is required for delete", {"operation": "delete"})
    
    def _validate_get_data(self, state: WorkflowState):
        """Validate data for task retrieval"""
        if not state["input_data"].get("task_id"):
            raise WorkflowError("Task ID is required for get", {"operation": "get"})
    
    async def database_executor_node(self, state: WorkflowState) -> WorkflowState:
        """Execute database CRUD operations using task tools"""
        state["current_node"] = "database_executor"
        state["visited_nodes"].append("database_executor")
        
        from ..tools import TaskDatabaseTool
        
        try:
            # Initialize task database tool
            task_tool = TaskDatabaseTool()
            
            operation = state["input_data"]["detected_operation"]
            
            # Prepare tool input
            tool_input = {
                "operation": operation,
                "task_data": state["input_data"].get("task_data"),
                "task_id": state["input_data"].get("task_id"),
                "filters": state["input_data"].get("filters", {})
            }
            
            # Prepare context
            tool_context = {
                "user_id": state["user_id"],
                "user_context": state.get("user_context", {})
            }
            
            # Execute tool
            tool_result = await task_tool.execute(tool_input, tool_context)
            
            # Store result
            state["output_data"] = {
                "operation": operation,
                "result": tool_result.data,
                "success": tool_result.success,
                "error": tool_result.error,
                "execution_time": tool_result.execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store metrics
            state["metrics"]["task_execution"] = {
                "success": tool_result.success,
                "execution_time": tool_result.execution_time,
                "operation": operation
            }
            
        except Exception as e:
            # Handle tool execution errors
            state["output_data"] = {
                "operation": state["input_data"]["detected_operation"],
                "result": {},
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["metrics"]["task_execution"] = {
                "success": False,
                "error": str(e),
                "operation": state["input_data"]["detected_operation"]
            }
        
        return state
    
    async def schedule_recalculator_node(self, state: WorkflowState) -> WorkflowState:
        """Recalculate intelligent scheduling using TaskSchedulingTool"""
        state["current_node"] = "schedule_recalculator"
        state["visited_nodes"].append("schedule_recalculator")
        
        operation = state["input_data"]["detected_operation"]
        
        # Only recalculate for operations that affect scheduling
        if operation in ["create", "update", "delete"]:
            from ..tools import TaskSchedulingTool
            
            try:
                # Initialize scheduling tool
                scheduling_tool = TaskSchedulingTool()
                
                # Get all user tasks for rescheduling
                # For now, create a simple input with the current task
                current_task = state["output_data"].get("result", {})
                if isinstance(current_task, dict) and "task" in current_task:
                    tasks_to_schedule = [current_task["task"]]
                else:
                    # If no specific task, create a placeholder for scheduling
                    tasks_to_schedule = [{"id": "placeholder", "title": "Task update", "priority": "medium"}]
                
                # Prepare scheduling input
                scheduling_input = {
                    "tasks": tasks_to_schedule,
                    "constraints": {
                        "respect_priorities": True,
                        "avoid_conflicts": True,
                        "optimize_for": "productivity"
                    }
                }
                
                # Prepare context
                scheduling_context = {
                    "user_id": state["user_id"],
                    "user_context": state.get("user_context", {})
                }
                
                # Execute scheduling
                scheduling_result = await scheduling_tool.execute(scheduling_input, scheduling_context)
                
                # Store scheduling metrics
                state["metrics"]["schedule_recalculation"] = {
                    "success": scheduling_result.success,
                    "execution_time": scheduling_result.execution_time,
                    "scheduled_tasks": len(scheduling_result.data.get("scheduled_tasks", [])),
                    "operation_trigger": operation,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                # Handle scheduling errors gracefully
                state["metrics"]["schedule_recalculation"] = {
                    "success": False,
                    "error": str(e),
                    "operation_trigger": operation,
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            # No scheduling needed for read operations
            state["metrics"]["schedule_recalculation"] = {
                "skipped": True,
                "reason": f"Operation '{operation}' does not affect scheduling",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
    async def notification_service_node(self, state: WorkflowState) -> WorkflowState:
        """Send user notifications for task changes using email tools"""
        state["current_node"] = "notification_service"
        state["visited_nodes"].append("notification_service")
        
        operation = state["input_data"]["detected_operation"]
        
        # Send notifications for operations that change data
        if operation in ["create", "update", "delete"]:
            from ..tools import SystemEmailTool
            
            try:
                # Initialize system email tool for agent notifications
                email_tool = SystemEmailTool()
                
                # Get task details for notification
                task_result = state["output_data"].get("result", {})
                task_title = "Unknown Task"
                
                if isinstance(task_result, dict):
                    if "task" in task_result:
                        task_title = task_result["task"].get("title", "Unknown Task")
                    elif "title" in task_result:
                        task_title = task_result["title"]
                
                # Prepare notification email
                subject_map = {
                    "create": f"Task Created: {task_title}",
                    "update": f"Task Updated: {task_title}",
                    "delete": f"Task Deleted: {task_title}"
                }
                
                message_map = {
                    "create": f"A new task '{task_title}' has been created in your PulsePlan.",
                    "update": f"Your task '{task_title}' has been updated in PulsePlan.",
                    "delete": f"The task '{task_title}' has been deleted from your PulsePlan."
                }
                
                # Get user email from context (would normally come from user profile)
                user_email = state.get("user_context", {}).get("email", "user@example.com")
                
                # Prepare email input
                email_input = {
                    "operation": "send",
                    "to": user_email,
                    "subject": subject_map[operation],
                    "body": message_map[operation],
                    "sender": "agent"  # Agent sending notification
                }
                
                # Prepare context
                email_context = {
                    "user_id": state["user_id"],
                    "user_context": state.get("user_context", {})
                }
                
                # Send notification email
                email_result = await email_tool.execute(email_input, email_context)
                
                # Store notification metrics
                state["metrics"]["notification_sent"] = {
                    "success": email_result.success,
                    "method": "email",
                    "operation": operation,
                    "task_title": task_title,
                    "recipient": user_email,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                # Handle notification errors gracefully (non-critical)
                state["metrics"]["notification_sent"] = {
                    "success": False,
                    "error": str(e),
                    "operation": operation,
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            # No notifications for read operations
            state["metrics"]["notification_sent"] = {
                "skipped": True,
                "reason": f"Operation '{operation}' does not require notification",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
