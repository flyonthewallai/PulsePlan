"""Base interface for calendar providers."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class CalendarProvider(ABC):
    """Abstract base class for calendar provider integrations."""

    @abstractmethod
    async def list_calendars(self, oauth_token_id: UUID) -> List[Dict[str, Any]]:
        """
        List all calendars available for the authenticated account.

        Returns:
            List of calendar dicts with keys:
            - provider_calendar_id: str
            - summary: str
            - timezone: str
            - is_primary: bool (optional)
        """
        pass

    @abstractmethod
    async def watch_calendar(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        callback_url: str,
        channel_token: str,
        ttl_days: int = 7
    ) -> Dict[str, Any]:
        """
        Set up a watch/webhook for calendar changes.

        Returns:
            Dict with keys:
            - channel_id: str
            - resource_id: str
            - expiration: datetime
        """
        pass

    @abstractmethod
    async def stop_watch(
        self,
        calendar_id: UUID,
        channel_id: str,
        resource_id: str
    ) -> None:
        """Stop an active watch channel."""
        pass

    @abstractmethod
    async def list_events(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        sync_token: Optional[str] = None,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        page_token: Optional[str] = None,
        max_results: int = 250
    ) -> Dict[str, Any]:
        """
        List events from a calendar.

        Uses sync_token for incremental sync if provided,
        otherwise uses time_min/time_max window.

        Returns:
            Dict with keys:
            - events: List[Dict]
            - next_page_token: Optional[str]
            - next_sync_token: Optional[str]
        """
        pass

    @abstractmethod
    async def get_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_id: str
    ) -> Dict[str, Any]:
        """Get a single event by ID."""
        pass

    @abstractmethod
    async def insert_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new event.

        Args:
            event_dict: Event data in provider-specific format

        Returns:
            Created event dict
        """
        pass

    @abstractmethod
    async def update_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_id: str,
        event_dict: Dict[str, Any],
        etag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing event.

        Args:
            etag: For optimistic concurrency control

        Returns:
            Updated event dict

        Raises:
            PreconditionFailed: If etag doesn't match (HTTP 412)
        """
        pass

    @abstractmethod
    async def delete_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_id: str
    ) -> None:
        """Delete an event."""
        pass


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class PreconditionFailed(ProviderError):
    """Raised when an update fails due to etag mismatch."""
    pass


class SyncTokenInvalid(ProviderError):
    """Raised when a sync token is no longer valid (HTTP 410)."""
    pass


class ProviderAuthError(ProviderError):
    """Raised when authentication fails."""
    pass
