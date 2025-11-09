"""
Pomodoro Settings and Phase APIs

Settings persist per user; phases log start/end events per focus session.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.pomodoro.settings_service import get_pomodoro_settings_service
from app.services.focus.focus_phase_service import get_focus_phase_service

logger = logging.getLogger(__name__)

router = APIRouter()


class PomodoroSettingsModel(BaseModel):
    focus_minutes: int = Field(25, ge=1, le=480)
    break_minutes: int = Field(5, ge=1, le=240)
    long_break_minutes: int = Field(15, ge=1, le=480)
    cycles_per_session: int = Field(4, ge=1, le=12)
    auto_start_breaks: bool = True
    auto_start_next_session: bool = False
    play_sound_on_complete: bool = True
    desktop_notifications: bool = True


@router.get("/settings", response_model=PomodoroSettingsModel)
async def get_settings(current_user: CurrentUser = Depends(get_current_user)):
    svc = get_pomodoro_settings_service()
    settings = await svc.get_settings(current_user.user_id)
    return PomodoroSettingsModel(**settings)


@router.put("/settings", response_model=PomodoroSettingsModel)
async def put_settings(
    payload: PomodoroSettingsModel,
    current_user: CurrentUser = Depends(get_current_user)
):
    svc = get_pomodoro_settings_service()
    settings = await svc.upsert_settings(current_user.user_id, payload.model_dump())
    return PomodoroSettingsModel(**settings)


class PhaseStartRequest(BaseModel):
    session_id: str
    phase_type: str = Field(..., pattern="^(focus|break|long_break)$")
    expected_duration_minutes: Optional[int] = None


class PhaseEndRequest(BaseModel):
    phase_id: str
    interrupted: Optional[bool] = False
    ended_at_iso: Optional[str] = None


@router.post("/phases/start", response_model=Dict[str, Any])
async def start_phase(
    payload: PhaseStartRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    svc = get_focus_phase_service()
    result = await svc.start_phase(
        user_id=current_user.user_id,
        session_id=payload.session_id,
        phase_type=payload.phase_type,
        expected_duration_minutes=payload.expected_duration_minutes,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to start phase"))
    return result


@router.post("/phases/end", response_model=Dict[str, Any])
async def end_phase(
    payload: PhaseEndRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    svc = get_focus_phase_service()
    result = await svc.end_phase(
        user_id=current_user.user_id,
        phase_id=payload.phase_id,
        interrupted=payload.interrupted or False,
        ended_at_iso=payload.ended_at_iso,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to end phase"))
    return result

