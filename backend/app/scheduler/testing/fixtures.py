"""
Test fixture generation utilities.

Provides helper functions to create realistic test data for tasks,
availability windows, preferences, and other scheduler inputs.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.domain import BusyEvent, Preferences, Task


def create_test_task(
    task_id: str,
    title: Optional[str] = None,
    duration_minutes: int = 60,
    min_block_minutes: int = 30,
    max_block_minutes: Optional[int] = None,
    deadline_hours: Optional[int] = None,
    kind: str = "study",
    weight: float = 1.0,
    user_id: str = "test_user"
) -> Task:
    """
    Create a test task with specified or default parameters.

    Args:
        task_id: Unique task identifier
        title: Task title (auto-generated if None)
        duration_minutes: Total time required
        min_block_minutes: Minimum contiguous block size
        max_block_minutes: Maximum contiguous block size
        deadline_hours: Hours from now for deadline (None for no deadline)
        kind: Task type
        weight: Task importance weight
        user_id: User identifier

    Returns:
        Configured Task object
    """
    if title is None:
        title = f"Test Task {task_id}"

    if max_block_minutes is None:
        max_block_minutes = min(duration_minutes, 120)

    deadline = None
    if deadline_hours is not None:
        # Use timezone-aware datetime
        import pytz
        utc = pytz.UTC
        deadline = datetime.now(utc) + timedelta(hours=deadline_hours)

    return Task(
        id=task_id,
        user_id=user_id,
        title=title,
        kind=kind,
        estimated_minutes=duration_minutes,
        min_block_minutes=min_block_minutes,
        max_block_minutes=max_block_minutes,
        deadline=deadline,
        earliest_start=None,
        weight=weight
    )


def create_test_availability(
    start_hour: int = 9,
    end_hour: int = 17,
    days: int = 7,
    base_date: Optional[datetime] = None
) -> List[Dict[str, str]]:
    """
    Create availability windows for testing.

    Args:
        start_hour: Daily start hour (24-hour format)
        end_hour: Daily end hour (24-hour format)
        days: Number of days to generate
        base_date: Starting date (defaults to today)

    Returns:
        List of availability window dictionaries
    """
    if base_date is None:
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    availability = []

    for day_offset in range(days):
        day = base_date + timedelta(days=day_offset)
        start_time = day.replace(hour=start_hour)
        end_time = day.replace(hour=end_hour)

        availability.append({
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        })

    return availability


def create_test_preferences(
    timezone: str = "UTC",
    workday_start: str = "09:00",
    workday_end: str = "17:00",
    max_daily_effort_minutes: int = 480,
    granularity_minutes: int = 30
) -> Preferences:
    """
    Create test user preferences.

    Args:
        timezone: User timezone
        workday_start: Workday start time (HH:MM format)
        workday_end: Workday end time (HH:MM format)
        max_daily_effort_minutes: Maximum daily work time
        granularity_minutes: Scheduling time slot granularity

    Returns:
        Configured Preferences object
    """
    return Preferences(
        timezone=timezone,
        workday_start=workday_start,
        workday_end=workday_end,
        max_daily_effort_minutes=max_daily_effort_minutes,
        session_granularity_minutes=granularity_minutes,
        break_every_minutes=50,
        break_duration_minutes=10,
        latenight_penalty=3.0,
        morning_penalty=1.0,
        context_switch_penalty=2.0,
        min_gap_between_blocks=15
    )


def create_test_busy_events(
    n_events: int = 3,
    base_date: Optional[datetime] = None,
    event_duration_minutes: int = 60
) -> List[BusyEvent]:
    """
    Create test busy events for calendar conflicts.

    Args:
        n_events: Number of events to create
        base_date: Base date for events (defaults to today)
        event_duration_minutes: Duration of each event

    Returns:
        List of BusyEvent objects
    """
    if base_date is None:
        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    events = []

    for i in range(n_events):
        # Spread events across different days
        event_day = base_date + timedelta(days=i % 7)
        event_hour = 10 + (i * 2) % 8  # Vary the time

        start_time = event_day.replace(hour=event_hour)
        end_time = start_time + timedelta(minutes=event_duration_minutes)

        event = BusyEvent(
            id=f"test_event_{i}",
            source="pulse",
            start=start_time,
            end=end_time,
            title=f"Test Meeting {i}",
            hard=True
        )
        events.append(event)

    return events


def create_realistic_course_tasks(
    course_name: str,
    n_assignments: int = 3,
    n_readings: int = 5,
    n_exams: int = 2,
    semester_weeks: int = 16
) -> List[Task]:
    """
    Create realistic academic tasks for a course.

    Args:
        course_name: Name of the course
        n_assignments: Number of assignments
        n_readings: Number of readings
        n_exams: Number of exams
        semester_weeks: Length of semester in weeks

    Returns:
        List of realistic academic tasks
    """
    tasks = []
    base_date = datetime.now()
    semester_end = base_date + timedelta(weeks=semester_weeks)

    # Create assignments
    for i in range(n_assignments):
        due_week = (i + 1) * (semester_weeks // n_assignments)
        due_date = base_date + timedelta(weeks=due_week)

        # Assignments typically take 2-6 hours
        duration = random.randint(120, 360)

        task = Task(
            id=f"{course_name.lower()}_assignment_{i+1}",
            user_id="test_user",
            title=f"{course_name} Assignment {i+1}",
            kind="assignment",
            estimated_minutes=duration,
            min_block_minutes=60,  # Assignments need focus
            max_block_minutes=180,
            deadline=due_date,
            weight=2.5,  # Assignments are important
            course_id=course_name.lower(),
            tags=["academic", "graded"]
        )
        tasks.append(task)

    # Create readings
    for i in range(n_readings):
        # Spread readings throughout semester
        week = random.randint(1, semester_weeks - 1)
        due_date = base_date + timedelta(weeks=week)

        # Readings typically take 1-3 hours
        duration = random.randint(60, 180)

        task = Task(
            id=f"{course_name.lower()}_reading_{i+1}",
            user_id="test_user",
            title=f"{course_name} Reading {i+1}",
            kind="reading",
            estimated_minutes=duration,
            min_block_minutes=30,  # Can be broken up
            max_block_minutes=120,
            deadline=due_date,
            weight=1.0,  # Lower priority than assignments
            course_id=course_name.lower(),
            tags=["academic", "preparation"]
        )
        tasks.append(task)

    # Create exams (with prep time)
    for i in range(n_exams):
        # Exams typically at midterm and final
        if i == 0:
            exam_week = semester_weeks // 2
        else:
            exam_week = semester_weeks - 1

        exam_date = base_date + timedelta(weeks=exam_week)

        # Exam prep typically takes 3-8 hours
        duration = random.randint(180, 480)

        task = Task(
            id=f"{course_name.lower()}_exam_prep_{i+1}",
            user_id="test_user",
            title=f"{course_name} Exam {i+1} Preparation",
            kind="exam",
            estimated_minutes=duration,
            min_block_minutes=90,  # Need substantial blocks
            max_block_minutes=240,
            deadline=exam_date - timedelta(days=1),  # Prep day before
            weight=3.0,  # High priority
            course_id=course_name.lower(),
            tags=["academic", "critical", "high_focus"]
        )
        tasks.append(task)

    return tasks


def create_stress_test_scenario(
    n_tasks: int = 50,
    n_busy_events: int = 20,
    horizon_days: int = 14,
    complexity_level: str = "high"
) -> Dict[str, Any]:
    """
    Create a stress test scenario with many tasks and constraints.

    Args:
        n_tasks: Number of tasks to create
        n_busy_events: Number of calendar conflicts
        horizon_days: Time horizon in days
        complexity_level: "low", "medium", or "high" complexity

    Returns:
        Dictionary with tasks, events, and preferences
    """
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Generate tasks with varying complexity
    tasks = []
    for i in range(n_tasks):
        if complexity_level == "low":
            duration = random.randint(30, 120)
            min_block = 30
            deadline_days = random.randint(1, horizon_days)
            weight = 1.0
            prerequisites = []
        elif complexity_level == "medium":
            duration = random.randint(60, 240)
            min_block = random.randint(30, 60)
            deadline_days = random.randint(1, horizon_days)
            weight = random.uniform(0.5, 2.0)
            prerequisites = [f"stress_task_{random.randint(0, max(0, i-3))}"] if i > 2 and random.random() < 0.2 else []
        else:  # high
            duration = random.randint(30, 360)
            min_block = random.randint(15, 90)
            deadline_days = random.randint(1, horizon_days)
            weight = random.uniform(0.1, 5.0)
            prerequisites = [f"stress_task_{j}" for j in range(max(0, i-2), i) if random.random() < 0.3]

        deadline = base_date + timedelta(days=deadline_days, hours=random.randint(8, 20))

        task = Task(
            id=f"stress_task_{i}",
            user_id="stress_test_user",
            title=f"Stress Test Task {i}",
            kind=random.choice(["study", "assignment", "project", "reading", "exam"]),
            estimated_minutes=duration,
            min_block_minutes=min_block,
            max_block_minutes=min(duration, 240),
            deadline=deadline,
            weight=weight,
            prerequisites=prerequisites
        )

        # Add complexity features
        if complexity_level in ["medium", "high"] and random.random() < 0.3:
            # Add preferred windows
            task.preferred_windows = [
                {
                    "dow": random.randint(0, 6),
                    "start": f"{random.randint(9, 14):02d}:00",
                    "end": f"{random.randint(15, 18):02d}:00"
                }
            ]

        if complexity_level == "high" and random.random() < 0.2:
            # Add avoid windows
            task.avoid_windows = [
                {
                    "dow": random.randint(0, 6),
                    "start": f"{random.randint(18, 20):02d}:00",
                    "end": f"{random.randint(21, 23):02d}:00"
                }
            ]

        tasks.append(task)

    # Generate busy events
    busy_events = []
    for i in range(n_busy_events):
        event_day = random.randint(0, horizon_days - 1)
        event_date = base_date + timedelta(days=event_day)
        event_hour = random.randint(8, 18)
        event_duration = random.randint(30, 180)

        start_time = event_date.replace(hour=event_hour)
        end_time = start_time + timedelta(minutes=event_duration)

        event = BusyEvent(
            id=f"stress_event_{i}",
            source=random.choice(["google", "microsoft", "pulse"]),
            start=start_time,
            end=end_time,
            title=f"Stress Event {i}",
            hard=random.choice([True, False]),
            movable=random.choice([True, False])
        )
        busy_events.append(event)

    # Create challenging preferences
    preferences = Preferences(
        timezone="UTC",
        workday_start="08:00" if complexity_level == "high" else "09:00",
        workday_end="20:00" if complexity_level == "high" else "17:00",
        max_daily_effort_minutes=300 if complexity_level == "high" else 480,
        session_granularity_minutes=15 if complexity_level == "high" else 30,
        break_every_minutes=45,
        break_duration_minutes=15,
        deep_work_windows=[
            {"dow": i, "start": "14:00", "end": "16:00"} for i in range(0, 5)
        ] if complexity_level == "high" else [],
        no_study_windows=[
            {"dow": i, "start": "12:00", "end": "13:00"} for i in range(0, 7)  # Lunch
        ] if complexity_level in ["medium", "high"] else [],
        latenight_penalty=5.0 if complexity_level == "high" else 3.0,
        context_switch_penalty=3.0 if complexity_level == "high" else 2.0
    )

    return {
        "tasks": tasks,
        "busy_events": busy_events,
        "preferences": preferences,
        "horizon_days": horizon_days,
        "complexity": complexity_level
    }


def create_edge_case_scenarios() -> List[Dict[str, Any]]:
    """
    Create edge case scenarios for thorough testing.

    Returns:
        List of edge case scenarios
    """
    scenarios = []

    # Edge case 1: Empty schedule
    scenarios.append({
        "name": "empty_schedule",
        "tasks": [],
        "busy_events": [],
        "preferences": create_test_preferences(),
        "description": "No tasks to schedule"
    })

    # Edge case 2: Impossible deadline
    impossible_task = create_test_task(
        "impossible",
        duration_minutes=480,
        deadline_hours=1  # 8 hours of work in 1 hour
    )
    scenarios.append({
        "name": "impossible_deadline",
        "tasks": [impossible_task],
        "busy_events": [],
        "preferences": create_test_preferences(),
        "description": "Task with impossible deadline"
    })

    # Edge case 3: Fully booked calendar
    base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    all_day_events = []
    for hour in range(8, 18):
        event_start = base_time.replace(hour=hour)
        event_end = event_start + timedelta(hours=1)
        all_day_events.append(BusyEvent(
            id=f"busy_{hour}",
            source="google",
            start=event_start,
            end=event_end,
            title=f"Meeting {hour}",
            hard=True
        ))

    scenarios.append({
        "name": "fully_booked",
        "tasks": [create_test_task("squeezed", duration_minutes=60)],
        "busy_events": all_day_events,
        "preferences": create_test_preferences(),
        "description": "No available time slots"
    })

    # Edge case 4: Circular dependencies
    task_a = create_test_task("circular_a", prerequisites=["circular_b"])
    task_b = create_test_task("circular_b", prerequisites=["circular_a"])
    scenarios.append({
        "name": "circular_dependencies",
        "tasks": [task_a, task_b],
        "busy_events": [],
        "preferences": create_test_preferences(),
        "description": "Circular task dependencies"
    })

    # Edge case 5: Very fine granularity
    fine_prefs = create_test_preferences(granularity_minutes=15)
    scenarios.append({
        "name": "fine_granularity",
        "tasks": [create_test_task("fine", duration_minutes=37)],  # Odd duration
        "busy_events": [],
        "preferences": fine_prefs,
        "description": "Fine time granularity with odd durations"
    })

    return scenarios
