"""
Fallback greedy scheduler for when OR-Tools fails or times out.

Provides a simple but effective heuristic-based scheduling algorithm
that can always produce a feasible solution if one exists.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from heapq import heappush, heappop

from ..core.domain import Task, BusyEvent, Preferences, ScheduleBlock, ScheduleSolution
from .time_index import TimeIndex

logger = logging.getLogger(__name__)


class GreedyScheduler:
    """
    Greedy heuristic scheduler for fallback scenarios.
    
    Uses priority-based task selection with best-fit slot assignment
    to produce reasonable schedules when optimization fails.
    """
    
    def __init__(self):
        """Initialize greedy scheduler."""
        self.debug_info = []
    
    def schedule(
        self,
        tasks: List[Task],
        free_slots: List[int],
        prefs: Preferences,
        util_matrix: Dict[str, Dict[int, float]],
        time_index: TimeIndex
    ) -> ScheduleSolution:
        """
        Generate schedule using greedy heuristics.
        
        Args:
            tasks: Tasks to schedule
            free_slots: Available time slot indices
            prefs: User preferences
            util_matrix: Utility scores for task/slot combinations
            time_index: Time discretization
            
        Returns:
            Schedule solution with assigned blocks
        """
        start_time = datetime.now()
        
        # Sort tasks by priority
        prioritized_tasks = self._prioritize_tasks(tasks, time_index)
        
        # Initialize state
        assigned_blocks = []
        remaining_slots = set(free_slots)
        unscheduled_tasks = []
        
        # Process tasks in priority order
        for task in prioritized_tasks:
            blocks = self._assign_task(
                task, remaining_slots, util_matrix, time_index, prefs
            )
            
            if blocks:
                assigned_blocks.extend(blocks)
                
                # Remove used slots
                for block in blocks:
                    block_slots = time_index.window_to_indices(
                        block.start, block.end, inclusive_end=False
                    )
                    remaining_slots -= set(block_slots)
                
                logger.debug(f"Assigned task {task.title} to {len(blocks)} blocks")
            else:
                unscheduled_tasks.append(task.id)
                logger.warning(f"Could not schedule task {task.title}")
        
        solve_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Calculate objective value (simplified)
        objective_value = sum(block.utility_score for block in assigned_blocks)
        
        solution = ScheduleSolution(
            feasible=True,
            blocks=assigned_blocks,
            objective_value=objective_value,
            solve_time_ms=solve_time_ms,
            solver_status="greedy_heuristic",
            unscheduled_tasks=unscheduled_tasks,
            diagnostics={
                'method': 'greedy',
                'total_tasks': len(tasks),
                'scheduled_tasks': len(tasks) - len(unscheduled_tasks),
                'total_blocks': len(assigned_blocks),
                'debug_info': self.debug_info[-10:]  # Recent debug info
            }
        )
        
        logger.info(
            f"Greedy scheduler completed: {len(assigned_blocks)} blocks, "
            f"{len(unscheduled_tasks)} unscheduled tasks, "
            f"time={solve_time_ms}ms"
        )
        
        return solution
    
    def _prioritize_tasks(self, tasks: List[Task], time_index: TimeIndex) -> List[Task]:
        """
        Sort tasks by scheduling priority.
        
        Uses multiple criteria:
        1. Deadline urgency
        2. Task weight/importance
        3. Scheduling difficulty (fewer available slots)
        """
        def priority_score(task: Task) -> Tuple[float, float, float]:
            # Deadline urgency (higher = more urgent)
            if task.deadline:
                days_remaining = (task.deadline - time_index.start_dt).days
                urgency = max(0, 14 - days_remaining) / 14.0
            else:
                urgency = 0.0
            
            # Task importance (higher = more important)
            importance = task.weight
            
            # Difficulty (approximation - higher = harder to schedule)
            difficulty = task.estimated_minutes / max(1, task.min_block_minutes)
            
            # Return tuple for sorting (negate values we want to maximize)
            return (-urgency, -importance, difficulty)
        
        return sorted(tasks, key=priority_score)
    
    def _assign_task(
        self,
        task: Task,
        available_slots: set,
        util_matrix: Dict[str, Dict[int, float]],
        time_index: TimeIndex,
        prefs: Preferences
    ) -> List[ScheduleBlock]:
        """
        Assign a single task to available time slots.
        
        Args:
            task: Task to assign
            available_slots: Set of available slot indices
            util_matrix: Utility scores
            time_index: Time discretization
            prefs: User preferences
            
        Returns:
            List of schedule blocks for the task
        """
        if not available_slots:
            return []
        
        # Calculate required slots
        required_slots = int(np.ceil(task.estimated_minutes / time_index.granularity_minutes))
        min_block_slots = int(np.ceil(task.min_block_minutes / time_index.granularity_minutes))
        
        if task.max_block_minutes > 0:
            max_block_slots = int(task.max_block_minutes / time_index.granularity_minutes)
        else:
            max_block_slots = required_slots  # No limit
        
        # Find available contiguous blocks
        contiguous_blocks = self._find_contiguous_blocks(
            available_slots, time_index, min_block_slots, max_block_slots
        )
        
        if not contiguous_blocks:
            self.debug_info.append(f"No contiguous blocks for task {task.title}")
            return []
        
        # Score and sort blocks by utility
        scored_blocks = self._score_blocks(
            task, contiguous_blocks, util_matrix, time_index, prefs
        )
        
        # Assign task using best blocks
        return self._assign_using_best_blocks(
            task, scored_blocks, required_slots, time_index
        )
    
    def _find_contiguous_blocks(
        self,
        available_slots: set,
        time_index: TimeIndex,
        min_slots: int,
        max_slots: int
    ) -> List[List[int]]:
        """
        Find all contiguous blocks of available slots.
        
        Args:
            available_slots: Set of available slot indices
            time_index: Time discretization
            min_slots: Minimum block size
            max_slots: Maximum block size
            
        Returns:
            List of contiguous slot blocks
        """
        if not available_slots:
            return []
        
        # Sort available slots
        sorted_slots = sorted(available_slots)
        
        # Group into contiguous sequences
        sequences = []
        current_seq = [sorted_slots[0]]
        
        for slot_idx in sorted_slots[1:]:
            if slot_idx == current_seq[-1] + 1:
                current_seq.append(slot_idx)
            else:
                if len(current_seq) >= min_slots:
                    sequences.append(current_seq)
                current_seq = [slot_idx]
        
        # Add final sequence
        if len(current_seq) >= min_slots:
            sequences.append(current_seq)
        
        # Split long sequences into max_slots chunks
        blocks = []
        for seq in sequences:
            if len(seq) <= max_slots:
                blocks.append(seq)
            else:
                # Split into multiple blocks
                for start in range(0, len(seq), max_slots):
                    block = seq[start:start + max_slots]
                    if len(block) >= min_slots:
                        blocks.append(block)
        
        return blocks
    
    def _score_blocks(
        self,
        task: Task,
        blocks: List[List[int]],
        util_matrix: Dict[str, Dict[int, float]],
        time_index: TimeIndex,
        prefs: Preferences
    ) -> List[Tuple[float, List[int]]]:
        """
        Score contiguous blocks for task assignment.
        
        Args:
            task: Task being assigned
            blocks: List of contiguous slot blocks
            util_matrix: Utility scores
            time_index: Time discretization
            prefs: User preferences
            
        Returns:
            List of (score, block) tuples, sorted by score descending
        """
        scored_blocks = []
        task_utils = util_matrix.get(task.id, {})
        
        for block in blocks:
            score = 0.0
            
            # Base utility score
            block_utility = sum(task_utils.get(slot_idx, 0.0) for slot_idx in block)
            score += block_utility
            
            # Time preference bonuses/penalties
            score += self._calculate_time_preferences(task, block, time_index, prefs)
            
            # Block quality bonuses
            score += self._calculate_block_quality(task, block, time_index)
            
            scored_blocks.append((score, block))
        
        # Sort by score descending
        return sorted(scored_blocks, key=lambda x: x[0], reverse=True)
    
    def _calculate_time_preferences(
        self,
        task: Task,
        block: List[int],
        time_index: TimeIndex,
        prefs: Preferences
    ) -> float:
        """Calculate score adjustment based on time preferences."""
        score = 0.0
        
        for slot_idx in block:
            slot_dt = time_index.index_to_datetime(slot_idx)
            if slot_dt is None:
                continue
            
            slot_context = time_index.get_slot_context(slot_idx)
            
            # Preferred/avoided windows for task
            if task.preferred_windows:
                in_preferred = any(
                    self._datetime_in_window(slot_dt, window)
                    for window in task.preferred_windows
                )
                if in_preferred:
                    score += 2.0
            
            if task.avoid_windows:
                in_avoided = any(
                    self._datetime_in_window(slot_dt, window)
                    for window in task.avoid_windows
                )
                if in_avoided:
                    score -= 3.0
            
            # General time preferences
            if slot_context.get('is_weekend', False):
                score -= 1.0  # Slight weekend penalty
            
            hour = slot_context.get('hour', 12)
            if hour >= 22 or hour < 6:
                score -= 2.0  # Late night/early morning penalty
            elif 9 <= hour <= 17:
                score += 1.0  # Work hours bonus
        
        return score
    
    def _calculate_block_quality(
        self,
        task: Task,
        block: List[int],
        time_index: TimeIndex
    ) -> float:
        """Calculate score based on block characteristics."""
        score = 0.0
        block_duration = len(block) * time_index.granularity_minutes
        
        # Prefer blocks close to ideal size
        ideal_duration = min(task.estimated_minutes, task.max_block_minutes or float('inf'))
        size_ratio = block_duration / ideal_duration
        
        if 0.8 <= size_ratio <= 1.2:
            score += 2.0  # Good size match
        elif size_ratio < 0.5:
            score -= 1.0  # Too small
        elif size_ratio > 2.0:
            score -= 1.0  # Too large
        
        # Prefer longer blocks (less fragmentation)
        if block_duration >= 90:  # 90+ minutes
            score += 1.0
        
        return score
    
    def _assign_using_best_blocks(
        self,
        task: Task,
        scored_blocks: List[Tuple[float, List[int]]],
        required_slots: int,
        time_index: TimeIndex
    ) -> List[ScheduleBlock]:
        """
        Assign task using the best available blocks.
        
        Args:
            task: Task to assign
            scored_blocks: Scored and sorted blocks
            required_slots: Total slots needed
            time_index: Time discretization
            
        Returns:
            List of schedule blocks
        """
        if not scored_blocks:
            return []
        
        assigned_blocks = []
        remaining_slots = required_slots
        used_slot_indices = set()
        
        for score, block in scored_blocks:
            if remaining_slots <= 0:
                break
            
            # Check for conflicts with already assigned slots
            if any(slot_idx in used_slot_indices for slot_idx in block):
                continue
            
            # Determine how much of this block to use
            slots_to_use = min(len(block), remaining_slots)
            selected_slots = block[:slots_to_use]
            
            # Create schedule block
            start_time, end_time = time_index.indices_to_window(selected_slots)
            
            schedule_block = ScheduleBlock(
                task_id=task.id,
                start=start_time,
                end=end_time,
                utility_score=score / len(selected_slots),  # Normalize by block size
                estimated_completion_probability=0.7  # Default estimate
            )
            
            assigned_blocks.append(schedule_block)
            used_slot_indices.update(selected_slots)
            remaining_slots -= slots_to_use
        
        # Check if we assigned enough time
        total_assigned_time = sum(block.duration_minutes for block in assigned_blocks)
        
        if total_assigned_time < task.estimated_minutes * 0.8:  # Allow 20% tolerance
            self.debug_info.append(
                f"Insufficient time assigned to {task.title}: "
                f"{total_assigned_time}/{task.estimated_minutes} minutes"
            )
        
        return assigned_blocks
    
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
                    return dt_time >= start or dt_time <= end
            except:
                return False
        
        return True


def greedy_fill(
    tasks: List[Task],
    free_slots: List[int],
    prefs: Preferences,
    util_matrix: Dict[str, Dict[int, float]],
    time_index: TimeIndex
) -> ScheduleSolution:
    """
    Main entry point for greedy fallback scheduling.
    
    Args:
        tasks: Tasks to schedule
        free_slots: Available time slots
        prefs: User preferences
        util_matrix: Utility matrix from ML models
        time_index: Time discretization
        
    Returns:
        Schedule solution
    """
    scheduler = GreedyScheduler()
    return scheduler.schedule(tasks, free_slots, prefs, util_matrix, time_index)