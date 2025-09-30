"""
Canvas delta sync job - incremental sync for Canvas assignments
Runs every 15-30 minutes to fetch updates since last sync
"""
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import asyncio

try:
    import httpx
except ImportError:
    httpx = None

from app.config.database.supabase import get_supabase_client
from app.services.integrations.canvas_token_service import get_canvas_token_service
from app.database.models import TaskModel, ExternalSource, ExternalCursorModel

logger = logging.getLogger(__name__)


class CanvasDeltaSyncJob:
    """Delta sync job for incremental Canvas updates"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.token_service = get_canvas_token_service()

    async def execute_delta_sync(self, user_id: str) -> Dict[str, Any]:
        """
        Execute delta sync for a user

        Args:
            user_id: User ID to sync

        Returns:
            Dict with sync results
        """
        if not httpx:
            raise ImportError("httpx library required for Canvas integration")

        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting Canvas delta sync for user {user_id}")

            # Get Canvas credentials
            token_data = await self.token_service.retrieve_canvas_token(user_id)
            if not token_data:
                return await self._create_error_result(
                    user_id, start_time, "Canvas credentials not found or invalid"
                )

            # Check if integration needs reauth
            if token_data.get("status") == "needs_reauth":
                return await self._create_error_result(
                    user_id, start_time, "Canvas integration needs reauthorization"
                )

            api_token = token_data["api_token"]
            base_url = token_data["base_url"]

            # Get last delta sync timestamp
            last_sync = await self._get_last_delta_sync(user_id)
            if not last_sync:
                return await self._create_error_result(
                    user_id, start_time, "No initial sync found. Please run full backfill first."
                )

            # Calculate sync window
            since_timestamp = last_sync
            now_timestamp = datetime.utcnow()

            results = {
                "user_id": user_id,
                "started_at": start_time.isoformat(),
                "sync_window": {
                    "since": since_timestamp.isoformat(),
                    "until": now_timestamp.isoformat()
                },
                "courses_checked": 0,
                "assignments_updated": 0,
                "assignments_created": 0,
                "assignments_deleted": 0,
                "errors": []
            }

            # Get user's active courses
            courses = await self._get_user_active_courses(user_id, api_token, base_url)
            results["courses_checked"] = len(courses)

            # Check each course for updated assignments
            for course in courses:
                try:
                    course_result = await self._sync_course_assignments(
                        user_id, api_token, base_url, course, since_timestamp
                    )
                    results["assignments_updated"] += course_result["updated"]
                    results["assignments_created"] += course_result["created"]
                    results["errors"].extend(course_result["errors"])

                except Exception as e:
                    logger.error(f"Error syncing course {course.get('id')} for user {user_id}: {e}")
                    results["errors"].append(f"Course {course.get('id')}: {str(e)}")

            # Check for deleted assignments
            deleted_count = await self._check_for_deleted_assignments(
                user_id, api_token, base_url, since_timestamp
            )
            results["assignments_deleted"] = deleted_count

            # Update delta sync timestamp
            await self._update_last_delta_sync(user_id, now_timestamp)

            # Update integration status
            await self._update_integration_status(user_id)

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["completed_at"] = datetime.utcnow().isoformat()
            results["execution_time"] = execution_time
            results["status"] = "completed"

            logger.info(
                f"Canvas delta sync completed for user {user_id} in {execution_time:.2f}s. "
                f"Updated {results['assignments_updated']}, created {results['assignments_created']}, "
                f"deleted {results['assignments_deleted']} assignments"
            )

            return results

        except Exception as e:
            return await self._create_error_result(user_id, start_time, str(e))

    async def _get_last_delta_sync(self, user_id: str) -> Optional[datetime]:
        """Get timestamp of last delta sync"""
        try:
            response = await self.supabase.table("integration_canvas").select(
                "last_delta_at, last_full_sync_at"
            ).eq("user_id", user_id).single().execute()

            if not response.data:
                return None

            # Use last delta sync, or fall back to last full sync
            last_delta = response.data.get("last_delta_at")
            last_full = response.data.get("last_full_sync_at")

            if last_delta:
                return datetime.fromisoformat(last_delta)
            elif last_full:
                return datetime.fromisoformat(last_full)
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting last delta sync for user {user_id}: {e}")
            return None

    async def _get_user_active_courses(
        self,
        user_id: str,
        api_token: str,
        base_url: str
    ) -> List[Dict[str, Any]]:
        """Get user's active courses for delta sync"""
        try:
            headers = {"Authorization": f"Bearer {api_token}"}
            url = f"{base_url}/api/v1/courses"
            params = {
                "enrollment_type": "student",
                "enrollment_state": "active",
                "state": ["available"],
                "per_page": 100
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 401:
                await self.token_service.mark_needs_reauth(user_id, "401_unauthorized")
                raise ValueError("Canvas token is invalid (401)")

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching active courses for user {user_id}: {e}")
            raise

    async def _sync_course_assignments(
        self,
        user_id: str,
        api_token: str,
        base_url: str,
        course: Dict[str, Any],
        since_timestamp: datetime
    ) -> Dict[str, Any]:
        """Sync assignments for a specific course since timestamp"""
        course_id = course["id"]
        course_name = course.get("name", f"Course {course_id}")

        try:
            # Fetch assignments updated since last sync
            assignments = await self._fetch_updated_course_assignments(
                api_token, base_url, course_id, since_timestamp
            )

            if not assignments:
                return {"updated": 0, "created": 0, "errors": []}

            updated_count = 0
            created_count = 0
            errors = []

            # Process each assignment
            for assignment_data in assignments:
                try:
                    # Add course context
                    assignment_data["course_name"] = course_name
                    assignment_data["course_code"] = course.get("course_code", "")

                    # Check if assignment exists in our system
                    existing_task = await self._get_existing_task(
                        user_id, str(assignment_data["id"])
                    )

                    if existing_task:
                        # Update existing task if Canvas version is newer
                        canvas_updated = self._parse_canvas_timestamp(assignment_data.get("updated_at"))
                        our_updated = existing_task.get("external_updated_at")

                        if canvas_updated and (not our_updated or canvas_updated > datetime.fromisoformat(our_updated)):
                            await self._update_task_from_assignment(
                                existing_task["id"], assignment_data, canvas_updated
                            )
                            updated_count += 1
                    else:
                        # Create new task
                        await self._create_task_from_assignment(
                            user_id, assignment_data
                        )
                        created_count += 1

                except Exception as e:
                    logger.error(f"Error processing assignment {assignment_data.get('id')}: {e}")
                    errors.append(f"Assignment {assignment_data.get('id')}: {str(e)}")

            return {
                "updated": updated_count,
                "created": created_count,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Error syncing course {course_id} assignments: {e}")
            return {"updated": 0, "created": 0, "errors": [str(e)]}

    async def _fetch_updated_course_assignments(
        self,
        api_token: str,
        base_url: str,
        course_id: str,
        since_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch assignments updated since timestamp"""
        try:
            headers = {"Authorization": f"Bearer {api_token}"}
            url = f"{base_url}/api/v1/courses/{course_id}/assignments"

            # Use updated_since parameter if supported by Canvas
            params = {
                "include": ["submission"],
                "per_page": 100,
                "order_by": "updated_at",
                "bucket": ["upcoming", "overdue", "undated", "past"]
            }

            # Add updated_since if Canvas supports it (fallback to client-side filtering)
            canvas_timestamp = since_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            # params["updated_since"] = canvas_timestamp  # Uncomment if Canvas supports this

            assignments = []
            page = 1

            while True:
                params["page"] = page
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params=params, timeout=30)

                response.raise_for_status()
                page_assignments = response.json()

                if not page_assignments:
                    break

                # Filter assignments (published and updated since timestamp)
                for assignment in page_assignments:
                    if not assignment.get("published", False):
                        continue

                    # Client-side filtering by updated_at
                    updated_at = self._parse_canvas_timestamp(assignment.get("updated_at"))
                    if updated_at and updated_at > since_timestamp:
                        assignments.append(assignment)

                page += 1

                # Prevent infinite loops
                if page > 100:
                    logger.warning(f"Reached page limit for course {course_id}")
                    break

            return assignments

        except Exception as e:
            logger.error(f"Error fetching updated assignments for course {course_id}: {e}")
            raise

    async def _get_existing_task(self, user_id: str, canvas_id: str) -> Optional[Dict[str, Any]]:
        """Get existing task by external Canvas ID"""
        try:
            response = await self.supabase.table("tasks").select("*").eq(
                "user_id", user_id
            ).eq("external_source", "canvas").eq("external_id", canvas_id).single().execute()

            return response.data
        except Exception:
            return None

    async def _update_task_from_assignment(
        self,
        task_id: str,
        assignment_data: Dict[str, Any],
        canvas_updated: datetime
    ):
        """Update existing task with Canvas assignment data"""
        try:
            # Convert assignment to task updates
            updates = await self._assignment_to_task_updates(assignment_data, canvas_updated)

            await self.supabase.table("tasks").update(updates).eq("id", task_id).execute()

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            raise

    async def _create_task_from_assignment(
        self,
        user_id: str,
        assignment_data: Dict[str, Any]
    ):
        """Create new task from Canvas assignment"""
        try:
            # Convert assignment to task
            task_data = await self._assignment_to_task_data(user_id, assignment_data)

            await self.supabase.table("tasks").insert(task_data).execute()

        except Exception as e:
            logger.error(f"Error creating task from assignment {assignment_data.get('id')}: {e}")
            raise

    async def _assignment_to_task_updates(
        self,
        assignment_data: Dict[str, Any],
        canvas_updated: datetime
    ) -> Dict[str, Any]:
        """Convert Canvas assignment to task update fields"""
        # Extract due date
        due_at = assignment_data.get("due_at")
        due_date = None
        if due_at:
            try:
                due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00")).isoformat()
            except Exception:
                pass

        # Calculate estimated time
        points_possible = assignment_data.get("points_possible", 0) or 0
        estimated_minutes = max(30, min(300, int(points_possible * 3))) if points_possible > 0 else 60

        return {
            "title": assignment_data.get("name", "Untitled Assignment"),
            "description": assignment_data.get("description", ""),
            "subject": assignment_data.get("course_name", ""),
            "due_date": due_date,
            "estimated_minutes": estimated_minutes,
            "external_updated_at": canvas_updated.isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    async def _assignment_to_task_data(
        self,
        user_id: str,
        assignment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Canvas assignment to full task data"""
        # Extract due date
        due_at = assignment_data.get("due_at")
        due_date = None
        if due_at:
            try:
                due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00")).isoformat()
            except Exception:
                pass

        # Calculate estimated time
        points_possible = assignment_data.get("points_possible", 0) or 0
        estimated_minutes = max(30, min(300, int(points_possible * 3))) if points_possible > 0 else 60

        # Determine task type
        submission_types = assignment_data.get("submission_types", [])
        task_type = "assignment"
        if "online_quiz" in submission_types:
            task_type = "quiz"
        elif "discussion_topic" in submission_types:
            task_type = "task"

        # Get external updated_at
        external_updated_at = self._parse_canvas_timestamp(assignment_data.get("updated_at"))

        return {
            "user_id": user_id,
            "title": assignment_data.get("name", "Untitled Assignment"),
            "description": assignment_data.get("description", ""),
            "task_type": task_type,
            "subject": assignment_data.get("course_name", ""),
            "due_date": due_date,
            "estimated_minutes": estimated_minutes,
            "external_source": "canvas",
            "external_id": str(assignment_data["id"]),
            "external_course_id": str(assignment_data.get("course_id", "")),
            "external_updated_at": external_updated_at.isoformat() if external_updated_at else None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    async def _check_for_deleted_assignments(
        self,
        user_id: str,
        api_token: str,
        base_url: str,
        since_timestamp: datetime
    ) -> int:
        """Check for assignments that were deleted in Canvas"""
        # This is a simplified implementation
        # In practice, Canvas doesn't provide a direct way to detect deletions
        # You would need to compare the full list periodically

        # For now, we'll mark assignments as deleted if they haven't been updated
        # in a long time and are no longer published

        try:
            # Get our Canvas tasks that haven't been updated recently
            old_threshold = since_timestamp - timedelta(days=30)

            response = await self.supabase.table("tasks").select("*").eq(
                "user_id", user_id
            ).eq("external_source", "canvas").lt(
                "external_updated_at", old_threshold.isoformat()
            ).execute()

            old_tasks = response.data or []
            deleted_count = 0

            # For each old task, check if it still exists in Canvas
            for task in old_tasks:
                try:
                    external_course_id = task.get("external_course_id")
                    external_id = task.get("external_id")

                    if not external_course_id or not external_id:
                        continue

                    # Try to fetch the assignment from Canvas
                    headers = {"Authorization": f"Bearer {api_token}"}
                    url = f"{base_url}/api/v1/courses/{external_course_id}/assignments/{external_id}"

                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, headers=headers, timeout=10)

                    if response.status_code == 404:
                        # Assignment was deleted in Canvas, remove from our system
                        await self.supabase.table("tasks").delete().eq("id", task["id"]).execute()
                        deleted_count += 1
                        logger.info(f"Deleted task {task['id']} (Canvas assignment no longer exists)")

                except Exception as e:
                    # Ignore errors for individual assignment checks
                    logger.debug(f"Error checking assignment {task.get('external_id')}: {e}")

            return deleted_count

        except Exception as e:
            logger.error(f"Error checking for deleted assignments for user {user_id}: {e}")
            return 0

    async def _update_last_delta_sync(self, user_id: str, sync_timestamp: datetime):
        """Update last delta sync timestamp"""
        try:
            await self.supabase.table("integration_canvas").update({
                "last_delta_at": sync_timestamp.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

        except Exception as e:
            logger.error(f"Error updating last delta sync for user {user_id}: {e}")

    async def _update_integration_status(self, user_id: str):
        """Update integration status to OK"""
        try:
            await self.supabase.table("integration_canvas").update({
                "status": "ok",
                "last_error_code": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

        except Exception as e:
            logger.error(f"Error updating integration status for user {user_id}: {e}")

    def _parse_canvas_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Canvas timestamp string to datetime"""
        if not timestamp_str:
            return None

        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            return None

    async def _create_error_result(
        self,
        user_id: str,
        start_time: datetime,
        error_message: str
    ) -> Dict[str, Any]:
        """Create error result dict"""
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        # Mark integration status if needed
        if "401" in error_message or "unauthorized" in error_message.lower():
            await self.token_service.mark_needs_reauth(user_id, "401_unauthorized")
        elif "credentials not found" in error_message.lower():
            pass  # Don't update status for missing credentials
        else:
            # Mark as error for other failures
            try:
                await self.supabase.table("integration_canvas").update({
                    "status": "error",
                    "last_error_code": "delta_sync_failed",
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).execute()
            except Exception:
                pass

        logger.error(f"Canvas delta sync failed for user {user_id}: {error_message}")

        return {
            "user_id": user_id,
            "started_at": start_time.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "execution_time": execution_time,
            "status": "failed",
            "error": error_message,
            "courses_checked": 0,
            "assignments_updated": 0,
            "assignments_created": 0,
            "assignments_deleted": 0,
            "errors": [error_message]
        }


# Global job instance
_delta_sync_job: Optional[CanvasDeltaSyncJob] = None

def get_canvas_delta_sync_job() -> CanvasDeltaSyncJob:
    """Get global Canvas delta sync job instance"""
    global _delta_sync_job
    if _delta_sync_job is None:
        _delta_sync_job = CanvasDeltaSyncJob()
    return _delta_sync_job


# Convenience function for external use
async def execute_canvas_delta_sync(user_id: str) -> Dict[str, Any]:
    """Execute Canvas delta sync for a user"""
    job = get_canvas_delta_sync_job()
    return await job.execute_delta_sync(user_id)