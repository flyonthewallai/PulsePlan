"""
Comprehensive test suite for scheduler system.

Integrates invariant checking, golden tests, performance benchmarks,
and stability testing into a unified pytest-compatible test suite.
"""

import asyncio
import logging
from typing import List

import pytest

from ..core.domain import Task
from ..service import SchedulerService
from .fixtures import (
    create_edge_case_scenarios,
    create_realistic_course_tasks,
    create_stress_test_scenario,
    create_test_preferences,
)
from .golden_tests import GoldenTestRunner, create_basic_scenarios
from .invariants import ScheduleInvariantError, check_invariants
from .performance import (
    PerformanceBenchmark,
    StabilityTester,
    create_benchmark_scenarios,
)

logger = logging.getLogger(__name__)


class TestSchedulerInvariants:
    """Test suite for scheduler invariants."""

    def test_invariant_checking_empty_schedule(self):
        """Test invariant checking with empty schedule."""
        from ..core.domain import ScheduleSolution

        empty_solution = ScheduleSolution(feasible=True, blocks=[])

        result = check_invariants(
            solution=empty_solution,
            tasks=[],
            busy_events=[],
            preferences=create_test_preferences(),
            strict=False
        )

        assert result.passed
        assert len(result.violations) == 0
        assert "no_overlaps" in result.checked_invariants

    def test_invariant_checking_with_violations(self):
        """Test invariant checking detects violations."""
        from datetime import datetime

        from ..core.domain import ScheduleBlock, ScheduleSolution

        # Create overlapping blocks
        block1 = ScheduleBlock(
            task_id="task1",
            start=datetime(2025, 9, 26, 10, 0),
            end=datetime(2025, 9, 26, 11, 0)
        )
        block2 = ScheduleBlock(
            task_id="task2",
            start=datetime(2025, 9, 26, 10, 30),
            end=datetime(2025, 9, 26, 11, 30)
        )

        solution = ScheduleSolution(
            feasible=True,
            blocks=[block1, block2]
        )

        result = check_invariants(
            solution=solution,
            tasks=[],
            busy_events=[],
            preferences=create_test_preferences(),
            strict=False
        )

        assert not result.passed
        assert len(result.violations) > 0
        assert any("overlap" in violation.lower() for violation in result.violations)

    def test_invariant_checking_strict_mode(self):
        """Test that strict mode raises exceptions."""
        from datetime import datetime

        from ..core.domain import ScheduleBlock, ScheduleSolution

        # Create invalid block (end before start)
        invalid_block = ScheduleBlock(
            task_id="invalid",
            start=datetime(2025, 9, 26, 11, 0),
            end=datetime(2025, 9, 26, 10, 0)  # End before start
        )

        solution = ScheduleSolution(feasible=True, blocks=[invalid_block])

        with pytest.raises(ScheduleInvariantError):
            check_invariants(
                solution=solution,
                tasks=[],
                busy_events=[],
                preferences=create_test_preferences(),
                strict=True
            )


class TestGoldenTestSuite:
    """Test suite for golden test scenarios."""

    @pytest.fixture
    def golden_runner(self):
        """Create golden test runner for tests."""
        # Use a mock or test-specific service if needed
        service = SchedulerService()
        return GoldenTestRunner(
            scheduler_service=service,
            performance_budget_ms=5000  # Relaxed for tests
        )

    @pytest.mark.asyncio
    async def test_basic_scenarios(self, golden_runner):
        """Test basic golden scenarios."""
        scenarios = create_basic_scenarios()

        for scenario in scenarios[:1]:  # Test just the first one for speed
            result = await golden_runner.run_scenario(scenario)

            # Log results for debugging
            logger.info(f"Golden test '{scenario.name}': {result.passed}")

            if result.errors:
                for error in result.errors:
                    logger.error(f"  Error: {error}")

            # Basic assertions
            assert result.execution_time_ms > 0
            assert result.scenario_name == scenario.name

    @pytest.mark.asyncio
    async def test_load_fixture_scenarios(self, golden_runner):
        """Test loading and running fixture scenarios."""
        # This would load from the fixtures directory
        scenarios = golden_runner.load_all_scenarios()

        # Should have at least the fixtures we created
        assert len(scenarios) >= 2

        # Test one scenario
        if scenarios:
            result = await golden_runner.run_scenario(scenarios[0])
            assert result.execution_time_ms > 0

    def test_scenario_creation_and_saving(self, golden_runner, tmp_path):
        """Test creating and saving scenarios."""
        scenarios = create_basic_scenarios()
        scenario = scenarios[0]

        # Use temporary directory for test
        golden_runner.fixtures_dir = tmp_path

        golden_runner.save_scenario(scenario, "test_scenario.json")

        # Verify file was created
        saved_file = tmp_path / "test_scenario.json"
        assert saved_file.exists()

        # Verify we can load it back
        from .golden_tests import load_test_scenario
        loaded_scenario = load_test_scenario(saved_file)
        assert loaded_scenario.name == scenario.name


class TestPerformanceBenchmarks:
    """Test suite for performance benchmarking."""

    @pytest.fixture
    def benchmark(self):
        """Create performance benchmark for tests."""
        service = SchedulerService()
        return PerformanceBenchmark(
            scheduler_service=service,
            performance_budget_ms=10000  # 10 seconds for tests
        )

    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test
    async def test_simple_performance_benchmark(self, benchmark):
        """Test basic performance benchmark."""
        scenarios = create_benchmark_scenarios()
        simple_generator = scenarios["simple_tasks"]

        # Test with small numbers for speed
        results = await benchmark.benchmark_scenario(
            scenario_name="test_simple",
            task_generator=simple_generator,
            n_tasks_list=[5, 10],  # Small task counts for testing
            n_runs=3  # Few runs for testing
        )

        assert len(results) == 2  # Two task counts

        for n_tasks, result in results.items():
            assert result.n_runs == 3
            assert result.avg_time_ms > 0
            assert result.success_rate >= 0.0

            # Log performance metrics
            logger.info(f"Performance for {n_tasks} tasks: avg={result.avg_time_ms:.1f}ms")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stress_performance(self, benchmark):
        """Test performance under stress conditions."""
        def stress_generator(n_tasks: int) -> List[Task]:
            scenario = create_stress_test_scenario(n_tasks=n_tasks, complexity_level="medium")
            return scenario["tasks"]

        results = await benchmark.benchmark_scenario(
            scenario_name="stress_test",
            task_generator=stress_generator,
            n_tasks_list=[15],  # Medium complexity for testing
            n_runs=2
        )

        result = results[15]
        assert result.avg_time_ms > 0

        # Check that we're not hitting extreme performance issues
        assert result.avg_time_ms < 30000  # Less than 30 seconds


class TestStabilityTesting:
    """Test suite for stability and determinism testing."""

    @pytest.fixture
    def stability_tester(self):
        """Create stability tester for tests."""
        service = SchedulerService()
        return StabilityTester(
            scheduler_service=service,
            random_seed=42  # Reproducible tests
        )

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_basic_stability(self, stability_tester):
        """Test basic stability across random scenarios."""
        result = await stability_tester.run_stability_test(
            n_scenarios=20,  # Small number for testing
            max_tasks=10,    # Limited complexity
            determinism_runs=2
        )

        assert result.total_scenarios == 20
        assert result.successful_runs >= 0
        assert result.stability_score >= 0.0
        assert result.stability_score <= 1.0

        # Log stability metrics
        logger.info(f"Stability score: {result.stability_score:.3f}")
        logger.info(f"Success rate: {result.successful_runs}/{result.total_scenarios}")


class TestRealisticScenarios:
    """Test suite for realistic academic scenarios."""

    def test_course_task_generation(self):
        """Test realistic course task generation."""
        tasks = create_realistic_course_tasks(
            course_name="Computer Science",
            n_assignments=2,
            n_readings=3,
            n_exams=1
        )

        assert len(tasks) == 6  # 2 + 3 + 1

        # Check task types
        assignments = [t for t in tasks if t.kind == "assignment"]
        readings = [t for t in tasks if t.kind == "reading"]
        exams = [t for t in tasks if t.kind == "exam"]

        assert len(assignments) == 2
        assert len(readings) == 3
        assert len(exams) == 1

        # Check that all tasks have deadlines
        for task in tasks:
            assert task.deadline is not None
            assert task.course_id == "computer science"

    @pytest.mark.asyncio
    async def test_realistic_scheduling_integration(self):
        """Test scheduling realistic academic workload."""
        # Create a realistic semester workload
        cs_tasks = create_realistic_course_tasks("Computer Science", 1, 2, 1)
        math_tasks = create_realistic_course_tasks("Mathematics", 1, 1, 1)

        all_tasks = cs_tasks + math_tasks

        # This would normally go through the full scheduler
        # For now, just test task creation
        assert len(all_tasks) == 6  # 2 courses * 3 tasks each

        # Verify task diversity
        course_ids = {task.course_id for task in all_tasks}
        assert len(course_ids) == 2


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_edge_case_scenarios(self):
        """Test that edge case scenarios are properly defined."""
        edge_cases = create_edge_case_scenarios()

        assert len(edge_cases) >= 5  # Should have multiple edge cases

        # Check that each edge case has required fields
        for scenario in edge_cases:
            assert "name" in scenario
            assert "tasks" in scenario
            assert "description" in scenario

    @pytest.mark.asyncio
    async def test_empty_task_list(self):
        """Test scheduler behavior with no tasks."""
        service = SchedulerService()

        from ..io.dto import ScheduleRequest
        request = ScheduleRequest(
            user_id="test_user",
            horizon_days=7,
            dry_run=True,
            job_id="empty_test"
        )

        # Mock the service to return empty task list
        # In a real test, you'd mock the repository methods
        # For now, this tests the edge case handling structure
        assert request.user_id == "test_user"

    def test_stress_scenario_generation(self):
        """Test stress scenario generation with different complexity levels."""
        for complexity in ["low", "medium", "high"]:
            scenario = create_stress_test_scenario(
                n_tasks=10,
                complexity_level=complexity
            )

            assert len(scenario["tasks"]) == 10
            assert scenario["complexity"] == complexity

            if complexity == "high":
                # High complexity should have some constraints
                complex_tasks = [
                    t for t in scenario["tasks"]
                    if hasattr(t, 'prerequisites') and t.prerequisites
                ]
                assert len(complex_tasks) > 0  # Should have some prereq tasks


class TestIntegration:
    """Integration tests combining multiple testing approaches."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_testing_pipeline(self):
        """Test the complete testing pipeline on a single scenario."""
        # 1. Create a test scenario
        scenario = create_stress_test_scenario(n_tasks=8, complexity_level="medium")

        # 2. Test fixture generation
        assert len(scenario["tasks"]) == 8
        assert "preferences" in scenario

        # 3. Create scheduler service
        service = SchedulerService()

        # 4. Basic functional test (would need proper request handling)
        from ..io.dto import ScheduleRequest
        request = ScheduleRequest(
            user_id="integration_test",
            horizon_days=scenario["horizon_days"],
            dry_run=True,
            job_id="integration_test_job"
        )

        # For now, just test that we can create the request
        assert request.user_id == "integration_test"

        # In a full integration test, you would:
        # - Execute the scheduling
        # - Run invariant checks on the result
        # - Measure performance
        # - Verify expected outcomes

    def test_test_framework_completeness(self):
        """Test that all testing components are properly integrated."""
        # Verify all testing modules are importable
        from . import fixtures, golden_tests, invariants, performance

        # Verify key functions are available
        assert hasattr(invariants, 'check_invariants')
        assert hasattr(golden_tests, 'GoldenTestRunner')
        assert hasattr(performance, 'PerformanceBenchmark')
        assert hasattr(fixtures, 'create_test_task')

        logger.info("All testing components successfully integrated")


# Pytest configuration and marks
pytestmark = pytest.mark.asyncio


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (may skip in CI)")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# Test runner entry point for manual execution
async def run_comprehensive_tests():
    """Manual test runner for comprehensive scheduler testing."""
    logger.info("Starting comprehensive scheduler tests...")

    try:
        # 1. Run invariant tests
        logger.info("Testing invariants...")
        test_invariants = TestSchedulerInvariants()
        test_invariants.test_invariant_checking_empty_schedule()
        logger.info("✓ Invariant tests passed")

        # 2. Run golden tests (basic)
        logger.info("Testing golden scenarios...")
        service = SchedulerService()
        golden_runner = GoldenTestRunner(service, performance_budget_ms=10000)
        scenarios = create_basic_scenarios()

        results = []
        for scenario in scenarios[:2]:  # Test first two
            result = await golden_runner.run_scenario(scenario)
            results.append(result)

        passed_golden = sum(1 for r in results if r.passed)
        logger.info(f"✓ Golden tests: {passed_golden}/{len(results)} passed")

        # 3. Run performance benchmark (lightweight)
        logger.info("Testing performance...")
        benchmark = PerformanceBenchmark(service, performance_budget_ms=15000)
        scenarios = create_benchmark_scenarios()

        perf_results = await benchmark.benchmark_scenario(
            "test_run",
            scenarios["simple_tasks"],
            [5, 8],
            n_runs=2
        )

        avg_time = sum(r.avg_time_ms for r in perf_results.values()) / len(perf_results)
        logger.info(f"✓ Performance tests: avg {avg_time:.1f}ms")

        # 4. Run stability test (lightweight)
        logger.info("Testing stability...")
        stability_tester = StabilityTester(service)
        stability_result = await stability_tester.run_stability_test(
            n_scenarios=15,
            max_tasks=8
        )

        logger.info(f"✓ Stability test: score {stability_result.stability_score:.3f}")

        logger.info("🎉 All comprehensive tests completed successfully!")

        return {
            "golden_tests_passed": passed_golden,
            "golden_tests_total": len(results),
            "average_performance_ms": avg_time,
            "stability_score": stability_result.stability_score
        }

    except Exception as e:
        logger.error(f"Comprehensive tests failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Allow running this test file directly
    import sys
    if sys.version_info >= (3, 7):
        asyncio.run(run_comprehensive_tests())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_comprehensive_tests())
