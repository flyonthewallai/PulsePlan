"""
Calendar synchronization service - Main entry point

This module provides backward compatibility by re-exporting the modular
calendar sync components. The original 1009-line service has been split into:

- calendar_sync/sync_service.py (~450 lines) - Core CalendarSyncService
- calendar_sync/event_processor.py (~250 lines) - Event processing
- calendar_sync/webhook_service.py (~100 lines) - Webhook handling
- calendar_sync/sync_helpers.py (~220 lines) - Helper utilities
- calendar_sync/__init__.py (~30 lines) - Package exports

Total: ~1050 lines across 5 files (modular structure)
"""

# Re-export for backward compatibility
from app.services.integrations.calendar_sync import (
    CalendarSyncService,
    get_calendar_sync_service,
    CalendarWebhookService,
    get_calendar_webhook_service,
    EventProcessor,
    CalendarSyncHelpers,
    get_sync_helpers
)

__all__ = [
    "CalendarSyncService",
    "get_calendar_sync_service",
    "CalendarWebhookService",
    "get_calendar_webhook_service",
    "EventProcessor",
    "CalendarSyncHelpers",
    "get_sync_helpers",
]
