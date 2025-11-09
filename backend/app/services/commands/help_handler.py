"""
Help Command Handler
Returns list of available commands with examples
"""
from typing import Dict, Any
import logging
from .base import BaseCommandHandler, CommandResult

logger = logging.getLogger(__name__)


class HelpCommandHandler(BaseCommandHandler):
    """Handler for /help command - shows available commands"""

    def __init__(self):
        super().__init__()
        self.command_name = "help"

    async def execute(self, user_id: str, parameters: Dict[str, Any]) -> CommandResult:
        """
        Execute help command
        
        No parameters required - returns static list of commands
        """
        help_text = """## 🎯 Available Commands

**Task Management:**
- `/todo [title] [due date] [priority]` - Create a new task
  - Example: `/todo Finish essay tomorrow at 5pm high priority`
  - Example: `/todo Buy groceries #personal`

**Scheduling:**
- `/schedule [title] [time] [duration]` - Schedule an event
  - Example: `/schedule Team meeting tomorrow at 2pm`
  - Example: `/schedule Study session Friday 3pm for 90 minutes`

- `/reschedule [task] to [new time]` - Reschedule a task/event
  - Example: `/reschedule essay to tomorrow`
  - Example: `/reschedule team meeting to 3pm`

**Productivity:**
- `/focus [duration] [on task]` - Start a focus/Pomodoro timer
  - Example: `/focus` (default 25 minutes)
  - Example: `/focus 50 minutes on essay writing`

**Information:**
- `/briefing` - Show today's daily briefing
  - Example: `/briefing`

- `/help` - Show this help message
  - Example: `/help`

---

💡 **Tips:**
- Commands are deterministic and execute immediately
- You can also chat naturally - I'll understand your intent
- Use `#tags` to organize tasks
- Specify priorities as: low, medium, high
- Date formats: "tomorrow", "next Friday", "Oct 30 at 3pm"

Type `/` to see command suggestions!"""

        return CommandResult(
            success=True,
            command=self.command_name,
            result={"help_text": help_text},
            immediate_response=help_text
        )

