"""
Calendar integration tools for PulsePlan agents.
Handles Google and Microsoft calendar operations across different providers.
"""
from typing import Dict, Any
import asyncio
from datetime import datetime

from ..core.base import CalendarTool, ToolResult, ToolError


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
            import httpx
            
            # Get Microsoft access token
            access_token = context["oauth_tokens"]["microsoft_access_token"]
            
            # Prepare Graph API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Build query parameters
            params = {
                "$select": "id,subject,start,end,body,location,attendees,categories",
                "$orderby": "start/dateTime",
                "$top": 100
            }
            
            if start_date:
                params["$filter"] = f"start/dateTime ge '{start_date}'"
            
            if end_date:
                if "$filter" in params:
                    params["$filter"] += f" and end/dateTime le '{end_date}'"
                else:
                    params["$filter"] = f"end/dateTime le '{end_date}'"
            
            # Make Graph API call
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/events",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                
                graph_data = response.json()
                events = []
                
                for event in graph_data.get("value", []):
                    events.append({
                        "id": event["id"],
                        "title": event["subject"],
                        "start": event["start"]["dateTime"] + "Z" if not event["start"]["dateTime"].endswith("Z") else event["start"]["dateTime"],
                        "end": event["end"]["dateTime"] + "Z" if not event["end"]["dateTime"].endswith("Z") else event["end"]["dateTime"],
                        "description": event.get("body", {}).get("content", ""),
                        "location": event.get("location", {}).get("displayName", ""),
                        "provider": "microsoft",
                        "raw_data": event
                    })
                
                return ToolResult(
                    success=True,
                    data={
                        "events": events,
                        "total": len(events),
                        "date_range": {"start": start_date, "end": end_date}
                    },
                    metadata={"provider": "microsoft", "operation": "list"}
                )
            
        except Exception as e:
            raise ToolError(f"Failed to list Microsoft Calendar events: {e}", self.name, recoverable=True)
    
    async def create_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Create Microsoft Calendar event"""
        try:
            import httpx
            
            # Get Microsoft access token
            access_token = context["oauth_tokens"]["microsoft_access_token"]
            
            # Prepare Graph API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Build event payload
            event_payload = {
                "subject": event_data.get("title", "New Event"),
                "start": {
                    "dateTime": event_data.get("start"),
                    "timeZone": event_data.get("timezone", "UTC")
                },
                "end": {
                    "dateTime": event_data.get("end"),
                    "timeZone": event_data.get("timezone", "UTC")
                }
            }
            
            if event_data.get("description"):
                event_payload["body"] = {
                    "contentType": "text",
                    "content": event_data["description"]
                }
                
            if event_data.get("location"):
                event_payload["location"] = {
                    "displayName": event_data["location"]
                }
            
            # Make Graph API call to create event
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://graph.microsoft.com/v1.0/me/events",
                    headers=headers,
                    json=event_payload,
                    timeout=30.0
                )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                
                created_event_data = response.json()
                
                created_event = {
                    "id": created_event_data["id"],
                    "title": created_event_data["subject"],
                    "start": created_event_data["start"]["dateTime"],
                    "end": created_event_data["end"]["dateTime"],
                    "description": created_event_data.get("body", {}).get("content", ""),
                    "location": created_event_data.get("location", {}).get("displayName", ""),
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
            import httpx
            
            # Get Microsoft access token
            access_token = context["oauth_tokens"]["microsoft_access_token"]
            
            # Prepare Graph API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Build update payload with only provided fields
            update_payload = {}
            
            if "title" in event_data:
                update_payload["subject"] = event_data["title"]
            
            if "start" in event_data:
                update_payload["start"] = {
                    "dateTime": event_data["start"],
                    "timeZone": event_data.get("timezone", "UTC")
                }
                
            if "end" in event_data:
                update_payload["end"] = {
                    "dateTime": event_data["end"],
                    "timeZone": event_data.get("timezone", "UTC")
                }
                
            if "description" in event_data:
                update_payload["body"] = {
                    "contentType": "text",
                    "content": event_data["description"]
                }
                
            if "location" in event_data:
                update_payload["location"] = {
                    "displayName": event_data["location"]
                }
            
            # Make Graph API call to update event
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
                    headers=headers,
                    json=update_payload,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                
                updated_event_data = response.json()
                
                updated_event = {
                    "id": updated_event_data["id"],
                    "title": updated_event_data["subject"],
                    "start": updated_event_data["start"]["dateTime"],
                    "end": updated_event_data["end"]["dateTime"],
                    "description": updated_event_data.get("body", {}).get("content", ""),
                    "location": updated_event_data.get("location", {}).get("displayName", ""),
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
            import httpx
            
            # Get Microsoft access token
            access_token = context["oauth_tokens"]["microsoft_access_token"]
            
            # Prepare Graph API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Make Graph API call to delete event
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code not in [200, 204]:
                    raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                
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


class UnifiedCalendarTool:
    """Unified calendar tool that can handle multiple providers"""
    
    def __init__(self):
        self.google_tool = GoogleCalendarTool()
        self.microsoft_tool = MicrosoftCalendarTool()
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute calendar operation using appropriate provider"""
        try:
            operation = input_data.get("operation")
            provider = input_data.get("provider", "auto")
            
            # Auto-detect provider based on available tokens
            if provider == "auto":
                oauth_tokens = context.get("oauth_tokens", {})
                if "google_access_token" in oauth_tokens:
                    provider = "google"
                elif "microsoft_access_token" in oauth_tokens:
                    provider = "microsoft"
                else:
                    return ToolResult(
                        success=False,
                        error="No calendar provider tokens available",
                        metadata={"operation": operation}
                    )
            
            # Route to appropriate tool
            if provider == "google":
                return await self.google_tool.execute(input_data, context)
            elif provider == "microsoft":
                return await self.microsoft_tool.execute(input_data, context)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported calendar provider: {provider}",
                    metadata={"operation": operation}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calendar operation failed: {e}",
                metadata={"operation": input_data.get("operation")}
            )