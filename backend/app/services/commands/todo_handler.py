"""
Todo Command Handler
Creates tasks/todos using the existing TodoDatabaseTool
"""
from typing import Dict, Any
import logging
from datetime import datetime
from .base import BaseCommandHandler, CommandResult
from app.agents.tools.data.todos import TodoDatabaseTool

logger = logging.getLogger(__name__)


class TodoCommandHandler(BaseCommandHandler):
    """Handler for /todo command - creates new tasks/todos"""

    def __init__(self):
        super().__init__()
        self.command_name = "todo"

    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute todo creation command
        
        Parameters expected:
            - title (required): Task title
            - due_date (optional): Due date in ISO format
            - priority (optional): low/medium/high
            - tags (optional): List of tags
        """
        # Validate required parameters
        validation_error = self.validate_required_parameters(parameters, ['title'])
        if validation_error:
            return validation_error

        try:
            # Use existing TodoDatabaseTool (NO duplication)
            todo_tool = TodoDatabaseTool()
            context = {"user_id": user_id}

            # Prepare todo data
            todo_data = {
                "title": parameters["title"],
                "priority": parameters.get("priority", "medium"),
                "tags": parameters.get("tags", []),
            }

            # Add due_date if provided
            if parameters.get("due_date"):
                todo_data["due_date"] = parameters["due_date"]

            # Add description if provided
            if parameters.get("description"):
                todo_data["description"] = parameters["description"]

            # Create the todo
            result = await todo_tool.create_todo(todo_data, context)

            if result.success:
                # Format response message
                title = parameters["title"]
                due_text = ""
                if parameters.get("due_date"):
                    try:
                        due_dt = datetime.fromisoformat(parameters["due_date"].replace('Z', '+00:00'))
                        due_text = f" due {due_dt.strftime('%b %d at %I:%M %p')}"
                    except:
                        due_text = f" due {parameters['due_date']}"

                response_msg = f"✅ Created task: {title}{due_text}"

                return CommandResult(
                    success=True,
                    command=self.command_name,
                    result=result.data,
                    immediate_response=response_msg
                )
            else:
                return CommandResult(
                    success=False,
                    command=self.command_name,
                    immediate_response=f"Failed to create task: {result.error}",
                    error=result.error
                )

        except Exception as e:
            logger.error(f"Error in todo command handler: {e}", exc_info=True)
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=f"Error creating task: {str(e)}",
                error=str(e)
            )

