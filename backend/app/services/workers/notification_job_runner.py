"""
iOS notification jobs for PulsePlan.
Handles predictable, scheduled notifications including daily briefings, weekly summaries,
and due date reminders.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pytz
from enum import Enum

from app.config.database.supabase import get_supabase_client
from app.services.infrastructure.cache_service import get_cache_service
from app.services.notifications.ios_notification_service import get_ios_notification_service
from app.memory.processing.ingestion import get_ingestion_service

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationCategory(Enum):
    BRIEFING = "briefing"
    REMINDER = "reminder"
    SUMMARY = "summary"
    DEADLINE = "deadline"
    ACHIEVEMENT = "achievement"


class NotificationJobRunner:
    """Predictable notification jobs for iOS push notifications and email"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.cache_service = get_cache_service()
        self.ios_service = get_ios_notification_service()
        self.ingestion_service = get_ingestion_service()
    
    async def send_daily_briefings(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Send daily briefing notifications to all active users
        Runs every morning at user's preferred time
        """
        start_time = datetime.utcnow()
        logger.info("Starting daily briefing notification job")
        
        try:
            # Get users who have enabled daily briefings
            users = await self._get_briefing_enabled_users()
            
            if not users:
                return {
                    "job": "daily_briefings",
                    "total_users": 0,
                    "sent_notifications": 0,
                    "failed_notifications": 0,
                    "execution_time": (datetime.utcnow() - start_time).total_seconds()
                }
            
            results = {
                "job": "daily_briefings",
                "started_at": start_time.isoformat(),
                "total_users": len(users),
                "sent_notifications": 0,
                "failed_notifications": 0,
                "notifications": []
            }
            
            # Process users in batches
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]
                batch_tasks = []
                
                for user in batch:
                    task = asyncio.create_task(
                        self._send_daily_briefing_to_user(user, results)
                    )
                    batch_tasks.append(task)
                
                # Wait for batch completion
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Small delay between batches
                await asyncio.sleep(0.5)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["completed_at"] = datetime.utcnow().isoformat()
            results["execution_time"] = execution_time
            
            logger.info(
                f"Daily briefing job completed. "
                f"Sent: {results['sent_notifications']}, "
                f"Failed: {results['failed_notifications']} in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Daily briefing job failed: {e}")
            raise
    
    async def send_weekly_summaries(self, batch_size: int = 25) -> Dict[str, Any]:
        """
        Send weekly productivity summary notifications
        Runs every Sunday evening or Monday morning
        """
        start_time = datetime.utcnow()
        logger.info("Starting weekly summary notification job")
        
        try:
            users = await self._get_weekly_summary_enabled_users()
            
            if not users:
                return {
                    "job": "weekly_summaries",
                    "total_users": 0,
                    "sent_notifications": 0,
                    "failed_notifications": 0,
                    "execution_time": (datetime.utcnow() - start_time).total_seconds()
                }
            
            results = {
                "job": "weekly_summaries",
                "started_at": start_time.isoformat(),
                "total_users": len(users),
                "sent_notifications": 0,
                "failed_notifications": 0,
                "notifications": []
            }
            
            # Process users in smaller batches (weekly summaries are more intensive)
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]
                batch_tasks = []
                
                for user in batch:
                    task = asyncio.create_task(
                        self._send_weekly_summary_to_user(user, results)
                    )
                    batch_tasks.append(task)
                
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                await asyncio.sleep(1)  # Longer delay for intensive operations
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["completed_at"] = datetime.utcnow().isoformat()
            results["execution_time"] = execution_time
            
            logger.info(
                f"Weekly summary job completed. "
                f"Sent: {results['sent_notifications']}, "
                f"Failed: {results['failed_notifications']} in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Weekly summary job failed: {e}")
            raise
    
    async def send_due_date_reminders(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Send due date reminder notifications for upcoming assignments
        Runs multiple times daily to catch assignments at different reminder intervals
        """
        start_time = datetime.utcnow()
        logger.info("Starting due date reminder notification job")
        
        try:
            # Get assignments due in the next 1, 3, and 7 days
            upcoming_assignments = await self._get_upcoming_assignments()
            
            if not upcoming_assignments:
                return {
                    "job": "due_date_reminders",
                    "total_assignments": 0,
                    "sent_notifications": 0,
                    "failed_notifications": 0,
                    "execution_time": (datetime.utcnow() - start_time).total_seconds()
                }
            
            results = {
                "job": "due_date_reminders",
                "started_at": start_time.isoformat(),
                "total_assignments": len(upcoming_assignments),
                "sent_notifications": 0,
                "failed_notifications": 0,
                "notifications": []
            }
            
            # Process assignments in batches
            for i in range(0, len(upcoming_assignments), batch_size):
                batch = upcoming_assignments[i:i + batch_size]
                batch_tasks = []
                
                for assignment in batch:
                    task = asyncio.create_task(
                        self._send_due_date_reminder(assignment, results)
                    )
                    batch_tasks.append(task)
                
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                await asyncio.sleep(0.3)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["completed_at"] = datetime.utcnow().isoformat()
            results["execution_time"] = execution_time
            
            logger.info(
                f"Due date reminder job completed. "
                f"Sent: {results['sent_notifications']}, "
                f"Failed: {results['failed_notifications']} in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Due date reminder job failed: {e}")
            raise
    
    async def send_achievement_notifications(self, batch_size: int = 75) -> Dict[str, Any]:
        """
        Send achievement and milestone notifications
        Runs daily to recognize user accomplishments
        """
        start_time = datetime.utcnow()
        logger.info("Starting achievement notification job")
        
        try:
            achievements = await self._detect_user_achievements()
            
            if not achievements:
                return {
                    "job": "achievement_notifications",
                    "total_achievements": 0,
                    "sent_notifications": 0,
                    "failed_notifications": 0,
                    "execution_time": (datetime.utcnow() - start_time).total_seconds()
                }
            
            results = {
                "job": "achievement_notifications",
                "started_at": start_time.isoformat(),
                "total_achievements": len(achievements),
                "sent_notifications": 0,
                "failed_notifications": 0,
                "notifications": []
            }
            
            # Process achievements in batches
            for i in range(0, len(achievements), batch_size):
                batch = achievements[i:i + batch_size]
                batch_tasks = []
                
                for achievement in batch:
                    task = asyncio.create_task(
                        self._send_achievement_notification(achievement, results)
                    )
                    batch_tasks.append(task)
                
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                await asyncio.sleep(0.4)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["completed_at"] = datetime.utcnow().isoformat()
            results["execution_time"] = execution_time
            
            logger.info(
                f"Achievement notification job completed. "
                f"Sent: {results['sent_notifications']}, "
                f"Failed: {results['failed_notifications']} in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Achievement notification job failed: {e}")
            raise
    
    async def _send_daily_briefing_to_user(self, user: Dict[str, Any], results: Dict[str, Any]):
        """Send daily briefing notification to a single user"""
        user_id = user["user_id"]

        try:
            # Get user's timezone and preferred briefing time
            from app.core.utils.timezone_utils import get_timezone_manager
            tz_mgr = get_timezone_manager()
            user_tz_str = user.get("timezone", "UTC")
            briefing_time = user.get("daily_briefing_time", "08:00")

            # Check if it's the right time for this user
            now_utc = datetime.utcnow().replace(tzinfo=tz_mgr._default_timezone)
            current_time = tz_mgr.convert_to_user_timezone(now_utc, user_tz_str)
            if not self._is_briefing_time(current_time, briefing_time):
                return

            # Generate daily briefing content
            briefing_data = await self._generate_daily_briefing(user_id)

            if not briefing_data:
                return

            # Save briefing to database
            try:
                from app.database.repositories.integration_repositories import get_briefings_repository
                from uuid import UUID

                briefings_repo = get_briefings_repository()
                await briefings_repo.save_briefing(
                    user_id=UUID(user_id),
                    briefing_date=datetime.utcnow().date(),
                    content=briefing_data
                )
                logger.info(f"Saved briefing to database for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to save briefing to database for user {user_id}: {e}")

            # Send email if enabled
            email_sent = False
            if user.get("daily_briefing_email_enabled", True):
                try:
                    from app.workers.communication.email_service import get_email_service

                    email_service = get_email_service()
                    email_result = await email_service.send_daily_briefing(
                        to=user.get("email"),
                        user_name=user.get("full_name", user.get("email", "").split('@')[0]),
                        briefing_data=briefing_data
                    )
                    email_sent = email_result.get("success", False)
                    logger.info(f"Daily briefing email sent to user {user_id}: {email_sent}")
                except Exception as e:
                    logger.error(f"Failed to send daily briefing email to user {user_id}: {e}")

            # Send iOS push notification if enabled
            notification_sent = False
            if user.get("daily_briefing_notification_enabled", True):
                # Create notification payload
                notification = {
                    "title": f"Good morning! Here's your daily briefing",
                    "body": briefing_data["summary"],
                    "category": NotificationCategory.BRIEFING.value,
                    "priority": NotificationPriority.NORMAL.value,
                    "data": {
                        "type": "daily_briefing",
                        "user_id": user_id,
                        "tasks_today": briefing_data.get("tasks_count", 0),
                        "upcoming_deadlines": briefing_data.get("deadlines_count", 0),
                        "deep_link": "pulseplan://briefing/daily"
                    }
                }

                # Send iOS push notification
                notification_sent = await self.ios_service.send_notification(
                    user_id, notification, scheduled_for=None
                )

            if email_sent or notification_sent:
                results["sent_notifications"] += 1
                results["notifications"].append({
                    "user_id": user_id,
                    "type": "daily_briefing",
                    "status": "sent",
                    "email_sent": email_sent,
                    "notification_sent": notification_sent,
                    "sent_at": datetime.utcnow().isoformat()
                })
            else:
                results["failed_notifications"] += 1
                results["notifications"].append({
                    "user_id": user_id,
                    "type": "daily_briefing",
                    "status": "failed",
                    "failed_at": datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Failed to send daily briefing to user {user_id}: {e}")
            results["failed_notifications"] += 1
    
    async def _send_weekly_summary_to_user(self, user: Dict[str, Any], results: Dict[str, Any]):
        """Send weekly summary notification to a single user"""
        user_id = user["user_id"]
        
        try:
            # Generate weekly summary using the weekly pulse tool
            from app.agents.tools.weekly_pulse import WeeklyPulseTool
            
            pulse_tool = WeeklyPulseTool()
            pulse_result = await pulse_tool.execute(
                {"user_id": user_id, "week_offset": 0},
                {"user_id": user_id}
            )
            
            if not pulse_result.success:
                logger.warning(f"Failed to generate weekly pulse for user {user_id}")
                return
            
            pulse_data = pulse_result.data
            
            # Create engaging notification based on pulse data
            productivity_score = pulse_data.get("productivity_score", 7.0)
            completed_tasks = pulse_data.get("completed_tasks", 0)
            achievements = pulse_data.get("achievements", [])
            
            if productivity_score >= 8.0:
                title = f"Outstanding week! You scored {productivity_score}/10"
                body = f"Completed {completed_tasks} tasks with excellent productivity"
            elif productivity_score >= 7.0:
                title = f"Great week! You scored {productivity_score}/10"
                body = f"Completed {completed_tasks} tasks and stayed on track"
            else:
                title = f"Week wrapped up - {productivity_score}/10"
                body = f"Completed {completed_tasks} tasks. Let's aim higher next week!"
            
            notification = {
                "title": title,
                "body": body,
                "category": NotificationCategory.SUMMARY.value,
                "priority": NotificationPriority.NORMAL.value,
                "data": {
                    "type": "weekly_summary",
                    "user_id": user_id,
                    "productivity_score": productivity_score,
                    "completed_tasks": completed_tasks,
                    "achievements_count": len(achievements),
                    "deep_link": "pulseplan://analytics/weekly"
                }
            }
            
            success = await self.ios_service.send_notification(
                user_id, notification, scheduled_for=None
            )
            
            if success:
                results["sent_notifications"] += 1
                results["notifications"].append({
                    "user_id": user_id,
                    "type": "weekly_summary",
                    "productivity_score": productivity_score,
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                })
            else:
                results["failed_notifications"] += 1
                
        except Exception as e:
            logger.error(f"Failed to send weekly summary to user {user_id}: {e}")
            results["failed_notifications"] += 1
    
    async def _send_due_date_reminder(self, assignment: Dict[str, Any], results: Dict[str, Any]):
        """Send due date reminder for a specific assignment"""
        user_id = assignment["user_id"]
        assignment_name = assignment["name"]
        due_at = assignment["due_at"]
        course_name = assignment.get("course_name", "")
        
        try:
            # Calculate time until due date
            due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
            time_until_due = due_date - datetime.now(pytz.UTC)
            days_until_due = time_until_due.days
            hours_until_due = time_until_due.total_seconds() / 3600
            
            # Determine reminder message and priority based on time left
            if hours_until_due <= 6:
                title = f"Due in {int(hours_until_due)} hours: {assignment_name}"
                priority = NotificationPriority.CRITICAL.value
                body = f"{course_name} - Submit soon to avoid being late!"
            elif hours_until_due <= 24:
                title = f"Due tomorrow: {assignment_name}"
                priority = NotificationPriority.HIGH.value
                body = f"{course_name} - Make sure to complete this today"
            elif days_until_due <= 3:
                title = f"Due in {days_until_due} days: {assignment_name}"
                priority = NotificationPriority.NORMAL.value
                body = f"{course_name} - Start working on this soon"
            else:
                title = f"Due in {days_until_due} days: {assignment_name}"
                priority = NotificationPriority.LOW.value
                body = f"{course_name} - Plan ahead for this assignment"
            
            notification = {
                "title": title,
                "body": body,
                "category": NotificationCategory.DEADLINE.value,
                "priority": priority,
                "data": {
                    "type": "due_date_reminder",
                    "user_id": user_id,
                    "assignment_id": assignment["canvas_id"],
                    "assignment_name": assignment_name,
                    "course_name": course_name,
                    "due_at": due_at,
                    "hours_until_due": int(hours_until_due),
                    "deep_link": f"pulseplan://assignment/{assignment['canvas_id']}"
                }
            }
            
            success = await self.ios_service.send_notification(
                user_id, notification, scheduled_for=None
            )
            
            if success:
                results["sent_notifications"] += 1
                results["notifications"].append({
                    "user_id": user_id,
                    "assignment_id": assignment["canvas_id"],
                    "type": "due_date_reminder",
                    "hours_until_due": int(hours_until_due),
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                })
            else:
                results["failed_notifications"] += 1
                
        except Exception as e:
            logger.error(f"Failed to send due date reminder for assignment {assignment['canvas_id']}: {e}")
            results["failed_notifications"] += 1
    
    async def _send_achievement_notification(self, achievement: Dict[str, Any], results: Dict[str, Any]):
        """Send achievement notification to user"""
        user_id = achievement["user_id"]
        achievement_type = achievement["type"]
        achievement_data = achievement["data"]
        
        try:
            # Create achievement-specific notification
            if achievement_type == "completion_streak":
                days = achievement_data["streak_days"]
                title = f"{days}-day completion streak!"
                body = f"You've completed tasks {days} days in a row. Keep it up!"
            
            elif achievement_type == "productivity_milestone":
                score = achievement_data["productivity_score"]
                title = f"Productivity milestone: {score}/10!"
                body = "You've reached a new personal best in weekly productivity"
            
            elif achievement_type == "early_completion":
                assignment_name = achievement_data["assignment_name"]
                hours_early = achievement_data["hours_early"]
                title = f"Early bird! Completed ahead of schedule"
                body = f"Finished '{assignment_name}' {hours_early} hours early"
            
            elif achievement_type == "perfect_week":
                title = "Perfect week achieved!"
                body = "You completed every single task this week. Amazing work!"
            
            else:
                title = "Achievement unlocked!"
                body = "You've reached a new milestone in your productivity journey"
            
            notification = {
                "title": title,
                "body": body,
                "category": NotificationCategory.ACHIEVEMENT.value,
                "priority": NotificationPriority.NORMAL.value,
                "data": {
                    "type": "achievement",
                    "user_id": user_id,
                    "achievement_type": achievement_type,
                    "achievement_data": achievement_data,
                    "deep_link": "pulseplan://achievements"
                }
            }
            
            success = await self.ios_service.send_notification(
                user_id, notification, scheduled_for=None
            )
            
            if success:
                results["sent_notifications"] += 1
                results["notifications"].append({
                    "user_id": user_id,
                    "achievement_type": achievement_type,
                    "type": "achievement",
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                })
            else:
                results["failed_notifications"] += 1
                
        except Exception as e:
            logger.error(f"Failed to send achievement notification to user {user_id}: {e}")
            results["failed_notifications"] += 1
    
    async def _get_briefing_enabled_users(self) -> List[Dict[str, Any]]:
        """Get users who have enabled daily briefing notifications"""
        try:
            response = await self.supabase.table("user_preferences").select(
                "user_id, timezone, daily_briefing_enabled, daily_briefing_time"
            ).eq("daily_briefing_enabled", True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting briefing enabled users: {e}")
            return []
    
    async def _get_weekly_summary_enabled_users(self) -> List[Dict[str, Any]]:
        """Get users who have enabled weekly summary notifications"""
        try:
            response = await self.supabase.table("user_preferences").select(
                "user_id, timezone, weekly_summary_enabled"
            ).eq("weekly_summary_enabled", True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting weekly summary enabled users: {e}")
            return []
    
    async def _get_upcoming_assignments(self) -> List[Dict[str, Any]]:
        """Get assignments due in the next 1, 3, and 7 days"""
        try:
            # Get assignments due in the next week
            next_week = (datetime.utcnow() + timedelta(days=7)).isoformat()
            
            response = await self.supabase.table("assignments").select(
                "user_id, canvas_id, name, due_at, course_name, points_possible"
            ).lte("due_at", next_week).gte("due_at", datetime.utcnow().isoformat()
            ).neq("submission_status", "graded").execute()
            
            assignments = response.data or []
            
            # Filter based on reminder preferences and avoid duplicates
            filtered_assignments = []
            
            for assignment in assignments:
                # Check if we've already sent a reminder for this assignment today
                cache_key = f"reminder_sent:{assignment['canvas_id']}:{datetime.utcnow().strftime('%Y-%m-%d')}"
                if await self.cache_service.exists(cache_key):
                    continue
                
                # Calculate hours until due
                due_date = datetime.fromisoformat(assignment["due_at"].replace('Z', '+00:00'))
                hours_until_due = (due_date - datetime.now(pytz.UTC)).total_seconds() / 3600
                
                # Send reminders at specific intervals
                if (hours_until_due <= 6 or  # 6 hours before
                    (24 <= hours_until_due <= 26) or  # 1 day before (with 2-hour window)
                    (72 <= hours_until_due <= 74) or  # 3 days before
                    (168 <= hours_until_due <= 170)):  # 7 days before
                    
                    filtered_assignments.append(assignment)
                    
                    # Mark as reminder sent for today
                    await self.cache_service.set(cache_key, True, 86400)  # 24 hour TTL
            
            return filtered_assignments
            
        except Exception as e:
            logger.error(f"Error getting upcoming assignments: {e}")
            return []
    
    async def _detect_user_achievements(self) -> List[Dict[str, Any]]:
        """Detect user achievements that deserve notifications"""
        try:
            achievements = []
            
            # Get users with recent activity
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            
            # Check for completion streaks
            streak_achievements = await self._detect_completion_streaks()
            achievements.extend(streak_achievements)
            
            # Check for productivity milestones
            productivity_achievements = await self._detect_productivity_milestones()
            achievements.extend(productivity_achievements)
            
            # Check for early completions
            early_completion_achievements = await self._detect_early_completions()
            achievements.extend(early_completion_achievements)
            
            # Check for perfect weeks
            perfect_week_achievements = await self._detect_perfect_weeks()
            achievements.extend(perfect_week_achievements)
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error detecting user achievements: {e}")
            return []
    
    async def _detect_completion_streaks(self) -> List[Dict[str, Any]]:
        """Detect users with notable task completion streaks"""
        # This would query the database to find users with consecutive days of task completion
        # For now, returning mock data
        return []
    
    async def _detect_productivity_milestones(self) -> List[Dict[str, Any]]:
        """Detect users who have hit new productivity milestones"""
        # This would analyze weekly pulse data to find new personal bests
        return []
    
    async def _detect_early_completions(self) -> List[Dict[str, Any]]:
        """Detect users who completed assignments significantly early"""
        # This would check for assignments completed well before their due date
        return []
    
    async def _detect_perfect_weeks(self) -> List[Dict[str, Any]]:
        """Detect users who had perfect task completion weeks"""
        # This would check for weeks where users completed 100% of scheduled tasks
        return []
    
    async def _generate_daily_briefing(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Generate daily briefing content for a user"""
        try:
            # Get today's scheduled tasks
            today = datetime.utcnow().date()
            
            # Get tasks scheduled for today
            tasks_response = await self.supabase.table("scheduled_blocks").select(
                "task_id, title, start_time, end_time"
            ).eq("user_id", user_id).gte("start_time", today.isoformat()
            ).lt("start_time", (today + timedelta(days=1)).isoformat()).execute()
            
            today_tasks = tasks_response.data or []
            
            # Get upcoming deadlines (next 7 days)
            next_week = (datetime.utcnow() + timedelta(days=7)).isoformat()
            deadlines_response = await self.supabase.table("assignments").select(
                "name, due_at, course_name"
            ).eq("user_id", user_id).lte("due_at", next_week
            ).gte("due_at", datetime.utcnow().isoformat()
            ).neq("submission_status", "graded").limit(5).execute()
            
            upcoming_deadlines = deadlines_response.data or []
            
            # Create summary
            if len(today_tasks) == 0:
                summary = "Your schedule is clear today - perfect for catching up or getting ahead!"
            elif len(today_tasks) == 1:
                summary = f"You have 1 task scheduled today. "
            else:
                summary = f"You have {len(today_tasks)} tasks scheduled today. "
            
            if upcoming_deadlines:
                summary += f"You also have {len(upcoming_deadlines)} upcoming deadlines to keep in mind."
            else:
                summary += "No pressing deadlines ahead - great planning!"
            
            return {
                "summary": summary,
                "tasks_count": len(today_tasks),
                "deadlines_count": len(upcoming_deadlines),
                "today_tasks": today_tasks,
                "upcoming_deadlines": upcoming_deadlines
            }
            
        except Exception as e:
            logger.error(f"Error generating daily briefing for user {user_id}: {e}")
            return None
    
    def _is_briefing_time(self, current_time: datetime, preferred_time: str) -> bool:
        """Check if it's the right time to send a briefing"""
        try:
            # Parse preferred time (format: "HH:MM")
            hour, minute = map(int, preferred_time.split(':'))
            
            # Check if current time is within 30 minutes of preferred time
            preferred = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            time_diff = abs((current_time - preferred).total_seconds())
            
            # Return True if within 30 minutes
            return time_diff <= 1800  # 30 minutes in seconds
            
        except Exception as e:
            logger.warning(f"Error checking briefing time: {e}")
            return False


# Backward compatible alias
NotificationJobs = NotificationJobRunner


# Global notification jobs instance
_notification_jobs: Optional[NotificationJobRunner] = None


def get_notification_jobs() -> NotificationJobRunner:
    """Get global notification jobs instance"""
    global _notification_jobs
    if _notification_jobs is None:
        _notification_jobs = NotificationJobs()
    return _notification_jobs


# Entry point functions for job scheduler
async def run_daily_briefings() -> Dict[str, Any]:
    """Run daily briefing notifications job"""
    jobs = get_notification_jobs()
    return await jobs.send_daily_briefings()


async def run_weekly_summaries() -> Dict[str, Any]:
    """Run weekly summary notifications job"""
    jobs = get_notification_jobs()
    return await jobs.send_weekly_summaries()


async def run_due_date_reminders() -> Dict[str, Any]:
    """Run due date reminder notifications job"""
    jobs = get_notification_jobs()
    return await jobs.send_due_date_reminders()


async def run_achievement_notifications() -> Dict[str, Any]:
    """Run achievement notifications job"""
    jobs = get_notification_jobs()
    return await jobs.send_achievement_notifications()
