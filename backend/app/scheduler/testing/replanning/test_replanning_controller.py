"""
Test suite for replanning controller and scope management.
"""

import pytest
from datetime import datetime, timedelta
from typing import List
import pytz

from app.scheduler.replanning import (
    ReplanningController, ReplanScope, ReplanConstraint, ChangeType
)
from app.scheduler.domain import Task, ScheduleBlock, Preferences, BusyEvent
from app.scheduler.optimization.time_index import TimeIndex
from app.scheduler.testing.fixtures import create_test_task, create_test_preferences


class TestReplanningController:
    """Test replanning controller functionality."""

    @pytest.fixture
    def controller(self):
        """Create replanning controller."""
        return ReplanningController()

    @pytest.fixture
    def utc(self):
        """UTC timezone."""
        return pytz.UTC

    @pytest.fixture
    def base_time(self, utc):
        """Base time for testing."""
        return datetime(2025, 9, 26, 9, 0, tzinfo=utc)

    @pytest.fixture
    def existing_blocks(self, base_time):
        """Create sample existing schedule blocks."""
        return [
            ScheduleBlock(
                task_id="task1",
                start=base_time,
                end=base_time + timedelta(hours=1),
                utility_score=1.0,
                estimated_completion_probability=0.8
            ),
            ScheduleBlock(
                task_id="task2",
                start=base_time + timedelta(hours=2),
                end=base_time + timedelta(hours=3),
                utility_score=1.0,
                estimated_completion_probability=0.9
            ),
            ScheduleBlock(
                task_id="task3",
                start=base_time + timedelta(hours=4),
                end=base_time + timedelta(hours=6),  # 2-hour block
                utility_score=1.0,
                estimated_completion_probability=0.7
            )
        ]

    @pytest.fixture
    def time_index(self, base_time):
        """Create test time index."""
        return TimeIndex(
            timezone="UTC",
            start_dt=base_time,
            end_dt=base_time + timedelta(days=2),
            granularity_minutes=30
        )

    def test_minimal_scope_constraints(self, controller):
        """Test minimal scope allows very few changes."""
        constraints = controller._get_scope_constraints(ReplanScope.MINIMAL)

        assert constraints.max_blocks_to_move == 2
        assert constraints.max_move_distance_hours == 1.0
        assert constraints.min_stability_ratio == 0.95
        assert constraints.max_disruption_score == 20.0
        assert constraints.preserve_adjacency is True

    def test_complete_scope_constraints(self, controller):
        """Test complete scope allows all changes."""
        constraints = controller._get_scope_constraints(ReplanScope.COMPLETE)

        assert constraints.max_blocks_to_move is None
        assert constraints.max_move_distance_hours is None
        assert constraints.min_stability_ratio == 0.0
        assert constraints.max_disruption_score == 100.0
        assert constraints.preserve_adjacency is False

    def test_constraint_merging(self, controller):
        """Test merging of custom constraints with base constraints."""
        base = controller._get_scope_constraints(ReplanScope.MODERATE)
        custom = ReplanConstraint(
            protected_task_ids={"task1", "task2"},
            max_blocks_to_move=5,
            min_stability_ratio=0.9
        )

        merged = controller._merge_constraints(base, custom)

        assert "task1" in merged.protected_task_ids
        assert "task2" in merged.protected_task_ids
        assert merged.max_blocks_to_move == 5
        assert merged.min_stability_ratio == 0.9  # Higher of the two
        assert merged.max_move_distance_hours == base.max_move_distance_hours

    def test_analyze_replanning_scope_minimal(self, controller, existing_blocks, base_time, time_index):
        """Test minimal scope analysis."""
        tasks = [create_test_task("new_task", duration_minutes=60)]
        preferences = create_test_preferences()

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.MINIMAL,
            time_index=time_index
        )

        # Minimal scope should be very conservative
        assert len(result.move_candidates) <= 2  # At most 2 blocks can move
        assert result.stability_ratio >= 0.6     # At least 60% stable
        assert result.disruption_score <= 50.0   # Reasonable disruption score

        # Most blocks should have NONE or very limited changes
        none_changes = sum(1 for changes in result.allowed_changes.values()
                          if changes == [ChangeType.NONE])
        assert none_changes >= 1  # At least one block should be unchanged

    def test_analyze_replanning_scope_complete(self, controller, existing_blocks, base_time, time_index):
        """Test complete scope analysis."""
        tasks = [create_test_task("new_task", duration_minutes=60)]
        preferences = create_test_preferences()

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.COMPLETE,
            time_index=time_index
        )

        # Complete scope should allow most changes
        assert len(result.move_candidates) == len(existing_blocks)
        assert result.stability_ratio <= 0.5

        # All blocks should allow various changes
        for block in existing_blocks:
            changes = result.allowed_changes.get(block.task_id, [])
            assert ChangeType.MOVE in changes
            assert ChangeType.RESCHEDULE in changes

    def test_protected_task_constraints(self, controller, existing_blocks, base_time, time_index):
        """Test that protected tasks are properly handled."""
        tasks = [create_test_task("new_task", duration_minutes=60)]
        preferences = create_test_preferences()

        custom_constraints = ReplanConstraint(
            protected_task_ids={"task1", "task2"}
        )

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.MODERATE,
            custom_constraints=custom_constraints,
            time_index=time_index
        )

        # Protected tasks should not be in move candidates
        assert "task1" not in result.move_candidates
        assert "task2" not in result.move_candidates
        assert "task1" in result.protected_blocks
        assert "task2" in result.protected_blocks

        # Protected tasks should only allow NONE changes
        assert result.allowed_changes["task1"] == [ChangeType.NONE]
        assert result.allowed_changes["task2"] == [ChangeType.NONE]

    def test_disruption_analysis(self, controller, existing_blocks, base_time, time_index):
        """Test disruption score calculation."""
        tasks = []
        preferences = create_test_preferences()

        # Add a busy event near one of the blocks
        busy_events = [
            BusyEvent(
                id="meeting",
                source="google",
                start=base_time + timedelta(hours=1, minutes=30),
                end=base_time + timedelta(hours=2, minutes=30),
                title="Important Meeting",
                hard=True
            )
        ]

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=busy_events,
            preferences=preferences,
            scope=ReplanScope.MODERATE,
            time_index=time_index
        )

        # Block near the busy event should have higher disruption
        # This would affect task2 which is at base_time + 2 hours
        assert result.disruption_score > 0

        # Disruption scores should be reasonable
        assert 0 <= result.disruption_score <= 100

    def test_filter_existing_blocks(self, controller, existing_blocks, base_time, time_index):
        """Test filtering blocks into protected and changeable sets."""
        tasks = []
        preferences = create_test_preferences()

        custom_constraints = ReplanConstraint(
            protected_task_ids={"task1"}
        )

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.MODERATE,
            custom_constraints=custom_constraints,
            time_index=time_index
        )

        protected, changeable = controller.filter_existing_blocks(existing_blocks, result)

        # task1 should be protected
        protected_task_ids = {b.task_id for b in protected}
        changeable_task_ids = {b.task_id for b in changeable}

        assert "task1" in protected_task_ids
        assert "task1" not in changeable_task_ids
        assert len(protected) + len(changeable) == len(existing_blocks)

    def test_merge_opportunities(self, controller, base_time, time_index):
        """Test finding merge opportunities."""
        # Create blocks from the same task that could be merged
        existing_blocks = [
            ScheduleBlock(
                task_id="task1",
                start=base_time,
                end=base_time + timedelta(hours=1),
                utility_score=1.0,
                estimated_completion_probability=0.8
            ),
            ScheduleBlock(
                task_id="task1",  # Same task
                start=base_time + timedelta(hours=1, minutes=15),  # Small gap
                end=base_time + timedelta(hours=2),
                utility_score=1.0,
                estimated_completion_probability=0.8
            ),
            ScheduleBlock(
                task_id="task2",
                start=base_time + timedelta(hours=3),
                end=base_time + timedelta(hours=4),
                utility_score=1.0,
                estimated_completion_probability=0.9
            )
        ]

        tasks = []
        preferences = create_test_preferences()

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.AGGRESSIVE,  # Allows merging
            time_index=time_index
        )

        # Should find merge opportunity for task1 blocks
        assert len(result.merge_opportunities) > 0
        merge_found = any(
            (pair[0] == "task1" and pair[1] == "task1") or
            (pair[0] == "task1" or pair[1] == "task1")
            for pair in result.merge_opportunities
        )
        assert merge_found

    def test_validate_replanning_result_stability(self, controller, existing_blocks, base_time):
        """Test validation of replanning results for stability."""
        # Create a mock replan result
        from app.scheduler.replanning import ReplanResult

        replan_result = ReplanResult(
            allowed_changes={"task1": [ChangeType.NONE], "task2": [ChangeType.MOVE], "task3": [ChangeType.MOVE]},
            protected_blocks={"task1"},
            move_candidates=["task2", "task3"],
            merge_opportunities=[],
            disruption_score=30.0,
            stability_ratio=0.33  # Only 1/3 blocks stable
        )

        # Create new blocks where task1 is unchanged but others are moved significantly
        new_blocks = [
            existing_blocks[0],  # task1 unchanged
            ScheduleBlock(
                task_id="task2",
                start=base_time + timedelta(hours=10),  # Moved significantly
                end=base_time + timedelta(hours=11),
                utility_score=1.0,
                estimated_completion_probability=0.9
            ),
            ScheduleBlock(
                task_id="task3",
                start=base_time + timedelta(hours=12),  # Moved significantly
                end=base_time + timedelta(hours=14),
                utility_score=1.0,
                estimated_completion_probability=0.7
            )
        ]

        is_valid, violations = controller.validate_replanning_result(
            existing_blocks, new_blocks, replan_result
        )

        # Should be valid since we respected the constraints
        assert is_valid
        assert len(violations) == 0

    def test_validate_replanning_result_violations(self, controller, existing_blocks, base_time):
        """Test validation catches constraint violations."""
        from app.scheduler.replanning import ReplanResult

        replan_result = ReplanResult(
            allowed_changes={"task1": [ChangeType.NONE], "task2": [ChangeType.MOVE], "task3": [ChangeType.MOVE]},
            protected_blocks={"task1"},  # task1 is protected
            move_candidates=["task2", "task3"],
            merge_opportunities=[],
            disruption_score=30.0,
            stability_ratio=0.67  # 2/3 blocks should be stable
        )

        # Create new blocks that violate constraints
        new_blocks = [
            ScheduleBlock(
                task_id="task1",
                start=base_time + timedelta(hours=5),  # Protected block moved!
                end=base_time + timedelta(hours=6),
                utility_score=1.0,
                estimated_completion_probability=0.8
            ),
            existing_blocks[1],  # task2 unchanged
            existing_blocks[2]   # task3 unchanged
        ]

        is_valid, violations = controller.validate_replanning_result(
            existing_blocks, new_blocks, replan_result
        )

        # Should be invalid due to protected block being moved
        assert not is_valid
        assert len(violations) > 0
        assert any("protected" in v.lower() for v in violations)

    def test_blocks_substantially_same(self, controller, base_time):
        """Test block similarity detection."""
        block1 = ScheduleBlock(
            task_id="task1",
            start=base_time,
            end=base_time + timedelta(hours=1),
            utility_score=1.0,
            estimated_completion_probability=0.8
        )

        # Same block
        block2 = ScheduleBlock(
            task_id="task1",
            start=base_time,
            end=base_time + timedelta(hours=1),
            utility_score=1.0,
            estimated_completion_probability=0.8
        )

        # Slightly different timing (within tolerance)
        block3 = ScheduleBlock(
            task_id="task1",
            start=base_time + timedelta(minutes=10),  # 10 min difference
            end=base_time + timedelta(hours=1, minutes=10),
            utility_score=1.0,
            estimated_completion_probability=0.8
        )

        # Very different timing (outside tolerance)
        block4 = ScheduleBlock(
            task_id="task1",
            start=base_time + timedelta(hours=2),  # 2 hour difference
            end=base_time + timedelta(hours=3),
            utility_score=1.0,
            estimated_completion_probability=0.8
        )

        assert controller._blocks_substantially_same(block1, block2)
        assert controller._blocks_substantially_same(block1, block3)
        assert not controller._blocks_substantially_same(block1, block4)

    def test_frozen_periods_constraint(self, controller, existing_blocks, base_time, time_index):
        """Test that frozen periods are properly respected."""
        tasks = []
        preferences = create_test_preferences()

        # Add frozen period that overlaps with task2
        frozen_start = base_time + timedelta(hours=1, minutes=30)
        frozen_end = base_time + timedelta(hours=2, minutes=30)

        custom_constraints = ReplanConstraint(
            frozen_periods=[(frozen_start, frozen_end)]
        )

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.MODERATE,
            custom_constraints=custom_constraints,
            time_index=time_index
        )

        # task2 (which overlaps with frozen period) should be protected
        assert "task2" in result.protected_blocks
        assert result.allowed_changes["task2"] == [ChangeType.NONE]

    def test_max_blocks_to_move_constraint(self, controller, existing_blocks, base_time, time_index):
        """Test max blocks to move constraint."""
        tasks = []
        preferences = create_test_preferences()

        custom_constraints = ReplanConstraint(
            max_blocks_to_move=1  # Only allow 1 block to move
        )

        result = controller.analyze_replanning_scope(
            existing_blocks=existing_blocks,
            new_tasks=tasks,
            busy_events=[],
            preferences=preferences,
            scope=ReplanScope.MODERATE,
            custom_constraints=custom_constraints,
            time_index=time_index
        )

        # Should have at most 1 move candidate
        assert len(result.move_candidates) <= 1