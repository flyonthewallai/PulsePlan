"""
Calendar Repository
Handles all database operations for calendar-related tables
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class CalendarLinkRepository(BaseRepository):
    """Repository for calendar_links table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "calendar_links"

    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all calendar links for a user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching calendar links for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user_id",
                details={"user_id": user_id}
            )

    async def get_by_task_id(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get calendar link by task ID"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("task_id", task_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching calendar link for task {task_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_task_id",
                details={"task_id": task_id, "user_id": user_id}
            )

    async def delete_by_id(self, link_id: str) -> bool:
        """Delete a calendar link by ID"""
        return await self.delete(link_id)


class CalendarCalendarRepository(BaseRepository):
    """Repository for calendar_calendars table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "calendar_calendars"

    async def get_primary_write_calendar(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the primary write calendar for a user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id, provider_calendar_id")\
                .eq("user_id", user_id)\
                .eq("is_primary_write", True)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching primary write calendar for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_primary_write_calendar",
                details={"user_id": user_id}
            )

    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all calendars for a user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching calendars for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_user_id",
                details={"user_id": user_id}
            )
    
    async def get_active_by_provider(
        self,
        user_id: str,
        provider: str
    ) -> List[Dict[str, Any]]:
        """Get active calendars for a user by provider"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .eq("is_active", True)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(
                f"Error fetching active {provider} calendars for user {user_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_active_by_provider",
                details={"user_id": user_id, "provider": provider}
            )
    
    async def get_by_watch_channel(
        self,
        channel_id: str,
        resource_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get calendar by Google watch channel details"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("watch_channel_id", channel_id)\
                .eq("watch_resource_id", resource_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(
                f"Error fetching calendar for channel {channel_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_watch_channel",
                details={"channel_id": channel_id, "resource_id": resource_id}
            )

    async def unset_primary_write(self, user_id: str) -> None:
        """Unset all primary write calendars for a user"""
        try:
            self.supabase.table(self.table_name)\
                .update({"is_primary_write": False})\
                .eq("user_id", user_id)\
                .eq("is_primary_write", True)\
                .execute()
        
        except Exception as e:
            logger.error(f"Error unsetting primary write for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="unset_primary_write",
                details={"user_id": user_id}
            )

    async def set_primary_write(self, calendar_id: str) -> None:
        """Set a calendar as primary write"""
        try:
            self.supabase.table(self.table_name)\
                .update({"is_primary_write": True})\
                .eq("id", calendar_id)\
                .execute()
        
        except Exception as e:
            logger.error(f"Error setting primary write for calendar {calendar_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="set_primary_write",
                details={"calendar_id": calendar_id}
            )

    async def deactivate_all(self, user_id: str) -> None:
        """Deactivate all calendars for a user"""
        try:
            self.supabase.table(self.table_name)\
                .update({"is_active": False})\
                .eq("user_id", user_id)\
                .execute()
        
        except Exception as e:
            logger.error(f"Error deactivating calendars for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="deactivate_all",
                details={"user_id": user_id}
            )

    async def activate_calendar(self, calendar_id: str, user_id: str) -> None:
        """Activate a specific calendar"""
        try:
            self.supabase.table(self.table_name)\
                .update({"is_active": True})\
                .eq("id", calendar_id)\
                .eq("user_id", user_id)\
                .execute()
        
        except Exception as e:
            logger.error(f"Error activating calendar {calendar_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="activate_calendar",
                details={"calendar_id": calendar_id, "user_id": user_id}
            )

    async def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active calendars"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id, user_id, summary")\
                .eq("is_active", True)\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching all active calendars: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_all_active"
            )

    async def get_with_watch_channels(self) -> List[Dict[str, Any]]:
        """Get all calendars with watch channels"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id, summary, watch_expiration_at")\
                .not_.is_("watch_channel_id", "null")\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching calendars with watch channels: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_with_watch_channels"
            )


class CalendarEventRepository(BaseRepository):
    """Repository for calendar_events table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "calendar_events"

    async def get_by_external_id(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Get calendar event by external ID"""
        try:
            response = self.supabase.table(self.table_name)\
                .select(
                    "description, location, html_link, attendees, creator_email, organizer_email, "
                    "status, transparency, visibility, categories, importance, sensitivity, "
                    "recurrence, has_attachments"
                )\
                .eq("external_id", external_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching calendar event {external_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_external_id",
                details={"external_id": external_id}
            )

    async def delete_by_filters(self, filters: Dict[str, Any]) -> bool:
        """Delete calendar events matching filters"""
        try:
            query = self.supabase.table(self.table_name).delete()
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return bool(response.data is not None)
        
        except Exception as e:
            logger.error(f"Error deleting calendar events with filters {filters}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_filters",
                details={"filters": filters}
            )

    async def bulk_insert(self, events: List[Dict[str, Any]]) -> bool:
        """Insert multiple calendar events"""
        try:
            response = self.supabase.table(self.table_name).insert(events).execute()
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error inserting calendar events: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="bulk_insert",
                details={"event_count": len(events)}
            )

    async def update_by_filters(self, update_data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Update calendar events matching filters"""
        try:
            query = self.supabase.table(self.table_name).update(update_data)
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error updating calendar events: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_by_filters",
                details={"filters": filters}
            )

    async def delete_by_id(self, event_id: str) -> bool:
        """Delete calendar event by ID"""
        try:
            response = self.supabase.table(self.table_name).delete().eq("id", event_id).execute()
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error deleting calendar event {event_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_by_id",
                details={"event_id": event_id}
            )


class CalendarSyncConflictRepository(BaseRepository):
    """Repository for calendar_sync_conflicts table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "calendar_sync_conflicts"

    async def get_unresolved_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all unresolved conflicts for a user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select(
                    "id, user_id, event1_id, event2_id, conflict_type, confidence_score, "
                    "resolution_status, detected_at, resolved_at"
                )\
                .eq("user_id", user_id)\
                .eq("resolution_status", "unresolved")\
                .execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching unresolved conflicts for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_unresolved_by_user",
                details={"user_id": user_id}
            )

    async def get_by_id_and_user(self, conflict_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get conflict by ID and user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", conflict_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        
        except Exception as e:
            logger.error(f"Error fetching conflict {conflict_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_and_user",
                details={"conflict_id": conflict_id, "user_id": user_id}
            )

    async def get_users_with_unresolved_conflicts(self) -> List[str]:
        """
        Get list of user IDs with unresolved conflicts
        
        Returns:
            List of unique user IDs
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("user_id")\
                .eq("resolution_status", "unresolved")\
                .execute()
            
            if not response.data:
                return []
            
            # Return unique user IDs
            return list(set(row["user_id"] for row in response.data))
        
        except Exception as e:
            logger.error(f"Error fetching users with unresolved conflicts: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_users_with_unresolved_conflicts"
            )

    async def delete_old_resolved_conflicts(self, cutoff_datetime: datetime) -> int:
        """
        Delete old resolved conflicts
        
        Args:
            cutoff_datetime: Cutoff datetime
            
        Returns:
            Number of conflicts deleted
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .match({"resolution_status": "resolved"})\
                .lt("resolved_at", cutoff_datetime.isoformat())\
                .execute()
            
            return len(response.data) if response.data else 0
        
        except Exception as e:
            logger.error(f"Error deleting old resolved conflicts: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete_old_resolved_conflicts",
                details={"cutoff_datetime": cutoff_datetime.isoformat()}
            )

    async def create(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sync conflict"""
        try:
            response = self.supabase.table(self.table_name).insert(conflict_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            raise RepositoryError(
                message="Failed to create sync conflict",
                table=self.table_name,
                operation="create"
            )
        
        except RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Error creating sync conflict: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create",
                details={"conflict_data": conflict_data}
            )

    async def update_by_id(self, conflict_id: str, update_data: Dict[str, Any]) -> bool:
        """Update conflict by ID"""
        try:
            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("id", conflict_id)\
                .execute()
            
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error updating conflict {conflict_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update_by_id",
                details={"conflict_id": conflict_id}
            )


class WebhookSubscriptionRepository(BaseRepository):
    """Repository for webhook_subscriptions table operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "webhook_subscriptions"

    async def get_user_by_subscription_id(
        self,
        subscription_id: str,
        provider: str
    ) -> Optional[str]:
        """Get user_id for a webhook subscription"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("user_id")\
                .eq("subscription_id", subscription_id)\
                .eq("provider", provider)\
                .single()\
                .execute()
            
            return response.data["user_id"] if response.data else None
        
        except Exception as e:
            logger.error(
                f"Error fetching user for subscription {subscription_id}: {e}",
                exc_info=True
            )
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_user_by_subscription_id",
                details={"subscription_id": subscription_id, "provider": provider}
            )


def get_calendar_link_repository() -> CalendarLinkRepository:
    """Dependency injection function"""
    return CalendarLinkRepository()


def get_calendar_calendar_repository() -> CalendarCalendarRepository:
    """Dependency injection function"""
    return CalendarCalendarRepository()


def get_calendar_event_repository() -> CalendarEventRepository:
    """Dependency injection function"""
    return CalendarEventRepository()


def get_calendar_sync_conflict_repository() -> CalendarSyncConflictRepository:
    """Dependency injection function"""
    return CalendarSyncConflictRepository()


def get_webhook_subscription_repository() -> WebhookSubscriptionRepository:
    """Dependency injection function"""
    return WebhookSubscriptionRepository()

