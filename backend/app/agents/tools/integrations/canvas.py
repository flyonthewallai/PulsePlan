"""
Canvas LMS integration tool for PulsePlan agents.
Handles Canvas assignment and course synchronization through manual sync requests.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.base import BaseTool, ToolResult, ToolError
from app.jobs.canvas.canvas_sync import get_canvas_sync

logger = logging.getLogger(__name__)

class CanvasLMSTool(BaseTool):
    """
    Canvas LMS integration tool wrapper.
    
    Delegates to the Canvas sync job for actual synchronization operations.
    Primary use cases:
    1. User-requested Canvas sync
    2. Getting upcoming assignments
    3. Checking sync status
    """
    
    def __init__(self):
        super().__init__(
            name="canvas_lms",
            description="Canvas LMS integration for assignment and course data synchronization"
        )
        
        self.canvas_sync = get_canvas_sync()
    
    def get_required_tokens(self) -> List[str]:
        """Canvas requires API token from user's Canvas integration"""
        return ["canvas_api_token"]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for Canvas operations"""
        operation = input_data.get("operation")
        
        if not operation:
            return False
        
        valid_operations = {
            "sync_canvas_data", "get_upcoming_assignments", "force_sync"
        }
        
        return operation in valid_operations
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute Canvas operation - manual sync trigger"""
        start_time = datetime.utcnow()
        
        try:
            operation = input_data.get("operation")
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required in context", self.name)
            
            # Get Canvas credentials from context or input
            canvas_config = context.get("canvas_config", {})
            canvas_api_key = input_data.get("canvas_api_key") or canvas_config.get("access_token")
            canvas_url = input_data.get("canvas_url") or canvas_config.get("base_url")
            
            # Route to appropriate operation
            if operation == "sync_canvas_data" or operation == "force_sync":
                force_refresh = operation == "force_sync" or input_data.get("force_refresh", False)
                include_grades = input_data.get("include_grades", False)
                
                result = await self.canvas_sync.sync_user_canvas_data(
                    user_id=user_id,
                    canvas_api_key=canvas_api_key,
                    canvas_url=canvas_url,
                    force_refresh=force_refresh,
                    include_grades=include_grades
                )
                
            elif operation == "get_upcoming_assignments":
                days_ahead = input_data.get("days_ahead", 14)
                
                result = await self.canvas_sync.get_upcoming_assignments(
                    user_id=user_id,
                    days_ahead=days_ahead,
                    canvas_api_key=canvas_api_key,
                    canvas_url=canvas_url
                )
                
            else:
                raise ToolError(f"Unknown operation: {operation}", self.name)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            tool_result = ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": user_id,
                    "canvas_url": canvas_url
                }
            )
            
            self.log_execution(input_data, tool_result, context)
            return tool_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Canvas LMS tool execution failed: {e}")
            
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "operation": input_data.get("operation"),
                    "user_id": context.get("user_id")
                }
            )
    

# Create global instance
canvas_lms_tool = CanvasLMSTool()