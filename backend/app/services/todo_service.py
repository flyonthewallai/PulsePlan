"""
Todo Service
Business logic layer for todo operations
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.database.repositories.task_repositories import (
    TodoRepository,
    TodoTagRepository,
    PredefinedTagRepository,
    UserTagRepository
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TodoService:
    """Service for todo business logic"""

    def __init__(
        self,
        repository: TodoRepository = None,
        tag_repo: TodoTagRepository = None,
        predefined_tag_repo: PredefinedTagRepository = None,
        user_tag_repo: UserTagRepository = None
    ):
        """Initialize service with repositories"""
        self.repo = repository or TodoRepository()
        self.tag_repo = tag_repo or TodoTagRepository()
        self.predefined_tag_repo = predefined_tag_repo or PredefinedTagRepository()
        self.user_tag_repo = user_tag_repo or UserTagRepository()

    async def create_todo(
        self,
        user_id: str,
        todo_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new todo

        Args:
            user_id: User ID
            todo_data: Todo data

        Returns:
            Created todo dictionary

        Raises:
            ServiceError: If validation or creation fails
        """
        try:
            # Validate required fields
            if not todo_data.get("title"):
                raise ServiceError("Todo title is required", "todo", "create")

            # Validate priority
            priority = todo_data.get("priority", "medium")
            if priority not in ["low", "medium", "high"]:
                priority = "medium"

            # Process tags
            tags_input = todo_data.get("tags") or []
            processed_tags = await self._process_tags(tags_input, todo_data["title"], user_id)

            # Create todo record
            todo_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": todo_data["title"].strip(),
                "description": todo_data.get("description", "").strip() or None,
                "completed": False,
                "priority": priority,
                "due_date": todo_data.get("due_date"),
                "estimated_minutes": todo_data.get("estimated_minutes"),
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Create todo in database
            created_todo = await self.repo.create(todo_record)

            # Update tags using junction table
            if processed_tags:
                await self.tag_repo.update_tags_for_todo(created_todo["id"], processed_tags)

            # Add tags to response
            created_todo["tags"] = processed_tags

            logger.info(f"Created todo {created_todo['id']} for user {user_id}")
            return created_todo

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error creating todo: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "create")

    async def get_todo(self, todo_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific todo

        Args:
            todo_id: Todo ID
            user_id: User ID

        Returns:
            Todo dictionary or None if not found

        Raises:
            ServiceError: If retrieval fails
        """
        try:
            todo = await self.repo.get_by_id_and_user(todo_id, user_id)

            if not todo:
                return None

            # Get tags from junction table
            tags = await self.tag_repo.get_tags_for_todo(todo_id)
            todo["tags"] = tags

            return todo

        except Exception as e:
            logger.error(f"Error getting todo {todo_id}: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "get")

    async def list_todos(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List todos with optional filters

        Args:
            user_id: User ID
            filters: Optional filters

        Returns:
            Dictionary with todos list and metadata

        Raises:
            ServiceError: If listing fails
        """
        try:
            # Get todos from database
            todos = await self.repo.get_by_user(user_id, filters)

            # Apply tag filtering if specified
            if filters and filters.get("tags"):
                filter_tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
                todo_ids = [todo["id"] for todo in todos]

                if todo_ids:
                    # Get todos that match the tag filter
                    filtered_todo_ids = await self.tag_repo.get_todos_by_tags(filter_tags, todo_ids)
                    # Filter todos to only those with matching tags
                    todos = [todo for todo in todos if todo["id"] in filtered_todo_ids]

            # Get tags for each todo
            for todo in todos:
                tags = await self.tag_repo.get_tags_for_todo(todo["id"])
                todo["tags"] = tags

            return {
                "todos": todos,
                "total": len(todos),
                "filters_applied": filters or {}
            }

        except Exception as e:
            logger.error(f"Error listing todos: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "list")

    async def update_todo(
        self,
        todo_id: str,
        user_id: str,
        todo_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a todo

        Args:
            todo_id: Todo ID
            user_id: User ID
            todo_data: Update data

        Returns:
            Updated todo dictionary

        Raises:
            ServiceError: If validation or update fails
        """
        try:
            # Prepare update data
            update_data = {}

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
            if "estimated_minutes" in todo_data:
                update_data["estimated_minutes"] = todo_data["estimated_minutes"]

            # Update in database
            updated_todo = await self.repo.update_by_user(todo_id, user_id, update_data)

            if not updated_todo:
                raise ServiceError("Todo not found", "todo", "update")

            # Process tags if provided
            if "tags" in todo_data:
                title = todo_data.get("title", updated_todo.get("title", ""))
                processed_tags = await self._process_tags(todo_data["tags"], title, user_id)
                await self.tag_repo.update_tags_for_todo(todo_id, processed_tags)
                updated_todo["tags"] = processed_tags
            else:
                # Get existing tags
                tags = await self.tag_repo.get_tags_for_todo(todo_id)
                updated_todo["tags"] = tags

            logger.info(f"Updated todo {todo_id} for user {user_id}")
            return updated_todo

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error updating todo {todo_id}: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "update")

    async def delete_todo(self, todo_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete a todo

        Args:
            todo_id: Todo ID
            user_id: User ID

        Returns:
            Deletion confirmation dictionary

        Raises:
            ServiceError: If deletion fails
        """
        try:
            deleted = await self.repo.delete_by_user(todo_id, user_id)

            if not deleted:
                raise ServiceError("Todo not found", "todo", "delete")

            logger.info(f"Deleted todo {todo_id} for user {user_id}")

            return {
                "deleted_todo_id": todo_id,
                "deleted_at": datetime.utcnow().isoformat(),
                "deleted_by": user_id
            }

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error deleting todo {todo_id}: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "delete")

    async def bulk_toggle_todos(
        self,
        todo_ids: List[str],
        user_id: str,
        completed: bool = True
    ) -> Dict[str, Any]:
        """
        Bulk toggle completion status for multiple todos

        Args:
            todo_ids: List of todo IDs
            user_id: User ID
            completed: Completion status to set

        Returns:
            Dictionary with updated todos

        Raises:
            ServiceError: If bulk update fails
        """
        try:
            if not todo_ids:
                raise ServiceError("No todo IDs provided", "todo", "bulk_toggle")

            # Prepare update data
            update_data = {
                "completed": completed
            }

            if completed:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            else:
                update_data["completed_at"] = None

            # Bulk update in database
            updated_todos = await self.repo.bulk_update(todo_ids, user_id, update_data)

            logger.info(f"Bulk toggled {len(updated_todos)} todos for user {user_id}")

            return {
                "updated_todos": updated_todos,
                "total_updated": len(updated_todos),
                "completed": completed
            }

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error bulk toggling todos: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "bulk_toggle")

    async def search_by_title(
        self,
        user_id: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Search todos by title

        Args:
            user_id: User ID
            title: Title to search for

        Returns:
            Dictionary with search results

        Raises:
            ServiceError: If search fails
        """
        try:
            # Try exact match first
            exact_todos = await self.repo.search_by_title(user_id, title, exact_match=True)

            if exact_todos:
                todos = exact_todos
                match_type = "exact"
            else:
                # Fall back to partial match
                todos = await self.repo.search_by_title(user_id, title, exact_match=False)
                match_type = "partial"

            # Get tags for each todo
            for todo in todos:
                tags = await self.tag_repo.get_tags_for_todo(todo["id"])
                todo["tags"] = tags

            return {
                "todos": todos,
                "total": len(todos),
                "search_term": title.strip(),
                "match_type": match_type
            }

        except Exception as e:
            logger.error(f"Error searching todos by title: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "search_by_title")

    async def convert_to_task(self, todo_id: str, user_id: str) -> Dict[str, Any]:
        """
        Convert a todo to a full task

        Args:
            todo_id: Todo ID
            user_id: User ID

        Returns:
            Dictionary with created task and conversion info

        Raises:
            ServiceError: If conversion fails
        """
        try:
            # Get the todo to convert
            todo = await self.get_todo(todo_id, user_id)

            if not todo:
                raise ServiceError("Todo not found", "todo", "convert_to_task")

            # Import TaskService to create task
            from app.services.task_service import TaskService
            task_service = TaskService()

            # Create task from todo data
            task_data = {
                "title": todo["title"],
                "description": todo.get("description") or "Task converted from todo",
                "priority": todo.get("priority", "medium"),
                "status": "pending",
                "due_date": todo.get("due_date"),
                "tags": todo.get("tags", []),
                "estimated_minutes": todo.get("estimated_minutes", 60),
                "task_type": "assignment"
            }

            created_task = await task_service.create_task(user_id, task_data)

            # Delete the original todo
            await self.delete_todo(todo_id, user_id)

            logger.info(f"Converted todo {todo_id} to task {created_task['id']}")

            return {
                "task": created_task,
                "original_todo_id": todo_id,
                "converted_at": datetime.utcnow().isoformat()
            }

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error converting todo {todo_id} to task: {e}", exc_info=True)
            raise ServiceError(str(e), "todo", "convert_to_task")

    async def _process_tags(
        self,
        provided_tags: List[str],
        title: str,
        user_id: str
    ) -> List[str]:
        """
        Process tags with intelligent selection from predefined and user custom tags

        Args:
            provided_tags: List of tag names provided by user
            title: Todo title for auto-suggestion
            user_id: User ID

        Returns:
            List of processed tag names (max 3)

        Raises:
            ServiceError: If tag processing fails
        """
        try:
            # Get predefined tags
            predefined_tags = await self.predefined_tag_repo.get_all()
            predefined_tag_names = {tag["name"].lower() for tag in predefined_tags}

            # Get user's custom tags
            user_tags = await self.user_tag_repo.get_by_user(user_id)
            user_tag_names = {tag["name"].lower() for tag in user_tags}

            # All available tags
            all_available_tags = predefined_tag_names | user_tag_names

            processed_tags = []
            title_lower = title.lower()

            # If tags were explicitly provided, validate them
            for tag in provided_tags:
                tag_lower = tag.lower()
                if tag_lower in all_available_tags:
                    processed_tags.append(tag_lower)

            # Auto-suggest tags based on title
            auto_tags = self._auto_suggest_tags(title_lower)

            # Add auto-suggested tags that aren't already in processed_tags
            for auto_tag in auto_tags:
                if auto_tag not in processed_tags and auto_tag in all_available_tags:
                    processed_tags.append(auto_tag)

            # Create custom tags for any provided tags that don't exist
            for tag in provided_tags:
                tag_lower = tag.lower()
                if tag_lower not in processed_tags and tag_lower not in all_available_tags:
                    # This is a new custom tag
                    try:
                        await self.user_tag_repo.create({
                            "user_id": user_id,
                            "name": tag_lower,
                            "color": self._get_random_tag_color()
                        })
                        processed_tags.append(tag_lower)
                    except Exception as e:
                        logger.warning(f"Failed to create custom tag '{tag_lower}': {e}")
                        # Still add the tag even if DB insertion fails
                        processed_tags.append(tag_lower)

            # Limit to 3 tags max
            return processed_tags[:3]

        except Exception as e:
            logger.error(f"Error processing tags: {e}", exc_info=True)
            # Fallback to provided tags or empty list
            return provided_tags[:3] if provided_tags else []

    def _auto_suggest_tags(self, title_lower: str) -> List[str]:
        """Auto-suggest tags based on title keywords"""
        auto_tags = []

        # Academic tags
        if any(word in title_lower for word in [
            "homework", "assignment", "study", "exam", "test", "quiz",
            "project", "research", "paper", "essay", "lab", "class", "lecture", "course"
        ]):
            auto_tags.extend(["academic", "study"])

        # Work tags
        if any(word in title_lower for word in [
            "meeting", "call", "interview", "presentation", "report",
            "deadline", "client", "email", "work", "job", "office"
        ]):
            auto_tags.extend(["work", "professional"])

        # Personal/Life tags
        if any(word in title_lower for word in [
            "shopping", "shop", "buy", "pick up", "get", "purchase", "store", "groceries"
        ]):
            auto_tags.extend(["personal", "shopping"])
        if any(word in title_lower for word in [
            "clean", "cleaning", "organize", "tidy", "laundry", "dishes", "vacuum"
        ]):
            auto_tags.extend(["personal", "cleaning"])
        if any(word in title_lower for word in [
            "gym", "workout", "exercise", "fitness", "run", "walk", "yoga", "sport"
        ]):
            auto_tags.extend(["personal", "fitness"])
        if any(word in title_lower for word in [
            "doctor", "dentist", "checkup", "appointment", "health", "medical", "therapy"
        ]):
            auto_tags.extend(["personal", "health"])
        if any(word in title_lower for word in [
            "family", "mom", "dad", "parent", "sibling", "kids", "children", "friends"
        ]):
            auto_tags.extend(["personal", "family"])

        # Creative tags
        if any(word in title_lower for word in [
            "write", "writing", "blog", "article", "creative", "design", "art", "music"
        ]):
            auto_tags.extend(["personal", "creative"])

        # Urgency tags
        if any(word in title_lower for word in [
            "urgent", "asap", "important", "critical", "priority", "emergency", "immediately"
        ]):
            auto_tags.append("urgent")

        # Time-based tags
        if any(word in title_lower for word in ["daily", "weekly", "routine", "habit"]):
            auto_tags.append("routine")

        return auto_tags

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


def get_todo_service() -> TodoService:
    """Dependency injection helper for TodoService"""
    return TodoService()

