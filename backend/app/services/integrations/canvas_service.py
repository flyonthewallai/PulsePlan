"""
Canvas LMS integration service for syncing assignments and courses
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

try:
    import httpx
except ImportError:
    httpx = None

from app.database.repositories.task_repositories import (
    TaskRepository,
    get_task_repository
)
from app.database.repositories.integration_repositories import (
    CanvasIntegrationRepository,
    get_canvas_integration_repository
)
from app.services.infrastructure.cache_service import get_cache_service
from app.services.auth.token_service import get_token_service
from app.config.core.settings import get_settings

logger = logging.getLogger(__name__)


class CanvasService:
    """Service for Canvas LMS integration and assignment synchronization"""
    
    def __init__(
        self,
        task_repository: Optional[TaskRepository] = None,
        canvas_integration_repository: Optional[CanvasIntegrationRepository] = None
    ):
        self.settings = get_settings()
        self._task_repository = task_repository
        self._canvas_integration_repository = canvas_integration_repository
        self.cache_service = get_cache_service()
        self.token_service = get_token_service()
    
    @property
    def task_repository(self) -> TaskRepository:
        """Lazy-load task repository"""
        if self._task_repository is None:
            self._task_repository = get_task_repository()
        return self._task_repository
    
    @property
    def canvas_integration_repository(self) -> CanvasIntegrationRepository:
        """Lazy-load canvas integration repository"""
        if self._canvas_integration_repository is None:
            self._canvas_integration_repository = get_canvas_integration_repository()
        return self._canvas_integration_repository
    
    async def sync_user_assignments(
        self,
        user_id: str,
        canvas_api_key: str,
        canvas_url: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Sync Canvas assignments for a user"""
        if not httpx:
            raise ImportError("httpx library required for Canvas integration")
        
        try:
            # Check cache first
            if not force_refresh:
                cached_assignments = await self.cache_service.get(f"canvas:assignments:{user_id}")
                if cached_assignments:
                    return {
                        "user_id": user_id,
                        "assignments_count": len(cached_assignments),
                        "cached": True,
                        "sync_timestamp": datetime.utcnow().isoformat()
                    }
            
            # Get courses first
            courses = await self._get_user_courses(canvas_api_key, canvas_url)
            
            # Get assignments from all courses
            all_assignments = []
            for course in courses:
                course_assignments = await self._get_course_assignments(
                    canvas_api_key, 
                    canvas_url, 
                    course['id']
                )
                
                # Add course context to assignments
                for assignment in course_assignments:
                    assignment['course_name'] = course['name']
                    assignment['course_code'] = course.get('course_code', '')
                    
                all_assignments.extend(course_assignments)
            
            # Process and store assignments
            processed_assignments = []
            for assignment in all_assignments:
                processed_assignment = await self._process_assignment(user_id, assignment)
                if processed_assignment:
                    processed_assignments.append(processed_assignment)
            
            # Store assignments in database
            if processed_assignments:
                await self._store_assignments(user_id, processed_assignments)
            
            # Update Canvas integration status
            await self._update_integration_status(user_id, len(processed_assignments))
            
            # Cache results
            await self.cache_service.set(
                f"canvas:assignments:{user_id}", 
                processed_assignments, 
                900  # 15 minutes
            )
            
            logger.info(f"Synced {len(processed_assignments)} Canvas assignments for user {user_id}")
            
            return {
                "user_id": user_id,
                "assignments_count": len(processed_assignments),
                "courses_count": len(courses),
                "cached": False,
                "sync_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Canvas sync failed for user {user_id}: {e}")
            raise
    
    async def _get_user_courses(self, api_key: str, canvas_url: str) -> List[Dict[str, Any]]:
        """Get user's Canvas courses"""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            url = f"{canvas_url}/api/v1/courses"
            params = {
                "enrollment_type": "student",
                "enrollment_state": "active",
                "state": ["available", "completed"],
                "include": ["term"],
                "per_page": 100
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                courses = response.json()
            
            # Filter out concluded courses older than 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            active_courses = []
            
            for course in courses:
                # Include current courses and recently concluded courses
                workflow_state = course.get('workflow_state', '')
                if workflow_state in ['available', 'completed']:
                    # Check if course ended recently for completed courses
                    if workflow_state == 'completed':
                        term = course.get('term', {})
                        end_at = term.get('end_at')
                        if end_at:
                            try:
                                end_date = datetime.fromisoformat(end_at.replace('Z', '+00:00'))
                                if end_date < six_months_ago:
                                    continue  # Skip old completed courses
                            except:
                                pass  # Keep course if date parsing fails
                    
                    active_courses.append(course)
            
            logger.info(f"Found {len(active_courses)} active Canvas courses")
            return active_courses
            
        except Exception as e:
            logger.error(f"Error fetching Canvas courses: {e}")
            raise
    
    async def _get_course_assignments(
        self, 
        api_key: str, 
        canvas_url: str, 
        course_id: str
    ) -> List[Dict[str, Any]]:
        """Get assignments for a specific course"""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            url = f"{canvas_url}/api/v1/courses/{course_id}/assignments"
            params = {
                "include": ["submission"],
                "per_page": 100,
                "order_by": "due_at",
                "bucket": ["upcoming", "overdue", "undated", "past"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                assignments = response.json()
            
            # Filter assignments (only include those that are published and have due dates or are recent)
            filtered_assignments = []
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            
            for assignment in assignments:
                # Only include published assignments
                if not assignment.get('published', False):
                    continue
                
                # Include assignments with due dates or recent assignments without due dates
                due_at = assignment.get('due_at')
                created_at = assignment.get('created_at')
                
                if due_at or (created_at and datetime.fromisoformat(created_at.replace('Z', '+00:00')) > one_month_ago):
                    filtered_assignments.append(assignment)
            
            return filtered_assignments
            
        except Exception as e:
            logger.error(f"Error fetching assignments for course {course_id}: {e}")
            return []
    
    async def _process_assignment(self, user_id: str, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a Canvas assignment into standardized format"""
        try:
            # Extract due date
            due_at = assignment.get('due_at')
            due_date = None
            if due_at:
                try:
                    due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00')).isoformat()
                except:
                    pass
            
            # Determine assignment type
            assignment_type = "assignment"
            submission_types = assignment.get('submission_types', [])
            if 'online_quiz' in submission_types:
                assignment_type = "quiz"
            elif 'discussion_topic' in submission_types:
                assignment_type = "discussion"
            
            # Extract submission status
            submission = assignment.get('submission', {})
            submission_status = submission.get('workflow_state', 'unsubmitted') if submission else 'unsubmitted'
            
            # Calculate estimated time (basic heuristic based on points)
            points_possible = assignment.get('points_possible', 0)
            estimated_minutes = max(30, min(180, int(points_possible * 2))) if points_possible else 60
            
            return {
                "canvas_id": assignment['id'],
                "course_id": assignment.get('course_id'),
                "name": assignment.get('name', 'Untitled Assignment'),
                "description": assignment.get('description', ''),
                "due_at": due_date,
                "points_possible": points_possible,
                "submission_types": submission_types,
                "assignment_type": assignment_type,
                "html_url": assignment.get('html_url', ''),
                "submission_status": submission_status,
                "submitted_at": submission.get('submitted_at'),
                "grade": submission.get('score'),
                "graded_at": submission.get('graded_at'),
                "course_name": assignment.get('course_name', ''),
                "course_code": assignment.get('course_code', ''),
                "estimated_minutes": estimated_minutes,
                "created_at": assignment.get('created_at'),
                "updated_at": assignment.get('updated_at'),
                "synced_at": datetime.utcnow().isoformat(),
                "is_published": assignment.get('published', False),
                "unlock_at": assignment.get('unlock_at'),
                "lock_at": assignment.get('lock_at')
            }
            
        except Exception as e:
            logger.error(f"Error processing Canvas assignment {assignment.get('id')}: {e}")
            return None
    
    async def _store_assignments(self, user_id: str, assignments: List[Dict[str, Any]]):
        """Store Canvas assignments in consolidated tasks table"""
        try:
            # Clear existing Canvas assignments for this user from consolidated tasks table
            # TODO: Add delete_by_filters to TaskRepository
            from app.config.database.supabase import get_supabase_client
            supabase = get_supabase_client()
            await supabase.table("tasks").delete().eq("user_id", user_id).eq("source", "canvas").execute()

            # Convert assignments to consolidated tasks format
            task_records = []
            for assignment in assignments:
                task_record = {
                    "user_id": user_id,
                    "title": assignment["name"],
                    "task_type": "assignment",
                    "source": "canvas",
                    "canvas_id": assignment["canvas_id"],
                    "canvas_course_id": assignment.get("course_id"),
                    "due_date": assignment.get("due_at"),
                    "html_url": assignment.get("html_url"),
                    "submission_type": assignment.get("submission_type"),
                    "description": assignment.get("description"),
                    "canvas_points": assignment.get("points_possible"),
                    "created_at": assignment.get("created_at")
                }
                task_records.append(task_record)

            # Insert new assignments as tasks
            if task_records:
                # Insert in batches to avoid payload size limits
                batch_size = 100
                for i in range(0, len(task_records), batch_size):
                    batch = task_records[i:i + batch_size]
                    # Use repository to insert tasks
                    await self.task_repository.bulk_create(batch)

        except Exception as e:
            logger.error(f"Error storing Canvas assignments for user {user_id}: {e}")
            raise
    
    async def _update_integration_status(self, user_id: str, assignment_count: int):
        """Update Canvas integration status in database"""
        try:
            integration_data = {
                "user_id": user_id,
                "is_active": True,
                "last_sync": datetime.utcnow().isoformat(),
                "assignments_synced": assignment_count,
                "sync_source": "api",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert integration status
            await self.canvas_integration_repository.upsert_integration(integration_data)
            
        except Exception as e:
            logger.error(f"Error updating Canvas integration status for user {user_id}: {e}")
    
    async def get_user_assignments(
        self,
        user_id: str,
        include_completed: bool = False,
        days_ahead: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get Canvas assignments for user with optional filtering"""
        try:
            # Use task repository with filters
            # TODO: Add complex query support to TaskRepository for these filters
            from app.config.database.supabase import get_supabase_client
            supabase = get_supabase_client()
            query = supabase.table("tasks").select("*").eq("user_id", user_id).eq("source", "canvas").eq("task_type", "assignment")
            
            if not include_completed:
                query = query.neq("submission_status", "graded")
            
            if days_ahead:
                future_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
                query = query.lte("due_at", future_date)
            
            # Only include assignments that are not too old
            one_month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            query = query.or_(f"due_at.gte.{one_month_ago},due_at.is.null")
            
            response = await query.order("due_at", desc=False, nullsfirst=False).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting Canvas assignments for user {user_id}: {e}")
            return []
    
    async def get_integration_status(self, user_id: str) -> Dict[str, Any]:
        """Get Canvas integration status for user"""
        try:
            response = await self.canvas_integration_repository.get_by_user(user_id)
            
            if response:
                return response
            else:
                return {
                    "user_id": user_id,
                    "is_active": False,
                    "last_sync": None,
                    "assignments_synced": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting Canvas integration status for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "is_active": False,
                "last_sync": None,
                "assignments_synced": 0,
                "error": str(e)
            }
    
    async def create_connection_code(self, user_id: str) -> str:
        """Create a temporary connection code for Canvas extension"""
        import secrets
        import string
        
        # Generate 8-character alphanumeric code
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        # Store code with expiration (valid for 10 minutes)
        expiry = datetime.utcnow() + timedelta(minutes=10)
        
        try:
            connection_data = {
                "user_id": user_id,
                "connection_code": code,
                "connection_code_expiry": expiry.isoformat(),
                "is_active": False,  # Will be activated when extension connects
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.canvas_integration_repository.upsert_integration(connection_data)
            
            return code
            
        except Exception as e:
            logger.error(f"Error creating Canvas connection code for user {user_id}: {e}")
            raise
    
    async def activate_connection(self, connection_code: str, canvas_data: Dict[str, Any]) -> bool:
        """Activate Canvas connection using connection code"""
        try:
            # Find user by connection code
            # TODO: Add get_by_connection_code to CanvasIntegrationRepository
            from app.config.database.supabase import get_supabase_client
            supabase = get_supabase_client()
            response = await supabase.table("canvas_integrations").select("*").eq(
                "connection_code", connection_code
            ).single().execute()
            
            if not response.data:
                return False
            
            integration = response.data
            user_id = integration["user_id"]
            
            # Check if code is still valid
            expiry = datetime.fromisoformat(integration["connection_code_expiry"])
            if datetime.utcnow() > expiry:
                return False
            
            # Update integration with Canvas data
            update_data = {
                "is_active": True,
                "canvas_url": canvas_data.get("canvas_url"),
                "canvas_user_id": canvas_data.get("user_id"),
                "canvas_user_name": canvas_data.get("user_name"),
                "extension_version": canvas_data.get("extension_version"),
                "connected_at": datetime.utcnow().isoformat(),
                "connection_code": None,  # Clear the code
                "connection_code_expiry": None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.canvas_integration_repository.upsert_integration({**update_data, "user_id": user_id})
            
            logger.info(f"Canvas integration activated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating Canvas connection with code {connection_code}: {e}")
            return False


# Global Canvas service instance
_canvas_service: Optional[CanvasService] = None

def get_canvas_service() -> CanvasService:
    """Get global Canvas service instance"""
    global _canvas_service
    if _canvas_service is None:
        _canvas_service = CanvasService()
    return _canvas_service