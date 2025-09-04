"""
Timezone-aware scheduler that only runs briefing jobs when needed
Analyzes user timezones and creates dynamic scheduling jobs
"""
import logging
import asyncio
from typing import Dict, Any, List, Set, Optional
from datetime import datetime, time
from collections import defaultdict
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config.supabase import get_supabase_client
from .scheduler import WorkerScheduler

logger = logging.getLogger(__name__)


class TimezoneAwareScheduler:
    """Smart scheduler that only runs jobs for timezones that have users"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.worker_scheduler = WorkerScheduler()
        self.supabase = get_supabase_client()
        self.active_timezone_jobs = set()
        
    async def start(self):
        """Start the scheduler and analyze user timezones"""
        logger.info("Starting timezone-aware scheduler...")
        
        # Analyze user timezones and create targeted jobs
        await self._analyze_and_schedule_timezones()
        
        # Schedule a job to refresh timezone analysis daily
        self.scheduler.add_job(
            func=self._analyze_and_schedule_timezones,
            trigger=CronTrigger(hour=0, minute=0),  # Daily at midnight UTC
            id="refresh_timezone_analysis",
            name="Refresh Timezone Analysis",
            replace_existing=True,
        )
        
        self.scheduler.start()
        logger.info("Timezone-aware scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Timezone-aware scheduler stopped")
    
    async def _analyze_and_schedule_timezones(self):
        """Analyze user timezones and create targeted scheduling jobs"""
        try:
            logger.info("Analyzing user timezones for smart scheduling...")
            
            # Get all users with briefing preferences
            timezone_analysis = await self._get_timezone_analysis()
            
            if not timezone_analysis:
                logger.info("No users found with briefing preferences")
                return
            
            # Remove old timezone-specific jobs
            await self._cleanup_old_timezone_jobs()
            
            # Create new timezone-specific jobs
            await self._create_timezone_jobs(timezone_analysis)
            
            logger.info(f"Created briefing jobs for {len(timezone_analysis)} different timezone/time combinations")
            
        except Exception as e:
            logger.error(f"Error analyzing timezones: {e}")
    
    async def _get_timezone_analysis(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get analysis of user timezones and briefing times"""
        try:
            # Query user preferences to understand timezone distribution
            response = await self.supabase.table("user_preferences").select(
                "user_id, daily_briefing_enabled, daily_briefing_time, daily_briefing_timezone, weekly_pulse_enabled, weekly_pulse_day, weekly_pulse_time"
            ).eq("daily_briefing_enabled", True).execute()
            
            if not response.data:
                return {}
            
            # Group users by timezone and briefing time
            timezone_groups = defaultdict(list)
            
            for user_prefs in response.data:
                tz = user_prefs.get("daily_briefing_timezone", "UTC")
                time_str = user_prefs.get("daily_briefing_time", "08:00:00")
                
                # Create a key combining timezone and time
                key = f"{tz}_{time_str}"
                timezone_groups[key].append({
                    "user_id": user_prefs["user_id"],
                    "timezone": tz,
                    "briefing_time": time_str,
                    "weekly_pulse_enabled": user_prefs.get("weekly_pulse_enabled", False),
                    "weekly_pulse_day": user_prefs.get("weekly_pulse_day", 0),
                    "weekly_pulse_time": user_prefs.get("weekly_pulse_time", "18:00:00")
                })
            
            return dict(timezone_groups)
            
        except Exception as e:
            logger.error(f"Error getting timezone analysis: {e}")
            return {}
    
    async def _cleanup_old_timezone_jobs(self):
        """Remove old timezone-specific jobs"""
        for job_id in list(self.active_timezone_jobs):
            try:
                self.scheduler.remove_job(job_id)
                self.active_timezone_jobs.discard(job_id)
            except Exception as e:
                logger.warning(f"Error removing job {job_id}: {e}")
    
    async def _create_timezone_jobs(self, timezone_analysis: Dict[str, List[Dict[str, Any]]]):
        """Create specific jobs for each timezone/time combination"""
        for tz_time_key, users in timezone_analysis.items():
            try:
                # Parse the key to get timezone and time
                tz_name, time_str = tz_time_key.split("_", 1)
                user_count = len(users)
                
                # Parse the time
                try:
                    hour, minute, _ = time_str.split(":")
                    briefing_hour = int(hour)
                    briefing_minute = int(minute)
                except:
                    briefing_hour, briefing_minute = 8, 0
                
                # Convert to UTC for scheduling
                utc_hour, utc_minute = self._convert_to_utc(tz_name, briefing_hour, briefing_minute)
                
                # Create daily briefing job for this timezone/time combination
                job_id = f"briefing_{tz_name}_{briefing_hour:02d}{briefing_minute:02d}"
                
                self.scheduler.add_job(
                    func=self._run_timezone_specific_briefings,
                    args=[tz_time_key, users],
                    trigger=CronTrigger(hour=utc_hour, minute=utc_minute),
                    id=job_id,
                    name=f"Briefings for {user_count} users in {tz_name} at {briefing_hour:02d}:{briefing_minute:02d}",
                    replace_existing=True,
                )
                
                self.active_timezone_jobs.add(job_id)
                
                logger.info(f"Created job {job_id} for {user_count} users in {tz_name} at {briefing_hour:02d}:{briefing_minute:02d} (UTC {utc_hour:02d}:{utc_minute:02d})")
                
                # Create weekly pulse jobs for users who have it enabled
                weekly_users = [u for u in users if u.get("weekly_pulse_enabled")]
                if weekly_users:
                    await self._create_weekly_pulse_jobs(tz_time_key, weekly_users)
                
            except Exception as e:
                logger.error(f"Error creating job for {tz_time_key}: {e}")
    
    async def _create_weekly_pulse_jobs(self, tz_time_key: str, users: List[Dict[str, Any]]):
        """Create weekly pulse jobs for users in a timezone"""
        try:
            # Group users by their weekly pulse day and time
            pulse_groups = defaultdict(list)
            
            for user in users:
                pulse_day = user.get("weekly_pulse_day", 0)  # 0 = Sunday
                pulse_time = user.get("weekly_pulse_time", "18:00:00")
                pulse_key = f"{pulse_day}_{pulse_time}"
                pulse_groups[pulse_key].append(user)
            
            for pulse_key, pulse_users in pulse_groups.items():
                try:
                    pulse_day, pulse_time_str = pulse_key.split("_", 1)
                    pulse_day = int(pulse_day)
                    
                    # Parse pulse time
                    try:
                        hour, minute, _ = pulse_time_str.split(":")
                        pulse_hour = int(hour)
                        pulse_minute = int(minute)
                    except:
                        pulse_hour, pulse_minute = 18, 0
                    
                    # Get timezone from first user
                    tz_name = pulse_users[0]["timezone"]
                    
                    # Convert to UTC
                    utc_hour, utc_minute = self._convert_to_utc(tz_name, pulse_hour, pulse_minute)
                    
                    # Convert day (0=Sunday) to cron format (0=Monday, 6=Sunday)
                    cron_day = (pulse_day + 6) % 7
                    
                    job_id = f"pulse_{tz_name}_{pulse_day}_{pulse_hour:02d}{pulse_minute:02d}"
                    
                    self.scheduler.add_job(
                        func=self._run_timezone_specific_pulse,
                        args=[tz_time_key, pulse_users],
                        trigger=CronTrigger(day_of_week=cron_day, hour=utc_hour, minute=utc_minute),
                        id=job_id,
                        name=f"Weekly pulse for {len(pulse_users)} users in {tz_name}",
                        replace_existing=True,
                    )
                    
                    self.active_timezone_jobs.add(job_id)
                    
                    logger.info(f"Created weekly pulse job {job_id} for {len(pulse_users)} users")
                    
                except Exception as e:
                    logger.error(f"Error creating weekly pulse job for {pulse_key}: {e}")
                    
        except Exception as e:
            logger.error(f"Error creating weekly pulse jobs: {e}")
    
    def _convert_to_utc(self, timezone_name: str, hour: int, minute: int) -> tuple[int, int]:
        """Convert local time to UTC for scheduling"""
        try:
            # Create timezone object
            local_tz = pytz.timezone(timezone_name)
            
            # Create a datetime object for today at the specified time
            now = datetime.now()
            local_dt = local_tz.localize(datetime(now.year, now.month, now.day, hour, minute))
            
            # Convert to UTC
            utc_dt = local_dt.utctimetuple()
            
            return utc_dt.tm_hour, utc_dt.tm_min
            
        except Exception as e:
            logger.warning(f"Error converting {timezone_name} time to UTC: {e}, using original time")
            return hour, minute
    
    async def _run_timezone_specific_briefings(self, tz_time_key: str, users: List[Dict[str, Any]]):
        """Run briefings for users in a specific timezone at their preferred time"""
        try:
            logger.info(f"Running briefings for {len(users)} users with key {tz_time_key}")
            
            # Create a mock user list in the format expected by the worker scheduler
            formatted_users = []
            for user in users:
                # Get full user info from auth.users table
                try:
                    user_response = await self.supabase.table("users").select(
                        "id, email, name"
                    ).eq("id", user["user_id"]).execute()
                    
                    if user_response.data:
                        user_data = user_response.data[0]
                        user_data.update({
                            "briefing_preferences": {
                                "daily_briefing_enabled": True,
                                "daily_briefing_time": user["briefing_time"],
                                "daily_briefing_timezone": user["timezone"],
                                "daily_briefing_email_enabled": True
                            },
                            "timezone": user["timezone"]
                        })
                        formatted_users.append(user_data)
                        
                except Exception as e:
                    logger.warning(f"Error getting user info for {user['user_id']}: {e}")
            
            # Process briefings using the existing worker scheduler logic
            results = []
            for formatted_user in formatted_users:
                try:
                    result = await self.worker_scheduler._process_daily_briefing(formatted_user)
                    results.append(result)
                    
                    # Log result
                    logger.info(
                        f"Briefing processed for user {formatted_user['id']}: "
                        f"{'Success' if result.success else 'Failed - ' + str(result.error)}"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process briefing for user {formatted_user.get('id')}: {e}")
            
            # Log summary
            success_count = sum(1 for r in results if r.success)
            failure_count = len(results) - success_count
            
            logger.info(
                f"Timezone-specific briefing completed for {tz_time_key}: "
                f"{success_count} success, {failure_count} failures"
            )
            
        except Exception as e:
            logger.error(f"Error running timezone-specific briefings for {tz_time_key}: {e}")
    
    async def _run_timezone_specific_pulse(self, tz_time_key: str, users: List[Dict[str, Any]]):
        """Run weekly pulse for users in a specific timezone"""
        try:
            logger.info(f"Running weekly pulse for {len(users)} users with key {tz_time_key}")
            
            # Similar logic as briefings but for weekly pulse
            formatted_users = []
            for user in users:
                try:
                    user_response = await self.supabase.table("users").select(
                        "id, email, name"
                    ).eq("id", user["user_id"]).execute()
                    
                    if user_response.data:
                        user_data = user_response.data[0]
                        user_data.update({
                            "pulse_preferences": {
                                "weekly_pulse_enabled": True,
                                "weekly_pulse_day": user.get("weekly_pulse_day", 0),
                                "weekly_pulse_time": user.get("weekly_pulse_time", "18:00:00"),
                                "weekly_pulse_email_enabled": True
                            },
                            "timezone": user["timezone"]
                        })
                        formatted_users.append(user_data)
                        
                except Exception as e:
                    logger.warning(f"Error getting user info for pulse {user['user_id']}: {e}")
            
            # Process weekly pulse using existing logic
            results = []
            for formatted_user in formatted_users:
                try:
                    result = await self.worker_scheduler._process_weekly_pulse(formatted_user)
                    results.append(result)
                    
                    logger.info(
                        f"Weekly pulse processed for user {formatted_user['id']}: "
                        f"{'Success' if result.success else 'Failed - ' + str(result.error)}"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process weekly pulse for user {formatted_user.get('id')}: {e}")
            
            # Log summary
            success_count = sum(1 for r in results if r.success)
            failure_count = len(results) - success_count
            
            logger.info(
                f"Timezone-specific weekly pulse completed for {tz_time_key}: "
                f"{success_count} success, {failure_count} failures"
            )
            
        except Exception as e:
            logger.error(f"Error running timezone-specific weekly pulse for {tz_time_key}: {e}")


# Global scheduler instance
_timezone_scheduler: Optional['TimezoneAwareScheduler'] = None

def get_timezone_scheduler() -> TimezoneAwareScheduler:
    """Get global timezone-aware scheduler instance"""
    global _timezone_scheduler
    if _timezone_scheduler is None:
        _timezone_scheduler = TimezoneAwareScheduler()
    return _timezone_scheduler