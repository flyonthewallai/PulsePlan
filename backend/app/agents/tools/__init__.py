"""
PulsePlan Tools Package
Centralized tool definitions for LangGraph workflows
"""
from .base import BaseTool, ToolError, ToolResult, CalendarTool, TaskTool, EmailTool, BriefingTool
from .calendar import GoogleCalendarTool, MicrosoftCalendarTool
from .tasks import TaskDatabaseTool, TaskSchedulingTool
from .todos import TodoDatabaseTool
from .email import EmailManagerTool, GmailUserTool, OutlookUserTool, SystemEmailTool
from .briefing import DataAggregatorTool, ContentSynthesizerTool
from .web_search import WebSearchTool, NewsSearchTool, ResearchTool
from .canvas import CanvasLMSTool
from .weekly_pulse import WeeklyPulseTool
from .memory import MemoryTool
from .preferences import PreferencesTool
from .contacts import GoogleContactsTool

__all__ = [
    # Base classes
    "BaseTool",
    "ToolError", 
    "ToolResult",
    "CalendarTool",
    "TaskTool",
    "EmailTool", 
    "BriefingTool",
    
    # Calendar tools
    "GoogleCalendarTool",
    "MicrosoftCalendarTool",
    
    # Task tools
    "TaskDatabaseTool",
    "TaskSchedulingTool",
    "TodoDatabaseTool",
    
    # Email tools
    "EmailManagerTool",
    "GmailUserTool",
    "OutlookUserTool", 
    "SystemEmailTool",
    
    # Briefing tools
    "DataAggregatorTool",
    "ContentSynthesizerTool",
    "WeeklyPulseTool",
    
    # Web search tools
    "WebSearchTool",
    "NewsSearchTool", 
    "ResearchTool",
    
    # Integration tools
    "CanvasLMSTool",
    
    # Management tools
    "MemoryTool",
    "PreferencesTool",
    "GoogleContactsTool"
]