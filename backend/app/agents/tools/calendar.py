"""
Calendar integration tools for PulsePlan agents.
Handles Google and Microsoft calendar operations across different providers.
"""
from typing import Dict, Any
import asyncio
from datetime import datetime

from .base import CalendarTool, ToolResult, ToolError


class GoogleCalendarTool(CalendarTool):
    """Google Calendar integration tool"""
    
    def __init__(self):
        super().__init__(
            name="google_calendar",
            description="Google Calendar operations via Google Calendar API"
        )
    
    def get_required_tokens(self) -> list[str]:
        return ["google"]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for Google Calendar operations"""
        operation = input_data.get("operation")
        
        if operation not in ["list", "create", "update", "delete"]:
            return False
        
        if operation in ["update", "delete"] and not input_data.get("event_id"):
            return False
        
        if operation in ["create", "update"] and not input_data.get("event_data"):
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute Google Calendar operation"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data", self.name)
            
            operation = input_data["operation"]
            
            # Route to specific operation
            if operation == "list":
                result = await self.list_events(
                    start_date=input_data.get("start_date", ""),
                    end_date=input_data.get("end_date", ""),
                    context=context
                )
            elif operation == "create":
                result = await self.create_event(
                    event_data=input_data["event_data"],
                    context=context
                )
            elif operation == "update":
                result = await self.update_event(
                    event_id=input_data["event_id"],
                    event_data=input_data["event_data"],
                    context=context
                )
            elif operation == "delete":
                result = await self.delete_event(
                    event_id=input_data["event_id"],
                    context=context
                )
            
            # Add execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Log execution
            self.log_execution(input_data, result, context)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def list_events(self, start_date: str, end_date: str, context: Dict[str, Any]) -> ToolResult:
        """List Google Calendar events"""
        try:
            from ..services.calendar_sync_service import get_calendar_sync_service
            
            calendar_service = get_calendar_sync_service()
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required for calendar operations", self.name)
            
            # Parse dates if provided
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Get events from database (already synced)
            events = await calendar_service.get_user_events(
                user_id=user_id,
                start_date=start_dt,
                end_date=end_dt,
                provider="google"
            )
            
            return ToolResult(
                success=True,
                data={
                    "events": events,
                    "total": len(events),
                    "date_range": {"start": start_date, "end": end_date}
                },
                metadata={"provider": "google", "operation": "list"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to list Google Calendar events: {e}", self.name, recoverable=True)
    
    async def create_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create Google Calendar event"""
        try:
            from ..services.calendar_sync_service import get_calendar_sync_service
            
            calendar_service = get_calendar_sync_service()
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required for calendar operations", self.name)
            
            # Create event via Google Calendar API and sync to database
            created_event = await calendar_service.create_google_event(user_id, event_data)
            
            return ToolResult(
                success=True,
                data={"event": created_event},
                metadata={"provider": "google", "operation": "create"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to create Google Calendar event: {e}", self.name, recoverable=True)
    
    async def update_event(self, event_id: str, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update Google Calendar event"""
        try:
            from ..services.calendar_sync_service import get_calendar_sync_service
            
            calendar_service = get_calendar_sync_service()
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required for calendar operations", self.name)
            
            # Update event via Google Calendar API and sync to database
            updated_event = await calendar_service.update_google_event(user_id, event_id, event_data)
            
            return ToolResult(
                success=True,
                data={"event": updated_event},
                metadata={"provider": "google", "operation": "update"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to update Google Calendar event: {e}", self.name, recoverable=True)
    
    async def delete_event(self, event_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete Google Calendar event"""
        try:
            from ..services.calendar_sync_service import get_calendar_sync_service
            
            calendar_service = get_calendar_sync_service()
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required for calendar operations", self.name)
            
            # Delete event via Google Calendar API and remove from database
            success = await calendar_service.delete_google_event(user_id, event_id)
            
            if not success:
                raise ToolError(f"Failed to delete event {event_id}", self.name)
            
            return ToolResult(
                success=True,
                data={
                    "deleted_event_id": event_id,
                    "deleted_at": datetime.utcnow().isoformat()
                },
                metadata={"provider": "google", "operation": "delete"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to delete Google Calendar event: {e}", self.name, recoverable=True)


class MicrosoftCalendarTool(CalendarTool):
    """Microsoft Calendar integration tool"""
    
    def __init__(self):
        super().__init__(
            name="microsoft_calendar",
            description="Microsoft Calendar operations via Microsoft Graph API"
        )
    
    def get_required_tokens(self) -> list[str]:
        return ["microsoft"]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for Microsoft Calendar operations"""
        # Same validation logic as Google Calendar
        operation = input_data.get("operation")
        
        if operation not in ["list", "create", "update", "delete"]:
            return False
        
        if operation in ["update", "delete"] and not input_data.get("event_id"):
            return False
        
        if operation in ["create", "update"] and not input_data.get("event_data"):
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute Microsoft Calendar operation"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data", self.name)
            
            operation = input_data["operation"]
            
            # Route to specific operation
            if operation == "list":
                result = await self.list_events(
                    start_date=input_data.get("start_date", ""),
                    end_date=input_data.get("end_date", ""),
                    context=context
                )
            elif operation == "create":
                result = await self.create_event(
                    event_data=input_data["event_data"],
                    context=context
                )
            elif operation == "update":
                result = await self.update_event(
                    event_id=input_data["event_id"],
                    event_data=input_data["event_data"],
                    context=context
                )
            elif operation == "delete":
                result = await self.delete_event(
                    event_id=input_data["event_id"],
                    context=context
                )
            
            # Add execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Log execution
            self.log_execution(input_data, result, context)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def list_events(self, start_date: str, end_date: str, context: Dict[str, Any]) -> ToolResult:
        """List Microsoft Calendar events"""
        try:
            # TODO: Implement actual Microsoft Graph API call
            await asyncio.sleep(0.1)  # Simulate API call
            
            mock_events = [
                {
                    "id": "microsoft_event_1",
                    "title": "Project Review",
                    "start": "2024-01-15T10:00:00Z",
                    "end": "2024-01-15T11:00:00Z",
                    "provider": "microsoft"
                }
            ]
            
            return ToolResult(
                success=True,
                data={
                    "events": mock_events,
                    "total": len(mock_events),
                    "date_range": {"start": start_date, "end": end_date}
                },
                metadata={"provider": "microsoft", "operation": "list"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to list Microsoft Calendar events: {e}", self.name, recoverable=True)
    
    async def create_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create Microsoft Calendar event"""
        try:
            # TODO: Implement actual Microsoft Graph API call
            await asyncio.sleep(0.2)  # Simulate API call
            
            created_event = {
                "id": f"microsoft_event_{datetime.utcnow().timestamp()}",
                "title": event_data.get("title", "New Event"),
                "start": event_data.get("start"),
                "end": event_data.get("end"),
                "description": event_data.get("description", ""),
                "provider": "microsoft",
                "created_at": datetime.utcnow().isoformat()
            }
            
            return ToolResult(
                success=True,
                data={"event": created_event},
                metadata={"provider": "microsoft", "operation": "create"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to create Microsoft Calendar event: {e}", self.name, recoverable=True)
    
    async def update_event(self, event_id: str, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Update Microsoft Calendar event"""
        try:
            # TODO: Implement actual Microsoft Graph API call
            await asyncio.sleep(0.2)  # Simulate API call
            
            updated_event = {
                "id": event_id,
                "title": event_data.get("title", "Updated Event"),
                "start": event_data.get("start"),
                "end": event_data.get("end"),
                "description": event_data.get("description", ""),
                "provider": "microsoft",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            return ToolResult(
                success=True,
                data={"event": updated_event},
                metadata={"provider": "microsoft", "operation": "update"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to update Microsoft Calendar event: {e}", self.name, recoverable=True)
    
    async def delete_event(self, event_id: str, context: Dict[str, Any]) -> ToolResult:
        """Delete Microsoft Calendar event"""
        try:
            # TODO: Implement actual Microsoft Graph API call
            await asyncio.sleep(0.1)  # Simulate API call
            
            return ToolResult(
                success=True,
                data={
                    "deleted_event_id": event_id,
                    "deleted_at": datetime.utcnow().isoformat()
                },
                metadata={"provider": "microsoft", "operation": "delete"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to delete Microsoft Calendar event: {e}", self.name, recoverable=True)