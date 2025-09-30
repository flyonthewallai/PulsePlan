"""
Preferences management tool for PulsePlan agents.
Handles structured user constraints, rules, and scheduling preferences.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.base import BaseTool, ToolResult, ToolError
from app.services.infrastructure.preferences_service import (
    get_preferences_service, 
    PreferencesService,
    PreferenceCreate,
    PreferenceUpdate
)

logger = logging.getLogger(__name__)

class PreferencesTool(BaseTool):
    """
    Preferences management tool for structured user constraints and settings.
    
    This tool provides agents with the ability to:
    1. Get user preferences and constraints
    2. Set and update user preferences  
    3. Check time constraints against preferences
    4. Validate scheduling proposals
    5. Get preference defaults
    """
    
    def __init__(self):
        super().__init__(
            name="preferences",
            description="Manage structured user preferences, constraints, and settings for scheduling and planning"
        )
        
        self.preferences_service = get_preferences_service()
    
    def get_required_tokens(self) -> List[str]:
        """No OAuth tokens required - uses internal preferences system"""
        return []
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for preferences operations"""
        operation = input_data.get("operation")
        
        if not operation:
            return False
        
        valid_operations = {
            "get_preference", "get_preferences_by_category", "set_preference",
            "update_preference", "delete_preference", "get_scheduling_constraints",
            "check_time_constraint", "get_defaults", "validate_schedule"
        }
        
        return operation in valid_operations
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute preferences operation based on input"""
        start_time = datetime.utcnow()
        
        try:
            operation = input_data.get("operation")
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required in context", self.name)
            
            # Route to appropriate operation
            if operation == "get_preference":
                result = await self._get_preference(input_data, user_id)
            elif operation == "get_preferences_by_category":
                result = await self._get_preferences_by_category(input_data, user_id)
            elif operation == "set_preference":
                result = await self._set_preference(input_data, user_id)
            elif operation == "update_preference":
                result = await self._update_preference(input_data, user_id)
            elif operation == "delete_preference":
                result = await self._delete_preference(input_data, user_id)
            elif operation == "get_scheduling_constraints":
                result = await self._get_scheduling_constraints(input_data, user_id)
            elif operation == "check_time_constraint":
                result = await self._check_time_constraint(input_data, user_id)
            elif operation == "get_defaults":
                result = await self._get_defaults(input_data, user_id)
            elif operation == "validate_schedule":
                result = await self._validate_schedule(input_data, user_id)
            else:
                raise ToolError(f"Unknown operation: {operation}", self.name)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            tool_result = ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": user_id
                }
            )
            
            self.log_execution(input_data, tool_result, context)
            return tool_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Preferences tool execution failed: {e}")
            
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": context.get("user_id")
                }
            )
    
    async def _get_preference(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get a specific preference by category and key"""
        category = input_data.get("category")
        preference_key = input_data.get("preference_key")
        
        if not category or not preference_key:
            raise ToolError("category and preference_key are required", self.name)
        
        preference = await self.preferences_service.get_preference(user_id, category, preference_key)
        
        if preference:
            return {
                "found": True,
                "preference": {
                    "id": preference.id,
                    "category": preference.category,
                    "preference_key": preference.preference_key,
                    "value": preference.value,
                    "description": preference.description,
                    "is_active": preference.is_active,
                    "priority": preference.priority,
                    "created_at": preference.created_at.isoformat(),
                    "updated_at": preference.updated_at.isoformat()
                }
            }
        else:
            return {
                "found": False,
                "default_value": await self._get_default_value(category, preference_key)
            }
    
    async def _get_preferences_by_category(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get all preferences for a category"""
        category = input_data.get("category")
        active_only = input_data.get("active_only", True)
        
        preferences = await self.preferences_service.get_preferences_by_category(
            user_id, category, active_only
        )
        
        formatted_preferences = []
        for pref in preferences:
            formatted_preferences.append({
                "id": pref.id,
                "category": pref.category,
                "preference_key": pref.preference_key,
                "value": pref.value,
                "description": pref.description,
                "is_active": pref.is_active,
                "priority": pref.priority,
                "created_at": pref.created_at.isoformat(),
                "updated_at": pref.updated_at.isoformat()
            })
        
        return {
            "category": category,
            "preferences": formatted_preferences,
            "total_count": len(formatted_preferences)
        }
    
    async def _set_preference(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Set/create a preference"""
        category = input_data.get("category")
        preference_key = input_data.get("preference_key")
        value = input_data.get("value")
        description = input_data.get("description")
        is_active = input_data.get("is_active", True)
        priority = input_data.get("priority", 1)
        
        if not category or not preference_key or value is None:
            raise ToolError("category, preference_key, and value are required", self.name)
        
        # Validate preference structure
        validation_result = self._validate_preference_value(category, preference_key, value)
        if not validation_result["valid"]:
            raise ToolError(f"Invalid preference value: {validation_result['error']}", self.name)
        
        preference = PreferenceCreate(
            category=category,
            preference_key=preference_key,
            value=value,
            description=description,
            is_active=is_active,
            priority=priority
        )
        
        preference_id = await self.preferences_service.set_preference(user_id, preference)
        
        if not preference_id:
            raise ToolError("Failed to set preference", self.name)
        
        return {
            "preference_id": preference_id,
            "category": category,
            "preference_key": preference_key,
            "set_at": datetime.utcnow().isoformat()
        }
    
    async def _update_preference(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing preference"""
        category = input_data.get("category")
        preference_key = input_data.get("preference_key")
        value = input_data.get("value")
        description = input_data.get("description")
        is_active = input_data.get("is_active")
        priority = input_data.get("priority")
        
        if not category or not preference_key:
            raise ToolError("category and preference_key are required", self.name)
        
        updates = PreferenceUpdate(
            value=value,
            description=description,
            is_active=is_active,
            priority=priority
        )
        
        success = await self.preferences_service.update_preference(
            user_id, category, preference_key, updates
        )
        
        if not success:
            raise ToolError("Failed to update preference or preference not found", self.name)
        
        return {
            "updated": True,
            "category": category,
            "preference_key": preference_key,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def _delete_preference(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Delete a preference"""
        category = input_data.get("category")
        preference_key = input_data.get("preference_key")
        
        if not category or not preference_key:
            raise ToolError("category and preference_key are required", self.name)
        
        success = await self.preferences_service.delete_preference(user_id, category, preference_key)
        
        if not success:
            raise ToolError("Failed to delete preference or preference not found", self.name)
        
        return {
            "deleted": True,
            "category": category,
            "preference_key": preference_key,
            "deleted_at": datetime.utcnow().isoformat()
        }
    
    async def _get_scheduling_constraints(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get all scheduling constraints for the user"""
        constraints = await self.preferences_service.get_scheduling_constraints(user_id)
        
        return {
            "user_id": user_id,
            "scheduling_constraints": constraints,
            "constraint_count": len(constraints)
        }
    
    async def _check_time_constraint(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Check if a proposed time violates any constraints"""
        proposed_time = input_data.get("proposed_time")
        
        if not proposed_time:
            raise ToolError("proposed_time is required", self.name)
        
        # Validate proposed_time structure
        required_fields = ["day", "start_time", "end_time"]
        for field in required_fields:
            if field not in proposed_time:
                raise ToolError(f"proposed_time must include {field}", self.name)
        
        constraint_check = await self.preferences_service.check_time_constraint(
            user_id, proposed_time
        )
        
        return {
            "proposed_time": proposed_time,
            "constraint_check": constraint_check,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def _get_defaults(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get default preference values for a category"""
        category = input_data.get("category")
        
        if not category:
            raise ToolError("category is required", self.name)
        
        defaults = await self.preferences_service.get_preference_defaults(category)
        
        return {
            "category": category,
            "defaults": defaults
        }
    
    async def _validate_schedule(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Validate a proposed schedule against all user constraints"""
        schedule_items = input_data.get("schedule_items", [])
        
        if not schedule_items:
            raise ToolError("schedule_items is required", self.name)
        
        validation_results = []
        overall_valid = True
        
        for i, item in enumerate(schedule_items):
            if "proposed_time" not in item:
                validation_results.append({
                    "item_index": i,
                    "valid": False,
                    "error": "Missing proposed_time"
                })
                overall_valid = False
                continue
            
            constraint_check = await self.preferences_service.check_time_constraint(
                user_id, item["proposed_time"]
            )
            
            item_valid = constraint_check["allowed"]
            overall_valid = overall_valid and item_valid
            
            validation_results.append({
                "item_index": i,
                "item_title": item.get("title", f"Item {i+1}"),
                "proposed_time": item["proposed_time"],
                "valid": item_valid,
                "violations": constraint_check.get("violations", []),
                "warnings": constraint_check.get("warnings", [])
            })
        
        return {
            "schedule_valid": overall_valid,
            "total_items": len(schedule_items),
            "valid_items": sum(1 for result in validation_results if result["valid"]),
            "validation_results": validation_results,
            "validated_at": datetime.utcnow().isoformat()
        }
    
    def _validate_preference_value(self, category: str, key: str, value: Any) -> Dict[str, Any]:
        """Validate preference value structure"""
        try:
            # Basic validation - in production, implement comprehensive validation
            if category == "scheduling":
                if key == "no_work_windows" and not isinstance(value, list):
                    return {"valid": False, "error": "no_work_windows must be a list"}
                if key == "preferred_study_blocks" and not isinstance(value, dict):
                    return {"valid": False, "error": "preferred_study_blocks must be a dict"}
            
            elif category == "study":
                if key == "difficulty_ordering" and value not in ["hardest_first", "easiest_first", "mixed"]:
                    return {"valid": False, "error": "Invalid difficulty_ordering value"}
            
            elif category == "notifications":
                if key == "channels" and not isinstance(value, dict):
                    return {"valid": False, "error": "notification channels must be a dict"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _get_default_value(self, category: str, preference_key: str) -> Any:
        """Get default value for a specific preference"""
        defaults = await self.preferences_service.get_preference_defaults(category)
        return defaults.get(preference_key)

# Create global instance
preferences_tool = PreferencesTool()