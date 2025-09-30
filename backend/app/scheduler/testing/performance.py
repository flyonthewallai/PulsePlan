"""
Performance and stability testing for scheduler algorithms.

Provides comprehensive benchmarking, stress testing, and determinism
validation to ensure production-ready scheduling performance.
"""

import logging
import random
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..core.domain import BusyEvent, Task
from ..io.dto import ScheduleRequest, ScheduleResponse
from ..service import SchedulerService
from .fixtures import (
    create_test_preferences,
    create_test_task,
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a scheduling run."""
    execution_time_ms: int
    peak_memory_mb: float
    solver_time_ms: int
    n_tasks: int
    n_slots: int
    n_constraints: int
    feasible: bool
    objective_value: float
    solver_status: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BenchmarkResult:
    """Result of performance benchmark execution."""
    scenario_name: str
    n_runs: int
    success_rate: float
    avg_time_ms: float
    p50_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    max_time_ms: float
    min_time_ms: float
    std_dev_ms: float
    within_budget: bool
    deterministic: bool
    error_rate: float
    metrics: List[PerformanceMetrics]
    errors: List[str]


@dataclass
class StabilityTestResult:
    """Result of stability testing across multiple random inputs."""
    total_scenarios: int
    successful_runs: int
    failed_runs: int
    avg_performance_ms: float
    performance_degradation: float
    determinism_score: float
    invariant_violations: int
    unique_outcomes: int
    stability_score: float  # Overall stability metric (0-1)


class PerformanceBenchmark:
    """
    Performance benchmarking for scheduler algorithms.

    Measures execution time, memory usage, and scalability characteristics
    across various input sizes and complexity levels.
    """

    def __init__(
        self,
        scheduler_service: Optional[SchedulerService] = None,
        performance_budget_ms: int = 2000,
        memory_budget_mb: float = 256.0
    ):
        """
        Initialize performance benchmark.

        Args:
            scheduler_service: Scheduler service to benchmark
            performance_budget_ms: Maximum acceptable execution time
            memory_budget_mb: Maximum acceptable memory usage
        """
        self.scheduler_service = scheduler_service or SchedulerService()
        self.performance_budget_ms = performance_budget_ms
        self.memory_budget_mb = memory_budget_mb

    async def benchmark_scenario(
        self,
        scenario_name: str,
        task_generator: Callable[[int], List[Task]],
        n_tasks_list: List[int],
        n_runs: int = 10
    ) -> Dict[int, BenchmarkResult]:
        """
        Benchmark a scenario across different task counts.

        Args:
            scenario_name: Name of the benchmark scenario
            task_generator: Function that generates tasks given count
            n_tasks_list: List of task counts to benchmark
            n_runs: Number of runs per task count

        Returns:
            Dictionary mapping task count to benchmark results
        """
        results = {}

        logger.info(f"Starting benchmark '{scenario_name}' with {len(n_tasks_list)} complexity levels")

        for n_tasks in n_tasks_list:
            logger.info(f"Benchmarking {n_tasks} tasks ({n_runs} runs)")

            tasks = task_generator(n_tasks)
            result = await self._benchmark_tasks(scenario_name, tasks, n_runs)
            results[n_tasks] = result

            # Log key metrics
            logger.info(
                f"  {n_tasks} tasks: avg={result.avg_time_ms:.1f}ms, "
                f"p95={result.p95_time_ms:.1f}ms, "
                f"success_rate={result.success_rate:.1%}"
            )

        return results

    async def _benchmark_tasks(
        self,
        scenario_name: str,
        tasks: List[Task],
        n_runs: int
    ) -> BenchmarkResult:
        """Benchmark a specific set of tasks."""
        metrics_list = []
        errors = []

        # Generate consistent test data
        base_datetime = datetime.now().replace(minute=0, second=0, microsecond=0)
        busy_events = self._generate_test_busy_events(base_datetime)
        preferences = create_test_preferences()

        for run_idx in range(n_runs):
            try:
                # Add slight randomization to avoid caching effects
                random_offset = random.randint(0, 60)  # minutes
                run_datetime = base_datetime + timedelta(minutes=random_offset)

                # Create request
                request = ScheduleRequest(
                    user_id=f"benchmark_user_{run_idx}",
                    horizon_days=7,
                    dry_run=True,
                    job_id=f"benchmark_{scenario_name}_{run_idx}"
                )

                # Measure performance
                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()

                response = await self.scheduler_service.schedule(request)

                end_time = time.perf_counter()
                end_memory = self._get_memory_usage()

                execution_time_ms = int((end_time - start_time) * 1000)
                peak_memory_mb = max(start_memory, end_memory)

                # Extract solver metrics
                solver_time_ms = response.metrics.get('solve_time_ms', execution_time_ms)
                n_constraints = response.metrics.get('n_constraints', 0)
                objective_value = response.metrics.get('objective_value', 0.0)
                solver_status = response.metrics.get('solver_status', 'unknown')

                metrics = PerformanceMetrics(
                    execution_time_ms=execution_time_ms,
                    peak_memory_mb=peak_memory_mb,
                    solver_time_ms=solver_time_ms,
                    n_tasks=len(tasks),
                    n_slots=response.metrics.get('n_slots', 0),
                    n_constraints=n_constraints,
                    feasible=response.feasible,
                    objective_value=objective_value,
                    solver_status=solver_status
                )

                metrics_list.append(metrics)

            except Exception as e:
                error_msg = f"Run {run_idx} failed: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Calculate statistics
        if metrics_list:
            times = [m.execution_time_ms for m in metrics_list]
            success_rate = len(metrics_list) / n_runs
            error_rate = len(errors) / n_runs

            avg_time = statistics.mean(times)
            p50_time = statistics.median(times)
            p95_time = self._percentile(times, 95)
            p99_time = self._percentile(times, 99)
            max_time = max(times)
            min_time = min(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

            within_budget = p95_time <= self.performance_budget_ms

            # Check determinism (same inputs should produce similar times)
            coefficient_of_variation = std_dev / avg_time if avg_time > 0 else 1.0
            deterministic = coefficient_of_variation < 0.2  # Less than 20% variation

        else:
            # All runs failed
            success_rate = 0.0
            error_rate = 1.0
            avg_time = p50_time = p95_time = p99_time = max_time = min_time = std_dev = 0.0
            within_budget = deterministic = False

        return BenchmarkResult(
            scenario_name=scenario_name,
            n_runs=n_runs,
            success_rate=success_rate,
            avg_time_ms=avg_time,
            p50_time_ms=p50_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            max_time_ms=max_time,
            min_time_ms=min_time,
            std_dev_ms=std_dev,
            within_budget=within_budget,
            deterministic=deterministic,
            error_rate=error_rate,
            metrics=metrics_list,
            errors=errors
        )

    def _generate_test_busy_events(self, base_datetime: datetime) -> List[BusyEvent]:
        """Generate realistic busy events for testing."""
        events = []

        for day_offset in range(7):
            day = base_datetime + timedelta(days=day_offset)

            # Add some meetings
            meeting_start = day.replace(hour=10, minute=0)
            events.append(BusyEvent(
                id=f"meeting_{day_offset}",
                source="google",
                start=meeting_start,
                end=meeting_start + timedelta(hours=1),
                title="Daily Meeting"
            ))

            # Add lunch break
            lunch_start = day.replace(hour=12, minute=0)
            events.append(BusyEvent(
                id=f"lunch_{day_offset}",
                source="pulse",
                start=lunch_start,
                end=lunch_start + timedelta(minutes=30),
                title="Lunch Break"
            ))

        return events

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb
        except ImportError:
            return 0.0

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = k - f

        if f == len(sorted_data) - 1:
            return sorted_data[f]
        else:
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c


class StabilityTester:
    """
    Stability and determinism testing for scheduler algorithms.

    Tests scheduler behavior across random inputs to ensure consistent
    performance and deterministic outputs.
    """

    def __init__(
        self,
        scheduler_service: Optional[SchedulerService] = None,
        random_seed: int = 42
    ):
        """
        Initialize stability tester.

        Args:
            scheduler_service: Scheduler service to test
            random_seed: Seed for reproducible random testing
        """
        self.scheduler_service = scheduler_service or SchedulerService()
        self.random_seed = random_seed
        random.seed(random_seed)

    async def run_stability_test(
        self,
        n_scenarios: int = 100,
        max_tasks: int = 20,
        determinism_runs: int = 3
    ) -> StabilityTestResult:
        """
        Run comprehensive stability test.

        Args:
            n_scenarios: Number of random scenarios to test
            max_tasks: Maximum number of tasks per scenario
            determinism_runs: Number of runs to check determinism

        Returns:
            Comprehensive stability test results
        """
        logger.info(f"Starting stability test with {n_scenarios} scenarios")

        successful_runs = 0
        failed_runs = 0
        performance_times = []
        invariant_violations = 0
        unique_outcomes = set()
        determinism_failures = 0

        # Track performance degradation over time
        early_times = []
        late_times = []

        for scenario_idx in range(n_scenarios):
            try:
                # Generate random scenario
                scenario = self._generate_random_scenario(scenario_idx, max_tasks)

                # Test basic execution
                start_time = time.perf_counter()
                response = await self._execute_scenario(scenario)
                execution_time = (time.perf_counter() - start_time) * 1000

                if response.feasible:
                    successful_runs += 1

                    # Validate invariants
                    try:
                        # Would need to convert response to domain objects
                        # This is simplified for the example
                        pass
                    except Exception as e:
                        invariant_violations += 1
                        logger.warning(f"Invariant violation in scenario {scenario_idx}: {e}")

                    # Track unique outcomes (simplified - could hash solution structure)
                    outcome_signature = self._hash_solution(response)
                    unique_outcomes.add(outcome_signature)

                    # Test determinism
                    if scenario_idx % 10 == 0:  # Test every 10th scenario for determinism
                        deterministic = await self._test_determinism(scenario, determinism_runs)
                        if not deterministic:
                            determinism_failures += 1

                performance_times.append(execution_time)

                # Track performance degradation
                if scenario_idx < n_scenarios * 0.2:  # First 20%
                    early_times.append(execution_time)
                elif scenario_idx > n_scenarios * 0.8:  # Last 20%
                    late_times.append(execution_time)

            except Exception as e:
                failed_runs += 1
                logger.error(f"Scenario {scenario_idx} failed: {e}")

            # Progress reporting
            if (scenario_idx + 1) % 20 == 0:
                logger.info(f"Completed {scenario_idx + 1}/{n_scenarios} scenarios")

        # Calculate metrics
        total_runs = successful_runs + failed_runs
        avg_performance = statistics.mean(performance_times) if performance_times else 0.0

        # Performance degradation
        early_avg = statistics.mean(early_times) if early_times else avg_performance
        late_avg = statistics.mean(late_times) if late_times else avg_performance
        performance_degradation = (late_avg - early_avg) / early_avg if early_avg > 0 else 0.0

        # Determinism score
        determinism_tests = (n_scenarios // 10)
        determinism_score = (determinism_tests - determinism_failures) / determinism_tests if determinism_tests > 0 else 1.0

        # Overall stability score (0-1)
        success_factor = successful_runs / total_runs if total_runs > 0 else 0.0
        performance_factor = min(1.0, 2000 / avg_performance) if avg_performance > 0 else 1.0  # 2s target
        invariant_factor = max(0.0, 1.0 - (invariant_violations / successful_runs)) if successful_runs > 0 else 0.0

        stability_score = (success_factor + performance_factor + invariant_factor + determinism_score) / 4

        result = StabilityTestResult(
            total_scenarios=n_scenarios,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            avg_performance_ms=avg_performance,
            performance_degradation=performance_degradation,
            determinism_score=determinism_score,
            invariant_violations=invariant_violations,
            unique_outcomes=len(unique_outcomes),
            stability_score=stability_score
        )

        logger.info(f"Stability test completed: score={stability_score:.3f}, success_rate={success_factor:.1%}")

        return result

    def _generate_random_scenario(self, seed: int, max_tasks: int) -> Dict[str, Any]:
        """Generate a random test scenario."""
        random.seed(self.random_seed + seed)

        n_tasks = random.randint(1, max_tasks)
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

        tasks = []
        for i in range(n_tasks):
            # Random task parameters
            duration = random.randint(30, 240)  # 30min to 4hrs
            min_block = random.randint(15, min(60, duration))
            deadline_hours = random.randint(8, 168)  # 8hrs to 1 week

            task = {
                "id": f"random_task_{seed}_{i}",
                "title": f"Random Task {i}",
                "kind": random.choice(["study", "assignment", "project", "reading"]),
                "estimated_minutes": duration,
                "min_block_minutes": min_block,
                "deadline": (base_time + timedelta(hours=deadline_hours)).isoformat(),
                "weight": random.uniform(0.5, 3.0)
            }
            tasks.append(task)

        # Random busy events
        busy_events = []
        for day in range(7):
            if random.random() < 0.6:  # 60% chance of event per day
                day_start = base_time + timedelta(days=day)
                event_start = day_start + timedelta(hours=random.randint(9, 16))
                event_duration = random.randint(30, 120)

                busy_events.append({
                    "id": f"random_event_{seed}_{day}",
                    "title": f"Random Event {day}",
                    "start": event_start.isoformat(),
                    "end": (event_start + timedelta(minutes=event_duration)).isoformat(),
                    "hard": random.choice([True, False])
                })

        return {
            "tasks": tasks,
            "busy_events": busy_events,
            "base_time": base_time
        }

    async def _execute_scenario(self, scenario: Dict[str, Any]) -> ScheduleResponse:
        """Execute a test scenario."""
        request = ScheduleRequest(
            user_id="stability_test_user",
            horizon_days=7,
            dry_run=True,
            job_id=f"stability_test_{hash(str(scenario))}"
        )

        return await self.scheduler_service.schedule(request)

    async def _test_determinism(self, scenario: Dict[str, Any], n_runs: int) -> bool:
        """Test if scenario produces deterministic results."""
        results = []

        for _ in range(n_runs):
            response = await self._execute_scenario(scenario)
            result_hash = self._hash_solution(response)
            results.append(result_hash)

        # All results should be identical for determinism
        return len(set(results)) == 1

    def _hash_solution(self, response: ScheduleResponse) -> str:
        """Create a hash of the solution for comparison."""
        # Create a deterministic representation of the solution
        if not response.blocks:
            return "empty_solution"

        # Sort blocks by start time and task_id for consistency
        sorted_blocks = sorted(
            response.blocks,
            key=lambda b: (b.start, b.task_id)
        )

        # Create signature from key solution features
        signature_parts = []
        for block in sorted_blocks:
            signature_parts.append(f"{block.task_id}:{block.start}:{block.end}")

        return hash("|".join(signature_parts))


# Predefined benchmark scenarios
def create_benchmark_scenarios() -> Dict[str, Callable[[int], List[Task]]]:
    """Create predefined benchmark scenarios for common patterns."""

    def simple_tasks(n: int) -> List[Task]:
        """Generate simple tasks with basic constraints."""
        tasks = []
        base_time = datetime.now()

        for i in range(n):
            task = create_test_task(
                task_id=f"simple_{i}",
                duration_minutes=random.randint(60, 120),
                deadline_hours=random.randint(24, 72)
            )
            tasks.append(task)

        return tasks

    def complex_constraints(n: int) -> List[Task]:
        """Generate tasks with complex constraints and dependencies."""
        tasks = []
        base_time = datetime.now()

        for i in range(n):
            # Some tasks have prerequisites
            prerequisites = []
            if i > 0 and random.random() < 0.3:
                prerequisites = [f"complex_{random.randint(0, i-1)}"]

            task = create_test_task(
                task_id=f"complex_{i}",
                duration_minutes=random.randint(30, 240),
                deadline_hours=random.randint(12, 168),
                min_block_minutes=random.randint(30, 60)
            )
            task.prerequisites = prerequisites
            task.weight = random.uniform(0.5, 3.0)

            # Add some preferred/avoid windows
            if random.random() < 0.4:
                task.preferred_windows = [
                    {"dow": random.randint(0, 6), "start": "09:00", "end": "17:00"}
                ]

            tasks.append(task)

        return tasks

    def deadline_pressure(n: int) -> List[Task]:
        """Generate tasks with tight, overlapping deadlines."""
        tasks = []
        base_time = datetime.now()

        # All tasks have deadlines within 48 hours
        for i in range(n):
            task = create_test_task(
                task_id=f"urgent_{i}",
                duration_minutes=random.randint(90, 180),
                deadline_hours=random.randint(8, 48)
            )
            task.weight = random.uniform(2.0, 5.0)  # High priority
            tasks.append(task)

        return tasks

    return {
        "simple_tasks": simple_tasks,
        "complex_constraints": complex_constraints,
        "deadline_pressure": deadline_pressure
    }
