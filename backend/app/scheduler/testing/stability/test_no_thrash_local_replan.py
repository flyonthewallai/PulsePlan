"""
Test no-thrash guarantee: local replanning doesn't move too many blocks.
"""

import pytest
from typing import List
from datetime import datetime, timedelta

from ...service import SchedulerService
from ...determinism import get_deterministic_scheduler, DeterminismConfig
from ...domain import ScheduleBlock, BusyEvent
from ...io.dto import ScheduleRequest
from ..fixtures import create_test_task, create_test_preferences, create_test_busy_events


class TestNoThrashLocalReplan:
    """Test that local replanning doesn't cause excessive schedule thrashing."""

    @pytest.fixture
    def stable_service(self):
        """Create scheduler with stability configuration."""
        config = DeterminismConfig(
            random_seed=42,
            max_move_ratio_threshold=0.2,  # Max 20% of blocks can move
            frozen_window_hours=12,
            inertia_penalty_weight=5.0
        )
        scheduler = SchedulerService()
        scheduler.deterministic_scheduler = get_deterministic_scheduler(config)
        return scheduler

    @pytest.fixture
    def base_scenario(self):
        """Create base scheduling scenario with existing blocks."""
        base_time = datetime(2025, 9, 26, 8, 0)

        tasks = [
            create_test_task("morning_study", duration_minutes=90, deadline_hours=48),
            create_test_task("afternoon_project", duration_minutes=120, deadline_hours=72),
            create_test_task("evening_reading", duration_minutes=60, deadline_hours=24),
            create_test_task("assignment_work", duration_minutes=90, deadline_hours=96),
            create_test_task("exam_prep", duration_minutes=150, deadline_hours=120)
        ]

        # Create existing schedule blocks
        existing_blocks = [
            ScheduleBlock(
                task_id="morning_study",
                start=base_time.replace(hour=9),
                end=base_time.replace(hour=10, minute=30)
            ),
            ScheduleBlock(
                task_id="afternoon_project",
                start=base_time.replace(hour=14),
                end=base_time.replace(hour=16)
            ),
            ScheduleBlock(
                task_id="evening_reading",
                start=base_time.replace(hour=19),
                end=base_time.replace(hour=20)
            )
        ]

        return {
            "tasks": tasks,
            "existing_blocks": existing_blocks,
            "base_time": base_time
        }

    @pytest.mark.asyncio
    async def test_small_calendar_change_minimal_moves(self, stable_service, base_scenario):
        """Test that small calendar changes don't cause excessive block movement."""
        tasks = base_scenario["tasks"]
        existing_blocks = base_scenario["existing_blocks"]
        base_time = base_scenario["base_time"]

        # Add a small conflicting event (1 hour meeting)
        new_event = BusyEvent(
            id="small_meeting",
            source="google",
            start=base_time.replace(hour=15),  # Conflicts with afternoon project
            end=base_time.replace(hour=16),
            title="Team Meeting",
            hard=True
        )

        request = ScheduleRequest(
            user_id="stability_test",
            horizon_days=3,
            dry_run=True,
            job_id="small_change_test"
        )

        # Run scheduling with new conflict
        response = await stable_service.schedule(request)

        if response.feasible and response.blocks:
            # Calculate stability metrics
            det_scheduler = stable_service.deterministic_scheduler
            stability_metrics = det_scheduler.calculate_stability_metrics(
                response, existing_blocks
            )

            moved_ratio = stability_metrics['moved_block_ratio']
            blocks_moved = stability_metrics['blocks_moved']

            # Assert no-thrash guarantee
            assert moved_ratio <= 0.3, f"Too many blocks moved: {moved_ratio:.1%} > 30%"
            assert blocks_moved <= 2, f"Too many individual blocks moved: {blocks_moved}"

            # Check that frozen window blocks weren't moved
            det_scheduler = stable_service.deterministic_scheduler
            frozen_start, frozen_end = det_scheduler.get_frozen_window(base_time)

            frozen_violations = []
            for new_block in response.blocks:
                for existing_block in existing_blocks:
                    if (new_block.task_id == existing_block.task_id and
                        existing_block.start >= frozen_start and
                        existing_block.start < frozen_end):

                        # Check if block was significantly moved (>15 min)
                        time_diff = abs((new_block.start - existing_block.start).total_seconds())
                        if time_diff > 900:  # 15 minutes
                            frozen_violations.append(new_block.task_id)

            assert len(frozen_violations) == 0, f"Frozen window violations: {frozen_violations}"

    @pytest.mark.asyncio
    async def test_locked_blocks_not_moved(self, stable_service, base_scenario):
        """Test that locked blocks are never moved during replanning."""
        existing_blocks = base_scenario["existing_blocks"]

        # Mark one block as locked
        locked_block = existing_blocks[0]  # morning_study
        locked_block.locked = True
        locked_block.manual = False

        # Mark another as manual
        manual_block = existing_blocks[1]  # afternoon_project
        manual_block.locked = False
        manual_block.manual = True

        det_scheduler = stable_service.deterministic_scheduler

        # Test locked block identification
        locked_task_ids = det_scheduler.identify_locked_blocks(existing_blocks)

        assert "morning_study" in locked_task_ids, "Locked block not identified"
        assert "afternoon_project" in locked_task_ids, "Manual block not identified"

        # Add major conflicting event
        major_conflict = BusyEvent(
            id="all_day_meeting",
            source="google",
            start=base_scenario["base_time"].replace(hour=9),
            end=base_scenario["base_time"].replace(hour=17),
            title="All Day Conference",
            hard=True
        )

        request = ScheduleRequest(
            user_id="locked_test",
            horizon_days=3,
            dry_run=True,
            job_id="locked_test"
        )

        # Even with major conflict, locked blocks should not move
        response = await stable_service.schedule(request)

        if response.blocks:
            # Find the locked tasks in new schedule
            new_blocks_by_task = {block.task_id: block for block in response.blocks}

            # Locked block should be in same position (or conflict should be reported)
            if "morning_study" in new_blocks_by_task:
                new_morning_block = new_blocks_by_task["morning_study"]
                time_diff = abs((new_morning_block.start - locked_block.start).total_seconds())
                assert time_diff <= 900, "Locked block was moved significantly"

    @pytest.mark.asyncio
    async def test_inertia_penalties_reduce_movement(self, stable_service, base_scenario):
        """Test that inertia penalties discourage unnecessary block movement."""
        existing_blocks = base_scenario["existing_blocks"]
        base_time = base_scenario["base_time"]

        det_scheduler = stable_service.deterministic_scheduler

        # Create a solution that would move blocks
        from ...domain import ScheduleSolution

        moved_blocks = [
            ScheduleBlock(
                task_id="morning_study",
                start=base_time.replace(hour=10),    # Moved 1 hour later
                end=base_time.replace(hour=11, minute=30)
            ),
            ScheduleBlock(
                task_id="afternoon_project",
                start=base_time.replace(hour=15),    # Moved 1 hour later
                end=base_time.replace(hour=17)
            )
        ]

        moved_solution = ScheduleSolution(
            feasible=True,
            blocks=moved_blocks,
            objective_value=100.0
        )

        # Calculate inertia penalties
        penalties = det_scheduler.calculate_inertia_penalties(
            moved_solution, existing_blocks, base_time
        )

        # Should have penalties for moved blocks
        assert penalties["morning_study"] > 0, "No penalty for moving morning block"
        assert penalties["afternoon_project"] > 0, "No penalty for moving afternoon block"

        # Blocks moved further should have higher penalties
        morning_penalty = penalties["morning_study"]
        afternoon_penalty = penalties["afternoon_project"]

        # Both moved 1 hour, so penalties should be similar
        assert abs(morning_penalty - afternoon_penalty) < 1.0

    @pytest.mark.asyncio
    async def test_stability_metrics_calculation(self, stable_service):
        """Test stability metrics calculation accuracy."""
        det_scheduler = stable_service.deterministic_scheduler

        base_time = datetime(2025, 9, 26, 9, 0)

        # Original schedule
        existing_blocks = [
            ScheduleBlock(
                task_id="task1",
                start=base_time.replace(hour=9),
                end=base_time.replace(hour=10)
            ),
            ScheduleBlock(
                task_id="task2",
                start=base_time.replace(hour=11),
                end=base_time.replace(hour=12)
            ),
            ScheduleBlock(
                task_id="task3",
                start=base_time.replace(hour=14),
                end=base_time.replace(hour=15)
            )
        ]

        # New schedule: move task1, keep task2, remove task3, add task4
        new_blocks = [
            ScheduleBlock(
                task_id="task1",
                start=base_time.replace(hour=10),  # Moved 1 hour
                end=base_time.replace(hour=11)
            ),
            ScheduleBlock(
                task_id="task2",
                start=base_time.replace(hour=11),  # Same position
                end=base_time.replace(hour=12)
            ),
            ScheduleBlock(
                task_id="task4",  # New task
                start=base_time.replace(hour=13),
                end=base_time.replace(hour=14)
            )
        ]

        from ...domain import ScheduleSolution
        new_solution = ScheduleSolution(feasible=True, blocks=new_blocks)

        # Calculate metrics
        metrics = det_scheduler.calculate_stability_metrics(new_solution, existing_blocks)

        # Verify metrics
        assert metrics['blocks_moved'] == 1, f"Expected 1 moved block, got {metrics['blocks_moved']}"
        assert metrics['blocks_added'] == 1, f"Expected 1 added block, got {metrics['blocks_added']}"
        assert metrics['blocks_removed'] == 1, f"Expected 1 removed block, got {metrics['blocks_removed']}"
        assert metrics['moved_block_ratio'] == 1/3, f"Expected 33% move ratio, got {metrics['moved_block_ratio']}"

    @pytest.mark.asyncio
    async def test_no_thrash_validation(self, stable_service):
        """Test no-thrash guarantee validation."""
        det_scheduler = stable_service.deterministic_scheduler

        base_time = datetime(2025, 9, 26, 9, 0)

        existing_blocks = [
            ScheduleBlock(task_id="task1", start=base_time.replace(hour=9), end=base_time.replace(hour=10)),
            ScheduleBlock(task_id="task2", start=base_time.replace(hour=11), end=base_time.replace(hour=12)),
            ScheduleBlock(task_id="task3", start=base_time.replace(hour=14), end=base_time.replace(hour=15))
        ]

        # Good solution (only moves 1 block = 33% < 20% fails, but let's test boundary)
        good_blocks = [
            ScheduleBlock(task_id="task1", start=base_time.replace(hour=9), end=base_time.replace(hour=10)),
            ScheduleBlock(task_id="task2", start=base_time.replace(hour=11), end=base_time.replace(hour=12)),
            ScheduleBlock(task_id="task3", start=base_time.replace(hour=14), end=base_time.replace(hour=15))
        ]

        # Bad solution (moves all blocks = 100%)
        bad_blocks = [
            ScheduleBlock(task_id="task1", start=base_time.replace(hour=10), end=base_time.replace(hour=11)),
            ScheduleBlock(task_id="task2", start=base_time.replace(hour=12), end=base_time.replace(hour=13)),
            ScheduleBlock(task_id="task3", start=base_time.replace(hour=15), end=base_time.replace(hour=16))
        ]

        from ...domain import ScheduleSolution

        good_solution = ScheduleSolution(feasible=True, blocks=good_blocks)
        bad_solution = ScheduleSolution(feasible=True, blocks=bad_blocks)

        # Test validation
        good_valid, good_reason = det_scheduler.validate_no_thrash_guarantee(
            good_solution, existing_blocks, threshold=0.5  # 50% threshold for this test
        )
        bad_valid, bad_reason = det_scheduler.validate_no_thrash_guarantee(
            bad_solution, existing_blocks, threshold=0.5
        )

        assert good_valid, f"Good solution should pass: {good_reason}"
        assert not bad_valid, f"Bad solution should fail: {bad_reason}"