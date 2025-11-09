"""
Agent Operations Module
Handles direct CRUD operations and workflow execution
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.agents.core.orchestration.agent_task_manager import get_agent_task_manager
from app.agents.core.orchestration.intent_processor import ActionType
from app.agents.core.conversation.conversation_manager import get_conversation_manager

logger = logging.getLogger(__name__)


async def _cancel_pending_gates_for_action(action_id_str: str):
    """Cancel any pending gates associated with an action to prevent continuation loops."""
    try:
        from app.database.repositories.integration_repositories import create_nlu_repository
        nlu_repo = create_nlu_repository()

        # Find and cancel any pending gates for this action
        response = nlu_repo.supabase.table("pending_gates")\
            .select("gate_token")\
            .eq("action_id", action_id_str)\
            .is_("confirmed_at", "null")\
            .is_("cancelled_at", "null")\
            .execute()

        if response.data and len(response.data) > 0:
            for gate in response.data:
                await nlu_repo.cancel_gate(gate["gate_token"])
                logger.info(f"Cancelled pending gate {gate['gate_token']} for action {action_id_str}")
    except Exception as gate_error:
        logger.error(f"Failed to cancel pending gate: {gate_error}")


async def execute_crud_operation_direct(
    user_id: str,
    conversation_id: str,
    intent_result,
    original_query: str
):
    """Execute simple CRUD operations directly without workflow tasks"""
    try:
        task_manager = get_agent_task_manager()
        
        if intent_result.action == ActionType.CREATE_TASK:
            await _execute_task_creation_direct(user_id, conversation_id, intent_result, original_query, task_manager)
        elif intent_result.action == ActionType.DELETE_TASK:
            await _execute_task_deletion_direct(user_id, conversation_id, intent_result, task_manager)
        elif intent_result.action == ActionType.UPDATE_TASK:
            await _execute_task_update_direct(user_id, conversation_id, intent_result, original_query, task_manager)
        elif intent_result.action == ActionType.COMPLETE_TASK:
            await _execute_task_completion_direct(user_id, conversation_id, intent_result, task_manager)
        
    except Exception as e:
        logger.error(f"CRUD operation failed: {e}")

        # Cancel any pending gates associated with this action to prevent infinite loops
        if hasattr(intent_result, 'metadata') and intent_result.metadata.get('action_id'):
            await _cancel_pending_gates_for_action(intent_result.metadata.get('action_id'))

        # Create failure card with actual task title if available
        task_title = "task"
        if hasattr(intent_result, 'task_info') and intent_result.task_info and intent_result.task_info.task_title:
            task_title = intent_result.task_info.task_title

        await task_manager.create_crud_failure_card(
            user_id=user_id,
            operation="failed",
            entity_type="task",
            entity_title=task_title,
            conversation_id=conversation_id
        )


async def _execute_task_creation_direct(user_id: str, conversation_id: str, intent_result, original_query: str, task_manager):
    """Execute task creation directly"""
    from app.agents.tools.data.tasks import TaskDatabaseTool
    task_tool = TaskDatabaseTool()
    
    # Check for batch task creation
    batch_tasks = intent_result.metadata.get("batch_tasks", [])
    
    if batch_tasks:
        # Handle batch task creation
        created_tasks = []
        failed_tasks = []
        
        for task_info in batch_tasks:
            result = await task_tool.execute(
                input_data={
                    "operation": "create",
                    "task_data": {
                        "title": task_info.task_title,
                        "description": task_info.task_description,
                        "due_date": task_info.due_date,
                        "priority": task_info.priority,
                        "tags": task_info.tags,
                        "status": "pending"
                    }
                },
                context={"user_id": user_id}
            )
            
            if result.success:
                created_tasks.append(task_info.task_title)
            else:
                failed_tasks.append(task_info.task_title)
        
        # Create success card for batch operation
        if created_tasks:
            entity_title = created_tasks[0] if len(created_tasks) == 1 else f"{len(created_tasks)} tasks"
            
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="created",
                entity_type="task",
                entity_title=entity_title,
                conversation_id=conversation_id,
                details={
                    "created_tasks": created_tasks,
                    "failed_tasks": failed_tasks,
                    "total_requested": len(batch_tasks)
                }
            )
        else:
            # All tasks failed
            await task_manager.create_crud_failure_card(
                user_id=user_id,
                operation="failed",
                entity_type="task",
                entity_title="Task Creation",
                conversation_id=conversation_id
            )
    else:
        # Single task creation
        if not intent_result.task_info:
            # Cancel pending gates before returning to prevent continuation loops
            if hasattr(intent_result, 'metadata') and intent_result.metadata.get('action_id'):
                await _cancel_pending_gates_for_action(intent_result.metadata.get('action_id'))

            await task_manager.create_crud_failure_card(
                user_id=user_id,
                operation="failed",
                entity_type="task",
                entity_title="Task Creation",
                conversation_id=conversation_id
            )
            return
        
        # Create task
        result = await task_tool.execute(
            input_data={
                "operation": "create",
                "task_data": {
                    "title": intent_result.task_info.task_title,
                    "description": intent_result.task_info.task_description,
                    "due_date": intent_result.task_info.due_date,
                    "priority": intent_result.task_info.priority,
                    "tags": intent_result.task_info.tags,
                    "status": "pending"
                }
            },
            context={"user_id": user_id}
        )
        
        if result.success:
            # LLM now returns structured ISO dates, but we need to validate them
            due_date_iso = intent_result.task_info.due_date
            if due_date_iso:
                logger.info(f"🔍 [STRUCTURED-DATE] Received ISO date: '{due_date_iso}'")
                # Validate the date
                validated_date = await _validate_llm_date(due_date_iso, user_id, original_query)
                if validated_date != due_date_iso:
                    logger.warning(f"🔍 [DATE-VALIDATION] LLM date corrected: '{due_date_iso}' → '{validated_date}'")
                    due_date_iso = validated_date
            
            # Create success card with task details
            success_card_details = {
                "due_date": due_date_iso,
                "tags": intent_result.task_info.tags,
                "priority": intent_result.task_info.priority,
                "description": intent_result.task_info.task_description
            }
            
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="created",
                entity_type="task",
                entity_title=intent_result.task_info.task_title,
                entity_id=result.data.get("id") if result.data else None,
                details=success_card_details,
                conversation_id=conversation_id
            )
        else:
            # Cancel pending gates before creating failure card
            if hasattr(intent_result, 'metadata') and intent_result.metadata.get('action_id'):
                await _cancel_pending_gates_for_action(intent_result.metadata.get('action_id'))

            # Create failure card
            await task_manager.create_crud_failure_card(
                user_id=user_id,
                operation="failed",
                entity_type="task",
                entity_title=intent_result.task_info.task_title,
                conversation_id=conversation_id
            )


async def _execute_task_deletion_direct(user_id: str, conversation_id: str, intent_result, task_manager):
    """Execute todo deletion directly (DELETE_TASK should operate on todos, not tasks)"""
    from app.agents.tools.data.todos import TodoDatabaseTool
    todo_tool = TodoDatabaseTool()
    
    # Check for batch task deletion
    batch_tasks = intent_result.metadata.get("batch_tasks", [])
    
    if batch_tasks:
        # Handle batch todo deletion
        todo_titles = [task_info.task_title for task_info in batch_tasks]
        deleted_todos = []
        failed_todos = []
        
        # Delete each todo individually since TodoDatabaseTool doesn't have batch delete
        for todo_title in todo_titles:
            try:
                result = await todo_tool.execute(
                    input_data={
                        "operation": "delete",
                        "title": todo_title
                    },
                    context={"user_id": user_id}
                )
                if result.success:
                    deleted_todos.append(todo_title)
                else:
                    failed_todos.append(todo_title)
            except Exception as e:
                logger.error(f"Failed to delete todo {todo_title}: {e}")
                failed_todos.append(todo_title)
        
        # Create success card for batch operation
        if deleted_todos:
            entity_title = deleted_todos[0] if len(deleted_todos) == 1 else f"{len(deleted_todos)} todos"
            
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="deleted",
                entity_type="todo",
                entity_title=entity_title,
                conversation_id=conversation_id,
                details={
                    "deleted_todos": deleted_todos,
                    "failed_todos": failed_todos,
                    "total_requested": len(batch_tasks)
                }
            )
        else:
            # All todos failed
            await task_manager.create_crud_failure_card(
                user_id=user_id,
                operation="failed",
                entity_type="todo",
                entity_title="Todo Deletion",
                conversation_id=conversation_id
            )
    else:
        # Single todo deletion
        if not intent_result.task_info:
            await task_manager.create_crud_failure_card(
                user_id=user_id,
                operation="failed",
                entity_type="todo",
                entity_title="Todo Deletion",
                conversation_id=conversation_id
            )
            return
        
        # Delete single todo
        result = await todo_tool.execute(
            input_data={
                "operation": "delete",
                "title": intent_result.task_info.task_title
            },
            context={"user_id": user_id}
        )
        
        if result.success:
            # Create success card
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="deleted",
                entity_type="todo",
                entity_title=intent_result.task_info.task_title,
                conversation_id=conversation_id
            )
        else:
            # Create failure card
            await task_manager.create_crud_failure_card(
                user_id=user_id,
                operation="failed",
                entity_type="todo",
                entity_title=f"Todo '{intent_result.task_info.task_title}' not found",
                conversation_id=conversation_id,
                details={
                    "error": f"No todo found with title '{intent_result.task_info.task_title}'. Please check the todo name.",
                    "suggested_action": f"Check existing todo names or create a new todo"
                }
            )


async def _execute_task_update_direct(user_id: str, conversation_id: str, intent_result, original_query: str, task_manager):
    """Execute todo update directly (UPDATE_TASK should operate on todos, not tasks)"""
    logger.info(f"🔧 [UPDATE_TODO] Starting UPDATE_TASK execution (operating on todos)")
    from app.agents.tools.data.todos import TodoDatabaseTool
    todo_tool = TodoDatabaseTool()
    
    if not intent_result.task_info:
        logger.error(f"🔧 [UPDATE_TODO] No task_info provided")
        await task_manager.create_crud_failure_card(
            user_id=user_id,
            operation="failed",
            entity_type="todo",
            entity_title="Todo Update",
            conversation_id=conversation_id
        )
        return
    
    logger.info(f"🔧 [UPDATE_TODO] Updating todo: {intent_result.task_info.task_title}")
    
    # Validate due_date if provided
    validated_due_date = intent_result.task_info.due_date
    if validated_due_date:
        validated_due_date = await _validate_llm_date(validated_due_date, user_id, original_query)
        if validated_due_date != intent_result.task_info.due_date:
            logger.warning(f"🔍 [DATE-VALIDATION] Todo update date corrected: '{intent_result.task_info.due_date}' → '{validated_due_date}'")
    
    # Prepare input data for TodoDatabaseTool
    input_data = {
        "operation": "update",
        "title": intent_result.task_info.task_title,
        "todo_data": {
            "title": intent_result.task_info.task_title,
            "description": intent_result.task_info.task_description,
            "due_date": validated_due_date,
            "priority": intent_result.task_info.priority,
            "tags": intent_result.task_info.tags
        }
    }
    
    # Update todo by title
    result = await todo_tool.execute(
        input_data=input_data,
        context={"user_id": user_id}
    )
    
    if result.success:
        # TodoDatabaseTool returns the updated todo in result.data.todo
        updated_todo = result.data.get("todo", {})
        todo_title = updated_todo.get("title", intent_result.task_info.task_title)
        
        # Create success card
        await task_manager.create_crud_success_card(
            user_id=user_id,
            operation="updated",
            entity_type="todo",
            entity_title=todo_title,
            conversation_id=conversation_id,
            details={
                "updated_todo": todo_title,
                "changes": {
                    "due_date": intent_result.task_info.due_date,
                    "priority": intent_result.task_info.priority,
                    "description": intent_result.task_info.task_description,
                    "tags": intent_result.task_info.tags
                }
            }
        )
    else:
        # Todo update failed - likely todo doesn't exist
        todo_title = intent_result.task_info.task_title if intent_result.task_info else "Unknown Todo"
        await task_manager.create_crud_failure_card(
            user_id=user_id,
            operation="failed",
            entity_type="todo",
            entity_title=f"Todo '{todo_title}' not found",
            conversation_id=conversation_id,
            details={
                "error": f"No todo found with title '{todo_title}'. Please check the todo name or create it first.",
                "suggested_action": f"Create a new todo called '{todo_title}' or check existing todo names"
            }
        )


async def _execute_task_completion_direct(user_id: str, conversation_id: str, intent_result, task_manager):
    """Execute todo completion directly (COMPLETE_TASK should operate on todos, not tasks)"""
    logger.info(f"🔧 [COMPLETE_TODO] Starting COMPLETE_TASK execution (operating on todos)")
    from app.agents.tools.data.todos import TodoDatabaseTool
    todo_tool = TodoDatabaseTool()
    
    if not intent_result.task_info:
        logger.error(f"🔧 [COMPLETE_TODO] No task_info provided")
        await task_manager.create_crud_failure_card(
            user_id=user_id,
            operation="failed",
            entity_type="todo",
            entity_title="Todo Completion",
            conversation_id=conversation_id
        )
        return
    
    logger.info(f"🔧 [COMPLETE_TODO] Completing todo: {intent_result.task_info.task_title}")
    # Complete todo by updating its status
    result = await todo_tool.execute(
        input_data={
            "operation": "update",
            "title": intent_result.task_info.task_title,
            "todo_data": {
                "completed": True,
                "status": "completed"
            }
        },
        context={"user_id": user_id}
    )
    
    if result.success:
        # Create success card
        await task_manager.create_crud_success_card(
            user_id=user_id,
            operation="completed",
            entity_type="todo",
            entity_title=intent_result.task_info.task_title,
            conversation_id=conversation_id,
            details={
                "completed_todo": intent_result.task_info.task_title,
                "completed_at": datetime.utcnow().isoformat()
            }
        )
    else:
        # Todo completion failed - likely todo doesn't exist
        todo_title = intent_result.task_info.task_title if intent_result.task_info else "Unknown Todo"
        await task_manager.create_crud_failure_card(
            user_id=user_id,
            operation="failed",
            entity_type="todo",
            entity_title=f"Todo '{todo_title}' not found",
            conversation_id=conversation_id,
            details={
                "error": f"No todo found with title '{todo_title}'. Please check the todo name or create it first.",
                "suggested_action": f"Create a new todo called '{todo_title}' or check existing todo names"
            }
        )


async def execute_task_listing_direct(
    user_id: str,
    conversation_id: str,
    intent_result,
    original_query: str
) -> None:
    """Execute task listing directly without creating a task card"""
    try:
        logger.info(f"Executing direct task listing for user {user_id}")
        
        # Extract filters from workflow parameters
        filters = intent_result.workflow_params.get("filters", {})
        
        # Add common filters from entities
        if intent_result.entities.get("status"):
            filters["status"] = intent_result.entities["status"]
        if intent_result.entities.get("priority"):
            filters["priority"] = intent_result.entities["priority"]
        if intent_result.entities.get("due_date"):
            filters["due_before"] = intent_result.entities["due_date"]
        if intent_result.entities.get("tags"):
            filters["tags"] = intent_result.entities["tags"]

        from app.agents.tools.data.tasks import TaskDatabaseTool
        task_tool = TaskDatabaseTool()

        # List tasks
        result = await task_tool.execute(
            input_data={
                "operation": "list",
                "filters": filters
            },
            context={"user_id": user_id}
        )

        if result.success:
            tasks = result.data.get("tasks", [])
            task_count = len(tasks)
            
            # Check if quantity was specified
            quantity_limit = filters.get("limit")
            
            # Generate appropriate response message
            if task_count == 0:
                response_message = "You don't have any tasks matching those criteria."
            elif task_count == 1:
                response_message = f"Here's your task: {tasks[0].get('title', 'Untitled')}"
            else:
                if quantity_limit:
                    response_message = f"Here are your {task_count} tasks (requested {quantity_limit}):"
                else:
                    response_message = f"Here are your {task_count} tasks:"
            
            # Create a formatted task list for the response
            task_list = []
            # Use quantity limit if specified, otherwise show all tasks
            display_limit = quantity_limit if quantity_limit else len(tasks)
            for task in tasks[:display_limit]:
                task_list.append({
                    "title": task.get("title", "Untitled"),
                    "status": task.get("status", "pending"),
                    "priority": task.get("priority", "medium"),
                    "due_date": task.get("due_date"),
                    "id": task.get("id")
                })

            # Send success card directly
            task_manager = get_agent_task_manager()
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="listed",
                entity_type="tasks",
                entity_title=f"{task_count} tasks",
                details={"task_count": task_count, "tasks": task_list},
                conversation_id=conversation_id
            )

            # Add the response to conversation
            conversation_manager = get_conversation_manager()
            await conversation_manager.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=response_message,
                metadata={
                    "action": "list_tasks",
                    "task_count": task_count,
                    "tasks": task_list
                }
            )

            logger.info(f"Successfully listed {task_count} tasks for user {user_id}")
        else:
            logger.error(f"Task listing failed: {result.error}")
            
            # Send error message
            conversation_manager = get_conversation_manager()
            await conversation_manager.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content="I had trouble retrieving your tasks. Please try again.",
                metadata={"action": "list_tasks", "error": result.error}
            )

    except Exception as e:
        logger.error(f"Direct task listing failed: {e}")
        
        # Send error message
        conversation_manager = get_conversation_manager()
        await conversation_manager.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content="I encountered an error while retrieving your tasks. Please try again.",
            metadata={"action": "list_tasks", "error": str(e)}
        )


async def _validate_llm_date(llm_date: str, user_id: str, original_query: str) -> str:
    """
    Validate and correct LLM-generated dates to ensure they are reasonable.
    
    Args:
        llm_date: ISO date string from LLM
        user_id: User ID for timezone lookup
        original_query: Original user query for context
        
    Returns:
        Validated/corrected ISO date string
    """
    try:
        from datetime import datetime, timedelta
        import pytz
        from app.core.utils.timezone_utils import get_timezone_manager
        
        # Parse the LLM date
        try:
            parsed_date = datetime.fromisoformat(llm_date.replace('Z', '+00:00'))
        except ValueError:
            logger.error(f"Invalid ISO date from LLM: {llm_date}")
            return None
        
        # Get user timezone
        timezone_manager = get_timezone_manager()
        user_tz = await timezone_manager.get_user_timezone(user_id)
        current_time = datetime.now(user_tz)
        
        # Convert LLM date to user timezone for validation
        if parsed_date.tzinfo is None:
            # Assume it's in user timezone if no timezone info
            parsed_date = user_tz.localize(parsed_date)
        else:
            parsed_date = parsed_date.astimezone(user_tz)
        
        # Validation rules
        min_date = current_time - timedelta(hours=1)  # Allow up to 1 hour in the past (for edge cases)
        max_date = current_time + timedelta(days=730)  # Max 2 years in future
        
        # Semantic validation - check if the date makes sense given the query
        query_lower = original_query.lower()
        
        # Check for "tonight" - should be today, not tomorrow or later
        if "tonight" in query_lower and parsed_date.date() > current_time.date():
            logger.warning(f"User said 'tonight' but LLM returned future date: {llm_date}")
            # Correct to tonight if it's not too late, otherwise tomorrow night
            if current_time.hour < 22:  # Before 10pm
                corrected_date = current_time.replace(hour=parsed_date.hour, minute=parsed_date.minute, second=0, microsecond=0)
            else:
                corrected_date = current_time.replace(hour=parsed_date.hour, minute=parsed_date.minute, second=0, microsecond=0) + timedelta(days=1)
            return corrected_date.isoformat()
        
        # Check for "tomorrow" - should be exactly 1 day from now
        if "tomorrow" in query_lower:
            expected_date = current_time.date() + timedelta(days=1)
            if parsed_date.date() != expected_date:
                logger.warning(f"User said 'tomorrow' but LLM returned {parsed_date.date()}, correcting to {expected_date}")
                corrected_date = current_time.replace(year=expected_date.year, month=expected_date.month, day=expected_date.day, 
                                                    hour=parsed_date.hour, minute=parsed_date.minute, second=0, microsecond=0)
                return corrected_date.isoformat()
        
        # Basic time range validation
        if parsed_date < min_date:
            logger.warning(f"LLM date is in the past: {llm_date}, correcting to tomorrow")
            # If it's in the past, move to tomorrow at the same time
            corrected_date = current_time.replace(hour=parsed_date.hour, minute=parsed_date.minute, second=0, microsecond=0) + timedelta(days=1)
            return corrected_date.isoformat()
        
        if parsed_date > max_date:
            logger.warning(f"LLM date is too far in future: {llm_date}, correcting to 1 year from now")
            # If too far in future, cap at 1 year from now
            corrected_date = current_time + timedelta(days=365)
            corrected_date = corrected_date.replace(hour=parsed_date.hour, minute=parsed_date.minute, second=0, microsecond=0)
            return corrected_date.isoformat()
        
        # Date is reasonable, return as-is
        return llm_date
        
    except Exception as e:
        logger.error(f"Error validating LLM date: {e}")
        return llm_date  # Return original if validation fails
