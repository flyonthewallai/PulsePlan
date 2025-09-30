"""
Golden test suite for scheduler validation.

Provides comprehensive test scenarios stored as JSON fixtures with
expected outcomes for regression testing and validation.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.domain import BusyEvent, Preferences, ScheduleSolution, Task
from ..io.dto import ScheduleRequest, ScheduleResponse
from ..service import SchedulerService
from .invariants import check_invariants

logger = logging.getLogger(__name__)


@dataclass
class GoldenTestScenario:
    """A complete test scenario with inputs and expected outcomes."""
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    availability: List[Dict[str, Any]]
    busy_events: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    expected: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class GoldenTestResult:
    """Result of running a golden test scenario."""
    scenario_name: str
    passed: bool
    schedule_produced: bool
    invariants_passed: bool
    expected_matches: bool
    performance_within_bounds: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    execution_time_ms: int


class GoldenTestRunner:
    """
    Runs golden test scenarios against the scheduler service.

    Validates both correctness (invariants, expected outcomes) and
    performance (timing, determinism) of scheduling algorithms.
    """

    def __init__(
        self,
        scheduler_service: Optional[SchedulerService] = None,
        fixtures_dir: Optional[Path] = None,
        performance_budget_ms: int = 2000
    ):
        """
        Initialize golden test runner.

        Args:
            scheduler_service: Scheduler service instance (auto-created if None)
            fixtures_dir: Directory containing test fixtures
            performance_budget_ms: Maximum allowed execution time per scenario
        """
        self.scheduler_service = scheduler_service or SchedulerService()
        self.fixtures_dir = fixtures_dir or Path(__file__).parent / "fixtures"
        self.performance_budget_ms = performance_budget_ms

        # Ensure fixtures directory exists
        self.fixtures_dir.mkdir(exist_ok=True)

    async def run_all_scenarios(self) -> List[GoldenTestResult]:
        """
        Run all golden test scenarios found in fixtures directory.

        Returns:
            List of test results for all scenarios
        """
        scenarios = self.load_all_scenarios()
        results = []

        logger.info(f"Running {len(scenarios)} golden test scenarios")

        for scenario in scenarios:
            try:
                result = await self.run_scenario(scenario)
                results.append(result)

                status = "PASS" if result.passed else "FAIL"
                logger.info(f"Scenario '{scenario.name}': {status} ({result.execution_time_ms}ms)")

                if result.errors:
                    for error in result.errors:
                        logger.error(f"  Error: {error}")

            except Exception as e:
                logger.error(f"Failed to run scenario '{scenario.name}': {e}")
                results.append(GoldenTestResult(
                    scenario_name=scenario.name,
                    passed=False,
                    schedule_produced=False,
                    invariants_passed=False,
                    expected_matches=False,
                    performance_within_bounds=False,
                    errors=[f"Test execution failed: {str(e)}"],
                    warnings=[],
                    metrics={},
                    execution_time_ms=0
                ))

        return results

    async def run_scenario(self, scenario: GoldenTestScenario) -> GoldenTestResult:
        """
        Run a single golden test scenario.

        Args:
            scenario: Test scenario to execute

        Returns:
            Detailed test result
        """
        errors = []
        warnings = []
        metrics = {}
        start_time = datetime.now()

        try:
            # Convert scenario to domain objects
            tasks = self._scenario_to_tasks(scenario)
            busy_events = self._scenario_to_busy_events(scenario)
            preferences = self._scenario_to_preferences(scenario)

            # Build schedule request
            request = ScheduleRequest(
                user_id="golden_test_user",
                horizon_days=scenario.expected.get("horizon_days", 7),
                dry_run=True,  # Don't persist test results
                job_id=f"golden_test_{scenario.name}"
            )

            # Execute scheduling
            response = await self.scheduler_service.schedule(request)
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Check if schedule was produced
            schedule_produced = response.feasible and len(response.blocks) > 0

            # Validate invariants if we got a schedule
            invariants_passed = True
            if schedule_produced:
                try:
                    # Convert response blocks to domain objects for invariant checking
                    schedule_blocks = self._response_to_schedule_blocks(response)

                    # Build solution object
                    solution = ScheduleSolution(
                        feasible=response.feasible,
                        blocks=schedule_blocks,
                        total_scheduled_minutes=sum(block.duration_minutes for block in schedule_blocks),
                        unscheduled_tasks=response.metrics.get("unscheduled_tasks", []),
                        objective_value=response.metrics.get("objective_value", 0.0),
                        solve_time_ms=response.metrics.get("solve_time_ms", execution_time_ms),
                        solver_status=response.metrics.get("solver_status", "unknown")
                    )

                    invariant_result = check_invariants(
                        solution=solution,
                        tasks=tasks,
                        busy_events=busy_events,
                        preferences=preferences,
                        strict=False
                    )

                    invariants_passed = invariant_result.passed
                    if not invariants_passed:
                        errors.extend(invariant_result.violations)
                    warnings.extend(invariant_result.warnings)
                    metrics.update(invariant_result.metrics)

                except Exception as e:
                    invariants_passed = False
                    errors.append(f"Invariant checking failed: {str(e)}")

            # Check expected outcomes
            expected_matches = self._validate_expected_outcomes(response, scenario.expected, errors, warnings)

            # Check performance
            performance_within_bounds = execution_time_ms <= self.performance_budget_ms
            if not performance_within_bounds:
                warnings.append(
                    f"Performance budget exceeded: {execution_time_ms}ms > {self.performance_budget_ms}ms"
                )

            # Calculate additional metrics
            metrics.update({
                'execution_time_ms': execution_time_ms,
                'blocks_produced': len(response.blocks),
                'feasible': response.feasible,
                'solver_status': response.metrics.get('solver_status', 'unknown')
            })

            # Overall pass/fail
            passed = (
                invariants_passed and
                expected_matches and
                performance_within_bounds and
                len(errors) == 0
            )

            return GoldenTestResult(
                scenario_name=scenario.name,
                passed=passed,
                schedule_produced=schedule_produced,
                invariants_passed=invariants_passed,
                expected_matches=expected_matches,
                performance_within_bounds=performance_within_bounds,
                errors=errors,
                warnings=warnings,
                metrics=metrics,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return GoldenTestResult(
                scenario_name=scenario.name,
                passed=False,
                schedule_produced=False,
                invariants_passed=False,
                expected_matches=False,
                performance_within_bounds=False,
                errors=[f"Scenario execution failed: {str(e)}"],
                warnings=[],
                metrics={'execution_time_ms': execution_time_ms},
                execution_time_ms=execution_time_ms
            )

    def load_all_scenarios(self) -> List[GoldenTestScenario]:
        """Load all test scenarios from fixtures directory."""
        scenarios = []

        for fixture_file in self.fixtures_dir.glob("*.json"):
            try:
                scenario = load_test_scenario(fixture_file)
                scenarios.append(scenario)
            except Exception as e:
                logger.error(f"Failed to load scenario from {fixture_file}: {e}")

        return scenarios

    def save_scenario(self, scenario: GoldenTestScenario, filename: Optional[str] = None):
        """Save a test scenario to fixtures directory."""
        if filename is None:
            filename = f"{scenario.name.lower().replace(' ', '_')}.json"

        filepath = self.fixtures_dir / filename

        scenario_dict = asdict(scenario)

        with open(filepath, 'w') as f:
            json.dump(scenario_dict, f, indent=2, default=str)

        logger.info(f"Saved scenario '{scenario.name}' to {filepath}")

    def _scenario_to_tasks(self, scenario: GoldenTestScenario) -> List[Task]:
        """Convert scenario task data to Task domain objects."""
        tasks = []

        for i, task_data in enumerate(scenario.tasks):
            # Parse datetime strings
            deadline = None
            if task_data.get("deadline"):
                deadline = datetime.fromisoformat(task_data["deadline"])

            earliest_start = None
            if task_data.get("earliest_start"):
                earliest_start = datetime.fromisoformat(task_data["earliest_start"])

            task = Task(
                id=task_data.get("id", f"test_task_{i}"),
                user_id="golden_test_user",
                title=task_data.get("title", f"Test Task {i}"),
                kind=task_data.get("kind", "study"),
                estimated_minutes=task_data.get("estimated_minutes", 60),
                min_block_minutes=task_data.get("min_block_minutes", 30),
                max_block_minutes=task_data.get("max_block_minutes", 120),
                deadline=deadline,
                earliest_start=earliest_start,
                preferred_windows=task_data.get("preferred_windows", []),
                avoid_windows=task_data.get("avoid_windows", []),
                fixed=task_data.get("fixed", False),
                prerequisites=task_data.get("prerequisites", []),
                weight=task_data.get("weight", 1.0),
                course_id=task_data.get("course_id"),
                tags=task_data.get("tags", [])
            )
            tasks.append(task)

        return tasks

    def _scenario_to_busy_events(self, scenario: GoldenTestScenario) -> List[BusyEvent]:
        """Convert scenario busy event data to BusyEvent domain objects."""
        events = []

        for i, event_data in enumerate(scenario.busy_events):
            start = datetime.fromisoformat(event_data["start"])
            end = datetime.fromisoformat(event_data["end"])

            event = BusyEvent(
                id=event_data.get("id", f"test_event_{i}"),
                source=event_data.get("source", "pulse"),
                start=start,
                end=end,
                title=event_data.get("title", f"Test Event {i}"),
                movable=event_data.get("movable", False),
                hard=event_data.get("hard", True),
                location=event_data.get("location"),
                metadata=event_data.get("metadata", {})
            )
            events.append(event)

        return events

    def _scenario_to_preferences(self, scenario: GoldenTestScenario) -> Preferences:
        """Convert scenario preferences data to Preferences domain object."""
        prefs_data = scenario.preferences

        return Preferences(
            timezone=prefs_data.get("timezone", "UTC"),
            workday_start=prefs_data.get("workday_start", "08:30"),
            workday_end=prefs_data.get("workday_end", "22:00"),
            break_every_minutes=prefs_data.get("break_every_minutes", 50),
            break_duration_minutes=prefs_data.get("break_duration_minutes", 10),
            deep_work_windows=prefs_data.get("deep_work_windows", []),
            no_study_windows=prefs_data.get("no_study_windows", []),
            max_daily_effort_minutes=prefs_data.get("max_daily_effort_minutes", 480),
            max_concurrent_courses=prefs_data.get("max_concurrent_courses", 3),
            spacing_policy=prefs_data.get("spacing_policy", {}),
            latenight_penalty=prefs_data.get("latenight_penalty", 3.0),
            morning_penalty=prefs_data.get("morning_penalty", 1.0),
            context_switch_penalty=prefs_data.get("context_switch_penalty", 2.0),
            min_gap_between_blocks=prefs_data.get("min_gap_between_blocks", 15),
            session_granularity_minutes=prefs_data.get("session_granularity_minutes", 30)
        )

    def _response_to_schedule_blocks(self, response: ScheduleResponse) -> List:
        """Convert response blocks to domain ScheduleBlock objects."""
        from ..core.domain import ScheduleBlock

        blocks = []
        for block_data in response.blocks:
            start = datetime.fromisoformat(block_data.start)
            end = datetime.fromisoformat(block_data.end)

            block = ScheduleBlock(
                task_id=block_data.task_id,
                start=start,
                end=end,
                estimated_completion_probability=block_data.metadata.get("completion_probability", 0.0),
                utility_score=block_data.metadata.get("utility_score", 0.0),
                penalties_applied=block_data.metadata.get("penalties_applied", {}),
                alternatives=block_data.metadata.get("alternatives", [])
            )
            blocks.append(block)

        return blocks

    def _validate_expected_outcomes(
        self,
        response: ScheduleResponse,
        expected: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> bool:
        """Validate that response matches expected outcomes."""
        matches = True

        # Check feasibility expectation
        expected_feasible = expected.get("feasible", True)
        if response.feasible != expected_feasible:
            errors.append(
                f"Feasibility mismatch: got {response.feasible}, expected {expected_feasible}"
            )
            matches = False

        # Check number of tasks scheduled
        expected_scheduled = expected.get("num_tasks_scheduled")
        if expected_scheduled is not None:
            actual_scheduled = len(set(block.task_id for block in response.blocks))
            if actual_scheduled != expected_scheduled:
                errors.append(
                    f"Scheduled tasks count mismatch: got {actual_scheduled}, expected {expected_scheduled}"
                )
                matches = False

        # Check total scheduled time (with tolerance)
        expected_total_time = expected.get("total_scheduled_minutes")
        if expected_total_time is not None:
            actual_total_time = sum(
                (datetime.fromisoformat(block.end) - datetime.fromisoformat(block.start)).total_seconds() / 60
                for block in response.blocks
            )
            tolerance = expected.get("time_tolerance_minutes", 30)

            if abs(actual_total_time - expected_total_time) > tolerance:
                errors.append(
                    f"Total scheduled time mismatch: got {actual_total_time}min, "
                    f"expected {expected_total_time}min (±{tolerance}min)"
                )
                matches = False

        # Check solver status if specified
        expected_solver_status = expected.get("solver_status")
        if expected_solver_status is not None:
            actual_status = response.metrics.get("solver_status")
            if actual_status != expected_solver_status:
                warnings.append(
                    f"Solver status difference: got {actual_status}, expected {expected_solver_status}"
                )

        # Check specific task assignments if provided
        expected_assignments = expected.get("task_assignments", {})
        for task_id, expected_count in expected_assignments.items():
            actual_count = sum(1 for block in response.blocks if block.task_id == task_id)
            if actual_count != expected_count:
                errors.append(
                    f"Task {task_id} assignment mismatch: got {actual_count} blocks, "
                    f"expected {expected_count}"
                )
                matches = False

        return matches


def load_test_scenario(filepath: Path) -> GoldenTestScenario:
    """
    Load a test scenario from JSON file.

    Args:
        filepath: Path to the JSON fixture file

    Returns:
        GoldenTestScenario object

    Raises:
        ValueError: If the file format is invalid
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Validate required fields
        required_fields = ['name', 'tasks', 'availability', 'expected']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return GoldenTestScenario(
            name=data['name'],
            description=data.get('description', ''),
            tasks=data['tasks'],
            availability=data['availability'],
            busy_events=data.get('busy_events', []),
            preferences=data.get('preferences', {}),
            expected=data['expected'],
            metadata=data.get('metadata', {})
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load scenario from {filepath}: {e}")


def create_basic_scenarios() -> List[GoldenTestScenario]:
    """Create a set of basic test scenarios for common use cases."""
    scenarios = []

    # Scenario 1: Simple two-task scheduling
    scenarios.append(GoldenTestScenario(
        name="simple_two_tasks",
        description="Basic scenario with two tasks and clear availability",
        tasks=[
            {
                "id": "essay",
                "title": "Essay Assignment",
                "kind": "assignment",
                "estimated_minutes": 120,
                "min_block_minutes": 60,
                "max_block_minutes": 120,
                "deadline": "2025-09-30T23:59:00",
                "weight": 2.0
            },
            {
                "id": "quiz_prep",
                "title": "Quiz Preparation",
                "kind": "study",
                "estimated_minutes": 60,
                "min_block_minutes": 30,
                "max_block_minutes": 90,
                "deadline": "2025-09-28T23:59:00",
                "weight": 1.5
            }
        ],
        availability=[
            {
                "start": "2025-09-26T09:00:00",
                "end": "2025-09-26T17:00:00"
            }
        ],
        busy_events=[],
        preferences={
            "timezone": "UTC",
            "workday_start": "09:00",
            "workday_end": "17:00",
            "max_daily_effort_minutes": 480,
            "session_granularity_minutes": 30
        },
        expected={
            "feasible": True,
            "num_tasks_scheduled": 2,
            "total_scheduled_minutes": 180,
            "time_tolerance_minutes": 30
        },
        metadata={
            "category": "basic",
            "complexity": "low"
        }
    ))

    # Scenario 2: Deadline conflict
    scenarios.append(GoldenTestScenario(
        name="deadline_conflict",
        description="Tasks with tight deadlines that may not all fit",
        tasks=[
            {
                "id": "urgent_task",
                "title": "Urgent Assignment",
                "kind": "assignment",
                "estimated_minutes": 240,
                "min_block_minutes": 120,
                "deadline": "2025-09-26T18:00:00",
                "weight": 3.0
            },
            {
                "id": "long_task",
                "title": "Long Project",
                "kind": "project",
                "estimated_minutes": 360,
                "min_block_minutes": 60,
                "deadline": "2025-09-26T20:00:00",
                "weight": 2.0
            }
        ],
        availability=[
            {
                "start": "2025-09-26T09:00:00",
                "end": "2025-09-26T17:00:00"
            }
        ],
        busy_events=[
            {
                "id": "meeting",
                "title": "Team Meeting",
                "start": "2025-09-26T14:00:00",
                "end": "2025-09-26T15:00:00",
                "hard": True
            }
        ],
        preferences={
            "timezone": "UTC",
            "workday_start": "09:00",
            "workday_end": "17:00",
            "max_daily_effort_minutes": 420,
            "session_granularity_minutes": 30
        },
        expected={
            "feasible": False,
            "num_tasks_scheduled": 1,
            "solver_status": "infeasible"
        },
        metadata={
            "category": "constraints",
            "complexity": "medium"
        }
    ))

    # Scenario 3: Complex multi-day scenario
    scenarios.append(GoldenTestScenario(
        name="multi_day_complex",
        description="Multiple tasks across several days with various constraints",
        tasks=[
            {
                "id": "research",
                "title": "Research Paper",
                "kind": "project",
                "estimated_minutes": 480,
                "min_block_minutes": 90,
                "max_block_minutes": 180,
                "deadline": "2025-09-29T23:59:00",
                "weight": 2.5
            },
            {
                "id": "coding_hw",
                "title": "Coding Homework",
                "kind": "assignment",
                "estimated_minutes": 180,
                "min_block_minutes": 60,
                "deadline": "2025-09-28T23:59:00",
                "weight": 2.0,
                "prerequisites": []
            },
            {
                "id": "reading",
                "title": "Course Reading",
                "kind": "reading",
                "estimated_minutes": 120,
                "min_block_minutes": 30,
                "weight": 1.0
            }
        ],
        availability=[
            {
                "start": "2025-09-26T09:00:00",
                "end": "2025-09-26T17:00:00"
            },
            {
                "start": "2025-09-27T09:00:00",
                "end": "2025-09-27T17:00:00"
            },
            {
                "start": "2025-09-28T09:00:00",
                "end": "2025-09-28T17:00:00"
            }
        ],
        busy_events=[
            {
                "id": "class1",
                "title": "Lecture",
                "start": "2025-09-26T10:00:00",
                "end": "2025-09-26T11:30:00",
                "hard": True
            },
            {
                "id": "class2",
                "title": "Lecture",
                "start": "2025-09-27T10:00:00",
                "end": "2025-09-27T11:30:00",
                "hard": True
            }
        ],
        preferences={
            "timezone": "UTC",
            "workday_start": "09:00",
            "workday_end": "17:00",
            "max_daily_effort_minutes": 360,
            "session_granularity_minutes": 30,
            "deep_work_windows": [
                {"dow": 0, "start": "14:00", "end": "16:00"},
                {"dow": 1, "start": "14:00", "end": "16:00"}
            ]
        },
        expected={
            "feasible": True,
            "num_tasks_scheduled": 3,
            "total_scheduled_minutes": 780,
            "time_tolerance_minutes": 60
        },
        metadata={
            "category": "comprehensive",
            "complexity": "high"
        }
    ))

    return scenarios
