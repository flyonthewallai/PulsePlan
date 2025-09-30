"""
Comprehensive timezone utilities for the scheduler.

Provides consistent timezone handling across the scheduling system,
integrating with user-specific timezone settings from the database.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import pytz
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class TimezoneManager:
    """
    Centralized timezone management for scheduling operations.

    Handles user-specific timezones from the users table and provides
    consistent datetime conversion utilities.
    """

    def __init__(self):
        """Initialize timezone manager."""
        self._timezone_cache: Dict[str, Any] = {}
        self._default_timezone = pytz.UTC

    async def get_user_timezone(self, user_id: str, db_session=None) -> pytz.BaseTzInfo:
        """
        Get user-specific timezone from users table.

        Args:
            user_id: User identifier
            db_session: Database session (optional)

        Returns:
            User's timezone or UTC if not found
        """
        # Check cache first
        if user_id in self._timezone_cache:
            return self._timezone_cache[user_id]

        # Query users table for timezone
        try:
            # Use Supabase client to get user timezone
            from ...config.database.supabase import get_supabase
            supabase = get_supabase()
            
            result = supabase.table("users").select("timezone").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                user_tz_str = result.data[0].get("timezone")
            else:
                user_tz_str = None

            if user_tz_str:
                try:
                    # Try pytz first (more comprehensive)
                    user_tz = pytz.timezone(user_tz_str)
                except pytz.UnknownTimeZoneError:
                    try:
                        # Fall back to zoneinfo
                        user_tz = ZoneInfo(user_tz_str)
                    except Exception:
                        logger.warning(f"Unknown timezone '{user_tz_str}' for user {user_id}, using UTC")
                        user_tz = self._default_timezone
            else:
                # Default to Mountain Time (Denver) for now since user mentioned 4am issue
                user_tz = pytz.timezone("America/Denver")
                logger.info(f"No timezone set for user {user_id}, defaulting to America/Denver")

            # Cache the result
            self._timezone_cache[user_id] = user_tz
            return user_tz

        except Exception as e:
            logger.error(f"Failed to get timezone for user {user_id}: {e}")
            # Default to Mountain Time for now
            user_tz = pytz.timezone("America/Denver")
            self._timezone_cache[user_id] = user_tz
            return user_tz

    def ensure_timezone_aware(
        self,
        dt: datetime,
        default_tz: Optional[Union[str, pytz.BaseTzInfo]] = None
    ) -> datetime:
        """
        Ensure datetime is timezone-aware.

        Args:
            dt: Datetime to check
            default_tz: Default timezone if dt is naive

        Returns:
            Timezone-aware datetime
        """
        if dt.tzinfo is not None:
            return dt

        # Handle default timezone
        if default_tz is None:
            tz = self._default_timezone
        elif isinstance(default_tz, str):
            try:
                tz = pytz.timezone(default_tz)
            except pytz.UnknownTimeZoneError:
                try:
                    tz = ZoneInfo(default_tz)
                except Exception:
                    logger.warning(f"Unknown timezone '{default_tz}', using UTC")
                    tz = self._default_timezone
        else:
            tz = default_tz

        return dt.replace(tzinfo=tz) if hasattr(tz, 'zone') else tz.localize(dt)

    def convert_to_user_timezone(
        self,
        dt: datetime,
        user_tz: Union[str, pytz.BaseTzInfo]
    ) -> datetime:
        """
        Convert datetime to user's timezone.

        Args:
            dt: Datetime to convert
            user_tz: Target user timezone

        Returns:
            Datetime in user's timezone
        """
        # Ensure input is timezone-aware
        if dt.tzinfo is None:
            dt = self.ensure_timezone_aware(dt)

        # Handle user timezone
        if isinstance(user_tz, str):
            try:
                target_tz = pytz.timezone(user_tz)
            except pytz.UnknownTimeZoneError:
                try:
                    target_tz = ZoneInfo(user_tz)
                except Exception:
                    logger.warning(f"Unknown timezone '{user_tz}', using UTC")
                    target_tz = self._default_timezone
        else:
            target_tz = user_tz

        return dt.astimezone(target_tz)

    def normalize_datetime_comparison(
        self,
        dt1: datetime,
        dt2: datetime,
        default_tz: Optional[Union[str, pytz.BaseTzInfo]] = None
    ) -> tuple[datetime, datetime]:
        """
        Normalize two datetimes for safe comparison.

        Args:
            dt1: First datetime
            dt2: Second datetime
            default_tz: Default timezone for naive datetimes

        Returns:
            Tuple of normalized datetimes
        """
        # Ensure both are timezone-aware
        dt1_aware = self.ensure_timezone_aware(dt1, default_tz)
        dt2_aware = self.ensure_timezone_aware(dt2, default_tz)

        # Convert to UTC for comparison
        dt1_utc = dt1_aware.astimezone(self._default_timezone)
        dt2_utc = dt2_aware.astimezone(self._default_timezone)

        return dt1_utc, dt2_utc

    def get_timezone_offset(self, tz: Union[str, pytz.BaseTzInfo], dt: Optional[datetime] = None) -> timedelta:
        """
        Get timezone offset from UTC.

        Args:
            tz: Timezone
            dt: Reference datetime (defaults to now)

        Returns:
            Timezone offset
        """
        if dt is None:
            dt = datetime.now()

        if isinstance(tz, str):
            try:
                tz_obj = pytz.timezone(tz)
            except pytz.UnknownTimeZoneError:
                try:
                    tz_obj = ZoneInfo(tz)
                except Exception:
                    return timedelta(0)
        else:
            tz_obj = tz

        # Get localized datetime
        if hasattr(tz_obj, 'localize'):
            localized_dt = tz_obj.localize(dt.replace(tzinfo=None))
        else:
            localized_dt = dt.replace(tzinfo=tz_obj)

        # Calculate offset from UTC
        utc_dt = localized_dt.astimezone(self._default_timezone)
        return localized_dt.utcoffset() or timedelta(0)

    def is_business_hours(
        self,
        dt: datetime,
        user_tz: Union[str, pytz.BaseTzInfo],
        start_hour: int = 9,
        end_hour: int = 17
    ) -> bool:
        """
        Check if datetime falls within business hours in user's timezone.

        Args:
            dt: Datetime to check
            user_tz: User's timezone
            start_hour: Business day start hour
            end_hour: Business day end hour

        Returns:
            True if within business hours
        """
        user_dt = self.convert_to_user_timezone(dt, user_tz)
        return start_hour <= user_dt.hour < end_hour and user_dt.weekday() < 5

    def get_timezone_info(self, tz_str: str) -> Dict[str, Any]:
        """
        Get comprehensive timezone information.

        Args:
            tz_str: Timezone string

        Returns:
            Dictionary with timezone info
        """
        try:
            tz = pytz.timezone(tz_str)
            now = datetime.now()
            localized_now = tz.localize(now)

            return {
                'timezone': tz_str,
                'offset': self.get_timezone_offset(tz, now),
                'dst_active': bool(localized_now.dst()),
                'utc_offset_hours': localized_now.utcoffset().total_seconds() / 3600,
                'display_name': str(tz),
                'is_dst': localized_now.dst() != timedelta(0)
            }
        except Exception as e:
            return {
                'timezone': tz_str,
                'error': str(e),
                'valid': False
            }


# Global timezone manager instance
_timezone_manager = None

def get_timezone_manager() -> TimezoneManager:
    """Get global timezone manager instance."""
    global _timezone_manager
    if _timezone_manager is None:
        _timezone_manager = TimezoneManager()
    return _timezone_manager


def ensure_timezone_aware(dt: datetime, default_tz: str = "UTC") -> datetime:
    """Convenience function to ensure datetime is timezone-aware."""
    return get_timezone_manager().ensure_timezone_aware(dt, default_tz)


def safe_datetime_comparison(dt1: datetime, dt2: datetime, default_tz: str = "UTC") -> tuple[datetime, datetime]:
    """Convenience function for safe datetime comparison."""
    return get_timezone_manager().normalize_datetime_comparison(dt1, dt2, default_tz)