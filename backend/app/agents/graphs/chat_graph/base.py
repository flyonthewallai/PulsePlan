"""
Base imports and references for ChatGraph modules
Provides easy access to base workflow components
"""

# Re-export base components for easy import within chat_graph modules
from ..base import (
    WorkflowType,
    WorkflowState, 
    WorkflowError,
    BaseWorkflow,
    create_initial_state
)

__all__ = [
    'WorkflowType',
    'WorkflowState',
    'WorkflowError', 
    'BaseWorkflow',
    'create_initial_state'
]