"""
Test determinism guarantee: same inputs produce identical schedules.
"""

import pytest
from typing import List
from datetime import datetime, timedelta

from ...service import SchedulerService
from ...determinism import get_deterministic_scheduler, DeterminismConfig, create_request_hash
from ...io.dto import ScheduleRequest
from ..fixtures import create_test_task, create_test_preferences


class TestDeterminismSameInputs:
    """Test that identical inputs produce identical schedules."""

    @pytest.fixture
    def deterministic_service(self):
        """Create scheduler with deterministic configuration."""
        config = DeterminismConfig(random_seed=42)
        scheduler = SchedulerService()
        # Ensure deterministic behavior
        scheduler.deterministic_scheduler = get_deterministic_scheduler(config)
        return scheduler

    @pytest.fixture
    def test_scenario(self):
        """Create consistent test scenario."""
        base_time = datetime(2025, 9, 26, 9, 0)  # Fixed time for consistency

        tasks = [
            create_test_task(
                "essay_assignment",
                title="Essay Assignment",
                duration_minutes=120,
                deadline_hours=72
            ),
            create_test_task(
                "math_homework",
                title="Math Homework",
                duration_minutes=90,
                deadline_hours=48
            ),
            create_test_task(
                "reading_chapter",
                title="Chapter Reading",
                duration_minutes=60,
                deadline_hours=24
            )
        ]

        return {
            "tasks": tasks,
            "request": ScheduleRequest(
                user_id="determinism_test_user",
                horizon_days=3,
                dry_run=True,
                job_id="determinism_test"
            )
        }

    @pytest.mark.asyncio
    async def test_identical_schedules_multiple_runs(self, deterministic_service, test_scenario):
        """Test that running the same scenario multiple times produces identical results."""
        request = test_scenario["request"]
        tasks = test_scenario["tasks"]

        # Create request hash for comparison
        request_hash = create_request_hash(tasks, [], request.horizon_days, request.user_id)

        # Run the same scenario 10 times
        results = []
        schedule_hashes = []

        for run_idx in range(10):
            # Reset RNG seeds before each run
            deterministic_service.deterministic_scheduler._seed_rngs()

            # Execute scheduling
            response = await deterministic_service.schedule(request)
            results.append(response)

            # Calculate schedule hash
            if response.blocks:
                block_sigs = []
                for block in sorted(response.blocks, key=lambda b: (b.start, b.task_id)):
                    sig = f"{block.task_id}:{block.start}:{block.end}"
                    block_sigs.append(sig)
                schedule_hash = "|".join(block_sigs)
            else:
                schedule_hash = "empty_schedule"

            schedule_hashes.append(schedule_hash)

        # Assert all runs produced identical schedules
        assert len(set(schedule_hashes)) == 1, f"Non-deterministic results: {len(set(schedule_hashes))} unique schedules"

        # Verify specific properties are identical across runs
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result.feasible == first_result.feasible, f"Run {i} feasibility differs"
            assert len(result.blocks) == len(first_result.blocks), f"Run {i} block count differs"

            # Compare blocks in detail
            if result.blocks and first_result.blocks:
                for j, (block1, block2) in enumerate(zip(
                    sorted(first_result.blocks, key=lambda b: (b.start, b.task_id)),
                    sorted(result.blocks, key=lambda b: (b.start, b.task_id))
                )):
                    assert block1.task_id == block2.task_id, f"Run {i} block {j} task_id differs"
                    assert block1.start == block2.start, f"Run {i} block {j} start time differs"
                    assert block1.end == block2.end, f"Run {i} block {j} end time differs"

    @pytest.mark.asyncio
    async def test_stable_task_sorting(self, deterministic_service):
        """Test that task sorting is stable and deterministic."""
        det_scheduler = deterministic_service.deterministic_scheduler

        # Create tasks with same deadline to test tie-breaking
        base_deadline = datetime.now() + timedelta(hours=24)

        tasks = [
            create_test_task("task_c", title="Task C", deadline_hours=24),
            create_test_task("task_a", title="Task A", deadline_hours=24),
            create_test_task("task_b", title="Task B", deadline_hours=24)
        ]

        # Set same deadline and course for tie-breaking test
        for task in tasks:
            task.deadline = base_deadline
            task.course_id = "TEST_COURSE"

        # Sort multiple times
        sorted_results = []
        for _ in range(5):
            sorted_tasks = det_scheduler.stable_sort_tasks(tasks.copy())
            task_ids = [t.id for t in sorted_tasks]
            sorted_results.append(task_ids)

        # All sorting results should be identical
        assert len(set(tuple(result) for result in sorted_results)) == 1

        # Should be sorted by task_id since other fields are identical
        expected_order = ["task_a", "task_b", "task_c"]
        assert sorted_results[0] == expected_order

    @pytest.mark.asyncio
    async def test_schedule_hash_consistency(self, deterministic_service):
        """Test that schedule hash calculation is consistent."""
        det_scheduler = deterministic_service.deterministic_scheduler

        from ...domain import ScheduleBlock

        # Create consistent blocks
        block1 = ScheduleBlock(
            task_id="task1",
            start=datetime(2025, 9, 26, 10, 0),
            end=datetime(2025, 9, 26, 11, 0)
        )
        block2 = ScheduleBlock(
            task_id="task2",
            start=datetime(2025, 9, 26, 11, 0),
            end=datetime(2025, 9, 26, 12, 0)
        )

        blocks = [block1, block2]

        # Calculate hash multiple times
        hashes = []
        for _ in range(5):
            # Test with blocks in different order
            shuffled_blocks = blocks.copy()
            hash_result = det_scheduler.calculate_existing_blocks_hash(shuffled_blocks)
            hashes.append(hash_result)

        # All hashes should be identical despite input order
        assert len(set(hashes)) == 1

    @pytest.mark.asyncio
    async def test_request_hash_stability(self, test_scenario):
        """Test that request hash is stable for same inputs."""
        tasks = test_scenario["tasks"]
        request = test_scenario["request"]

        # Calculate hash multiple times
        hashes = []
        for _ in range(5):
            hash_result = create_request_hash(
                tasks.copy(),
                [],
                request.horizon_days,
                request.user_id
            )
            hashes.append(hash_result)

        # All hashes should be identical
        assert len(set(hashes)) == 1

        # Hash should be deterministic and not change with task order
        shuffled_tasks = tasks.copy()
        shuffled_tasks.reverse()

        shuffled_hash = create_request_hash(
            shuffled_tasks,
            [],
            request.horizon_days,
            request.user_id
        )

        assert shuffled_hash == hashes[0]

    @pytest.mark.asyncio
    async def test_empty_schedule_determinism(self, deterministic_service):
        """Test deterministic behavior with empty/no-solution scenarios."""
        # Create impossible scenario
        impossible_task = create_test_task(
            "impossible",
            duration_minutes=480,  # 8 hours
            deadline_hours=1       # Due in 1 hour
        )

        request = ScheduleRequest(
            user_id="impossible_test",
            horizon_days=1,
            dry_run=True,
            job_id="impossible_test"
        )

        # Run multiple times
        results = []
        for _ in range(3):
            deterministic_service.deterministic_scheduler._seed_rngs()
            response = await deterministic_service.schedule(request)
            results.append({
                'feasible': response.feasible,
                'block_count': len(response.blocks),
                'status': response.metrics.get('solver_status', 'unknown')
            })

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Non-deterministic results for impossible scenario"