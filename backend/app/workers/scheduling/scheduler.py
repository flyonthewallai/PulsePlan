"""
Background task scheduler for daily briefings, weekly pulse, and other jobs
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ...config.database.supabase import get_supabase_client
from ...agents.orchestrator import get_agent_orchestrator
from ..communication.email_service import get_email_service
from ..core.types import JobResult, JobStatus

logger = logging.getLogger(__name__)


class WorkerScheduler:
    """Background job scheduler using APScheduler"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.email_service = get_email_service()
        self.agent_orchestrator = get_agent_orchestrator()
        self.supabase = get_supabase_client()
        
    async def start(self):
        """Start the scheduler and register jobs"""
        logger.info("Starting worker scheduler...")
        
        # Daily briefing job - Run every 15 minutes to catch all user timezones
        self.scheduler.add_job(
            func=self.run_daily_briefings,
            trigger=CronTrigger(minute="*/15"),  # Every 15 minutes
            id="daily_briefings",
            name="Daily Briefing Job",
            replace_existing=True,
        )
        
        # Weekly pulse job - Run every hour to catch all user timezones and days
        self.scheduler.add_job(
            func=self.run_weekly_pulse,
            trigger=CronTrigger(minute=0),  # Every hour
            id="weekly_pulse",
            name="Weekly Pulse Job", 
            replace_existing=True,
        )
        
        self.scheduler.start()
        logger.info("Worker scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Worker scheduler stopped")
    
    async def run_daily_briefings(self) -> List[JobResult]:
        """Execute daily briefing job for all eligible users"""
        logger.info("Starting daily briefing job execution")
        start_time = datetime.utcnow()
        
        try:
            # Get eligible users
            users = await self._get_briefing_eligible_users()
            logger.info(f"Found {len(users)} eligible users for daily briefing")
            
            if not users:
                return []
            
            results = []
            
            # Process each user through agent system
            for user in users:
                try:
                    result = await self._process_daily_briefing(user)
                    results.append(result)
                    
                    # Log result
                    logger.info(
                        f"Daily briefing processed for user {user['id']}: "
                        f"{'Success' if result.success else 'Failed - ' + str(result.error)}"
                    )
                    
                except Exception as e:
                    error_result = JobResult(
                        success=False,
                        user_id=user["id"],
                        email=user["email"],
                        error=str(e),
                        timestamp=datetime.utcnow()
                    )
                    results.append(error_result)
                    logger.error(f"Failed to process daily briefing for user {user['id']}: {e}")
            
            # Log summary
            success_count = sum(1 for r in results if r.success)
            failure_count = len(results) - success_count
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Daily briefing job completed: {success_count} success, "
                f"{failure_count} failures in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Daily briefing job failed completely: {e}")
            raise
    
    async def run_weekly_pulse(self) -> List[JobResult]:
        """Execute weekly pulse job for all eligible users"""
        logger.info("Starting weekly pulse job execution")
        start_time = datetime.utcnow()
        
        try:
            # Get eligible users
            users = await self._get_pulse_eligible_users()
            logger.info(f"Found {len(users)} eligible users for weekly pulse")
            
            if not users:
                return []
            
            results = []
            
            # Process each user through agent system
            for user in users:
                try:
                    result = await self._process_weekly_pulse(user)
                    results.append(result)
                    
                    logger.info(
                        f"Weekly pulse processed for user {user['id']}: "
                        f"{'Success' if result.success else 'Failed - ' + str(result.error)}"
                    )
                    
                except Exception as e:
                    error_result = JobResult(
                        success=False,
                        user_id=user["id"],
                        email=user["email"],
                        error=str(e),
                        timestamp=datetime.utcnow()
                    )
                    results.append(error_result)
                    logger.error(f"Failed to process weekly pulse for user {user['id']}: {e}")
            
            # Log summary
            success_count = sum(1 for r in results if r.success)
            failure_count = len(results) - success_count
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Weekly pulse job completed: {success_count} success, "
                f"{failure_count} failures in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Weekly pulse job failed completely: {e}")
            raise
    
    async def _get_briefing_eligible_users(self) -> List[Dict[str, Any]]:
        """Get users eligible for daily briefing based on current time in their timezone"""
        try:
            from datetime import datetime
            import pytz
            
            # Get all users with daily briefing enabled
            response = await self.supabase.table("user_preferences").select(
                "user_id, daily_briefing_enabled, daily_briefing_time, daily_briefing_timezone, daily_briefing_email_enabled"
            ).eq("daily_briefing_enabled", True).execute()
            
            if not response.data:
                return []
            
            eligible_users = []
            current_utc = datetime.utcnow()
            
            for user_prefs in response.data:
                try:
                    # Get user timezone and briefing time
                    user_tz_str = user_prefs.get("daily_briefing_timezone", "UTC")
                    briefing_time_str = user_prefs.get("daily_briefing_time", "08:00:00")
                    user_id = user_prefs["user_id"]
                    
                    # Convert to timezone object
                    try:
                        user_tz = pytz.timezone(user_tz_str)
                    except:
                        user_tz = pytz.UTC
                    
                    # Get current time in user's timezone
                    current_user_time = current_utc.replace(tzinfo=pytz.UTC).astimezone(user_tz)
                    
                    # Parse briefing time
                    try:
                        hour, minute, second = briefing_time_str.split(":")
                        briefing_hour = int(hour)
                        briefing_minute = int(minute)
                    except:
                        briefing_hour, briefing_minute = 8, 0  # Default to 8 AM
                    
                    # Check if it's the right time for briefing (within 30 minute window)
                    target_time = current_user_time.replace(
                        hour=briefing_hour, 
                        minute=briefing_minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    time_diff = abs((current_user_time - target_time).total_seconds())
                    
                    # If within 30 minutes of target time
                    if time_diff <= 1800:  # 30 minutes
                        # Get full user info
                        user_response = await self.supabase.table("users").select(
                            "id, email, name"
                        ).eq("id", user_id).execute()
                        
                        if user_response.data:
                            user_data = user_response.data[0]
                            user_data.update({
                                "briefing_preferences": user_prefs,
                                "timezone": user_tz_str
                            })
                            eligible_users.append(user_data)
                            
                except Exception as e:
                    logger.warning(f"Error processing user {user_prefs.get('user_id')}: {e}")
                    continue
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"Failed to get briefing eligible users: {e}")
            return []
    
    async def _get_pulse_eligible_users(self) -> List[Dict[str, Any]]:
        """Get users eligible for weekly pulse based on current time in their timezone"""
        try:
            from datetime import datetime
            import pytz
            
            # Get all users with weekly pulse enabled
            response = await self.supabase.table("user_preferences").select(
                "user_id, weekly_pulse_enabled, weekly_pulse_day, weekly_pulse_time, daily_briefing_timezone, weekly_pulse_email_enabled"
            ).eq("weekly_pulse_enabled", True).execute()
            
            if not response.data:
                return []
            
            eligible_users = []
            current_utc = datetime.utcnow()
            
            for user_prefs in response.data:
                try:
                    # Get user timezone and pulse settings
                    user_tz_str = user_prefs.get("daily_briefing_timezone", "UTC")  # Use same timezone as briefing
                    pulse_time_str = user_prefs.get("weekly_pulse_time", "18:00:00")
                    pulse_day = user_prefs.get("weekly_pulse_day", 0)  # 0 = Sunday
                    user_id = user_prefs["user_id"]
                    
                    # Convert to timezone object
                    try:
                        user_tz = pytz.timezone(user_tz_str)
                    except:
                        user_tz = pytz.UTC
                    
                    # Get current time in user's timezone
                    current_user_time = current_utc.replace(tzinfo=pytz.UTC).astimezone(user_tz)
                    
                    # Check if it's the right day (0=Monday, 6=Sunday in Python weekday())
                    # Convert pulse_day (0=Sunday) to Python weekday (6=Sunday)
                    target_weekday = (pulse_day + 6) % 7
                    
                    if current_user_time.weekday() == target_weekday:
                        # Parse pulse time
                        try:
                            hour, minute, second = pulse_time_str.split(":")
                            pulse_hour = int(hour)
                            pulse_minute = int(minute)
                        except:
                            pulse_hour, pulse_minute = 18, 0  # Default to 6 PM
                        
                        # Check if it's the right time for pulse (within 1 hour window)
                        target_time = current_user_time.replace(
                            hour=pulse_hour, 
                            minute=pulse_minute, 
                            second=0, 
                            microsecond=0
                        )
                        
                        time_diff = abs((current_user_time - target_time).total_seconds())
                        
                        # If within 1 hour of target time
                        if time_diff <= 3600:  # 1 hour
                            # Get full user info
                            user_response = await self.supabase.table("users").select(
                                "id, email, name"
                            ).eq("id", user_id).execute()
                            
                            if user_response.data:
                                user_data = user_response.data[0]
                                user_data.update({
                                    "pulse_preferences": user_prefs,
                                    "timezone": user_tz_str
                                })
                                eligible_users.append(user_data)
                                
                except Exception as e:
                    logger.warning(f"Error processing user {user_prefs.get('user_id')}: {e}")
                    continue
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"Failed to get pulse eligible users: {e}")
            return []
    
    async def _process_daily_briefing(self, user: Dict[str, Any]) -> JobResult:
        """Process daily briefing for a single user using agent system"""
        try:
            from app.services.cache_service import get_cache_service
            from datetime import datetime
            
            user_id = user["id"]
            email = user["email"]
            name = user.get("name", "User")
            
            # Check if we've already sent a briefing today to prevent duplicates
            today = datetime.utcnow().date().isoformat()
            cache_key = f"briefing_sent:{user_id}:{today}"
            cache_service = get_cache_service()
            
            if await cache_service.exists(cache_key):
                return JobResult(
                    success=True,
                    user_id=user_id,
                    email=email,
                    timestamp=datetime.utcnow(),
                    data={"briefing_sent": False, "reason": "Already sent today"}
                )
            
            # Use briefing agent to generate content
            briefing_result = await self.agent_orchestrator.run_briefing_workflow(
                user_id=user_id,
                context={
                    "user_email": email,
                    "user_name": name,
                    "timezone": user.get("timezone", "UTC"),
                    "briefing_type": "daily"
                }
            )
            
            if not briefing_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error="Agent failed to generate briefing",
                    timestamp=datetime.utcnow()
                )
            
            # Extract briefing data
            briefing_data = briefing_result.get("data", {})
            
            # Send email using email service
            email_result = await self.email_service.send_daily_briefing(
                to=email,
                user_name=name,
                briefing_data=briefing_data
            )
            
            if not email_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error=email_result.get("error", "Email sending failed"),
                    timestamp=datetime.utcnow()
                )
            
            # Mark briefing as sent for today to prevent duplicates
            await cache_service.set(cache_key, True, ttl=86400)  # 24 hours
            
            return JobResult(
                success=True,
                user_id=user_id,
                email=email,
                timestamp=datetime.utcnow(),
                data={"briefing_sent": True, "email_id": email_result.get("message_id")}
            )
            
        except Exception as e:
            return JobResult(
                success=False,
                user_id=user["id"],
                email=user["email"],
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def _process_weekly_pulse(self, user: Dict[str, Any]) -> JobResult:
        """Process weekly pulse for a single user using agent system"""
        try:
            user_id = user["id"]
            email = user["email"]
            name = user.get("name", "User")
            
            # Use weekly pulse agent to generate content
            pulse_result = await self.agent_orchestrator.run_weekly_pulse_workflow(
                user_id=user_id,
                context={
                    "user_email": email,
                    "user_name": name,
                    "timezone": user.get("timezone", "UTC"),
                    "pulse_type": "weekly"
                }
            )
            
            if not pulse_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error="Agent failed to generate weekly pulse",
                    timestamp=datetime.utcnow()
                )
            
            # Extract pulse data
            pulse_data = pulse_result.get("data", {})
            
            # Send email using email service
            email_result = await self.email_service.send_weekly_pulse(
                to=email,
                user_name=name,
                pulse_data=pulse_data
            )
            
            if not email_result.get("success"):
                return JobResult(
                    success=False,
                    user_id=user_id,
                    email=email,
                    error=email_result.get("error", "Email sending failed"),
                    timestamp=datetime.utcnow()
                )
            
            return JobResult(
                success=True,
                user_id=user_id,
                email=email,
                timestamp=datetime.utcnow(),
                data={"pulse_sent": True, "email_id": email_result.get("message_id")}
            )
            
        except Exception as e:
            return JobResult(
                success=False,
                user_id=user["id"],
                email=user["email"],
                error=str(e),
                timestamp=datetime.utcnow()
            )


# Global scheduler instance
_scheduler: Optional[WorkerScheduler] = None

def get_worker_scheduler() -> WorkerScheduler:
    """Get global worker scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = WorkerScheduler()
    return _scheduler