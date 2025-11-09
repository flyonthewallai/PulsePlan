"""
Focus Command Handler
Starts a focus/Pomodoro timer session
"""
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from .base import BaseCommandHandler, CommandResult

logger = logging.getLogger(__name__)


class FocusCommandHandler(BaseCommandHandler):
    """Handler for /focus command - starts focus/pomodoro timer"""

    def __init__(self):
        super().__init__()
        self.command_name = "focus"

    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute focus session start command
        
        Parameters expected:
            - duration (optional): Duration in minutes (default: 25 for Pomodoro)
            - task (optional): What the user is focusing on
        """
        try:
            duration = parameters.get("duration", 25)  # Default Pomodoro time
            task = parameters.get("task", "your work")

            # Calculate end time
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration)

            # For now, just return a motivational message
            # In future, this could create a focus session record in DB
            # and integrate with notifications/timers
            
            response_msg = f"🎯 Focus session started for {duration} minutes"
            if task and task != "your work":
                response_msg += f" on {task}"
            response_msg += f"\nYou'll be done at {end_time.strftime('%I:%M %p')}. Stay focused!"

            return CommandResult(
                success=True,
                command=self.command_name,
                result={
                    "duration": duration,
                    "task": task,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                immediate_response=response_msg
            )

        except Exception as e:
            logger.error(f"Error in focus command handler: {e}", exc_info=True)
            return CommandResult(
                success=False,
                command=self.command_name,
                immediate_response=f"Error starting focus session: {str(e)}",
                error=str(e)
            )

