"""
Todo management tools for PulsePlan agents.
Handles lightweight CRUD operations for quick task capture.
"""
from typing import Dict, Any, List, Optional
import asyncio
import uuid
from datetime import datetime

from .base import TaskTool, ToolResult, ToolError
from ...scheduler.domain import Todo, TodoPriority, TodoStatus


class TodoDatabaseTool(TaskTool):
    """Todo CRUD operations tool for lightweight task management"""
    
    def __init__(self):
        super().__init__(
            name="todo_database",
            description="Lightweight todo creation, reading, updating, and deletion operations"
        )
    
    def get_required_tokens(self) -> List[str]:
        """Return list of required OAuth tokens for this tool"""
        return []  # No OAuth tokens required for database operations
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for todo operations"""
        operation = input_data.get("operation")
        
        if operation not in ["create", "update", "delete", "get", "list", "bulk_toggle", "convert_to_task"]:
            return False
        
        if operation == "create" and not input_data.get("todo_data"):
            return False
        
        if operation in ["update", "delete", "get", "convert_to_task"] and not input_data.get("todo_id"):
            return False
        
        if operation == "update" and not input_data.get("todo_data"):
            return False
            
        if operation == "bulk_toggle" and not input_data.get("todo_ids"):
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute todo operation"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data", self.name)
            
            operation = input_data["operation"]
            
            # Route to specific operation
            if operation == "create":
                result = await self.create_todo(
                    todo_data=input_data["todo_data"],
                    context=context
                )
            elif operation == "update":
                result = await self.update_todo(
                    todo_id=input_data["todo_id"],
                    todo_data=input_data["todo_data"],
                    context=context
                )
            elif operation == "delete":
                result = await self.delete_todo(
                    todo_id=input_data["todo_id"],
                    context=context
                )
            elif operation == "get":
                result = await self.get_todo(
                    todo_id=input_data["todo_id"],
                    context=context
                )
            elif operation == "list":
                result = await self.list_todos(
                    filters=input_data.get("filters", {}),
                    context=context
                )
            elif operation == "bulk_toggle":
                result = await self.bulk_toggle_todos(
                    todo_ids=input_data["todo_ids"],
                    completed=input_data.get("completed", True),
                    context=context
                )
            elif operation == "convert_to_task":
                result = await self.convert_todo_to_task(
                    todo_id=input_data["todo_id"],
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
    
    async def create_todo(self, todo_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create new todo"""
        try:
            from ...config.supabase import get_supabase
            
            print(f"🗄️ [TODO DATABASE] Received todo_data: {todo_data}")
            
            # Validate required fields
            if not todo_data.get("title"):
                raise ToolError("Todo title is required", self.name)
            
            user_id = context["user_id"]
            todo_id = str(uuid.uuid4())
            
            # Parse and validate priority
            priority = todo_data.get("priority", "medium")
            if priority not in ["low", "medium", "high"]:
                priority = "medium"
            
            # Parse due date if provided
            due_date = None
            if todo_data.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(todo_data["due_date"].replace("Z", "+00:00"))
                except ValueError:
                    pass  # Invalid date format, leave as None
            
            # Create todo domain object
            todo = Todo(
                id=todo_id,
                user_id=user_id,
                title=todo_data["title"].strip(),
                description=todo_data.get("description", "").strip() or None,
                priority=priority,
                due_date=due_date,
                tags=todo_data.get("tags", [])
            )
            
            # Insert into Supabase database
            supabase = get_supabase()
            
            todo_record = {
                "id": todo.id,
                "user_id": todo.user_id,
                "title": todo.title,
                "description": todo.description,
                "completed": todo.completed,
                "priority": todo.priority,  # Will be cast to todo_priority enum by Supabase
                "status": todo.status,      # Will be cast to todo_status enum by Supabase
                "due_date": todo.due_date.isoformat() if todo.due_date else None,
                "tags": todo.tags,
                "created_at": todo.created_at.isoformat(),
                "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                "updated_at": todo.updated_at.isoformat()
            }
            
            result = supabase.table("todos").insert(todo_record).execute()
            
            if result.data:
                return ToolResult(
                    success=True,
                    data={"todo": todo.to_dict()},
                    metadata={"operation": "create", "user_id": user_id, "record_id": todo.id}
                )
            else:
                raise ToolError("Failed to insert todo into database", self.name)
            
        except Exception as e:
            raise ToolError(f"Failed to create todo: {e}", self.name, recoverable=True)
    
    async def update_todo(self, todo_id: str, todo_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update existing todo"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.05)  # Simulate fast database call
            
            user_id = context["user_id"]
            
            # First get existing todo (mock)
            existing_todo = Todo(
                id=todo_id,
                user_id=user_id,
                title="Existing Todo",
                created_at=datetime(2024, 1, 1)
            )
            
            # Update fields
            if "title" in todo_data:
                existing_todo.title = todo_data["title"].strip()
            if "description" in todo_data:
                existing_todo.description = todo_data["description"].strip() or None
            if "completed" in todo_data:
                if todo_data["completed"]:
                    existing_todo.mark_completed()
                else:
                    existing_todo.mark_pending()
            if "priority" in todo_data and todo_data["priority"] in ["low", "medium", "high"]:
                existing_todo.priority = todo_data["priority"]
            if "tags" in todo_data:
                existing_todo.tags = todo_data["tags"]
            if "due_date" in todo_data:
                try:
                    existing_todo.due_date = datetime.fromisoformat(todo_data["due_date"].replace("Z", "+00:00")) if todo_data["due_date"] else None
                except ValueError:
                    pass
            
            existing_todo.updated_at = datetime.now()
            
            return ToolResult(
                success=True,
                data={"todo": existing_todo.to_dict()},
                metadata={"operation": "update", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to update todo: {e}", self.name, recoverable=True)
    
    async def delete_todo(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete todo"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.05)  # Simulate fast database call
            
            user_id = context["user_id"]
            
            return ToolResult(
                success=True,
                data={
                    "deleted_todo_id": todo_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "deleted_by": user_id
                },
                metadata={"operation": "delete", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to delete todo: {e}", self.name, recoverable=True)
    
    async def get_todo(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get specific todo"""
        try:
            from ...config.supabase import get_supabase
            
            user_id = context["user_id"]
            supabase = get_supabase()
            
            # Query todo from database
            result = supabase.table("todos").select("*").eq("id", todo_id).eq("user_id", user_id).execute()
            
            if not result.data:
                raise ToolError(f"Todo with ID {todo_id} not found", self.name)
            
            todo_record = result.data[0]
            
            # Convert database record back to Todo object
            todo = Todo(
                id=todo_record["id"],
                user_id=todo_record["user_id"],
                title=todo_record["title"],
                description=todo_record["description"],
                completed=todo_record["completed"],
                priority=todo_record["priority"],
                status=todo_record["status"],
                due_date=datetime.fromisoformat(todo_record["due_date"]) if todo_record["due_date"] else None,
                tags=todo_record["tags"] or [],
                created_at=datetime.fromisoformat(todo_record["created_at"]),
                completed_at=datetime.fromisoformat(todo_record["completed_at"]) if todo_record["completed_at"] else None,
                updated_at=datetime.fromisoformat(todo_record["updated_at"])
            )
            
            return ToolResult(
                success=True,
                data={"todo": todo.to_dict()},
                metadata={"operation": "get", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to get todo: {e}", self.name, recoverable=True)
    
    async def list_todos(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List todos with filters"""
        try:
            from ...config.supabase import get_supabase
            
            user_id = context["user_id"]
            supabase = get_supabase()
            
            # Start with base query
            query = supabase.table("todos").select("*").eq("user_id", user_id)
            
            # Apply filters
            if filters.get("completed") is not None:
                query = query.eq("completed", filters["completed"])
            if filters.get("priority"):
                query = query.eq("priority", filters["priority"])
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            
            # Execute query
            result = query.order("created_at", desc=True).execute()
            
            # Convert records to Todo objects
            todos = []
            for todo_record in result.data:
                todo = Todo(
                    id=todo_record["id"],
                    user_id=todo_record["user_id"],
                    title=todo_record["title"],
                    description=todo_record["description"],
                    completed=todo_record["completed"],
                    priority=todo_record["priority"],
                    status=todo_record["status"],
                    due_date=datetime.fromisoformat(todo_record["due_date"]) if todo_record["due_date"] else None,
                    tags=todo_record["tags"] or [],
                    created_at=datetime.fromisoformat(todo_record["created_at"]),
                    completed_at=datetime.fromisoformat(todo_record["completed_at"]) if todo_record["completed_at"] else None,
                    updated_at=datetime.fromisoformat(todo_record["updated_at"])
                )
                todos.append(todo)
            
            # Apply tag filtering (client-side since Supabase doesn't handle array contains easily)
            if filters.get("tags"):
                filter_tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
                todos = [t for t in todos if any(tag in t.tags for tag in filter_tags)]
            
            # Convert to dicts
            todo_dicts = [todo.to_dict() for todo in todos]
            
            return ToolResult(
                success=True,
                data={
                    "todos": todo_dicts,
                    "total": len(todo_dicts),
                    "filters_applied": filters
                },
                metadata={"operation": "list", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to list todos: {e}", self.name, recoverable=True)
    
    async def bulk_toggle_todos(self, todo_ids: List[str], completed: bool, context: Dict[str, Any]) -> ToolResult:
        """Toggle completion status for multiple todos"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.1)  # Simulate database call
            
            user_id = context["user_id"]
            
            # Mock bulk operation
            updated_todos = []
            for todo_id in todo_ids:
                todo = Todo(
                    id=todo_id,
                    user_id=user_id,
                    title=f"Todo {todo_id}",
                    completed=completed
                )
                updated_todos.append(todo.to_dict())
            
            return ToolResult(
                success=True,
                data={
                    "updated_todos": updated_todos,
                    "total_updated": len(updated_todos),
                    "completed": completed
                },
                metadata={"operation": "bulk_toggle", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to bulk toggle todos: {e}", self.name, recoverable=True)
    
    async def convert_todo_to_task(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Convert todo to full task"""
        try:
            # TODO: Implement actual database operation with Supabase
            await asyncio.sleep(0.1)  # Simulate database call
            
            user_id = context["user_id"]
            
            # Mock conversion
            # In real implementation, would:
            # 1. Get todo from database
            # 2. Create new task with todo data
            # 3. Delete todo
            # 4. Return created task
            
            converted_task = {
                "id": str(uuid.uuid4()),
                "title": "Converted Task",
                "description": "Task converted from todo",
                "kind": "admin",
                "estimated_minutes": 60,
                "min_block_minutes": 30,
                "priority": "medium",
                "status": "pending",
                "created_by": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            return ToolResult(
                success=True,
                data={
                    "task": converted_task,
                    "original_todo_id": todo_id,
                    "converted_at": datetime.utcnow().isoformat()
                },
                metadata={"operation": "convert_to_task", "user_id": user_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to convert todo to task: {e}", self.name, recoverable=True)

    # Implement abstract methods from TaskTool (not used for todos)
    async def create_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for todo tool"""
        raise ToolError("Create task not supported by todo tool", self.name)
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for todo tool"""
        raise ToolError("Update task not supported by todo tool", self.name)
    
    async def delete_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Not implemented for todo tool"""
        raise ToolError("Delete task not supported by todo tool", self.name)
    
    async def list_tasks(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for todo tool"""
        raise ToolError("List tasks not supported by todo tool", self.name)