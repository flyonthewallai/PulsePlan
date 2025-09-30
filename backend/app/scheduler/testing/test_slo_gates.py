"""
Test suite for SLO gates and performance monitoring.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.scheduler.performance import (
    SLOGate, SLOLevel, SLOConfig, CoarseningStrategy,
    PerformanceMetrics, SLOViolationError
)
from app.scheduler.domain import ScheduleSolution, ScheduleBlock
from app.scheduler.io.dto import ScheduleRequest


class TestSLOGate:
    """Test SLO gate functionality."""

    @pytest.fixture
    def slo_config(self):
        """Test SLO configuration."""
        return SLOConfig(
            p50_latency_ms=1000,      # Strict for testing
            p95_latency_ms=3000,
            p99_latency_ms=5000,
            max_concurrent_requests=2,  # Low for testing
            min_feasibility_rate=0.8,
            latency_window_minutes=1,   # Short window for testing
            quality_window_minutes=1
        )

    @pytest.fixture
    def slo_gate(self, slo_config):
        """Create SLO gate with test configuration."""
        return SLOGate(slo_config)

    @pytest.fixture
    def sample_request(self):
        """Create sample schedule request."""
        return ScheduleRequest(
            user_id="test_user",
            horizon_days=3,
            job_id="test_job"
        )

    @pytest.fixture
    def sample_solution(self):
        """Create sample schedule solution."""
        return ScheduleSolution(
            feasible=True,
            blocks=[
                ScheduleBlock(
                    task_id="task1",
                    start=datetime.now(),
                    end=datetime.now() + timedelta(hours=1)
                )
            ],
            objective_value=1.0,
            solve_time_ms=500
        )

    def test_slo_gate_initialization(self, slo_gate):
        """Test SLO gate initializes correctly."""
        assert slo_gate.current_status.level == SLOLevel.GREEN
        assert slo_gate.consecutive_violations == 0
        assert len(slo_gate.metrics_history) == 0
        assert len(slo_gate.active_requests) == 0

    @pytest.mark.asyncio
    async def test_request_lifecycle_green_status(self, slo_gate, sample_request, sample_solution):
        """Test normal request lifecycle with green SLO status."""
        # Check SLO before request
        slo_context = await slo_gate.check_slo_before_request(sample_request)

        assert slo_context['slo_level'] == SLOLevel.GREEN
        assert len(slo_context['coarsening_params']) == 0
        assert not slo_context['auto_coarsening_enabled']

        request_id = slo_context['request_id']
        assert request_id in slo_gate.active_requests

        # Record completion
        await slo_gate.record_request_completion(
            request_id, sample_solution, sample_request
        )

        assert request_id not in slo_gate.active_requests
        assert len(slo_gate.metrics_history) == 1

        metrics = slo_gate.metrics_history[0]
        assert metrics.feasible is True
        assert metrics.blocks_scheduled == 1
        assert metrics.error_occurred is False

    @pytest.mark.asyncio
    async def test_high_latency_triggers_yellow_status(self, slo_gate, sample_request, sample_solution):
        """Test that high latency triggers yellow SLO status."""
        # Simulate high latency by manually adding metrics
        base_time = datetime.now()

        # Add several high-latency metrics
        for i in range(5):
            high_latency_metrics = PerformanceMetrics(
                timestamp=base_time + timedelta(seconds=i),
                latency_ms=4000,  # Above p95 threshold (3000ms)
                memory_mb=100,
                cpu_percent=20,
                concurrent_requests=1,
                feasible=True,
                blocks_scheduled=1,
                total_tasks=1
            )
            slo_gate.metrics_history.append(high_latency_metrics)

        # Update SLO status
        await slo_gate._update_slo_status()

        assert slo_gate.current_status.level in [SLOLevel.YELLOW, SLOLevel.ORANGE]
        assert len(slo_gate.current_status.violations) > 0
        assert slo_gate.current_status.auto_coarsening_enabled is True

    @pytest.mark.asyncio
    async def test_low_feasibility_triggers_violations(self, slo_gate, sample_request):
        """Test that low feasibility rate triggers violations."""
        base_time = datetime.now()

        # Add metrics with low feasibility
        for i in range(10):
            infeasible_metrics = PerformanceMetrics(
                timestamp=base_time + timedelta(seconds=i),
                latency_ms=1000,  # Normal latency
                memory_mb=100,
                cpu_percent=20,
                concurrent_requests=1,
                feasible=i < 3,  # Only 30% feasible (below 80% threshold)
                blocks_scheduled=0 if i >= 3 else 1,
                total_tasks=1
            )
            slo_gate.metrics_history.append(infeasible_metrics)

        await slo_gate._update_slo_status()

        assert slo_gate.current_status.level != SLOLevel.GREEN
        violations = [v for v in slo_gate.current_status.violations if 'feasibility' in v.lower()]
        assert len(violations) > 0

    @pytest.mark.asyncio
    async def test_coarsening_parameters_yellow_level(self, slo_gate):
        """Test coarsening parameters for yellow SLO level."""
        # Manually set yellow status
        slo_gate.current_status.level = SLOLevel.YELLOW
        slo_gate.current_status.recommendations = [
            CoarseningStrategy.LIMIT_ITERATIONS,
            CoarseningStrategy.DISABLE_LEARNING
        ]
        slo_gate.consecutive_violations = 1

        params = slo_gate._get_coarsening_parameters()

        assert 'max_solve_time_seconds' in params
        assert params['max_solve_time_seconds'] < 10  # Reduced from default
        assert params.get('disable_ml_features', False) is True

    @pytest.mark.asyncio
    async def test_coarsening_parameters_red_level(self, slo_gate):
        """Test aggressive coarsening for red SLO level."""
        # Manually set red status
        slo_gate.current_status.level = SLOLevel.RED
        slo_gate.current_status.recommendations = [
            CoarseningStrategy.SIMPLIFY_CONSTRAINTS,
            CoarseningStrategy.INCREASE_GRANULARITY,
            CoarseningStrategy.REDUCE_HORIZON,
            CoarseningStrategy.LIMIT_ITERATIONS,
            CoarseningStrategy.DISABLE_LEARNING
        ]
        slo_gate.consecutive_violations = 3

        params = slo_gate._get_coarsening_parameters()

        assert 'disable_soft_constraints' in params
        assert 'force_granularity_minutes' in params
        assert 'max_horizon_days' in params
        assert 'max_solve_time_seconds' in params
        assert 'disable_ml_features' in params

        assert params['force_granularity_minutes'] == 60
        assert params['max_horizon_days'] <= 3
        assert params['disable_soft_constraints'] is True

    @pytest.mark.asyncio
    async def test_concurrent_request_limit_rejection(self, slo_gate, sample_request):
        """Test that too many concurrent requests are rejected."""
        # Manually set red status and add active requests
        slo_gate.current_status.level = SLOLevel.RED
        slo_gate.active_requests = {
            'req1': 1000,
            'req2': 1001,
            'req3': 1002  # Exceeds limit of 2
        }

        with pytest.raises(SLOViolationError):
            await slo_gate.check_slo_before_request(sample_request)

    @pytest.mark.asyncio
    async def test_error_recording(self, slo_gate, sample_request):
        """Test recording of request errors."""
        slo_context = await slo_gate.check_slo_before_request(sample_request)
        request_id = slo_context['request_id']

        error = Exception("Test error")
        await slo_gate.record_request_completion(
            request_id, None, sample_request, error
        )

        assert len(slo_gate.metrics_history) == 1
        metrics = slo_gate.metrics_history[0]
        assert metrics.error_occurred is True
        assert metrics.error_type == "Exception"
        assert metrics.feasible is False

    def test_health_status_reporting(self, slo_gate):
        """Test health status reporting."""
        # Add some sample metrics
        base_time = datetime.now()
        for i in range(3):
            metrics = PerformanceMetrics(
                timestamp=base_time + timedelta(seconds=i),
                latency_ms=1000 + i * 500,
                memory_mb=100,
                cpu_percent=20,
                concurrent_requests=1,
                feasible=True,
                blocks_scheduled=1,
                total_tasks=1
            )
            slo_gate.metrics_history.append(metrics)

        health_status = slo_gate.get_health_status()

        assert 'slo_level' in health_status
        assert 'violations' in health_status
        assert 'auto_coarsening_enabled' in health_status
        assert 'metrics' in health_status
        assert 'recommendations' in health_status

        assert health_status['metrics']['metrics_collected'] == 3

    def test_windowed_metrics_filtering(self, slo_gate):
        """Test that windowed metrics correctly filter by time."""
        base_time = datetime.now()

        # Add metrics over a longer time span
        for i in range(10):
            metrics = PerformanceMetrics(
                timestamp=base_time - timedelta(minutes=i),  # Going backwards
                latency_ms=1000,
                memory_mb=100,
                cpu_percent=20,
                concurrent_requests=1,
                feasible=True,
                blocks_scheduled=1,
                total_tasks=1
            )
            slo_gate.metrics_history.append(metrics)

        # Get metrics within 5-minute window
        window_metrics = slo_gate._get_windowed_metrics(
            base_time, timedelta(minutes=5)
        )

        # Should only get metrics from last 5 minutes
        assert len(window_metrics) == 6  # 0, 1, 2, 3, 4, 5 minutes ago

    @pytest.mark.asyncio
    async def test_slo_status_level_transitions(self, slo_gate):
        """Test SLO level transitions based on violations."""
        # Start with green (no violations)
        await slo_gate._update_slo_status()
        assert slo_gate.current_status.level == SLOLevel.GREEN

        # Add one violation -> should go to yellow
        base_time = datetime.now()
        high_latency_metrics = PerformanceMetrics(
            timestamp=base_time,
            latency_ms=4000,  # Above p95 threshold
            memory_mb=100,
            cpu_percent=20,
            concurrent_requests=1,
            feasible=True,
            blocks_scheduled=1,
            total_tasks=1
        )
        slo_gate.metrics_history.append(high_latency_metrics)

        await slo_gate._update_slo_status()
        assert slo_gate.current_status.level in [SLOLevel.YELLOW, SLOLevel.ORANGE]
        assert slo_gate.consecutive_violations > 0