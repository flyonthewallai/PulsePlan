"""
Reschedule Command Handler
Reschedules existing tasks/events using existing update tools
"""
from typing import Dict, Any
import logging
from datetime import datetime
from .base import BaseCommandHandler, CommandResult
from app.agents.tools.data.tasks import TaskDatabaseTool
from app.agents.tools.data.todos import TodoDatabaseTool

logger = logging.getLogger(__name__)


class RescheduleCommandHandler(BaseCommandHandler):
    """Handler for /reschedule command - updates task/event times"""

    def __init__(self):
        super().__init__()
        self.command_name = "reschedule"

    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute reschedule command
        
        Parameters expected:
            - task_identifier (required): Task name or ID
            - new_time (required): New date/time in ISO format
        """
        # Validate required parameters
        validation_error = self.validate_required_parameters(
            parameters, ['task_identifier', 'new_time']
        )
        if validation_error:
            return validation_error

        try:
            task_identifier = parameters["task_identifier"]
            new_time = parameters["new_time"]
            
            # Parse new time
            new_dt = datetime.fromisoformat(new_time.replace('Z', '+00:00'))

            # First try to find and update as a todo
            todo_tool = TodoDatabaseTool()
            context = {"user_id": user_id}

            # List todos to find matching one
            list_result = await todo_tool.list_todos({}, context)
            
            if list_result.success and list_result.data:
                todos = list_result.data.get("todos", [])
                
                # Find todo by title (case-insensitive partial match)
                matching_todo = None
                for todo in todos:
                    if task_identifier.lower() in todo.get("title", "").lower():
                        matching_todo = todo
                        break

                if matching_todo:
                    # Update the todo's due_date
                    update_result = await todo_tool.update_todo(
                        matching_todo["id"],
                        {"due_date": new_dt.isoformat()},
                        context
                    )

                    if update_result.success:
                        time_str = new_dt.strftime('%b %d at %I:%M %p')
                        return CommandResult(
                            success=True,
                            command=self.command_name,
                            result=update_result.data,
                            immediate_response=f"✅ Rescheduled '{matching_todo['title']}' to {time_str}"
                        )

            # If not found as todo, try as task
            task_tool = TaskDatabaseTool()
            list_result = await task_tool.execute(
                input_data={"operation": "list"},
                context=context
            )

            if list_result.success and list_result.data:
                tasks = list_result.data.get("tasks", [])
                
                # Find task by title
                matching_task = None
                for task in tasks:
                    if task_identifier.lower() in task.get("title", "").lower():
                        matching_task = task
                        break

                if matching_task:
                    # Update the task's due_date
                    update_result = await task_tool.execute(
                        input_data={
                            "operation": "update",
                            "task_id": matching_task["id"],
                            "updates": {"due_date": new_dt.isoformat()}
                        },
                        context=context
                    )

                    if update_result.success:
                        time_str = new_dt.strftime('%b %d at %I:%M %p')
                        return CommandResult(
                            success=True,
                            command=self.command_name,
                            result=update_result.data,
                            immediate_response=f"✅ Rescheduled '{matching_task['title']}' to {time_str}"
                        )

            # Not found
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=f"Could not find task or todo matching '{task_identifier}'",
                error="Task not found",
                requires_clarification=True,
                clarification_prompt=f"I couldn't find a task matching '{task_identifier}'. Can you be more specific?"
            )

        except Exception as e:
            logger.error(f"Error in reschedule command handler: {e}", exc_info=True)
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=f"Error rescheduling: {str(e)}",
                error=str(e)
            )

