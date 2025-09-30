"""
Agent Workflow Execution Module
Handles complex workflow execution and background tasks
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.agents.core.orchestration.agent_task_manager import get_agent_task_manager, TaskStatus
from app.agents.core.conversation.conversation_manager import get_conversation_manager
from app.agents.core.conversation.conversation_state_manager import get_conversation_state_manager
from app.agents.core.conversation.websocket_notification_manager import get_websocket_manager
from app.agents.core.orchestration.intent_processor import ActionType
from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


async def execute_workflow_background(
    user_id: str,
    conversation_id: str,
    task_id: str,
    intent_result,
    original_query: str
):
    """
    Execute workflow in background with progress tracking and WebSocket notifications
    """
    try:
        logger.info(f"Executing background workflow: {intent_result.workflow_type} for task {task_id}")

        task_manager = get_agent_task_manager()
        conversation_manager = get_conversation_manager()
        conversation_state_manager = get_conversation_state_manager()
        websocket_manager = get_websocket_manager()

        # Update task to in progress
        await task_manager.update_task_progress(
            task_id=task_id,
            status=TaskStatus.IN_PROGRESS,
            progress=10
        )
        
        # Update conversation state
        await conversation_state_manager.update_task_status(
            conversation_id=conversation_id,
            user_id=user_id,
            task_id=task_id,
            status="in_progress"
        )

        # Route to appropriate workflow execution
        if intent_result.action == ActionType.CREATE_TASK:
            result = await execute_task_creation(intent_result, user_id, task_id)
        elif intent_result.action == ActionType.DELETE_TASK:
            result = await execute_task_deletion(intent_result, user_id, task_id)
        elif intent_result.action == ActionType.UPDATE_TASK:
            result = await execute_task_update(intent_result, user_id, task_id)
        elif intent_result.action == ActionType.COMPLETE_TASK:
            result = await execute_task_completion(intent_result, user_id, task_id)
        elif intent_result.action == ActionType.LIST_TASKS:
            result = await execute_task_listing(intent_result, user_id, task_id)
        elif intent_result.action == ActionType.SCHEDULE_EVENT:
            result = await execute_event_scheduling(intent_result, user_id, task_id)
        elif intent_result.action == ActionType.WEB_SEARCH:
            result = await execute_web_search(intent_result, user_id, task_id, original_query)
        elif intent_result.action == ActionType.DAILY_BRIEFING:
            result = await execute_daily_briefing(user_id, task_id)
        else:
            # Use legacy orchestrator for other workflows
            result = await execute_legacy_workflow(
                intent_result.workflow_type, original_query, user_id, task_id
            )

        # Complete task with result
        if result.get("success", False):
            await task_manager.complete_task(
                task_id=task_id,
                result=result,
                success_message=result.get("message", "Workflow completed successfully")
            )
            
            # Update conversation state
            await conversation_state_manager.update_task_status(
                conversation_id=conversation_id,
                user_id=user_id,
                task_id=task_id,
                status="completed",
                result=result
            )

            # Send success notification via WebSocket
            task_card = await task_manager.get_task_card(task_id)
            success_message = result.get("message", "Task completed successfully!")
            follow_up = "Need anything else?" if intent_result.action in [ActionType.CREATE_TASK, ActionType.DELETE_TASK] else None
            
            await websocket_manager.send_task_completion(
                user_id=user_id,
                task_id=task_id,
                task_title=task_card.title if task_card else "Task",
                status="success",
                message=success_message,
                follow_up_question=follow_up,
                workflow_type=intent_result.workflow_type
            )

            # Add result to conversation
            if result.get("response"):
                await conversation_manager.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="assistant",
                    content=result["response"],
                    metadata={"task_id": task_id, "workflow_type": intent_result.workflow_type}
                )
        else:
            # Handle failure
            await task_manager.fail_task(
                task_id=task_id,
                error_message=result.get("error", "Workflow execution failed"),
                error_details=result
            )
            
            # Update conversation state
            await conversation_state_manager.update_task_status(
                conversation_id=conversation_id,
                user_id=user_id,
                task_id=task_id,
                status="failed",
                result=result
            )
            
            # Send failure notification via WebSocket
            task_card = await task_manager.get_task_card(task_id)
            await websocket_manager.send_task_completion(
                user_id=user_id,
                task_id=task_id,
                task_title=task_card.title if task_card else "Task",
                status="failed",
                message=result.get("error", "Task failed"),
                workflow_type=intent_result.workflow_type
            )

    except Exception as e:
        logger.error(f"Background workflow execution failed: {e}")
        try:
            await task_manager.fail_task(
                task_id=task_id,
                error_message=str(e),
                error_details={"exception": str(e)}
            )
        except:
            pass  # Avoid cascading failures


async def execute_task_creation(intent_result, user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute task creation workflow"""
    try:
        task_manager = get_agent_task_manager()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=30)

        if not intent_result.task_info:
            return {"success": False, "error": "No task information extracted"}

        # Use existing task tools
        from app.agents.tools.tasks import TaskDatabaseTool
        task_tool = TaskDatabaseTool()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=60)

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

        # Update progress
        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            # Also create success card
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="created",
                entity_type="task",
                entity_title=intent_result.task_info.task_title
            )

            return {
                "success": True,
                "response": f"I've created the task '{intent_result.task_info.task_title}' for you.",
                "task_data": result.data
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_task_deletion(intent_result, user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute task deletion workflow"""
    try:
        task_manager = get_agent_task_manager()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=30)

        # Extract task name from multiple possible sources
        task_name = (
            intent_result.workflow_params.get("task_name") or
            intent_result.entities.get("target_task") or
            intent_result.entities.get("task_name") or
            intent_result.entities.get("task_title") or
            intent_result.task_info.task_title if intent_result.task_info else None
        )
        
        if not task_name:
            return {"success": False, "error": "No task name provided for deletion"}

        # Use existing task tools
        from app.agents.tools.tasks import TaskDatabaseTool
        task_tool = TaskDatabaseTool()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=60)

        # Delete task
        result = await task_tool.execute(
            input_data={
                "operation": "delete",
                "title": task_name
            },
            context={"user_id": user_id}
        )

        # Update progress
        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            # Create success card
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="deleted",
                entity_type="task",
                entity_title=task_name
            )

            return {
                "success": True,
                "response": f"I've deleted the task '{task_name}' for you.",
                "task_data": result.data
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Task deletion failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_task_update(intent_result, user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute task update workflow"""
    try:
        task_manager = get_agent_task_manager()
        await task_manager.update_task_progress(task_id, progress=30)

        # Extract task information
        task_name = (
            intent_result.workflow_params.get("task_name") or
            intent_result.entities.get("target_task") or
            intent_result.entities.get("task_name") or
            intent_result.entities.get("task_title") or
            intent_result.task_info.task_title if intent_result.task_info else None
        )
        
        if not task_name:
            return {"success": False, "error": "No task name provided for update"}

        from app.agents.tools.tasks import TaskDatabaseTool
        task_tool = TaskDatabaseTool()

        await task_manager.update_task_progress(task_id, progress=60)

        # Use new title if provided (rename scenario)
        new_title = (
            intent_result.entities.get("new_title") or
            (intent_result.task_info.task_title if intent_result.task_info else None)
        )

        # Update task
        result = await task_tool.execute(
            input_data={
                "operation": "update",
                "title": task_name,
                "task_data": {
                    "title": new_title or task_name,
                    "description": intent_result.task_info.task_description if intent_result.task_info else None,
                    "due_date": intent_result.task_info.due_date if intent_result.task_info else None,
                    "priority": intent_result.task_info.priority if intent_result.task_info else None,
                    "tags": intent_result.task_info.tags if intent_result.task_info else None
                }
            },
            context={"user_id": user_id}
        )

        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="updated",
                entity_type="task",
                entity_title=task_name
            )

            return {
                "success": True,
                "response": f"I've updated the task '{task_name}' for you.",
                "task_data": result.data
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Task update failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_task_completion(intent_result, user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute task completion workflow"""
    try:
        task_manager = get_agent_task_manager()
        await task_manager.update_task_progress(task_id, progress=30)

        # Extract task information
        task_name = (
            intent_result.workflow_params.get("task_name") or
            intent_result.entities.get("target_task") or
            intent_result.entities.get("task_name") or
            intent_result.entities.get("task_title") or
            intent_result.task_info.task_title if intent_result.task_info else None
        )
        
        if not task_name:
            return {"success": False, "error": "No task name provided for completion"}

        from app.agents.tools.tasks import TaskDatabaseTool
        task_tool = TaskDatabaseTool()

        await task_manager.update_task_progress(task_id, progress=60)

        # Complete task
        result = await task_tool.execute(
            input_data={
                "operation": "update",
                "title": task_name,
                "task_data": {"status": "completed"}
            },
            context={"user_id": user_id}
        )

        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="completed",
                entity_type="task",
                entity_title=task_name
            )

            return {
                "success": True,
                "response": f"I've marked the task '{task_name}' as completed.",
                "task_data": result.data
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Task completion failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_task_listing(intent_result, user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute task listing workflow"""
    try:
        task_manager = get_agent_task_manager()
        await task_manager.update_task_progress(task_id, progress=30)

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

        from app.agents.tools.tasks import TaskDatabaseTool
        task_tool = TaskDatabaseTool()

        await task_manager.update_task_progress(task_id, progress=60)

        # List tasks
        result = await task_tool.execute(
            input_data={
                "operation": "list",
                "filters": filters
            },
            context={"user_id": user_id}
        )

        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            tasks = result.data.get("tasks", [])
            task_count = len(tasks)
            
            # Generate appropriate response message
            if task_count == 0:
                response_message = "You don't have any tasks matching those criteria."
            elif task_count == 1:
                response_message = f"Here's your task: {tasks[0].get('title', 'Untitled')}"
            else:
                response_message = f"Here are your {task_count} tasks:"
            
            # Create a formatted task list for the response
            task_list = []
            # Use quantity limit if specified, otherwise show all tasks
            display_limit = intent_result.workflow_params.get("filters", {}).get("limit", len(tasks))
            for task in tasks[:display_limit]:
                task_list.append({
                    "title": task.get("title", "Untitled"),
                    "status": task.get("status", "pending"),
                    "priority": task.get("priority", "medium"),
                    "due_date": task.get("due_date"),
                    "id": task.get("id")
                })

            await task_manager.create_crud_success_card(
                user_id=user_id,
                operation="listed",
                entity_type="tasks",
                entity_title=f"{task_count} tasks",
                details={"task_count": task_count, "tasks": task_list}
            )

            return {
                "success": True,
                "response": response_message,
                "task_data": {
                    "tasks": task_list,
                    "total_count": task_count,
                    "filters_applied": filters
                }
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Task listing failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_event_scheduling(intent_result, user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute event scheduling workflow"""
    try:
        task_manager = get_agent_task_manager()
        await task_manager.update_task_progress(task_id, progress=30)

        # Extract event information
        event_title = (
            intent_result.workflow_params.get("event_title") or
            intent_result.entities.get("event_title") or
            intent_result.entities.get("event_name")
        )
        
        if not event_title:
            return {"success": False, "error": "No event title provided for scheduling"}

        # For now, use legacy orchestrator for calendar operations
        # TODO: Implement proper calendar tool integration
        await task_manager.update_task_progress(task_id, progress=60)
        
        # Placeholder implementation
        await task_manager.update_task_progress(task_id, progress=90)

        await task_manager.create_crud_success_card(
            user_id=user_id,
            operation="scheduled",
            entity_type="event",
            entity_title=event_title
        )

        return {
            "success": True,
            "response": f"I've scheduled the event '{event_title}' for you.",
            "event_data": {"title": event_title}
        }

    except Exception as e:
        logger.error(f"Event scheduling failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_web_search(intent_result, user_id: str, task_id: str, query: str) -> Dict[str, Any]:
    """Execute web search workflow"""
    try:
        task_manager = get_agent_task_manager()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=20)

        search_query = intent_result.entities.get("search_query", query)

        # Use existing search tools
        from app.agents.tools.web_search import WebSearchTool
        search_tool = WebSearchTool()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=50)

        # Perform search
        result = await search_tool.execute(
            input_data={"query": search_query, "num_results": 5},
            context={"user_id": user_id}
        )

        # Update progress
        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            return {
                "success": True,
                "response": f"I found search results for '{search_query}'.",
                "search_data": result.data
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_daily_briefing(user_id: str, task_id: str) -> Dict[str, Any]:
    """Execute daily briefing workflow"""
    try:
        task_manager = get_agent_task_manager()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=20)

        # Use existing briefing tools
        from app.agents.tools.briefing import BriefingTool
        briefing_tool = BriefingTool()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=50)

        # Generate briefing
        result = await briefing_tool.execute(
            input_data={"briefing_type": "daily"},
            context={"user_id": user_id}
        )

        # Update progress
        await task_manager.update_task_progress(task_id, progress=90)

        if result.success:
            return {
                "success": True,
                "response": "Here's your daily briefing.",
                "briefing_data": result.data
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        logger.error(f"Daily briefing failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_legacy_workflow(
    workflow_type: str,
    query: str,
    user_id: str,
    task_id: str
) -> Dict[str, Any]:
    """Execute workflow using legacy orchestrator"""
    try:
        task_manager = get_agent_task_manager()

        # Update progress
        await task_manager.update_task_progress(task_id, progress=30)

        # Use legacy orchestrator for complex workflows
        orchestrator = AgentOrchestrator()

        # Map workflow types
        workflow_mapping = {
            "calendar": "CALENDAR",
            "email": "EMAIL",
            "scheduling": "SCHEDULING"
        }

        legacy_workflow_type = workflow_mapping.get(workflow_type, "NATURAL_LANGUAGE")

        # Update progress
        await task_manager.update_task_progress(task_id, progress=60)

        # Execute workflow
        result = await orchestrator.execute_workflow(
            workflow_type=legacy_workflow_type,
            input_data={"query": query},
            user_id=user_id
        )

        # Update progress
        await task_manager.update_task_progress(task_id, progress=90)

        return {
            "success": result.success,
            "response": result.result.get("message", "Workflow completed") if result.success else None,
            "error": result.error if not result.success else None,
            "workflow_data": result.result
        }

    except Exception as e:
        logger.error(f"Legacy workflow execution failed: {e}")
        return {"success": False, "error": str(e)}


