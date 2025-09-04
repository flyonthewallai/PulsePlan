"""
Base tool classes for PulsePlan agent tools
Provides abstract base classes and common functionality
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result structure for tool execution"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolError(Exception):
    """Base error class for tool operations"""
    
    def __init__(self, message: str, tool_name: str, recoverable: bool = False):
        self.message = message
        self.tool_name = tool_name
        self.recoverable = recoverable
        super().__init__(message)


class BaseTool(ABC):
    """Abstract base class for all PulsePlan tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    @abstractmethod
    def get_required_tokens(self) -> List[str]:
        """Return list of required OAuth tokens for this tool"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the tool operation"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute the tool operation"""
        pass
    
    def log_execution(self, input_data: Dict[str, Any], result: ToolResult, context: Dict[str, Any]):
        """Log tool execution for observability"""
        import logging
        
        logger = logging.getLogger(f"tools.{self.name}")
        logger.info(
            f"Tool {self.name} executed",
            extra={
                "tool_name": self.name,
                "success": result.success,
                "execution_time": result.execution_time,
                "user_id": context.get("user_id"),
                "error": result.error if not result.success else None
            }
        )


class CalendarTool(BaseTool):
    """Base class for calendar-specific tools"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    @abstractmethod
    async def list_events(self, start_date: str, end_date: str, context: Dict[str, Any]) -> ToolResult:
        """List calendar events in date range"""
        pass
    
    @abstractmethod
    async def create_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create a new calendar event"""
        pass
    
    @abstractmethod
    async def update_event(self, event_id: str, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update an existing calendar event"""
        pass
    
    @abstractmethod
    async def delete_event(self, event_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete a calendar event"""
        pass


class TaskTool(BaseTool):
    """Base class for task management tools"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    @abstractmethod
    async def create_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create a new task"""
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, task_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update an existing task"""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete a task"""
        pass
    
    @abstractmethod
    async def list_tasks(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List tasks with optional filtering"""
        pass


class EmailTool(BaseTool):
    """Base class for email management tools"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    @abstractmethod
    async def send_email(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Send an email"""
        pass
    
    @abstractmethod
    async def list_emails(self, filters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """List emails with optional filtering"""
        pass


class BriefingTool(BaseTool):
    """Base class for briefing and data aggregation tools"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    @abstractmethod
    async def aggregate_data(self, sources: List[str], context: Dict[str, Any]) -> ToolResult:
        """Aggregate data from multiple sources"""
        pass
    
    @abstractmethod
    async def synthesize_content(self, data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Synthesize aggregated data into briefing content"""
        pass