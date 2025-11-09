# Centralized Calendar System

PulsePlan's centralized calendar system provides a unified view of time-blocked tasks and external calendar events with Google two-way sync.

## Architecture Overview

### Components

1. **Database Schema**
   - `calendar_calendars`: Discovered calendars per provider account
   - `calendar_links`: Links between PulsePlan tasks and provider events
   - `calendar_events`: Cached external events

2. **Provider Abstraction** ([backend/app/integrations/providers/](../app/integrations/providers/))
   - Base interface for calendar providers
   - Google Calendar client with auto-token refresh
   - Mapping utilities for task ↔ event conversion

3. **Sync Workers** ([backend/app/jobs/calendar/](../app/jobs/calendar/))
   - `discover_calendars`: Discover available calendars
   - `pull_incremental`: Incremental sync using sync tokens
   - `push_from_task`: Push task changes to provider
   - `renew_watch`: Renew webhook channels

4. **Webhooks** ([backend/app/api/v1/endpoints/calendar_modules/webhooks.py](../app/api/v1/endpoints/calendar_modules/webhooks.py))
   - Real-time updates from Google Calendar watch notifications

5. **API Endpoints** ([backend/app/api/v1/endpoints/calendar_modules/timeblocks.py](../app/api/v1/endpoints/calendar_modules/timeblocks.py))
   - `GET /v1/timeblocks`: Unified calendar view
   - `POST /v1/timeblocks/link-task`: Link task to calendar (premium)
   - `DELETE /v1/timeblocks/unlink-task`: Unlink task from calendar
   - `POST /v1/timeblocks/set-primary-write`: Set primary write calendar
   - `POST /v1/timeblocks/select-calendars`: Select active calendars for view

## Setup

### 1. Environment Variables

Add to your `.env`:

```bash
# Google Calendar Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URL=https://yourapp.com/auth/google/callback
GOOGLE_WEBHOOK_VERIFICATION_TOKEN=your_random_secure_token

# API Base URL (for webhooks)
API_BASE_URL=https://api.yourapp.com
```

### 2. Database Migration

The database schema is already applied via Supabase MCP. Tables created:
- `calendar_calendars`
- `calendar_links`
- `calendar_events` (updated with new columns)

### 3. Google Cloud Console Setup

1. Enable Google Calendar API
2. Create OAuth 2.0 credentials
3. Add authorized redirect URI
4. Copy client ID and secret to `.env`

### 4. Webhook Setup

Google Calendar webhooks require:
- Public HTTPS endpoint
- Webhook verification token
- Domain verification (for production)

Development: Use ngrok or similar to expose your local API.

## Usage

### User Flow

1. **Connect Google Account**
   - User authenticates via OAuth
   - System stores encrypted tokens in `oauth_tokens`

2. **Discover Calendars**
   ```bash
   # Trigger calendar discovery
   POST /v1/integrations/google/discover-calendars
   ```

3. **Set Primary Write Calendar**
   ```bash
   POST /v1/timeblocks/set-primary-write
   {
     "calendarId": "uuid"
   }
   ```

4. **View Unified Timeblocks**
   ```bash
   GET /v1/timeblocks?from=2025-10-02T00:00:00Z&to=2025-10-09T00:00:00Z
   ```

5. **Link Task to Calendar (Premium)**
   ```bash
   POST /v1/timeblocks/link-task
   {
     "taskId": "uuid"
   }
   ```

### Backend Operations

**Manual Sync Trigger**
```python
from app.jobs.calendar.calendar_sync_worker import get_calendar_sync_worker

sync_worker = get_calendar_sync_worker()

# Discover calendars
result = await sync_worker.discover_calendars(user_id, provider="google")

# Pull incremental updates
result = await sync_worker.pull_incremental(calendar_id)

# Push task to calendar
result = await sync_worker.push_from_task(task_id)

# Renew watch channel
result = await sync_worker.renew_watch(calendar_id)
```

**Scheduled Jobs**

The calendar scheduler ([backend/app/workers/calendar_scheduler.py](../app/workers/calendar_scheduler.py)) runs:

- **Incremental Pull**: Every 20 minutes during active hours
- **Watch Renewal**: Every hour for expiring channels (<12h)

## Conflict Resolution

When a linked event/task is edited in multiple places:

1. **source_of_truth="task"**: Task always wins
2. **source_of_truth="calendar"**: Calendar always wins
3. **source_of_truth="latest_update"** (default): Compare timestamps
   - If event updated after last push → calendar wins
   - If task updated after last pull → task wins

## Premium Gating

**Free Users:**
- ✅ Read-only import of external calendars
- ✅ View unified timeblocks
- ❌ Two-way sync (create/update/delete provider events)

**Premium Users:**
- ✅ All free features
- ✅ Full two-way sync with primary write calendar
- ✅ Link tasks to calendar events
- ✅ Edit linked events in PulsePlan

Check subscription:
```python
user = supabase.table("users").select("subscription_status").eq("id", user_id).single()
is_premium = user["subscription_status"] in ["active", "premium"]
```

## Incremental Sync

Uses Google Calendar sync tokens for efficient updates:

1. **Initial Sync**: Fetch window (30 days back, 90 days forward)
2. **Save Sync Token**: Store `nextSyncToken` in `calendar_calendars.sync_token`
3. **Incremental Sync**: Use sync token to fetch only changes
4. **Handle 410 (Gone)**: Clear sync token and re-seed window

## Webhooks

Google Calendar watch channels:

- **TTL**: 7 days (renew when <12 hours remaining)
- **Verification**: Check `X-Goog-Channel-Token` header
- **States**:
  - `sync`: Initial notification (acknowledge only)
  - `exists`: Calendar changed (trigger pull)
  - `not_exists`: Resource deleted

Webhook endpoint: `POST /webhooks/google/calendar`

## Active Hours Scheduling

Incremental pulls only run during user active hours:

```python
# User working hours (default: all day if not set)
users.working_hours = {"start": 9, "end": 17}
users.timezone = "America/New_York"
```

This prevents unnecessary polling during sleep hours while webhooks handle real-time updates.

## Testing

Run integration tests:
```bash
cd backend
pytest tests/test_calendar_integration.py -v
```

Tests cover:
- Task ↔ Google Calendar event mapping
- All-day vs timed events
- Cancelled events
- Conflict resolution
- Premium gating concepts

## Troubleshooting

**Sync Token Invalid (410 Error)**
- Automatically handled by clearing token and re-syncing window

**Watch Channel Expired**
- Auto-renewed by scheduled job when <12 hours remaining

**Missing Primary Write Calendar**
- User must set primary write via `POST /v1/timeblocks/set-primary-write`

**Premium Features Not Working**
- Verify `users.subscription_status` in database
- Check API returns 402 Payment Required for free users

## Adding New Providers (Outlook/Apple)

1. Implement `CalendarProvider` interface in `app/integrations/providers/{provider}/`
2. Add provider-specific mapping functions
3. Update `CalendarProvider` enum in models
4. Add OAuth configuration to settings
5. Register provider in sync worker

## API Response Examples

### GET /v1/timeblocks

```json
{
  "items": [
    {
      "id": "task-uuid",
      "source": "task",
      "provider": null,
      "title": "Study for exam",
      "start": "2025-10-03T14:00:00Z",
      "end": "2025-10-03T16:00:00Z",
      "isAllDay": false,
      "readonly": false,
      "linkId": "link-uuid",
      "description": "Review chapters 1-5",
      "location": "Library",
      "color": "#1E40AF"
    },
    {
      "id": "google_event_123",
      "source": "calendar",
      "provider": "google",
      "title": "Team Meeting",
      "start": "2025-10-03T10:00:00Z",
      "end": "2025-10-03T11:00:00Z",
      "isAllDay": false,
      "readonly": true,
      "linkId": null,
      "description": "Weekly sync",
      "location": "Conference Room A"
    }
  ]
}
```

### POST /v1/timeblocks/link-task (Premium)

Request:
```json
{
  "taskId": "task-uuid"
}
```

Response:
```json
{
  "success": true,
  "message": "Task created",
  "eventId": "google_event_456"
}
```

### Error: Not Premium

```json
{
  "detail": "Premium subscription required for two-way calendar sync"
}
```
HTTP 402 Payment Required

## Architecture Decisions

1. **Single Primary Write**: Prevents conflicts and simplifies sync logic
2. **Sync Tokens over Polling**: Reduces API calls and improves performance
3. **Webhooks + Scheduled Sync**: Best of both worlds (instant + resilient)
4. **Active Hours Only**: Respects user privacy and reduces costs
5. **Supabase Direct Access**: Uses existing patterns (no SQLAlchemy for simplicity)

## Future Enhancements

- [ ] Outlook/Microsoft Calendar support
- [ ] Apple Calendar (CalDAV) support
- [ ] Recurring event expansion improvements
- [ ] Bulk operations API
- [ ] Calendar sharing/delegation
- [ ] Event reminders via push notifications
- [ ] Conflict resolution UI for users to choose winner
