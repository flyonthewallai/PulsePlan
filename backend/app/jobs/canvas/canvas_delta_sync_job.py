"""Compatibility wrapper for canvas delta sync job."""

from app.services.workers.canvas_delta_sync_job import CanvasDeltaSyncJob, get_canvas_delta_sync_job

__all__ = ["CanvasDeltaSyncJob", "get_canvas_delta_sync_job"]
