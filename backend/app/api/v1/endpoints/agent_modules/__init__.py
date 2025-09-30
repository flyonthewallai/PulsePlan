"""
Agent API Module
Modular agent system with separated concerns
"""
from .models import UnifiedAgentRequest, UnifiedAgentResponse, TaskStatusRequest, TaskCancelRequest
from .conversation import get_user_active_conversation, set_user_active_conversation
from .operations import execute_crud_operation_direct, execute_task_listing_direct
from .workflows import execute_workflow_background

__all__ = [
    'UnifiedAgentRequest',
    'UnifiedAgentResponse',
    'TaskStatusRequest',
    'TaskCancelRequest',
    'get_user_active_conversation',
    'set_user_active_conversation',
    'execute_crud_operation_direct',
    'execute_task_listing_direct',
    'execute_workflow_background'
]