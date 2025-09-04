"""
Calendar synchronization service for Google Calendar and Microsoft Outlook
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    build = Request = Credentials = None

try:
    import httpx
except ImportError:
    httpx = None

from ..config.supabase import get_supabase_client
from ..services.cache_service import get_cache_service
from ..services.token_service import get_token_service
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class CalendarSyncService:
    """Service for synchronizing calendar events from multiple providers"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.cache_service = get_cache_service()
        self.token_service = get_token_service()
    
    async def sync_user_calendars(
        self, 
        user_id: str, 
        days_ahead: int = 30,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Sync calendars for a user from all connected providers"""
        try:
            # Get user's connected calendar providers
            connected_accounts = await self.token_service.get_user_tokens(user_id)
            
            sync_results = {
                "user_id": user_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "providers_synced": [],
                "total_events": 0,
                "errors": []
            }
            
            # Sync Google Calendar if connected
            if connected_accounts.get("google"):
                try:
                    google_result = await self._sync_google_calendar(
                        user_id, 
                        connected_accounts["google"],
                        days_ahead,
                        force_refresh
                    )
                    sync_results["providers_synced"].append("google")
                    sync_results["total_events"] += google_result.get("event_count", 0)
                except Exception as e:
                    logger.error(f"Google Calendar sync failed for user {user_id}: {e}")
                    sync_results["errors"].append(f"Google Calendar: {str(e)}")
            
            # Sync Microsoft Calendar if connected
            if connected_accounts.get("microsoft"):
                try:
                    microsoft_result = await self._sync_microsoft_calendar(
                        user_id,
                        connected_accounts["microsoft"],
                        days_ahead,
                        force_refresh
                    )
                    sync_results["providers_synced"].append("microsoft")
                    sync_results["total_events"] += microsoft_result.get("event_count", 0)
                except Exception as e:
                    logger.error(f"Microsoft Calendar sync failed for user {user_id}: {e}")
                    sync_results["errors"].append(f"Microsoft Calendar: {str(e)}")
            
            # Update sync status in database
            await self._update_sync_status(user_id, sync_results)
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Calendar sync failed for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "providers_synced": [],
                "total_events": 0,
                "errors": [f"Sync failed: {str(e)}"]
            }
    
    async def _sync_google_calendar(
        self,
        user_id: str,
        google_tokens: Dict[str, Any],
        days_ahead: int,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Sync Google Calendar events"""
        if not build or not Credentials:
            raise ImportError("Google API libraries not available")
        
        try:
            # Check cache first
            cache_key = f"google_calendar_{days_ahead}d"
            if not force_refresh:
                cached_events = await self.cache_service.get_user_calendar_events(
                    user_id, cache_key
                )
                if cached_events:
                    return {"event_count": len(cached_events), "cached": True}
            
            # Prepare credentials
            creds = Credentials(
                token=google_tokens["access_token"],
                refresh_token=google_tokens.get("refresh_token"),
                client_id=self.settings.GOOGLE_CLIENT_ID,
                client_secret=self.settings.GOOGLE_CLIENT_SECRET
            )
            
            # Refresh token if needed
            if creds.expired:
                creds.refresh(Request())
                # Update tokens in database
                await self.token_service.update_tokens(
                    user_id, 
                    "google",
                    {
                        "access_token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "expires_at": creds.expiry.isoformat() if creds.expiry else None
                    }
                )
            
            # Build Google Calendar service
            service = build('calendar', 'v3', credentials=creds)
            
            # Define time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Get events from primary calendar
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=250,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process and store events
            processed_events = []
            for event in events:
                processed_event = await self._process_google_event(user_id, event)
                if processed_event:
                    processed_events.append(processed_event)
            
            # Store events in database
            if processed_events:
                await self._store_calendar_events(user_id, processed_events, "google")
            
            # Cache results
            await self.cache_service.set_user_calendar_events(
                user_id, cache_key, processed_events, 300
            )
            
            logger.info(f"Synced {len(processed_events)} Google Calendar events for user {user_id}")
            
            return {"event_count": len(processed_events), "cached": False}
            
        except Exception as e:
            logger.error(f"Google Calendar sync error for user {user_id}: {e}")
            raise
    
    async def _sync_microsoft_calendar(
        self,
        user_id: str,
        microsoft_tokens: Dict[str, Any],
        days_ahead: int,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Sync Microsoft Calendar events"""
        if not httpx:
            raise ImportError("httpx library not available")
        
        try:
            # Check cache first
            cache_key = f"microsoft_calendar_{days_ahead}d"
            if not force_refresh:
                cached_events = await self.cache_service.get_user_calendar_events(
                    user_id, cache_key
                )
                if cached_events:
                    return {"event_count": len(cached_events), "cached": True}
            
            # Prepare time range
            now = datetime.utcnow()
            start_time = now.isoformat() + 'Z'
            end_time = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Microsoft Graph API endpoint
            url = f"https://graph.microsoft.com/v1.0/me/calendar/events"
            params = {
                '$select': 'id,subject,start,end,location,bodyPreview,importance,sensitivity,showAs,isAllDay,isCancelled,organizer,attendees',
                '$filter': f"start/dateTime ge '{start_time}' and start/dateTime le '{end_time}'",
                '$orderby': 'start/dateTime',
                '$top': 250
            }
            
            headers = {
                'Authorization': f"Bearer {microsoft_tokens['access_token']}",
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 401:
                    # Token expired, try to refresh
                    refreshed_tokens = await self.token_service.refresh_microsoft_token(
                        user_id, microsoft_tokens.get("refresh_token")
                    )
                    if refreshed_tokens:
                        headers['Authorization'] = f"Bearer {refreshed_tokens['access_token']}"
                        response = await client.get(url, params=params, headers=headers)
                
                response.raise_for_status()
                data = response.json()
            
            events = data.get('value', [])
            
            # Process and store events
            processed_events = []
            for event in events:
                processed_event = await self._process_microsoft_event(user_id, event)
                if processed_event:
                    processed_events.append(processed_event)
            
            # Store events in database
            if processed_events:
                await self._store_calendar_events(user_id, processed_events, "microsoft")
            
            # Cache results
            await self.cache_service.set_user_calendar_events(
                user_id, cache_key, processed_events, 300
            )
            
            logger.info(f"Synced {len(processed_events)} Microsoft Calendar events for user {user_id}")
            
            return {"event_count": len(processed_events), "cached": False}
            
        except Exception as e:
            logger.error(f"Microsoft Calendar sync error for user {user_id}: {e}")
            raise
    
    async def _process_google_event(self, user_id: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a Google Calendar event into standard format"""
        try:
            # Extract start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Handle all-day events
            if 'date' in start:
                start_time = datetime.fromisoformat(start['date']).isoformat() + 'Z'
                end_time = datetime.fromisoformat(end['date']).isoformat() + 'Z'
                is_all_day = True
            else:
                start_time = start.get('dateTime', '')
                end_time = end.get('dateTime', '')
                is_all_day = False
            
            return {
                "external_id": event.get('id'),
                "provider": "google",
                "calendar_id": event.get('organizer', {}).get('email', 'primary'),
                "title": event.get('summary', 'Untitled Event'),
                "description": event.get('description', ''),
                "start_time": start_time,
                "end_time": end_time,
                "location": event.get('location', ''),
                "status": event.get('status', 'confirmed'),
                "html_link": event.get('htmlLink', ''),
                "attendees": event.get('attendees', []),
                "creator_email": event.get('creator', {}).get('email', ''),
                "organizer_email": event.get('organizer', {}).get('email', ''),
                "color_id": event.get('colorId'),
                "transparency": event.get('transparency', 'opaque'),
                "visibility": event.get('visibility', 'default'),
                "is_all_day": is_all_day,
                "is_cancelled": event.get('status') == 'cancelled',
                "has_attachments": bool(event.get('attachments')),
                "recurrence": event.get('recurrence'),
                "created_at": event.get('created'),
                "updated_at": event.get('updated'),
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Google event {event.get('id')}: {e}")
            return None
    
    async def _process_microsoft_event(self, user_id: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a Microsoft Calendar event into standard format"""
        try:
            start = event.get('start', {})
            end = event.get('end', {})
            
            return {
                "external_id": event.get('id'),
                "provider": "microsoft",
                "calendar_id": "primary",  # Microsoft Graph doesn't provide calendar ID in this context
                "title": event.get('subject', 'Untitled Event'),
                "description": event.get('bodyPreview', ''),
                "start_time": start.get('dateTime', ''),
                "end_time": end.get('dateTime', ''),
                "location": event.get('location', {}).get('displayName', ''),
                "status": 'confirmed',  # Microsoft uses different status model
                "html_link": event.get('webLink', ''),
                "attendees": event.get('attendees', []),
                "creator_email": event.get('organizer', {}).get('emailAddress', {}).get('address', ''),
                "organizer_email": event.get('organizer', {}).get('emailAddress', {}).get('address', ''),
                "importance": event.get('importance', 'normal'),
                "sensitivity": event.get('sensitivity', 'normal'),
                "is_all_day": event.get('isAllDay', False),
                "is_cancelled": event.get('isCancelled', False),
                "has_attachments": bool(event.get('hasAttachments')),
                "created_at": event.get('createdDateTime'),
                "updated_at": event.get('lastModifiedDateTime'),
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Microsoft event {event.get('id')}: {e}")
            return None
    
    async def _store_calendar_events(
        self, 
        user_id: str, 
        events: List[Dict[str, Any]], 
        provider: str
    ):
        """Store calendar events in database"""
        try:
            # Clear existing events from this provider for the user
            await self.supabase.table("calendar_events").delete().match({
                "user_id": user_id,
                "provider": provider
            }).execute()
            
            # Insert new events
            for event in events:
                event["user_id"] = user_id
                
            if events:
                await self.supabase.table("calendar_events").insert(events).execute()
                
        except Exception as e:
            logger.error(f"Error storing calendar events for user {user_id}: {e}")
            raise
    
    async def create_google_event(self, user_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Google Calendar and store in database"""
        if not build or not Credentials:
            raise ImportError("Google API libraries not available")
        
        try:
            # Get user's Google tokens
            tokens = await self.token_service.get_user_tokens(user_id)
            google_tokens = tokens.get("google")
            if not google_tokens:
                raise Exception("No Google account connected")
            
            # Prepare credentials
            creds = Credentials(
                token=google_tokens["access_token"],
                refresh_token=google_tokens.get("refresh_token"),
                client_id=self.settings.GOOGLE_CLIENT_ID,
                client_secret=self.settings.GOOGLE_CLIENT_SECRET
            )
            
            # Refresh token if needed
            if creds.expired:
                creds.refresh(Request())
                await self.token_service.update_tokens(
                    user_id, "google",
                    {
                        "access_token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "expires_at": creds.expiry.isoformat() if creds.expiry else None
                    }
                )
            
            # Build Google Calendar service
            service = build('calendar', 'v3', credentials=creds)
            
            # Create event in Google Calendar
            google_event = {
                'summary': event_data.get('title', 'New Event'),
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'start': {
                    'dateTime': event_data.get('start'),
                    'timeZone': event_data.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': event_data.get('end'),
                    'timeZone': event_data.get('timezone', 'UTC')
                }
            }
            
            created_event = service.events().insert(
                calendarId='primary',
                body=google_event
            ).execute()
            
            # Process and store in database
            processed_event = await self._process_google_event(user_id, created_event)
            if processed_event:
                await self._store_calendar_events(user_id, [processed_event], "google")
            
            logger.info(f"Created Google Calendar event {created_event['id']} for user {user_id}")
            return processed_event
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar event for user {user_id}: {e}")
            raise
    
    async def update_google_event(self, user_id: str, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update event in Google Calendar and database"""
        if not build or not Credentials:
            raise ImportError("Google API libraries not available")
        
        try:
            # Get user's Google tokens
            tokens = await self.token_service.get_user_tokens(user_id)
            google_tokens = tokens.get("google")
            if not google_tokens:
                raise Exception("No Google account connected")
            
            # Prepare credentials
            creds = Credentials(
                token=google_tokens["access_token"],
                refresh_token=google_tokens.get("refresh_token"),
                client_id=self.settings.GOOGLE_CLIENT_ID,
                client_secret=self.settings.GOOGLE_CLIENT_SECRET
            )
            
            # Refresh token if needed
            if creds.expired:
                creds.refresh(Request())
                await self.token_service.update_tokens(
                    user_id, "google",
                    {
                        "access_token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "expires_at": creds.expiry.isoformat() if creds.expiry else None
                    }
                )
            
            # Build Google Calendar service
            service = build('calendar', 'v3', credentials=creds)
            
            # Get existing event
            existing_event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update event data
            if 'title' in event_data:
                existing_event['summary'] = event_data['title']
            if 'description' in event_data:
                existing_event['description'] = event_data['description']
            if 'location' in event_data:
                existing_event['location'] = event_data['location']
            if 'start' in event_data:
                existing_event['start']['dateTime'] = event_data['start']
            if 'end' in event_data:
                existing_event['end']['dateTime'] = event_data['end']
            
            # Update in Google Calendar
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event
            ).execute()
            
            # Process and update in database
            processed_event = await self._process_google_event(user_id, updated_event)
            if processed_event:
                # Update existing record
                await self.supabase.table("calendar_events").update(processed_event).match({
                    "user_id": user_id,
                    "external_id": event_id,
                    "provider": "google"
                }).execute()
            
            logger.info(f"Updated Google Calendar event {event_id} for user {user_id}")
            return processed_event
            
        except Exception as e:
            logger.error(f"Error updating Google Calendar event {event_id} for user {user_id}: {e}")
            raise
    
    async def delete_google_event(self, user_id: str, event_id: str) -> bool:
        """Delete event from Google Calendar and database"""
        if not build or not Credentials:
            raise ImportError("Google API libraries not available")
        
        try:
            # Get user's Google tokens
            tokens = await self.token_service.get_user_tokens(user_id)
            google_tokens = tokens.get("google")
            if not google_tokens:
                raise Exception("No Google account connected")
            
            # Prepare credentials
            creds = Credentials(
                token=google_tokens["access_token"],
                refresh_token=google_tokens.get("refresh_token"),
                client_id=self.settings.GOOGLE_CLIENT_ID,
                client_secret=self.settings.GOOGLE_CLIENT_SECRET
            )
            
            # Refresh token if needed
            if creds.expired:
                creds.refresh(Request())
                await self.token_service.update_tokens(
                    user_id, "google",
                    {
                        "access_token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "expires_at": creds.expiry.isoformat() if creds.expiry else None
                    }
                )
            
            # Build Google Calendar service
            service = build('calendar', 'v3', credentials=creds)
            
            # Delete from Google Calendar
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Delete from database
            await self.supabase.table("calendar_events").delete().match({
                "user_id": user_id,
                "external_id": event_id,
                "provider": "google"
            }).execute()
            
            logger.info(f"Deleted Google Calendar event {event_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event {event_id} for user {user_id}: {e}")
            return False
    
    async def create_microsoft_event(self, user_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Microsoft Calendar and store in database"""
        if not httpx:
            raise ImportError("httpx library not available")
        
        try:
            # Get user's Microsoft tokens
            tokens = await self.token_service.get_user_tokens(user_id)
            microsoft_tokens = tokens.get("microsoft")
            if not microsoft_tokens:
                raise Exception("No Microsoft account connected")
            
            # Prepare event data for Microsoft Graph API
            microsoft_event = {
                "subject": event_data.get('title', 'New Event'),
                "body": {
                    "contentType": "HTML",
                    "content": event_data.get('description', '')
                },
                "start": {
                    "dateTime": event_data.get('start'),
                    "timeZone": event_data.get('timezone', 'UTC')
                },
                "end": {
                    "dateTime": event_data.get('end'),
                    "timeZone": event_data.get('timezone', 'UTC')
                },
                "location": {
                    "displayName": event_data.get('location', '')
                }
            }
            
            headers = {
                'Authorization': f"Bearer {microsoft_tokens['access_token']}",
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://graph.microsoft.com/v1.0/me/calendar/events",
                    json=microsoft_event,
                    headers=headers
                )
                
                if response.status_code == 401:
                    # Token expired, try to refresh
                    refreshed_tokens = await self.token_service.refresh_microsoft_token(
                        user_id, microsoft_tokens.get("refresh_token")
                    )
                    if refreshed_tokens:
                        headers['Authorization'] = f"Bearer {refreshed_tokens['access_token']}"
                        response = await client.post(
                            "https://graph.microsoft.com/v1.0/me/calendar/events",
                            json=microsoft_event,
                            headers=headers
                        )
                
                response.raise_for_status()
                created_event = response.json()
            
            # Process and store in database
            processed_event = await self._process_microsoft_event(user_id, created_event)
            if processed_event:
                await self._store_calendar_events(user_id, [processed_event], "microsoft")
            
            logger.info(f"Created Microsoft Calendar event {created_event['id']} for user {user_id}")
            return processed_event
            
        except Exception as e:
            logger.error(f"Error creating Microsoft Calendar event for user {user_id}: {e}")
            raise
    
    async def detect_and_resolve_conflicts(self, user_id: str) -> Dict[str, Any]:
        """Detect and resolve calendar sync conflicts"""
        try:
            # Get all events for the user
            events = await self.get_user_events(user_id)
            
            conflicts = []
            resolved_conflicts = 0
            
            # Group events by time windows to detect duplicates and overlaps
            events_by_time = {}
            for event in events:
                start_time = event['start_time']
                time_key = start_time[:16]  # Group by date and hour
                
                if time_key not in events_by_time:
                    events_by_time[time_key] = []
                events_by_time[time_key].append(event)
            
            # Detect conflicts within time windows
            for time_key, time_events in events_by_time.items():
                if len(time_events) > 1:
                    # Check for duplicates (same title, similar times)
                    for i, event1 in enumerate(time_events):
                        for j, event2 in enumerate(time_events[i+1:], i+1):
                            similarity_score = self._calculate_event_similarity(event1, event2)
                            
                            if similarity_score > 0.8:  # High similarity = likely duplicate
                                conflict = {
                                    "user_id": user_id,
                                    "event1_id": event1['id'],
                                    "event2_id": event2['id'],
                                    "conflict_type": "duplicate",
                                    "confidence_score": similarity_score,
                                    "resolution_status": "unresolved",
                                    "detected_at": datetime.utcnow().isoformat()
                                }
                                
                                # Store conflict in database
                                await self.supabase.table("calendar_sync_conflicts").insert(conflict).execute()
                                conflicts.append(conflict)
                                
                                # Auto-resolve: keep Google event if available, otherwise keep newest
                                if event1['provider'] == 'google' and event2['provider'] == 'microsoft':
                                    await self._resolve_conflict(conflict['user_id'], event1['id'], event2['id'], 'keep_event1', 'prefer_google')
                                    resolved_conflicts += 1
                                elif event2['provider'] == 'google' and event1['provider'] == 'microsoft':
                                    await self._resolve_conflict(conflict['user_id'], event2['id'], event1['id'], 'keep_event1', 'prefer_google')
                                    resolved_conflicts += 1
                                elif event1['synced_at'] > event2['synced_at']:
                                    await self._resolve_conflict(conflict['user_id'], event1['id'], event2['id'], 'keep_event1', 'prefer_newest')
                                    resolved_conflicts += 1
                                else:
                                    await self._resolve_conflict(conflict['user_id'], event2['id'], event1['id'], 'keep_event1', 'prefer_newest')
                                    resolved_conflicts += 1
            
            return {
                "conflicts_detected": len(conflicts),
                "conflicts_resolved": resolved_conflicts,
                "resolution_strategy": "prefer_google_then_newest",
                "conflicts": conflicts
            }
            
        except Exception as e:
            logger.error(f"Error detecting/resolving conflicts for user {user_id}: {e}")
            raise
    
    def _calculate_event_similarity(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> float:
        """Calculate similarity score between two events"""
        score = 0.0
        total_weight = 0.0
        
        # Title similarity (weight: 0.4)
        if event1.get('title') and event2.get('title'):
            title1 = event1['title'].lower().strip()
            title2 = event2['title'].lower().strip()
            if title1 == title2:
                score += 0.4
            elif title1 in title2 or title2 in title1:
                score += 0.3
            total_weight += 0.4
        
        # Time similarity (weight: 0.4)
        if event1.get('start_time') and event2.get('start_time'):
            start1 = datetime.fromisoformat(event1['start_time'].replace('Z', '+00:00'))
            start2 = datetime.fromisoformat(event2['start_time'].replace('Z', '+00:00'))
            time_diff = abs((start1 - start2).total_seconds())
            
            if time_diff == 0:
                score += 0.4
            elif time_diff < 900:  # 15 minutes
                score += 0.3
            elif time_diff < 3600:  # 1 hour
                score += 0.2
            total_weight += 0.4
        
        # Location similarity (weight: 0.2)
        if event1.get('location') and event2.get('location'):
            loc1 = event1['location'].lower().strip()
            loc2 = event2['location'].lower().strip()
            if loc1 == loc2:
                score += 0.2
            elif loc1 in loc2 or loc2 in loc1:
                score += 0.1
            total_weight += 0.2
        
        return score / total_weight if total_weight > 0 else 0.0
    
    async def _resolve_conflict(self, user_id: str, keep_event_id: str, remove_event_id: str, action: str, reason: str):
        """Resolve a calendar sync conflict"""
        try:
            # Update conflict status
            await self.supabase.table("calendar_sync_conflicts").update({
                "resolution_status": "resolved",
                "resolution_action": action,
                "resolved_at": datetime.utcnow().isoformat()
            }).match({
                "user_id": user_id,
                "event1_id": keep_event_id,
                "event2_id": remove_event_id
            }).execute()
            
            # Remove the conflicting event
            await self.supabase.table("calendar_events").delete().eq("id", remove_event_id).execute()
            
            logger.info(f"Resolved conflict for user {user_id}: kept {keep_event_id}, removed {remove_event_id} ({reason})")
            
        except Exception as e:
            logger.error(f"Error resolving conflict for user {user_id}: {e}")
    
    async def _update_sync_status(self, user_id: str, sync_results: Dict[str, Any]):
        """Update calendar sync status in database"""
        try:
            status_data = {
                "user_id": user_id,
                "last_sync_at": sync_results["sync_timestamp"],
                "sync_status": "success" if not sync_results["errors"] else "partial_failure",
                "synced_events_count": sync_results["total_events"],
                "errors": sync_results["errors"],
                "google_events": 0,  # Would be calculated from actual results
                "microsoft_events": 0,  # Would be calculated from actual results
                "sync_settings": {
                    "providers_synced": sync_results["providers_synced"],
                    "days_ahead": 30
                },
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert sync status
            await self.supabase.table("calendar_sync_status").upsert(
                status_data, 
                on_conflict="user_id"
            ).execute()
            
        except Exception as e:
            logger.error(f"Error updating sync status for user {user_id}: {e}")
    
    async def get_user_events(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get calendar events for user with optional filtering"""
        try:
            query = self.supabase.table("calendar_events").select("*").eq("user_id", user_id)
            
            if start_date:
                query = query.gte("start_time", start_date.isoformat())
            
            if end_date:
                query = query.lte("start_time", end_date.isoformat())
            
            if provider:
                query = query.eq("provider", provider)
            
            response = await query.order("start_time").execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting events for user {user_id}: {e}")
            return []
    
    async def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Get calendar sync status for user"""
        try:
            response = await self.supabase.table("calendar_sync_status").select("*").eq(
                "user_id", user_id
            ).single().execute()
            
            if response.data:
                return response.data
            else:
                return {
                    "user_id": user_id,
                    "sync_status": "never_synced",
                    "last_sync_at": None,
                    "synced_events_count": 0,
                    "errors": []
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "sync_status": "error",
                "last_sync_at": None,
                "synced_events_count": 0,
                "errors": [str(e)]
            }
    
    async def schedule_background_sync(self, user_id: str, interval_minutes: int = 10) -> bool:
        """Schedule background synchronization for user"""
        try:
            # This would integrate with a task queue like Celery or APScheduler
            # For now, just update the calendar preferences
            preferences = {
                "auto_sync_enabled": True,
                "sync_frequency_minutes": interval_minutes,
                "sync_period_days": 30,
                "conflict_resolution_strategy": "prefer_google",
                "create_external_events": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.supabase.table("calendar_preferences").upsert({
                "user_id": user_id,
                **preferences
            }, on_conflict="user_id").execute()
            
            logger.info(f"Scheduled background sync for user {user_id} every {interval_minutes} minutes")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling background sync for user {user_id}: {e}")
            return False


# Global calendar sync service instance
_calendar_sync_service: Optional[CalendarSyncService] = None

def get_calendar_sync_service() -> CalendarSyncService:
    """Get global calendar sync service instance"""
    global _calendar_sync_service
    if _calendar_sync_service is None:
        _calendar_sync_service = CalendarSyncService()
    return _calendar_sync_service


class CalendarWebhookService:
    """Service for handling calendar webhooks from providers"""
    
    def __init__(self):
        self.calendar_sync = get_calendar_sync_service()
    
    async def handle_google_webhook(self, user_id: str, resource_id: str, resource_state: str) -> Dict[str, Any]:
        """Handle Google Calendar webhook notification"""
        try:
            if resource_state == "sync":
                # Trigger incremental sync
                sync_result = await self.calendar_sync.sync_user_calendars(
                    user_id, days_ahead=7, force_refresh=True
                )
                
                # Detect and resolve any conflicts
                conflict_result = await self.calendar_sync.detect_and_resolve_conflicts(user_id)
                
                logger.info(f"Processed Google webhook for user {user_id}: {sync_result['total_events']} events, {conflict_result['conflicts_resolved']} conflicts resolved")
                
                return {
                    "success": True,
                    "sync_result": sync_result,
                    "conflict_result": conflict_result
                }
            
            return {"success": True, "message": "Webhook processed but no action taken"}
            
        except Exception as e:
            logger.error(f"Error handling Google webhook for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_microsoft_webhook(self, user_id: str, subscription_id: str, change_type: str) -> Dict[str, Any]:
        """Handle Microsoft Graph webhook notification"""
        try:
            if change_type in ["created", "updated", "deleted"]:
                # Trigger incremental sync
                sync_result = await self.calendar_sync.sync_user_calendars(
                    user_id, days_ahead=7, force_refresh=True
                )
                
                # Detect and resolve any conflicts
                conflict_result = await self.calendar_sync.detect_and_resolve_conflicts(user_id)
                
                logger.info(f"Processed Microsoft webhook for user {user_id}: {sync_result['total_events']} events, {conflict_result['conflicts_resolved']} conflicts resolved")
                
                return {
                    "success": True,
                    "sync_result": sync_result,
                    "conflict_result": conflict_result
                }
            
            return {"success": True, "message": "Webhook processed but no action taken"}
            
        except Exception as e:
            logger.error(f"Error handling Microsoft webhook for user {user_id}: {e}")
            return {"success": False, "error": str(e)}


# Global webhook service instance
_webhook_service: Optional[CalendarWebhookService] = None

def get_calendar_webhook_service() -> CalendarWebhookService:
    """Get global calendar webhook service instance"""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = CalendarWebhookService()
    return _webhook_service