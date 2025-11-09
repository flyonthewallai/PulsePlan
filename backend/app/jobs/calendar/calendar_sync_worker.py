"""Compatibility wrapper for calendar sync worker."""

from app.services.workers.calendar_sync_worker import CalendarSyncWorker, get_calendar_sync_worker

__all__ = ["CalendarSyncWorker", "get_calendar_sync_worker"]
