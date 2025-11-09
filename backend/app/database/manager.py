"""
Database Manager
Provides helper methods for database operations using Supabase
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)


class CalendarEventsRepository:
    """Repository for calendar_events table operations"""

    def __init__(self, supabase):
        self.supabase = supabase

    def get_events_in_range(
        self, user_id: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events within a date range for a user

        Args:
            user_id: User identifier
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of calendar event dictionaries
        """
        try:
            # Convert dates to ISO format for query
            start_iso = start_date.isoformat() if isinstance(start_date, date) else start_date
            end_iso = end_date.isoformat() if isinstance(end_date, date) else end_date

            # Query calendar events
            response = (
                self.supabase.table("calendar_events")
                .select("*")
                .eq("user_id", user_id)
                .gte("start_time", start_iso)
                .lte("start_time", end_iso)
                .execute()
            )

            events = response.data if response.data else []
            logger.info(
                f"[CalendarEventsRepo] Fetched {len(events)} events for user {user_id} "
                f"from {start_iso} to {end_iso}"
            )
            return events

        except Exception as e:
            logger.error(f"[CalendarEventsRepo] Error fetching events: {e}", exc_info=True)
            return []


class TimeblocksRepository:
    """Repository for timeblocks table operations"""

    def __init__(self, supabase):
        self.supabase = supabase

    def get_blocks_in_range(
        self, user_id: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get timeblocks within a date range for a user

        Args:
            user_id: User identifier
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of timeblock dictionaries
        """
        try:
            # Convert dates to ISO format for query
            start_iso = start_date.isoformat() if isinstance(start_date, date) else start_date
            end_iso = end_date.isoformat() if isinstance(end_date, date) else end_date

            # Query timeblocks
            response = (
                self.supabase.table("timeblocks")
                .select("*")
                .eq("user_id", user_id)
                .gte("start_time", start_iso)
                .lte("start_time", end_iso)
                .execute()
            )

            blocks = response.data if response.data else []
            logger.info(
                f"[TimeblocksRepo] Fetched {len(blocks)} blocks for user {user_id} "
                f"from {start_iso} to {end_iso}"
            )
            return blocks

        except Exception as e:
            logger.error(f"[TimeblocksRepo] Error fetching blocks: {e}", exc_info=True)
            return []

    def bulk_create(self, timeblocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk insert timeblocks into database

        Args:
            timeblocks: List of timeblock dictionaries to insert

        Returns:
            List of created timeblock records
        """
        if not timeblocks:
            logger.warning("[TimeblocksRepo] No timeblocks to create")
            return []

        try:
            # Insert timeblocks in bulk
            response = self.supabase.table("timeblocks").insert(timeblocks).execute()

            created = response.data if response.data else []
            logger.info(f"[TimeblocksRepo] Bulk created {len(created)} timeblocks")
            return created

        except Exception as e:
            logger.error(f"[TimeblocksRepo] Error bulk creating timeblocks: {e}", exc_info=True)
            # Try individual inserts as fallback
            created = []
            for block in timeblocks:
                try:
                    response = self.supabase.table("timeblocks").insert(block).execute()
                    if response.data:
                        created.extend(response.data)
                except Exception as individual_error:
                    logger.warning(f"[TimeblocksRepo] Failed to insert individual block: {individual_error}")
                    continue

            logger.info(f"[TimeblocksRepo] Fallback: created {len(created)}/{len(timeblocks)} timeblocks")
            return created


class TaskRepository:
    """Repository for tasks table operations"""

    def __init__(self, supabase):
        self.supabase = supabase

    def get_unscheduled_tasks(
        self, user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get unscheduled tasks for a user, optionally within a date range

        Args:
            user_id: User identifier
            start_date: Optional start date filter (for due_date)
            end_date: Optional end date filter (for due_date)

        Returns:
            List of task dictionaries
        """
        try:
            # Build query
            query = (
                self.supabase.table("tasks")
                .select("*")
                .eq("user_id", user_id)
                .eq("completed", False)
            )

            # Add date range filters if provided
            if start_date:
                start_iso = start_date.isoformat() if isinstance(start_date, date) else start_date
                query = query.gte("due_date", start_iso)

            if end_date:
                end_iso = end_date.isoformat() if isinstance(end_date, date) else end_date
                query = query.lte("due_date", end_iso)

            response = query.execute()

            tasks = response.data if response.data else []
            logger.info(f"[TaskRepo] Fetched {len(tasks)} unscheduled tasks for user {user_id}")
            return tasks

        except Exception as e:
            logger.error(f"[TaskRepo] Error fetching unscheduled tasks: {e}", exc_info=True)
            return []


class DatabaseManager:
    """
    Central database manager with repository pattern

    Provides unified access to all database operations
    """

    def __init__(self):
        self.supabase = get_supabase()
        self.calendar_events = CalendarEventsRepository(self.supabase)
        self.timeblocks = TimeblocksRepository(self.supabase)
        self.tasks = TaskRepository(self.supabase)

    def __getattr__(self, name):
        """
        Fallback for direct table access if repository doesn't exist

        Example: db.users.select() -> supabase.table("users").select()
        """
        # Check if it's a known repository
        if hasattr(self, name):
            return getattr(self, name)

        # Otherwise, return direct table access
        class TableProxy:
            def __init__(self, supabase, table_name):
                self.supabase = supabase
                self.table_name = table_name

            def __getattr__(self, method_name):
                """Proxy all method calls to supabase.table()"""
                table = self.supabase.table(self.table_name)
                return getattr(table, method_name)

        return TableProxy(self.supabase, name)


# Singleton instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """
    Get singleton DatabaseManager instance

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
