"""
User preferences service for managing structured user constraints and settings.
Handles scheduling rules, study preferences, and other user configuration.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field

from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)

@dataclass
class UserPreference:
    """Represents a user preference entry"""
    id: str
    user_id: str
    category: str
    preference_key: str
    value: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PreferenceUpdate(BaseModel):
    """Model for updating preferences"""
    value: Dict[str, Any]
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class PreferenceCreate(BaseModel):
    """Model for creating preferences"""
    category: str
    preference_key: str
    value: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 1

class PreferencesService:
    """Service for managing user preferences"""
    
    def __init__(self):
        self.db = get_supabase()
    
    async def get_preference(
        self, 
        user_id: str, 
        category: str, 
        preference_key: str
    ) -> Optional[UserPreference]:
        """Get a specific preference by category and key"""
        try:
            result = self.db.from_("user_preferences").select("*").eq(
                "user_id", user_id
            ).eq("category", category).eq("preference_key", preference_key).eq(
                "is_active", True
            ).order("priority", desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                row = result.data[0]
                return UserPreference(
                    id=row["id"],
                    user_id=row["user_id"],
                    category=row["category"],
                    preference_key=row["preference_key"],
                    value=row["value"],
                    description=row.get("description"),
                    is_active=row["is_active"],
                    priority=row["priority"],
                    created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get preference {category}.{preference_key}: {e}")
            return None
    
    async def get_preference_value(
        self, 
        user_id: str, 
        category: str, 
        preference_key: str,
        default: Any = None
    ) -> Any:
        """Get just the value of a preference, with optional default"""
        try:
            # Use the database function for efficiency
            result = self.db.rpc("get_preference_value", {
                "p_user_id": user_id,
                "p_category": category,
                "p_preference_key": preference_key
            }).execute()
            
            if result.data:
                return result.data
            
            return default
            
        except Exception as e:
            logger.error(f"Failed to get preference value {category}.{preference_key}: {e}")
            return default
    
    async def get_preferences_by_category(
        self, 
        user_id: str, 
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[UserPreference]:
        """Get all preferences for a user, optionally filtered by category"""
        try:
            # Use the database function
            result = self.db.rpc("get_user_preferences_by_category", {
                "p_user_id": user_id,
                "p_category": category,
                "p_active_only": active_only
            }).execute()
            
            preferences = []
            if result.data:
                for row in result.data:
                    pref = UserPreference(
                        id=row["id"],
                        user_id=row["user_id"],
                        category=row["category"],
                        preference_key=row["preference_key"],
                        value=row["value"],
                        description=row.get("description"),
                        is_active=row["is_active"],
                        priority=row["priority"],
                        created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
                    )
                    preferences.append(pref)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get preferences by category {category}: {e}")
            return []
    
    async def set_preference(
        self, 
        user_id: str, 
        preference: PreferenceCreate
    ) -> Optional[str]:
        """Set/update a preference"""
        try:
            upsert_data = {
                "user_id": user_id,
                "category": preference.category,
                "preference_key": preference.preference_key,
                "value": preference.value,
                "description": preference.description,
                "is_active": preference.is_active,
                "priority": preference.priority,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.from_("user_preferences").upsert(
                upsert_data,
                on_conflict="user_id,category,preference_key"
            ).select("id").execute()
            
            if result.data and len(result.data) > 0:
                pref_id = result.data[0]["id"]
                logger.info(f"Set preference {preference.category}.{preference.preference_key} for user {user_id}")
                return pref_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to set preference {preference.category}.{preference.preference_key}: {e}")
            return None
    
    async def update_preference(
        self, 
        user_id: str, 
        category: str, 
        preference_key: str,
        updates: PreferenceUpdate
    ) -> bool:
        """Update an existing preference"""
        try:
            update_data = {
                "value": updates.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if updates.description is not None:
                update_data["description"] = updates.description
            if updates.is_active is not None:
                update_data["is_active"] = updates.is_active
            if updates.priority is not None:
                update_data["priority"] = updates.priority
            
            result = self.db.from_("user_preferences").update(update_data).eq(
                "user_id", user_id
            ).eq("category", category).eq("preference_key", preference_key).execute()
            
            success = result.data and len(result.data) > 0
            if success:
                logger.info(f"Updated preference {category}.{preference_key} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update preference {category}.{preference_key}: {e}")
            return False
    
    async def delete_preference(
        self, 
        user_id: str, 
        category: str, 
        preference_key: str
    ) -> bool:
        """Delete a preference"""
        try:
            result = self.db.from_("user_preferences").delete().eq(
                "user_id", user_id
            ).eq("category", category).eq("preference_key", preference_key).execute()
            
            success = result.data and len(result.data) > 0
            if success:
                logger.info(f"Deleted preference {category}.{preference_key} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete preference {category}.{preference_key}: {e}")
            return False
    
    async def get_scheduling_constraints(self, user_id: str) -> Dict[str, Any]:
        """Get all scheduling-related constraints for the user"""
        try:
            scheduling_prefs = await self.get_preferences_by_category(user_id, "scheduling")
            
            constraints = {}
            for pref in scheduling_prefs:
                constraints[pref.preference_key] = pref.value
            
            return constraints
            
        except Exception as e:
            logger.error(f"Failed to get scheduling constraints: {e}")
            return {}
    
    async def check_time_constraint(
        self, 
        user_id: str, 
        proposed_time: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if a proposed time slot violates any user constraints.
        
        Args:
            user_id: User identifier
            proposed_time: Dict with 'day', 'start_time', 'end_time', 'duration_minutes'
        
        Returns:
            Dict with 'allowed': bool, 'violations': List[str], 'warnings': List[str]
        """
        try:
            constraints = await self.get_scheduling_constraints(user_id)
            
            violations = []
            warnings = []
            
            # Check no-work windows
            no_work_windows = constraints.get("no_work_windows", [])
            for window in no_work_windows:
                if self._time_overlaps_window(proposed_time, window):
                    violations.append(f"Conflicts with no-work window: {window.get('description', 'Blocked time')}")
            
            # Check deep work preferences
            deep_work_windows = constraints.get("deep_work_windows", [])
            if deep_work_windows and not any(self._time_overlaps_window(proposed_time, window) for window in deep_work_windows):
                warnings.append("Outside of preferred deep work hours")
            
            # Check maximum continuous study time
            max_continuous = constraints.get("break_preferences", {}).get("max_continuous_study_minutes", 180)
            if proposed_time.get("duration_minutes", 0) > max_continuous:
                violations.append(f"Exceeds maximum continuous study time ({max_continuous} minutes)")
            
            return {
                "allowed": len(violations) == 0,
                "violations": violations,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Failed to check time constraint: {e}")
            return {"allowed": True, "violations": [], "warnings": []}
    
    def _time_overlaps_window(self, proposed_time: Dict[str, Any], window: Dict[str, Any]) -> bool:
        """Check if proposed time overlaps with a constraint window"""
        try:
            # Simple overlap check - in production, use proper datetime parsing
            proposed_day = proposed_time.get("day")
            window_day = window.get("day")
            
            # Check day match
            if window_day == "daily" or window_day == proposed_day:
                proposed_start = proposed_time.get("start_time")
                proposed_end = proposed_time.get("end_time")
                window_start = window.get("start_time")
                window_end = window.get("end_time")
                
                # Basic time overlap check (assumes HH:MM format)
                if proposed_start and proposed_end and window_start and window_end:
                    return not (proposed_end <= window_start or proposed_start >= window_end)
            
            # Check if proposed day is in window days list
            if isinstance(window_day, list) and proposed_day in window_day:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking time overlap: {e}")
            return False
    
    async def get_preference_defaults(self, category: str) -> Dict[str, Any]:
        """Get default preference values for a category"""
        defaults = {
            "scheduling": {
                "no_work_windows": [],
                "preferred_study_blocks": {
                    "default": {"duration_minutes": 50, "break_minutes": 10}
                },
                "deep_work_windows": [],
                "break_preferences": {
                    "min_break_between_subjects": 15,
                    "max_continuous_study_minutes": 180
                }
            },
            "study": {
                "difficulty_ordering": "hardest_first",
                "context_switching_penalty": 2.0,
                "procrastination_buffer_days": 2,
                "preferred_study_environment": "quiet"
            },
            "notifications": {
                "reminder_timing": {
                    "assignments": [{"days_before": 3}, {"hours_before": 2}],
                    "exams": [{"weeks_before": 2}, {"days_before": 1}]
                },
                "channels": {
                    "email": {"enabled": True},
                    "push": {"enabled": True}
                }
            },
            "general": {
                "timezone": "UTC",
                "date_format": "MM/DD/YYYY",
                "time_format": "12h",
                "week_start": "Monday"
            }
        }
        
        return defaults.get(category, {})

# Global preferences service instance
preferences_service = PreferencesService()

def get_preferences_service() -> PreferencesService:
    """Get the global preferences service instance"""
    return preferences_service
