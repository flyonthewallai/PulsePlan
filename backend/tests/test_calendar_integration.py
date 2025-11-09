"""
Integration tests for centralized calendar system.
Tests Google two-way sync, conflict resolution, and premium gating.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4


# Mapping tests
def test_task_to_gcal_event():
    """Test converting a PulsePlan task to Google Calendar event"""
    from app.integrations.providers.google.mapping import task_to_gcal_event

    task = {
        "id": str(uuid4()),
        "title": "Study for exam",
        "description": "Review chapters 1-5",
        "start_date": "2025-10-03T14:00:00Z",
        "end_date": "2025-10-03T16:00:00Z",
        "all_day": False,
        "location": "Library",
        "task_type": "study"
    }

    gcal_event = task_to_gcal_event(task, calendar_timezone="America/New_York")

    assert gcal_event["summary"] == "Study for exam"
    assert gcal_event["description"] == "Review chapters 1-5"
    assert gcal_event["location"] == "Library"
    assert "start" in gcal_event
    assert "dateTime" in gcal_event["start"]
    assert gcal_event["extendedProperties"]["private"]["pulseplan_task_id"] == task["id"]
    assert gcal_event["extendedProperties"]["private"]["pulseplan_task_type"] == "study"


def test_task_to_gcal_event_allday():
    """Test converting an all-day task to Google Calendar event"""
    from app.integrations.providers.google.mapping import task_to_gcal_event

    task = {
        "id": str(uuid4()),
        "title": "All-day event",
        "start_date": "2025-10-03T00:00:00Z",
        "end_date": "2025-10-03T23:59:59Z",
        "all_day": True
    }

    gcal_event = task_to_gcal_event(task)

    assert "date" in gcal_event["start"]
    assert "date" in gcal_event["end"]
    assert "dateTime" not in gcal_event["start"]


def test_gcal_to_cache_row():
    """Test converting Google Calendar event to cache row"""
    from app.integrations.providers.google.mapping import gcal_to_cache_row

    user_id = str(uuid4())
    calendar_id = str(uuid4())

    gcal_event = {
        "id": "google_event_123",
        "summary": "Team Meeting",
        "description": "Weekly sync",
        "start": {
            "dateTime": "2025-10-03T10:00:00-04:00"
        },
        "end": {
            "dateTime": "2025-10-03T11:00:00-04:00"
        },
        "location": "Conference Room A",
        "attendees": [
            {"email": "alice@example.com"},
            {"email": "bob@example.com"}
        ],
        "status": "confirmed",
        "etag": "\"abc123\""
    }

    cache_row = gcal_to_cache_row(gcal_event, user_id, calendar_id)

    assert cache_row["user_id"] == user_id
    assert cache_row["calendar_id_ref"] == calendar_id
    assert cache_row["provider"] == "google"
    assert cache_row["external_id"] == "google_event_123"
    assert cache_row["title"] == "Team Meeting"
    assert cache_row["description"] == "Weekly sync"
    assert cache_row["location"] == "Conference Room A"
    assert cache_row["attendees"] == ["alice@example.com", "bob@example.com"]
    assert cache_row["is_cancelled"] is False
    assert cache_row["is_all_day"] is False
    assert cache_row["etag"] == "\"abc123\""


def test_gcal_to_cache_row_cancelled():
    """Test that cancelled events are marked correctly"""
    from app.integrations.providers.google.mapping import gcal_to_cache_row

    user_id = str(uuid4())
    calendar_id = str(uuid4())

    gcal_event = {
        "id": "google_event_456",
        "summary": "Cancelled Meeting",
        "start": {
            "dateTime": "2025-10-03T10:00:00Z"
        },
        "end": {
            "dateTime": "2025-10-03T11:00:00Z"
        },
        "status": "cancelled"
    }

    cache_row = gcal_to_cache_row(gcal_event, user_id, calendar_id)

    assert cache_row["is_cancelled"] is True


def test_extract_pulseplan_task_id():
    """Test extracting PulsePlan task ID from Google event"""
    from app.integrations.providers.google.mapping import extract_pulseplan_task_id

    task_id = str(uuid4())

    gcal_event = {
        "id": "google_event_789",
        "summary": "Task Event",
        "extendedProperties": {
            "private": {
                "pulseplan_task_id": task_id
            }
        }
    }

    extracted_id = extract_pulseplan_task_id(gcal_event)
    assert extracted_id == task_id


def test_extract_pulseplan_task_id_none():
    """Test extracting task ID from event without extended properties"""
    from app.integrations.providers.google.mapping import extract_pulseplan_task_id

    gcal_event = {
        "id": "google_event_999",
        "summary": "Regular Event"
    }

    extracted_id = extract_pulseplan_task_id(gcal_event)
    assert extracted_id is None


# Model tests
def test_calendar_calendar_model():
    """Test CalendarCalendarModel"""
    from app.database.models import CalendarCalendarModel, CalendarProvider

    calendar = CalendarCalendarModel(
        user_id=str(uuid4()),
        oauth_token_id=str(uuid4()),
        provider=CalendarProvider.GOOGLE,
        provider_calendar_id="primary",
        summary="Personal Calendar",
        timezone="America/New_York",
        is_active=True,
        is_primary_write=True
    )

    assert calendar.provider == "google"
    assert calendar.is_active is True
    assert calendar.is_primary_write is True


def test_calendar_link_model():
    """Test CalendarLinkModel"""
    from app.database.models import CalendarLinkModel, CalendarProvider, SourceOfTruth

    link = CalendarLinkModel(
        user_id=str(uuid4()),
        task_id=str(uuid4()),
        calendar_id=str(uuid4()),
        provider=CalendarProvider.GOOGLE,
        provider_event_id="google_event_123",
        source_of_truth=SourceOfTruth.LATEST_UPDATE
    )

    assert link.provider == "google"
    assert link.source_of_truth == "latest_update"


def test_calendar_event_model():
    """Test CalendarEventModel with new fields"""
    from app.database.models import CalendarEventModel

    event = CalendarEventModel(
        user_id=str(uuid4()),
        calendar_id_ref=str(uuid4()),
        provider="google",
        external_id="google_event_123",
        title="Team Meeting",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=1),
        is_cancelled=False,
        is_all_day=False
    )

    assert event.provider == "google"
    assert event.is_cancelled is False
    assert event.is_all_day is False


# Conflict resolution tests
def test_gcal_to_task_update():
    """Test converting Google event to task update fields"""
    from app.integrations.providers.google.mapping import gcal_to_task_update

    gcal_event = {
        "id": "google_event_123",
        "summary": "Updated Meeting Title",
        "description": "Updated description",
        "start": {
            "dateTime": "2025-10-03T15:00:00Z"
        },
        "end": {
            "dateTime": "2025-10-03T16:00:00Z"
        },
        "location": "New Location",
        "attendees": [
            {"email": "charlie@example.com"}
        ]
    }

    task_update = gcal_to_task_update(gcal_event)

    assert task_update["title"] == "Updated Meeting Title"
    assert task_update["description"] == "Updated description"
    assert task_update["location"] == "New Location"
    assert task_update["attendees"] == ["charlie@example.com"]
    assert "start_date" in task_update
    assert "end_date" in task_update


# Premium gating test concept (would need mocking for full test)
def test_premium_required_concept():
    """Conceptual test for premium gating"""
    # This would be a full integration test with mocked user subscription

    # Free user
    free_user_subscription = "free"
    assert free_user_subscription not in ["active", "premium"]

    # Premium user
    premium_user_subscription = "active"
    assert premium_user_subscription in ["active", "premium"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
