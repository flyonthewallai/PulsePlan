"""
Preferences repository for scheduler data access.

Handles loading and updating user scheduling preferences from various storage backends.
"""

import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict

from .base_repository import BasePreferencesRepository
from ...core.domain import Preferences
from ....core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class PreferencesRepository(BasePreferencesRepository):
    """Repository for user preferences data access operations."""

    def __init__(self, storage_backend):
        """
        Initialize preferences repository.

        Args:
            storage_backend: Storage backend instance
        """
        self.storage = storage_backend
        self.timezone_manager = get_timezone_manager()

    async def load_preferences(self, user_id: str) -> Preferences:
        """
        Load user preferences for scheduling.

        Args:
            user_id: User identifier

        Returns:
            User preferences with defaults if not found
        """
        try:
            if self.storage.backend_type == "memory":
                return await self._load_preferences_from_memory(user_id)
            elif self.storage.backend_type == "database":
                return await self._load_preferences_from_db(user_id)
            else:
                return Preferences(timezone="UTC")

        except Exception as e:
            logger.error(f"Failed to load preferences for user {user_id}: {e}")
            return Preferences(timezone="UTC")

    async def update_preferences(self, user_id: str, updates: Dict[str, Any]):
        """
        Update user preferences.

        Args:
            user_id: User identifier
            updates: Dictionary of preference updates
        """
        try:
            if self.storage.backend_type == "memory":
                await self._update_preferences_in_memory(user_id, updates)
            elif self.storage.backend_type == "database":
                await self._update_preferences_in_db(user_id, updates)

            logger.debug(f"Updated preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")

    async def get_window(self, user_id: str, horizon_days: int) -> Tuple[datetime, datetime]:
        """
        Get the time window for scheduling.

        Args:
            user_id: User identifier
            horizon_days: Days ahead to schedule

        Returns:
            (start_datetime, end_datetime) for scheduling
        """
        try:
            prefs = await self.load_preferences(user_id)

            # Start from beginning of current day in user timezone
            now = datetime.now()

            # For simplicity, use current timezone
            # In production, would use prefs.timezone
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=horizon_days)

            return start_dt, end_dt

        except Exception as e:
            logger.error(f"Failed to get window for user {user_id}: {e}")
            now = datetime.now()
            return now, now + timedelta(days=horizon_days)

    async def _load_preferences_from_memory(self, user_id: str) -> Preferences:
        """Load preferences from memory storage."""
        prefs = self.storage.get_preferences(user_id)
        if prefs:
            return prefs

        # Return defaults
        return Preferences(
            timezone="UTC",
            workday_start="09:00",
            workday_end="17:00",
            max_daily_effort_minutes=480,
            session_granularity_minutes=30
        )

    async def _load_preferences_from_db(self, user_id: str) -> Preferences:
        """Load preferences from database."""
        try:
            from app.config.database.supabase import get_supabase

            supabase = get_supabase()

            # Query user preferences from database
            response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()

            prefs = {}
            for pref in response.data:
                key = pref["preference_key"]
                value = pref["value"]
                prefs[key] = value

            # Get user timezone from users table
            user_response = supabase.table("users").select("timezone").eq("id", user_id).single().execute()
            timezone = user_response.data.get("timezone", "UTC") if user_response.data else "UTC"

            # Create Preferences object with database data
            preferences = Preferences(
                timezone=timezone,
                working_hours_start=prefs.get("working_hours_start", 9),
                working_hours_end=prefs.get("working_hours_end", 17),
                break_duration_minutes=prefs.get("break_duration_minutes", 15),
                max_daily_work_hours=prefs.get("max_daily_work_hours", 8),
                preferred_work_days=prefs.get("preferred_work_days", [1, 2, 3, 4, 5]),  # Mon-Fri
                focus_time_blocks=prefs.get("focus_time_blocks", True)
            )

            logger.info(f"Loaded preferences from database for user {user_id}")
            return preferences

        except Exception as e:
            logger.error(f"Failed to load preferences from database: {e}")
            return Preferences(timezone="UTC")

    async def _update_preferences_in_memory(self, user_id: str, updates: Dict[str, Any]):
        """Update preferences in memory storage."""
        current_prefs = self.storage.get_preferences(user_id)
        if current_prefs:
            prefs_dict = asdict(current_prefs)
            prefs_dict.update(updates)
            updated_prefs = Preferences(**prefs_dict)
        else:
            # Create new preferences
            default_prefs = asdict(Preferences(timezone="UTC"))
            default_prefs.update(updates)
            updated_prefs = Preferences(**default_prefs)

        self.storage.set_preferences(user_id, updated_prefs)

    async def _update_preferences_in_db(self, user_id: str, updates: Dict[str, Any]):
        """Update preferences in database."""
        # TODO: Implement database update
        logger.warning("Database backend not implemented")
