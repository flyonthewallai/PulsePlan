"""
Testing infrastructure for the scheduler subsystem.

Provides invariant checking, golden tests, performance benchmarks,
and stability testing for production-ready scheduling algorithms.
"""

from .fixtures import (
    create_test_availability,
    create_test_preferences,
    create_test_task,
)
from .golden_tests import GoldenTestRunner, load_test_scenario
from .invariants import ScheduleInvariantError, check_invariants
from .performance import PerformanceBenchmark, StabilityTester

__all__ = [
    'check_invariants',
    'ScheduleInvariantError',
    'GoldenTestRunner',
    'load_test_scenario',
    'PerformanceBenchmark',
    'StabilityTester',
    'create_test_task',
    'create_test_availability',
    'create_test_preferences'
]
