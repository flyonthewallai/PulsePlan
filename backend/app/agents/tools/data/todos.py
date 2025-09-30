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

logger = logging.getLogger(__name__)


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
            from ...config.supabase import get_supabase

            # Validate required fields
            if not todo_data.get("title"):
                raise ToolError("Todo title is required", self.name)

            user_id = context["user_id"]
            todo_id = str(uuid.uuid4())

            # Parse and validate priority
            priority = todo_data.get("priority", "medium")
            if priority not in ["low", "medium", "high"]:
                priority = "medium"

            # Parse due date if provided using natural language parser
            due_date = None
            if todo_data.get("due_date"):
                try:
                    # First try ISO format for backward compatibility
                    if todo_data["due_date"].count("-") >= 2:  # Looks like ISO format
                        due_date = datetime.fromisoformat(todo_data["due_date"].replace("Z", "+00:00"))
                    else:
                        # Use natural language parser
                        from ..utils.date_parser import get_date_parser
                        date_parser = get_date_parser()
                        due_date = await date_parser.parse_date(
                            todo_data["due_date"], 
                            user_id,
                            context.get("user_timezone")
                        )
                except (ValueError, Exception) as e:
                    # Log the error but continue without due date
                    print(f"Failed to parse due date '{todo_data['due_date']}': {e}")
                    pass

            # Process tags with intelligent selection
            tags_input = todo_data.get("tags") or []
            processed_tags = await self._process_tags(tags_input, todo_data["title"], user_id)

            # Create todo domain object
            todo = Todo(
                id=todo_id,
                user_id=user_id,
                title=todo_data["title"].strip(),
                description=todo_data.get("description", "").strip() if todo_data.get("description") else None,
                priority=priority,
                due_date=due_date,
                tags=processed_tags
            )

            # Insert into Supabase database
            supabase = get_supabase()

            todo_record = {
                "id": todo.id,
                "user_id": todo.user_id,
                "title": todo.title,
                "description": todo.description,
                "completed": todo.completed,
                "priority": todo.priority,
                "due_date": todo.due_date.isoformat() if todo.due_date else None,
                "estimated_minutes": todo_data.get("estimated_minutes"),
                "created_at": todo.created_at.isoformat(),
                "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                "updated_at": todo.updated_at.isoformat()
            }

            # Check if todo with same title already exists for this user (prevent accidental duplicates)
            existing_check = supabase.table("todos").select("id, title").eq("user_id", user_id).eq("title", todo.title).execute()
            if existing_check.data:
                # You might want to return the existing todo instead of creating a duplicate
                # For now, we'll continue with creation but log the warning
                pass

            # Insert into new todos table
            result = supabase.table("todos").insert(todo_record).execute()

            if result.data:
                # Update tags using junction table
                if processed_tags:
                    await self._update_todo_tags(todo.id, processed_tags, user_id)

                # Emit websocket event for todo creation
                try:
                    from ...core.infrastructure.websocket import websocket_manager
                    todo_data = todo.to_dict()
                    todo_data["user_id"] = user_id
                    todo_data["type"] = "todo"  # Distinguish from tasks
                    
                    # Use a default workflow_id for agent-created todos
                    workflow_id = f"agent_create_{user_id}"
                    await websocket_manager.emit_task_created(workflow_id, todo_data)
                except Exception as ws_error:
                    # Don't fail the todo creation if websocket emission fails
                    pass

                return ToolResult(
                    success=True,
                    data={"todo": todo.to_dict()},
                    metadata={"operation": "create", "user_id": user_id, "record_id": todo.id}
                )
            else:
                raise ToolError("Failed to insert todo into database", self.name)

        except Exception as e:
            raise ToolError(f"Failed to create todo: {e}", self.name, recoverable=True)

    async def _process_tags(self, provided_tags: List[str], title: str, user_id: str) -> List[str]:
        """Process tags with intelligent selection from predefined and user custom tags"""
        try:
            from ...config.supabase import get_supabase
            supabase = get_supabase()

            # Get predefined tags
            predefined_response = supabase.table("predefined_tags").select("name").execute()
            predefined_tags = {tag["name"].lower() for tag in predefined_response.data}

            # Get user's custom tags
            user_tags_response = supabase.table("user_tags").select("name").eq("user_id", user_id).execute()
            user_custom_tags = {tag["name"].lower() for tag in user_tags_response.data}

            # All available tags
            all_available_tags = predefined_tags | user_custom_tags

            processed_tags = []
            title_lower = title.lower()

            # If tags were explicitly provided, validate them
            for tag in provided_tags:
                tag_lower = tag.lower()
                if tag_lower in all_available_tags:
                    processed_tags.append(tag_lower)

            # Auto-suggest tags based on title if no tags provided or to supplement provided tags
            if not provided_tags or len(processed_tags) < len(provided_tags):
                auto_tags = []

                # Academic tags
                if any(word in title_lower for word in ["homework", "assignment", "study", "exam", "test", "quiz", "project", "research", "paper", "essay", "lab", "class", "lecture", "course"]):
                    auto_tags.extend(["academic", "study"])
                
                # Work tags
                if any(word in title_lower for word in ["meeting", "call", "interview", "presentation", "report", "deadline", "client", "email", "work", "job", "office"]):
                    auto_tags.extend(["work", "professional"])
                
                # Personal/Life tags
                if any(word in title_lower for word in ["shopping", "shop", "buy", "pick up", "get", "purchase", "store", "groceries"]):
                    auto_tags.extend(["personal", "shopping"])
                if any(word in title_lower for word in ["clean", "cleaning", "organize", "tidy", "laundry", "dishes", "vacuum"]):
                    auto_tags.extend(["personal", "cleaning"])
                if any(word in title_lower for word in ["gym", "workout", "exercise", "fitness", "run", "walk", "yoga", "sport"]):
                    auto_tags.extend(["personal", "fitness"])
                if any(word in title_lower for word in ["doctor", "dentist", "checkup", "appointment", "health", "medical", "therapy"]):
                    auto_tags.extend(["personal", "health"])
                if any(word in title_lower for word in ["family", "mom", "dad", "parent", "sibling", "kids", "children", "friends"]):
                    auto_tags.extend(["personal", "family"])
                
                # Creative tags
                if any(word in title_lower for word in ["write", "writing", "blog", "article", "creative", "design", "art", "music"]):
                    auto_tags.extend(["personal", "creative"])
                
                # Urgency tags
                if any(word in title_lower for word in ["urgent", "asap", "important", "critical", "priority", "emergency", "immediately"]):
                    auto_tags.append("urgent")
                
                # Time-based tags
                if any(word in title_lower for word in ["daily", "weekly", "routine", "habit"]):
                    auto_tags.append("routine")

                # Add auto-suggested tags that aren't already in processed_tags and exist in available tags
                for auto_tag in auto_tags:
                    if auto_tag not in processed_tags and auto_tag in all_available_tags:
                        processed_tags.append(auto_tag)
                        
                # If no predefined tags match, create custom tags from provided tags
                for tag in provided_tags:
                    tag_lower = tag.lower()
                    if tag_lower not in processed_tags and tag_lower not in all_available_tags:
                        # This is a new custom tag - add it to user's custom tags
                        try:
                            supabase.table("user_tags").insert({
                                "user_id": user_id,
                                "name": tag_lower,
                                "color": self._get_random_tag_color()
                            }).execute()
                            processed_tags.append(tag_lower)
                        except Exception as e:
                            print(f"Failed to create custom tag '{tag_lower}': {e}")
                            # Still add the tag even if DB insertion fails
                            processed_tags.append(tag_lower)

            return processed_tags[:3]  # Limit to 3 tags max

        except Exception as e:
            print(f"Error processing tags: {e}")
            return provided_tags or []  # Fallback to provided tags or empty list

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
            from ...config.supabase import get_supabase
            supabase = get_supabase()

            # First, delete existing tags for this todo
            supabase.table("todo_tags").delete().eq("todo_id", todo_id).execute()

            # Insert new tags
            if new_tags:
                tag_records = [
                    {"todo_id": todo_id, "tag_name": tag}
                    for tag in new_tags
                ]
                supabase.table("todo_tags").insert(tag_records).execute()

        except Exception as e:
            print(f"Error updating todo tags: {e}")
            raise

    async def _get_todo_tags(self, todo_id: str) -> List[str]:
        """Get tags for a todo from junction table"""
        try:
            from ...config.supabase import get_supabase
            supabase = get_supabase()

            result = supabase.table("todo_tags").select("tag_name").eq("todo_id", todo_id).execute()
            return [row["tag_name"] for row in result.data]

        except Exception as e:
            print(f"Error getting todo tags: {e}")
            return []

    async def update_todo(self, todo_id: str, todo_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update existing todo"""
        try:
            from app.config.database.supabase import get_supabase
            supabase = get_supabase()
            
            user_id = context["user_id"]
            
            # Prepare update data
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Only include provided fields
            if "title" in todo_data:
                update_data["title"] = todo_data["title"].strip()
            if "description" in todo_data:
                update_data["description"] = todo_data["description"].strip() or None
            if "completed" in todo_data:
                update_data["completed"] = bool(todo_data["completed"])
                if update_data["completed"]:
                    update_data["completed_at"] = datetime.utcnow().isoformat()
                else:
                    update_data["completed_at"] = None
            if "priority" in todo_data and todo_data["priority"] in ["low", "medium", "high"]:
                update_data["priority"] = todo_data["priority"]
            if "due_date" in todo_data:
                update_data["due_date"] = todo_data["due_date"]

            # Process tags if provided
            processed_tags = None
            if "tags" in todo_data:
                processed_tags = await self._process_tags(todo_data["tags"], todo_data.get("title", ""), user_id)

            # Update in database
            response = supabase.table("todos").update(update_data).eq("id", todo_id).eq("user_id", user_id).execute()

            if not response.data:
                raise Exception("Todo not found or update failed")

            # Update tags using junction table if tags were provided
            if processed_tags is not None:
                await self._update_todo_tags(todo_id, processed_tags, user_id)

            updated_todo = response.data[0]

            # Emit websocket event for todo update
            try:
                from ...core.infrastructure.websocket import websocket_manager
                todo_data_ws = updated_todo.copy()
                todo_data_ws["user_id"] = user_id
                todo_data_ws["type"] = "todo"  # Distinguish from tasks
                
                # Use a default workflow_id for agent-updated todos
                workflow_id = f"agent_update_{user_id}"
                await websocket_manager.emit_task_updated(workflow_id, todo_data_ws)
            except Exception as ws_error:
                # Don't fail the todo update if websocket emission fails
                print(f"[TODO DATABASE] Failed to emit websocket event: {ws_error}")

            return ToolResult(
                success=True,
                data={"todo": updated_todo},
                metadata={"operation": "update", "user_id": user_id, "todo_id": todo_id}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to update todo: {e}", self.name, recoverable=True)
    
    async def delete_todo(self, todo_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete todo"""
        try:
            from app.config.database.supabase import get_supabase
            supabase = get_supabase()
            
            user_id = context["user_id"]
            
            # Delete from database
            response = supabase.table("todos").delete().eq("id", todo_id).eq("user_id", user_id).execute()
            
            if not response.data:
                raise Exception("Todo not found or deletion failed")
            
            # Emit websocket event for todo deletion
            try:
                from ...core.infrastructure.websocket import websocket_manager
                todo_data_ws = {
                    "id": todo_id,
                    "user_id": user_id,
                    "type": "todo",  # Distinguish from tasks
                    "deleted_at": datetime.utcnow().isoformat()
                }
                
                # Use a default workflow_id for agent-deleted todos
                workflow_id = f"agent_delete_{user_id}"
                await websocket_manager.emit_task_deleted(workflow_id, todo_data_ws)
            except Exception as ws_error:
                # Don't fail the todo deletion if websocket emission fails
                print(f"[TODO DATABASE] Failed to emit websocket event: {ws_error}")
            
            return ToolResult(
                success=True,
                data={
                    "deleted_todo_id": todo_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "deleted_by": user_id
                },
                metadata={"operation": "delete", "user_id": user_id, "todo_id": todo_id}
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

            # Get tags for this todo from junction table
            todo_tags = await self._get_todo_tags(todo_record["id"])

            # Convert database record back to Todo object
            todo = Todo(
                id=todo_record["id"],
                user_id=todo_record["user_id"],
                title=todo_record["title"],
                description=todo_record["description"],
                completed=todo_record["completed"],
                priority=todo_record["priority"],
                due_date=datetime.fromisoformat(todo_record["due_date"]) if todo_record["due_date"] else None,
                tags=todo_tags,
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
            
            # Get todo IDs for tag filtering if needed
            todo_ids = [todo["id"] for todo in result.data]

            # Apply tag filtering using junction table
            if filters.get("tags") and todo_ids:
                filter_tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]

                # Query junction table for todos that have any of the specified tags
                tag_query = supabase.table("todo_tags").select("todo_id").in_("todo_id", todo_ids).in_("tag_name", filter_tags)
                tag_result = tag_query.execute()

                # Get unique todo IDs that have the specified tags
                filtered_todo_ids = list(set(row["todo_id"] for row in tag_result.data))

                # Filter todos to only those with matching tags
                result.data = [todo for todo in result.data if todo["id"] in filtered_todo_ids]

            # Convert records to Todo objects and populate tags from junction table
            todos = []
            for todo_record in result.data:
                # Get tags for this todo from junction table
                todo_tags = await self._get_todo_tags(todo_record["id"])

                todo = Todo(
                    id=todo_record["id"],
                    user_id=todo_record["user_id"],
                    title=todo_record["title"],
                    description=todo_record["description"],
                    completed=todo_record["completed"],
                    priority=todo_record["priority"],
                    due_date=datetime.fromisoformat(todo_record["due_date"]) if todo_record["due_date"] else None,
                    tags=todo_tags,
                    created_at=datetime.fromisoformat(todo_record["created_at"]),
                    completed_at=datetime.fromisoformat(todo_record["completed_at"]) if todo_record["completed_at"] else None,
                    updated_at=datetime.fromisoformat(todo_record["updated_at"])
                )
                todos.append(todo)
            
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
            from app.config.database.supabase import get_supabase
            supabase = get_supabase()
            
            user_id = context["user_id"]
            
            if not todo_ids:
                raise Exception("No todo IDs provided")
            
            # Prepare update data
            update_data = {
                "completed": completed,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if completed:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            else:
                update_data["completed_at"] = None
            
            # Bulk update in database
            response = supabase.table("todos").update(update_data).in_("id", todo_ids).eq("user_id", user_id).execute()
            
            updated_todos = response.data or []
            
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
            from app.config.database.supabase import get_supabase
            supabase = get_supabase()
            
            user_id = context["user_id"]
            
            # Get the todo to convert
            todo_response = supabase.table("todos").select("*").eq("id", todo_id).eq("user_id", user_id).single().execute()
            
            if not todo_response.data:
                raise Exception("Todo not found")
                
            todo = todo_response.data
            
            # Create new task from todo data
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "user_id": user_id,
                "title": todo["title"],
                "description": todo.get("description", "Task converted from todo"),
                "priority": todo.get("priority", "medium"),
                "status": "pending",
                "due_date": todo.get("due_date"),
                "tags": todo.get("tags", []),
                "estimated_hours": 1.0,  # Default estimate
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": {"converted_from_todo": todo_id}
            }
            
            # Insert task
            task_response = supabase.table("tasks").insert(task_data).execute()
            
            if not task_response.data:
                raise Exception("Failed to create task")
            
            # Delete the original todo
            delete_response = supabase.table("todos").delete().eq("id", todo_id).eq("user_id", user_id).execute()
            
            converted_task = task_response.data[0]
            
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

    async def search_todos_by_title(self, title: str, context: Dict[str, Any]) -> ToolResult:
        """Search for todos by title (case-insensitive partial match with exact match priority)"""
        try:
            from app.config.database.supabase import get_supabase
            supabase = get_supabase()

            user_id = context["user_id"]
            title_trimmed = title.strip()
            
            logger.info(f"🔍 [SEARCH-DEBUG] Searching for '{title_trimmed}' (repr: {repr(title_trimmed)}) in user {user_id}")

            # First try exact match (case-insensitive)
            exact_response = supabase.table("todos").select("*").eq("user_id", user_id).ilike("title", title_trimmed).execute()
            exact_todos = exact_response.data or []
            
            # Debug: show all todos for this user
            all_todos_response = supabase.table("todos").select("*").eq("user_id", user_id).execute()
            all_todos = all_todos_response.data or []
            logger.info(f"🔍 [SEARCH-DEBUG] All todos for user: {[(todo['title'], repr(todo['title'])) for todo in all_todos]}")

            if exact_todos:
                # Found exact match(es)
                todos = exact_todos
                logger.info(f"🔍 [SEARCH-DEBUG] Found exact match: {len(todos)}")
            else:
                # Fall back to partial match
                logger.info(f"🔍 [SEARCH-DEBUG] No exact match, trying partial match")
                partial_response = supabase.table("todos").select("*").eq("user_id", user_id).ilike("title", f"%{title_trimmed}%").execute()
                todos = partial_response.data or []
                logger.info(f"🔍 [SEARCH-DEBUG] Partial match found: {len(todos)} todos")

            return ToolResult(
                success=True,
                data={
                    "todos": todos,
                    "total": len(todos),
                    "search_term": title_trimmed,
                    "match_type": "exact" if exact_todos else "partial"
                },
                metadata={"operation": "search_by_title", "user_id": user_id, "search_term": title_trimmed}
            )

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
