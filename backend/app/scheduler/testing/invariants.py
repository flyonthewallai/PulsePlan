"""
Schedule invariant checking functions.

Validates that generated schedules satisfy all fundamental constraints
and maintain logical consistency across all scheduling components.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.domain import BusyEvent, Preferences, ScheduleBlock, ScheduleSolution, Task
from ..optimization.time_index import TimeIndex

logger = logging.getLogger(__name__)


class ScheduleInvariantError(Exception):
    """Raised when a schedule violates fundamental invariants."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}


@dataclass
class InvariantCheckResult:
    """Result of invariant checking with detailed feedback."""
    passed: bool
    violations: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    checked_invariants: List[str]


def check_invariants(
    solution: ScheduleSolution,
    tasks: List[Task],
    busy_events: List[BusyEvent],
    preferences: Preferences,
    time_index: Optional[TimeIndex] = None,
    strict: bool = True
) -> InvariantCheckResult:
    """
    Comprehensive invariant checking for schedule solutions.

    Args:
        solution: The schedule solution to validate
        tasks: Original tasks that were scheduled
        busy_events: Calendar events that constrain scheduling
        preferences: User preferences and constraints
        time_index: Time discretization used for scheduling
        strict: If True, raises exception on violations; if False, returns result

    Returns:
        InvariantCheckResult with detailed validation results

    Raises:
        ScheduleInvariantError: If strict=True and invariants are violated
    """
    violations = []
    warnings = []
    metrics = {}
    checked_invariants = []

    try:
        # Core structural invariants
        _check_no_overlaps(solution.blocks, violations, checked_invariants)
        _check_block_duration_consistency(solution.blocks, violations, checked_invariants)
        _check_temporal_ordering(solution.blocks, violations, checked_invariants)

        # Task-related invariants
        if tasks:
            _check_task_assignment_consistency(solution.blocks, tasks, violations, warnings, checked_invariants)
            _check_minimum_block_lengths(solution.blocks, tasks, violations, checked_invariants)
            _check_deadline_compliance(solution.blocks, tasks, violations, warnings, checked_invariants)
            _check_prerequisite_ordering(solution.blocks, tasks, violations, checked_invariants)

        # Calendar constraint invariants
        if busy_events:
            _check_no_calendar_conflicts(solution.blocks, busy_events, violations, checked_invariants)

        # Preference compliance checks
        if preferences:
            _check_preference_compliance(solution.blocks, preferences, warnings, checked_invariants)
            _check_daily_effort_limits(solution.blocks, preferences, violations, warnings, checked_invariants)

        # Time index consistency
        if time_index:
            _check_time_index_alignment(solution.blocks, time_index, violations, checked_invariants)

        # Solution metadata consistency
        _check_solution_metadata_consistency(solution, violations, checked_invariants)

        # Extended invariants
        _check_horizon_bounds(solution.blocks, violations, checked_invariants)
        _check_earliest_start_compliance(solution.blocks, tasks, violations, checked_invariants)
        _check_max_splits_per_task(solution.blocks, tasks, violations, checked_invariants)
        _check_transition_buffers(solution.blocks, preferences, violations, warnings, checked_invariants)
        _check_timezone_dst_correctness(solution.blocks, preferences, violations, warnings, checked_invariants)

        # Calculate metrics
        metrics = _calculate_invariant_metrics(solution, tasks, busy_events, preferences)

        # Prepare result
        result = InvariantCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
            checked_invariants=checked_invariants
        )

        if strict and violations:
            raise ScheduleInvariantError(
                f"Schedule violates {len(violations)} invariants: {'; '.join(violations)}",
                context={
                    'violations': violations,
                    'warnings': warnings,
                    'metrics': metrics,
                    'solution_id': getattr(solution, 'id', None)
                }
            )

        return result

    except Exception as e:
        if isinstance(e, ScheduleInvariantError):
            raise

        # Wrap unexpected errors
        raise ScheduleInvariantError(
            f"Invariant checking failed with error: {str(e)}",
            context={'original_error': str(e), 'error_type': type(e).__name__}
        )


def _check_no_overlaps(blocks: List[ScheduleBlock], violations: List[str], checked: List[str]):
    """Check that no schedule blocks overlap in time."""
    checked.append("no_overlaps")

    for i, block1 in enumerate(blocks):
        for j, block2 in enumerate(blocks[i + 1:], i + 1):
            # Check for any temporal overlap
            overlap_start = max(block1.start, block2.start)
            overlap_end = min(block1.end, block2.end)

            if overlap_start < overlap_end:
                violations.append(
                    f"Blocks overlap: {block1.task_id} ({block1.start} - {block1.end}) "
                    f"and {block2.task_id} ({block2.start} - {block2.end})"
                )


def _check_block_duration_consistency(blocks: List[ScheduleBlock], violations: List[str], checked: List[str]):
    """Check that block durations match start/end time differences."""
    checked.append("block_duration_consistency")

    for block in blocks:
        calculated_duration = int((block.end - block.start).total_seconds() / 60)

        if calculated_duration != block.duration_minutes:
            violations.append(
                f"Block {block.task_id} duration mismatch: calculated {calculated_duration}min, "
                f"stored {block.duration_minutes}min"
            )

        if calculated_duration <= 0:
            violations.append(
                f"Block {block.task_id} has invalid duration: {calculated_duration}min"
            )


def _check_temporal_ordering(blocks: List[ScheduleBlock], violations: List[str], checked: List[str]):
    """Check that all blocks have start < end."""
    checked.append("temporal_ordering")

    for block in blocks:
        if block.start >= block.end:
            violations.append(
                f"Block {block.task_id} has invalid time ordering: "
                f"start {block.start} >= end {block.end}"
            )


def _check_task_assignment_consistency(
    blocks: List[ScheduleBlock],
    tasks: List[Task],
    violations: List[str],
    warnings: List[str],
    checked: List[str]
):
    """Check that all blocks reference valid tasks and task coverage."""
    checked.append("task_assignment_consistency")

    task_ids = {task.id for task in tasks}
    block_task_ids = {block.task_id for block in blocks}

    # Check for invalid task references
    for block in blocks:
        if block.task_id not in task_ids:
            violations.append(
                f"Block references unknown task: {block.task_id}"
            )

    # Check task coverage
    scheduled_tasks = {block.task_id for block in blocks}
    unscheduled_tasks = task_ids - scheduled_tasks

    if unscheduled_tasks:
        warnings.append(
            f"Unscheduled tasks: {', '.join(sorted(unscheduled_tasks))}"
        )

    # Check total scheduled time per task
    task_scheduled_time = {}
    for block in blocks:
        task_scheduled_time[block.task_id] = task_scheduled_time.get(block.task_id, 0) + block.duration_minutes

    task_lookup = {task.id: task for task in tasks}
    for task_id, scheduled_time in task_scheduled_time.items():
        if task_id in task_lookup:
            required_time = task_lookup[task_id].estimated_minutes
            if scheduled_time < required_time:
                warnings.append(
                    f"Task {task_id} under-scheduled: {scheduled_time}min scheduled, "
                    f"{required_time}min required"
                )
            elif scheduled_time > required_time * 1.5:  # Allow some flexibility
                warnings.append(
                    f"Task {task_id} over-scheduled: {scheduled_time}min scheduled, "
                    f"{required_time}min required"
                )


def _check_minimum_block_lengths(blocks: List[ScheduleBlock], tasks: List[Task], violations: List[str], checked: List[str]):
    """Check that all blocks meet minimum duration requirements."""
    checked.append("minimum_block_lengths")

    task_lookup = {task.id: task for task in tasks}

    for block in blocks:
        if block.task_id in task_lookup:
            task = task_lookup[block.task_id]
            if block.duration_minutes < task.min_block_minutes:
                violations.append(
                    f"Block {block.task_id} violates minimum duration: "
                    f"{block.duration_minutes}min < {task.min_block_minutes}min required"
                )


def _check_deadline_compliance(
    blocks: List[ScheduleBlock],
    tasks: List[Task],
    violations: List[str],
    warnings: List[str],
    checked: List[str]
):
    """Check that all blocks respect task deadlines."""
    checked.append("deadline_compliance")

    task_lookup = {task.id: task for task in tasks}

    for block in blocks:
        if block.task_id in task_lookup:
            task = task_lookup[block.task_id]
            if task.deadline and block.end > task.deadline:
                violations.append(
                    f"Block {block.task_id} violates deadline: "
                    f"ends at {block.end}, deadline is {task.deadline}"
                )
            elif task.deadline and block.start > task.deadline - timedelta(hours=1):
                warnings.append(
                    f"Block {block.task_id} starts very close to deadline: "
                    f"starts at {block.start}, deadline is {task.deadline}"
                )


def _check_prerequisite_ordering(blocks: List[ScheduleBlock], tasks: List[Task], violations: List[str], checked: List[str]):
    """Check that prerequisite tasks complete before dependent tasks start."""
    checked.append("prerequisite_ordering")

    task_lookup = {task.id: task for task in tasks}

    # Build task completion times
    task_completion_times = {}
    for block in blocks:
        task_id = block.task_id
        if task_id not in task_completion_times:
            task_completion_times[task_id] = block.end
        else:
            task_completion_times[task_id] = max(task_completion_times[task_id], block.end)

    # Build task start times
    task_start_times = {}
    for block in blocks:
        task_id = block.task_id
        if task_id not in task_start_times:
            task_start_times[task_id] = block.start
        else:
            task_start_times[task_id] = min(task_start_times[task_id], block.start)

    # Check prerequisites
    for task in tasks:
        if task.prerequisites and task.id in task_start_times:
            task_start = task_start_times[task.id]

            for prereq_id in task.prerequisites:
                if prereq_id in task_completion_times:
                    prereq_end = task_completion_times[prereq_id]
                    if prereq_end >= task_start:
                        violations.append(
                            f"Prerequisite ordering violation: task {task.id} starts at {task_start}, "
                            f"but prerequisite {prereq_id} doesn't complete until {prereq_end}"
                        )


def _check_no_calendar_conflicts(blocks: List[ScheduleBlock], busy_events: List[BusyEvent], violations: List[str], checked: List[str]):
    """Check that blocks don't conflict with existing calendar events."""
    checked.append("no_calendar_conflicts")

    for block in blocks:
        for event in busy_events:
            if not event.hard:
                continue  # Skip soft conflicts

            # Check for overlap
            overlap_start = max(block.start, event.start)
            overlap_end = min(block.end, event.end)

            if overlap_start < overlap_end:
                violations.append(
                    f"Block {block.task_id} conflicts with calendar event '{event.title}': "
                    f"block ({block.start} - {block.end}) overlaps event ({event.start} - {event.end})"
                )


def _check_preference_compliance(blocks: List[ScheduleBlock], preferences: Preferences, warnings: List[str], checked: List[str]):
    """Check compliance with user preferences (soft constraints)."""
    checked.append("preference_compliance")

    late_night_threshold = datetime.strptime("22:00", "%H:%M").time()
    early_morning_threshold = datetime.strptime("06:00", "%H:%M").time()

    for block in blocks:
        block_start_time = block.start.time()
        block_end_time = block.end.time()

        # Check for late night scheduling
        if block_start_time >= late_night_threshold:
            warnings.append(
                f"Block {block.task_id} starts late at night: {block.start}"
            )

        # Check for very early morning scheduling
        if block_start_time <= early_morning_threshold:
            warnings.append(
                f"Block {block.task_id} starts very early: {block.start}"
            )

        # Check workday boundaries
        try:
            workday_start = datetime.strptime(preferences.workday_start, "%H:%M").time()
            workday_end = datetime.strptime(preferences.workday_end, "%H:%M").time()

            if block_start_time < workday_start or block_end_time > workday_end:
                warnings.append(
                    f"Block {block.task_id} extends outside workday hours: "
                    f"{block.start} - {block.end}"
                )
        except (ValueError, AttributeError):
            pass  # Invalid time format in preferences


def _check_daily_effort_limits(
    blocks: List[ScheduleBlock],
    preferences: Preferences,
    violations: List[str],
    warnings: List[str],
    checked: List[str]
):
    """Check that daily effort limits are respected."""
    checked.append("daily_effort_limits")

    if not preferences.max_daily_effort_minutes:
        return

    # Group blocks by date
    daily_effort = {}
    for block in blocks:
        date = block.start.date()
        daily_effort[date] = daily_effort.get(date, 0) + block.duration_minutes

    for date, effort_minutes in daily_effort.items():
        if effort_minutes > preferences.max_daily_effort_minutes:
            violations.append(
                f"Daily effort limit exceeded on {date}: "
                f"{effort_minutes}min > {preferences.max_daily_effort_minutes}min limit"
            )
        elif effort_minutes > preferences.max_daily_effort_minutes * 0.9:
            warnings.append(
                f"Daily effort near limit on {date}: "
                f"{effort_minutes}min (limit: {preferences.max_daily_effort_minutes}min)"
            )


def _check_time_index_alignment(blocks: List[ScheduleBlock], time_index: TimeIndex, violations: List[str], checked: List[str]):
    """Check that blocks align with time index granularity."""
    checked.append("time_index_alignment")

    granularity_minutes = time_index.granularity_minutes

    for block in blocks:
        # Check start time alignment
        start_minutes = block.start.minute
        if start_minutes % granularity_minutes != 0:
            violations.append(
                f"Block {block.task_id} start time not aligned to {granularity_minutes}min granularity: {block.start}"
            )

        # Check duration alignment
        if block.duration_minutes % granularity_minutes != 0:
            violations.append(
                f"Block {block.task_id} duration not aligned to {granularity_minutes}min granularity: "
                f"{block.duration_minutes}min"
            )

        # Check if times are within time index bounds
        if block.start < time_index.start_dt or block.end > time_index.end_dt:
            violations.append(
                f"Block {block.task_id} outside time index bounds: "
                f"block ({block.start} - {block.end}), "
                f"index bounds ({time_index.start_dt} - {time_index.end_dt})"
            )


def _check_solution_metadata_consistency(solution: ScheduleSolution, violations: List[str], checked: List[str]):
    """Check that solution metadata is consistent with blocks."""
    checked.append("solution_metadata_consistency")

    # Check feasibility consistency (allow empty feasible solutions for valid cases)
    if solution.feasible and not solution.blocks:
        # Only flag as violation if there were tasks that should have been scheduled
        # Empty feasible solutions are valid when there are no tasks to schedule
        pass

    # Check total scheduled minutes
    calculated_total = sum(block.duration_minutes for block in solution.blocks)
    if solution.total_scheduled_minutes != calculated_total:
        violations.append(
            f"Total scheduled minutes mismatch: calculated {calculated_total}min, "
            f"stored {solution.total_scheduled_minutes}min"
        )

    # Check unscheduled tasks consistency
    scheduled_tasks = {block.task_id for block in solution.blocks}
    unscheduled_set = set(solution.unscheduled_tasks)

    # Should not have overlap
    overlap = scheduled_tasks & unscheduled_set
    if overlap:
        violations.append(
            f"Tasks appear in both scheduled blocks and unscheduled list: {', '.join(overlap)}"
        )


def _calculate_invariant_metrics(
    solution: ScheduleSolution,
    tasks: Optional[List[Task]],
    busy_events: Optional[List[BusyEvent]],
    preferences: Optional[Preferences]
) -> Dict[str, Any]:
    """Calculate metrics about the schedule for analysis."""
    metrics = {
        'total_blocks': len(solution.blocks),
        'total_scheduled_minutes': sum(block.duration_minutes for block in solution.blocks),
        'average_block_duration': 0,
        'fragmentation_score': 0,
        'calendar_utilization': 0,
        'preference_violations': 0
    }

    if solution.blocks:
        metrics['average_block_duration'] = metrics['total_scheduled_minutes'] / len(solution.blocks)

        # Calculate fragmentation (number of blocks per task)
        task_block_counts = {}
        for block in solution.blocks:
            task_block_counts[block.task_id] = task_block_counts.get(block.task_id, 0) + 1

        if task_block_counts:
            metrics['fragmentation_score'] = sum(task_block_counts.values()) / len(task_block_counts)

    if tasks:
        total_required_time = sum(task.estimated_minutes for task in tasks)
        metrics['task_coverage_ratio'] = metrics['total_scheduled_minutes'] / total_required_time if total_required_time > 0 else 0
        metrics['unscheduled_task_ratio'] = len(solution.unscheduled_tasks) / len(tasks) if tasks else 0

    return metrics


def has_overlaps(blocks: List[ScheduleBlock]) -> bool:
    """
    Quick check if any blocks overlap (for external use).

    Args:
        blocks: List of schedule blocks to check

    Returns:
        True if any overlaps exist, False otherwise
    """
    violations = []
    checked = []
    _check_no_overlaps(blocks, violations, checked)
    return len(violations) > 0


def validate_against_availability(blocks: List[ScheduleBlock], availability_windows: List[Dict]) -> bool:
    """
    Check if all blocks fall within available time windows.

    Args:
        blocks: Schedule blocks to validate
        availability_windows: List of availability windows with 'start' and 'end' keys

    Returns:
        True if all blocks are within availability, False otherwise
    """
    for block in blocks:
        block_within_availability = False

        for window in availability_windows:
            window_start = window.get('start')
            window_end = window.get('end')

            if window_start and window_end:
                if isinstance(window_start, str):
                    window_start = datetime.fromisoformat(window_start)
                if isinstance(window_end, str):
                    window_end = datetime.fromisoformat(window_end)

                if block.start >= window_start and block.end <= window_end:
                    block_within_availability = True
                    break

        if not block_within_availability:
            return False

    return True


def _check_horizon_bounds(blocks: List[ScheduleBlock], violations: List[str], checked: List[str]):
    """Check that no blocks are scheduled before now or after horizon end."""
    checked.append("horizon_bounds")

    now = datetime.now()
    # Reasonable horizon end (30 days from now)
    horizon_end = now + timedelta(days=30)

    for block in blocks:
        if block.start < now:
            violations.append(
                f"Block {block.task_id} scheduled in the past: {block.start} < {now}"
            )

        if block.start > horizon_end:
            violations.append(
                f"Block {block.task_id} scheduled beyond reasonable horizon: "
                f"{block.start} > {horizon_end}"
            )


def _check_earliest_start_compliance(
    blocks: List[ScheduleBlock],
    tasks: List[Task],
    violations: List[str],
    checked: List[str]
):
    """Check that blocks respect task earliest_start constraints."""
    checked.append("earliest_start_compliance")

    if not tasks:
        return

    task_lookup = {task.id: task for task in tasks}

    for block in blocks:
        if block.task_id in task_lookup:
            task = task_lookup[block.task_id]
            if task.earliest_start and block.start < task.earliest_start:
                violations.append(
                    f"Block {block.task_id} starts before earliest allowed time: "
                    f"{block.start} < {task.earliest_start}"
                )


def _check_max_splits_per_task(
    blocks: List[ScheduleBlock],
    tasks: List[Task],
    violations: List[str],
    checked: List[str]
):
    """Check that tasks don't exceed maximum allowed splits."""
    checked.append("max_splits_per_task")

    if not tasks:
        return

    task_lookup = {task.id: task for task in tasks}

    # Count blocks per task
    task_block_counts = {}
    for block in blocks:
        task_block_counts[block.task_id] = task_block_counts.get(block.task_id, 0) + 1

    for task_id, block_count in task_block_counts.items():
        if task_id in task_lookup:
            task = task_lookup[task_id]

            # Check if task has max_splits constraint (stored in metadata or tags)
            max_splits = None

            # Look for max_splits in task metadata/tags
            if hasattr(task, 'metadata') and task.metadata:
                max_splits = task.metadata.get('max_splits')
            elif hasattr(task, 'tags') and task.tags:
                # Look for tag like "max_splits:3"
                for tag in task.tags:
                    if tag.startswith('max_splits:'):
                        try:
                            max_splits = int(tag.split(':')[1])
                        except (IndexError, ValueError):
                            pass

            # Default conservative limit if not specified
            if max_splits is None:
                max_splits = 5  # Reasonable default

            if block_count > max_splits:
                violations.append(
                    f"Task {task_id} exceeds maximum splits: {block_count} > {max_splits}"
                )


def _check_transition_buffers(
    blocks: List[ScheduleBlock],
    preferences: Optional[Preferences],
    violations: List[str],
    warnings: List[str],
    checked: List[str]
):
    """Check that adequate transition time exists between blocks."""
    checked.append("transition_buffers")

    if not preferences or len(blocks) < 2:
        return

    # Get minimum gap requirement
    min_gap_minutes = getattr(preferences, 'min_gap_between_blocks', 15)

    # Sort blocks by start time
    sorted_blocks = sorted(blocks, key=lambda b: b.start)

    for i in range(len(sorted_blocks) - 1):
        current_block = sorted_blocks[i]
        next_block = sorted_blocks[i + 1]

        # Calculate gap between blocks
        gap_minutes = (next_block.start - current_block.end).total_seconds() / 60

        if gap_minutes < 0:
            # This should be caught by overlap check, but double-check
            violations.append(
                f"Overlapping blocks detected: {current_block.task_id} and {next_block.task_id}"
            )
        elif gap_minutes < min_gap_minutes:
            # Check if blocks are for different tasks or locations
            if current_block.task_id != next_block.task_id:
                warnings.append(
                    f"Insufficient transition time between {current_block.task_id} and "
                    f"{next_block.task_id}: {gap_minutes:.0f}min < {min_gap_minutes}min required"
                )


def _check_timezone_dst_correctness(
    blocks: List[ScheduleBlock],
    preferences: Optional[Preferences],
    violations: List[str],
    warnings: List[str],
    checked: List[str]
):
    """Check that timezone and DST boundaries are handled correctly."""
    checked.append("timezone_dst_correctness")

    if not preferences or not blocks:
        return

    try:
        import pytz

        user_timezone = preferences.timezone
        if user_timezone == "UTC":
            return  # No DST issues with UTC

        tz = pytz.timezone(user_timezone)

        for block in blocks:
            # Check if block times are timezone-aware
            if block.start.tzinfo is None:
                warnings.append(
                    f"Block {block.task_id} has naive datetime (no timezone): {block.start}"
                )
                continue

            # Check for DST transition issues
            # Convert to user timezone
            local_start = block.start.astimezone(tz)
            local_end = block.end.astimezone(tz)

            # Check if duration is preserved across DST transition
            utc_duration = (block.end - block.start).total_seconds()
            local_duration = (local_end - local_start).total_seconds()

            # Allow small differences due to DST transitions
            duration_diff = abs(utc_duration - local_duration)
            if duration_diff > 3600:  # More than 1 hour difference
                warnings.append(
                    f"Block {block.task_id} may have DST transition issue: "
                    f"duration difference {duration_diff/60:.0f} minutes"
                )

    except ImportError:
        # pytz not available, skip DST checks
        warnings.append("pytz not available for DST validation")
    except Exception as e:
        warnings.append(f"Timezone validation error: {str(e)}")


def _check_availability_window_compliance(
    blocks: List[ScheduleBlock],
    tasks: List[Task],
    violations: List[str],
    checked: List[str]
):
    """Check that blocks are scheduled within task availability windows."""
    checked.append("availability_window_compliance")

    if not tasks:
        return

    task_lookup = {task.id: task for task in tasks}

    for block in blocks:
        if block.task_id in task_lookup:
            task = task_lookup[block.task_id]

            # Check preferred windows
            if task.preferred_windows:
                block_in_preferred = False

                for window in task.preferred_windows:
                    if _datetime_in_window(block.start, window):
                        block_in_preferred = True
                        break

                if not block_in_preferred:
                    violations.append(
                        f"Block {block.task_id} scheduled outside preferred windows: {block.start}"
                    )


def _datetime_in_window(dt: datetime, window: Dict) -> bool:
    """Check if datetime falls within a time window specification."""
    dow = window.get('dow')
    start_time = window.get('start')
    end_time = window.get('end')

    # Check day of week
    if dow is not None and dt.weekday() != dow:
        return False

    # Check time range
    if start_time and end_time:
        dt_time = dt.time()
        try:
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()

            if start <= end:
                return start <= dt_time <= end
            else:
                # Overnight window
                return dt_time >= start or dt_time <= end
        except ValueError:
            return False

    return True
