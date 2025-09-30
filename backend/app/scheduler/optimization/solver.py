"""
OR-Tools based constraint satisfaction solver for scheduling optimization.

Uses Google OR-Tools CP-SAT solver to find optimal task assignments while
respecting hard constraints and minimizing soft constraint violations.
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
    logging.warning("OR-Tools not available, solver will use fallback")
    # Create a dummy cp_model for type annotations
    class cp_model:
        class CpModel:
            pass
        class CpSolver:
            def ObjectiveValue(self):
                return 0
        class CpSolverSolutionCallback:
            def __init__(self):
                pass
        # Constants
        OPTIMAL = "OPTIMAL"
        FEASIBLE = "FEASIBLE"
        INFEASIBLE = "INFEASIBLE"
        MODEL_INVALID = "MODEL_INVALID"
        UNKNOWN = "UNKNOWN"
        INT32_MAX = 2147483647

from ..core.domain import Task, BusyEvent, Preferences, ScheduleBlock, ScheduleSolution
from .time_index import TimeIndex
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class SchedulerSolver:
    """
    Constraint satisfaction solver for task scheduling.
    
    Uses CP-SAT to solve the scheduling optimization problem with both
    hard constraints (deadlines, conflicts) and soft constraints (preferences).
    """
    
    def __init__(
        self,
        time_limit_seconds: int = 10,
        num_search_workers: int = 4,
        random_seed: int = 42
    ):
        """
        Initialize scheduler solver.
        
        Args:
            time_limit_seconds: Maximum solve time
            num_search_workers: Number of parallel search workers
            random_seed: Random seed for reproducibility
        """
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools is required for SchedulerSolver")
            
        self.time_limit_seconds = time_limit_seconds
        self.num_search_workers = num_search_workers
        self.random_seed = random_seed
        self.timezone_manager = get_timezone_manager()

        # Solution tracking
        self.best_solution = None
        self.solution_callback = None
        
    def build(
        self,
        tasks: List[Task],
        busy_events: List[BusyEvent],
        prefs: Preferences,
        time_index: TimeIndex,
        learned: Dict[str, Any]
    ) -> cp_model.CpModel:
        """
        Build the constraint satisfaction model.
        
        Args:
            tasks: Tasks to schedule
            busy_events: Calendar events that block time
            prefs: User preferences and constraints
            time_index: Time discretization
            learned: ML-derived utilities and penalties
            
        Returns:
            CP-SAT model ready for solving
        """
        model = cp_model.CpModel()
        
        # Problem dimensions
        n_tasks = len(tasks)
        n_slots = len(time_index)
        
        # Create decision variables
        # x[t, s] = 1 if task t is assigned to slot s
        x = {}
        for t_idx, task in enumerate(tasks):
            for s_idx in range(n_slots):
                var_name = f"x_{task.id}_{s_idx}"
                x[(t_idx, s_idx)] = model.NewBoolVar(var_name)
        
        # Store variables for constraint building
        self.variables = {
            'x': x,
            'tasks': tasks,
            'time_index': time_index,
            'prefs': prefs,
            'busy_events': busy_events,
            'learned': learned
        }
        
        # Build constraints
        self._add_hard_constraints(model)
        self._add_soft_constraints(model)
        
        # Build objective
        self._build_objective(model)
        
        return model
    
    def solve(
        self, 
        model: cp_model.CpModel,
        hints: Optional[Dict] = None
    ) -> ScheduleSolution:
        """
        Solve the scheduling model.
        
        Args:
            model: CP-SAT model to solve
            hints: Optional solution hints for warm start
            
        Returns:
            Schedule solution with blocks and metadata
        """
        solver = cp_model.CpSolver()
        
        # Configure solver
        solver.parameters.max_time_in_seconds = self.time_limit_seconds
        solver.parameters.num_search_workers = self.num_search_workers
        solver.parameters.random_seed = self.random_seed
        solver.parameters.log_search_progress = False
        
        # Add solution callback to track best solution
        callback = SolutionCallback(self.variables)
        
        # Apply hints if provided
        if hints:
            self._apply_hints(model, hints)
        
        start_time = datetime.now()
        
        # Solve
        status = solver.Solve(model, callback)
        
        solve_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Extract solution
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            solution = self._extract_solution(solver, callback, solve_time_ms)
            solution.feasible = True
            solution.solver_status = self._status_to_string(status)
        else:
            # No feasible solution found
            solution = ScheduleSolution(
                feasible=False,
                blocks=[],
                solve_time_ms=solve_time_ms,
                solver_status=self._status_to_string(status),
                diagnostics={
                    'infeasible_reason': self._diagnose_infeasibility(model, solver),
                    'n_tasks': len(self.variables['tasks']),
                    'n_slots': len(self.variables['time_index']),
                    'time_limit_hit': solve_time_ms >= self.time_limit_seconds * 1000
                }
            )
        
        logger.info(
            f"Solver finished: {solution.solver_status}, "
            f"feasible={solution.feasible}, "
            f"time={solve_time_ms}ms, "
            f"blocks={len(solution.blocks)}"
        )
        
        return solution
    
    def _add_hard_constraints(self, model: cp_model.CpModel):
        """Add hard constraints that must be satisfied."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        busy_events = self.variables['busy_events']
        prefs = self.variables['prefs']
        
        # 1. Slot capacity constraint: max one task per slot
        for s_idx in range(len(time_index)):
            slot_vars = [x[(t_idx, s_idx)] for t_idx in range(len(tasks))]
            model.Add(sum(slot_vars) <= 1)
        
        # 2. Busy event constraints: no overlap with hard calendar events
        blocked_slots = time_index.filter_busy_slots(busy_events)
        for s_idx in blocked_slots:
            for t_idx in range(len(tasks)):
                model.Add(x[(t_idx, s_idx)] == 0)
        
        # 3. Task completion constraints: assign enough total time
        for t_idx, task in enumerate(tasks):
            task_slots = [x[(t_idx, s_idx)] for s_idx in range(len(time_index))]
            required_slots = int(np.ceil(task.estimated_minutes / time_index.granularity_minutes))
            model.Add(sum(task_slots) >= required_slots)
        
        # 4. Minimum block length constraints
        for t_idx, task in enumerate(tasks):
            min_block_slots = int(np.ceil(task.min_block_minutes / time_index.granularity_minutes))
            if min_block_slots > 1:
                self._add_min_block_constraint(model, t_idx, min_block_slots)
        
        # 5. Deadline constraints
        for t_idx, task in enumerate(tasks):
            if task.deadline:
                deadline_idx = time_index.datetime_to_index(task.deadline)
                if deadline_idx is not None:
                    # All task slots must be before deadline
                    for s_idx in range(deadline_idx, len(time_index)):
                        model.Add(x[(t_idx, s_idx)] == 0)
        
        # 6. Earliest start constraints
        for t_idx, task in enumerate(tasks):
            if task.earliest_start:
                earliest_idx = time_index.datetime_to_index(task.earliest_start)
                if earliest_idx is not None:
                    # No task slots before earliest start
                    for s_idx in range(min(earliest_idx, len(time_index))):
                        model.Add(x[(t_idx, s_idx)] == 0)
        
        # 7. Precedence constraints
        for t_idx, task in enumerate(tasks):
            if task.prerequisites:
                self._add_precedence_constraints(model, t_idx, task.prerequisites)
        
        # 8. Daily effort caps
        if prefs.max_daily_effort_minutes > 0:
            self._add_daily_effort_constraints(model)
        
        # 9. Pinned slot constraints
        for t_idx, task in enumerate(tasks):
            if task.pinned_slots:
                self._add_pinned_slot_constraints(model, t_idx, task.pinned_slots)
    
    def _add_min_block_constraint(self, model: cp_model.CpModel, task_idx: int, min_slots: int):
        """Add minimum contiguous block length constraint for a task."""
        x = self.variables['x']
        n_slots = len(self.variables['time_index'])
        
        # For each potential starting position, if task starts there,
        # it must continue for at least min_slots
        for start_idx in range(n_slots - min_slots + 1):
            # Create boolean for "task starts at start_idx"
            starts_here = model.NewBoolVar(f"starts_{task_idx}_{start_idx}")
            
            # starts_here = 1 iff x[start_idx] = 1 and (start_idx == 0 or x[start_idx-1] = 0)
            if start_idx == 0:
                model.Add(starts_here == x[(task_idx, start_idx)])
            else:
                # starts_here <= x[start_idx]
                model.Add(starts_here <= x[(task_idx, start_idx)])
                # starts_here <= 1 - x[start_idx-1]
                model.Add(starts_here <= 1 - x[(task_idx, start_idx - 1)])
                # starts_here >= x[start_idx] - x[start_idx-1]
                model.Add(starts_here >= x[(task_idx, start_idx)] - x[(task_idx, start_idx - 1)])
            
            # If task starts here, ensure minimum block length
            for offset in range(min_slots):
                slot_idx = start_idx + offset
                if slot_idx < n_slots:
                    model.Add(x[(task_idx, slot_idx)] >= starts_here)
    
    def _add_precedence_constraints(self, model: cp_model.CpModel, task_idx: int, prereq_ids: List[str]):
        """Add precedence constraints for task dependencies."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        n_slots = len(self.variables['time_index'])
        
        # Find prerequisite task indices
        task_id_to_idx = {task.id: i for i, task in enumerate(tasks)}
        prereq_indices = [task_id_to_idx[pid] for pid in prereq_ids if pid in task_id_to_idx]
        
        if not prereq_indices:
            return
        
        # Calculate latest slot for each task (weighted sum)
        task_end_slot = model.NewIntVar(0, n_slots - 1, f"end_slot_{task_idx}")
        model.Add(task_end_slot == sum(s_idx * x[(task_idx, s_idx)] for s_idx in range(n_slots)))
        
        for prereq_idx in prereq_indices:
            prereq_end_slot = model.NewIntVar(0, n_slots - 1, f"end_slot_{prereq_idx}")
            model.Add(prereq_end_slot == sum(s_idx * x[(prereq_idx, s_idx)] for s_idx in range(n_slots)))
            
            # Prerequisite must end before dependent task starts
            model.Add(prereq_end_slot < task_end_slot)
    
    def _add_daily_effort_constraints(self, model: cp_model.CpModel):
        """Add daily effort limit constraints."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        prefs = self.variables['prefs']
        
        max_daily_slots = int(prefs.max_daily_effort_minutes / time_index.granularity_minutes)
        
        # Get unique dates in horizon
        dates = list(set(slot.date() for slot in time_index.slots))
        
        for date in dates:
            day_slots = time_index.get_day_indices(datetime.combine(date, datetime.min.time()))
            
            # Sum all task assignments for this day
            daily_vars = []
            for t_idx in range(len(tasks)):
                for s_idx in day_slots:
                    if s_idx < len(time_index):
                        daily_vars.append(x[(t_idx, s_idx)])
            
            if daily_vars:
                model.Add(sum(daily_vars) <= max_daily_slots)
    
    def _add_pinned_slot_constraints(self, model: cp_model.CpModel, task_idx: int, pinned_slots: List[Dict]):
        """Add constraints for pinned time slots."""
        x = self.variables['x']
        time_index = self.variables['time_index']
        
        for pin in pinned_slots:
            start_time = pin.get('start')
            end_time = pin.get('end')
            
            if start_time and end_time:
                # Convert to slot indices
                pinned_indices = time_index.window_to_indices(start_time, end_time, inclusive_end=True)
                
                # Task must be scheduled in these slots
                for s_idx in pinned_indices:
                    if s_idx < len(time_index):
                        model.Add(x[(task_idx, s_idx)] == 1)
    
    def _add_soft_constraints(self, model: cp_model.CpModel):
        """Add soft constraints as penalty variables."""
        # Soft constraints are handled in the objective function
        # This method can be used to create auxiliary variables if needed
        pass
    
    def _build_objective(self, model: cp_model.CpModel):
        """Build the objective function maximizing utility and minimizing penalties."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        learned = self.variables['learned']
        
        # Extract utilities and weights
        util_matrix = learned.get('util', {})
        weights = learned.get('weights', {})
        
        objective_terms = []
        
        # 1. Utility terms (to maximize)
        for t_idx, task in enumerate(tasks):
            task_utils = util_matrix.get(task.id, {})
            for s_idx in range(len(time_index)):
                utility = task_utils.get(s_idx, 0.0)
                if utility > 0:
                    # Scale utility to integer (OR-Tools works with integers)
                    scaled_utility = int(utility * 1000)
                    objective_terms.append(scaled_utility * x[(t_idx, s_idx)])
        
        # 2. Penalty terms (to minimize)
        penalty_terms = self._build_penalty_terms(model)
        
        # Combine terms
        if objective_terms or penalty_terms:
            total_objective = sum(objective_terms) - sum(penalty_terms)
            model.Maximize(total_objective)
        else:
            # Fallback: maximize total scheduled time
            total_scheduled = sum(x[(t_idx, s_idx)] 
                                for t_idx in range(len(tasks))
                                for s_idx in range(len(time_index)))
            model.Maximize(total_scheduled)
    
    def _build_penalty_terms(self, model: cp_model.CpModel) -> List:
        """Build penalty terms for soft constraint violations."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        prefs = self.variables['prefs']
        weights = self.variables['learned'].get('weights', {})
        
        penalty_terms = []
        
        # 1. Context switch penalties
        context_switch_weight = int(weights.get('context_switch', 2.0) * 1000)
        if context_switch_weight > 0:
            switches = self._create_context_switch_vars(model)
            penalty_terms.extend([context_switch_weight * switch for switch in switches])
        
        # 2. Avoid window penalties
        avoid_window_weight = int(weights.get('avoid_window', 1.5) * 1000)
        if avoid_window_weight > 0:
            avoid_violations = self._create_avoid_window_vars(model)
            penalty_terms.extend([avoid_window_weight * violation for violation in avoid_violations])
        
        # 3. Late night penalties
        late_night_weight = int(weights.get('late_night', 3.0) * 1000)
        if late_night_weight > 0:
            late_vars = self._create_late_night_vars(model)
            penalty_terms.extend([late_night_weight * var for var in late_vars])
        
        # 4. Fragmentation penalties
        fragmentation_weight = int(weights.get('fragmentation', 1.2) * 1000)
        if fragmentation_weight > 0:
            frag_vars = self._create_fragmentation_vars(model)
            penalty_terms.extend([fragmentation_weight * var for var in frag_vars])
        
        return penalty_terms
    
    def _create_context_switch_vars(self, model: cp_model.CpModel) -> List:
        """Create variables for context switching penalties."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        n_slots = len(self.variables['time_index'])
        
        switch_vars = []
        
        # For each adjacent pair of slots, penalize different tasks
        for s_idx in range(n_slots - 1):
            for t1_idx in range(len(tasks)):
                for t2_idx in range(len(tasks)):
                    if t1_idx != t2_idx:
                        # Create switch variable
                        switch_var = model.NewBoolVar(f"switch_{t1_idx}_{t2_idx}_{s_idx}")
                        
                        # switch_var = 1 iff task t1 in slot s and task t2 in slot s+1
                        model.Add(switch_var <= x[(t1_idx, s_idx)])
                        model.Add(switch_var <= x[(t2_idx, s_idx + 1)])
                        model.Add(switch_var >= x[(t1_idx, s_idx)] + x[(t2_idx, s_idx + 1)] - 1)
                        
                        switch_vars.append(switch_var)
        
        return switch_vars
    
    def _create_avoid_window_vars(self, model: cp_model.CpModel) -> List:
        """Create variables for avoid window violations."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        
        avoid_vars = []
        
        for t_idx, task in enumerate(tasks):
            if not task.avoid_windows:
                continue
                
            for s_idx in range(len(time_index)):
                slot_dt = time_index.index_to_datetime(s_idx)
                if slot_dt is None:
                    continue
                
                # Check if slot is in any avoid window
                in_avoid_window = False
                for window in task.avoid_windows:
                    if self._datetime_in_window(slot_dt, window):
                        in_avoid_window = True
                        break
                
                if in_avoid_window:
                    # Penalize assignment to this slot
                    avoid_vars.append(x[(t_idx, s_idx)])
        
        return avoid_vars
    
    def _create_late_night_vars(self, model: cp_model.CpModel) -> List:
        """Create variables for late night penalties."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        
        late_vars = []
        
        # Define late night hours (after 10 PM)
        late_hour_threshold = 22
        
        for t_idx in range(len(tasks)):
            for s_idx in range(len(time_index)):
                slot_context = time_index.get_slot_context(s_idx)
                if slot_context.get('hour', 12) >= late_hour_threshold:
                    late_vars.append(x[(t_idx, s_idx)])
        
        return late_vars
    
    def _create_fragmentation_vars(self, model: cp_model.CpModel) -> List:
        """Create variables for task fragmentation penalties."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        n_slots = len(self.variables['time_index'])
        
        frag_vars = []
        
        # For each task, penalize gaps in assignment
        for t_idx in range(len(tasks)):
            for s_idx in range(1, n_slots - 1):
                # Create gap variable: task assigned to s-1 and s+1 but not s
                gap_var = model.NewBoolVar(f"gap_{t_idx}_{s_idx}")
                
                # gap_var = 1 iff x[s-1] = 1, x[s] = 0, x[s+1] = 1
                model.Add(gap_var <= x[(t_idx, s_idx - 1)])
                model.Add(gap_var <= 1 - x[(t_idx, s_idx)])
                model.Add(gap_var <= x[(t_idx, s_idx + 1)])
                model.Add(gap_var >= x[(t_idx, s_idx - 1)] + (1 - x[(t_idx, s_idx)]) + x[(t_idx, s_idx + 1)] - 2)
                
                frag_vars.append(gap_var)
        
        return frag_vars
    
    def _datetime_in_window(self, dt: datetime, window: Dict) -> bool:
        """Check if datetime falls within a time window."""
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
            except:
                return False
        
        return True
    
    def _apply_hints(self, model: cp_model.CpModel, hints: Dict):
        """Apply solution hints for warm start."""
        # TODO: Implement solution hints
        pass
    
    def _extract_solution(
        self, 
        solver: cp_model.CpSolver, 
        callback, 
        solve_time_ms: int
    ) -> ScheduleSolution:
        """Extract solution from solved model."""
        x = self.variables['x']
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        
        blocks = []
        unscheduled_tasks = []
        
        for t_idx, task in enumerate(tasks):
            task_slots = []
            
            # Find assigned slots for this task
            for s_idx in range(len(time_index)):
                if solver.Value(x[(t_idx, s_idx)]) == 1:
                    task_slots.append(s_idx)
            
            if task_slots:
                # Group into contiguous blocks
                slot_groups = time_index.get_contiguous_blocks(task_slots)
                
                for group in slot_groups:
                    start_time, end_time = time_index.indices_to_window(group)
                    
                    # Get utility score for first slot (representative)
                    util_matrix = self.variables['learned'].get('util', {})
                    task_utils = util_matrix.get(task.id, {})
                    utility_score = task_utils.get(group[0], 0.0)
                    
                    block = ScheduleBlock(
                        task_id=task.id,
                        start=start_time,
                        end=end_time,
                        utility_score=utility_score,
                        estimated_completion_probability=0.7  # Would come from ML model
                    )
                    blocks.append(block)
            else:
                unscheduled_tasks.append(task.id)
        
        # Calculate objective value
        objective_value = solver.ObjectiveValue() if solver.ObjectiveValue() != cp_model.INT32_MAX else 0
        
        return ScheduleSolution(
            feasible=True,
            blocks=blocks,
            objective_value=float(objective_value) / 1000.0,  # Unscale
            solve_time_ms=solve_time_ms,
            unscheduled_tasks=unscheduled_tasks,
            diagnostics={
                'n_variables': len(x),
                'n_constraints': solver.NumConstraints() if hasattr(solver, 'NumConstraints') else 0,
                'objective_bound': solver.BestObjectiveBound() if hasattr(solver, 'BestObjectiveBound') else 0
            }
        )
    
    def _status_to_string(self, status) -> str:
        """Convert solver status to string."""
        status_map = {
            cp_model.OPTIMAL: "optimal",
            cp_model.FEASIBLE: "feasible", 
            cp_model.INFEASIBLE: "infeasible",
            cp_model.MODEL_INVALID: "invalid",
            cp_model.UNKNOWN: "unknown"
        }
        return status_map.get(status, "unknown")
    
    def _diagnose_infeasibility(self, model: cp_model.CpModel, solver: cp_model.CpSolver) -> str:
        """Provide diagnosis for infeasible problems."""
        # Basic infeasibility diagnosis
        diagnostics = []
        
        tasks = self.variables['tasks']
        time_index = self.variables['time_index']
        busy_events = self.variables['busy_events']
        
        # Check if there's enough total time
        total_required_time = sum(task.estimated_minutes for task in tasks)
        blocked_slots = time_index.filter_busy_slots(busy_events)
        available_slots = len(time_index) - len(blocked_slots)
        available_time = available_slots * time_index.granularity_minutes
        
        if total_required_time > available_time:
            diagnostics.append(f"Insufficient time: need {total_required_time}min, have {available_time}min")
        
        # Check deadline conflicts
        for task in tasks:
            if task.deadline:
                deadline_idx = time_index.datetime_to_index(task.deadline)
                if deadline_idx is not None:
                    slots_before_deadline = deadline_idx
                    available_before_deadline = slots_before_deadline - len([
                        s for s in blocked_slots if s < deadline_idx
                    ])
                    time_before_deadline = available_before_deadline * time_index.granularity_minutes
                    
                    if task.estimated_minutes > time_before_deadline:
                        diagnostics.append(f"Task {task.title} cannot meet deadline")
        
        return "; ".join(diagnostics) if diagnostics else "Unknown infeasibility"


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    """Callback to track best solution during solving."""
    
    def __init__(self, variables: Dict):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.variables = variables
        self.solution_count = 0
        self.best_objective = float('-inf')
        
    def on_solution_callback(self):
        """Called when a new solution is found."""
        self.solution_count += 1
        objective = self.ObjectiveValue()
        
        if objective > self.best_objective:
            self.best_objective = objective
            
        # Could store solution details here if needed

