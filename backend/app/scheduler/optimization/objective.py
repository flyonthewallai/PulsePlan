"""
Objective function construction for the scheduling optimizer.

Builds utility maximization and penalty minimization objectives for the CP-SAT solver.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from ..core.domain import Task, Preferences
from .time_index import TimeIndex

logger = logging.getLogger(__name__)


def build_objective(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    util_matrix: Dict[str, Dict[int, float]],
    penalties: Dict[str, List],
    weights: Dict[str, float]
) -> None:
    """
    Build the complete objective function for the scheduling problem.
    
    Combines utility maximization with weighted penalty minimization.
    
    Args:
        model: CP-SAT model
        x: Decision variables x[task_idx, slot_idx]
        tasks: List of tasks being scheduled
        util_matrix: Utility values util_matrix[task_id][slot_idx]
        penalties: Penalty variables by type
        weights: Penalty weights
    """
    if not ORTOOLS_AVAILABLE:
        return
    
    objective_terms = []
    
    # 1. Utility maximization terms
    utility_terms = build_utility_terms(x, tasks, util_matrix)
    objective_terms.extend(utility_terms)
    
    # 2. Penalty minimization terms
    penalty_terms = build_penalty_terms(penalties, weights)
    
    # Combine terms (maximize utility, minimize penalties)
    if objective_terms or penalty_terms:
        total_objective = sum(objective_terms) - sum(penalty_terms)
        model.Maximize(total_objective)
        
        logger.debug(
            f"Objective built: {len(utility_terms)} utility terms, "
            f"{len(penalty_terms)} penalty terms"
        )
    else:
        # Fallback: maximize total scheduled slots
        n_tasks = len(tasks)
        n_slots = max(s_idx for _, s_idx in x.keys()) + 1 if x else 0
        
        total_scheduled = sum(
            x[(t_idx, s_idx)] 
            for t_idx in range(n_tasks)
            for s_idx in range(n_slots)
            if (t_idx, s_idx) in x
        )
        model.Maximize(total_scheduled)
        logger.debug("Using fallback objective: maximize scheduled slots")


def build_utility_terms(
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    util_matrix: Dict[str, Dict[int, float]]
) -> List:
    """
    Build utility maximization terms.
    
    Args:
        x: Decision variables
        tasks: List of tasks
        util_matrix: Utility values per task per slot
        
    Returns:
        List of utility terms for objective
    """
    utility_terms = []
    
    for t_idx, task in enumerate(tasks):
        task_utils = util_matrix.get(task.id, {})
        
        for slot_idx, utility in task_utils.items():
            if (t_idx, slot_idx) in x and utility > 0:
                # Scale utility to integer (OR-Tools prefers integers)
                scaled_utility = int(utility * 1000)
                utility_terms.append(scaled_utility * x[(t_idx, slot_idx)])
    
    return utility_terms


def build_penalty_terms(
    penalties: Dict[str, List],
    weights: Dict[str, float]
) -> List:
    """
    Build penalty minimization terms.
    
    Args:
        penalties: Penalty variables by type
        weights: Penalty weights
        
    Returns:
        List of weighted penalty terms
    """
    penalty_terms = []
    
    for penalty_type, penalty_vars in penalties.items():
        weight = weights.get(penalty_type, 1.0)
        scaled_weight = int(weight * 1000)  # Scale for integer arithmetic
        
        for penalty_var in penalty_vars:
            penalty_terms.append(scaled_weight * penalty_var)
    
    return penalty_terms


def create_context_switch_penalties(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex
) -> List:
    """
    Create penalty variables for context switching between different tasks.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks
        time_index: Time discretization
        
    Returns:
        List of context switch penalty variables
    """
    if not ORTOOLS_AVAILABLE:
        return []
    
    penalty_vars = []
    n_slots = len(time_index)
    n_tasks = len(tasks)
    
    # For each pair of adjacent time slots
    for s_idx in range(n_slots - 1):
        current_slot = s_idx
        next_slot = s_idx + 1
        
        # For each pair of different tasks
        for t1_idx in range(n_tasks):
            for t2_idx in range(n_tasks):
                if t1_idx == t2_idx:
                    continue  # No penalty for same task
                
                if ((t1_idx, current_slot) not in x or 
                    (t2_idx, next_slot) not in x):
                    continue
                
                # Create switch penalty variable
                switch_var = model.NewBoolVar(f"switch_{t1_idx}_{t2_idx}_{s_idx}")
                
                # switch_var = 1 iff task t1 in current slot AND task t2 in next slot
                model.Add(switch_var <= x[(t1_idx, current_slot)])
                model.Add(switch_var <= x[(t2_idx, next_slot)])
                model.Add(switch_var >= x[(t1_idx, current_slot)] + x[(t2_idx, next_slot)] - 1)
                
                penalty_vars.append(switch_var)
    
    return penalty_vars


def create_avoid_window_penalties(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex
) -> List:
    """
    Create penalty variables for scheduling in avoided time windows.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks with avoid windows
        time_index: Time discretization
        
    Returns:
        List of avoid window penalty variables
    """
    if not ORTOOLS_AVAILABLE:
        return []
    
    penalty_vars = []
    
    for t_idx, task in enumerate(tasks):
        if not task.avoid_windows:
            continue
        
        for s_idx in range(len(time_index)):
            if (t_idx, s_idx) not in x:
                continue
            
            slot_dt = time_index.index_to_datetime(s_idx)
            if slot_dt is None:
                continue
            
            # Check if slot falls in any avoid window
            in_avoid_window = False
            for window in task.avoid_windows:
                if _datetime_in_window(slot_dt, window):
                    in_avoid_window = True
                    break
            
            if in_avoid_window:
                # Create penalty variable equal to the assignment variable
                penalty_var = model.NewIntVar(0, 1, f"avoid_{t_idx}_{s_idx}")
                model.Add(penalty_var == x[(t_idx, s_idx)])
                penalty_vars.append(penalty_var)
    
    return penalty_vars


def create_time_preference_penalties(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex,
    prefs: Preferences
) -> Dict[str, List]:
    """
    Create penalty variables for time-based preferences.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks
        time_index: Time discretization
        prefs: User preferences
        
    Returns:
        Dictionary of penalty variables by type
    """
    if not ORTOOLS_AVAILABLE:
        return {}
    
    penalties = {
        'late_night': [],
        'early_morning': [],
        'weekend': []
    }
    
    # Define time thresholds
    late_night_hour = 22  # 10 PM
    early_morning_hour = 6  # 6 AM
    
    n_tasks = len(tasks)
    
    for s_idx in range(len(time_index)):
        slot_context = time_index.get_slot_context(s_idx)
        hour = slot_context.get('hour', 12)
        is_weekend = slot_context.get('is_weekend', False)
        
        for t_idx in range(n_tasks):
            if (t_idx, s_idx) not in x:
                continue
            
            # Late night penalty
            if hour >= late_night_hour:
                penalty_var = model.NewIntVar(0, 1, f"late_night_{t_idx}_{s_idx}")
                model.Add(penalty_var == x[(t_idx, s_idx)])
                penalties['late_night'].append(penalty_var)
            
            # Early morning penalty
            if hour < early_morning_hour:
                penalty_var = model.NewIntVar(0, 1, f"early_morning_{t_idx}_{s_idx}")
                model.Add(penalty_var == x[(t_idx, s_idx)])
                penalties['early_morning'].append(penalty_var)
            
            # Weekend penalty (if user prefers weekdays)
            if is_weekend:
                penalty_var = model.NewIntVar(0, 1, f"weekend_{t_idx}_{s_idx}")
                model.Add(penalty_var == x[(t_idx, s_idx)])
                penalties['weekend'].append(penalty_var)
    
    return penalties


def create_fragmentation_penalties(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex
) -> List:
    """
    Create penalty variables for task fragmentation (gaps in assignments).
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks
        time_index: Time discretization
        
    Returns:
        List of fragmentation penalty variables
    """
    if not ORTOOLS_AVAILABLE:
        return []
    
    penalty_vars = []
    n_slots = len(time_index)
    
    for t_idx in range(len(tasks)):
        # For each potential gap position (middle of 3 consecutive slots)
        for s_idx in range(1, n_slots - 1):
            prev_slot = s_idx - 1
            curr_slot = s_idx
            next_slot = s_idx + 1
            
            if not all((t_idx, slot) in x for slot in [prev_slot, curr_slot, next_slot]):
                continue
            
            # Create gap penalty variable
            # gap = 1 iff task assigned to prev and next but not current
            gap_var = model.NewBoolVar(f"gap_{t_idx}_{s_idx}")
            
            # gap_var <= x[prev] (if gap, then prev must be assigned)
            model.Add(gap_var <= x[(t_idx, prev_slot)])
            
            # gap_var <= 1 - x[curr] (if gap, then curr must not be assigned)
            model.Add(gap_var <= 1 - x[(t_idx, curr_slot)])
            
            # gap_var <= x[next] (if gap, then next must be assigned)
            model.Add(gap_var <= x[(t_idx, next_slot)])
            
            # gap_var >= x[prev] + (1 - x[curr]) + x[next] - 2
            model.Add(gap_var >= (x[(t_idx, prev_slot)] + 
                                 (1 - x[(t_idx, curr_slot)]) + 
                                 x[(t_idx, next_slot)] - 2))
            
            penalty_vars.append(gap_var)
    
    return penalty_vars


def create_fairness_penalties(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex
) -> List:
    """
    Create penalty variables for course/subject fairness.
    
    Penalizes uneven distribution of time across different courses.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks
        time_index: Time discretization
        
    Returns:
        List of fairness penalty variables
    """
    if not ORTOOLS_AVAILABLE:
        return []
    
    penalty_vars = []
    
    # Group tasks by course
    course_tasks = {}
    for t_idx, task in enumerate(tasks):
        course_id = task.course_id or "default"
        if course_id not in course_tasks:
            course_tasks[course_id] = []
        course_tasks[course_id].append(t_idx)
    
    if len(course_tasks) <= 1:
        return []  # No fairness needed with single course
    
    # Calculate total assignments per course
    course_totals = {}
    for course_id, task_indices in course_tasks.items():
        total_var = model.NewIntVar(0, len(time_index) * len(task_indices), 
                                   f"course_total_{course_id}")
        
        course_assignments = []
        for t_idx in task_indices:
            for s_idx in range(len(time_index)):
                if (t_idx, s_idx) in x:
                    course_assignments.append(x[(t_idx, s_idx)])
        
        if course_assignments:
            model.Add(total_var == sum(course_assignments))
            course_totals[course_id] = total_var
    
    # Create fairness penalties for each pair of courses
    course_ids = list(course_totals.keys())
    for i in range(len(course_ids)):
        for j in range(i + 1, len(course_ids)):
            course1 = course_ids[i]
            course2 = course_ids[j]
            
            # Create variables for absolute difference
            diff_var = model.NewIntVar(0, len(time_index) * len(tasks), 
                                      f"course_diff_{course1}_{course2}")
            
            # diff_var = |total1 - total2|
            model.AddAbsEquality(diff_var, course_totals[course1] - course_totals[course2])
            
            penalty_vars.append(diff_var)
    
    return penalty_vars


def create_spacing_penalties(
    model: cp_model.CpModel,
    x: Dict[Tuple[int, int], Any],
    tasks: List[Task],
    time_index: TimeIndex,
    prefs: Preferences
) -> List:
    """
    Create penalty variables for violating spacing policies.
    
    Args:
        model: CP-SAT model
        x: Decision variables
        tasks: List of tasks
        time_index: Time discretization
        prefs: User preferences with spacing policies
        
    Returns:
        List of spacing violation penalty variables
    """
    if not ORTOOLS_AVAILABLE:
        return []
    
    penalty_vars = []
    spacing_policy = prefs.spacing_policy
    
    if not spacing_policy:
        return []
    
    # Handle exam spacing
    if 'exam' in spacing_policy:
        exam_tasks = [(i, task) for i, task in enumerate(tasks) if task.kind == 'exam']
        
        for t_idx, task in exam_tasks:
            if task.deadline:
                # Get dates leading up to exam
                study_dates = _get_study_dates(task.deadline, days_back=7)
                
                # Encourage distribution across days
                for date in study_dates:
                    day_slots = time_index.get_day_indices(
                        datetime.combine(date, datetime.min.time())
                    )
                    
                    # Penalize having too much or too little on any day
                    day_assignments = [x[(t_idx, s_idx)] for s_idx in day_slots
                                     if (t_idx, s_idx) in x]
                    
                    if day_assignments:
                        day_total = model.NewIntVar(0, len(day_assignments), 
                                                   f"exam_day_total_{t_idx}_{date}")
                        model.Add(day_total == sum(day_assignments))
                        
                        # Penalty for zero (no study) or excessive study
                        zero_penalty = model.NewBoolVar(f"exam_zero_{t_idx}_{date}")
                        model.Add(zero_penalty == (day_total == 0))
                        penalty_vars.append(zero_penalty)
                        
                        # Penalty for excessive study (more than 4 hours)
                        max_daily_slots = 4 * 60 // time_index.granularity_minutes
                        if len(day_assignments) > max_daily_slots:
                            excess_var = model.NewIntVar(0, len(day_assignments), 
                                                        f"exam_excess_{t_idx}_{date}")
                            model.Add(excess_var >= day_total - max_daily_slots)
                            penalty_vars.append(excess_var)
    
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
                return start <= dt_time <= end
            else:
                # Overnight range
                return dt_time >= start or dt_time <= end
        except ValueError:
            return False
    
    return True


def _get_study_dates(deadline: datetime, days_back: int = 7) -> List:
    """Get list of dates for exam study period."""
    study_start = deadline - timedelta(days=days_back)
    dates = []
    
    current = study_start
    while current < deadline:
        dates.append(current.date())
        current += timedelta(days=1)
    
    return dates