"""
Command Handler Registry
Maps command names to handler instances
"""
from typing import Dict, Optional
from .base import BaseCommandHandler, CommandResult
from .todo_handler import TodoCommandHandler
from .schedule_handler import ScheduleCommandHandler
from .reschedule_handler import RescheduleCommandHandler
from .focus_handler import FocusCommandHandler
from .briefing_handler import BriefingCommandHandler
from .help_handler import HelpCommandHandler


# Global registry of command handlers
_COMMAND_HANDLERS: Dict[str, BaseCommandHandler] = {}


def register_handler(handler: BaseCommandHandler):
    """Register a command handler"""
    _COMMAND_HANDLERS[handler.command_name] = handler


def get_handler(command_name: str) -> Optional[BaseCommandHandler]:
    """Get handler for a command"""
    return _COMMAND_HANDLERS.get(command_name.lower())


def initialize_handlers():
    """Initialize and register all command handlers"""
    if _COMMAND_HANDLERS:
        return  # Already initialized
    
    handlers = [
        TodoCommandHandler(),
        ScheduleCommandHandler(),
        RescheduleCommandHandler(),
        FocusCommandHandler(),
        BriefingCommandHandler(),
        HelpCommandHandler(),
    ]
    
    for handler in handlers:
        register_handler(handler)


# Initialize handlers on import
initialize_handlers()


__all__ = [
    'BaseCommandHandler',
    'CommandResult',
    'get_handler',
    'register_handler',
    'initialize_handlers',
]

