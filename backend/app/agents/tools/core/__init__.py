"""
Core tooling and base classes.

This module contains core tooling infrastructure including:
- Base tool classes and abstract interfaces
- Common tool utilities and shared functionality
- Tool factory patterns and configuration management
"""

from .base import (
    ToolResult,
    ToolError,
    BaseTool,
    CalendarTool,
    TaskTool,
    EmailTool,
    BriefingTool
)

__all__ = [
    "ToolResult",
    "ToolError",
    "BaseTool",
    "CalendarTool",
    "TaskTool",
    "EmailTool",
    "BriefingTool",
]
