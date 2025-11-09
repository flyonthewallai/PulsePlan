"""
Event/Timeblock management tools for PulsePlan agents.
Handles AI-driven event creation with explicit time slots.

ARCHITECTURE: Uses service layer (no direct Supabase access)
- TimeblockService for timeblock CRUD operations
- TagService for tag operations
- CourseService for course lookups
"""
from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime

from ..core.base import TaskTool, ToolResult, ToolError
from app.services.timeblock_service import TimeblockService, get_timeblock_service
from app.services.tag_service import TagService, get_tag_service
from app.services.course_service import CourseService, get_course_service
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class EventDatabaseTool(TaskTool):
    """Event/Timeblock CRUD operations tool for calendar management"""
    
    def __init__(
        self,
        timeblock_service: Optional[TimeblockService] = None,
        tag_service: Optional[TagService] = None,
        course_service: Optional[CourseService] = None
    ):
        super().__init__(
            name="event_database",
            description="AI-driven event/timeblock creation, reading, updating, and deletion operations"
        )
        # Dependency injection for testing/flexibility
        self.timeblock_service = timeblock_service or get_timeblock_service()
        self.tag_service = tag_service or get_tag_service()
        self.course_service = course_service or get_course_service()
    
    def get_required_tokens(self) -> List[str]:
        """Return list of required OAuth tokens for this tool"""
        return []  # No OAuth tokens required for database operations
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for event operations"""
        operation = input_data.get("operation")

        if operation not in ["create", "update", "delete", "get", "list"]:
            return False

        if operation == "create" and not input_data.get("event_data"):
            return False

        if operation in ["update", "delete", "get"]:
            if not input_data.get("event_id"):
                return False

        if operation == "update" and not input_data.get("event_data"):
            return False

        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute event operation"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data", self.name)
            
            operation = input_data["operation"]
            
            # Route to specific operation
            if operation == "create":
                result = await self.create_event(
                    event_data=input_data["event_data"],
                    context=context
                )
            elif operation == "update":
                result = await self.update_event(
                    event_id=input_data["event_id"],
                    event_data=input_data["event_data"],
                    context=context
                )
            elif operation == "delete":
                result = await self.delete_event(
                    event_id=input_data["event_id"],
                    context=context
                )
            elif operation == "get":
                result = await self.get_event(
                    event_id=input_data["event_id"],
                    context=context
                )
            elif operation == "list":
                result = await self.list_events(
                    filters=input_data.get("filters", {}),
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
    
    async def create_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create new event as a row in the timeblocks table."""
        try:
            # Validate required fields
            if not event_data.get("title"):
                raise ToolError("Event title is required", self.name)
                
            if not event_data.get("start_date"):
                raise ToolError("Event start time is required", self.name)
                
            if not event_data.get("end_date"):
                raise ToolError("Event end time is required", self.name)

            user_id = context["user_id"]
            event_id = str(uuid.uuid4())

            # Parse and validate dates
            try:
                start_date = datetime.fromisoformat(event_data["start_date"].replace("Z", "+00:00"))
                end_date = datetime.fromisoformat(event_data["end_date"].replace("Z", "+00:00"))
                
                if end_date <= start_date:
                    raise ToolError("End time must be after start time", self.name)
                    
                # Calculate duration in minutes (used only for metadata)
                duration_minutes = int((end_date - start_date).total_seconds() / 60)
                
            except (ValueError, AttributeError) as e:
                raise ToolError(f"Invalid date format: {e}", self.name)

            # Parse and validate priority
            priority = event_data.get("priority", "medium")
            if priority not in ["low", "medium", "high", "critical"]:
                priority = "medium"

            # Map kind -> timeblock.type
            kind = event_data.get("kind", "admin")
            valid_kinds = [
                "study", "assignment", "exam", "project", "hobby", "admin",
                "meeting", "class", "focus", "break"
            ]
            block_type = kind if kind in valid_kinds else "admin"

            # Process course if provided
            course_id = event_data.get("course_id")
            if event_data.get("course") and not course_id:
                # Use CourseService to find course by name
                course_id = await self.course_service.find_course_by_name(
                    event_data["course"],
                    user_id
                )

            # Process tags with intelligent selection using TagService
            tags_input = event_data.get("tags") or []
            processed_tags = await self._process_tags(tags_input, event_data["title"], user_id)

            # Prepare timeblock data
            timeblock_data = {
                "id": event_id,
                "title": event_data["title"].strip(),
                "start_time": start_date,
                "end_time": end_date,
                "type": block_type,
                "status": "scheduled",
                "source": "agent",
                "location": event_data.get("location"),
                "notes": event_data.get("description"),
                "metadata": {
                    "priority": priority,
                    "course": event_data.get("course"),
                    "course_id": course_id,
                    "tags": processed_tags,
                    "estimated_minutes": duration_minutes
                },
            }

            # Create timeblock using service
            created_event = await self.timeblock_service.create_timeblock(user_id, timeblock_data)

            # Emit websocket event for timeblock creation
            try:
                from ....core.infrastructure.websocket import websocket_manager
                event_data_ws = created_event.copy()
                event_data_ws["user_id"] = user_id
                event_data_ws["type"] = "timeblock"  # Distinguish from tasks
                
                # Use a default workflow_id for agent-created events
                workflow_id = f"agent_create_event_{user_id}"
                await websocket_manager.emit_task_created(workflow_id, event_data_ws)
            except Exception as ws_error:
                # Don't fail the event creation if websocket emission fails
                logger.warning(f"Failed to emit websocket event: {ws_error}")

            return ToolResult(
                success=True,
                data={"event": created_event, "event_id": event_id},
                metadata={"operation": "create", "user_id": user_id, "event_id": event_id}
            )

        except ServiceError as e:
            logger.error(f"Service error creating event: {e}", exc_info=True)
            raise ToolError(f"Failed to create event: {e.message}", self.name, recoverable=True)
        except Exception as e:
            logger.error(f"Failed to create event: {e}", exc_info=True)
            raise ToolError(f"Failed to create event: {e}", self.name, recoverable=True)

    async def _process_tags(self, provided_tags: List[str], title: str, user_id: str) -> List[str]:
        """Process tags with intelligent selection from predefined and user custom tags"""
        try:
            # Get all available tags using TagService
            all_tags = await self.tag_service.get_all_available_tags(user_id)
            predefined_tags = {tag["name"].lower() for tag in all_tags.get("predefined", [])}
            user_custom_tags = {tag["name"].lower() for tag in all_tags.get("user", [])}
            all_available_tags = predefined_tags | user_custom_tags

            processed_tags = []
            title_lower = title.lower()

            # If tags were explicitly provided, validate them
            for tag in provided_tags:
                tag_lower = tag.lower()
                if tag_lower in all_available_tags:
                    processed_tags.append(tag_lower)

            # Auto-suggest tags based on title if no tags provided
            if not provided_tags or len(processed_tags) < len(provided_tags):
                auto_tags = []

                # Study/Academic tags
                if any(word in title_lower for word in ["study", "homework", "assignment", "exam", "test", "quiz", "project", "research", "lecture", "class"]):
                    auto_tags.extend(["academic", "study"])
                
                # Meeting tags
                if any(word in title_lower for word in ["meeting", "call", "interview", "standup", "sync", "1:1", "one-on-one"]):
                    auto_tags.extend(["meeting", "work"])
                
                # Exercise/Health tags
                if any(word in title_lower for word in ["gym", "workout", "exercise", "fitness", "run", "walk", "yoga", "sport", "training"]):
                    auto_tags.extend(["fitness", "health"])
                
                # Social/Personal tags
                if any(word in title_lower for word in ["lunch", "dinner", "coffee", "breakfast", "hang out", "party", "birthday", "celebration"]):
                    auto_tags.extend(["personal", "social"])
                
                # Hobby tags
                if any(word in title_lower for word in ["hobby", "practice", "music", "art", "creative", "gaming", "reading"]):
                    auto_tags.append("hobby")

                # Add auto-suggested tags that aren't already in processed_tags
                for auto_tag in auto_tags:
                    if auto_tag not in processed_tags and auto_tag in all_available_tags:
                        processed_tags.append(auto_tag)

            return processed_tags[:3]  # Limit to 3 tags max

        except Exception as e:
            logger.warning(f"Error processing tags: {e}")
            return provided_tags or []

    async def update_event(self, event_id: str, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update an existing timeblock."""
        try:
            user_id = context["user_id"]
            
            # Prepare update data
            update_data: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}
            
            # Only include provided fields
            if "title" in event_data:
                update_data["title"] = event_data["title"].strip()
            if "description" in event_data:
                update_data["notes"] = event_data["description"].strip() or None
            if "start_date" in event_data:
                update_data["start_time"] = event_data["start_date"]
            if "end_date" in event_data:
                update_data["end_time"] = event_data["end_date"]
            if "kind" in event_data:
                update_data["type"] = event_data["kind"]
            if "location" in event_data:
                update_data["location"] = event_data["location"]

            # Merge metadata updates if present
            metadata_updates: Dict[str, Any] = {}
            if "priority" in event_data and event_data["priority"] in ["low", "medium", "high", "critical"]:
                metadata_updates["priority"] = event_data["priority"]
            if "course" in event_data:
                metadata_updates["course"] = event_data["course"]
            if "course_id" in event_data:
                metadata_updates["course_id"] = event_data["course_id"]
            if "tags" in event_data:
                metadata_updates["tags"] = event_data["tags"]
            if metadata_updates:
                update_data["metadata"] = metadata_updates

            # Update using service
            updated_event = await self.timeblock_service.update_timeblock(
                event_id,
                user_id,
                update_data
            )

            if not updated_event:
                raise ToolError("Event not found or update failed", self.name)

            # Emit websocket event for update
            try:
                from ....core.infrastructure.websocket import websocket_manager
                event_data_ws = updated_event.copy()
                event_data_ws["user_id"] = user_id
                event_data_ws["type"] = "timeblock"
                
                workflow_id = f"agent_update_event_{user_id}"
                await websocket_manager.emit_task_updated(workflow_id, event_data_ws)
            except Exception as ws_error:
                logger.warning(f"Failed to emit websocket event: {ws_error}")

            return ToolResult(
                success=True,
                data={"event": updated_event},
                metadata={"operation": "update", "user_id": user_id, "event_id": event_id}
            )
            
        except ServiceError as e:
            logger.error(f"Service error updating event: {e}", exc_info=True)
            raise ToolError(f"Failed to update event: {e.message}", self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to update event: {e}", self.name, recoverable=True)
    
    async def delete_event(self, event_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete a timeblock."""
        try:
            user_id = context["user_id"]
            
            # Delete using service
            deleted = await self.timeblock_service.delete_timeblock(event_id, user_id)
            
            if not deleted:
                raise ToolError("Event not found or deletion failed", self.name)
            
            # Emit websocket event for deletion
            try:
                from ....core.infrastructure.websocket import websocket_manager
                event_data_ws = {
                    "id": event_id,
                    "user_id": user_id,
                    "type": "timeblock",
                    "deleted_at": datetime.utcnow().isoformat()
                }
                
                workflow_id = f"agent_delete_event_{user_id}"
                await websocket_manager.emit_task_deleted(workflow_id, event_data_ws)
            except Exception as ws_error:
                logger.warning(f"Failed to emit websocket event: {ws_error}")
            
            return ToolResult(
                success=True,
                data={
                    "deleted_event_id": event_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "deleted_by": user_id
                },
                metadata={"operation": "delete", "user_id": user_id, "event_id": event_id}
            )
            
        except ServiceError as e:
            logger.error(f"Service error deleting event: {e}", exc_info=True)
            raise ToolError(f"Failed to delete event: {e.message}", self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to delete event: {e}", self.name, recoverable=True)
    
    async def get_event(self, event_id: str, context: Dict[str, Any]) -> ToolResult:
        """Get a specific timeblock."""
        try:
            user_id = context["user_id"]
            
            # Get using service
            event_record = await self.timeblock_service.get_timeblock(event_id, user_id)
            
            if not event_record:
                raise ToolError(f"Event with ID {event_id} not found", self.name)
            
            return ToolResult(
                success=True,
                data={"event": event_record},
                metadata={"operation": "get", "user_id": user_id}
            )
            
        except ServiceError as e:
            logger.error(f"Service error getting event: {e}", exc_info=True)
            raise ToolError(f"Failed to get event: {e.message}", self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to get event: {e}", self.name, recoverable=True)
    
    async def list_events(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List timeblocks with filters."""
        try:
            user_id = context["user_id"]
            
            # Prepare filters for service
            service_filters = {}
            if filters.get("start_after"):
                service_filters["start_after"] = filters["start_after"]
            if filters.get("end_before"):
                service_filters["end_before"] = filters["end_before"]
            if filters.get("kind"):
                service_filters["type"] = filters["kind"]
            if filters.get("priority"):
                # Note: priority is in metadata, handled by filtering logic if needed
                pass
            
            # List using service
            events = await self.timeblock_service.list_timeblocks_with_filters(user_id, service_filters)
            
            return ToolResult(
                success=True,
                data={
                    "events": events,
                    "total": len(events),
                    "filters_applied": filters
                },
                metadata={"operation": "list", "user_id": user_id}
            )
            
        except ServiceError as e:
            logger.error(f"Service error listing events: {e}", exc_info=True)
            raise ToolError(f"Failed to list events: {e.message}", self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Failed to list events: {e}", self.name, recoverable=True)

    # Implement abstract methods from TaskTool (delegate to event methods)
    async def create_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Delegate to create_event"""
        return await self.create_event(task_data, context)
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Delegate to update_event"""
        return await self.update_event(task_id, task_data, context)
    
    async def delete_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delegate to delete_event"""
        return await self.delete_event(task_id, context)
    
    async def list_tasks(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Delegate to list_events"""
        return await self.list_events(filters, context)
