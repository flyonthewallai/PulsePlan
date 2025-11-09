"""
Focus Session API Endpoints
Handles Pomodoro/focus session tracking and analytics
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.focus.focus_session_service import get_focus_session_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models

class SessionStartRequest(BaseModel):
    """Request to start a new focus session"""
    expected_duration: int = Field(..., description="Expected duration in minutes", ge=1, le=480)
    task_id: Optional[str] = Field(None, description="Optional linked task UUID")
    context: Optional[str] = Field(None, description="Natural language description of focus context")
    session_type: str = Field("pomodoro", description="Session type: pomodoro, deep_work, study, break")
    auto_match_entity: bool = Field(True, description="Whether to automatically match context to existing entities")
    
    class Config:
        schema_extra = {
            "example": {
                "expected_duration": 25,
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "context": "Studying for biology exam - Chapter 5 cellular respiration",
                "session_type": "pomodoro"
            }
        }


class SessionEndRequest(BaseModel):
    """Request to end a focus session"""
    was_completed: bool = Field(True, description="Whether session was fully completed")
    focus_score: Optional[int] = Field(None, description="User rating of focus quality (1-5)", ge=1, le=5)
    interruption_count: int = Field(0, description="Number of interruptions during session", ge=0)
    session_notes: Optional[str] = Field(None, description="Optional notes about the session")
    
    class Config:
        schema_extra = {
            "example": {
                "was_completed": True,
                "focus_score": 4,
                "interruption_count": 1,
                "session_notes": "Had to take a quick phone call but stayed focused otherwise"
            }
        }


class SessionResponse(BaseModel):
    """Response containing session data"""
    success: bool
    session_id: Optional[str] = None
    session: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Endpoints

@router.post("/start", response_model=SessionResponse, status_code=201)
async def start_focus_session(
    request: SessionStartRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Start a new focus/Pomodoro session
    
    **Returns:**
    - `session_id`: UUID of the created session
    - `session`: Full session object including start time
    
    **Use this when:**
    - User clicks "Start" on Pomodoro timer
    - User begins a deep work session
    - AI agent initiates a focus block
    """
    try:
        logger.info(f"Starting focus session for user {current_user.user_id}")
        
        # Check if user already has an active session
        focus_service = get_focus_session_service()
        active_session = await focus_service.get_active_session(current_user.user_id)
        
        if active_session:
            logger.warning(f"User {current_user.user_id} attempted to start session with active session {active_session['id']}")
            # Auto-complete the previous session
            await focus_service.end_session(
                session_id=active_session['id'],
                user_id=current_user.user_id,
                was_completed=False  # Mark as incomplete since user started a new one
            )
        
        result = await focus_service.start_session(
            user_id=current_user.user_id,
            expected_duration=request.expected_duration,
            task_id=request.task_id,
            context=request.context,
            session_type=request.session_type,
            auto_match_entity=request.auto_match_entity
        )
        
        if result['success']:
            response_data = {
                "success": True,
                "session_id": result['session_id'],
                "session": result['session']
            }
            
            # Include matched entity info if available
            if 'matched_entity' in result:
                response_data["matched_entity"] = result['matched_entity']
                logger.info(
                    f"Matched entity: {result['matched_entity']['type']} "
                    f"(confidence: {result['matched_entity']['confidence']:.2f}, "
                    f"reason: {result['matched_entity']['match_reason']})"
                )
            
            return response_data
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to start session'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting focus session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/{session_id}/end", response_model=Dict[str, Any])
async def end_focus_session(
    session_id: str,
    request: SessionEndRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    End an active focus session and record metrics
    
    **Path Parameters:**
    - `session_id`: UUID of the session to end
    
    **Returns:**
    - Updated session with computed duration and metrics
    - Completion percentage vs expected duration
    - Triggers profile recomputation
    
    **Use this when:**
    - Timer completes
    - User manually stops session
    - Session is interrupted/cancelled
    """
    try:
        logger.info(f"Ending focus session {session_id} for user {current_user.user_id}")
        
        focus_service = get_focus_session_service()
        result = await focus_service.end_session(
            session_id=session_id,
            user_id=current_user.user_id,
            was_completed=request.was_completed,
            focus_score=request.focus_score,
            interruption_count=request.interruption_count,
            session_notes=request.session_notes
        )
        
        if result['success']:
            return {
                "success": True,
                "session": result['session'],
                "actual_duration": result['actual_duration'],
                "expected_duration": result['expected_duration'],
                "completion_percentage": result['completion_percentage']
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to end session'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending focus session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/active", response_model=Dict[str, Any])
async def get_active_session(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get user's currently active focus session (if any)
    
    **Returns:**
    - Active session data or null if no active session
    - Can be used to resume timer on app reopen
    """
    try:
        focus_service = get_focus_session_service()
        active_session = await focus_service.get_active_session(current_user.user_id)
        
        return {
            "active_session": active_session
        }
        
    except Exception as e:
        logger.error(f"Error getting active session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get active session: {str(e)}")


@router.get("/history", response_model=Dict[str, Any])
async def get_session_history(
    limit: int = Query(50, description="Number of sessions to return", ge=1, le=200),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    start_date: Optional[str] = Query(None, description="Filter sessions after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter sessions before this date (ISO format)"),
    task_id: Optional[str] = Query(None, description="Filter by specific task"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get user's focus session history
    
    **Query Parameters:**
    - `limit`: Max sessions to return (default 50, max 200)
    - `offset`: Pagination offset
    - `start_date`: ISO date to filter from
    - `end_date`: ISO date to filter to
    - `task_id`: Filter by specific task UUID
    
    **Returns:**
    - Array of session objects sorted by start_time DESC
    - Total count
    """
    try:
        focus_service = get_focus_session_service()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = await focus_service.get_user_sessions(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
            start_date=start_dt,
            end_date=end_dt,
            task_id=task_id
        )
        
        if result['success']:
            return {
                "sessions": result['sessions'],
                "count": result['count'],
                "limit": limit,
                "offset": offset
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to fetch sessions'))
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching session history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch session history: {str(e)}")


@router.get("/profile", response_model=Dict[str, Any])
async def get_focus_profile(
    recompute: bool = Query(False, description="Force recompute profile from scratch"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get user's aggregated focus analytics profile
    
    **Returns:**
    - Average focus duration
    - Peak productivity hours and days
    - Completion ratios
    - Interruption patterns
    - Task estimation accuracy
    
    **Use this for:**
    - Displaying user insights
    - Training predictive models
    - Personalized recommendations
    """
    try:
        focus_service = get_focus_session_service()
        
        if recompute:
            profile = await focus_service.compute_user_profile(current_user.user_id)
        else:
            profile = await focus_service.get_user_profile(current_user.user_id)
        
        return {
            "success": True,
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"Error fetching focus profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.get("/{session_id}/insights", response_model=Dict[str, Any])
async def get_session_insights(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get AI-powered insights for a specific session
    
    **Path Parameters:**
    - `session_id`: UUID of the session
    
    **Returns:**
    - Personalized insights comparing this session to user's history
    - Positive reinforcement for good habits
    - Suggestions for improvement
    """
    try:
        focus_service = get_focus_session_service()
        result = await focus_service.get_session_insights(
            user_id=current_user.user_id,
            session_id=session_id
        )
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating session insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a focus session
    
    **Path Parameters:**
    - `session_id`: UUID of the session to delete
    
    **Note:** This is a hard delete and will affect profile metrics
    """
    try:
        focus_service = get_focus_session_service()
        
        result = await focus_service.delete_session(
            session_id=session_id,
            user_id=current_user.user_id
        )
        
        return result
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

