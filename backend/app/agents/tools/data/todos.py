"""
Todo management tools for PulsePlan agents.
Handles lightweight CRUD operations for quick task capture.
"""
from typing import Dict, Any, List, Optional
import asyncio
import uuid
import logging
from datetime import datetime

from ..core.base import TaskTool, ToolResult, ToolError
from app.scheduler.core.domain import Todo, TodoPriority, TodoStatus
from app.services.todo_service import TodoService
from app.services.tag_service import TagService
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TodoDatabaseTool(TaskTool):
    """Todo CRUD operations tool for lightweight task management"""

    def __init__(self, todo_service: TodoService = None, tag_service: TagService = None):
        super().__init__(
            name="todo_database",
            description="Lightweight todo creation, reading, updating, and deletion operations"
        )
        self.todo_service = todo_service or TodoService()
        self.tag_service = tag_service or TagService()
    
    def get_required_tokens(self) -> List[str]:
        """Return list of required OAuth tokens for this tool"""
        return []  # No OAuth tokens required for database operations
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for todo operations"""
        operation = input_data.get("operation")

        if operation not in ["create", "update", "delete", "get", "list", "bulk_toggle", "convert_to_task", "search_by_title"]:
            return False

        if operation == "create" and not input_data.get("todo_data"):
            return False

        if operation in ["update", "delete", "get", "convert_to_task"]:
            # Allow either todo_id or title for these operations
            if not input_data.get("todo_id") and not input_data.get("title"):
                return False

        if operation == "update" and not input_data.get("todo_data"):
            return False

        if operation == "bulk_toggle" and not input_data.get("todo_ids"):
            return False

        if operation == "search_by_title" and not input_data.get("title"):
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
                todo_id = input_data.get("todo_id")
                if not todo_id and input_data.get("title"):
                    # Search for todo by title first
                    title = input_data["title"]
                    logger.info(f"🔍 [TODO-SEARCH] Searching for todo with title: '{title}'")
                    logger.info(f"🔍 [TODO-SEARCH] Title length: {len(title)}, repr: {repr(title)}")
                    search_result = await self.search_todos_by_title(title, context)
                    logger.info(f"🔍 [TODO-SEARCH] Search result: success={search_result.success}, found={len(search_result.data.get('todos', []))} todos")
                    
                    if search_result.success and search_result.data.get("todos"):
                        if len(search_result.data["todos"]) > 1:
                            # Multiple matches found - list them for user
                            todo_titles = [todo["title"] for todo in search_result.data["todos"]]
                            logger.warning(f"🔍 [TODO-SEARCH] Multiple todos found: {todo_titles}")
                            raise ToolError(f"Multiple todos found with similar titles: {', '.join(todo_titles)}. Please be more specific.", self.name)
                        todo_id = search_result.data["todos"][0]["id"]
                        logger.info(f"🔍 [TODO-SEARCH] Found todo ID: {todo_id}")
                    else:
                        logger.error(f"🔍 [TODO-SEARCH] No todo found with title '{input_data['title']}'")
                        raise ToolError(f"No todo found with title '{input_data['title']}'. Check the exact title and try again.", self.name)

                logger.info(f"🔧 [TODO-UPDATE] Updating todo {todo_id} with data: {input_data['todo_data']}")
                result = await self.update_todo(
                    todo_id=todo_id,
                    todo_data=input_data["todo_data"],
                    context=context
                )
                logger.info(f"🔧 [TODO-UPDATE] Update result: success={result.success}, error={result.error if not result.success else 'None'}")
            elif operation == "delete":
                todo_id = input_data.get("todo_id")
                if not todo_id and input_data.get("title"):
                    # Search for todo by title first
                    search_result = await self.search_todos_by_title(input_data["title"], context)
                    if search_result.success and search_result.data.get("todos"):
                        if len(search_result.data["todos"]) > 1:
                            # Multiple matches found - list them for user
                            todo_titles = [todo["title"] for todo in search_result.data["todos"]]
                            raise ToolError(f"Multiple todos found with similar titles: {', '.join(todo_titles)}. Please be more specific.", self.name)
                        todo_id = search_result.data["todos"][0]["id"]
                    else:
                        raise ToolError(f"No todo found with title '{input_data['title']}'. Check the exact title and try again.", self.name)

                result = await self.delete_todo(
                    todo_id=todo_id,
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
            elif operation == "search_by_title":
                result = await self.search_todos_by_title(
                    title=input_data["title"],
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
            # Validate required fields
            if not todo_data.get("title"):
                raise ToolError("Todo title is required", self.name)

            user_id = context["user_id"]

            # Use TodoService to create
            todo = await self.todo_service.create_todo(user_id, todo_data)

            # Emit websocket event for todo creation
            try:
                from ...core.infrastructure.websocket import websocket_manager
                todo_ws_data = todo.copy()
                todo_ws_data["user_id"] = user_id
                todo_ws_data["type"] = "todo"  # Distinguish from tasks
                
                # Use a default workflow_id for agent-created todos
                workflow_id = f"agent_create_{user_id}"
                await websocket_manager.emit_task_created(workflow_id, todo_ws_data)
            except Exception as ws_error:
                # Don't fail the todo creation if websocket emission fails
                logger.warning(f"Failed to emit websocket event: {ws_error}")

            return ToolResult(
                success=True,
                data={"todo": todo, "todo_id": todo["id"]},
                metadata={"operation": "create", "user_id": user_id, "todo_id": todo["id"]}
            )

        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to create todo: {e}", self.name, recoverable=True)

    async def _process_tags(self, provided_tags: List[str], title: str, user_id: str) -> List[str]:
        """Process tags with intelligent selection from predefined and user custom tags"""
        try:
            # Use TagService for all tag processing - RULES.md Section 1.4
            processed_tags = await self.tag_service.process_tags_for_todo(
                provided_tags=provided_tags,
                title=title,
                user_id=user_id
            )
            return processed_tags

        except Exception as e:
            logger.error(f"Error processing tags: {e}", exc_info=True)
            return provided_tags[:3] if provided_tags else []  # Fallback to provided tags or empty list

    def _get_random_tag_color(self) -> str:
        """Get a random color for new custom tags"""
        colors = [
            "#3B82F6",  # Blue
            "#10B981",  # Green
            "#F59E0B",  # Yellow
            "#EF4444",  # Red
            "#8B5CF6",  # Purple
            "#06B6D4",  # Cyan
            "#F97316",  # Orange
            "#84CC16",  # Lime
            "#EC4899",  # Pink
            "#6B7280"   # Gray
        ]
        import random
        return random.choice(colors)

    async def _update_todo_tags(self, todo_id: str, new_tags: List[str], user_id: str) -> None:
        """Update tags for a todo using junction table"""
        try:
            # Use TagService to update todo tags - RULES.md Section 1.4
            await self.tag_service.update_todo_tags(todo_id, new_tags)

        except Exception as e:
            logger.error(f"Error updating todo tags: {e}", exc_info=True)
            raise

    async def _get_todo_tags(self, todo_id: str) -> List[str]:
        """Get tags for a todo from junction table"""
        try:
            # Use TagService to get todo tags - RULES.md Section 1.4
            return await self.tag_service.get_todo_tags(todo_id)

        except Exception as e:
            logger.error(f"Error getting todo tags: {e}", exc_info=True)
            return []

    async def update_todo(self, todo_id: str, todo_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update existing todo"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService to update
            updated_todo = await self.todo_service.update_todo(todo_id, user_id, todo_data)

            # Emit websocket event for todo update
            try:
                from ...core.infrastructure.websocket import websocket_manager
                todo_ws_data = updated_todo.copy()
                todo_ws_data["user_id"] = user_id
                todo_ws_data["type"] = "todo"  # Distinguish from tasks
                
                # Use a default workflow_id for agent-updated todos
                workflow_id = f"agent_update_{user_id}"
                await websocket_manager.emit_task_updated(workflow_id, todo_ws_data)
            except Exception as ws_error:
                # Don't fail the todo update if websocket emission fails
                logger.warning(f"Failed to emit websocket event: {ws_error}")

            return ToolResult(
                success=True,
                data={"todo": updated_todo},
                metadata={"operation": "update", "user_id": user_id, "todo_id": todo_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to update todo: {e}", self.name, recoverable=True)
    
    async def delete_todo(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete todo"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService to delete
            result = await self.todo_service.delete_todo(todo_id, user_id)
            
            # Emit websocket event for todo deletion
            try:
                from ...core.infrastructure.websocket import websocket_manager
                todo_ws_data = {
                    "id": todo_id,
                    "user_id": user_id,
                    "type": "todo",  # Distinguish from tasks
                    "deleted_at": result["deleted_at"]
                }
                
                # Use a default workflow_id for agent-deleted todos
                workflow_id = f"agent_delete_{user_id}"
                await websocket_manager.emit_task_deleted(workflow_id, todo_ws_data)
            except Exception as ws_error:
                # Don't fail the todo deletion if websocket emission fails
                logger.warning(f"Failed to emit websocket event: {ws_error}")
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "delete", "user_id": user_id, "todo_id": todo_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to delete todo: {e}", self.name, recoverable=True)
    
    async def get_todo(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get specific todo"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService to get todo
            todo = await self.todo_service.get_todo(todo_id, user_id)
            
            if not todo:
                raise ToolError(f"Todo with ID {todo_id} not found", self.name)
            
            return ToolResult(
                success=True,
                data={"todo": todo},
                metadata={"operation": "get", "user_id": user_id}
            )
            
        except ToolError:
            raise
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to get todo: {e}", self.name, recoverable=True)
    
    async def list_todos(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List todos with filters"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService to list todos
            result = await self.todo_service.list_todos(user_id, filters)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "list", "user_id": user_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to list todos: {e}", self.name, recoverable=True)
    
    async def bulk_toggle_todos(self, todo_ids: List[str], completed: bool, context: Dict[str, Any]) -> ToolResult:
        """Toggle completion status for multiple todos"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService for bulk toggle
            result = await self.todo_service.bulk_toggle_todos(todo_ids, user_id, completed)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "bulk_toggle", "user_id": user_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to bulk toggle todos: {e}", self.name, recoverable=True)
    
    async def convert_todo_to_task(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Convert todo to full task"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService to convert
            result = await self.todo_service.convert_to_task(todo_id, user_id)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "convert_to_task", "user_id": user_id}
            )
            
        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to convert todo to task: {e}", self.name, recoverable=True)

    async def search_todos_by_title(self, title: str, context: Dict[str, Any]) -> ToolResult:
        """Search for todos by title (case-insensitive partial match with exact match priority)"""
        try:
            user_id = context["user_id"]
            
            # Use TodoService to search
            result = await self.todo_service.search_by_title(user_id, title)

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "search_by_title", "user_id": user_id, "search_term": title.strip()}
            )

        except ServiceError as e:
            raise ToolError(str(e), self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to search todos by title: {e}", self.name, recoverable=True)

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
