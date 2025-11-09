"""
Canvas initial backfill job - idempotent and resilient
Handles the first-time sync of Canvas assignments and courses
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import math

try:
    import httpx
except ImportError:
    httpx = None

from app.config.database.supabase import get_supabase_client
from app.services.integrations.canvas_token_service import get_canvas_token_service
from app.database.models import (
    TaskModel, ExternalSource, ExternalCursorModel, AssignmentImportModel,
    CourseModel, STANDARD_COURSE_COLORS
)
from app.config.core.settings import get_settings

logger = logging.getLogger(__name__)


class CanvasBackfillJob:
    """Initial Canvas backfill job with resilience and idempotency"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.token_service = get_canvas_token_service()
        self.settings = get_settings()

    async def _get_or_create_course(
        self,
        user_id: str,
        canvas_course: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get or create a course record for a Canvas course

        Args:
            user_id: User ID
            canvas_course: Canvas course data

        Returns:
            Course ID if successful, None if failed
        """
        try:
            canvas_id = canvas_course.get("id")
            if not canvas_id:
                logger.warning(f"Canvas course missing ID: {canvas_course}")
                return None

            # Try to find existing course
            response = self.supabase.table("courses").select("*").eq(
                "user_id", user_id
            ).eq("canvas_id", canvas_id).eq("external_source", "canvas").execute()

            if response.data:
                course_id = response.data[0]["id"]
                logger.debug(f"Found existing course {course_id} for Canvas course {canvas_id}")
                return course_id

            # Get existing course colors for this user
            existing_response = self.supabase.table("courses").select("color").eq(
                "user_id", user_id
            ).execute()

            existing_colors = [c["color"] for c in existing_response.data] if existing_response.data else []

            # Get next available color
            color = CourseModel.get_next_color(existing_colors)

            # Create new course
            course = CourseModel.from_canvas_course(user_id, canvas_course, color)
            course_dict = course.to_supabase_insert()

            insert_response = self.supabase.table("courses").insert(course_dict).execute()

            if insert_response.data:
                course_id = insert_response.data[0]["id"]
                logger.info(f"Created new course {course_id} for Canvas course '{canvas_course.get('name')}' with color {color}")
                return course_id
            else:
                logger.error(f"Failed to insert course: {insert_response}")
                return None

        except Exception as e:
            logger.error(f"Error getting/creating course for Canvas course {canvas_course.get('id', 'unknown')}: {e}")
            return None

    async def execute_backfill(
        self,
        user_id: str,
        force_restart: bool = False
    ) -> Dict[str, Any]:
        """
        Execute initial Canvas backfill

        Args:
            user_id: User ID to backfill
            force_restart: Force restart from beginning

        Returns:
            Dict with backfill results
        """
        if not httpx:
            raise ImportError("httpx library required for Canvas integration")

        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting Canvas backfill for user {user_id}")

            # Get Canvas credentials
            token_data = await self.token_service.retrieve_canvas_token(user_id)
            if not token_data:
                raise ValueError("Canvas credentials not found or invalid")

            api_token = token_data["api_token"]
            base_url = token_data["base_url"]

            # Check if backfill already completed (unless force restart)
            if not force_restart:
                existing_sync = await self._get_last_full_sync(user_id)
                if existing_sync and existing_sync.get("completed"):
                    logger.info(f"Backfill already completed for user {user_id}")
                    return {
                        "user_id": user_id,
                        "status": "already_completed",
                        "last_sync": existing_sync,
                        "execution_time": 0
                    }

            # Initialize progress tracking
            progress = await self._init_backfill_progress(user_id, force_restart)

            results = {
                "user_id": user_id,
                "started_at": start_time.isoformat(),
                "courses_processed": 0,
                "assignments_imported": 0,
                "assignments_upserted": 0,
                "errors": [],
                "status": "in_progress"
            }

            # Step 1: Fetch and process courses
            courses_result = await self._fetch_and_store_courses(
                user_id, api_token, base_url, progress
            )
            results["courses_processed"] = courses_result["count"]
            results["errors"].extend(courses_result["errors"])

            # Step 2: Fetch assignments for each course
            assignments_result = await self._fetch_assignments_by_course(
                user_id, api_token, base_url, courses_result["courses"], progress
            )
            results["assignments_imported"] = assignments_result["imported"]
            results["errors"].extend(assignments_result["errors"])

            # Step 3: Process assignments into tasks
            processing_result = await self._process_assignments_to_tasks(user_id, progress)
            results["assignments_upserted"] = processing_result["upserted"]
            results["errors"].extend(processing_result["errors"])

            # Mark backfill as completed
            await self._mark_backfill_completed(user_id, results)

            # Update integration status
            await self._update_integration_status(
                user_id,
                results["assignments_upserted"]
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["completed_at"] = datetime.utcnow().isoformat()
            results["execution_time"] = execution_time
            results["status"] = "completed"

            logger.info(
                f"Canvas backfill completed for user {user_id} in {execution_time:.2f}s. "
                f"Processed {results['courses_processed']} courses, "
                f"imported {results['assignments_imported']} assignments, "
                f"upserted {results['assignments_upserted']} tasks"
            )

            return results

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Canvas backfill failed for user {user_id}: {e}")

            # Mark integration as needing attention
            if "401" in str(e) or "unauthorized" in str(e).lower():
                await self.token_service.mark_needs_reauth(user_id, "401_unauthorized")

            return {
                "user_id": user_id,
                "started_at": start_time.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time": execution_time,
                "status": "failed",
                "error": str(e),
                "courses_processed": 0,
                "assignments_imported": 0,
                "assignments_upserted": 0,
                "errors": [str(e)]
            }

    async def _get_last_full_sync(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the last full sync status from oauth_tokens metadata"""
        try:
            # TODO: Store metadata in a separate table
            # For now, always return None to trigger fresh sync
            return None

        except Exception as e:
            logger.warning(f"Could not get last sync for user {user_id}: {e}")
            return None

    async def _init_backfill_progress(
        self,
        user_id: str,
        force_restart: bool = False
    ) -> Dict[str, Any]:
        """Initialize or resume backfill progress"""
        try:
            # Check for existing progress
            if not force_restart:
                response = self.supabase.table("external_cursor").select("*").eq(
                    "user_id", user_id
                ).eq("source", "canvas").execute()

                if response.data:
                    # Resume from existing progress
                    cursors = {item["cursor_type"]: item["cursor_value"] for item in response.data}
                    logger.info(f"Resuming backfill for user {user_id} from existing cursors")
                    return {"cursors": cursors, "mode": "resume"}

            # Start fresh backfill
            if force_restart:
                # Clear existing progress
                self.supabase.table("external_cursor").delete().eq(
                    "user_id", user_id
                ).eq("source", "canvas").execute()

                # Clear staging data
                self.supabase.table("assignment_import").delete().eq(
                    "user_id", user_id
                ).execute()

            logger.info(f"Starting fresh backfill for user {user_id}")
            return {"cursors": {}, "mode": "fresh"}

        except Exception as e:
            logger.warning(f"Error initializing backfill progress for user {user_id}: {e}")
            return {"cursors": {}, "mode": "fresh"}

    async def _fetch_and_store_courses(
        self,
        user_id: str,
        api_token: str,
        base_url: str,
        progress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch and store user's Canvas courses"""
        try:
            headers = {"Authorization": f"Bearer {api_token}"}
            url = f"{base_url}/api/v1/courses"
            params = {
                "enrollment_type": "student",
                "enrollment_state": "active",
                "include": ["term"],
                "per_page": 100
            }

            courses = []
            page = 1
            errors = []

            while True:
                try:
                    params["page"] = page
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, headers=headers, params=params, timeout=30)

                    if response.status_code == 401:
                        await self.token_service.mark_needs_reauth(user_id, "401_unauthorized")
                        raise ValueError("Canvas token is invalid (401)")

                    response.raise_for_status()
                    page_courses = response.json()

                    if not page_courses:
                        break

                    courses.extend(page_courses)
                    page += 1

                    # Set cursor after each successful page
                    await self._set_cursor(user_id, "courses", f"page_{page}")

                except Exception as e:
                    logger.error(f"Error fetching courses page {page} for user {user_id}: {e}")
                    errors.append(f"Course page {page}: {str(e)}")
                    break

            # Filter courses (active and recently completed only)
            filtered_courses = await self._filter_courses(courses)

            # Store courses (this is idempotent)
            await self._store_courses(user_id, filtered_courses)

            logger.info(f"Fetched {len(courses)} total courses, filtered to {len(filtered_courses)} active courses")

            return {
                "count": len(filtered_courses),
                "courses": filtered_courses,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Error fetching courses for user {user_id}: {e}")
            return {"count": 0, "courses": [], "errors": [str(e)]}

    async def _fetch_assignments_by_course(
        self,
        user_id: str,
        api_token: str,
        base_url: str,
        courses: List[Dict[str, Any]],
        progress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch assignments for each course with progress tracking"""
        total_imported = 0
        errors = []

        # Get resume point if any
        processed_courses = progress.get("cursors", {}).get("assignments_course_progress", "")
        processed_course_ids = set(processed_courses.split(",")) if processed_courses else set()

        for course in courses:
            course_id = str(course["id"])

            # Skip already processed courses (idempotency)
            if course_id in processed_course_ids:
                logger.debug(f"Skipping already processed course {course_id}")
                continue

            try:
                course_assignments = await self._fetch_course_assignments(
                    api_token, base_url, course_id
                )

                logger.info(f"Fetched {len(course_assignments)} assignments from course {course_id}")

                # Store in staging table with raw payloads
                imported = await self._store_assignments_staging(
                    user_id, course_id, course, course_assignments
                )
                total_imported += imported

                # Update progress cursor
                processed_course_ids.add(course_id)
                await self._set_cursor(
                    user_id,
                    "assignments_course_progress",
                    ",".join(processed_course_ids)
                )

                logger.info(
                    f"Imported {imported} assignments from course {course_id} for user {user_id}"
                )

            except Exception as e:
                logger.error(f"Error processing course {course_id} for user {user_id}: {e}")
                errors.append(f"Course {course_id}: {str(e)}")
                continue

        return {
            "imported": total_imported,
            "errors": errors
        }

    async def _fetch_course_assignments(
        self,
        api_token: str,
        base_url: str,
        course_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all assignments for a course with pagination"""
        headers = {"Authorization": f"Bearer {api_token}"}
        url = f"{base_url}/api/v1/courses/{course_id}/assignments"
        params = {
            "include": ["submission"],
            "per_page": 100,
            "order_by": "due_at"
            # Removed bucket filtering to get ALL assignments including future ones
        }

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

            # Filter published assignments only
            published_assignments = [
                assignment for assignment in page_assignments
                if assignment.get("published", False)
            ]

            assignments.extend(published_assignments)
            page += 1

        return assignments

    async def _store_assignments_staging(
        self,
        user_id: str,
        course_id: str,
        course: Dict[str, Any],
        assignments: List[Dict[str, Any]]
    ) -> int:
        """Store assignments in staging table with idempotency"""
        if not assignments:
            return 0

        course_name = course.get("name", f"Course {course_id}")
        course_code = course.get("course_code", "")

        staging_records = []
        for assignment in assignments:
            # Add course context to assignment
            assignment["course_name"] = course_name
            assignment["course_code"] = course_code

            staging_record = AssignmentImportModel(
                user_id=user_id,
                canvas_id=str(assignment["id"]),
                course_id=course_id,
                raw_payload=assignment,
                processed=False,
                created_at=datetime.utcnow()
            )
            staging_records.append(staging_record.to_supabase_insert())

        # Use upsert for idempotency (on conflict: user_id, canvas_id)
        try:
            batch_size = 50
            total_inserted = 0

            for i in range(0, len(staging_records), batch_size):
                batch = staging_records[i:i + batch_size]
                self.supabase.table("assignment_import").upsert(
                    batch,
                    on_conflict="user_id,canvas_id"
                ).execute()
                total_inserted += len(batch)

            return total_inserted

        except Exception as e:
            logger.error(f"Error storing assignments staging for course {course_id}: {e}")
            return 0

    async def _process_assignments_to_tasks(
        self,
        user_id: str,
        progress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process staged assignments into tasks table"""
        try:
            # Get unprocessed assignments from staging
            response = self.supabase.table("assignment_import").select("*").eq(
                "user_id", user_id
            ).eq("processed", False).execute()

            staging_assignments = response.data or []
            if not staging_assignments:
                return {"upserted": 0, "errors": []}

            task_records = []
            processed_ids = []
            errors = []

            # Cache for course IDs to avoid repeated lookups
            course_cache = {}

            for staging_assignment in staging_assignments:
                try:
                    assignment_data = staging_assignment["raw_payload"]
                    canvas_id = staging_assignment["canvas_id"]
                    assignment_name = assignment_data.get("name", "Unknown")

                    # Get or create course for this assignment
                    course_id = None
                    canvas_course_id = assignment_data.get("course_id")
                    if canvas_course_id:
                        if canvas_course_id in course_cache:
                            course_id = course_cache[canvas_course_id]
                        else:
                            # Create Canvas course data from assignment
                            canvas_course = {
                                "id": canvas_course_id,
                                "name": assignment_data.get("course_name", f"Course {canvas_course_id}"),
                                "course_code": assignment_data.get("course_code", "")
                            }
                            course_id = await self._get_or_create_course(user_id, canvas_course)
                            if course_id:
                                course_cache[canvas_course_id] = course_id

                    # Convert to TaskModel with course_id
                    task = await self._convert_assignment_to_task(user_id, assignment_data, course_id)
                    if task:
                        logger.debug(f"Successfully converted assignment '{assignment_name}' (ID: {canvas_id})")
                        task_records.append(task.to_supabase_insert())
                        processed_ids.append(staging_assignment["id"])
                    else:
                        logger.warning(f"Task conversion returned None for assignment '{assignment_name}' (ID: {canvas_id}) - likely filtered out by date")

                except Exception as e:
                    logger.error(f"Error converting assignment '{assignment_name}' (ID: {canvas_id}): {e}")
                    errors.append(f"Assignment {canvas_id}: {str(e)}")

            # Upsert tasks with UNIQUE constraint on (user_id, external_source, external_id)
            upserted_count = 0
            if task_records:
                logger.info(f"Attempting to upsert {len(task_records)} tasks to database")
                batch_size = 50
                for i in range(0, len(task_records), batch_size):
                    batch = task_records[i:i + batch_size]
                    # Normalize keys across batch to satisfy PostgREST 'All object keys must match'
                    try:
                        all_keys = set()
                        for obj in batch:
                            all_keys.update(obj.keys())
                        normalized_batch = []
                        for obj in batch:
                            normalized_obj = {key: obj.get(key, None) for key in all_keys}
                            normalized_batch.append(normalized_obj)
                        batch = normalized_batch
                    except Exception:
                        pass
                    try:
                        logger.debug(f"Upserting batch {i//batch_size + 1}: {len(batch)} tasks")
                        # Log first task in batch for debugging
                        if batch:
                            sample_task = batch[0]
                            logger.debug(f"Sample task: {sample_task.get('title')} (Canvas ID: {sample_task.get('canvas_id')})")

                        result = self.supabase.table("tasks").upsert(
                            batch,
                            on_conflict="user_id,external_source,external_id"
                        ).execute()

                        logger.info(f"Successfully upserted batch: {len(batch)} tasks")
                        upserted_count += len(batch)
                    except Exception as e:
                        logger.error(f"Error upserting task batch {i//batch_size + 1}: {e}")
                        logger.error(f"Failed batch sample: {batch[0] if batch else 'No tasks in batch'}")
                        errors.append(f"Task batch upsert: {str(e)}")

            # Mark staging assignments as processed
            if processed_ids:
                self.supabase.table("assignment_import").update({
                    "processed": True,
                    "processed_at": datetime.utcnow().isoformat()
                }).in_("id", processed_ids).execute()

            return {
                "upserted": upserted_count,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Error processing assignments to tasks for user {user_id}: {e}")
            return {"upserted": 0, "errors": [str(e)]}

    async def _convert_assignment_to_task(
        self,
        user_id: str,
        assignment_data: Dict[str, Any],
        course_id: Optional[str] = None
    ) -> Optional[TaskModel]:
        """Convert Canvas assignment to TaskModel"""
        try:
            # Extract due date
            due_at = assignment_data.get("due_at")
            due_date = None
            if due_at:
                try:
                    due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Skip past assignments (only import current and future assignments)
            from datetime import timezone
            current_date = datetime.utcnow().replace(tzinfo=timezone.utc)
            if due_date and due_date < current_date:
                logger.debug(f"Skipping past assignment '{assignment_data.get('name')}' due {due_date}")
                return None
            elif due_date and due_date >= current_date:
                logger.info(f"Including future assignment '{assignment_data.get('name')}' due {due_date}")
            elif not due_date:
                logger.debug(f"Including undated assignment '{assignment_data.get('name')}'")
                # Don't filter out assignments without due dates

            # Calculate estimated time based on points
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
            external_updated_at = None
            updated_at_str = assignment_data.get("updated_at")
            if updated_at_str:
                try:
                    external_updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Build task with all Canvas-specific fields
            task_data = {
                "user_id": user_id,
                "title": assignment_data.get("name", "Untitled Assignment"),
                "description": assignment_data.get("description", ""),
                "task_type": task_type,
                "course_id": course_id,  # Link to courses table
                # schema uses 'course' (text) not 'subject'
                "course": assignment_data.get("course_name", ""),
                "due_date": due_date,
                "estimated_minutes": estimated_minutes,

                # External source tracking (legacy fields)
                "external_source": "canvas",
                "external_id": str(assignment_data["id"]),
                "external_course_id": str(assignment_data.get("course_id", "")),
                "external_updated_at": external_updated_at,

                # Canvas-specific fields
                "canvas_id": assignment_data["id"],
                "canvas_course_id": assignment_data.get("course_id"),
                "canvas_points": assignment_data.get("points_possible"),
                "canvas_max_points": assignment_data.get("points_possible"),
                "submission_type": ",".join(submission_types) if submission_types else None,
                "html_url": assignment_data.get("html_url"),

                # Sync metadata
                "source": "canvas",
                "sync_source": "canvas",
                "last_synced_at": datetime.utcnow(),

                # Standard timestamps
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Create TaskModel with all fields
            return TaskModel(**{k: v for k, v in task_data.items() if v is not None})

        except Exception as e:
            logger.error(f"Error converting assignment {assignment_data.get('id')}: {e}")
            return None

    async def _filter_courses(self, courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter courses to include only active and recently completed"""
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        filtered_courses = []

        logger.info(f"Filtering {len(courses)} courses...")

        for course in courses:
            course_id = course.get("id")
            course_name = course.get("name", "Unnamed Course")
            workflow_state = course.get("workflow_state", "")

            logger.debug(f"Course {course_id} '{course_name}': state={workflow_state}")

            if workflow_state not in ["available", "completed"]:
                logger.debug(f"Skipping course {course_id} - invalid state: {workflow_state}")
                continue

            # For completed courses, check if they ended recently
            if workflow_state == "completed":
                term = course.get("term", {})
                end_at = term.get("end_at")
                if end_at:
                    try:
                        end_date = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
                        if end_date < six_months_ago:
                            logger.debug(f"Skipping old completed course {course_id} - ended {end_date}")
                            continue
                    except Exception:
                        pass

            filtered_courses.append(course)
            logger.debug(f"Including course {course_id} '{course_name}'")

        logger.info(f"Filtered to {len(filtered_courses)} active courses")
        return filtered_courses

    async def _store_courses(self, user_id: str, courses: List[Dict[str, Any]]):
        """Store courses in database (idempotent)"""
        # This is a simplified implementation
        # In production, you might want a separate courses table
        pass

    async def _set_cursor(self, user_id: str, cursor_type: str, cursor_value: str):
        """Set external cursor for progress tracking"""
        try:
            # Align with schema.sql: external_cursor has updated_at only (no created_at)
            cursor_record = {
                "user_id": user_id,
                "source": "canvas",
                "cursor_type": cursor_type,
                "cursor_value": cursor_value,
                "updated_at": datetime.utcnow().isoformat(),
            }

            self.supabase.table("external_cursor").upsert(
                cursor_record,
                on_conflict="user_id,source,cursor_type"
            ).execute()

        except Exception as e:
            logger.error(f"Error setting cursor {cursor_type} for user {user_id}: {e}")

    async def _mark_backfill_completed(self, user_id: str, results: Dict[str, Any]):
        """Mark backfill as completed in oauth_tokens metadata"""
        try:
            # TODO: Store metadata in a separate table or add metadata column to oauth_tokens
            # For now, just update the updated_at timestamp
            self.supabase.table("oauth_tokens").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).eq("provider", "canvas").execute()

        except Exception as e:
            logger.error(f"Error marking backfill completed for user {user_id}: {e}")

    async def _update_integration_status(self, user_id: str, assignments_count: int):
        """Update integration status in oauth_tokens"""
        try:
            # TODO: Store metadata in a separate table or add metadata column to oauth_tokens
            # For now, just mark as active
            self.supabase.table("oauth_tokens").update({
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).eq("provider", "canvas").execute()

        except Exception as e:
            logger.error(f"Error updating integration status for user {user_id}: {e}")


# Global job instance
_backfill_job: Optional[CanvasBackfillJob] = None

def get_canvas_backfill_job() -> CanvasBackfillJob:
    """Get global Canvas backfill job instance"""
    global _backfill_job
    if _backfill_job is None:
        _backfill_job = CanvasBackfillJob()
    return _backfill_job


# Convenience function for external use
async def execute_canvas_backfill(user_id: str, force_restart: bool = False) -> Dict[str, Any]:
    """Execute Canvas backfill for a user"""
    job = get_canvas_backfill_job()
    return await job.execute_backfill(user_id, force_restart)