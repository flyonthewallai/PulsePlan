# Scheduler Acceptance Gate

The Scheduler Acceptance Gate is a comprehensive testing framework that validates all critical components of the PulsePlan scheduling system before deployment. It ensures production readiness through rigorous testing of functionality, performance, safety, and integration.

## Overview

The acceptance gate consists of multiple test categories that must all pass for deployment approval:

1. **Core Functionality Tests** - Basic scheduling operations
2. **Invariant Tests** - Business rule compliance
3. **Golden Scenario Tests** - Regression testing with known scenarios
4. **Performance Tests** - Speed and scalability validation
5. **Safety Tests** - ML safety rails and monitoring
6. **Semantic Verification Tests** - API response correctness
7. **Integration Tests** - End-to-end system validation
8. **Stress Tests** - Edge cases and error recovery

## Usage

### Local Development

```bash
# Run the full acceptance gate
make test-acceptance-gate

# Or run directly with Python
python scripts/run_acceptance_gate.py
```

### CI/CD Integration

The acceptance gate automatically runs in GitHub Actions on:
- Pull requests affecting scheduler code
- Pushes to main/develop branches

See `.github/workflows/scheduler_acceptance_gate.yml` for the complete CI configuration.

## Test Categories

### 1. Core Functionality Tests

Validates basic scheduling operations:

- **Basic Scheduling**: Can schedule simple task sets
- **Empty Schedule Handling**: Gracefully handles empty inputs
- **Constraint Satisfaction**: Properly handles scheduling constraints
- **Fallback Mechanism**: Falls back gracefully when optimization fails

### 2. Invariant Tests

Ensures business rules are maintained:

- No double-booking of time slots
- Schedules respect task deadlines
- Priority ordering is maintained
- Resource constraints are honored

### 3. Golden Scenario Tests

Regression testing with known scenarios:

- Validates against previously tested scheduling scenarios
- Ensures no degradation in scheduling quality
- Tests edge cases that have been encountered in production

### 4. Performance Tests

Validates system performance requirements:

- **Basic Load**: Average scheduling time < 5 seconds
- **Concurrent Requests**: Handles multiple simultaneous requests
- **Large Task Sets**: Scales to larger horizons (14+ days)

Performance thresholds:
- Average schedule time: < 5,000ms
- Maximum schedule time: < 30,000ms
- 95th percentile: < 10,000ms

### 5. Safety Tests

Validates ML safety mechanisms:

- **Safety Rails**: ML safety monitoring is functional
- **Violation Detection**: Detects and handles safety violations
- **Fallback Behavior**: Falls back safely when ML fails

### 6. Semantic Verification Tests

Validates API response correctness:

- **Basic Verification**: Responses are semantically correct
- **Issue Detection**: Detects problems in responses
- **Frontend Compatibility**: Ensures frontend can consume responses

### 7. Integration Tests

End-to-end system validation:

- **Full Pipeline**: Complete request-to-response flow
- **Component Integration**: All components work together
- **Real-world Scenarios**: Realistic usage patterns

### 8. Stress Tests

Edge cases and error recovery:

- **Memory Usage**: No memory leaks under load
- **Error Recovery**: Graceful error handling
- **Resource Limits**: Respects system resource constraints

## Performance Requirements

The acceptance gate enforces these performance requirements:

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Average Schedule Time | < 5 seconds | User experience requirement |
| Maximum Schedule Time | < 30 seconds | Prevents timeouts |
| 95th Percentile | < 10 seconds | Most requests are fast |
| Concurrent Requests | 3+ simultaneous | Multi-user support |
| Memory Usage | Stable under load | No memory leaks |

## Safety Requirements

Safety violations that cause acceptance gate failure:

- ML safety violations detected
- Constraint violations in schedules
- Semantic verification failures (errors)
- Integration test failures
- Performance regression > 50%

## Failure Handling

When the acceptance gate fails:

1. **Deployment is blocked** - No deployment to production
2. **Detailed report** generated with failure reasons
3. **Performance metrics** included for analysis
4. **Individual test results** provided for debugging

### Debugging Failed Tests

1. Check the acceptance gate report for specific failures
2. Run individual test categories locally:
   ```bash
   python -m app.scheduler.testing.test_invariants
   python -m app.scheduler.testing.test_golden_schedules
   ```
3. Use performance profiling for slow tests
4. Check logs for detailed error messages

## Configuration

The acceptance gate can be configured through environment variables:

```bash
# Performance thresholds (milliseconds)
ACCEPTANCE_GATE_MAX_SCHEDULE_TIME=30000
ACCEPTANCE_GATE_AVG_SCHEDULE_TIME=5000

# Test configuration
ACCEPTANCE_GATE_GOLDEN_TEST_LIMIT=10
ACCEPTANCE_GATE_PERFORMANCE_RUNS=5

# CI configuration
CI_ARTIFACTS_DIR=artifacts
PYTHONPATH=/path/to/backend
```

## Output Format

The acceptance gate produces:

### Console Output
```
🚀 Starting Scheduler Acceptance Gate...

Running core functionality tests...
✅ core_basic_scheduling (1250ms)
✅ core_empty_schedule (850ms)
...

Overall Result: ✅ PASSED
- Total Tests: 24
- Passed: 24
- Failed: 0
- Success Rate: 100.0%
```

### JSON Results
```json
{
  "overall_passed": true,
  "total_tests": 24,
  "passed_tests": 24,
  "failed_tests": 0,
  "performance_metrics": {
    "avg_schedule_time_ms": 2150.0,
    "max_schedule_time_ms": 8900.0,
    "p95_schedule_time_ms": 5200.0
  },
  "safety_metrics": {
    "safety_violations": 0,
    "verification_issues": 0
  }
}
```

## Best Practices

### For Developers

1. **Run locally** before committing scheduler changes
2. **Fix failures immediately** - don't accumulate technical debt
3. **Monitor performance trends** - watch for gradual degradation
4. **Add golden tests** for new edge cases discovered

### For CI/CD

1. **Block deployment** on acceptance gate failure
2. **Archive test results** for trend analysis
3. **Alert on performance regression** > 20%
4. **Generate detailed reports** for failed deployments

### For Monitoring

1. **Track acceptance gate trends** over time
2. **Monitor performance metrics** in production
3. **Correlate failures** with recent changes
4. **Set up alerts** for repeated failures

## Integration with PulsePlan

The acceptance gate integrates with:

- **GitHub Actions** - Automated CI/CD testing
- **Scheduler Service** - Core scheduling validation
- **Safety Systems** - ML safety monitoring
- **Semantic Verification** - API correctness
- **Performance Monitoring** - Real-time metrics
- **Error Tracking** - Failure analysis

## Future Enhancements

Planned improvements:

1. **Historical Trending** - Track performance over time
2. **A/B Testing** - Compare scheduling algorithms
3. **Load Testing** - Higher concurrent user simulation
4. **Chaos Engineering** - Failure injection testing
5. **Production Validation** - Post-deployment verification

## Support

For issues with the acceptance gate:

1. Check the [troubleshooting guide](TROUBLESHOOTING.md)
2. Review test logs and error messages
3. Run individual components in isolation
4. Contact the scheduling team for complex issues

---

The acceptance gate ensures that PulsePlan's scheduling system maintains high quality, performance, and reliability standards throughout development and deployment.