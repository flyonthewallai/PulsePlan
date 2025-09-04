"""
Input Validation Utilities
Common validation helpers for ChatGraph workflow
"""
from typing import Dict, Any
from ..base import WorkflowState, WorkflowError


class InputValidator:
    """Validation utilities for ChatGraph inputs"""
    
    @staticmethod
    def validate_query(state: WorkflowState) -> None:
        """Validate user query input"""
        query = state["input_data"].get("query", "").strip()
        
        if not query:
            raise WorkflowError("Empty user query provided", {
                "state": state,
                "validation_error": "query_empty"
            })
        
        if len(query) > 10000:  # 10KB limit
            raise WorkflowError("Query too long", {
                "query_length": len(query),
                "max_length": 10000,
                "validation_error": "query_too_long"
            })
    
    @staticmethod
    def validate_state_structure(state: WorkflowState) -> None:
        """Validate required state structure"""
        required_fields = ["user_id", "input_data", "workflow_type"]
        
        for field in required_fields:
            if field not in state:
                raise WorkflowError(f"Missing required state field: {field}", {
                    "missing_field": field,
                    "validation_error": "missing_state_field"
                })
    
    @staticmethod
    def validate_user_context(state: WorkflowState) -> None:
        """Validate user context availability"""
        user_context = state.get("user_context", {})
        
        # Log available context for debugging
        print(f"🔍 [VALIDATION] Available user context keys: {list(user_context.keys())}")
        
        # Context is optional, so this is just informational
        if not user_context:
            print("⚠️ [VALIDATION] No user context available - responses may be limited")