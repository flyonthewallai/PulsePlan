"""
Intelligent replanning scope controls.

Provides sophisticated controls to limit the scope of replanning operations,
preventing unnecessary disruption while maintaining schedule quality.
"""

import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.domain import Task, ScheduleBlock, Preferences, BusyEvent
from ..optimization.time_index import TimeIndex
from ...core.utils.timezone_utils import get_timezone_manager, safe_datetime_comparison

logger = logging.getLogger(__name__)


class ReplanScope(Enum):
    """Defines the scope of replanning operations."""
    MINIMAL = "minimal"          # Only reschedule absolutely necessary blocks
    CONSERVATIVE = "conservative"  # Limited changes, preserve most of schedule
    MODERATE = "moderate"        # Balanced approach with reasonable changes
    AGGRESSIVE = "aggressive"    # Allow major changes for optimization
    COMPLETE = "complete"        # Full replanning, ignore existing schedule


class ChangeType(Enum):
    """Types of changes that can be made during replanning."""
    NONE = "none"
    MOVE = "move"               # Change start/end time
    SPLIT = "split"             # Split into multiple blocks
    MERGE = "merge"             # Merge with adjacent blocks
    RESCHEDULE = "reschedule"   # Move to different day/time
    CANCEL = "cancel"           # Remove from schedule


@dataclass
class ReplanConstraint:
    """Constraints that limit replanning scope."""
    # Time-based constraints
    earliest_change_time: Optional[datetime] = None  # Don't change blocks before this time
    latest_change_time: Optional[datetime] = None    # Don't change blocks after this time
    frozen_periods: List[Tuple[datetime, datetime]] = None  # Time periods that cannot be changed

    # Block-based constraints
    protected_task_ids: Set[str] = None             # Tasks that cannot be moved
    protected_block_ids: Set[str] = None            # Specific blocks that cannot be moved
    max_blocks_to_move: Optional[int] = None        # Limit total number of blocks to move
    max_move_distance_hours: Optional[float] = None # Maximum distance blocks can be moved

    # Quality constraints
    min_stability_ratio: float = 0.8               # Minimum fraction of blocks to keep stable
    max_disruption_score: float = 100.0            # Maximum allowed disruption score
    preserve_adjacency: bool = True                 # Try to keep related blocks together

    def __post_init__(self):
        """Initialize empty collections if None."""
        if self.frozen_periods is None:
            self.frozen_periods = []
        if self.protected_task_ids is None:
            self.protected_task_ids = set()
        if self.protected_block_ids is None:
            self.protected_block_ids = set()


@dataclass
class ReplanResult:
    """Result of replanning analysis."""
    allowed_changes: Dict[str, List[ChangeType]]    # block_id -> allowed change types
    protected_blocks: Set[str]                      # block_ids that cannot be changed
    move_candidates: List[str]                      # block_ids that can be moved
    merge_opportunities: List[Tuple[str, str]]      # pairs of blocks that can be merged
    disruption_score: float                         # Overall disruption score (0-100)
    stability_ratio: float                          # Fraction of blocks remaining stable


class ReplanningController:
    """
    Intelligent controller for managing replanning scope and constraints.

    Analyzes existing schedules and determines what changes are allowed
    based on user preferences, stability requirements, and optimization goals.
    """

    def __init__(self):
        """Initialize replanning controller."""
        self.scope_presets = self._create_scope_presets()

    def analyze_replanning_scope(
        self,
        existing_blocks: List[ScheduleBlock],
        new_tasks: List[Task],
        busy_events: List[BusyEvent],
        preferences: Preferences,
        scope: ReplanScope = ReplanScope.MODERATE,
        custom_constraints: Optional[ReplanConstraint] = None,
        time_index: Optional[TimeIndex] = None
    ) -> ReplanResult:
        """
        Analyze what changes are allowed during replanning.

        Args:
            existing_blocks: Current schedule blocks
            new_tasks: Tasks to be scheduled
            busy_events: Calendar conflicts
            preferences: User preferences
            scope: Overall replanning scope
            custom_constraints: Additional constraints
            time_index: Time discretization info

        Returns:
            Analysis of allowed changes and constraints
        """
        # Get base constraints for the scope
        constraints = self._get_scope_constraints(scope)

        # Apply custom constraints if provided
        if custom_constraints:
            constraints = self._merge_constraints(constraints, custom_constraints)

        # Apply time-based filters
        constraints = self._apply_time_filters(constraints, time_index, preferences)

        # Analyze existing blocks
        disruption_analysis = self._analyze_disruption_potential(
            existing_blocks, new_tasks, busy_events, constraints
        )

        # Determine allowed changes per block
        allowed_changes = self._determine_allowed_changes(
            existing_blocks, disruption_analysis, constraints
        )

        # Find optimization opportunities
        move_candidates = self._find_move_candidates(existing_blocks, constraints, disruption_analysis)
        merge_opportunities = self._find_merge_opportunities(existing_blocks, constraints)

        # Calculate metrics
        disruption_score = self._calculate_disruption_score(disruption_analysis)
        stability_ratio = self._calculate_stability_ratio(existing_blocks, allowed_changes)

        # Identify protected blocks
        protected_blocks = self._identify_protected_blocks(existing_blocks, constraints)

        logger.info(
            f"Replanning analysis: scope={scope.value}, "
            f"protected={len(protected_blocks)}, candidates={len(move_candidates)}, "
            f"disruption={disruption_score:.1f}, stability={stability_ratio:.2f}"
        )

        return ReplanResult(
            allowed_changes=allowed_changes,
            protected_blocks=protected_blocks,
            move_candidates=move_candidates,
            merge_opportunities=merge_opportunities,
            disruption_score=disruption_score,
            stability_ratio=stability_ratio
        )

    def filter_existing_blocks(
        self,
        existing_blocks: List[ScheduleBlock],
        replan_result: ReplanResult
    ) -> Tuple[List[ScheduleBlock], List[ScheduleBlock]]:
        """
        Split existing blocks into protected and changeable sets.

        Args:
            existing_blocks: All existing schedule blocks
            replan_result: Analysis result from analyze_replanning_scope

        Returns:
            Tuple of (protected_blocks, changeable_blocks)
        """
        protected = []
        changeable = []

        for block in existing_blocks:
            if block.task_id in replan_result.protected_blocks:
                protected.append(block)
            else:
                changeable.append(block)

        logger.debug(f"Split blocks: {len(protected)} protected, {len(changeable)} changeable")
        return protected, changeable

    def validate_replanning_result(
        self,
        original_blocks: List[ScheduleBlock],
        new_blocks: List[ScheduleBlock],
        replan_result: ReplanResult
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a replanning result respects the constraints.

        Args:
            original_blocks: Original schedule blocks
            new_blocks: Proposed new schedule blocks
            replan_result: Replanning constraints

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []

        # Check stability ratio
        original_block_map = {b.task_id: b for b in original_blocks}
        unchanged_count = 0

        for new_block in new_blocks:
            if new_block.task_id in original_block_map:
                original = original_block_map[new_block.task_id]
                if self._blocks_substantially_same(original, new_block):
                    unchanged_count += 1

        actual_stability = unchanged_count / len(original_blocks) if original_blocks else 1.0

        if actual_stability < replan_result.stability_ratio * 0.9:  # 10% tolerance
            violations.append(
                f"Stability ratio {actual_stability:.2f} below minimum {replan_result.stability_ratio:.2f}"
            )

        # Check protected blocks weren't changed
        for block_id in replan_result.protected_blocks:
            original_block = next((b for b in original_blocks if b.task_id == block_id), None)
            new_block = next((b for b in new_blocks if b.task_id == block_id), None)

            if original_block and new_block:
                if not self._blocks_substantially_same(original_block, new_block):
                    violations.append(f"Protected block {block_id} was modified")
            elif original_block and not new_block:
                violations.append(f"Protected block {block_id} was removed")

        is_valid = len(violations) == 0
        return is_valid, violations

    def _create_scope_presets(self) -> Dict[ReplanScope, ReplanConstraint]:
        """Create default constraint presets for each scope level."""
        return {
            ReplanScope.MINIMAL: ReplanConstraint(
                max_blocks_to_move=2,
                max_move_distance_hours=1.0,
                min_stability_ratio=0.95,
                max_disruption_score=20.0,
                preserve_adjacency=True
            ),
            ReplanScope.CONSERVATIVE: ReplanConstraint(
                max_blocks_to_move=5,
                max_move_distance_hours=4.0,
                min_stability_ratio=0.85,
                max_disruption_score=40.0,
                preserve_adjacency=True
            ),
            ReplanScope.MODERATE: ReplanConstraint(
                max_blocks_to_move=10,
                max_move_distance_hours=12.0,
                min_stability_ratio=0.70,
                max_disruption_score=60.0,
                preserve_adjacency=True
            ),
            ReplanScope.AGGRESSIVE: ReplanConstraint(
                max_blocks_to_move=20,
                max_move_distance_hours=48.0,
                min_stability_ratio=0.50,
                max_disruption_score=80.0,
                preserve_adjacency=False
            ),
            ReplanScope.COMPLETE: ReplanConstraint(
                max_blocks_to_move=None,
                max_move_distance_hours=None,
                min_stability_ratio=0.0,
                max_disruption_score=100.0,
                preserve_adjacency=False
            )
        }

    def _get_scope_constraints(self, scope: ReplanScope) -> ReplanConstraint:
        """Get base constraints for a scope level."""
        return self.scope_presets.get(scope, self.scope_presets[ReplanScope.MODERATE])

    def _merge_constraints(
        self,
        base: ReplanConstraint,
        custom: ReplanConstraint
    ) -> ReplanConstraint:
        """Merge custom constraints with base constraints."""
        # Custom constraints override base constraints
        merged = ReplanConstraint(
            earliest_change_time=custom.earliest_change_time or base.earliest_change_time,
            latest_change_time=custom.latest_change_time or base.latest_change_time,
            frozen_periods=base.frozen_periods + custom.frozen_periods,
            protected_task_ids=base.protected_task_ids | custom.protected_task_ids,
            protected_block_ids=base.protected_block_ids | custom.protected_block_ids,
            max_blocks_to_move=custom.max_blocks_to_move or base.max_blocks_to_move,
            max_move_distance_hours=custom.max_move_distance_hours or base.max_move_distance_hours,
            min_stability_ratio=max(base.min_stability_ratio, custom.min_stability_ratio),
            max_disruption_score=min(base.max_disruption_score, custom.max_disruption_score),
            preserve_adjacency=base.preserve_adjacency and custom.preserve_adjacency
        )
        return merged

    def _apply_time_filters(
        self,
        constraints: ReplanConstraint,
        time_index: Optional[TimeIndex],
        preferences: Preferences
    ) -> ReplanConstraint:
        """Apply time-based filtering to constraints."""
        if not time_index:
            return constraints

        # Add imminent deadlines to frozen periods
        now = datetime.now()

        # Handle timezone-aware comparison using timezone manager
        if time_index.start_dt:
            tz_manager = get_timezone_manager()
            now_aware = tz_manager.ensure_timezone_aware(now)
            start_aware = tz_manager.ensure_timezone_aware(time_index.start_dt)

            if start_aware > now_aware:
                # Add buffer before start time
                buffer_hours = getattr(preferences, 'replan_buffer_hours', 2)
                frozen_start = max(now_aware, start_aware - timedelta(hours=buffer_hours))
                constraints.frozen_periods.append((frozen_start, start_aware))

        return constraints

    def _analyze_disruption_potential(
        self,
        existing_blocks: List[ScheduleBlock],
        new_tasks: List[Task],
        busy_events: List[BusyEvent],
        constraints: ReplanConstraint
    ) -> Dict[str, float]:
        """Analyze disruption potential for each block."""
        disruption_scores = {}

        for block in existing_blocks:
            score = 0.0

            # Base disruption from moving any existing block
            score += 10.0

            # Higher disruption for blocks starting soon
            now = datetime.now()

            # Use timezone manager for safe comparison
            now_aware, block_start_aware = safe_datetime_comparison(now, block.start)
            time_to_start = (block_start_aware - now_aware).total_seconds() / 3600  # hours
            if time_to_start < 24:  # Less than 24 hours
                score += (24 - time_to_start) * 2.0

            # Higher disruption for long blocks (harder to reschedule)
            duration_hours = block.duration_minutes / 60
            if duration_hours > 2:
                score += (duration_hours - 2) * 5.0

            # Higher disruption if block is adjacent to busy events
            for event in busy_events:
                if abs((block.start - event.start).total_seconds()) < 3600:  # Within 1 hour
                    score += 15.0
                if abs((block.end - event.end).total_seconds()) < 3600:
                    score += 15.0

            # Lower disruption for flexible blocks
            if hasattr(block, 'metadata') and block.metadata.get('flexible', False):
                score *= 0.7

            disruption_scores[block.task_id] = score

        return disruption_scores

    def _determine_allowed_changes(
        self,
        existing_blocks: List[ScheduleBlock],
        disruption_analysis: Dict[str, float],
        constraints: ReplanConstraint
    ) -> Dict[str, List[ChangeType]]:
        """Determine what changes are allowed for each block."""
        allowed_changes = {}

        for block in existing_blocks:
            changes = []

            # Check if block is protected
            if (block.task_id in constraints.protected_task_ids or
                block.task_id in constraints.protected_block_ids):
                changes = [ChangeType.NONE]
            else:
                disruption_score = disruption_analysis.get(block.task_id, 0.0)

                # For very conservative constraints, protect more blocks
                if constraints.max_disruption_score <= 20.0:  # MINIMAL scope
                    # Only allow changes to blocks with very low disruption
                    if disruption_score <= 15.0:
                        changes.append(ChangeType.MOVE)
                    # Allow splitting only for very long blocks
                    if block.duration_minutes > 180:  # More than 3 hours
                        changes.append(ChangeType.SPLIT)
                else:
                    # Normal behavior for other scopes
                    # Allow moves for low-disruption blocks
                    if disruption_score < constraints.max_disruption_score:
                        changes.append(ChangeType.MOVE)
                        changes.append(ChangeType.RESCHEDULE)

                    # Allow splitting for long blocks
                    if block.duration_minutes > 90:  # More than 1.5 hours
                        changes.append(ChangeType.SPLIT)

                    # Allow merging if preserve_adjacency is False
                    if not constraints.preserve_adjacency:
                        changes.append(ChangeType.MERGE)

                    # Allow cancellation for very flexible blocks
                    if (hasattr(block, 'metadata') and
                        block.metadata.get('flexible', False) and
                        disruption_score < 30.0):
                        changes.append(ChangeType.CANCEL)

            if not changes:
                changes = [ChangeType.NONE]

            allowed_changes[block.task_id] = changes

        return allowed_changes

    def _find_move_candidates(
        self,
        existing_blocks: List[ScheduleBlock],
        constraints: ReplanConstraint,
        disruption_analysis: Dict[str, float]
    ) -> List[str]:
        """Find blocks that are good candidates for moving."""
        candidates = []

        # Sort blocks by disruption score (lowest first)
        sorted_blocks = sorted(
            existing_blocks,
            key=lambda b: disruption_analysis.get(b.task_id, 0.0)
        )

        max_candidates = constraints.max_blocks_to_move or len(existing_blocks)

        for block in sorted_blocks[:max_candidates]:
            if (block.task_id not in constraints.protected_task_ids and
                block.task_id not in constraints.protected_block_ids and
                disruption_analysis.get(block.task_id, 0.0) < constraints.max_disruption_score):
                candidates.append(block.task_id)

        return candidates

    def _find_merge_opportunities(
        self,
        existing_blocks: List[ScheduleBlock],
        constraints: ReplanConstraint
    ) -> List[Tuple[str, str]]:
        """Find pairs of blocks that could be merged."""
        opportunities = []

        if constraints.preserve_adjacency:
            return opportunities  # No merging if preserving adjacency

        # Look for blocks of same task that could be merged
        task_blocks = {}
        for block in existing_blocks:
            if block.task_id not in task_blocks:
                task_blocks[block.task_id] = []
            task_blocks[block.task_id].append(block)

        for task_id, blocks in task_blocks.items():
            if len(blocks) > 1 and task_id not in constraints.protected_task_ids:
                # Sort by start time
                blocks.sort(key=lambda b: b.start)

                # Look for adjacent or nearby blocks
                for i in range(len(blocks) - 1):
                    block1, block2 = blocks[i], blocks[i + 1]
                    gap_minutes = (block2.start - block1.end).total_seconds() / 60

                    if gap_minutes <= 30:  # Blocks within 30 minutes
                        opportunities.append((block1.task_id, block2.task_id))

        return opportunities

    def _calculate_disruption_score(self, disruption_analysis: Dict[str, float]) -> float:
        """Calculate overall disruption score."""
        if not disruption_analysis:
            return 0.0

        # Use weighted average with higher weight for high-disruption blocks
        total_weighted_score = 0.0
        total_weight = 0.0

        for score in disruption_analysis.values():
            weight = 1.0 + (score / 50.0)  # Higher scores get more weight
            total_weighted_score += score * weight
            total_weight += weight

        return min(100.0, total_weighted_score / total_weight if total_weight > 0 else 0.0)

    def _calculate_stability_ratio(
        self,
        existing_blocks: List[ScheduleBlock],
        allowed_changes: Dict[str, List[ChangeType]]
    ) -> float:
        """Calculate the fraction of blocks that will remain stable."""
        if not existing_blocks:
            return 1.0

        stable_count = 0
        for block in existing_blocks:
            changes = allowed_changes.get(block.task_id, [ChangeType.NONE])
            if changes == [ChangeType.NONE]:
                stable_count += 1

        return stable_count / len(existing_blocks)

    def _identify_protected_blocks(
        self,
        existing_blocks: List[ScheduleBlock],
        constraints: ReplanConstraint
    ) -> Set[str]:
        """Identify blocks that are protected from changes."""
        protected = set()

        # Add explicitly protected tasks and blocks
        protected.update(constraints.protected_task_ids)
        protected.update(constraints.protected_block_ids)

        # Add blocks in frozen time periods
        for block in existing_blocks:
            for frozen_start, frozen_end in constraints.frozen_periods:
                if (block.start >= frozen_start and block.start < frozen_end) or \
                   (block.end > frozen_start and block.end <= frozen_end):
                    protected.add(block.task_id)
                    break

        # Add blocks outside change time bounds
        if constraints.earliest_change_time:
            for block in existing_blocks:
                if block.start < constraints.earliest_change_time:
                    protected.add(block.task_id)

        if constraints.latest_change_time:
            for block in existing_blocks:
                if block.start > constraints.latest_change_time:
                    protected.add(block.task_id)

        return protected

    def _blocks_substantially_same(self, block1: ScheduleBlock, block2: ScheduleBlock) -> bool:
        """Check if two blocks are substantially the same (allowing small differences)."""
        # Allow up to 15 minutes difference in start time
        time_diff = abs((block1.start - block2.start).total_seconds()) / 60
        duration_diff = abs(block1.duration_minutes - block2.duration_minutes)

        return (time_diff <= 15 and
                duration_diff <= 15 and
                block1.task_id == block2.task_id)


# Global controller instance
_controller = None

def get_replanning_controller() -> ReplanningController:
    """Get global replanning controller instance."""
    global _controller
    if _controller is None:
        _controller = ReplanningController()
    return _controller

