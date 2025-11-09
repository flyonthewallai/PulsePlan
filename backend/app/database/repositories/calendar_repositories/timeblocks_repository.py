"""
Timeblocks Repository
Query v_timeblocks view for unified calendar feed and manage timeblocks table
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import uuid

from app.config.database.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class TimeblocksRepository:
    """Repository for querying unified timeblocks view and managing timeblocks table"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def fetch_timeblocks(
        self,
        user_id: str,
        dt_from: datetime,
        dt_to: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch timeblocks for a user within a time window

        Args:
            user_id: User UUID
            dt_from: Start of time window (timezone-aware)
            dt_to: End of time window (timezone-aware)

        Returns:
            List of timeblock dictionaries from v_timeblocks view

        Filters:
            - Only active calendars (for calendar events)
            - Non-cancelled events
            - Only scheduled tasks (with start_date and end_date)
            - Time window overlap (start < to AND end > from)
        """
        try:
            # Convert to UTC ISO format
            from_str = dt_from.astimezone(timezone.utc).isoformat()
            to_str = dt_to.astimezone(timezone.utc).isoformat()

            logger.info(f"[Timeblocks] Fetching timeblocks for user {user_id} from {from_str} to {to_str}")

            # Try RPC function first
            try:
                response = self.supabase.rpc(
                    'get_timeblocks_for_user',
                    {
                        'p_user_id': user_id,
                        'p_from': from_str,
                        'p_to': to_str
                    }
                ).execute()

                if response.data is not None:
                    logger.info(f"[Timeblocks] RPC returned {len(response.data)} items")
                    return response.data
                else:
                    logger.warning("RPC returned None, falling back to direct query")
                    
            except Exception as rpc_error:
                logger.warning(f"RPC call failed: {rpc_error}, falling back to direct query")

            # Fallback to direct view query
            return await self._fetch_timeblocks_direct(user_id, from_str, to_str)

        except Exception as e:
            logger.error(f"Error fetching timeblocks: {str(e)}")
            # Return empty list instead of raising to prevent frontend errors
            return []

    async def _fetch_timeblocks_direct(
        self,
        user_id: str,
        from_str: str,
        to_str: str
    ) -> List[Dict[str, Any]]:
        """
        Direct query fallback when RPC is not available

        Note: This may include events from inactive calendars.
        For production, implement the RPC function for proper filtering.
        """
        try:
            logger.info(f"[Timeblocks] Using direct query fallback for user {user_id}")
            
            # Query v_timeblocks view directly
            # Note: Supabase client is synchronous, no await needed
            response = self.supabase.from_('v_timeblocks') \
                .select('*') \
                .eq('user_id', user_id) \
                .lt('start_at', to_str) \
                .gt('end_at', from_str) \
                .order('start_at', desc=False) \
                .execute()

            logger.info(f"[Timeblocks] Direct query returned {len(response.data or [])} items")
            return response.data or []

        except Exception as e:
            logger.error(f"Error in direct timeblocks query: {str(e)}")
            return []

    async def get_timeblocks_for_user(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Compatibility wrapper used by scheduling services to load busy blocks."""
        try:
            return await self.fetch_timeblocks(user_id=user_id, dt_from=start_date, dt_to=end_date)
        except Exception as e:
            logger.error(f"Error fetching timeblocks for user {user_id}: {e}")
            return []

    async def get_calendar_link(
        self,
        task_id: str = None,
        provider_event_id: str = None,
        provider_calendar_id: str = None
    ) -> Dict[str, Any] | None:
        """
        Fetch calendar link for a task or provider event

        Args:
            task_id: Task UUID (optional)
            provider_event_id: External event ID (optional)
            provider_calendar_id: External calendar ID (optional)

        Returns:
            Calendar link record or None
        """
        try:
            query = self.supabase.from_('calendar_links').select('*')

            if task_id:
                query = query.eq('task_id', task_id)
            elif provider_event_id and provider_calendar_id:
                query = query.eq('provider_event_id', provider_event_id) \
                             .eq('provider_calendar_id', provider_calendar_id)
            else:
                return None

            response = query.limit(1).execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error fetching calendar link: {str(e)}")
            return None

    # ===== CRUD Operations for timeblocks table =====

    async def create_timeblock(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        task_id: Optional[str] = None,
        type: str = "task_block",
        status: str = "scheduled",
        source: str = "pulse",
        agent_reasoning: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        all_day: bool = False,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new timeblock

        Args:
            user_id: User UUID
            title: Timeblock title
            start_time: Start time (timezone-aware)
            end_time: End time (timezone-aware)
            task_id: Optional parent task UUID
            type: Timeblock type (task_block, habit, focus, etc.)
            status: Status (scheduled, completed, etc.)
            source: Source (pulse, external, manual, agent, scheduler)
            agent_reasoning: Optional AI reasoning data
            location: Optional location
            all_day: Whether it's an all-day timeblock
            notes: Optional notes
            metadata: Optional flexible metadata

        Returns:
            Created timeblock record

        Raises:
            Exception: If creation fails
        """
        try:
            # Validate time range
            if end_time <= start_time:
                raise ValueError("end_time must be after start_time")

            # Convert to UTC ISO format
            start_str = start_time.astimezone(timezone.utc).isoformat()
            end_str = end_time.astimezone(timezone.utc).isoformat()

            data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "task_id": task_id,
                "title": title,
                "start_time": start_str,
                "end_time": end_str,
                "type": type,
                "status": status,
                "source": source,
                "agent_reasoning": agent_reasoning,
                "location": location,
                "all_day": all_day,
                "notes": notes,
                "metadata": metadata or {}
            }

            response = self.supabase.table("timeblocks").insert(data).execute()

            if not response.data:
                raise Exception("Failed to create timeblock")

            logger.info(f"[Timeblocks] Created timeblock {response.data[0]['id']} for user {user_id}")
            return response.data[0]

        except Exception as e:
            logger.error(f"Error creating timeblock: {str(e)}")
            raise

    async def get_timeblock(
        self,
        timeblock_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single timeblock by ID

        Args:
            timeblock_id: Timeblock UUID
            user_id: User UUID (for RLS)

        Returns:
            Timeblock record or None
        """
        try:
            response = self.supabase.table("timeblocks") \
                .select("*") \
                .eq("id", timeblock_id) \
                .eq("user_id", user_id) \
                .single() \
                .execute()

            return response.data if response.data else None

        except Exception as e:
            logger.error(f"Error fetching timeblock {timeblock_id}: {str(e)}")
            return None

    async def get_timeblocks_for_task(
        self,
        task_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all timeblocks associated with a task

        Args:
            task_id: Task UUID
            user_id: User UUID (for RLS)

        Returns:
            List of timeblock records
        """
        try:
            response = self.supabase.table("timeblocks") \
                .select("*") \
                .eq("task_id", task_id) \
                .eq("user_id", user_id) \
                .order("start_time", desc=False) \
                .execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching timeblocks for task {task_id}: {str(e)}")
            return []

    async def update_timeblock(
        self,
        timeblock_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a timeblock

        Args:
            timeblock_id: Timeblock UUID
            user_id: User UUID (for RLS)
            updates: Dictionary of fields to update

        Returns:
            Updated timeblock record or None

        Raises:
            ValueError: If time range validation fails
        """
        try:
            # Validate time range if both fields provided
            if "start_time" in updates and "end_time" in updates:
                start = updates["start_time"]
                end = updates["end_time"]
                if isinstance(start, datetime) and isinstance(end, datetime):
                    if end <= start:
                        raise ValueError("end_time must be after start_time")
                    updates["start_time"] = start.astimezone(timezone.utc).isoformat()
                    updates["end_time"] = end.astimezone(timezone.utc).isoformat()

            # Add updated_at timestamp
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()

            response = self.supabase.table("timeblocks") \
                .update(updates) \
                .eq("id", timeblock_id) \
                .eq("user_id", user_id) \
                .execute()

            if not response.data:
                logger.warning(f"No timeblock found to update: {timeblock_id}")
                return None

            logger.info(f"[Timeblocks] Updated timeblock {timeblock_id} for user {user_id}")
            return response.data[0]

        except Exception as e:
            logger.error(f"Error updating timeblock {timeblock_id}: {str(e)}")
            raise

    async def delete_timeblock(
        self,
        timeblock_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a timeblock

        Args:
            timeblock_id: Timeblock UUID
            user_id: User UUID (for RLS)

        Returns:
            True if deleted, False if not found
        """
        try:
            response = self.supabase.table("timeblocks") \
                .delete() \
                .eq("id", timeblock_id) \
                .eq("user_id", user_id) \
                .execute()

            success = bool(response.data)
            if success:
                logger.info(f"[Timeblocks] Deleted timeblock {timeblock_id} for user {user_id}")
            else:
                logger.warning(f"No timeblock found to delete: {timeblock_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting timeblock {timeblock_id}: {str(e)}")
            return False

    async def mark_timeblock_completed(
        self,
        timeblock_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a timeblock as completed

        Args:
            timeblock_id: Timeblock UUID
            user_id: User UUID (for RLS)

        Returns:
            Updated timeblock record or None
        """
        return await self.update_timeblock(
            timeblock_id,
            user_id,
            {"status": "completed"}
        )

    async def get_timeblocks_by_status(
        self,
        user_id: str,
        status: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get timeblocks by status

        Args:
            user_id: User UUID
            status: Status to filter by (scheduled, completed, etc.)
            limit: Maximum number of records to return

        Returns:
            List of timeblock records
        """
        try:
            response = self.supabase.table("timeblocks") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("status", status) \
                .order("start_time", desc=False) \
                .limit(limit) \
                .execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching timeblocks by status {status}: {str(e)}")
            return []

    async def list_timeblocks(
        self,
        user_id: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        List timeblocks with flexible filters

        Args:
            user_id: User UUID
            filters: Dictionary of filters:
                - start_after: Filter by start_time >= value
                - end_before: Filter by end_time <= value
                - type: Filter by timeblock type
                - status: Filter by status
                - limit: Maximum number of records (default: 100)

        Returns:
            List of timeblock records
        """
        try:
            query = self.supabase.table("timeblocks") \
                .select("*") \
                .eq("user_id", user_id)

            # Apply filters
            if filters.get("start_after"):
                start_after = filters["start_after"]
                if isinstance(start_after, datetime):
                    start_after = start_after.astimezone(timezone.utc).isoformat()
                query = query.gte("start_time", start_after)

            if filters.get("end_before"):
                end_before = filters["end_before"]
                if isinstance(end_before, datetime):
                    end_before = end_before.astimezone(timezone.utc).isoformat()
                query = query.lte("end_time", end_before)

            if filters.get("type"):
                query = query.eq("type", filters["type"])

            if filters.get("status"):
                query = query.eq("status", filters["status"])

            # Default limit
            limit = filters.get("limit", 100)
            query = query.order("start_time", desc=False).limit(limit)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error listing timeblocks with filters: {str(e)}")
            return []


# Singleton instance
_timeblocks_repo = None


def get_timeblocks_repository() -> TimeblocksRepository:
    """Get timeblocks repository singleton"""
    global _timeblocks_repo
    if _timeblocks_repo is None:
        _timeblocks_repo = TimeblocksRepository()
    return _timeblocks_repo
