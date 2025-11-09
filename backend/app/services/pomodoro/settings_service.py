import logging
from typing import Dict, Any, Optional

from app.database.repositories.user_repositories import (
    PomodoroSettingsRepository,
    get_pomodoro_settings_repository
)

logger = logging.getLogger(__name__)


class PomodoroSettingsService:
    def __init__(self, pomodoro_settings_repository: Optional[PomodoroSettingsRepository] = None):
        self._pomodoro_settings_repository = pomodoro_settings_repository
    
    @property
    def pomodoro_settings_repository(self) -> PomodoroSettingsRepository:
        """Lazy-load pomodoro settings repository"""
        if self._pomodoro_settings_repository is None:
            self._pomodoro_settings_repository = get_pomodoro_settings_repository()
        return self._pomodoro_settings_repository

    async def get_settings(self, user_id: str) -> Dict[str, Any]:
        settings = await self.pomodoro_settings_repository.get_by_user(user_id)
        if settings:
            return settings
        # default row (not persisted until upsert)
        return {
            "user_id": user_id,
            "focus_minutes": 25,
            "break_minutes": 5,
            "long_break_minutes": 15,
            "cycles_per_session": 4,
            "auto_start_breaks": True,
            "auto_start_next_session": False,
            "play_sound_on_complete": True,
            "desktop_notifications": True,
        }

    async def upsert_settings(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.pomodoro_settings_repository.upsert_settings(
            user_id=user_id,
            settings_data=payload
        )
        if result:
            return result
        return {**payload, "user_id": user_id}


_settings_service = None


def get_pomodoro_settings_service() -> PomodoroSettingsService:
    global _settings_service
    if _settings_service is None:
        _settings_service = PomodoroSettingsService()
    return _settings_service








