import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.database.repositories.user_repositories import (
    FocusPhaseRepository,
    get_focus_phase_repository
)

logger = logging.getLogger(__name__)


class FocusPhaseService:
    def __init__(self, focus_phase_repository: Optional[FocusPhaseRepository] = None):
        self._focus_phase_repository = focus_phase_repository
    
    @property
    def focus_phase_repository(self) -> FocusPhaseRepository:
        """Lazy-load focus phase repository"""
        if self._focus_phase_repository is None:
            self._focus_phase_repository = get_focus_phase_repository()
        return self._focus_phase_repository

    async def start_phase(
        self,
        user_id: str,
        session_id: str,
        phase_type: str,
        expected_duration_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "phase_type": phase_type,
            "expected_duration_minutes": expected_duration_minutes,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        
        phase = await self.focus_phase_repository.create_phase(data)
        if phase:
            return {"success": True, "phase": phase}
        return {"success": False, "error": "Insert failed"}

    async def end_phase(
        self,
        user_id: str,
        phase_id: str,
        interrupted: bool = False,
        ended_at_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        ended = ended_at_iso or datetime.now(timezone.utc).isoformat()
        update_data = {"ended_at": ended, "interrupted": interrupted}
        
        phase = await self.focus_phase_repository.update_phase(
            phase_id=phase_id,
            user_id=user_id,
            update_data=update_data
        )
        if phase:
            return {"success": True, "phase": phase}
        return {"success": False, "error": "Update failed"}


_phase_service = None


def get_focus_phase_service() -> FocusPhaseService:
    global _phase_service
    if _phase_service is None:
        _phase_service = FocusPhaseService()
    return _phase_service








