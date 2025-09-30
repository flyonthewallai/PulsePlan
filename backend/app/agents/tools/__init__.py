"""
Agent tools module - Comprehensive tool ecosystem organized by domain.

This module provides organized access to all agent tools grouped by functionality:
- integrations: External service tools (Canvas, Calendar, Email)
- scheduling: Advanced scheduling and intelligent scheduling tools  
- communication: Communication and notification tools
- data: Data management and CRUD operation tools
- search: Search and retrieval tools
- core: Core tooling and base classes
"""

# Re-export from modules for backward compatibility
from .core import *
from .integrations import *
from .scheduling import *
from .communication import *
from .data import *
from .search import *

__all__ = [
    # Core tooling
    "BaseTool",
    "BaseDatabaseTool",
    "BaseServiceTool", 
    "ToolFactory",
    "ToolConfig",
    "ToolExecutor",
    "ToolResponse",
    "ToolError",
    
    # Integration tools
    "CanvasDatabaseTool",
    "TaskDatabaseTool",
    "get_canvas_tool_factory",
    "get_task_tool_factory",
    "CalendarDatabaseTool",
    "CalendarServiceTool",
    "get_calendar_tool_factory",
    "EmailServiceTool",
    "EmailDatabaseTool",
    "get_email_tool_factory",
    
    # Scheduling tools
    "SchedulingDatabaseTool",
    "SchedulingPreviewTool", 
    "SchedulingServiceTool",
    "get_scheduling_tool_factory",
    "PreviewSystemTool",
    "SchedulePreviewTool",
    "get_preview_tool_factory",
    "TransparentSchedulerTool",
    "IntelligentSchedulingTool", 
    "get_transparent_scheduler_factory",
    
    # Communication tools
    "BriefingTool",
    "BriefingDatabaseTool",
    "BriefingServiceTool",
    "get_briefing_tool_factory",
    "NotificationTool",
    "NotificationDatabaseTool",
    "NotificationServiceTool", 
    "get_notification_tool_factory",
    "WeeklyPulseTool",
    "PulseViewTool",
    "PulseServiceTool",
    "get_weekly_pulse_tool_factory",
    "get_pulse_view_tool_factory", 
    "PulseDatabaseTool",
    
    # Data tools
    "ContactsTool",
    "ContactsDatabaseTool", 
    "ContactsServiceTool",
    "get_contacts_tool_factory",
    "MemoryServiceTool",
    "MemoryDatabaseTool",
    "MemoryTool",
    "get_memory_tool_factory",
    "PreferencesTool",
    "PreferencesDatabaseTool",
    "PreferencesServiceTool",
    "get_preferences_tool_factory",
    "TaskTool",
    "TaskDatabaseTool",
    "TaskServiceTool",
    "get_task_tool_factory",
    "TodoTool",
    "TodoDatabaseTool",
    "TodoServiceTool", 
    "get_todo_tool_factory",
    
    # Search tools
    "WebSearchTool",
    "SearchServiceTool",
    "SearchDatabaseTool", 
    "get_web_search_tool_factory",
]