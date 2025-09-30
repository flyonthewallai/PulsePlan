"""
Time discretization and indexing for the scheduler.

Provides efficient mapping between continuous time and discrete scheduling slots.
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple, Set, Optional
import pytz
from ..core.domain import BusyEvent, Preferences
from ...core.utils.timezone_utils import get_timezone_manager


class TimeIndex:
    """
    Manages discretized time slots for scheduling optimization.
    
    Converts continuous time into discrete slots of fixed granularity
    (e.g., 15 or 30 minutes) within a specified horizon.
    """
    
    def __init__(
        self, 
        timezone: str, 
        start_dt: datetime, 
        end_dt: datetime, 
        granularity_minutes: int = 30
    ):
        """
        Initialize time index with discretized slots.
        
        Args:
            timezone: Target timezone (e.g., 'America/New_York')
            start_dt: Start of scheduling horizon (timezone-aware)
            end_dt: End of scheduling horizon (timezone-aware)
            granularity_minutes: Slot duration in minutes (15 or 30)
        """
        self.timezone = pytz.timezone(timezone)
        self.granularity_minutes = granularity_minutes
        self.granularity_delta = timedelta(minutes=granularity_minutes)
        self.timezone_manager = get_timezone_manager()

        # Ensure timezone-aware datetimes using timezone manager
        start_dt = self.timezone_manager.ensure_timezone_aware(start_dt, self.timezone)
        end_dt = self.timezone_manager.ensure_timezone_aware(end_dt, self.timezone)
            
        self.start_dt = start_dt
        self.end_dt = end_dt
        
        # Generate all time slots
        self.slots = self._generate_slots()
        
        # Create bidirectional mapping
        self.slot_to_index = {slot: idx for idx, slot in enumerate(self.slots)}
        self.index_to_slot = {idx: slot for idx, slot in enumerate(self.slots)}
        
    def _generate_slots(self) -> List[datetime]:
        """Generate all discrete time slots within the horizon."""
        slots = []
        current = self.start_dt
        
        while current < self.end_dt:
            slots.append(current)
            current += self.granularity_delta
            
        return slots
    
    def datetime_to_index(self, dt: datetime) -> Optional[int]:
        """
        Convert datetime to slot index.
        
        Args:
            dt: Datetime to convert
            
        Returns:
            Slot index or None if outside horizon
        """
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
            
        # Round down to nearest slot boundary
        slot_dt = self._round_to_slot(dt)
        return self.slot_to_index.get(slot_dt)
    
    def index_to_datetime(self, index: int) -> Optional[datetime]:
        """Convert slot index to datetime."""
        return self.index_to_slot.get(index)
    
    def _round_to_slot(self, dt: datetime) -> datetime:
        """Round datetime down to nearest slot boundary."""
        # Get minutes since start of day
        minutes_since_start = (dt - self.start_dt).total_seconds() / 60
        
        # Round down to granularity boundary
        slot_minutes = int(minutes_since_start // self.granularity_minutes) * self.granularity_minutes
        
        return self.start_dt + timedelta(minutes=slot_minutes)
    
    def window_to_indices(
        self, 
        start: datetime, 
        end: datetime, 
        inclusive_end: bool = False
    ) -> List[int]:
        """
        Convert time window to list of slot indices.
        
        Args:
            start: Window start time
            end: Window end time  
            inclusive_end: Whether to include end slot
            
        Returns:
            List of slot indices covering the window
        """
        start_idx = self.datetime_to_index(start)
        end_idx = self.datetime_to_index(end)
        
        if start_idx is None or end_idx is None:
            return []
        
        if inclusive_end:
            return list(range(start_idx, end_idx + 1))
        else:
            return list(range(start_idx, end_idx))
    
    def indices_to_window(self, indices: List[int]) -> Tuple[datetime, datetime]:
        """
        Convert list of slot indices to time window.
        
        Args:
            indices: List of consecutive slot indices
            
        Returns:
            (start_time, end_time) of the window
        """
        if not indices:
            raise ValueError("Cannot convert empty indices list")
            
        min_idx = min(indices)
        max_idx = max(indices)
        
        start_time = self.index_to_datetime(min_idx)
        end_time = self.index_to_datetime(max_idx) + self.granularity_delta
        
        return start_time, end_time
    
    def get_day_indices(self, date: datetime) -> List[int]:
        """Get all slot indices for a specific day."""
        # Start of day in user timezone
        day_start = self.timezone.localize(
            datetime.combine(date.date(), time.min)
        )
        day_end = day_start + timedelta(days=1)
        
        return self.window_to_indices(day_start, day_end)
    
    def get_workday_indices(self, date: datetime, prefs: Preferences) -> List[int]:
        """
        Get slot indices for workday hours on a specific day.
        
        Args:
            date: Target date
            prefs: User preferences with workday bounds
            
        Returns:
            List of slot indices within workday hours
        """
        # Parse workday times
        start_time = time.fromisoformat(prefs.workday_start)
        end_time = time.fromisoformat(prefs.workday_end)
        
        # Create datetime bounds
        day_start = self.timezone.localize(
            datetime.combine(date.date(), start_time)
        )
        day_end = self.timezone.localize(
            datetime.combine(date.date(), end_time)
        )
        
        return self.window_to_indices(day_start, day_end)
    
    def filter_busy_slots(self, busy_events: List[BusyEvent]) -> Set[int]:
        """
        Get set of slot indices blocked by busy events.
        
        Args:
            busy_events: List of calendar events
            
        Returns:
            Set of blocked slot indices
        """
        blocked_slots = set()
        
        for event in busy_events:
            if event.hard:  # Only hard events block scheduling
                event_indices = self.window_to_indices(
                    event.start, 
                    event.end, 
                    inclusive_end=True
                )
                blocked_slots.update(event_indices)
        
        return blocked_slots
    
    def get_free_slots(
        self, 
        busy_events: List[BusyEvent], 
        prefs: Preferences,
        dates: Optional[List[datetime]] = None
    ) -> List[int]:
        """
        Get all free slot indices within workday hours.
        
        Args:
            busy_events: Calendar events that block slots
            prefs: User preferences
            dates: Specific dates to check (default: all days in horizon)
            
        Returns:
            List of available slot indices
        """
        if dates is None:
            # Get all unique dates in horizon
            dates = list(set(slot.date() for slot in self.slots))
        
        free_slots = []
        blocked_slots = self.filter_busy_slots(busy_events)
        
        for date in dates:
            day_slots = self.get_workday_indices(
                datetime.combine(date, time.min), 
                prefs
            )
            
            # Filter out blocked slots
            available_slots = [
                slot_idx for slot_idx in day_slots 
                if slot_idx not in blocked_slots
            ]
            
            free_slots.extend(available_slots)
        
        return sorted(free_slots)
    
    def get_contiguous_blocks(self, slot_indices: List[int]) -> List[List[int]]:
        """
        Group consecutive slot indices into contiguous blocks.
        
        Args:
            slot_indices: List of slot indices
            
        Returns:
            List of contiguous blocks (each block is a list of consecutive indices)
        """
        if not slot_indices:
            return []
        
        sorted_indices = sorted(slot_indices)
        blocks = []
        current_block = [sorted_indices[0]]
        
        for i in range(1, len(sorted_indices)):
            if sorted_indices[i] == sorted_indices[i-1] + 1:
                # Consecutive slot
                current_block.append(sorted_indices[i])
            else:
                # Gap found, start new block
                blocks.append(current_block)
                current_block = [sorted_indices[i]]
        
        # Add final block
        blocks.append(current_block)
        
        return blocks
    
    def block_duration_minutes(self, block_indices: List[int]) -> int:
        """Get duration of a contiguous block in minutes."""
        return len(block_indices) * self.granularity_minutes
    
    def get_slot_context(self, slot_idx: int) -> Dict:
        """
        Get contextual information about a time slot.
        
        Args:
            slot_idx: Slot index
            
        Returns:
            Dictionary with slot context (hour, day_of_week, etc.)
        """
        slot_dt = self.index_to_datetime(slot_idx)
        if slot_dt is None:
            return {}
            
        return {
            'datetime': slot_dt,
            'hour': slot_dt.hour,
            'minute': slot_dt.minute,
            'day_of_week': slot_dt.weekday(),  # Monday=0, Sunday=6
            'is_weekend': slot_dt.weekday() >= 5,
            'is_morning': slot_dt.hour < 12,
            'is_afternoon': 12 <= slot_dt.hour < 18,
            'is_evening': slot_dt.hour >= 18,
            'week_of_year': slot_dt.isocalendar()[1]
        }
    
    @property
    def total_slots(self) -> int:
        """Total number of slots in the time horizon."""
        return len(self.slots)
    
    @property
    def horizon_days(self) -> int:
        """Number of days in the scheduling horizon."""
        return (self.end_dt - self.start_dt).days
    
    def __len__(self) -> int:
        """Return total number of slots."""
        return self.total_slots
    
    def __repr__(self) -> str:
        """String representation of the time index."""
        return (
            f"TimeIndex(start={self.start_dt}, end={self.end_dt}, "
            f"granularity={self.granularity_minutes}min, "
            f"slots={self.total_slots})"
        )
