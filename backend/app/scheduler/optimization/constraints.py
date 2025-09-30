"""
Constraint building helpers for the OR-Tools scheduler.

Provides modular constraint construction functions for different types
of scheduling constraints.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from ..core.domain import Task, BusyEvent, Preferences
from .time_index import TimeIndex

logger = logging.getLogger(__name__)


def add_busy_constraints(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    time_index: TimeIndex,
    busy_events: List[BusyEvent]
):
    """
    Add constraints to prevent scheduling over busy calendar events.
    
    Args:
        model: CP-SAT model
        x: Decision variables x[task_idx, slot_idx]
        time_index: Time discretization
        busy_events: Calendar events that block scheduling
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    blocked_slots = time_index.filter_busy_slots(busy_events)
    n_tasks = max(t_idx for t_idx, _ in x.keys()) + 1 if x else 0
    
    logger.debug(f"Adding busy constraints for {len(blocked_slots)} blocked slots")
    
    for slot_idx in blocked_slots:
        for task_idx in range(n_tasks):
            if (task_idx, slot_idx) in x:
                model.Add(x[(task_idx, slot_idx)] == 0)


def add_deadline_constraints(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex
):
    """
    Add constraints to ensure tasks are completed before their deadlines.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks with potential deadlines
        time_index: Time discretization
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    deadline_count = 0
    
    for t_idx, task in enumerate(tasks):
        if task.deadline:
            deadline_idx = time_index.datetime_to_index(task.deadline)
            if deadline_idx is not None:
                # Prevent assignment to slots at or after deadline
                for s_idx in range(deadline_idx, len(time_index)):
                    if (t_idx, s_idx) in x:
                        model.Add(x[(t_idx, s_idx)] == 0)
                deadline_count += 1
    
    logger.debug(f"Added deadline constraints for {deadline_count} tasks")


def add_block_length_constraints(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    granularity_minutes: int
):
    """
    Add minimum and maximum block length constraints.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks with block constraints
        granularity_minutes: Time slot duration
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    n_slots = max(s_idx for _, s_idx in x.keys()) + 1 if x else 0
    
    for t_idx, task in enumerate(tasks):
        # Minimum block length
        min_slots = int(np.ceil(task.min_block_minutes / granularity_minutes))
        if min_slots > 1:
            add_min_block_length_constraint(model, x, t_idx, min_slots, n_slots)
        
        # Maximum block length (if specified)
        if task.max_block_minutes > 0:
            max_slots = int(task.max_block_minutes / granularity_minutes)
            if max_slots > min_slots:
                add_max_block_length_constraint(model, x, t_idx, max_slots, n_slots)


def add_min_block_length_constraint(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    task_idx: int,
    min_slots: int,
    n_slots: int
):
    """
    Add minimum contiguous block length constraint for a specific task.
    
    Uses the "no short blocks" approach: if a task is assigned to a slot,
    and it's the start of a block, then the next min_slots-1 slots must
    also be assigned to the same task.
    """
    # For each potential block start position
    for start_idx in range(n_slots - min_slots + 1):
        if (task_idx, start_idx) not in x:
            continue
            
        # Create indicator for "block starts here"
        starts_here = model.NewBoolVar(f"starts_{task_idx}_{start_idx}")
        
        # Define "starts here" condition
        if start_idx == 0:
            # First slot: starts here if assigned
            model.Add(starts_here == x[(task_idx, start_idx)])
        else:
            # Not first slot: starts here if assigned and previous is not assigned
            if (task_idx, start_idx - 1) in x:
                # starts_here <= x[start_idx]
                model.Add(starts_here <= x[(task_idx, start_idx)])
                # starts_here <= 1 - x[start_idx-1] 
                model.Add(starts_here <= 1 - x[(task_idx, start_idx - 1)])
                # starts_here >= x[start_idx] - x[start_idx-1]
                model.Add(starts_here >= x[(task_idx, start_idx)] - x[(task_idx, start_idx - 1)])
            else:
                model.Add(starts_here == x[(task_idx, start_idx)])
        
        # If block starts here, ensure minimum length
        for offset in range(min_slots):
            slot_idx = start_idx + offset
            if slot_idx < n_slots and (task_idx, slot_idx) in x:
                model.Add(x[(task_idx, slot_idx)] >= starts_here)


def add_max_block_length_constraint(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    task_idx: int,
    max_slots: int,
    n_slots: int
):
    """
    Add maximum contiguous block length constraint for a specific task.
    
    Prevents blocks longer than max_slots by ensuring that in any window
    of max_slots+1 consecutive slots, at least one is not assigned.
    """
    window_size = max_slots + 1
    
    for start_idx in range(n_slots - window_size + 1):
        window_vars = []
        for offset in range(window_size):
            slot_idx = start_idx + offset
            if (task_idx, slot_idx) in x:
                window_vars.append(x[(task_idx, slot_idx)])
        
        if window_vars:
            # At most max_slots can be assigned in this window
            model.Add(sum(window_vars) <= max_slots)


def add_precedence_constraints(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex
):
    """
    Add precedence constraints for task dependencies.
    
    Ensures prerequisite tasks are completed before dependent tasks start.
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    # Build task ID to index mapping
    task_id_to_idx = {task.id: i for i, task in enumerate(tasks)}
    n_slots = len(time_index)
    
    precedence_count = 0
    
    for t_idx, task in enumerate(tasks):
        if not task.prerequisites:
            continue
        
        # Find prerequisite task indices
        prereq_indices = []
        for prereq_id in task.prerequisites:
            if prereq_id in task_id_to_idx:
                prereq_indices.append(task_id_to_idx[prereq_id])
        
        if not prereq_indices:
            continue
        
        # For each prerequisite
        for prereq_idx in prereq_indices:
            # Calculate latest completion slot for prerequisite
            prereq_end_var = model.NewIntVar(0, n_slots - 1, f"prereq_end_{prereq_idx}")
            
            # End slot is the maximum assigned slot (or 0 if none assigned)
            prereq_slots = [(task_idx, s_idx) for s_idx in range(n_slots) 
                           if (prereq_idx, s_idx) in x]
            
            if prereq_slots:
                end_terms = []
                any_assigned = model.NewBoolVar(f"prereq_assigned_{prereq_idx}")
                
                # any_assigned = 1 if any slot is assigned
                model.Add(any_assigned <= sum(x[(prereq_idx, s_idx)] for s_idx in range(n_slots)
                                             if (prereq_idx, s_idx) in x))
                
                # If assigned, end_var >= max assigned slot
                for s_idx in range(n_slots):
                    if (prereq_idx, s_idx) in x:
                        assigned_here = x[(prereq_idx, s_idx)]
                        model.Add(prereq_end_var >= s_idx * assigned_here)
            
            # Calculate earliest start slot for dependent task
            task_start_var = model.NewIntVar(0, n_slots - 1, f"task_start_{t_idx}")
            
            # Start slot is the minimum assigned slot (or n_slots-1 if none assigned)
            task_slots = [(t_idx, s_idx) for s_idx in range(n_slots)
                         if (t_idx, s_idx) in x]
            
            if task_slots:
                for s_idx in range(n_slots):
                    if (t_idx, s_idx) in x:
                        # If assigned to this slot, start must be <= this slot
                        model.Add(task_start_var <= s_idx + n_slots * (1 - x[(t_idx, s_idx)]))
                        # If assigned to this slot and no earlier assignment, this is start
                        earlier_assignments = sum(x[(t_idx, earlier)] for earlier in range(s_idx)
                                                if (t_idx, earlier) in x)
                        model.Add(task_start_var >= s_idx - n_slots * (1 - x[(t_idx, s_idx)] + earlier_assignments))
            
            # Precedence constraint: prerequisite must end before dependent starts
            # Add small gap (1 slot) to ensure clear precedence
            model.Add(prereq_end_var + 1 <= task_start_var)
            
        precedence_count += 1
    
    logger.debug(f"Added precedence constraints for {precedence_count} tasks")


def add_daily_caps(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    prefs: Preferences,
    time_index: TimeIndex
):
    """
    Add daily effort limit constraints.
    
    Ensures total scheduled work per day doesn't exceed user limits.
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    if prefs.max_daily_effort_minutes <= 0:
        return
    
    max_daily_slots = int(prefs.max_daily_effort_minutes / time_index.granularity_minutes)
    n_tasks = max(t_idx for t_idx, _ in x.keys()) + 1 if x else 0
    
    # Get unique dates in horizon
    dates = list(set(slot.date() for slot in time_index.slots))
    
    for date in dates:
        # Get all slots for this date
        day_start = datetime.combine(date, datetime.min.time())
        day_slots = time_index.get_day_indices(day_start)
        
        # Sum all task assignments for this day
        daily_vars = []
        for t_idx in range(n_tasks):
            for s_idx in day_slots:
                if s_idx < len(time_index) and (t_idx, s_idx) in x:
                    daily_vars.append(x[(t_idx, s_idx)])
        
        if daily_vars:
            model.Add(sum(daily_vars) <= max_daily_slots)
    
    logger.debug(f"Added daily caps for {len(dates)} days")


def add_spacing_for_exam(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex,
    prefs: Preferences
):
    """
    Add spacing constraints for exam preparation.
    
    Ensures exam preparation is distributed across multiple days
    rather than crammed into single sessions.
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    spacing_policy = prefs.spacing_policy
    if not spacing_policy or 'exam' not in spacing_policy:
        return
    
    exam_tasks = [(i, task) for i, task in enumerate(tasks) if task.kind == 'exam']
    if not exam_tasks:
        return
    
    # Parse spacing policy (e.g., "2-3 spaced blocks/day")
    policy = spacing_policy['exam']
    
    for t_idx, task in exam_tasks:
        if task.deadline:
            # Find study period (e.g., 7 days before exam)
            study_period_days = 7
            study_start = task.deadline - timedelta(days=study_period_days)
            
            # Get dates in study period
            current_date = study_start
            study_dates = []
            while current_date < task.deadline:
                study_dates.append(current_date.date())
                current_date += timedelta(days=1)
            
            # Encourage distribution across days
            min_study_days = min(3, len(study_dates))
            
            if len(study_dates) >= min_study_days:
                # Create binary variables for "studied on day X"
                day_vars = []
                for date in study_dates:
                    day_var = model.NewBoolVar(f"exam_study_{t_idx}_{date}")
                    
                    # Link to actual slot assignments
                    day_start = datetime.combine(date, datetime.min.time())
                    day_slots = time_index.get_day_indices(day_start)
                    
                    day_assignments = [x[(t_idx, s_idx)] for s_idx in day_slots
                                     if (t_idx, s_idx) in x]
                    
                    if day_assignments:
                        # day_var = 1 if any assignment on this day
                        model.Add(day_var <= sum(day_assignments))
                        # Force day_var = 1 if total assignments >= 1
                        model.Add(day_var >= sum(day_assignments) / len(day_assignments))
                    
                    day_vars.append(day_var)
                
                # Require minimum number of study days
                if day_vars:
                    model.Add(sum(day_vars) >= min_study_days)
    
    logger.debug(f"Added spacing constraints for {len(exam_tasks)} exam tasks")


def add_workday_constraints(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    prefs: Preferences,
    time_index: TimeIndex
):
    """
    Add constraints to respect workday hours.
    
    Prevents scheduling outside user's preferred working hours.
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    n_tasks = max(t_idx for t_idx, _ in x.keys()) + 1 if x else 0
    
    # Parse workday hours
    try:
        workday_start_hour = int(prefs.workday_start.split(':')[0])
        workday_end_hour = int(prefs.workday_end.split(':')[0])
    except:
        # Use defaults if parsing fails
        workday_start_hour = 8
        workday_end_hour = 22
    
    blocked_count = 0
    
    for s_idx in range(len(time_index)):
        slot_context = time_index.get_slot_context(s_idx)
        hour = slot_context.get('hour', 12)
        
        # Block slots outside workday hours
        if hour < workday_start_hour or hour >= workday_end_hour:
            for t_idx in range(n_tasks):
                if (t_idx, s_idx) in x:
                    model.Add(x[(t_idx, s_idx)] == 0)
                    blocked_count += 1
    
    logger.debug(f"Blocked {blocked_count} slots outside workday hours")


def add_preferred_window_constraints(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex,
    weight: float = 1.0
) -> List:
    """
    Add soft constraints for preferred time windows.
    
    Returns penalty variables that can be used in objective function.
    """
    if not ORTOOLS_AVAILABLE:
        return []
    
    penalty_vars = []
    
    for t_idx, task in enumerate(tasks):
        if not task.preferred_windows:
            continue
        
        for s_idx in range(len(time_index)):
            if (t_idx, s_idx) not in x:
                continue
                
            slot_dt = time_index.index_to_datetime(s_idx)
            if slot_dt is None:
                continue
            
            # Check if slot is in preferred window
            in_preferred = False
            for window in task.preferred_windows:
                if _datetime_in_window(slot_dt, window):
                    in_preferred = True
                    break
            
            # If not in preferred window, add penalty
            if not in_preferred:
                penalty_var = model.NewIntVar(0, 1, f"not_preferred_{t_idx}_{s_idx}")
                model.Add(penalty_var == x[(t_idx, s_idx)])
                penalty_vars.append(penalty_var)
    
    return penalty_vars


def _datetime_in_window(dt: datetime, window: Dict) -> bool:
    """Check if datetime falls within a time window specification."""
    dow = window.get('dow')  # Day of week (0=Monday, 6=Sunday)
    start_time = window.get('start')  # "HH:MM"
    end_time = window.get('end')      # "HH:MM"
    
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
                # Normal time range (e.g., 9:00-17:00)
                return start <= dt_time <= end
            else:
                # Overnight range (e.g., 22:00-06:00)
                return dt_time >= start or dt_time <= end
        except ValueError:
            logger.warning(f"Invalid time format in window: {window}")
            return False
    
    return True