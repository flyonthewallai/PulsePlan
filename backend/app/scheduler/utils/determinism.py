"""
Deterministic scheduling and stability guarantees.

Provides RNG seeding, stable sorting, inertia costs, and frozen windows
to ensure consistent scheduling behavior and minimize thrashing.
"""

import hashlib
import random
import logging
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

import numpy as np

from ..core.domain import Task, BusyEvent, ScheduleBlock, ScheduleSolution

logger = logging.getLogger(__name__)


@dataclass
class DeterminismConfig:
    """Configuration for deterministic scheduling behavior."""
    random_seed: int = 42
    inertia_penalty_weight: float = 5.0
    frozen_window_hours: int = 12
    max_move_ratio_threshold: float = 0.2
    stable_sort_enabled: bool = True


class DeterministicScheduler:
    """
    Ensures deterministic and stable scheduling behavior.

    Features:
    - Seeded RNG for reproducible results
    - Stable sorting to break ties consistently
    - Inertia penalties to minimize block movement
    - Frozen windows to protect near-term schedule
    """

    def __init__(self, config: Optional[DeterminismConfig] = None):
        """Initialize deterministic scheduler with configuration."""
        self.config = config or DeterminismConfig()
        self._seed_rngs()

    def _seed_rngs(self):
        """Seed all random number generators for reproducibility."""
        # Python built-in random
        random.seed(self.config.random_seed)

        # NumPy random
        np.random.seed(self.config.random_seed)

        # OR-Tools will be seeded in solver initialization
        logger.debug(f"Seeded RNGs with seed: {self.config.random_seed}")

    def stable_sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Sort tasks with stable tie-breaking for deterministic ordering.

        Sort order:
        1. Due date (earliest first)
        2. Course ID (alphabetical)
        3. Task ID (UUID, for final deterministic tie-breaking)

        Args:
            tasks: List of tasks to sort

        Returns:
            Deterministically sorted tasks
        """
        if not self.config.stable_sort_enabled:
            return tasks

        def sort_key(task: Task) -> tuple:
            # Use epoch timestamp for None deadline (sorts to end)
            due_timestamp = task.deadline.timestamp() if task.deadline else float('inf')
            course_id = task.course_id or 'zzz_no_course'  # Sort no course to end
            task_id = task.id

            return (due_timestamp, course_id, task_id)

        sorted_tasks = sorted(tasks, key=sort_key)
        logger.debug(f"Stable sorted {len(sorted_tasks)} tasks")
        return sorted_tasks

    def calculate_existing_blocks_hash(self, blocks: List[ScheduleBlock]) -> str:
        """
        Calculate deterministic hash of existing schedule blocks.

        Used to detect schedule changes and measure stability.

        Args:
            blocks: List of existing schedule blocks

        Returns:
            Deterministic hash string
        """
        if not blocks:
            return "empty_schedule"

        # Create deterministic representation
        block_signatures = []
        for block in sorted(blocks, key=lambda b: (b.start, b.task_id)):
            signature = f"{block.task_id}:{block.start.isoformat()}:{block.end.isoformat()}"
            block_signatures.append(signature)

        combined = "|".join(block_signatures)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def get_frozen_window(self, now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Get the frozen window where existing blocks should not be moved.

        Args:
            now: Current time (defaults to datetime.now())

        Returns:
            Tuple of (window_start, window_end)
        """
        if now is None:
            now = datetime.now()

        window_start = now
        window_end = now + timedelta(hours=self.config.frozen_window_hours)

        return window_start, window_end

    def identify_locked_blocks(
        self,
        existing_blocks: List[ScheduleBlock],
        now: Optional[datetime] = None
    ) -> Set[str]:
        """
        Identify blocks that should not be moved (locked or manual).

        Args:
            existing_blocks: Current schedule blocks
            now: Current time (defaults to datetime.now())

        Returns:
            Set of task IDs for blocks that should not be moved
        """
        if now is None:
            now = datetime.now()

        frozen_start, frozen_end = self.get_frozen_window(now)
        locked_task_ids = set()

        for block in existing_blocks:
            # Lock if explicitly marked as locked or manual
            if getattr(block, 'locked', False) or getattr(block, 'manual', False):
                locked_task_ids.add(block.task_id)
                continue

            # Lock if in frozen window
            if block.start >= frozen_start and block.start < frozen_end:
                locked_task_ids.add(block.task_id)
                continue

        logger.debug(f"Identified {len(locked_task_ids)} locked tasks in frozen window")
        return locked_task_ids

    def calculate_inertia_penalties(
        self,
        current_solution: ScheduleSolution,
        existing_blocks: List[ScheduleBlock],
        now: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate inertia penalties for moving existing blocks.

        Higher penalties for:
        - Moving blocks in frozen window
        - Moving manually placed blocks
        - Moving recently scheduled blocks

        Args:
            current_solution: Proposed new schedule
            existing_blocks: Current schedule blocks
            now: Current time

        Returns:
            Dictionary mapping task_id to inertia penalty
        """
        if now is None:
            now = datetime.now()

        penalties = {}
        existing_by_task = {block.task_id: block for block in existing_blocks}
        frozen_start, frozen_end = self.get_frozen_window(now)

        for new_block in current_solution.blocks:
            task_id = new_block.task_id
            existing_block = existing_by_task.get(task_id)

            if not existing_block:
                # No penalty for new blocks
                penalties[task_id] = 0.0
                continue

            # Calculate time distance moved
            time_moved_hours = abs(
                (new_block.start - existing_block.start).total_seconds() / 3600
            )

            # Base penalty proportional to movement
            base_penalty = time_moved_hours * self.config.inertia_penalty_weight

            # Multipliers for special cases
            multiplier = 1.0

            # High penalty for moving frozen blocks
            if existing_block.start >= frozen_start and existing_block.start < frozen_end:
                multiplier *= 3.0

            # High penalty for moving manual blocks
            if getattr(existing_block, 'manual', False):
                multiplier *= 2.0

            # High penalty for moving locked blocks (should be prevented elsewhere)
            if getattr(existing_block, 'locked', False):
                multiplier *= 5.0

            penalties[task_id] = base_penalty * multiplier

        return penalties

    def calculate_stability_metrics(
        self,
        new_solution: ScheduleSolution,
        existing_blocks: List[ScheduleBlock]
    ) -> Dict[str, float]:
        """
        Calculate stability metrics comparing new vs existing schedule.

        Args:
            new_solution: Proposed new schedule
            existing_blocks: Current schedule blocks

        Returns:
            Dictionary with stability metrics
        """
        if not existing_blocks:
            return {
                'moved_block_ratio': 0.0,
                'avg_move_distance_hours': 0.0,
                'blocks_added': len(new_solution.blocks),
                'blocks_removed': 0,
                'stability_score': 1.0
            }

        existing_by_task = {block.task_id: block for block in existing_blocks}
        new_by_task = {block.task_id: block for block in new_solution.blocks}

        # Count moved blocks
        moved_count = 0
        total_move_hours = 0.0

        for task_id, new_block in new_by_task.items():
            existing_block = existing_by_task.get(task_id)
            if existing_block:
                # Check if significantly moved (>15 minutes)
                time_diff = abs((new_block.start - existing_block.start).total_seconds())
                if time_diff > 900:  # 15 minutes
                    moved_count += 1
                    total_move_hours += time_diff / 3600

        # Calculate metrics
        total_existing = len(existing_blocks)
        moved_ratio = moved_count / total_existing if total_existing > 0 else 0.0
        avg_move_distance = total_move_hours / moved_count if moved_count > 0 else 0.0

        blocks_added = len([tid for tid in new_by_task if tid not in existing_by_task])
        blocks_removed = len([tid for tid in existing_by_task if tid not in new_by_task])

        # Overall stability score (0-1, higher is more stable)
        stability_score = max(0.0, 1.0 - (moved_ratio + blocks_removed / total_existing))

        return {
            'moved_block_ratio': moved_ratio,
            'avg_move_distance_hours': avg_move_distance,
            'blocks_added': blocks_added,
            'blocks_removed': blocks_removed,
            'blocks_moved': moved_count,
            'stability_score': stability_score
        }

    def validate_no_thrash_guarantee(
        self,
        new_solution: ScheduleSolution,
        existing_blocks: List[ScheduleBlock],
        threshold: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate that the new schedule doesn't thrash (move too many blocks).

        Args:
            new_solution: Proposed new schedule
            existing_blocks: Current schedule blocks
            threshold: Maximum allowed move ratio (defaults to config)

        Returns:
            Tuple of (is_valid, reason)
        """
        if threshold is None:
            threshold = self.config.max_move_ratio_threshold

        metrics = self.calculate_stability_metrics(new_solution, existing_blocks)
        moved_ratio = metrics['moved_block_ratio']

        if moved_ratio <= threshold:
            return True, f"Move ratio {moved_ratio:.1%} within threshold {threshold:.1%}"
        else:
            return False, f"Thrashing detected: {moved_ratio:.1%} > {threshold:.1%} threshold"

    def ensure_deterministic_solution(
        self,
        solution: ScheduleSolution,
        request_hash: str
    ) -> ScheduleSolution:
        """
        Ensure solution is deterministic by sorting blocks and adding metadata.

        Args:
            solution: Original solution
            request_hash: Hash of the input request

        Returns:
            Solution with deterministic block ordering and metadata
        """
        # Sort blocks deterministically
        sorted_blocks = sorted(
            solution.blocks,
            key=lambda b: (b.start, b.task_id)
        )

        # Add determinism metadata
        solution_metadata = getattr(solution, 'diagnostics', {})
        solution_metadata.update({
            'determinism_seed': self.config.random_seed,
            'input_hash': request_hash,
            'block_count': len(sorted_blocks),
            'solution_hash': self.calculate_existing_blocks_hash(sorted_blocks)
        })

        # Return new solution with sorted blocks and metadata
        return ScheduleSolution(
            feasible=solution.feasible,
            blocks=sorted_blocks,
            objective_value=solution.objective_value,
            solve_time_ms=solution.solve_time_ms,
            solver_status=solution.solver_status,
            total_scheduled_minutes=solution.total_scheduled_minutes,
            unscheduled_tasks=sorted(solution.unscheduled_tasks),  # Also sort these
            diagnostics=solution_metadata,
            explanations=solution.explanations
        )


def create_request_hash(
    tasks: List[Task],
    events: List[BusyEvent],
    horizon_days: int,
    user_id: str
) -> str:
    """
    Create deterministic hash of scheduling request inputs.

    Args:
        tasks: Tasks to schedule
        events: Calendar events
        horizon_days: Scheduling horizon
        user_id: User identifier

    Returns:
        Deterministic hash of inputs
    """
    hash_components = []

    # Sort tasks and events for deterministic hashing
    sorted_tasks = sorted(tasks, key=lambda t: t.id)
    sorted_events = sorted(events, key=lambda e: e.id)

    # Add task signatures
    for task in sorted_tasks:
        task_sig = f"{task.id}:{task.estimated_minutes}:{task.deadline}"
        hash_components.append(task_sig)

    # Add event signatures
    for event in sorted_events:
        event_sig = f"{event.id}:{event.start}:{event.end}"
        hash_components.append(event_sig)

    # Add other parameters
    hash_components.extend([
        f"horizon:{horizon_days}",
        f"user:{user_id}"
    ])

    combined = "|".join(hash_components)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


# Global deterministic scheduler instance
_deterministic_scheduler = None

def get_deterministic_scheduler(config: Optional[DeterminismConfig] = None) -> DeterministicScheduler:
    """Get global deterministic scheduler instance."""
    global _deterministic_scheduler
    if _deterministic_scheduler is None or config is not None:
        _deterministic_scheduler = DeterministicScheduler(config)
    return _deterministic_scheduler