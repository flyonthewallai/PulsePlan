"""
Task management tools for PulsePlan agents.
Handles CRUD operations and intelligent task scheduling.
"""
from typing import Dict, Any, List
import asyncio
from datetime import datetime

from .base import TaskTool, ToolResult, ToolError


class TaskDatabaseTool(TaskTool):
    """Enhanced Task database operations tool with dependency validation and constraints"""
    
    def __init__(self):
        super().__init__(
            name="task_database",
            description="Comprehensive task CRUD operations with dependency validation and constraint checking"
        )
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for task operations"""
        operation = input_data.get("operation")
        
        if operation not in ["create", "update", "delete", "get", "list", "bulk_operations", "validate_dependencies"]:
            return False
        
        if operation == "create" and not input_data.get("task_data"):
            return False
        
        if operation in ["update", "delete", "get", "validate_dependencies"] and not input_data.get("task_id"):
            return False
        
        if operation == "update" and not input_data.get("task_data"):
            return False
            
        if operation == "bulk_operations" and not input_data.get("operations"):
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute task operation"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data", self.name)
            
            operation = input_data["operation"]
            
            # Route to specific operation
            if operation == "create":
                result = await self.create_task(
                    task_data=input_data["task_data"],
                    context=context
                )
            elif operation == "update":
                result = await self.update_task(
                    task_id=input_data["task_id"],
                    task_data=input_data["task_data"],
                    context=context
                )
            elif operation == "delete":
                result = await self.delete_task(
                    task_id=input_data["task_id"],
                    context=context
                )
            elif operation == "get":
                result = await self.get_task(
                    task_id=input_data["task_id"],
                    context=context
                )
            elif operation == "list":
                result = await self.list_tasks(
                    filters=input_data.get("filters", {}),
                    context=context
                )
            elif operation == "bulk_operations":
                result = await self.bulk_operations(
                    operations=input_data["operations"],
                    context=context
                )
            elif operation == "validate_dependencies":
                result = await self.validate_dependencies(
                    task_id=input_data["task_id"],
                    context=context
                )
            
            # Add execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Log execution
            self.log_execution(input_data, result, context)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def create_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create new task"""
        try:
            from ...config.supabase import get_supabase
            
            # Validate required fields
            if not task_data.get("title"):
                raise ToolError("Task title is required", self.name)
            
            user_id = context["user_id"]
            
            # Validate prerequisites exist if provided
            prerequisites = task_data.get("prerequisites", [])
            if prerequisites:
                await self._validate_prerequisites_exist(prerequisites, user_id)
            
            # Validate scheduling constraints
            await self._validate_scheduling_constraints(task_data)
            
            # Create task record for database
            task_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": task_data["title"],
                "description": task_data.get("description", ""),
                "kind": task_data.get("kind", "admin"),
                "estimated_minutes": task_data.get("estimated_minutes", 60),
                "min_block_minutes": task_data.get("min_block_minutes", 30),
                "max_block_minutes": task_data.get("max_block_minutes"),
                "deadline": task_data.get("deadline"),
                "earliest_start": task_data.get("earliest_start"),
                "preferred_windows": task_data.get("preferred_windows", []),
                "avoid_windows": task_data.get("avoid_windows", []),
                "fixed": task_data.get("fixed", False),
                "parent_task_id": task_data.get("parent_task_id"),
                "prerequisites": prerequisites,
                "weight": task_data.get("weight", 1.0),
                "course_id": task_data.get("course_id"),
                "must_finish_before": task_data.get("must_finish_before"),
                "tags": task_data.get("tags", []),
                "pinned_slots": task_data.get("pinned_slots", []),
                "status": task_data.get("status", "pending"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert into Supabase database
            supabase = get_supabase()
            result = supabase.table("tasks").insert(task_record).execute()
            
            if result.data:
                return ToolResult(
                    success=True,
                    data={"task": result.data[0]},
                    metadata={"operation": "create", "user_id": user_id, "record_id": task_record["id"]}
                )
            else:
                raise ToolError("Failed to insert task into database", self.name)
            
            return ToolResult(
                success=True,
                data={"task": task_record},
                metadata={"operation": "create", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to create task: {e}", self.name, recoverable=True)
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update existing task"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.1)  # Simulate database call
            
            user_id = context["user_id"]
            
            updated_task = {
                "id": task_id,
                "title": task_data.get("title", "Updated Task"),
                "description": task_data.get("description", ""),
                "status": task_data.get("status", "pending"),
                "priority": task_data.get("priority", "medium"),
                "due_date": task_data.get("due_date"),
                "created_by": user_id,
                "created_at": "2024-01-01T00:00:00Z",  # Would come from database
                "updated_at": datetime.utcnow().isoformat()
            }
            
            return ToolResult(
                success=True,
                data={"task": updated_task},
                metadata={"operation": "update", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to update task: {e}", self.name, recoverable=True)
    
    async def delete_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete task"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.1)  # Simulate database call
            
            user_id = context["user_id"]
            
            return ToolResult(
                success=True,
                data={
                    "deleted_task_id": task_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "deleted_by": user_id
                },
                metadata={"operation": "delete", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to delete task: {e}", self.name, recoverable=True)
    
    async def get_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get specific task"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.1)  # Simulate database call
            
            user_id = context["user_id"]
            
            task = {
                "id": task_id,
                "title": "Sample Task",
                "description": "This is a sample task",
                "status": "pending",
                "priority": "high",
                "due_date": "2024-01-20T00:00:00Z",
                "created_by": user_id,
                "created_at": "2024-01-10T00:00:00Z",
                "updated_at": "2024-01-10T00:00:00Z"
            }
            
            return ToolResult(
                success=True,
                data={"task": task},
                metadata={"operation": "get", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to get task: {e}", self.name, recoverable=True)
    
    async def list_tasks(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List tasks with filters"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.1)  # Simulate database call
            
            user_id = context["user_id"]
            
            tasks = [
                {
                    "id": "task_1",
                    "title": "Complete project proposal",
                    "status": "pending",
                    "priority": "high",
                    "due_date": "2024-01-20T00:00:00Z",
                    "created_by": user_id
                },
                {
                    "id": "task_2",
                    "title": "Review team feedback",
                    "status": "in_progress",
                    "priority": "medium",
                    "due_date": "2024-01-18T00:00:00Z",
                    "created_by": user_id
                }
            ]
            
            # Apply filters (mock implementation)
            filtered_tasks = tasks
            if filters.get("status"):
                filtered_tasks = [t for t in tasks if t["status"] == filters["status"]]
            if filters.get("priority"):
                filtered_tasks = [t for t in filtered_tasks if t["priority"] == filters["priority"]]
            
            return ToolResult(
                success=True,
                data={
                    "tasks": filtered_tasks,
                    "total": len(filtered_tasks),
                    "filters_applied": filters
                },
                metadata={"operation": "list", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to list tasks: {e}", self.name, recoverable=True)
    
    async def bulk_operations(self, operations: List[Dict[str, Any]], context: Dict[str, Any]) -> ToolResult:
        """Execute multiple task operations in sequence"""
        try:
            # TODO: Implement actual database batch operations with Supabase
            await asyncio.sleep(0.2)  # Simulate batch database call
            
            user_id = context["user_id"]
            results = []
            errors = []
            
            for i, operation in enumerate(operations):
                try:
                    op_type = operation.get("type")
                    if op_type == "create":
                        result = await self.create_task(operation["data"], context)
                    elif op_type == "update":
                        result = await self.update_task(operation["task_id"], operation["data"], context)
                    elif op_type == "delete":
                        result = await self.delete_task(operation["task_id"], context)
                    else:
                        errors.append(f"Operation {i}: Unknown operation type '{op_type}'")
                        continue
                    
                    results.append({
                        "operation_index": i,
                        "type": op_type,
                        "success": result.success,
                        "data": result.data
                    })
                    
                except Exception as e:
                    errors.append(f"Operation {i}: {str(e)}")
            
            return ToolResult(
                success=len(errors) == 0,
                data={
                    "results": results,
                    "total_operations": len(operations),
                    "successful_operations": len(results),
                    "failed_operations": len(errors),
                    "errors": errors
                },
                metadata={"operation": "bulk_operations", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to execute bulk operations: {e}", self.name, recoverable=True)
    
    async def validate_dependencies(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Validate task dependencies and constraints"""
        try:
            # TODO: Implement actual dependency validation with database
            await asyncio.sleep(0.1)  # Simulate dependency check
            
            user_id = context["user_id"]
            
            # Mock dependency validation
            validation_results = {
                "task_id": task_id,
                "dependencies_valid": True,
                "constraints_valid": True,
                "circular_dependencies": False,
                "missing_prerequisites": [],
                "scheduling_conflicts": [],
                "warnings": [],
                "recommendations": [
                    "Consider breaking large tasks into smaller blocks",
                    "Schedule high-priority tasks during peak productivity hours"
                ]
            }
            
            return ToolResult(
                success=True,
                data={"validation": validation_results},
                metadata={"operation": "validate_dependencies", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to validate dependencies: {e}", self.name, recoverable=True)
    
    async def _validate_prerequisites_exist(self, prerequisites: List[str], user_id: str) -> None:
        """Validate that prerequisite tasks exist"""
        # TODO: Implement actual database check
        await asyncio.sleep(0.05)
        
        # Mock validation - in real implementation would check database
        for prereq_id in prerequisites:
            if not prereq_id or not prereq_id.strip():
                raise ToolError(f"Invalid prerequisite task ID: {prereq_id}", self.name)
    
    async def _validate_scheduling_constraints(self, task_data: Dict[str, Any]) -> None:
        """Validate task scheduling constraints"""
        try:
            estimated_minutes = task_data.get("estimated_minutes", 60)
            min_block_minutes = task_data.get("min_block_minutes", 30)
            max_block_minutes = task_data.get("max_block_minutes")
            
            # Validate positive values
            if estimated_minutes <= 0:
                raise ToolError("Estimated minutes must be positive", self.name)
            if min_block_minutes <= 0:
                raise ToolError("Minimum block minutes must be positive", self.name)
            
            # Validate block constraints
            if max_block_minutes and max_block_minutes < min_block_minutes:
                raise ToolError("Maximum block minutes cannot be less than minimum", self.name)
            
            # Validate weight
            weight = task_data.get("weight", 1.0)
            if weight < 0:
                raise ToolError("Task weight cannot be negative", self.name)
                
        except ValueError as e:
            raise ToolError(f"Invalid scheduling constraint values: {e}", self.name)


class TaskSchedulingTool(TaskTool):
    """Intelligent task scheduling tool"""
    
    def __init__(self):
        super().__init__(
            name="task_scheduling",
            description="Intelligent scheduling and optimization of tasks"
        )
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for scheduling operations"""
        if not input_data.get("tasks"):
            return False
        
        if not isinstance(input_data["tasks"], list):
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute task scheduling"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data - tasks list required", self.name)
            
            tasks = input_data["tasks"]
            constraints = input_data.get("constraints", {})
            
            # Perform intelligent scheduling
            scheduled_tasks = await self.schedule_tasks(tasks, constraints, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ToolResult(
                success=True,
                data={
                    "scheduled_tasks": scheduled_tasks,
                    "scheduling_metadata": {
                        "total_tasks": len(tasks),
                        "constraints_applied": constraints,
                        "optimization_strategy": "priority_based"
                    }
                },
                execution_time=execution_time,
                metadata={"operation": "schedule", "user_id": context["user_id"]}
            )
            
            self.log_execution(input_data, result, context)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def schedule_tasks(self, tasks: List[Dict[str, Any]], constraints: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform intelligent task scheduling"""
        try:
            # TODO: Implement actual scheduling algorithm
            await asyncio.sleep(0.2)  # Simulate scheduling computation
            
            # Simple priority-based scheduling for now
            def priority_score(task):
                priority_map = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
                return priority_map.get(task.get("priority", "medium"), 2)
            
            # Sort by priority and due date
            sorted_tasks = sorted(tasks, key=lambda t: (
                -priority_score(t),
                t.get("due_date", "9999-12-31")
            ))
            
            # Add scheduling metadata
            scheduled_tasks = []
            for i, task in enumerate(sorted_tasks):
                scheduled_task = task.copy()
                scheduled_task.update({
                    "scheduled_order": i + 1,
                    "estimated_start": f"2024-01-15T{9 + i}:00:00Z",  # Mock scheduling
                    "estimated_duration": task.get("estimated_duration", 60),
                    "scheduling_confidence": 0.8
                })
                scheduled_tasks.append(scheduled_task)
            
            return scheduled_tasks
            
        except Exception as e:
            raise ToolError(f"Failed to schedule tasks: {e}", self.name, recoverable=True)
    
    # Implement abstract methods from TaskTool
    async def create_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for scheduling tool"""
        raise ToolError("Create task not supported by scheduling tool", self.name)
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for scheduling tool"""
        raise ToolError("Update task not supported by scheduling tool", self.name)
    
    async def delete_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Not implemented for scheduling tool"""
        raise ToolError("Delete task not supported by scheduling tool", self.name)
    
    async def list_tasks(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for scheduling tool"""
        raise ToolError("List tasks not supported by scheduling tool", self.name)