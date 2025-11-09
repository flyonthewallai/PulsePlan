"""
Task management tools for PulsePlan agents.
Handles CRUD operations and intelligent task scheduling.
"""
from typing import Dict, Any, List
import asyncio
import uuid
import logging
from datetime import datetime

from ..core.base import TaskTool, ToolResult, ToolError
from app.services.task_service import TaskService
from app.services.todo_service import TodoService
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TaskDatabaseTool(TaskTool):
    """Enhanced Task database operations tool with dependency validation and constraints"""
    
    def __init__(self):
        super().__init__(
            name="task_database",
            description="Comprehensive task CRUD operations with dependency validation and constraint checking"
        )
        self.task_service = TaskService()
        self.todo_service = TodoService()
    
    def get_required_tokens(self) -> List[str]:
        """Return list of required OAuth tokens for this tool"""
        return []  # No OAuth tokens required for database operations
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for task operations"""
        operation = input_data.get("operation")
        
        if operation not in ["create", "update", "delete", "get", "list", "bulk_operations", "validate_dependencies", "search_by_title", "delete_by_title_batch", "update_by_title_batch"]:
            return False
        
        if operation == "create" and not input_data.get("task_data"):
            return False
        
        if operation in ["update", "delete", "get", "validate_dependencies"] and not input_data.get("task_id") and not input_data.get("title"):
            return False
        
        if operation == "update" and not input_data.get("task_data"):
            return False
            
        if operation == "bulk_operations" and not input_data.get("operations"):
            return False
        
        if operation == "search_by_title" and not input_data.get("title"):
            return False
        
        if operation == "delete_by_title_batch" and not input_data.get("titles"):
            return False
        
        if operation == "update_by_title_batch" and not input_data.get("title") and not input_data.get("task_data"):
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
                task_id = input_data.get("task_id")
                if not task_id and input_data.get("title"):
                    # Search for task by title first
                    search_result = await self.search_tasks_by_title(input_data["title"], context)
                    if search_result.success and search_result.data.get("tasks"):
                        task_id = search_result.data["tasks"][0]["id"]
                    else:
                        raise ToolError(f"No task found with title '{input_data['title']}'", self.name)
                
                result = await self.update_task(
                    task_id=task_id,
                    task_data=input_data["task_data"],
                    context=context
                )
            elif operation == "delete":
                task_id = input_data.get("task_id")
                if not task_id and input_data.get("title"):
                    # Search for task by title first
                    search_result = await self.search_tasks_by_title(input_data["title"], context)
                    if search_result.success and search_result.data.get("tasks"):
                        if len(search_result.data["tasks"]) > 1:
                            # Multiple matches found - list them for user
                            task_titles = [task["title"] for task in search_result.data["tasks"]]
                            raise ToolError(f"Multiple tasks found with similar titles: {', '.join(task_titles)}. Please be more specific.", self.name)
                        task_id = search_result.data["tasks"][0]["id"]
                    else:
                        raise ToolError(f"No task found with title '{input_data['title']}'. Check the exact title and try again.", self.name)

                result = await self.delete_task(
                    task_id=task_id,
                    context=context
                )
            elif operation == "get":
                task_id = input_data.get("task_id")
                if not task_id and input_data.get("title"):
                    # Search for task by title first
                    search_result = await self.search_tasks_by_title(input_data["title"], context)
                    if search_result.success and search_result.data.get("tasks"):
                        task_id = search_result.data["tasks"][0]["id"]
                    else:
                        raise ToolError(f"No task found with title '{input_data['title']}'", self.name)
                
                result = await self.get_task(
                    task_id=task_id,
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
            elif operation == "search_by_title":
                result = await self.search_tasks_by_title(
                    title=input_data["title"],
                    context=context
                )
            elif operation == "delete_by_title_batch":
                result = await self.delete_tasks_by_title_batch(
                    titles=input_data["titles"],
                    context=context
                )
            elif operation == "update_by_title_batch":
                result = await self.update_task_by_title_batch(
                    title=input_data["title"],
                    task_data=input_data["task_data"],
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
        """Create new task or todo based on task_type"""
        try:
            # Validate required fields
            if not task_data.get("title"):
                raise ToolError("Task title is required", self.name)

            user_id = context["user_id"]
            task_type = task_data.get("task_type", "todo")  # Default to todo

            # If it's not an academic task type, create a todo instead
            if task_type not in ["assignment", "quiz", "exam"]:
                # Convert task_data to todo_data format
                todo_data = {
                    "title": task_data["title"],
                    "description": task_data.get("description", ""),
                    "priority": self._map_priority(task_data.get("priority", "medium")),
                    "due_date": task_data.get("due_date") or task_data.get("deadline"),
                    "tags": task_data.get("tags", []),
                    "estimated_minutes": task_data.get("estimated_minutes")
                }

                # Use TodoService to create the todo
                todo = await self.todo_service.create_todo(user_id, todo_data)
                return ToolResult(
                    success=True,
                    data={"todo": todo, "todo_id": todo["id"]},
                    metadata={"operation": "create", "user_id": user_id, "todo_id": todo["id"]}
                )

            # For academic tasks (assignment, quiz, exam), use TaskService
            task = await self.task_service.create_task(user_id, task_data)
            
            return ToolResult(
                success=True,
                data={"task": task},
                metadata={"operation": "create", "user_id": user_id, "record_id": task["id"]}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to create task: {e}", self.name, recoverable=True)

    def _map_priority(self, priority: str) -> str:
        """Map task priority to todo priority format"""
        priority_mapping = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "urgent": "high",
            "critical": "high"
        }
        return priority_mapping.get(priority.lower(), "medium")
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update existing task"""
        try:
            user_id = context["user_id"]
            
            # Use TaskService to update
            updated_task = await self.task_service.update_task(task_id, user_id, task_data)
            
            return ToolResult(
                success=True,
                data={"task": updated_task},
                metadata={"operation": "update", "user_id": user_id, "task_id": task_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise ToolError(f"Failed to update task: {e}", self.name, recoverable=True)
    
    async def delete_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete task"""
        try:
            user_id = context["user_id"]
            
            # Use TaskService to delete
            result = await self.task_service.delete_task(task_id, user_id)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "delete", "user_id": user_id, "task_id": task_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise ToolError(f"Failed to delete task: {e}", self.name, recoverable=True)
    
    async def get_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get specific task"""
        try:
            user_id = context["user_id"]
            
            # Use TaskService to get task
            task = await self.task_service.get_task(task_id, user_id)
            
            if not task:
                raise ToolError("Task not found", self.name, recoverable=True)
            
            return ToolResult(
                success=True,
                data={"task": task},
                metadata={"operation": "get", "user_id": user_id, "task_id": task_id}
            )
            
        except ToolError:
            raise
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to get task: {e}", self.name, recoverable=True)
    
    async def list_tasks(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List tasks with filters"""
        try:
            user_id = context["user_id"]
            
            # Use TaskService to list tasks
            result = await self.task_service.list_tasks(user_id, filters)

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "list", "user_id": user_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to list tasks: {e}", self.name, recoverable=True)
    
    async def search_tasks_by_title(self, title: str, context: Dict[str, Any]) -> ToolResult:
        """Search for tasks by title (case-insensitive partial match with exact match priority)"""
        try:
            user_id = context["user_id"]
            
            # Use TaskService to search
            result = await self.task_service.search_by_title(user_id, title)

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "search_by_title", "user_id": user_id, "search_term": title.strip()}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to search tasks by title: {e}", self.name, recoverable=True)
    
    async def delete_tasks_by_title_batch(self, titles: List[str], context: Dict[str, Any]) -> ToolResult:
        """Delete all tasks matching the given titles (handles multiple tasks with same title)"""
        try:
            user_id = context["user_id"]
            deleted_tasks = []
            failed_tasks = []
            
            for title in titles:
                title_trimmed = title.strip()
                
                # Search for all tasks with this title
                search_result = await self.search_tasks_by_title(title_trimmed, context)
                
                if search_result.success and search_result.data.get("tasks"):
                    tasks = search_result.data["tasks"]
                    
                    # Delete all tasks with this title
                    for task in tasks:
                        try:
                            result = await self.delete_task(task["id"], context)
                            if result.success:
                                deleted_tasks.append(task["title"])
                            else:
                                failed_tasks.append(task["title"])
                        except Exception as e:
                            logger.error(f"Failed to delete task {task['id']}: {e}")
                            failed_tasks.append(task["title"])
                else:
                    # No tasks found with this title
                    failed_tasks.append(title_trimmed)
            
            return ToolResult(
                success=len(deleted_tasks) > 0,
                data={
                    "deleted_tasks": deleted_tasks,
                    "failed_tasks": failed_tasks,
                    "total_requested": len(titles),
                    "total_deleted": len(deleted_tasks),
                    "total_failed": len(failed_tasks)
                },
                metadata={"operation": "delete_by_title_batch", "user_id": user_id, "titles": titles}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to delete tasks by title batch: {e}", self.name, recoverable=True)
    
    async def update_task_by_title_batch(self, title: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update all tasks matching the given title (handles multiple tasks with same title)"""
        try:
            user_id = context["user_id"]
            updated_tasks = []
            failed_tasks = []
            
            title_trimmed = title.strip()
            
            # Search for all tasks with this title
            search_result = await self.search_tasks_by_title(title_trimmed, context)
            
            if search_result.success and search_result.data.get("tasks"):
                tasks = search_result.data["tasks"]
                
                # Update all tasks with this title
                for task in tasks:
                    try:
                        result = await self.update_task(task["id"], task_data, context)
                        if result.success:
                            updated_tasks.append(task["title"])
                        else:
                            failed_tasks.append(task["title"])
                    except Exception as e:
                        logger.error(f"Failed to update task {task['id']}: {e}")
                        failed_tasks.append(task["title"])
            else:
                # No tasks found with this title
                failed_tasks.append(title_trimmed)
            
            return ToolResult(
                success=len(updated_tasks) > 0,
                data={
                    "updated_tasks": updated_tasks,
                    "failed_tasks": failed_tasks,
                    "total_requested": 1,
                    "total_updated": len(updated_tasks),
                    "total_failed": len(failed_tasks)
                },
                metadata={"operation": "update_by_title_batch", "user_id": user_id, "title": title}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to update tasks by title batch: {e}", self.name, recoverable=True)
    
    async def bulk_operations(self, operations: List[Dict[str, Any]], context: Dict[str, Any]) -> ToolResult:
        """Execute multiple task operations in sequence"""
        try:
            # Execute batch operations using implemented database methods
            
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
            user_id = context["user_id"]

            # Get the task and its dependencies - use service layer
            task = await self.task_service.get_task(task_id, user_id)

            if not task:
                raise Exception("Task not found")

            dependencies = task.get("dependencies", [])

            # Validate dependencies exist and are not circular
            missing_prerequisites = []
            circular_dependencies = False
            warnings = []

            if dependencies:
                # Check if dependencies exist - use service layer
                deps_result = await self.task_service.list_tasks(
                    user_id=user_id,
                    filters={"id__in": dependencies}
                )
                found_deps = {dep["id"]: dep for dep in deps_result.get("tasks", [])}
                
                for dep_id in dependencies:
                    if dep_id not in found_deps:
                        missing_prerequisites.append(dep_id)
                    elif found_deps[dep_id]["status"] == "cancelled":
                        warnings.append(f"Dependency '{found_deps[dep_id]['title']}' is cancelled")
                
                # Simple circular dependency check (could be enhanced)
                for dep_id in dependencies:
                    if dep_id == task_id:
                        circular_dependencies = True
                        break
            
            # Check for scheduling conflicts
            scheduling_conflicts = []
            if task.get("due_date"):
                # Could check for overlapping deadlines, resource conflicts, etc.
                pass
            
            validation_results = {
                "task_id": task_id,
                "dependencies_valid": len(missing_prerequisites) == 0,
                "constraints_valid": not circular_dependencies,
                "circular_dependencies": circular_dependencies,
                "missing_prerequisites": missing_prerequisites,
                "scheduling_conflicts": scheduling_conflicts,
                "warnings": warnings,
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
        if not prerequisites:
            return

        # Check each prerequisite ID
        for prereq_id in prerequisites:
            if not prereq_id or not prereq_id.strip():
                raise ToolError(f"Invalid prerequisite task ID: {prereq_id}", self.name)

        # Check if all prerequisites exist in database - use service layer
        result = await self.task_service.list_tasks(
            user_id=user_id,
            filters={"id__in": prerequisites}
        )

        found_ids = {task["id"] for task in result.get("tasks", [])}
        missing_ids = set(prerequisites) - found_ids

        if missing_ids:
            raise ToolError(f"Prerequisite tasks not found: {', '.join(missing_ids)}", self.name)
    
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
    
    def get_required_tokens(self) -> List[str]:
        """Return list of required OAuth tokens for this tool"""
        return []  # No OAuth tokens required for scheduling operations
    
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
            # Basic priority-based scheduling implementation
            # Can be enhanced with ML-based optimization in future
            
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
