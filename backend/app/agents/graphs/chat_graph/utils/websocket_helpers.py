"""
WebSocket Helper Utilities
Centralized WebSocket emission helpers to ensure consistency
"""
from typing import Dict, Any, Optional


class WebSocketHelper:
    """Helper class for consistent WebSocket emissions"""
    
    async def emit_node_status(self, workflow_id: str, node_name: str, status: str, data: Optional[Dict[str, Any]] = None):
        """Emit node status update with error handling"""
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_node_update(workflow_id, node_name, status, data or {})
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit {node_name} {status}: {e}")
    
    async def emit_tool_status(self, workflow_id: str, tool_name: str, status: str, result: Optional[str] = None, execution_time: Optional[float] = None):
        """Emit tool execution status with error handling"""
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_tool_update(workflow_id, tool_name, status, result, execution_time)
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit {tool_name} {status}: {e}")
    
    async def emit_task_created(self, workflow_id: str, task_data: Dict[str, Any]):
        """Emit task creation event with error handling"""
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_task_created(workflow_id, task_data)
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit task_created: {e}")
    
    async def emit_workflow_completion(self, workflow_id: str, output_data: Dict[str, Any]):
        """Emit workflow completion with error handling"""
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_workflow_status(workflow_id, "completed", output_data)
            await websocket_manager.emit_node_update(workflow_id, "result_processor", "completed")
            print(f"📡 [WEBSOCKET] Emitted workflow completion for {workflow_id}")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit workflow completion: {e}")