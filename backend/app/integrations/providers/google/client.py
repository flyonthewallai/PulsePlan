"""Google Calendar API client with auto-refresh using Supabase."""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import httpx
import logging

from app.integrations.providers.base import (
    CalendarProvider,
    ProviderError,
    PreconditionFailed,
    SyncTokenInvalid,
    ProviderAuthError
)
from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)


class GoogleCalendarClient(CalendarProvider):
    """Google Calendar API client with automatic token refresh."""

    BASE_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(self):
        self.supabase = get_supabase()

    async def _get_access_token(self, oauth_token_id: UUID) -> str:
        """Get valid access token, refreshing if necessary."""
        # Get token from database
        token_response = self.supabase.table("oauth_tokens").select("*").eq("id", str(oauth_token_id)).single().execute()

        if not token_response.data:
            raise ProviderAuthError(f"OAuth token {oauth_token_id} not found")

        token = token_response.data

        # Check if token needs refresh (expires within 5 minutes)
        expires_at = datetime.fromisoformat(token["expires_at"].replace("Z", "+00:00"))
        now_utc = datetime.now(expires_at.tzinfo)  # Use same timezone as expires_at
        if expires_at <= now_utc + timedelta(minutes=5):
            logger.info(f"Refreshing expired Google token for user {token['user_id']}")
            await self._refresh_token(token)
            # Reload token after refresh
            token_response = self.supabase.table("oauth_tokens").select("*").eq("id", str(oauth_token_id)).single().execute()
            token = token_response.data

        # Decrypt token
        from app.security.encryption import encryption_service
        return encryption_service.decrypt_token(token["access_token"], token["user_id"])

    async def _refresh_token(self, token: Dict[str, Any]) -> None:
        """Refresh the access token using the refresh token."""
        from app.config.core.settings import get_settings
        from app.security.encryption import encryption_service

        settings = get_settings()

        # Decrypt refresh token
        decrypted_refresh = encryption_service.decrypt_token(token["refresh_token"], token["user_id"])

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": decrypted_refresh,
                    "grant_type": "refresh_token",
                },
            )

            if response.status_code != 200:
                logger.error(f"Failed to refresh Google token: {response.text}")
                raise ProviderAuthError("Failed to refresh access token")

            data = response.json()

            # Encrypt new access token
            encrypted_access = encryption_service.encrypt_token(data["access_token"], token["user_id"])

            # Update token in database
            self.supabase.table("oauth_tokens").update({
                "access_token": encrypted_access,
                "expires_at": (datetime.utcnow() + timedelta(seconds=data["expires_in"])).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", token["id"]).execute()

    async def _request(
        self,
        method: str,
        endpoint: str,
        oauth_token_id: UUID,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to Google Calendar API."""
        access_token = await self._get_access_token(oauth_token_id)

        request_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=request_headers,
            )

            # Handle specific error codes
            if response.status_code == 401:
                raise ProviderAuthError("Authentication failed")
            elif response.status_code == 410:
                raise SyncTokenInvalid("Sync token is no longer valid")
            elif response.status_code == 412:
                raise PreconditionFailed("Event etag mismatch")
            elif response.status_code >= 400:
                logger.error(f"Google API error: {response.status_code} - {response.text}")
                raise ProviderError(f"Google API error: {response.status_code}")

            if response.status_code == 204:
                return {}

            return response.json()

    async def list_calendars(self, oauth_token_id: UUID) -> List[Dict[str, Any]]:
        """List all calendars for the authenticated user."""
        result = await self._request(
            "GET",
            "users/me/calendarList",
            oauth_token_id,
        )

        calendars = []
        for item in result.get("items", []):
            calendars.append({
                "provider_calendar_id": item["id"],
                "summary": item.get("summary", ""),
                "timezone": item.get("timeZone", "UTC"),
                "is_primary": item.get("primary", False),
                "background_color": item.get("backgroundColor"),
                "foreground_color": item.get("foregroundColor"),
            })

        return calendars

    async def watch_calendar(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        callback_url: str,
        channel_token: str,
        ttl_days: int = 7
    ) -> Dict[str, Any]:
        """Set up a watch channel for calendar changes."""
        # Google Calendar watch channels expire after 1 week max
        expiration_ms = int((datetime.utcnow() + timedelta(days=ttl_days)).timestamp() * 1000)

        channel_id = str(uuid.uuid4())

        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        result = await self._request(
            "POST",
            f"calendars/{provider_calendar_id}/events/watch",
            UUID(oauth_token_id),
            json={
                "id": channel_id,
                "type": "web_hook",
                "address": callback_url,
                "token": channel_token,
                "expiration": expiration_ms,
            },
        )

        return {
            "channel_id": result["id"],
            "resource_id": result["resourceId"],
            "expiration": datetime.fromtimestamp(int(result["expiration"]) / 1000),
        }

    async def stop_watch(
        self,
        calendar_id: UUID,
        channel_id: str,
        resource_id: str
    ) -> None:
        """Stop an active watch channel."""
        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        await self._request(
            "POST",
            "channels/stop",
            UUID(oauth_token_id),
            json={
                "id": channel_id,
                "resourceId": resource_id,
            },
        )

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
        """List events with incremental sync support."""
        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        params: Dict[str, Any] = {
            "maxResults": max_results,
            "singleEvents": True,  # Expand recurring events
        }

        if sync_token:
            # Incremental sync
            params["syncToken"] = sync_token
        else:
            # Full sync with time window
            if time_min:
                params["timeMin"] = time_min.isoformat() + "Z"
            if time_max:
                params["timeMax"] = time_max.isoformat() + "Z"

        if page_token:
            params["pageToken"] = page_token

        # URL-encode calendar ID to handle special characters like # in holiday calendars
        from urllib.parse import quote
        encoded_calendar_id = quote(provider_calendar_id, safe='')

        result = await self._request(
            "GET",
            f"calendars/{encoded_calendar_id}/events",
            UUID(oauth_token_id),
            params=params,
        )

        return {
            "events": result.get("items", []),
            "next_page_token": result.get("nextPageToken"),
            "next_sync_token": result.get("nextSyncToken"),
        }

    async def get_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_id: str
    ) -> Dict[str, Any]:
        """Get a single event by ID."""
        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        return await self._request(
            "GET",
            f"calendars/{provider_calendar_id}/events/{event_id}",
            UUID(oauth_token_id),
        )

    async def insert_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new event."""
        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        return await self._request(
            "POST",
            f"calendars/{provider_calendar_id}/events",
            UUID(oauth_token_id),
            json=event_dict,
        )

    async def update_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_id: str,
        event_dict: Dict[str, Any],
        etag: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing event with optional etag for concurrency control."""
        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        headers = {}
        if etag:
            headers["If-Match"] = etag

        return await self._request(
            "PUT",
            f"calendars/{provider_calendar_id}/events/{event_id}",
            UUID(oauth_token_id),
            json=event_dict,
            headers=headers,
        )

    async def delete_event(
        self,
        calendar_id: UUID,
        provider_calendar_id: str,
        event_id: str
    ) -> None:
        """Delete an event."""
        # Get oauth_token_id from calendar_id
        calendar_response = self.supabase.table("calendar_calendars").select("oauth_token_id").eq("id", str(calendar_id)).single().execute()
        if not calendar_response.data:
            raise ProviderError(f"Calendar {calendar_id} not found")

        oauth_token_id = calendar_response.data["oauth_token_id"]

        await self._request(
            "DELETE",
            f"calendars/{provider_calendar_id}/events/{event_id}",
            UUID(oauth_token_id),
        )
