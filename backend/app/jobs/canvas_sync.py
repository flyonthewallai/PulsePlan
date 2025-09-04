"""
Canvas LMS sync job for PulsePlan.
Handles automated syncing of assignments, courses, and student data.

This is a callable canvas sync tool that can be invoked when users request Canvas sync.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

try:
    import httpx
except ImportError:
    httpx = None

from app.config.supabase import get_supabase_client
from app.services.cache_service import get_cache_service
from app.services.token_service import get_token_service
from app.config.settings import get_settings
from app.memory import get_ingestion_service
from app.memory.types import Assignment

logger = logging.getLogger(__name__)


class CanvasSync:
    """Canvas LMS sync job for automated data synchronization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.cache_service = get_cache_service()
        self.token_service = get_token_service()
        self.ingestion_service = get_ingestion_service()
    
    async def sync_user_canvas_data(
        self,
        user_id: str,
        canvas_api_key: str = None,
        canvas_url: str = None,
        force_refresh: bool = False,
        include_grades: bool = False
    ) -> Dict[str, Any]:
        """
        Sync Canvas data for a user - callable sync tool
        
        Args:
            user_id: User ID to sync data for
            canvas_api_key: Canvas API key (optional if stored)
            canvas_url: Canvas URL (optional if stored)
            force_refresh: Force refresh from Canvas API
            include_grades: Include grade synchronization
        
        Returns:
            Dict with sync results
        """
        if not httpx:
            raise ImportError("httpx library required for Canvas integration")
        
        try:
            start_time = datetime.utcnow()
            
            # Get Canvas credentials if not provided
            if not canvas_api_key or not canvas_url:
                credentials = await self._get_user_canvas_credentials(user_id)
                canvas_api_key = canvas_api_key or credentials.get("api_key")
                canvas_url = canvas_url or credentials.get("canvas_url")
            
            if not canvas_api_key or not canvas_url:
                raise ValueError("Canvas API credentials not found for user")
            
            # Check cache first unless force refresh
            if not force_refresh:
                cached_result = await self._get_cached_sync_result(user_id)
                if cached_result:
                    return cached_result
            
            sync_results = {
                "user_id": user_id,
                "sync_started_at": start_time.isoformat(),
                "operations": {},
                "totals": {
                    "courses": 0,
                    "assignments": 0,
                    "assignments_ingested": 0
                }
            }
            
            # Sync courses
            try:
                courses_result = await self._sync_user_courses(
                    user_id, canvas_api_key, canvas_url
                )
                sync_results["operations"]["courses"] = courses_result
                sync_results["totals"]["courses"] = courses_result.get("courses_count", 0)
            except Exception as e:
                logger.error(f"Course sync failed for user {user_id}: {e}")
                sync_results["operations"]["courses"] = {"error": str(e)}
            
            # Sync assignments and ingest into memory
            try:
                assignments_result = await self._sync_assignments_with_ingestion(
                    user_id, canvas_api_key, canvas_url
                )
                sync_results["operations"]["assignments"] = assignments_result
                sync_results["totals"]["assignments"] = assignments_result.get("assignments_count", 0)
                sync_results["totals"]["assignments_ingested"] = assignments_result.get("assignments_ingested", 0)
            except Exception as e:
                logger.error(f"Assignment sync failed for user {user_id}: {e}")
                sync_results["operations"]["assignments"] = {"error": str(e)}
            
            # Sync grades if requested
            if include_grades:
                try:
                    grades_result = await self._sync_user_grades(
                        user_id, canvas_api_key, canvas_url
                    )
                    sync_results["operations"]["grades"] = grades_result
                except Exception as e:
                    logger.error(f"Grade sync failed for user {user_id}: {e}")
                    sync_results["operations"]["grades"] = {"error": str(e)}
            
            # Update sync metadata
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            sync_results["sync_completed_at"] = datetime.utcnow().isoformat()
            sync_results["execution_time_seconds"] = execution_time
            sync_results["success"] = True
            
            # Update integration status
            await self._update_integration_status(
                user_id, 
                sync_results["totals"]["assignments"]
            )
            
            # Cache results for 15 minutes
            await self._cache_sync_result(user_id, sync_results)
            
            logger.info(f"Canvas sync completed for user {user_id} in {execution_time:.2f}s")
            return sync_results
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Canvas sync failed for user {user_id}: {e}")
            
            return {
                "user_id": user_id,
                "sync_started_at": start_time.isoformat(),
                "sync_completed_at": datetime.utcnow().isoformat(),
                "execution_time_seconds": execution_time,
                "success": False,
                "error": str(e),
                "operations": {},
                "totals": {"courses": 0, "assignments": 0, "assignments_ingested": 0}
            }
    
    async def get_upcoming_assignments(
        self,
        user_id: str,
        days_ahead: int = 14,
        canvas_api_key: str = None,
        canvas_url: str = None
    ) -> Dict[str, Any]:
        """Get upcoming assignments for a user"""
        try:
            # Get Canvas credentials if not provided
            if not canvas_api_key or not canvas_url:
                credentials = await self._get_user_canvas_credentials(user_id)
                canvas_api_key = canvas_api_key or credentials.get("api_key")
                canvas_url = canvas_url or credentials.get("canvas_url")
            
            if not canvas_api_key or not canvas_url:
                raise ValueError("Canvas API credentials not found for user")
            
            end_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            # Get user's courses
            courses = await self._get_user_courses(canvas_api_key, canvas_url)
            
            upcoming_assignments = []
            
            for course in courses:
                course_id = course.get("id")
                course_name = course.get("name", f"Course {course_id}")
                
                try:
                    assignments = await self._get_course_assignments(
                        canvas_api_key, canvas_url, course_id
                    )
                    
                    for assignment in assignments:
                        due_at_str = assignment.get("due_at")
                        if due_at_str:
                            try:
                                due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
                                if due_at <= end_date and due_at >= datetime.utcnow():
                                    upcoming_assignments.append({
                                        "id": str(assignment.get("id")),
                                        "title": assignment.get("name", "Untitled"),
                                        "course": course_name,
                                        "due_at": due_at.isoformat(),
                                        "points_possible": assignment.get("points_possible"),
                                        "html_url": assignment.get("html_url"),
                                        "description": assignment.get("description", "")[:200]
                                    })
                            except ValueError:
                                continue
                
                except Exception as e:
                    logger.warning(f"Failed to get assignments for course {course_id}: {e}")
                    continue
            
            # Sort by due date
            upcoming_assignments.sort(key=lambda x: x["due_at"])
            
            return {
                "user_id": user_id,
                "days_ahead": days_ahead,
                "assignments_count": len(upcoming_assignments),
                "assignments": upcoming_assignments,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get upcoming assignments for user {user_id}: {e}")
            raise
    
    async def _get_user_canvas_credentials(self, user_id: str) -> Dict[str, Any]:
        """Get Canvas credentials for user from database"""
        try:
            # Try to get from canvas_integrations table
            response = await self.supabase.table("canvas_integrations").select("*").eq(
                "user_id", user_id
            ).single().execute()
            
            if response.data and response.data.get("is_active"):
                return {
                    "api_key": response.data.get("canvas_api_key"),
                    "canvas_url": response.data.get("canvas_url")
                }
            
            # Try to get from token service
            canvas_token = await self.token_service.get_token(user_id, "canvas_api_token")
            if canvas_token:
                return {
                    "api_key": canvas_token.get("access_token"),
                    "canvas_url": canvas_token.get("canvas_url")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting Canvas credentials for user {user_id}: {e}")
            return {}
    
    async def _get_cached_sync_result(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached sync result if available"""
        try:
            cached_result = await self.cache_service.get(f"canvas:sync:{user_id}")
            return cached_result
        except Exception as e:
            logger.warning(f"Error getting cached sync result for user {user_id}: {e}")
            return None
    
    async def _cache_sync_result(self, user_id: str, result: Dict[str, Any]):
        """Cache sync result for 15 minutes"""
        try:
            await self.cache_service.set(
                f"canvas:sync:{user_id}", 
                result, 
                900  # 15 minutes
            )
        except Exception as e:
            logger.warning(f"Error caching sync result for user {user_id}: {e}")
    
    async def _sync_user_courses(
        self, 
        user_id: str, 
        canvas_api_key: str, 
        canvas_url: str
    ) -> Dict[str, Any]:
        """Sync user's Canvas courses"""
        try:
            courses = await self._get_user_courses(canvas_api_key, canvas_url)
            
            # Store courses in database
            if courses:
                await self._store_courses(user_id, courses)
            
            return {
                "operation": "sync_courses",
                "courses_count": len(courses),
                "courses": courses,
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Course sync failed for user {user_id}: {e}")
            raise
    
    async def _sync_assignments_with_ingestion(
        self,
        user_id: str,
        canvas_api_key: str,
        canvas_url: str
    ) -> Dict[str, Any]:
        """Sync assignments and ingest into memory system"""
        try:
            # Get user's courses
            courses = await self._get_user_courses(canvas_api_key, canvas_url)
            
            all_assignments = []
            assignments_ingested = 0
            
            # Get assignments for each course
            for course in courses:
                course_id = course.get("id")
                course_name = course.get("name", f"Course {course_id}")
                
                try:
                    course_assignments = await self._get_course_assignments(
                        canvas_api_key, canvas_url, course_id
                    )
                    
                    # Add course context and ingest into memory
                    for assignment_data in course_assignments:
                        assignment_data["course_name"] = course_name
                        assignment_data["course_code"] = course.get("course_code", "")
                        
                        # Parse assignment for memory ingestion
                        try:
                            assignment = self._parse_canvas_assignment(assignment_data, course_name)
                            memory_id = await self.ingestion_service.ingest_assignment(user_id, assignment)
                            
                            if memory_id:
                                assignment_data["memory_id"] = memory_id
                                assignments_ingested += 1
                        except Exception as e:
                            logger.warning(f"Failed to ingest assignment {assignment_data.get('id')}: {e}")
                        
                        all_assignments.append(assignment_data)
                
                except Exception as e:
                    logger.warning(f"Failed to get assignments for course {course_id}: {e}")
                    continue
            
            # Store assignments in database
            if all_assignments:
                await self._store_assignments(user_id, all_assignments)
            
            return {
                "operation": "sync_assignments_with_ingestion",
                "assignments_count": len(all_assignments),
                "assignments_ingested": assignments_ingested,
                "courses_processed": len(courses),
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Assignment sync with ingestion failed for user {user_id}: {e}")
            raise
    
    async def _sync_user_grades(
        self,
        user_id: str,
        canvas_api_key: str,
        canvas_url: str
    ) -> Dict[str, Any]:
        """Sync user's grades from Canvas"""
        # Placeholder for grade sync implementation
        return {
            "operation": "sync_grades",
            "message": "Grade sync not yet implemented",
            "synced_at": datetime.utcnow().isoformat()
        }
    
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
            
            # Filter out old completed courses
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            active_courses = []
            
            for course in courses:
                workflow_state = course.get('workflow_state', '')
                if workflow_state in ['available', 'completed']:
                    if workflow_state == 'completed':
                        term = course.get('term', {})
                        end_at = term.get('end_at')
                        if end_at:
                            try:
                                end_date = datetime.fromisoformat(end_at.replace('Z', '+00:00'))
                                if end_date < six_months_ago:
                                    continue
                            except:
                                pass
                    
                    active_courses.append(course)
            
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
            
            # Filter published assignments
            filtered_assignments = []
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            
            for assignment in assignments:
                if not assignment.get('published', False):
                    continue
                
                due_at = assignment.get('due_at')
                created_at = assignment.get('created_at')
                
                if due_at or (created_at and datetime.fromisoformat(created_at.replace('Z', '+00:00')) > one_month_ago):
                    filtered_assignments.append(assignment)
            
            return filtered_assignments
            
        except Exception as e:
            logger.error(f"Error fetching assignments for course {course_id}: {e}")
            return []
    
    async def _store_courses(self, user_id: str, courses: List[Dict[str, Any]]):
        """Store courses in database"""
        try:
            # Process courses for storage
            processed_courses = []
            for course in courses:
                processed_course = {
                    "user_id": user_id,
                    "canvas_id": course.get("id"),
                    "name": course.get("name", "Untitled Course"),
                    "course_code": course.get("course_code"),
                    "workflow_state": course.get("workflow_state"),
                    "start_at": course.get("start_at"),
                    "end_at": course.get("end_at"),
                    "enrollment_term_id": course.get("enrollment_term_id"),
                    "account_id": course.get("account_id"),
                    "synced_at": datetime.utcnow().isoformat()
                }
                processed_courses.append(processed_course)
            
            if processed_courses:
                # Clear existing courses and insert new ones
                await self.supabase.table("canvas_courses").delete().eq("user_id", user_id).execute()
                await self.supabase.table("canvas_courses").insert(processed_courses).execute()
            
        except Exception as e:
            logger.error(f"Error storing courses for user {user_id}: {e}")
            raise
    
    async def _store_assignments(self, user_id: str, assignments: List[Dict[str, Any]]):
        """Store assignments in database"""
        try:
            # Process assignments for storage
            processed_assignments = []
            for assignment in assignments:
                processed_assignment = await self._process_assignment_for_storage(user_id, assignment)
                if processed_assignment:
                    processed_assignments.append(processed_assignment)
            
            if processed_assignments:
                # Clear existing assignments and insert new ones
                await self.supabase.table("assignments").delete().eq("user_id", user_id).execute()
                
                # Insert in batches
                batch_size = 100
                for i in range(0, len(processed_assignments), batch_size):
                    batch = processed_assignments[i:i + batch_size]
                    await self.supabase.table("assignments").insert(batch).execute()
            
        except Exception as e:
            logger.error(f"Error storing assignments for user {user_id}: {e}")
            raise
    
    async def _process_assignment_for_storage(self, user_id: str, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process assignment for database storage"""
        try:
            due_at = assignment.get('due_at')
            due_date = None
            if due_at:
                try:
                    due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00')).isoformat()
                except:
                    pass
            
            assignment_type = "assignment"
            submission_types = assignment.get('submission_types', [])
            if 'online_quiz' in submission_types:
                assignment_type = "quiz"
            elif 'discussion_topic' in submission_types:
                assignment_type = "discussion"
            
            submission = assignment.get('submission', {})
            submission_status = submission.get('workflow_state', 'unsubmitted') if submission else 'unsubmitted'
            
            points_possible = assignment.get('points_possible', 0)
            estimated_minutes = max(30, min(180, int(points_possible * 2))) if points_possible else 60
            
            return {
                "user_id": user_id,
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
                "lock_at": assignment.get('lock_at'),
                "memory_id": assignment.get('memory_id')
            }
            
        except Exception as e:
            logger.error(f"Error processing assignment {assignment.get('id')}: {e}")
            return None
    
    async def _update_integration_status(self, user_id: str, assignment_count: int):
        """Update Canvas integration status"""
        try:
            integration_data = {
                "user_id": user_id,
                "is_active": True,
                "last_sync": datetime.utcnow().isoformat(),
                "assignments_synced": assignment_count,
                "sync_source": "api",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.supabase.table("canvas_integrations").upsert(
                integration_data,
                on_conflict="user_id"
            ).execute()
            
        except Exception as e:
            logger.error(f"Error updating Canvas integration status for user {user_id}: {e}")
    
    def _parse_canvas_assignment(self, assignment_data: Dict[str, Any], course_name: str) -> Assignment:
        """Parse Canvas assignment data into Assignment object for memory ingestion"""
        points = assignment_data.get("points_possible", 0)
        effort_estimate = min(max(int(points * 5), 30), 300) if points else 60
        
        return Assignment(
            id=str(assignment_data.get("id")),
            title=assignment_data.get("name", "Untitled Assignment"),
            description=assignment_data.get("description", ""),
            course=course_name,
            due_at=assignment_data.get("due_at", ""),
            effort_min=effort_estimate,
            priority=self._calculate_priority(assignment_data),
            url=assignment_data.get("html_url")
        )
    
    def _calculate_priority(self, assignment_data: Dict[str, Any]) -> int:
        """Calculate assignment priority based on Canvas data"""
        points = assignment_data.get("points_possible", 0)
        
        if points >= 100:
            return 5
        elif points >= 50:
            return 4
        elif points >= 25:
            return 3
        elif points >= 10:
            return 2
        else:
            return 1


# Global Canvas sync instance
_canvas_sync: Optional[CanvasSync] = None

def get_canvas_sync() -> CanvasSync:
    """Get global Canvas sync instance"""
    global _canvas_sync
    if _canvas_sync is None:
        _canvas_sync = CanvasSync()
    return _canvas_sync


# Convenience functions for external use
async def sync_user_canvas_data(
    user_id: str,
    canvas_api_key: str = None,
    canvas_url: str = None,
    force_refresh: bool = False,
    include_grades: bool = False
) -> Dict[str, Any]:
    """Sync Canvas data for a user - convenience function"""
    canvas_sync = get_canvas_sync()
    return await canvas_sync.sync_user_canvas_data(
        user_id, canvas_api_key, canvas_url, force_refresh, include_grades
    )


async def get_upcoming_assignments(
    user_id: str,
    days_ahead: int = 14,
    canvas_api_key: str = None,
    canvas_url: str = None
) -> Dict[str, Any]:
    """Get upcoming assignments for a user - convenience function"""
    canvas_sync = get_canvas_sync()
    return await canvas_sync.get_upcoming_assignments(
        user_id, days_ahead, canvas_api_key, canvas_url
    )