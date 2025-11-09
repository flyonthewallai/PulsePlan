"""
Schedule Command Handler
Creates calendar events using existing calendar tools
"""
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from .base import BaseCommandHandler, CommandResult
from app.agents.orchestrator import get_agent_orchestrator
from app.agents.agent_models import WorkflowType

logger = logging.getLogger(__name__)


class ScheduleCommandHandler(BaseCommandHandler):
    """Handler for /schedule command - creates calendar events"""

    def __init__(self):
        super().__init__()
        self.command_name = "schedule"

    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute schedule/event creation command
        
        Parameters expected:
            - title (required): Event title
            - start_time (required): Start time in ISO format
            - duration (optional): Duration in minutes (default: 60)
            - location (optional): Event location
        """
        # Validate required parameters
        validation_error = self.validate_required_parameters(
            parameters, ['title', 'start_time']
        )
        if validation_error:
            return validation_error

        try:
            # Parse start time
            start_dt = datetime.fromisoformat(parameters["start_time"].replace('Z', '+00:00'))
            
            # Calculate end time
            duration = parameters.get("duration", 60)  # default 60 minutes
            end_dt = start_dt + timedelta(minutes=duration)

            # Use existing orchestrator/calendar workflow (NO duplication)
            orchestrator = await get_agent_orchestrator()
            
            result = await orchestrator.execute_workflow(
                workflow_type=WorkflowType.CALENDAR,
                user_id=user_id,
                input_data={
                    "operation": "create",
                    "provider": "google",  # Default provider
                    "event_data": {
                        "title": parameters["title"],
                        "description": parameters.get("description", ""),
                        "start": start_dt.isoformat(),
                        "end": end_dt.isoformat(),
                        "location": parameters.get("location"),
                    }
                }
            )

            if result.get("status") == "completed":
                # Format response
                title = parameters["title"]
                time_str = start_dt.strftime('%b %d at %I:%M %p')
                
                response_msg = f"📅 Scheduled: {title} on {time_str}"
                if parameters.get("location"):
                    response_msg += f" at {parameters['location']}"

                return CommandResult(
                    success=True,
                    command=self.command_name,
                    result=result.get("result"),
                    immediate_response=response_msg
                )
            else:
                error_msg = result.get("error", "Unknown error")
                return CommandResult(
                    success=False,
                    command=self.command_name,
                    immediate_response=f"Failed to schedule event: {error_msg}",
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Error in schedule command handler: {e}", exc_info=True)
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=f"Error scheduling event: {str(e)}",
                error=str(e)
            )

