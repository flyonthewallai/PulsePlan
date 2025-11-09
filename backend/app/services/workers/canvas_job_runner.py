"""Canvas job runner coordinating backfill, delta, and nightly syncs."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.jobs.canvas.canvas_backfill_job import get_canvas_backfill_job
from app.jobs.canvas.canvas_delta_sync_job import get_canvas_delta_sync_job
from app.jobs.canvas.nightly_canvas_sync import get_nightly_canvas_sync
from app.jobs.canvas.canvas_sync import get_canvas_sync


class CanvasJobRunner:
    """Facade around existing Canvas job implementations."""

    def __init__(self) -> None:
        self._backfill_job = get_canvas_backfill_job()
        self._delta_job = get_canvas_delta_sync_job()
        self._nightly_job = get_nightly_canvas_sync()
        self._canvas_sync = get_canvas_sync()

    async def run_backfill(self, user_id: str, force_restart: bool = False) -> Dict[str, Any]:
        return await self._backfill_job.execute_backfill(user_id=user_id, force_restart=force_restart)

    async def run_delta_sync(self, user_id: str) -> Dict[str, Any]:
        return await self._delta_job.execute_delta_sync(user_id)

    async def run_nightly_sync(self, batch_size: int = 50, max_concurrent: int = 10) -> Dict[str, Any]:
        return await self._nightly_job.run_nightly_sync(batch_size=batch_size, max_concurrent=max_concurrent)

    async def sync_user_canvas_data(
        self,
        user_id: str,
        *,
        canvas_api_key: Optional[str] = None,
        canvas_url: Optional[str] = None,
        force_refresh: bool = False,
        include_grades: bool = False,
    ) -> Dict[str, Any]:
        return await self._canvas_sync.sync_user_canvas_data(
            user_id=user_id,
            canvas_api_key=canvas_api_key,
            canvas_url=canvas_url,
            force_refresh=force_refresh,
            include_grades=include_grades,
        )


_canvas_job_runner: Optional[CanvasJobRunner] = None


def get_canvas_job_runner() -> CanvasJobRunner:
    global _canvas_job_runner
    if _canvas_job_runner is None:
        _canvas_job_runner = CanvasJobRunner()
    return _canvas_job_runner

