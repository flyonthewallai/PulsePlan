# Scheduler Testing Framework

A comprehensive testing suite for the PulsePlan scheduling system with invariant checking, golden tests, performance benchmarks, and stability testing.

## Overview

This testing framework implements the 3-step validation approach you requested:

1. **Step 1: Invariants as Code** - Automated checking of fundamental scheduling constraints
2. **Step 2: Golden Test Suite** - JSON-based scenarios with expected outcomes
3. **Step 3: Performance & Stability Testing** - Benchmarking and determinism validation

## Features

- ✅ **Invariant Checking** - Validates 10+ fundamental scheduling constraints
- ✅ **Golden Tests** - JSON fixture-based regression testing
- ✅ **Performance Benchmarks** - Scalability and timing analysis
- ✅ **Stability Testing** - Determinism and reliability validation
- ✅ **Realistic Fixtures** - Academic workload simulation
- ✅ **Edge Case Testing** - Boundary condition validation
- ✅ **Integration with pytest** - Standard testing workflow

## Quick Start

```bash
# Run all tests (fast mode)
cd backend/app/scheduler/testing
python run_tests.py --fast

# Run full comprehensive suite
python run_tests.py --full

# Run specific test categories
python run_tests.py --golden
python run_tests.py --performance
python run_tests.py --stability
python run_tests.py --invariants
```

## Architecture

```
testing/
├── __init__.py                     # Module exports
├── invariants.py                   # Constraint validation
├── golden_tests.py                 # JSON scenario testing
├── performance.py                  # Benchmarking & stability
├── fixtures.py                     # Test data generation
├── test_scheduler_comprehensive.py # pytest integration
├── run_tests.py                   # Test runner script
├── README.md                      # This documentation
└── fixtures/                      # JSON test scenarios
    ├── simple_two_tasks.json
    └── deadline_conflict.json
```

## Step 1: Invariants as Code

The `invariants.py` module implements comprehensive constraint checking:

### Usage Example
```python
from app.scheduler.testing.invariants import check_invariants

result = check_invariants(
    solution=schedule_solution,
    tasks=original_tasks,
    busy_events=calendar_events,
    preferences=user_preferences,
    strict=True  # Raises exception on violations
)

print(f"Passed: {result.passed}")
print(f"Violations: {result.violations}")
print(f"Checked: {result.checked_invariants}")
```

### Implemented Invariants
1. **No Overlaps** - Schedule blocks don't conflict
2. **Block Duration Consistency** - Duration matches start/end times
3. **Temporal Ordering** - All blocks have start < end
4. **Task Assignment Consistency** - All blocks reference valid tasks
5. **Minimum Block Lengths** - Blocks meet minimum duration requirements
6. **Deadline Compliance** - No tasks scheduled after deadlines
7. **Prerequisite Ordering** - Dependencies are respected
8. **No Calendar Conflicts** - No overlap with existing events
9. **Preference Compliance** - User preferences are honored
10. **Daily Effort Limits** - Daily work limits are respected
11. **Time Index Alignment** - Blocks align with time granularity
12. **Solution Metadata Consistency** - Solution stats match blocks

## Step 2: Golden Test Suite

JSON-based scenarios with expected outcomes for regression testing.

### Scenario Format
```json
{
  "name": "simple_two_tasks",
  "description": "Basic scenario with two tasks",
  "tasks": [
    {
      "id": "essay",
      "title": "Essay Assignment",
      "estimated_minutes": 120,
      "deadline": "2025-09-30T23:59:00"
    }
  ],
  "availability": [
    {
      "start": "2025-09-26T09:00:00",
      "end": "2025-09-26T17:00:00"
    }
  ],
  "expected": {
    "feasible": true,
    "num_tasks_scheduled": 2,
    "total_scheduled_minutes": 180
  }
}
```

### Usage Example
```python
from app.scheduler.testing.golden_tests import GoldenTestRunner

runner = GoldenTestRunner()
results = await runner.run_all_scenarios()

for result in results:
    print(f"{result.scenario_name}: {'PASS' if result.passed else 'FAIL'}")
```

## Step 3: Performance & Stability Testing

Comprehensive performance analysis and stability validation.

### Performance Benchmarks
```python
from app.scheduler.testing.performance import PerformanceBenchmark

benchmark = PerformanceBenchmark(performance_budget_ms=2000)

results = await benchmark.benchmark_scenario(
    scenario_name="scaling_test",
    task_generator=lambda n: create_n_tasks(n),
    n_tasks_list=[10, 25, 50, 100],
    n_runs=10
)

print(f"P95 performance: {results[50].p95_time_ms}ms")
```

### Stability Testing
```python
from app.scheduler.testing.performance import StabilityTester

tester = StabilityTester(random_seed=42)

result = await tester.run_stability_test(
    n_scenarios=100,
    max_tasks=20
)

print(f"Stability score: {result.stability_score:.3f}")
print(f"Determinism score: {result.determinism_score:.3f}")
```

## Test Categories

### 1. Unit Tests (Fast)
- Invariant checking validation
- Fixture generation
- Basic functionality tests

### 2. Golden Tests (Medium)
- Predefined scenario execution
- Expected outcome validation
- Regression detection

### 3. Performance Tests (Slow)
- Scalability benchmarks
- Memory usage analysis
- Response time percentiles

### 4. Stability Tests (Slow)
- Random scenario generation
- Determinism validation
- Long-running reliability

## Creating Custom Tests

### Add New Invariant
```python
def _check_my_constraint(blocks, violations, checked):
    checked.append("my_constraint")

    for block in blocks:
        if my_constraint_violated(block):
            violations.append(f"My constraint violated: {block.task_id}")
```

### Add Golden Scenario
```python
# Create JSON fixture in fixtures/ directory
{
  "name": "my_scenario",
  "tasks": [...],
  "expected": {...}
}
```

### Add Performance Scenario
```python
def my_task_generator(n_tasks: int) -> List[Task]:
    return [create_complex_task(i) for i in range(n_tasks)]

scenarios["my_scenario"] = my_task_generator
```

## Integration with Existing Tests

The framework integrates with your existing pytest setup:

```bash
# Run with pytest
pytest app/scheduler/testing/test_scheduler_comprehensive.py

# Run specific test classes
pytest app/scheduler/testing/test_scheduler_comprehensive.py::TestSchedulerInvariants

# Run with markers
pytest -m "not slow"  # Skip slow tests
```

## Continuous Integration

Example CI configuration:

```yaml
# .github/workflows/scheduler-tests.yml
- name: Run Fast Scheduler Tests
  run: |
    cd backend
    python app/scheduler/testing/run_tests.py --fast --output ci_results.json

- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: scheduler-test-results
    path: backend/ci_results.json
```

## Configuration

### Environment Variables
- `SCHEDULER_TEST_BUDGET_MS` - Performance budget (default: 2000)
- `SCHEDULER_TEST_MEMORY_MB` - Memory budget (default: 256)
- `SCHEDULER_TEST_SEED` - Random seed (default: 42)

### Test Fixtures Directory
Default: `app/scheduler/testing/fixtures/`

Override with:
```python
runner = GoldenTestRunner(fixtures_dir=Path("custom/fixtures"))
```

## Troubleshooting

### Common Issues

1. **OR-Tools Warning**: Normal for development, indicates fallback solver use
2. **Unicode Errors**: Use ASCII output in Windows environments
3. **Performance Timeouts**: Increase budget or use `--fast` mode
4. **Import Errors**: Ensure `backend/` is in Python path

### Debug Mode
```bash
python run_tests.py --verbose
```

### Manual Testing
```python
# Test individual components
from app.scheduler.testing import check_invariants, create_test_task

task = create_test_task("debug_task")
print(f"Created task: {task.title} ({task.estimated_minutes}min)")
```

## Metrics and Reporting

The framework generates comprehensive metrics:

- **Invariant Violations**: Count and descriptions
- **Performance Percentiles**: P50, P95, P99 response times
- **Success Rates**: Pass/fail ratios across scenarios
- **Stability Scores**: Overall system reliability (0-1)
- **Memory Usage**: Peak memory consumption
- **Determinism**: Consistency of outputs

Results are saved in JSON format for further analysis and tracking over time.

## Future Enhancements

- [ ] Visual performance dashboards
- [ ] Automated regression detection
- [ ] Load testing with concurrent users
- [ ] Integration with monitoring systems
- [ ] Custom constraint DSL
- [ ] Fuzzing and property-based testing