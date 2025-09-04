"""
Database Operations Workflow
Unified database operations for tasks and todos with intelligent routing
"""
from typing import Dict, List, Any
from datetime import datetime
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError


class DatabaseGraph(BaseWorkflow):
    """
    Database Operations Workflow that:
    1. Analyzes input to determine entity type (task/todo) and operation
    2. Validates data and permissions
    3. Routes to appropriate database tool (TaskDatabaseTool/TodoDatabaseTool)
    4. Manages cache invalidation and updates
    5. Logs operations for audit compliance
    6. Returns unified response format
    """
    
    def __init__(self):
        super().__init__(WorkflowType.DATABASE)
        
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for database workflow"""
        return {
            "input_validator": self.input_validator_node,
            "input_analyzer": self.input_analyzer_node,
            "validation_gate": self.validation_gate_node,
            "policy_gate": self.policy_gate_node,
            "rate_limiter": self.rate_limiter_node,
            "idempotency_checker": self.idempotency_checker_node,
            "tool_router": self.tool_router_node,
            "cache_manager": self.cache_manager_node,
            "audit_logger": self.audit_logger_node,
            "result_processor": self.result_processor_node,
            "trace_updater": self.trace_updater_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # Initial processing
            ("input_validator", "input_analyzer"),
            ("input_analyzer", "validation_gate"),
            ("validation_gate", "policy_gate"),
            
            # Standard workflow checks
            ("policy_gate", "rate_limiter"),
            ("rate_limiter", "idempotency_checker"),
            
            # Core execution
            ("idempotency_checker", "tool_router"),
            ("tool_router", "cache_manager"),
            ("cache_manager", "audit_logger"),
            
            # Final processing
            ("audit_logger", "result_processor"),
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    def input_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze input to determine entity type and operation"""
        state["current_node"] = "input_analyzer"
        state["visited_nodes"].append("input_analyzer")
        
        input_data = state["input_data"]
        
        # Determine entity type based on input structure
        entity_type = self._detect_entity_type(input_data)
        operation = self._detect_operation_type(input_data, entity_type)
        
        # Store analysis results
        state["input_data"]["entity_type"] = entity_type
        state["input_data"]["detected_operation"] = operation
        
        # Add analysis metadata
        state["metrics"]["input_analysis"] = {
            "entity_type": entity_type,
            "operation": operation,
            "input_size": len(str(input_data)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return state
    
    def _detect_entity_type(self, input_data: Dict[str, Any]) -> str:
        """Detect whether operation is for tasks or todos"""
        # Explicit entity type
        if "entity_type" in input_data:
            entity_type = input_data["entity_type"].lower()
            if entity_type in ["task", "todo"]:
                return entity_type
        
        # Check for entity-specific fields
        # Todo indicators (simple structure)
        if any(key in input_data for key in ["todo_id", "todo_data", "todo_ids"]):
            return "todo"
        
        # Task indicators (complex structure)
        if any(key in input_data for key in ["task_id", "task_data", "estimated_minutes", "min_block_minutes", "prerequisites"]):
            return "task"
        
        # Check operation-specific data
        data = input_data.get("task_data") or input_data.get("todo_data") or input_data.get("data", {})
        
        # Task-specific fields
        task_fields = ["kind", "estimated_minutes", "min_block_minutes", "prerequisites", "preferred_windows", "course_id"]
        if any(field in data for field in task_fields):
            return "task"
        
        # Todo-specific operations
        if input_data.get("operation") in ["bulk_toggle", "convert_to_task"]:
            return "todo"
        
        # Default to todo for simple operations
        return "todo"
    
    def _detect_operation_type(self, input_data: Dict[str, Any], entity_type: str) -> str:
        """Detect operation type based on input data"""
        # Explicit operation
        if "operation" in input_data:
            return input_data["operation"]
        
        # Infer from data structure
        entity_id_key = f"{entity_type}_id"
        entity_data_key = f"{entity_type}_data"
        
        if input_data.get(entity_id_key):
            if input_data.get("delete", False):
                return "delete"
            elif input_data.get(entity_data_key):
                return "update"
            else:
                return "get"
        elif input_data.get(entity_data_key):
            return "create"
        else:
            return "list"
    
    def validation_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Validate data based on entity type and operation"""
        state["current_node"] = "validation_gate"
        state["visited_nodes"].append("validation_gate")
        
        entity_type = state["input_data"]["entity_type"]
        operation = state["input_data"]["detected_operation"]
        
        # Entity-specific validation
        if entity_type == "task":
            self._validate_task_operation(state, operation)
        elif entity_type == "todo":
            self._validate_todo_operation(state, operation)
        else:
            raise WorkflowError(f"Unknown entity type: {entity_type}", {"entity_type": entity_type})
        
        return state
    
    def _validate_task_operation(self, state: WorkflowState, operation: str):
        """Validate task operation data"""
        valid_operations = ["create", "update", "delete", "get", "list", "bulk_operations", "validate_dependencies"]
        
        if operation not in valid_operations:
            raise WorkflowError(f"Invalid task operation: {operation}", {"valid_operations": valid_operations})
        
        input_data = state["input_data"]
        
        if operation == "create" and not input_data.get("task_data"):
            raise WorkflowError("Task data is required for create operation", {"operation": operation})
        
        if operation in ["update", "delete", "get", "validate_dependencies"] and not input_data.get("task_id"):
            raise WorkflowError("Task ID is required for this operation", {"operation": operation})
        
        if operation == "update" and not input_data.get("task_data"):
            raise WorkflowError("Task data is required for update operation", {"operation": operation})
        
        if operation == "bulk_operations" and not input_data.get("operations"):
            raise WorkflowError("Operations list is required for bulk operations", {"operation": operation})
    
    def _validate_todo_operation(self, state: WorkflowState, operation: str):
        """Validate todo operation data"""
        valid_operations = ["create", "update", "delete", "get", "list", "bulk_toggle", "convert_to_task"]
        
        if operation not in valid_operations:
            raise WorkflowError(f"Invalid todo operation: {operation}", {"valid_operations": valid_operations})
        
        input_data = state["input_data"]
        
        if operation == "create" and not input_data.get("todo_data"):
            raise WorkflowError("Todo data is required for create operation", {"operation": operation})
        
        if operation in ["update", "delete", "get", "convert_to_task"] and not input_data.get("todo_id"):
            raise WorkflowError("Todo ID is required for this operation", {"operation": operation})
        
        if operation == "update" and not input_data.get("todo_data"):
            raise WorkflowError("Todo data is required for update operation", {"operation": operation})
        
        if operation == "bulk_toggle" and not input_data.get("todo_ids"):
            raise WorkflowError("Todo IDs list is required for bulk toggle", {"operation": operation})
    
    async def tool_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route operation to appropriate database tool"""
        state["current_node"] = "tool_router"
        state["visited_nodes"].append("tool_router")
        
        entity_type = state["input_data"]["entity_type"]
        
        try:
            if entity_type == "task":
                result = await self._execute_task_operation(state)
            elif entity_type == "todo":
                result = await self._execute_todo_operation(state)
            else:
                raise WorkflowError(f"Unsupported entity type: {entity_type}")
            
            # Store tool execution result
            state["output_data"] = result
            
            # Store metrics
            state["metrics"]["tool_execution"] = {
                "entity_type": entity_type,
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0),
                "operation": state["input_data"]["detected_operation"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Handle tool execution errors
            state["output_data"] = {
                "success": False,
                "data": {},
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["metrics"]["tool_execution"] = {
                "entity_type": entity_type,
                "success": False,
                "error": str(e),
                "operation": state["input_data"]["detected_operation"],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
    async def _execute_task_operation(self, state: WorkflowState) -> Dict[str, Any]:
        """Execute task operation using TaskDatabaseTool"""
        from ..tools import TaskDatabaseTool
        
        task_tool = TaskDatabaseTool()
        
        # Prepare tool input
        tool_input = {
            "operation": state["input_data"]["detected_operation"],
            "task_data": state["input_data"].get("task_data"),
            "task_id": state["input_data"].get("task_id"),
            "filters": state["input_data"].get("filters", {}),
            "operations": state["input_data"].get("operations", [])
        }
        
        # Prepare context
        tool_context = {
            "user_id": state["user_id"],
            "user_context": state.get("user_context", {})
        }
        
        # Execute tool
        result = await task_tool.execute(tool_input, tool_context)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_todo_operation(self, state: WorkflowState) -> Dict[str, Any]:
        """Execute todo operation using TodoDatabaseTool"""
        from ..tools import TodoDatabaseTool
        
        todo_tool = TodoDatabaseTool()
        
        # Prepare tool input
        tool_input = {
            "operation": state["input_data"]["detected_operation"],
            "todo_data": state["input_data"].get("todo_data"),
            "todo_id": state["input_data"].get("todo_id"),
            "todo_ids": state["input_data"].get("todo_ids", []),
            "filters": state["input_data"].get("filters", {}),
            "completed": state["input_data"].get("completed", True)
        }
        
        # Prepare context
        tool_context = {
            "user_id": state["user_id"],
            "user_context": state.get("user_context", {})
        }
        
        # Execute tool
        result = await todo_tool.execute(tool_input, tool_context)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cache_manager_node(self, state: WorkflowState) -> WorkflowState:
        """Handle cache invalidation and updates"""
        state["current_node"] = "cache_manager"
        state["visited_nodes"].append("cache_manager")
        
        operation = state["input_data"]["detected_operation"]
        entity_type = state["input_data"]["entity_type"]
        
        # Only manage cache for operations that modify data
        if operation in ["create", "update", "delete", "bulk_operations", "bulk_toggle"]:
            try:
                # TODO: Implement Redis cache invalidation
                cache_keys_invalidated = await self._invalidate_cache(state, entity_type, operation)
                
                state["metrics"]["cache_management"] = {
                    "keys_invalidated": cache_keys_invalidated,
                    "operation": operation,
                    "entity_type": entity_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                # Cache errors should not fail the operation
                state["metrics"]["cache_management"] = {
                    "error": str(e),
                    "operation": operation,
                    "entity_type": entity_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            state["metrics"]["cache_management"] = {
                "skipped": True,
                "reason": f"Read operation '{operation}' does not require cache invalidation",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
    async def _invalidate_cache(self, state: WorkflowState, entity_type: str, operation: str) -> List[str]:
        """Invalidate relevant cache keys"""
        # TODO: Implement actual Redis cache invalidation
        user_id = state["user_id"]
        
        # Mock cache invalidation
        cache_keys = [
            f"{entity_type}s:user:{user_id}:list",
            f"{entity_type}s:user:{user_id}:count",
            f"user:{user_id}:dashboard"
        ]
        
        if operation in ["update", "delete"] and state["input_data"].get(f"{entity_type}_id"):
            cache_keys.append(f"{entity_type}:{state['input_data'][f'{entity_type}_id']}")
        
        return cache_keys
    
    async def audit_logger_node(self, state: WorkflowState) -> WorkflowState:
        """Log operations for audit compliance"""
        state["current_node"] = "audit_logger"
        state["visited_nodes"].append("audit_logger")
        
        operation = state["input_data"]["detected_operation"]
        entity_type = state["input_data"]["entity_type"]
        
        # Only log operations that modify data
        if operation in ["create", "update", "delete", "bulk_operations", "bulk_toggle"]:
            try:
                # TODO: Implement actual audit logging to database/external service
                audit_entry = await self._create_audit_log(state, entity_type, operation)
                
                state["metrics"]["audit_logging"] = {
                    "logged": True,
                    "audit_id": audit_entry["id"],
                    "operation": operation,
                    "entity_type": entity_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                # Audit logging errors should not fail the operation
                state["metrics"]["audit_logging"] = {
                    "logged": False,
                    "error": str(e),
                    "operation": operation,
                    "entity_type": entity_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            state["metrics"]["audit_logging"] = {
                "skipped": True,
                "reason": f"Read operation '{operation}' does not require audit logging",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
    async def _create_audit_log(self, state: WorkflowState, entity_type: str, operation: str) -> Dict[str, Any]:
        """Create audit log entry"""
        # TODO: Implement actual audit log creation
        import uuid
        
        audit_entry = {
            "id": str(uuid.uuid4()),
            "user_id": state["user_id"],
            "entity_type": entity_type,
            "operation": operation,
            "success": state["output_data"].get("success", False),
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": state.get("user_context", {}).get("ip_address", "unknown"),
            "user_agent": state.get("user_context", {}).get("user_agent", "unknown")
        }
        
        return audit_entry