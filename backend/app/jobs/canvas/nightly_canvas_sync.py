"""Compatibility wrapper for nightly Canvas sync."""

from app.services.workers.nightly_canvas_sync import NightlyCanvasSync, get_nightly_canvas_sync

__all__ = ["NightlyCanvasSync", "get_nightly_canvas_sync"]
