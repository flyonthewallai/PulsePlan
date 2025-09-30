"""
External service integration tools.

This module contains tools that integrate with external services and APIs including:
- Canvas LMS integration for assignments and courses
- Calendar services for scheduling and event management  
- Email services for communication and notifications
"""

# Canvas integration
from .canvas import (
    CanvasLMSTool
)

# Calendar integration  
from .calendar import (
    GoogleCalendarTool,
    MicrosoftCalendarTool
)

# Email integration
from .email import (
    GmailUserTool,
    OutlookUserTool,
    EmailIntegrationTool,
    EmailManagerTool
)

__all__ = [
    # Canvas tools
    "CanvasLMSTool",
    
    # Calendar tools
    "GoogleCalendarTool",
    "MicrosoftCalendarTool",
    
    # Email tools
    "GmailUserTool",
    "OutlookUserTool",
    "EmailIntegrationTool",
    "EmailManagerTool",
]
