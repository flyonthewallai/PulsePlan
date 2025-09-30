#!/usr/bin/env python3
"""
Scheduler Testing Runner

Provides a simple interface to run all scheduler tests including:
- Invariant checking
- Golden test scenarios
- Performance benchmarks
- Stability testing

Usage:
    python run_tests.py [options]

Options:
    --fast: Run only fast tests
    --full: Run complete test suite including slow tests
    --golden: Run only golden test scenarios
    --performance: Run only performance benchmarks
    --stability: Run only stability tests
    --invariants: Run only invariant tests
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import testing modules
try:
    from ..core.service import SchedulerService
    from .fixtures import create_edge_case_scenarios, create_stress_test_scenario
    from .golden_tests import GoldenTestRunner, create_basic_scenarios
    from .invariants import check_invariants
    from .performance import (
        PerformanceBenchmark,
        StabilityTester,
        create_benchmark_scenarios,
    )
except ImportError as e:
    logger.error(f"Failed to import testing modules: {e}")
    sys.exit(1)


class TestRunner:
    """Orchestrates scheduler testing across all test types."""

    def __init__(self, scheduler_service=None):
        """Initialize test runner with optional scheduler service."""
        self.scheduler_service = scheduler_service or SchedulerService()
        self.results = {}

    async def run_invariant_tests(self) -> Dict[str, Any]:
        """Run invariant checking tests."""
        logger.info("🔍 Running invariant tests...")

        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

        try:
            # Test 1: Empty schedule
            from ..core.domain import ScheduleSolution
            empty_solution = ScheduleSolution(feasible=True, blocks=[])

            from .fixtures import create_test_preferences
            result = check_invariants(
                solution=empty_solution,
                tasks=[],
                busy_events=[],
                preferences=create_test_preferences(),
                strict=False
            )

            results["total_tests"] += 1
            if result.passed:
                results["passed"] += 1
                logger.info("✓ Empty schedule invariants passed")
            else:
                results["failed"] += 1
                results["errors"].extend(result.violations)

            # Test 2: Basic validity checks
            # Add more invariant tests here as needed

        except Exception as e:
            results["errors"].append(f"Invariant test execution failed: {str(e)}")
            results["failed"] += 1

        logger.info(f"Invariant tests: {results['passed']}/{results['total_tests']} passed")
        return results

    async def run_golden_tests(self, test_limit: int = None) -> Dict[str, Any]:
        """Run golden test scenarios."""
        logger.info("🏆 Running golden test scenarios...")

        try:
            runner = GoldenTestRunner(
                scheduler_service=self.scheduler_service,
                performance_budget_ms=10000
            )

            # Load scenarios
            scenarios = create_basic_scenarios()
            if runner.fixtures_dir.exists():
                file_scenarios = runner.load_all_scenarios()
                scenarios.extend(file_scenarios)

            # Limit for fast testing
            if test_limit:
                scenarios = scenarios[:test_limit]

            results = await runner.run_all_scenarios()

            summary = {
                "total_scenarios": len(results),
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed),
                "average_time_ms": sum(r.execution_time_ms for r in results) / len(results) if results else 0,
                "within_budget": sum(1 for r in results if r.performance_within_bounds),
                "details": [
                    {
                        "name": r.scenario_name,
                        "passed": r.passed,
                        "time_ms": r.execution_time_ms,
                        "errors": r.errors
                    }
                    for r in results
                ]
            }

            logger.info(f"Golden tests: {summary['passed']}/{summary['total_scenarios']} passed")
            return summary

        except Exception as e:
            logger.error(f"Golden tests failed: {e}")
            return {
                "total_scenarios": 0,
                "passed": 0,
                "failed": 1,
                "errors": [str(e)]
            }

    async def run_performance_tests(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run performance benchmarks."""
        logger.info("⚡ Running performance benchmarks...")

        try:
            benchmark = PerformanceBenchmark(
                scheduler_service=self.scheduler_service,
                performance_budget_ms=5000 if quick_mode else 15000
            )

            scenarios = create_benchmark_scenarios()

            # Choose test parameters based on mode
            if quick_mode:
                task_counts = [5, 10]
                runs = 2
                test_scenarios = ["simple_tasks"]
            else:
                task_counts = [5, 10, 15, 20]
                runs = 5
                test_scenarios = ["simple_tasks", "complex_constraints"]

            all_results = {}
            summary = {
                "scenarios_tested": 0,
                "average_performance_ms": 0,
                "p95_performance_ms": 0,
                "within_budget_ratio": 0,
                "details": {}
            }

            total_times = []
            within_budget_count = 0
            total_benchmarks = 0

            for scenario_name in test_scenarios:
                if scenario_name in scenarios:
                    logger.info(f"Benchmarking {scenario_name}...")

                    results = await benchmark.benchmark_scenario(
                        scenario_name=scenario_name,
                        task_generator=scenarios[scenario_name],
                        n_tasks_list=task_counts,
                        n_runs=runs
                    )

                    all_results[scenario_name] = results
                    summary["details"][scenario_name] = {}

                    for n_tasks, result in results.items():
                        total_times.append(result.avg_time_ms)
                        if result.within_budget:
                            within_budget_count += 1
                        total_benchmarks += 1

                        summary["details"][scenario_name][n_tasks] = {
                            "avg_time_ms": result.avg_time_ms,
                            "p95_time_ms": result.p95_time_ms,
                            "success_rate": result.success_rate,
                            "within_budget": result.within_budget
                        }

                    summary["scenarios_tested"] += 1

            # Calculate overall metrics
            if total_times:
                summary["average_performance_ms"] = sum(total_times) / len(total_times)
                summary["p95_performance_ms"] = sorted(total_times)[int(len(total_times) * 0.95)]

            if total_benchmarks > 0:
                summary["within_budget_ratio"] = within_budget_count / total_benchmarks

            logger.info(
                f"Performance tests: avg {summary['average_performance_ms']:.1f}ms, "
                f"p95 {summary['p95_performance_ms']:.1f}ms"
            )

            return summary

        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            return {"error": str(e)}

    async def run_stability_tests(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run stability and determinism tests."""
        logger.info("🔒 Running stability tests...")

        try:
            tester = StabilityTester(
                scheduler_service=self.scheduler_service,
                random_seed=42
            )

            # Adjust parameters based on mode
            if quick_mode:
                n_scenarios = 20
                max_tasks = 10
                determinism_runs = 2
            else:
                n_scenarios = 100
                max_tasks = 20
                determinism_runs = 3

            result = await tester.run_stability_test(
                n_scenarios=n_scenarios,
                max_tasks=max_tasks,
                determinism_runs=determinism_runs
            )

            summary = {
                "total_scenarios": result.total_scenarios,
                "successful_runs": result.successful_runs,
                "success_rate": result.successful_runs / result.total_scenarios if result.total_scenarios > 0 else 0,
                "average_performance_ms": result.avg_performance_ms,
                "stability_score": result.stability_score,
                "determinism_score": result.determinism_score,
                "invariant_violations": result.invariant_violations,
                "performance_degradation": result.performance_degradation
            }

            logger.info(
                f"Stability tests: score {summary['stability_score']:.3f}, "
                f"success rate {summary['success_rate']:.1%}"
            )

            return summary

        except Exception as e:
            logger.error(f"Stability tests failed: {e}")
            return {"error": str(e)}

    async def run_full_suite(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run complete test suite."""
        logger.info("🚀 Running full scheduler test suite...")

        start_time = datetime.now()

        # Run all test categories
        results = {
            "timestamp": start_time.isoformat(),
            "mode": "quick" if quick_mode else "full",
            "invariant_tests": await self.run_invariant_tests(),
            "golden_tests": await self.run_golden_tests(test_limit=3 if quick_mode else None),
            "performance_tests": await self.run_performance_tests(quick_mode=quick_mode),
            "stability_tests": await self.run_stability_tests(quick_mode=quick_mode)
        }

        end_time = datetime.now()
        results["total_time_seconds"] = (end_time - start_time).total_seconds()

        # Calculate overall summary
        golden_passed = results["golden_tests"].get("passed", 0)
        golden_total = results["golden_tests"].get("total_scenarios", 0)
        stability_score = results["stability_tests"].get("stability_score", 0)
        avg_performance = results["performance_tests"].get("average_performance_ms", 0)

        results["summary"] = {
            "overall_health": "GOOD" if golden_passed == golden_total and stability_score > 0.8 else "NEEDS_ATTENTION",
            "golden_test_success_rate": golden_passed / golden_total if golden_total > 0 else 0,
            "stability_score": stability_score,
            "average_performance_ms": avg_performance,
            "total_runtime_seconds": results["total_time_seconds"]
        }

        logger.info(f"🎉 Test suite completed in {results['total_time_seconds']:.1f}s")
        logger.info(f"Overall health: {results['summary']['overall_health']}")

        return results

    def save_results(self, results: Dict[str, Any], output_file: str = None):
        """Save test results to JSON file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"scheduler_test_results_{timestamp}.json"

        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")


async def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Scheduler Testing Runner")
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument("--full", action="store_true", help="Run complete test suite")
    parser.add_argument("--golden", action="store_true", help="Run only golden test scenarios")
    parser.add_argument("--performance", action="store_true", help="Run only performance benchmarks")
    parser.add_argument("--stability", action="store_true", help="Run only stability tests")
    parser.add_argument("--invariants", action="store_true", help="Run only invariant tests")
    parser.add_argument("--output", "-o", help="Output file for results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    runner = TestRunner()

    try:
        if args.invariants:
            results = await runner.run_invariant_tests()
        elif args.golden:
            results = await runner.run_golden_tests()
        elif args.performance:
            results = await runner.run_performance_tests(quick_mode=args.fast)
        elif args.stability:
            results = await runner.run_stability_tests(quick_mode=args.fast)
        else:
            # Default to full suite
            results = await runner.run_full_suite(quick_mode=args.fast)

        # Save results if requested
        if args.output:
            runner.save_results(results, args.output)

        # Print summary
        print("\n" + "="*60)
        print("SCHEDULER TEST RESULTS SUMMARY")
        print("="*60)

        if "summary" in results:
            summary = results["summary"]
            print(f"Overall Health: {summary['overall_health']}")
            print(f"Golden Test Success: {summary['golden_test_success_rate']:.1%}")
            print(f"Stability Score: {summary['stability_score']:.3f}")
            print(f"Avg Performance: {summary['average_performance_ms']:.1f}ms")
            print(f"Total Runtime: {summary['total_runtime_seconds']:.1f}s")

        print("="*60)

        # Exit with appropriate code
        if "summary" in results:
            exit_code = 0 if results["summary"]["overall_health"] == "GOOD" else 1
        else:
            exit_code = 0

        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test run failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
