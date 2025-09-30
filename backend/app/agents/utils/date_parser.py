"""
Natural language date parsing utility for agent todo creation.

Handles various date formats and converts them to timezone-aware datetime objects.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pytz
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta

from ...core.utils.timezone_utils import get_timezone_manager


class DateParsingError(Exception):
    """Raised when date parsing fails"""
    pass


class NaturalDateParser:
    """
    Parses natural language dates into timezone-aware datetime objects.
    
    Supports various formats:
    - Relative dates: "tomorrow", "next week", "in 2 hours"
    - Specific dates: "Friday at 3pm", "January 15th", "Dec 25"
    - Time expressions: "morning", "afternoon", "evening", "tonight"
    """
    
    def __init__(self):
        self.timezone_manager = get_timezone_manager()
        
        # Common time mappings
        self.time_mappings = {
            'morning': 9,
            'afternoon': 14,
            'evening': 18,
            'night': 20,
            'tonight': 20,
            'noon': 12,
            'midnight': 0
        }
        
        # Relative day mappings
        self.relative_days = {
            'today': 0,
            'tomorrow': 1,
            'yesterday': -1,
            'day after tomorrow': 2
        }
        
        # Weekday mappings
        self.weekdays = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }

    async def parse_date(
        self, 
        date_str: str, 
        user_id: str, 
        user_timezone: Optional[str] = None
    ) -> Optional[datetime]:
        """
        Parse natural language date string into timezone-aware datetime.
        
        Args:
            date_str: Natural language date string
            user_id: User ID for timezone lookup
            user_timezone: Optional user timezone override
            
        Returns:
            Timezone-aware datetime object or None if parsing fails
        """
        if not date_str or not date_str.strip():
            return None
            
        date_str = date_str.lower().strip()
        
        try:
            # Get user timezone
            if user_timezone:
                user_tz = pytz.timezone(user_timezone)
            else:
                user_tz = await self.timezone_manager.get_user_timezone(user_id)
            
            # Get current time in user's timezone
            now = datetime.now(user_tz)
            
            # Try different parsing strategies
            parsed_date = (
                self._parse_relative_date(date_str, now) or
                self._parse_weekday_date(date_str, now) or
                self._parse_specific_date(date_str, user_tz) or
                self._parse_time_expression(date_str, now) or
                self._parse_duration_from_now(date_str, now) or
                self._parse_with_dateutil(date_str, user_tz)
            )
            
            if parsed_date:
                # Ensure timezone awareness
                if parsed_date.tzinfo is None:
                    parsed_date = user_tz.localize(parsed_date)
                elif parsed_date.tzinfo != user_tz:
                    parsed_date = parsed_date.astimezone(user_tz)
                
                # Convert to UTC for storage
                parsed_date = parsed_date.astimezone(pytz.UTC)
                    
                return parsed_date
                
        except Exception as e:
            # Log error but don't raise - return None for graceful fallback
            print(f"Date parsing error for '{date_str}': {e}")
            
        return None

    def _parse_relative_date(self, date_str: str, now: datetime) -> Optional[datetime]:
        """Parse relative dates like 'today', 'tomorrow', 'yesterday'"""
        for relative_word, days_offset in self.relative_days.items():
            if relative_word in date_str:
                target_date = now + timedelta(days=days_offset)
                
                # Extract time if specified
                time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', date_str)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    am_pm = time_match.group(3)
                    
                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                        
                    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Check for time words
                for time_word, default_hour in self.time_mappings.items():
                    if time_word in date_str:
                        return target_date.replace(hour=default_hour, minute=0, second=0, microsecond=0)
                
                # Default to end of day for due dates
                return target_date.replace(hour=23, minute=59, second=0, microsecond=0)
                
        return None

    def _parse_weekday_date(self, date_str: str, now: datetime) -> Optional[datetime]:
        """Parse weekday references like 'Friday', 'next Monday'"""
        is_next_week = 'next' in date_str
        
        for weekday_name, weekday_num in self.weekdays.items():
            if weekday_name in date_str:
                days_ahead = weekday_num - now.weekday()
                
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                    
                if is_next_week:
                    days_ahead += 7
                    
                target_date = now + timedelta(days=days_ahead)
                
                # Extract time if specified
                time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', date_str)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    am_pm = time_match.group(3)
                    
                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                        
                    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Check for time words
                for time_word, default_hour in self.time_mappings.items():
                    if time_word in date_str:
                        return target_date.replace(hour=default_hour, minute=0, second=0, microsecond=0)
                
                # Default to end of day
                return target_date.replace(hour=23, minute=59, second=0, microsecond=0)
                
        return None

    def _parse_specific_date(self, date_str: str, user_tz: pytz.BaseTzInfo) -> Optional[datetime]:
        """Parse specific dates like 'January 15th', 'Dec 25'"""
        # Month patterns
        month_patterns = [
            r'(january|jan)\s+(\d{1,2})',
            r'(february|feb)\s+(\d{1,2})',
            r'(march|mar)\s+(\d{1,2})',
            r'(april|apr)\s+(\d{1,2})',
            r'(may)\s+(\d{1,2})',
            r'(june|jun)\s+(\d{1,2})',
            r'(july|jul)\s+(\d{1,2})',
            r'(august|aug)\s+(\d{1,2})',
            r'(september|sep|sept)\s+(\d{1,2})',
            r'(october|oct)\s+(\d{1,2})',
            r'(november|nov)\s+(\d{1,2})',
            r'(december|dec)\s+(\d{1,2})'
        ]
        
        month_names = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        for i, pattern in enumerate(month_patterns):
            match = re.search(pattern, date_str)
            if match:
                month = i + 1
                day = int(match.group(2))
                
                # Determine year (current year or next year if date has passed)
                now = datetime.now(user_tz)
                year = now.year
                
                try:
                    target_date = user_tz.localize(datetime(year, month, day, 23, 59))
                    if target_date < now:
                        target_date = user_tz.localize(datetime(year + 1, month, day, 23, 59))
                    return target_date
                except ValueError:
                    # Invalid date (e.g., Feb 30)
                    continue
                    
        return None

    def _parse_time_expression(self, date_str: str, now: datetime) -> Optional[datetime]:
        """Parse time expressions like 'this morning', 'tonight', 'end of week'"""
        if 'this' in date_str:
            for time_word, default_hour in self.time_mappings.items():
                if time_word in date_str:
                    return now.replace(hour=default_hour, minute=0, second=0, microsecond=0)
        
        # Handle "tonight" specifically
        if 'tonight' in date_str:
            return now.replace(hour=20, minute=0, second=0, microsecond=0)
            
        # Handle "end of week" (Friday evening)
        if 'end of week' in date_str:
            days_until_friday = (4 - now.weekday()) % 7
            if days_until_friday == 0 and now.hour >= 17:  # It's Friday evening already
                days_until_friday = 7  # Next Friday
            target_date = now + timedelta(days=days_until_friday)
            return target_date.replace(hour=17, minute=0, second=0, microsecond=0)
            
        # Handle "next week" (Monday of next week)
        if 'next week' in date_str:
            days_until_next_monday = (7 - now.weekday()) % 7
            if days_until_next_monday == 0:  # It's Monday
                days_until_next_monday = 7
            target_date = now + timedelta(days=days_until_next_monday)
            return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    
        return None

    def _parse_duration_from_now(self, date_str: str, now: datetime) -> Optional[datetime]:
        """Parse duration expressions like 'in 2 hours', 'in 30 minutes'"""
        # Pattern for "in X hours/minutes/days"
        duration_pattern = r'in\s+(\d+)\s+(hour|hours|minute|minutes|day|days|week|weeks)'
        match = re.search(duration_pattern, date_str)
        
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit.startswith('hour'):
                return now + timedelta(hours=amount)
            elif unit.startswith('minute'):
                return now + timedelta(minutes=amount)
            elif unit.startswith('day'):
                return now + timedelta(days=amount)
            elif unit.startswith('week'):
                return now + timedelta(weeks=amount)
                
        return None

    def _parse_with_dateutil(self, date_str: str, user_tz: pytz.BaseTzInfo) -> Optional[datetime]:
        """Fallback parsing using dateutil library"""
        try:
            # Remove common words that might confuse dateutil
            cleaned_str = re.sub(r'\b(due|by|on|at)\b', '', date_str).strip()
            
            if not cleaned_str:
                return None
                
            parsed = dateutil_parser.parse(cleaned_str, fuzzy=True)
            
            # If no timezone info, assume user's timezone
            if parsed.tzinfo is None:
                parsed = user_tz.localize(parsed)
            else:
                parsed = parsed.astimezone(user_tz)
                
            return parsed
            
        except (ValueError, TypeError):
            return None


# Global instance
_date_parser = None

def get_date_parser() -> NaturalDateParser:
    """Get global date parser instance"""
    global _date_parser
    if _date_parser is None:
        _date_parser = NaturalDateParser()
    return _date_parser
