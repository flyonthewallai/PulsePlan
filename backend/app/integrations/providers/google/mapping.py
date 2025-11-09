"""Mapping between PulsePlan tasks and Google Calendar events."""
from typing import Dict, Any, Optional
from datetime import datetime
import pytz


def task_to_gcal_event(task: Dict[str, Any], calendar_timezone: str = "UTC") -> Dict[str, Any]:
    """
    Convert a PulsePlan task to a Google Calendar event.

    Args:
        task: Task dictionary with fields like title, start_date, end_date, etc.
        calendar_timezone: Calendar timezone for date handling

    Returns:
        Google Calendar event dict
    """
    event = {
        "summary": task.get("title", "Untitled Task"),
        "description": task.get("description") or task.get("notes"),
    }

    # Handle timing - all-day vs timed events
    if task.get("all_day"):
        # All-day event uses date format (not dateTime)
        start_date = task.get("start_date")
        end_date = task.get("end_date")

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        event["start"] = {"date": start_date.strftime("%Y-%m-%d")}
        event["end"] = {"date": end_date.strftime("%Y-%m-%d")}
    else:
        # Timed event uses dateTime format
        start_date = task.get("start_date")
        end_date = task.get("end_date")

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # Ensure UTC timezone
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=pytz.UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=pytz.UTC)

        event["start"] = {
            "dateTime": start_date.isoformat(),
            "timeZone": calendar_timezone
        }
        event["end"] = {
            "dateTime": end_date.isoformat(),
            "timeZone": calendar_timezone
        }

    # Optional fields
    if task.get("location"):
        event["location"] = task["location"]

    if task.get("meeting_url"):
        if not event.get("description"):
            event["description"] = ""
        event["description"] += f"\n\nMeeting URL: {task['meeting_url']}"

    # Store PulsePlan task ID in extended properties for two-way sync
    event["extendedProperties"] = {
        "private": {
            "pulseplan_task_id": task.get("id", ""),
            "pulseplan_task_type": task.get("task_type", "task")
        }
    }

    # Reminders
    if task.get("reminder_minutes"):
        event["reminders"] = {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": minutes}
                for minutes in task["reminder_minutes"][:5]  # Google allows max 5 reminders
            ]
        }

    # Attendees (if any)
    if task.get("attendees"):
        event["attendees"] = [{"email": email} for email in task["attendees"]]

    return event


def gcal_to_cache_row(gcal_event: Dict[str, Any], user_id: str, calendar_id: str) -> Dict[str, Any]:
    """
    Convert a Google Calendar event to a calendar_events cache row.

    Args:
        gcal_event: Google Calendar event dict
        user_id: User ID
        calendar_id: Calendar calendars ID reference

    Returns:
        Dict for calendar_events table insertion
    """
    # Parse start/end times
    start_data = gcal_event.get("start", {})
    end_data = gcal_event.get("end", {})

    # Check if all-day event
    is_all_day = "date" in start_data

    if is_all_day:
        # All-day events use date field
        start_time = datetime.fromisoformat(start_data["date"] + "T00:00:00")
        end_time = datetime.fromisoformat(end_data["date"] + "T23:59:59")
    else:
        # Timed events use dateTime field
        start_time = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00"))

    # Extract attendees
    attendees = []
    if gcal_event.get("attendees"):
        attendees = [a.get("email") for a in gcal_event["attendees"] if a.get("email")]

    # Check if cancelled
    is_cancelled = gcal_event.get("status") == "cancelled"

    # Extract calendar_id as the provider's calendar ID (not our internal UUID)
    calendar_id_str = gcal_event.get("organizer", {}).get("email", "")

    return {
        "user_id": user_id,
        "calendar_id_ref": calendar_id,
        "provider": "google",
        "external_id": gcal_event["id"],
        "calendar_id": calendar_id_str,  # Provider's calendar ID
        "title": gcal_event.get("summary", ""),
        "description": gcal_event.get("description"),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "is_all_day": is_all_day,
        "location": gcal_event.get("location"),
        "attendees": attendees if attendees else None,
        "is_cancelled": is_cancelled,
        "synced_at": datetime.utcnow().isoformat(),  # Changed from last_synced
        "status": gcal_event.get("status", "confirmed"),
        "html_link": gcal_event.get("htmlLink"),
        "creator_email": gcal_event.get("creator", {}).get("email"),
        "organizer_email": gcal_event.get("organizer", {}).get("email"),
        "created_at": gcal_event.get("created"),
        "updated_at": gcal_event.get("updated"),
    }


def gcal_to_task_update(gcal_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Google Calendar event to task update fields (for conflict resolution).

    Args:
        gcal_event: Google Calendar event dict

    Returns:
        Dict with task fields to update
    """
    # Parse start/end times
    start_data = gcal_event.get("start", {})
    end_data = gcal_event.get("end", {})

    is_all_day = "date" in start_data

    if is_all_day:
        start_time = datetime.fromisoformat(start_data["date"] + "T00:00:00")
        end_time = datetime.fromisoformat(end_data["date"] + "T23:59:59")
    else:
        start_time = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00"))

    update = {
        "title": gcal_event.get("summary", ""),
        "description": gcal_event.get("description"),
        "start_date": start_time.isoformat(),
        "end_date": end_time.isoformat(),
        "all_day": is_all_day,
        "location": gcal_event.get("location"),
    }

    # Extract attendees
    if gcal_event.get("attendees"):
        update["attendees"] = [a.get("email") for a in gcal_event["attendees"] if a.get("email")]

    return update


def extract_pulseplan_task_id(gcal_event: Dict[str, Any]) -> Optional[str]:
    """
    Extract PulsePlan task ID from Google Calendar event extended properties.

    Args:
        gcal_event: Google Calendar event dict

    Returns:
        Task ID if found, else None
    """
    extended_props = gcal_event.get("extendedProperties", {})
    private_props = extended_props.get("private", {})
    return private_props.get("pulseplan_task_id")
