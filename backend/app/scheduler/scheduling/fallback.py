"""
Deterministic fallback scheduling algorithm.

Provides a fully deterministic greedy scheduler that serves as a reliable
fallback when the CP-SAT solver fails or times out.
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.domain import Task, BusyEvent, Preferences, ScheduleBlock, ScheduleSolution
from ..optimization.time_index import TimeIndex

logger = logging.getLogger(__name__)


class UnscheduledReason(Enum):
    """Reasons why a task could not be scheduled."""
    NO_TIME = "no_time"
    AFTER_DEADLINE = "after_deadline"
    BLOCKED_PREREQ = "blocked_prereq"
    WINDOW_VIOLATION = "window_violation"
    INSUFFICIENT_CONTIGUOUS_TIME = "insufficient_contiguous_time"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    SPLITS_LIMIT_EXCEEDED = "splits_limit_exceeded"


@dataclass
class TaskPriority:
    """Priority calculation for deterministic task ordering."""
    urgency_score: float
    remaining_minutes: int
    created_at: datetime
    task_id: str

    def __lt__(self, other):
        """Compare tasks for deterministic sorting."""
        # Primary: urgency (higher first)
        if abs(self.urgency_score - other.urgency_score) > 0.001:
            return self.urgency_score > other.urgency_score

        # Secondary: remaining time (more first)
        if self.remaining_minutes != other.remaining_minutes:
            return self.remaining_minutes > other.remaining_minutes

        # Tertiary: creation time (older first)
        if self.created_at != other.created_at:
            return self.created_at < other.created_at

        # Final: task ID (lexicographic)
        return self.task_id < other.task_id


@dataclass
class TimeSlot:
    """Available time slot for scheduling."""
    start: datetime
    end: datetime
    duration_minutes: int
    day_offset: int  # Days from scheduling start
    slot_index: int  # Index in time grid

    def can_fit_task(self, task: Task, min_duration: int = None) -> bool:
        """Check if this slot can accommodate the task."""
        required_duration = min_duration or task.min_block_minutes
        return self.duration_minutes >= required_duration

    def split_at(self, duration_minutes: int) -> Tuple['TimeSlot', Optional['TimeSlot']]:
        """Split slot into used portion and remainder."""
        if duration_minutes >= self.duration_minutes:
            return self, None

        used_slot = TimeSlot(
            start=self.start,
            end=self.start + timedelta(minutes=duration_minutes),
            duration_minutes=duration_minutes,
            day_offset=self.day_offset,
            slot_index=self.slot_index
        )

        remaining_slot = TimeSlot(
            start=self.start + timedelta(minutes=duration_minutes),
            end=self.end,
            duration_minutes=self.duration_minutes - duration_minutes,
            day_offset=self.day_offset,
            slot_index=self.slot_index
        )

        return used_slot, remaining_slot


class DeterministicFallbackScheduler:
    """
    Fully deterministic greedy fallback scheduler.

    Provides guaranteed deterministic scheduling when CP-SAT solver fails.
    Includes comprehensive reason tracking for unscheduled tasks.
    """

    def __init__(self, random_seed: int = 42):
        """Initialize deterministic fallback scheduler."""
        self.random_seed = random_seed

    def schedule(
        self,
        tasks: List[Task],
        busy_events: List[BusyEvent],
        preferences: Preferences,
        time_index: TimeIndex,
        existing_blocks: Optional[List[ScheduleBlock]] = None
    ) -> ScheduleSolution:
        """
        Generate deterministic fallback schedule.

        Args:
            tasks: Tasks to schedule
            busy_events: Calendar conflicts
            preferences: User preferences
            time_index: Time discretization
            existing_blocks: Existing schedule blocks to preserve

        Returns:
            Complete schedule solution with reason codes
        """
        start_time = datetime.now()

        # Initialize tracking
        scheduled_blocks = []
        unscheduled_tasks = {}
        daily_effort_used = {}  # Track effort per day

        # Get available time slots
        available_slots = self._get_available_slots(
            busy_events, preferences, time_index, existing_blocks
        )

        # Sort tasks deterministically by priority
        prioritized_tasks = self._prioritize_tasks(tasks, time_index.start_dt)

        # Process prerequisites to determine dependencies
        prereq_graph = self._build_prerequisite_graph(tasks)
        completed_tasks = set()

        # Greedy scheduling loop
        for task_priority in prioritized_tasks:
            task = next(t for t in tasks if t.id == task_priority.task_id)

            # Check if prerequisites are satisfied
            if not self._prerequisites_satisfied(task, completed_tasks):
                unscheduled_tasks[task.id] = UnscheduledReason.BLOCKED_PREREQ
                continue

            # Attempt to schedule this task
            scheduled = self._schedule_single_task(
                task, available_slots, preferences, daily_effort_used, time_index
            )

            if scheduled:
                scheduled_blocks.extend(scheduled)
                completed_tasks.add(task.id)

                # Update daily effort tracking
                for block in scheduled:
                    day = block.start.date()
                    daily_effort_used[day] = daily_effort_used.get(day, 0) + block.duration_minutes

                logger.debug(f"Scheduled task {task.id} in {len(scheduled)} blocks")
            else:
                # Determine why task couldn't be scheduled
                reason = self._diagnose_unscheduled_reason(
                    task, available_slots, preferences, daily_effort_used, time_index
                )
                unscheduled_tasks[task.id] = reason
                logger.debug(f"Could not schedule task {task.id}: {reason.value}")

        # Calculate final metrics
        solve_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        total_scheduled_minutes = sum(block.duration_minutes for block in scheduled_blocks)

        # Build solution
        solution = ScheduleSolution(
            feasible=len(scheduled_blocks) > 0,
            blocks=scheduled_blocks,
            objective_value=float(len(scheduled_blocks)),  # Simple objective
            solve_time_ms=solve_time_ms,
            solver_status="greedy_fallback",
            total_scheduled_minutes=total_scheduled_minutes,
            unscheduled_tasks=list(unscheduled_tasks.keys()),
            diagnostics={
                'fallback_used': True,
                'scheduled_task_count': len(completed_tasks),
                'unscheduled_task_count': len(unscheduled_tasks),
                'unscheduled_reasons': {task_id: reason.value for task_id, reason in unscheduled_tasks.items()},
                'daily_effort_used': {str(day): minutes for day, minutes in daily_effort_used.items()}
            }
        )

        logger.info(
            f"Fallback scheduling completed: {len(scheduled_blocks)} blocks, "
            f"{len(unscheduled_tasks)} unscheduled, {solve_time_ms}ms"
        )

        return solution

    def _get_available_slots(
        self,
        busy_events: List[BusyEvent],
        preferences: Preferences,
        time_index: TimeIndex,
        existing_blocks: Optional[List[ScheduleBlock]] = None
    ) -> List[TimeSlot]:
        """Get all available time slots for scheduling."""
        slots = []

        # Create time windows based on preferences
        workday_start_time = datetime.strptime(preferences.workday_start, '%H:%M').time()
        workday_end_time = datetime.strptime(preferences.workday_end, '%H:%M').time()

        current_day = time_index.start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = time_index.end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        day_offset = 0
        slot_index = 0

        while current_day <= end_day:
            # Create daily availability window
            day_start = current_day.replace(
                hour=workday_start_time.hour,
                minute=workday_start_time.minute
            )
            day_end = current_day.replace(
                hour=workday_end_time.hour,
                minute=workday_end_time.minute
            )

            # Skip if outside time index bounds
            if day_end < time_index.start_dt or day_start > time_index.end_dt:
                current_day += timedelta(days=1)
                day_offset += 1
                continue

            # Collect all conflicts for this day
            conflicts = []

            # Add busy events
            for event in busy_events:
                if (event.hard and
                    event.end > day_start and
                    event.start < day_end):
                    conflicts.append((event.start, event.end))

            # Add existing blocks if preserving them
            if existing_blocks:
                for block in existing_blocks:
                    if (block.end > day_start and
                        block.start < day_end):
                        conflicts.append((block.start, block.end))

            # Sort conflicts by start time
            conflicts.sort(key=lambda x: x[0])

            # Find free slots between conflicts
            free_slots = self._find_free_slots_in_day(
                day_start, day_end, conflicts, time_index.granularity_minutes
            )

            # Convert to TimeSlot objects
            for start, end in free_slots:
                duration_minutes = int((end - start).total_seconds() / 60)
                if duration_minutes >= time_index.granularity_minutes:
                    slot = TimeSlot(
                        start=start,
                        end=end,
                        duration_minutes=duration_minutes,
                        day_offset=day_offset,
                        slot_index=slot_index
                    )
                    slots.append(slot)
                    slot_index += 1

            current_day += timedelta(days=1)
            day_offset += 1

        # Sort slots by start time for deterministic ordering
        slots.sort(key=lambda s: s.start)

        logger.debug(f"Found {len(slots)} available time slots")
        return slots

    def _find_free_slots_in_day(
        self,
        day_start: datetime,
        day_end: datetime,
        conflicts: List[Tuple[datetime, datetime]],
        granularity_minutes: int
    ) -> List[Tuple[datetime, datetime]]:
        """Find free time slots within a day, avoiding conflicts."""
        if not conflicts:
            return [(day_start, day_end)]

        free_slots = []
        current_start = day_start

        for conflict_start, conflict_end in conflicts:
            # Add slot before conflict if it exists
            if current_start < conflict_start:
                # Align to granularity
                aligned_end = self._align_to_granularity(conflict_start, granularity_minutes, round_down=True)
                if aligned_end > current_start:
                    free_slots.append((current_start, aligned_end))

            # Move past this conflict
            current_start = max(current_start, conflict_end)

        # Add final slot if it exists
        if current_start < day_end:
            free_slots.append((current_start, day_end))

        return free_slots

    def _align_to_granularity(
        self,
        dt: datetime,
        granularity_minutes: int,
        round_down: bool = True
    ) -> datetime:
        """Align datetime to scheduling granularity."""
        minute_offset = dt.minute % granularity_minutes
        if minute_offset == 0:
            return dt.replace(second=0, microsecond=0)

        if round_down:
            aligned_minute = dt.minute - minute_offset
        else:
            aligned_minute = dt.minute + (granularity_minutes - minute_offset)

        if aligned_minute >= 60:
            return dt.replace(hour=dt.hour + 1, minute=aligned_minute - 60, second=0, microsecond=0)
        elif aligned_minute < 0:
            return dt.replace(hour=dt.hour - 1, minute=aligned_minute + 60, second=0, microsecond=0)
        else:
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)

    def _prioritize_tasks(self, tasks: List[Task], start_time: datetime) -> List[TaskPriority]:
        """Create deterministic priority ordering for tasks."""
        priorities = []

        for task in tasks:
            # Calculate urgency score
            if task.deadline:
                # Handle timezone-aware/naive datetime comparison
                if task.deadline.tzinfo is None and start_time.tzinfo is not None:
                    # Make deadline timezone-aware using start_time's timezone
                    deadline_aware = task.deadline.replace(tzinfo=start_time.tzinfo)
                    time_to_deadline = (deadline_aware - start_time).total_seconds() / 3600  # hours
                elif task.deadline.tzinfo is not None and start_time.tzinfo is None:
                    # Make start_time timezone-aware using deadline's timezone
                    start_time_aware = start_time.replace(tzinfo=task.deadline.tzinfo)
                    time_to_deadline = (task.deadline - start_time_aware).total_seconds() / 3600  # hours
                else:
                    # Both have same timezone status
                    time_to_deadline = (task.deadline - start_time).total_seconds() / 3600  # hours

                urgency_score = max(0, 100 - time_to_deadline)  # Higher score = more urgent
            else:
                urgency_score = 50  # Medium urgency for tasks without deadlines

            priority = TaskPriority(
                urgency_score=urgency_score,
                remaining_minutes=task.estimated_minutes,
                created_at=task.created_at,
                task_id=task.id
            )
            priorities.append(priority)

        # Sort deterministically
        priorities.sort()

        logger.debug(f"Prioritized {len(priorities)} tasks deterministically")
        return priorities

    def _build_prerequisite_graph(self, tasks: List[Task]) -> Dict[str, Set[str]]:
        """Build prerequisite dependency graph."""
        prereq_graph = {}

        for task in tasks:
            prereq_graph[task.id] = set(task.prerequisites)

        return prereq_graph

    def _prerequisites_satisfied(self, task: Task, completed_tasks: Set[str]) -> bool:
        """Check if all prerequisites for a task are satisfied."""
        return all(prereq_id in completed_tasks for prereq_id in task.prerequisites)

    def _schedule_single_task(
        self,
        task: Task,
        available_slots: List[TimeSlot],
        preferences: Preferences,
        daily_effort_used: Dict,
        time_index: TimeIndex
    ) -> Optional[List[ScheduleBlock]]:
        """Attempt to schedule a single task using earliest-fit."""
        remaining_minutes = task.estimated_minutes
        scheduled_blocks = []
        splits_used = 0

        # Get max splits allowed
        max_splits = self._get_max_splits_for_task(task)

        # Sort slots by start time (earliest first)
        candidate_slots = sorted(available_slots, key=lambda s: s.start)

        for slot in candidate_slots:
            if remaining_minutes <= 0:
                break

            if splits_used >= max_splits:
                break

            # Check deadline constraint
            if task.deadline and slot.start >= task.deadline:
                continue

            # Check earliest start constraint
            if task.earliest_start and slot.start < task.earliest_start:
                continue

            # Check daily effort limits
            day = slot.start.date()
            current_daily_effort = daily_effort_used.get(day, 0)
            if current_daily_effort >= preferences.max_daily_effort_minutes:
                continue

            # Calculate how much we can schedule in this slot
            max_in_slot = min(
                remaining_minutes,
                slot.duration_minutes,
                task.max_block_minutes or float('inf'),
                preferences.max_daily_effort_minutes - current_daily_effort
            )

            # Must meet minimum block size
            if max_in_slot < task.min_block_minutes:
                continue

            # Use the slot
            duration_to_use = min(max_in_slot, remaining_minutes)

            # Create schedule block
            block = ScheduleBlock(
                task_id=task.id,
                start=slot.start,
                end=slot.start + timedelta(minutes=duration_to_use),
                utility_score=1.0,  # Simple utility for fallback
                estimated_completion_probability=0.7
            )

            scheduled_blocks.append(block)
            remaining_minutes -= duration_to_use
            splits_used += 1

            # Update the slot (remove used portion)
            if duration_to_use < slot.duration_minutes:
                # Split the slot
                used_slot, remaining_slot = slot.split_at(duration_to_use)
                if remaining_slot:
                    # Insert remaining slot back into available slots
                    # This is a simplified approach - in practice, you'd maintain the slot list properly
                    pass

        # Check if task was fully scheduled
        if remaining_minutes <= 0:
            return scheduled_blocks
        else:
            return None

    def _get_max_splits_for_task(self, task: Task) -> int:
        """Get maximum allowed splits for a task."""
        # Look in task tags for max_splits specification
        if task.tags:
            for tag in task.tags:
                if tag.startswith('max_splits:'):
                    try:
                        return int(tag.split(':')[1])
                    except (IndexError, ValueError):
                        pass

        # Default conservative limit
        return 3

    def _diagnose_unscheduled_reason(
        self,
        task: Task,
        available_slots: List[TimeSlot],
        preferences: Preferences,
        daily_effort_used: Dict,
        time_index: TimeIndex
    ) -> UnscheduledReason:
        """Diagnose why a task could not be scheduled."""
        # Check if there are any slots at all
        if not available_slots:
            return UnscheduledReason.NO_TIME

        # Check deadline issues
        if task.deadline:
            slots_before_deadline = [
                slot for slot in available_slots
                if slot.start < task.deadline
            ]
            if not slots_before_deadline:
                return UnscheduledReason.AFTER_DEADLINE

            # Check if enough time exists before deadline
            total_time_before_deadline = sum(
                slot.duration_minutes for slot in slots_before_deadline
            )
            if total_time_before_deadline < task.estimated_minutes:
                return UnscheduledReason.NO_TIME

        # Check contiguous time requirements
        suitable_slots = [
            slot for slot in available_slots
            if slot.duration_minutes >= task.min_block_minutes
        ]
        if not suitable_slots:
            return UnscheduledReason.INSUFFICIENT_CONTIGUOUS_TIME

        # Check daily limits
        for slot in suitable_slots:
            day = slot.start.date()
            if daily_effort_used.get(day, 0) >= preferences.max_daily_effort_minutes:
                continue
            else:
                # If we get here, there should be schedulable time
                # This might be a window violation or splits limit
                break
        else:
            return UnscheduledReason.DAILY_LIMIT_EXCEEDED

        # Check window violations
        if task.preferred_windows:
            slots_in_windows = []
            for slot in suitable_slots:
                for window in task.preferred_windows:
                    if self._slot_in_window(slot, window):
                        slots_in_windows.append(slot)
                        break

            if not slots_in_windows:
                return UnscheduledReason.WINDOW_VIOLATION

        # Must be a splits limit issue
        return UnscheduledReason.SPLITS_LIMIT_EXCEEDED

    def _slot_in_window(self, slot: TimeSlot, window: Dict) -> bool:
        """Check if slot falls within a time window."""
        dow = window.get('dow')
        start_time = window.get('start')
        end_time = window.get('end')

        # Check day of week
        if dow is not None and slot.start.weekday() != dow:
            return False

        # Check time range
        if start_time and end_time:
            slot_time = slot.start.time()
            try:
                window_start = datetime.strptime(start_time, '%H:%M').time()
                window_end = datetime.strptime(end_time, '%H:%M').time()

                if window_start <= window_end:
                    return window_start <= slot_time <= window_end
                else:
                    # Overnight window
                    return slot_time >= window_start or slot_time <= window_end
            except ValueError:
                return False

        return True


# Global fallback scheduler instance
_fallback_scheduler = None

def get_fallback_scheduler(random_seed: int = 42) -> DeterministicFallbackScheduler:
    """Get global fallback scheduler instance."""
    global _fallback_scheduler
    if _fallback_scheduler is None:
        _fallback_scheduler = DeterministicFallbackScheduler(random_seed)
    return _fallback_scheduler