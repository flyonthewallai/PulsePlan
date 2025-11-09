"""
Focus Session Service - Track and analyze Pomodoro/focus sessions
Implements comprehensive session tracking with ML-ready data collection
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.database.repositories.user_repositories import (
    FocusSessionRepository,
    UserFocusProfileRepository,
    get_focus_session_repository,
    get_user_focus_profile_repository
)
from app.services.infrastructure.cache_service import get_cache_service
from app.config.core.settings import get_settings
from app.services.focus.entity_matcher import get_entity_matcher

logger = logging.getLogger(__name__)


class FocusSessionService:
    """Service for managing focus session tracking and analytics"""
    
    def __init__(
        self,
        focus_session_repository: Optional[FocusSessionRepository] = None,
        focus_profile_repository: Optional[UserFocusProfileRepository] = None
    ):
        self.settings = get_settings()
        self._focus_session_repository = focus_session_repository
        self._focus_profile_repository = focus_profile_repository
        self.cache_service = get_cache_service()
        self.entity_matcher = get_entity_matcher()
    
    @property
    def focus_session_repository(self) -> FocusSessionRepository:
        """Lazy-load focus session repository"""
        if self._focus_session_repository is None:
            self._focus_session_repository = get_focus_session_repository()
        return self._focus_session_repository
    
    @property
    def focus_profile_repository(self) -> UserFocusProfileRepository:
        """Lazy-load focus profile repository"""
        if self._focus_profile_repository is None:
            self._focus_profile_repository = get_user_focus_profile_repository()
        return self._focus_profile_repository
    
    async def start_session(
        self,
        user_id: str,
        expected_duration: int,
        task_id: Optional[str] = None,
        context: Optional[str] = None,
        session_type: str = "pomodoro",
        auto_match_entity: bool = True
    ) -> Dict[str, Any]:
        """
        Start a new focus session
        
        Args:
            user_id: User UUID
            expected_duration: Planned duration in minutes
            task_id: Optional linked task UUID
            context: Natural language description
            session_type: Type of session (pomodoro, deep_work, study, etc.)
            auto_match_entity: Whether to automatically match context to existing entities
        
        Returns:
            Created session data with session_id and matched entity info
        """
        try:
            logger.info(f"Starting focus session for user {user_id}, duration: {expected_duration}min")
            
            # Try to match entity if context provided and no task_id
            matched_entity = None
            if auto_match_entity and context and not task_id:
                matched_entity = await self.entity_matcher.match_entity(
                    user_id=user_id,
                    input_text=context,
                    duration_minutes=expected_duration
                )
                logger.info(
                    f"Entity match: {matched_entity['entity_type']} "
                    f"(confidence: {matched_entity['confidence']:.2f})"
                )
            
            now = datetime.now(timezone.utc)
            session_data = {
                "user_id": user_id,
                "start_time": now.isoformat(),
                "actual_start_time": now.isoformat(),
                "expected_duration": expected_duration,
                "session_type": session_type,
                "context": context,
                "original_input": context,  # Store original for learning
                "task_id": task_id,
                "was_completed": False,
                "interruption_count": 0,
                "cycles_completed": 0
            }
            
            # Add matched entity data
            if matched_entity:
                session_data.update({
                    "linked_entity_type": matched_entity['entity_type'],
                    "linked_entity_id": matched_entity['entity_id'],
                    "entity_match_confidence": matched_entity['confidence'],
                    "auto_created_entity": matched_entity['auto_created']
                })
                # Also set task_id for backward compatibility
                if matched_entity['entity_type'] in ['task', 'exam', 'assignment']:
                    session_data["task_id"] = matched_entity['entity_id']
            
            # Insert into database using repository
            session = await self.focus_session_repository.create_session(session_data)
            
            if session:
                session_id = session['id']
                
                # Cache active session
                await self.cache_service.set(
                    f"focus:active:{user_id}",
                    session,
                    ttl_seconds=expected_duration * 60 + 600  # Add 10 min buffer
                )
                
                # Increment session counter
                await self._increment_session_counter(user_id)
                
                logger.info(f"Focus session {session_id} started successfully")
                
                result = {
                    "success": True,
                    "session_id": session_id,
                    "session": session
                }
                
                # Include matched entity info
                if matched_entity:
                    result["matched_entity"] = {
                        "type": matched_entity['entity_type'],
                        "id": matched_entity['entity_id'],
                        "entity": matched_entity.get('entity'),
                        "confidence": matched_entity['confidence'],
                        "auto_created": matched_entity['auto_created'],
                        "match_reason": matched_entity['match_reason']
                    }
                
                return result
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            logger.error(f"Error starting focus session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def end_session(
        self,
        session_id: str,
        user_id: str,
        was_completed: bool = True,
        focus_score: Optional[int] = None,
        interruption_count: int = 0,
        session_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a focus session and record metrics
        
        Args:
            session_id: Session UUID
            user_id: User UUID
            was_completed: Whether session finished fully
            focus_score: User rating 1-5
            interruption_count: Number of interruptions
            session_notes: Optional user notes
        
        Returns:
            Updated session data with computed metrics
        """
        try:
            logger.info(f"Ending focus session {session_id} for user {user_id}")
            
            end_time = datetime.now(timezone.utc)
            
            # Get session to calculate duration using repository
            session = await self.focus_session_repository.get_by_id_and_user(
                session_id=session_id,
                user_id=user_id
            )
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            start_time = datetime.fromisoformat(
                session.get('actual_start_time', session['start_time']).replace('Z', '+00:00')
            )
            
            actual_duration = int((end_time - start_time).total_seconds() / 60)
            
            # Calculate cycles completed (assuming 25-min pomodoro standard)
            cycles = actual_duration // 25 if actual_duration > 0 else 0
            
            update_data = {
                "end_time": end_time.isoformat(),
                "actual_end_time": end_time.isoformat(),
                "duration_minutes": actual_duration,
                "was_completed": was_completed,
                "interruption_count": interruption_count,
                "cycles_completed": cycles,
                "focus_score": focus_score,
                "session_notes": session_notes
            }
            
            # Update session using repository
            updated_session = await self.focus_session_repository.update_session(
                session_id=session_id,
                user_id=user_id,
                update_data=update_data
            )
            
            if updated_session:
                
                # Clear active session cache
                await self.cache_service.delete(f"focus:active:{user_id}")
                
                # Invalidate user profile cache (needs recompute)
                await self.cache_service.delete(f"focus:profile:{user_id}")
                
                # Trigger async profile update (fire-and-forget)
                # This will be picked up by the background worker
                await self._schedule_profile_update(user_id)
                
                logger.info(f"Focus session {session_id} ended: {actual_duration}min, completed: {was_completed}")
                
                return {
                    "success": True,
                    "session": updated_session,
                    "actual_duration": actual_duration,
                    "expected_duration": session.get('expected_duration'),
                    "completion_percentage": (actual_duration / session.get('expected_duration', 1)) * 100
                }
            else:
                raise Exception("Failed to update session")
                
        except Exception as e:
            logger.error(f"Error ending focus session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's focus sessions with optional filters
        """
        try:
            # Build filters for repository
            filters = {}
            if start_date:
                filters["start_date"] = start_date.isoformat()
            if end_date:
                filters["end_date"] = end_date.isoformat()
            
            # Get sessions using repository (note: offset not supported in base implementation)
            sessions = await self.focus_session_repository.get_by_user(
                user_id=user_id,
                filters=filters,
                limit=limit + offset  # Get more and slice
            )
            
            # Apply offset manually
            sessions = sessions[offset:offset + limit] if offset > 0 else sessions[:limit]
            
            # Apply task_id filter manually if specified (not in repository filters)
            if task_id:
                sessions = [s for s in sessions if s.get("task_id") == task_id]
            
            return {
                "success": True,
                "sessions": sessions,
                "count": len(sessions)
            }
            
        except Exception as e:
            logger.error(f"Error fetching user sessions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "sessions": []
            }
    
    async def get_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get currently active session for user"""
        try:
            # Check cache first
            cached = await self.cache_service.get(f"focus:active:{user_id}")
            if cached:
                return cached
            
            # Query DB using repository for session without end_time
            sessions = await self.focus_session_repository.get_by_user(
                user_id=user_id,
                limit=10
            )
            
            # Find first session without end_time
            for s in sessions:
                if not s.get("end_time"):
                    return s
            return None
            
        except Exception as e:
            logger.error(f"Error getting active session: {e}", exc_info=True)
            return None
    
    async def get_user_profile(self, user_id: str, force_recompute: bool = False) -> Dict[str, Any]:
        """
        Get user's focus analytics profile
        
        Returns aggregated metrics like average duration, peak hours, etc.
        """
        try:
            # Check cache
            if not force_recompute:
                cached = await self.cache_service.get(f"focus:profile:{user_id}")
                if cached:
                    return cached
            
            # Query from DB using repository
            profile = await self.focus_profile_repository.get_by_user(user_id)
            
            if profile:
                
                # Cache for 1 hour
                await self.cache_service.set(
                    f"focus:profile:{user_id}",
                    profile,
                    ttl_seconds=3600
                )
                
                return profile
            else:
                # Profile doesn't exist, compute it
                return await self.compute_user_profile(user_id)
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}", exc_info=True)
            return {}
    
    async def compute_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Compute or recompute user's focus profile from session data
        This is the core analytics function
        """
        try:
            logger.info(f"Computing focus profile for user {user_id}")
            
            # Get all completed sessions using repository
            filters = {"was_completed": True}
            sessions = await self.focus_session_repository.get_by_user(
                user_id=user_id,
                filters=filters,
                limit=500
            )
            
            if not sessions:
                logger.info(f"No sessions found for user {user_id}, creating empty profile")
                return await self._create_empty_profile(user_id)
            
            # Compute aggregates
            total_duration = sum(s.get('duration_minutes', 0) for s in sessions)
            avg_duration = total_duration / len(sessions) if sessions else 0
            
            # Break metrics
            total_breaks = sum(s.get('break_minutes', 0) for s in sessions)
            avg_breaks = total_breaks / len(sessions) if sessions else 0
            
            # Interruption metrics
            total_interruptions = sum(s.get('interruption_count', 0) for s in sessions)
            avg_interruptions = total_interruptions / len(sessions) if sessions else 0
            
            # Completion ratio
            sessions_with_expected = [s for s in sessions if s.get('expected_duration')]
            if sessions_with_expected:
                completion_ratios = [
                    s.get('duration_minutes', 0) / s.get('expected_duration', 1)
                    for s in sessions_with_expected
                ]
                avg_completion_ratio = sum(completion_ratios) / len(completion_ratios)
            else:
                avg_completion_ratio = 1.0
            
            # Peak hours analysis
            hour_counts = {}
            for session in sessions:
                start_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                hour = start_time.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # Get top 3 peak hours
            peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_hours_list = [hour for hour, _ in peak_hours]
            
            # Day of week analysis
            day_counts = {}
            for session in sessions:
                start_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                day_name = start_time.strftime('%a')
                day_counts[day_name] = day_counts.get(day_name, 0) + 1
            
            peak_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_days_list = [day for day, _ in peak_days]
            
            # Underestimation analysis
            underestimations = []
            for session in sessions_with_expected:
                actual = session.get('duration_minutes', 0)
                expected = session.get('expected_duration', 1)
                if expected > 0:
                    diff_pct = ((actual - expected) / expected) * 100
                    underestimations.append(diff_pct)
            
            avg_underestimation = sum(underestimations) / len(underestimations) if underestimations else 0
            
            # Build profile data
            profile_data = {
                "user_id": user_id,
                "avg_focus_duration_minutes": int(avg_duration),
                "avg_break_duration_minutes": int(avg_breaks),
                "avg_interruption_count": round(avg_interruptions, 2),
                "avg_completion_ratio": round(avg_completion_ratio, 2),
                "peak_focus_hours": peak_hours_list,
                "peak_focus_days": peak_days_list,
                "avg_underestimation_pct": round(avg_underestimation, 2),
                "total_sessions_count": len(sessions),
                "completed_sessions_count": len([s for s in sessions if s.get('was_completed')]),
                "focus_by_hour": hour_counts,
                "last_computed_at": datetime.now(timezone.utc).isoformat(),
                "sessions_analyzed_count": len(sessions)
            }
            
            # Upsert into database
            response = self.supabase.table("user_focus_profiles")\
                .upsert(profile_data, on_conflict="user_id")\
                .execute()
            
            if response.data:
                computed_profile = response.data[0]
                
                # Cache it
                await self.cache_service.set(
                    f"focus:profile:{user_id}",
                    computed_profile,
                    ttl_seconds=3600
                )
                
                logger.info(f"Focus profile computed for user {user_id}: {len(sessions)} sessions analyzed")
                return computed_profile
            else:
                raise Exception("Failed to save computed profile")
                
        except Exception as e:
            logger.error(f"Error computing user profile: {e}", exc_info=True)
            return {}
    
    async def get_session_insights(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Get AI-powered insights for a specific session
        Compares against user's historical performance
        """
        try:
            # Get the session using repository
            session = await self.focus_session_repository.get_by_id_and_user(
                session_id=session_id,
                user_id=user_id
            )
            
            if not session:
                return {"error": "Session not found"}
            
            # Get user profile
            profile = await self.get_user_profile(user_id)
            
            insights = []
            
            # Compare duration
            if session.get('duration_minutes') and profile.get('avg_focus_duration_minutes'):
                duration = session['duration_minutes']
                avg = profile['avg_focus_duration_minutes']
                
                if duration > avg * 1.2:
                    insights.append({
                        "type": "positive",
                        "message": f"Great job! You focused {duration}min, {int((duration/avg - 1) * 100)}% longer than your average."
                    })
                elif duration < avg * 0.8:
                    insights.append({
                        "type": "info",
                        "message": f"This session was shorter than usual. Your average is {avg}min."
                    })
            
            # Interruption check
            if session.get('interruption_count', 0) == 0 and session.get('was_completed'):
                insights.append({
                    "type": "positive",
                    "message": "Perfect focus! No interruptions during this session."
                })
            
            # Score feedback
            if session.get('focus_score'):
                score = session['focus_score']
                if score >= 4:
                    insights.append({
                        "type": "positive",
                        "message": "You rated this session highly. Keep up the great work!"
                    })
            
            return {
                "session_id": session_id,
                "insights": insights,
                "session": session,
                "profile": profile
            }
            
        except Exception as e:
            logger.error(f"Error generating session insights: {e}", exc_info=True)
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _create_empty_profile(self, user_id: str) -> Dict[str, Any]:
        """Create initial empty profile for new user"""
        empty_profile = {
            "user_id": user_id,
            "avg_focus_duration_minutes": 0,
            "avg_break_duration_minutes": 0,
            "avg_interruption_count": 0.0,
            "avg_completion_ratio": 0.0,
            "peak_focus_hours": [],
            "peak_focus_days": [],
            "avg_underestimation_pct": 0.0,
            "total_sessions_count": 0,
            "completed_sessions_count": 0,
            "focus_by_hour": {},
            "last_computed_at": datetime.now(timezone.utc).isoformat(),
            "sessions_analyzed_count": 0
        }
        
        response = self.supabase.table("user_focus_profiles")\
            .upsert(empty_profile, on_conflict="user_id")\
            .execute()
        
        return response.data[0] if response.data else empty_profile
    
    async def _increment_session_counter(self, user_id: str):
        """Increment session counter in cache (for rate limiting if needed)"""
        key = f"focus:count:daily:{user_id}"
        count = await self.cache_service.get(key) or 0
        await self.cache_service.set(key, count + 1, ttl_seconds=86400)  # 24h TTL
    
    async def _schedule_profile_update(self, user_id: str):
        """Schedule async profile recomputation (via queue/worker)"""
        # For now, just set a flag in Redis that worker can pick up
        await self.cache_service.set(
            f"focus:needs_update:{user_id}",
            {"user_id": user_id, "scheduled_at": datetime.now(timezone.utc).isoformat()},
            ttl_seconds=3600
        )
    
    async def delete_session(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Delete a focus session
        
        Args:
            session_id: Session UUID to delete
            user_id: User UUID (for authorization)
        
        Returns:
            Dictionary with success status
        
        Raises:
            ValueError: If session not found or not owned by user
        """
        try:
            # Delete from database with user_id check for authorization
            deleted = await self.focus_session_repository.delete_session(
                session_id=session_id,
                user_id=user_id
            )
            
            if deleted:
                # Invalidate profile cache
                await self.cache_service.delete(f"focus:profile:{user_id}")
                
                logger.info(f"Deleted focus session {session_id} for user {user_id}")
                
                return {
                    "success": True,
                    "message": "Session deleted successfully"
                }
            else:
                raise ValueError("Session not found or not authorized")
                
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
            raise


# Singleton instance
_focus_session_service = None


def get_focus_session_service() -> FocusSessionService:
    """Get or create Focus Session Service singleton"""
    global _focus_session_service
    if _focus_session_service is None:
        _focus_session_service = FocusSessionService()
    return _focus_session_service


