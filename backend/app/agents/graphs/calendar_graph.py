"""
Calendar Integration Workflow
Implements calendar operations with token validation and provider routing
Based on LANGGRAPH_AGENT_WORKFLOWS.md
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError


class CalendarGraph(BaseWorkflow):
    """
    Calendar Integration Workflow that:
    1. Validates OAuth tokens
    2. Routes to appropriate provider (Google/Microsoft)
    3. Executes calendar operations with idempotency
    4. Updates cache and sends notifications
    """
    
    def __init__(self):
        super().__init__(WorkflowType.CALENDAR)
        
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for calendar workflow"""
        return {
            "input_validator": self.input_validator_node,
            "token_validator": self.token_validator_node,
            "provider_selector": self.provider_selector_node,
            "sync_direction_router": self.sync_direction_router_node,
            "inbound_sync_node": self.inbound_sync_node,
            "outbound_sync_node": self.outbound_sync_node,
            "bidirectional_sync_node": self.bidirectional_sync_node,
            "provider_router": self.provider_router_node,
            "google_calendar_tool": self.google_calendar_tool_node,
            "microsoft_calendar_tool": self.microsoft_calendar_tool_node,
            "conflict_resolver": self.conflict_resolver_node,
            "cache_updater": self.cache_updater_node,
            "webhook_notifier": self.webhook_notifier_node,
            "structured_output": self.structured_output_node,
            "feedback_loop": self.feedback_loop_node,
            "response": self.response_node,
            "result_processor": self.result_processor_node,
            "trace_updater": self.trace_updater_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # Initial validation
            ("input_validator", "token_validator"),
            ("token_validator", "provider_selector"),
            ("provider_selector", "sync_direction_router"),
            
            # Sync direction routing
            ("sync_direction_router", self.sync_direction_router, {
                "inbound": "inbound_sync_node",
                "outbound": "outbound_sync_node",
                "bidirectional": "bidirectional_sync_node"
            }),
            
            # Sync processing
            ("inbound_sync_node", "conflict_resolver"),
            ("outbound_sync_node", "provider_router"),
            ("bidirectional_sync_node", "provider_router"),
            
            # Provider routing for outbound operations
            ("provider_router", self.provider_router, {
                "google": "google_calendar_tool",
                "microsoft": "microsoft_calendar_tool"
            }),
            
            # Post-execution processing
            ("google_calendar_tool", "conflict_resolver"),
            ("microsoft_calendar_tool", "conflict_resolver"),
            ("conflict_resolver", "cache_updater"),
            ("cache_updater", "webhook_notifier"),
            ("webhook_notifier", "structured_output"),
            ("structured_output", "feedback_loop"),
            ("feedback_loop", "response"),
            ("response", "result_processor"),
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    def token_validator_node(self, state: WorkflowState) -> WorkflowState:
        """Validate and refresh OAuth tokens"""
        state["current_node"] = "token_validator"
        state["visited_nodes"].append("token_validator")
        
        # Get required provider from input
        provider = state["input_data"].get("provider")
        if not provider:
            raise WorkflowError("Missing calendar provider", {"state": state})
        
        # Get connected accounts
        connected_accounts = state.get("connected_accounts", {})
        if provider not in connected_accounts:
            raise WorkflowError(
                f"No {provider} account connected", 
                {"provider": provider, "user_id": state["user_id"]}
            )
        
        account_info = connected_accounts[provider]
        
        # Check token expiry
        expires_at = account_info.get("expires_at")
        if expires_at:
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.utcnow() >= expiry_time:
                # TODO: Implement token refresh
                state["metrics"]["token_refresh_needed"] = True
                # For now, just log the need for refresh
        
        # Store validated token info
        state["input_data"]["validated_token"] = {
            "provider": provider,
            "token_valid": True,
            "expires_at": expires_at
        }
        
        return state
    
    def provider_selector_node(self, state: WorkflowState) -> WorkflowState:
        """Select appropriate calendar provider"""
        state["current_node"] = "provider_selector"
        state["visited_nodes"].append("provider_selector")
        
        provider = state["input_data"]["provider"].lower()
        
        # Validate supported providers
        supported_providers = ["google", "microsoft"]
        if provider not in supported_providers:
            raise WorkflowError(
                f"Unsupported provider: {provider}",
                {"supported": supported_providers}
            )
        
        state["input_data"]["selected_provider"] = provider
        
        return state
    
    def sync_direction_router(self, state: WorkflowState) -> str:
        """Route based on sync direction"""
        sync_direction = state["input_data"].get("sync_direction", "outbound")
        return sync_direction
    
    def provider_router(self, state: WorkflowState) -> str:
        """Route to appropriate provider tool"""
        return state["input_data"]["selected_provider"]
    
    def sync_direction_router_node(self, state: WorkflowState) -> WorkflowState:
        """Determine sync direction based on operation"""
        state["current_node"] = "sync_direction_router"
        state["visited_nodes"].append("sync_direction_router")
        
        operation = state["input_data"].get("operation", "list")
        
        # Determine sync direction
        if operation == "sync_inbound":
            state["input_data"]["sync_direction"] = "inbound"
        elif operation in ["create", "update", "delete"]:
            state["input_data"]["sync_direction"] = "outbound"
        elif operation == "bidirectional_sync":
            state["input_data"]["sync_direction"] = "bidirectional"
        else:
            # Default to outbound for list and other operations
            state["input_data"]["sync_direction"] = "outbound"
        
        return state
    
    async def inbound_sync_node(self, state: WorkflowState) -> WorkflowState:
        """Handle inbound synchronization from calendar providers"""
        state["current_node"] = "inbound_sync"
        state["visited_nodes"].append("inbound_sync")
        
        from ..services.calendar_sync_service import get_calendar_sync_service
        
        try:
            calendar_service = get_calendar_sync_service()
            user_id = state["user_id"]
            
            # Perform inbound sync from all connected providers
            sync_results = await calendar_service.sync_user_calendars(
                user_id=user_id,
                days_ahead=state["input_data"].get("days_ahead", 30),
                force_refresh=state["input_data"].get("force_refresh", False)
            )
            
            state["output_data"] = {
                "operation": "inbound_sync",
                "result": sync_results,
                "success": len(sync_results.get("errors", [])) == 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["metrics"]["inbound_sync"] = {
                "providers_synced": len(sync_results.get("providers_synced", [])),
                "total_events": sync_results.get("total_events", 0),
                "errors": len(sync_results.get("errors", []))
            }
            
        except Exception as e:
            state["output_data"] = {
                "operation": "inbound_sync",
                "result": {},
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
    def outbound_sync_node(self, state: WorkflowState) -> WorkflowState:
        """Handle outbound synchronization to calendar providers"""
        state["current_node"] = "outbound_sync"
        state["visited_nodes"].append("outbound_sync")
        
        # Outbound sync proceeds to provider-specific tools
        # No additional processing needed here
        return state
    
    async def bidirectional_sync_node(self, state: WorkflowState) -> WorkflowState:
        """Handle bidirectional synchronization"""
        state["current_node"] = "bidirectional_sync"
        state["visited_nodes"].append("bidirectional_sync")
        
        from ..services.calendar_sync_service import get_calendar_sync_service
        
        try:
            calendar_service = get_calendar_sync_service()
            user_id = state["user_id"]
            
            # First, perform inbound sync
            inbound_results = await calendar_service.sync_user_calendars(
                user_id=user_id,
                days_ahead=30,
                force_refresh=True
            )
            
            # Then handle any outbound operations from the input
            outbound_results = {}
            if state["input_data"].get("event_data"):
                # This is a create/update operation, proceed to provider tools
                pass
            
            state["output_data"] = {
                "operation": "bidirectional_sync",
                "inbound_result": inbound_results,
                "outbound_result": outbound_results,
                "success": len(inbound_results.get("errors", [])) == 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            state["output_data"] = {
                "operation": "bidirectional_sync",
                "result": {},
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return state
    
    def provider_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to provider-specific processing"""
        state["current_node"] = "provider_router"
        state["visited_nodes"].append("provider_router")
        
        # No additional processing needed, routing handled by conditional edge
        return state
    
    async def google_calendar_tool_node(self, state: WorkflowState) -> WorkflowState:
        """Execute Google Calendar operations"""
        state["current_node"] = "google_calendar_tool"
        state["visited_nodes"].append("google_calendar_tool")
        
        from ..tools import GoogleCalendarTool
        
        try:
            # Initialize Google Calendar tool
            google_tool = GoogleCalendarTool()
            
            # Prepare tool input
            tool_input = {
                "operation": state["input_data"].get("operation", "list"),
                "start_date": state["input_data"].get("start_date"),
                "end_date": state["input_data"].get("end_date"),
                "event_data": state["input_data"].get("event_data"),
                "event_id": state["input_data"].get("event_id")
            }
            
            # Prepare context
            tool_context = {
                "user_id": state["user_id"],
                "connected_accounts": state.get("connected_accounts", {}),
                "user_context": state.get("user_context", {})
            }
            
            # Execute tool
            tool_result = await google_tool.execute(tool_input, tool_context)
            
            # Store result
            state["output_data"] = {
                "provider": "google",
                "operation": tool_input["operation"],
                "result": tool_result.data,
                "success": tool_result.success,
                "error": tool_result.error,
                "execution_time": tool_result.execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store metrics
            state["metrics"]["google_calendar_execution"] = {
                "success": tool_result.success,
                "execution_time": tool_result.execution_time,
                "operation": tool_input["operation"]
            }
            
        except Exception as e:
            # Handle tool execution errors
            state["output_data"] = {
                "provider": "google",
                "operation": state["input_data"].get("operation", "list"),
                "result": {},
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["metrics"]["google_calendar_execution"] = {
                "success": False,
                "error": str(e),
                "operation": state["input_data"].get("operation", "list")
            }
        
        return state
    
    async def microsoft_calendar_tool_node(self, state: WorkflowState) -> WorkflowState:
        """Execute Microsoft Calendar operations"""
        state["current_node"] = "microsoft_calendar_tool"
        state["visited_nodes"].append("microsoft_calendar_tool")
        
        from ..tools import MicrosoftCalendarTool
        
        try:
            # Initialize Microsoft Calendar tool
            microsoft_tool = MicrosoftCalendarTool()
            
            # Prepare tool input
            tool_input = {
                "operation": state["input_data"].get("operation", "list"),
                "start_date": state["input_data"].get("start_date"),
                "end_date": state["input_data"].get("end_date"),
                "event_data": state["input_data"].get("event_data"),
                "event_id": state["input_data"].get("event_id")
            }
            
            # Prepare context
            tool_context = {
                "user_id": state["user_id"],
                "connected_accounts": state.get("connected_accounts", {}),
                "user_context": state.get("user_context", {})
            }
            
            # Execute tool
            tool_result = await microsoft_tool.execute(tool_input, tool_context)
            
            # Store result
            state["output_data"] = {
                "provider": "microsoft",
                "operation": tool_input["operation"],
                "result": tool_result.data,
                "success": tool_result.success,
                "error": tool_result.error,
                "execution_time": tool_result.execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store metrics
            state["metrics"]["microsoft_calendar_execution"] = {
                "success": tool_result.success,
                "execution_time": tool_result.execution_time,
                "operation": tool_input["operation"]
            }
            
        except Exception as e:
            # Handle tool execution errors
            state["output_data"] = {
                "provider": "microsoft",
                "operation": state["input_data"].get("operation", "list"),
                "result": {},
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["metrics"]["microsoft_calendar_execution"] = {
                "success": False,
                "error": str(e),
                "operation": state["input_data"].get("operation", "list")
            }
        
        return state
    
    def cache_updater_node(self, state: WorkflowState) -> WorkflowState:
        """Update Redis cache with calendar data"""
        state["current_node"] = "cache_updater"
        state["visited_nodes"].append("cache_updater")
        
        # TODO: Implement Redis cache updates
        # For now, just track in metrics
        cache_key = f"calendar:{state['user_id']}:{state['input_data']['selected_provider']}"
        
        state["metrics"]["cache_update"] = {
            "cache_key": cache_key,
            "operation": state["input_data"].get("operation"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return state
    
    def webhook_notifier_node(self, state: WorkflowState) -> WorkflowState:
        """Send real-time webhook notifications"""
        state["current_node"] = "webhook_notifier"
        state["visited_nodes"].append("webhook_notifier")
        
        # TODO: Implement webhook notifications
        # For now, just track in metrics
        state["metrics"]["webhook_notification"] = {
            "user_id": state["user_id"],
            "provider": state["input_data"]["selected_provider"],
            "operation": state["input_data"].get("operation"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return state
    
    async def conflict_resolver_node(self, state: WorkflowState) -> WorkflowState:
        """Resolve calendar synchronization conflicts"""
        state["current_node"] = "conflict_resolver"
        state["visited_nodes"].append("conflict_resolver")
        
        from ..services.calendar_sync_service import get_calendar_sync_service
        
        try:
            calendar_service = get_calendar_sync_service()
            user_id = state["user_id"]
            
            # Detect and resolve conflicts
            conflict_results = await calendar_service.detect_and_resolve_conflicts(user_id)
            
            state["metrics"]["conflict_resolution"] = {
                "conflicts_detected": conflict_results.get("conflicts_detected", 0),
                "conflicts_resolved": conflict_results.get("conflicts_resolved", 0),
                "resolution_strategy": conflict_results.get("resolution_strategy", "prefer_google")
            }
            
            # Add conflict info to output if conflicts were found
            if conflict_results.get("conflicts_detected", 0) > 0:
                if "conflict_resolution" not in state["output_data"]:
                    state["output_data"]["conflict_resolution"] = conflict_results
            
        except Exception as e:
            logger.error(f"Error in conflict resolver: {e}")
            state["metrics"]["conflict_resolution_error"] = str(e)
        
        return state
    
    def _mock_calendar_operation(self, provider: str, operation: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock calendar operations for development"""
        
        if operation == "list":
            return {
                "events": [
                    {
                        "id": "event_1",
                        "title": "Team Meeting",
                        "start": "2024-01-15T10:00:00Z",
                        "end": "2024-01-15T11:00:00Z",
                        "provider": provider
                    },
                    {
                        "id": "event_2", 
                        "title": "Project Review",
                        "start": "2024-01-15T14:00:00Z",
                        "end": "2024-01-15T15:00:00Z",
                        "provider": provider
                    }
                ],
                "total": 2
            }
        
        elif operation == "create":
            event_data = input_data.get("event", {})
            return {
                "id": "new_event_123",
                "title": event_data.get("title", "New Event"),
                "start": event_data.get("start"),
                "end": event_data.get("end"),
                "created": datetime.utcnow().isoformat(),
                "provider": provider
            }
        
        elif operation == "update":
            event_id = input_data.get("event_id")
            event_data = input_data.get("event", {})
            return {
                "id": event_id,
                "title": event_data.get("title", "Updated Event"),
                "start": event_data.get("start"),
                "end": event_data.get("end"),
                "updated": datetime.utcnow().isoformat(),
                "provider": provider
            }
        
        elif operation == "delete":
            event_id = input_data.get("event_id")
            return {
                "id": event_id,
                "deleted": True,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": provider
            }
        
        else:
            return {
                "error": f"Unsupported operation: {operation}",
                "supported": ["list", "create", "update", "delete"]
            }
    
    def _create_structured_output(self, state: WorkflowState) -> Dict[str, Any]:
        """Create calendar-specific structured output"""
        output_data = state.get("output_data", {})
        operation = state["input_data"].get("operation", "unknown")
        provider = state["input_data"].get("selected_provider", "unknown")
        
        # Extract calendar-specific data
        calendar_data = {
            "provider": provider,
            "operation": operation,
            "events": output_data.get("result", {}).get("events", []),
            "event_count": len(output_data.get("result", {}).get("events", [])),
            "conflicts": output_data.get("conflict_resolution", {}).get("conflicts_detected", 0) > 0,
            "sync_results": output_data.get("result") if operation.endswith("sync") else None
        }
        
        return calendar_data
    
    def _requires_user_feedback(self, state: WorkflowState) -> bool:
        """Determine if calendar workflow needs user feedback"""
        # Check base conditions first
        if super()._requires_user_feedback(state):
            return True
        
        # Calendar-specific feedback conditions
        output_data = state.get("output_data", {})
        
        # Need feedback if there are conflicts
        if output_data.get("conflict_resolution", {}).get("conflicts_detected", 0) > 0:
            return True
        
        # Need feedback if operation failed due to missing permissions
        if not output_data.get("success", True):
            error = output_data.get("error", "")
            if "permission" in error.lower() or "access" in error.lower():
                return True
        
        return False
    
    def _create_feedback_request(self, state: WorkflowState) -> Dict[str, Any]:
        """Create calendar-specific feedback request"""
        output_data = state.get("output_data", {})
        
        # Check for conflicts
        conflict_info = output_data.get("conflict_resolution", {})
        if conflict_info.get("conflicts_detected", 0) > 0:
            return {
                "message": f"I found {conflict_info['conflicts_detected']} calendar conflicts. How would you like me to resolve them?",
                "options": ["Prefer Google Calendar", "Prefer Microsoft Calendar", "Ask me for each conflict"],
                "required_info": ["conflict_resolution_preference"],
                "context": {
                    "conflicts": conflict_info,
                    "workflow_type": state["workflow_type"]
                }
            }
        
        # Check for permission errors
        if not output_data.get("success", True):
            error = output_data.get("error", "")
            if "permission" in error.lower():
                return {
                    "message": "I need additional permissions to access your calendar. Would you like me to guide you through re-authorization?",
                    "options": ["Yes, help me re-authorize", "Try a different approach", "Skip for now"],
                    "required_info": ["authorization_preference"],
                    "context": {
                        "error": error,
                        "provider": state["input_data"].get("selected_provider")
                    }
                }
        
        # Fallback to parent implementation
        return super()._create_feedback_request(state)
    
    def _get_suggested_actions(self, state: WorkflowState) -> List[str]:
        """Get calendar-specific suggested actions"""
        actions = []
        operation = state["input_data"].get("operation")
        
        if state.get("error"):
            actions.extend(["Try again", "Check permissions", "Re-authorize account"])
        else:
            if operation == "list":
                actions.extend(["Create new event", "Sync calendars", "Check for conflicts"])
            elif operation in ["create", "update"]:
                actions.extend(["View updated schedule", "Create another event", "Set reminder"])
            elif operation == "sync_inbound":
                actions.extend(["View synced events", "Resolve conflicts", "Sync again"])
            elif operation == "delete":
                actions.extend(["View remaining events", "Create replacement event"])
        
        return actions[:5]