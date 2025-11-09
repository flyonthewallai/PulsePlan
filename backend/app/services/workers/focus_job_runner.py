"""Focus profile job runner used by APScheduler jobs.

This module provides single-run job methods that the scheduler can invoke
to compute and update user focus profiles periodically.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.services.focus.focus_session_service import get_focus_session_service
from app.services.infrastructure.cache_service import get_cache_service
from app.database.repositories.user_repositories import (
    FocusSessionRepository,
    UserFocusProfileRepository,
    get_focus_session_repository,
    get_user_focus_profile_repository,
)

logger = logging.getLogger(__name__)


class FocusJobRunner:
    """Executes discrete focus profile jobs (update profiles, cleanup)."""

    def __init__(
        self,
        focus_session_repository: Optional[FocusSessionRepository] = None,
        user_focus_profile_repository: Optional[UserFocusProfileRepository] = None,
        focus_service=None,
        cache_service=None,
    ) -> None:
        self._focus_session_repository = focus_session_repository
        self._user_focus_profile_repository = user_focus_profile_repository
        self.focus_service = focus_service or get_focus_session_service()
        self.cache_service = cache_service or get_cache_service()

    @property
    def focus_session_repository(self) -> FocusSessionRepository:
        if self._focus_session_repository is None:
            self._focus_session_repository = get_focus_session_repository()
        return self._focus_session_repository

    @property
    def user_focus_profile_repository(self) -> UserFocusProfileRepository:
        if self._user_focus_profile_repository is None:
            self._user_focus_profile_repository = get_user_focus_profile_repository()
        return self._user_focus_profile_repository

    async def run_profile_updates(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Process pending focus profile updates for users.

        Finds users needing profile updates from:
        1. Redis cache flags (focus:needs_update:*)
        2. Database (users with recent sessions but stale profiles)

        Args:
            batch_size: Maximum number of users to process in one run

        Returns:
            Summary dict with success/failed/skipped counts
        """
        logger.info("Starting focus profile update job")

        try:
            # Method 1: Check Redis for flagged users
            users_from_cache = await self._get_users_needing_update_from_cache()

            # Method 2: Check DB for users with recent sessions but old profiles
            users_from_db = await self._get_users_with_stale_profiles()

            # Combine and deduplicate
            all_users = list(set(users_from_cache + users_from_db))

            if not all_users:
                logger.info("No pending profile updates found")
                return {
                    "success": 0,
                    "failed": 0,
                    "skipped": 0,
                    "total_checked": 0,
                }

            # Limit to batch_size
            users_to_process = all_users[:batch_size]
            logger.info(f"Processing {len(users_to_process)} users (of {len(all_users)} total)")

            results = {
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "total_checked": len(all_users),
            }

            # Process each user
            for user_id in users_to_process:
                try:
                    result = await self._update_user_profile(user_id)
                    if result:
                        results["success"] += 1
                    else:
                        results["skipped"] += 1
                except Exception as e:
                    logger.error(f"Failed to update profile for user {user_id}: {e}", exc_info=True)
                    results["failed"] += 1

            logger.info(
                f"Focus profile update batch complete: "
                f"{results['success']} succeeded, "
                f"{results['failed']} failed, "
                f"{results['skipped']} skipped"
            )

            return results

        except Exception as e:
            logger.error(f"Error processing pending updates: {e}", exc_info=True)
            return {
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "total_checked": 0,
                "error": str(e),
            }

    async def _get_users_needing_update_from_cache(self) -> List[str]:
        """Get list of user IDs flagged in cache for profile update."""
        try:
            # Scan Redis for focus:needs_update:* keys
            client = await self.cache_service._get_client()
            pattern = "focus:needs_update:*"
            keys = await client.keys(pattern)

            user_ids = []
            for key in keys:
                # Extract user_id from key (format: focus:needs_update:{user_id})
                parts = key.split(":")
                if len(parts) >= 3:
                    user_ids.append(parts[2])

            return user_ids

        except Exception as e:
            logger.error(f"Error getting users from cache: {e}")
            return []

    async def _get_users_with_stale_profiles(self, hours: int = 24) -> List[str]:
        """
        Find users whose profiles haven't been updated recently but have new sessions.

        Args:
            hours: Consider profiles stale if older than this many hours
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Use repository method for complex query
            # Note: This method is in UserFocusProfileRepository but queries focus_sessions
            return await self.user_focus_profile_repository.get_users_with_stale_profiles(
                cutoff_time, limit=100
            )

        except Exception as e:
            logger.error(f"Error getting users with stale profiles: {e}")
            # Fallback: just get all users with sessions in last 24h
            try:
                cutoff = datetime.utcnow() - timedelta(hours=24)
                return await self.focus_session_repository.get_user_ids_with_recent_sessions(
                    cutoff, limit=100
                )
            except Exception:
                pass

            return []

    async def _update_user_profile(self, user_id: str) -> bool:
        """
        Update a single user's focus profile.

        Returns:
            True if updated successfully, False if skipped/failed
        """
        try:
            logger.info(f"Updating focus profile for user {user_id}")

            # Check if user has enough sessions (minimum 3 for meaningful stats)
            session_count = await self.focus_session_repository.get_session_count(user_id)

            if session_count < 3:
                logger.info(
                    f"User {user_id} has only {session_count} sessions, skipping profile update"
                )
                # Clear update flag
                await self.cache_service.delete(f"focus:needs_update:{user_id}")
                return False

            # Compute profile
            profile = await self.focus_service.compute_user_profile(user_id)

            if profile:
                logger.info(
                    f"Profile updated for user {user_id}: "
                    f"{profile.get('total_sessions_count')} sessions analyzed, "
                    f"avg duration: {profile.get('avg_focus_duration_minutes')}min"
                )

                # Clear update flag
                await self.cache_service.delete(f"focus:needs_update:{user_id}")

                return True
            else:
                logger.warning(f"Failed to compute profile for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
            return False


_job_runner: Optional[FocusJobRunner] = None


def get_focus_job_runner() -> FocusJobRunner:
    """Singleton accessor for FocusJobRunner."""
    global _job_runner
    if _job_runner is None:
        _job_runner = FocusJobRunner()
    return _job_runner


# Backward-compatible aliases -------------------------------------------------
FocusProfileWorker = FocusJobRunner


def get_focus_profile_worker() -> FocusJobRunner:
    """Backward-compatible alias for get_focus_job_runner."""
    return get_focus_job_runner()

