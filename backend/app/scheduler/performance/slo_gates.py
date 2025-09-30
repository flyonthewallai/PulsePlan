"""
Service Level Objective (SLO) gates and performance monitoring for the scheduler.

Implements performance monitoring, SLO breach detection, and automatic
algorithm coarsening to maintain scheduling responsiveness under load.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import deque

from ..core.domain import ScheduleSolution
from ..io.dto import ScheduleRequest
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class SLOLevel(Enum):
    """SLO violation severity levels."""
    GREEN = "green"      # All SLOs met
    YELLOW = "yellow"    # Minor violations, enable coarsening
    ORANGE = "orange"    # Moderate violations, aggressive coarsening
    RED = "red"          # Severe violations, emergency fallback


class CoarseningStrategy(Enum):
    """Available coarsening strategies."""
    REDUCE_HORIZON = "reduce_horizon"        # Shorten planning horizon
    INCREASE_GRANULARITY = "increase_granularity"  # Use 60-min slots vs 30-min
    SIMPLIFY_CONSTRAINTS = "simplify_constraints"   # Relax soft constraints
    LIMIT_ITERATIONS = "limit_iterations"    # Cap solver iterations
    DISABLE_LEARNING = "disable_learning"    # Skip ML features


@dataclass
class SLOConfig:
    """SLO configuration and thresholds."""
    # Latency thresholds (milliseconds)
    p50_latency_ms: int = 2000      # 2s for median response
    p95_latency_ms: int = 8000      # 8s for 95th percentile
    p99_latency_ms: int = 15000     # 15s for 99th percentile

    # Throughput thresholds
    max_concurrent_requests: int = 10
    requests_per_minute: int = 100

    # Resource thresholds
    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0

    # Quality thresholds
    min_feasibility_rate: float = 0.95   # 95% of requests should be feasible
    min_blocks_scheduled_ratio: float = 0.8  # 80% of tasks should be scheduled

    # Monitoring windows
    latency_window_minutes: int = 5
    throughput_window_minutes: int = 1
    quality_window_minutes: int = 10


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics."""
    timestamp: datetime
    latency_ms: int
    memory_mb: float
    cpu_percent: float
    concurrent_requests: int
    feasible: bool
    blocks_scheduled: int
    total_tasks: int
    error_occurred: bool = False
    error_type: Optional[str] = None


@dataclass
class SLOStatus:
    """Current SLO status and recommendations."""
    level: SLOLevel
    violations: List[str] = field(default_factory=list)
    recommendations: List[CoarseningStrategy] = field(default_factory=list)
    current_latency_p95: float = 0.0
    current_throughput: float = 0.0
    current_feasibility_rate: float = 0.0
    auto_coarsening_enabled: bool = False


class SLOGate:
    """
    SLO monitoring and automatic coarsening gate.

    Monitors scheduling performance in real-time and automatically
    applies coarsening strategies when SLOs are breached.
    """

    def __init__(self, config: SLOConfig = None):
        """Initialize SLO gate with configuration."""
        self.config = config or SLOConfig()
        self.timezone_manager = get_timezone_manager()

        # Performance tracking
        self.metrics_history: deque = deque(maxlen=1000)
        self.active_requests: Dict[str, float] = {}  # request_id -> start_time

        # SLO status
        self.current_status = SLOStatus(level=SLOLevel.GREEN)
        self.consecutive_violations = 0
        self.last_coarsening_applied = None

        # Coarsening strategies (ordered by severity)
        self.coarsening_strategies = {
            SLOLevel.YELLOW: [
                CoarseningStrategy.LIMIT_ITERATIONS,
                CoarseningStrategy.DISABLE_LEARNING
            ],
            SLOLevel.ORANGE: [
                CoarseningStrategy.INCREASE_GRANULARITY,
                CoarseningStrategy.REDUCE_HORIZON,
                CoarseningStrategy.LIMIT_ITERATIONS,
                CoarseningStrategy.DISABLE_LEARNING
            ],
            SLOLevel.RED: [
                CoarseningStrategy.SIMPLIFY_CONSTRAINTS,
                CoarseningStrategy.INCREASE_GRANULARITY,
                CoarseningStrategy.REDUCE_HORIZON,
                CoarseningStrategy.LIMIT_ITERATIONS,
                CoarseningStrategy.DISABLE_LEARNING
            ]
        }

    async def check_slo_before_request(self, request: ScheduleRequest) -> Dict[str, Any]:
        """
        Check SLO status before processing a request.

        Returns coarsening parameters to apply based on current SLO status.
        """
        # Update SLO status
        await self._update_slo_status()

        # Check if we should reject the request due to overload
        if self.current_status.level == SLOLevel.RED:
            concurrent_count = len(self.active_requests)
            if concurrent_count >= self.config.max_concurrent_requests:
                raise SLOViolationError(
                    f"Too many concurrent requests ({concurrent_count}), rejecting"
                )

        # Track request start
        request_id = request.job_id or f"req_{int(time.time() * 1000)}"
        self.active_requests[request_id] = time.time()

        # Get coarsening parameters
        coarsening_params = self._get_coarsening_parameters()

        logger.info(
            f"SLO check for request {request_id}: "
            f"level={self.current_status.level.value}, "
            f"coarsening={len(coarsening_params) > 0}"
        )

        return {
            'request_id': request_id,
            'slo_level': self.current_status.level,
            'coarsening_params': coarsening_params,
            'auto_coarsening_enabled': self.current_status.auto_coarsening_enabled
        }

    async def record_request_completion(
        self,
        request_id: str,
        solution: ScheduleSolution,
        request: ScheduleRequest,
        error: Optional[Exception] = None
    ):
        """Record completion metrics for a request."""
        end_time = time.time()
        start_time = self.active_requests.pop(request_id, end_time)
        latency_ms = int((end_time - start_time) * 1000)

        # Collect system metrics (simplified - would use psutil in production)
        memory_mb = 100.0  # Placeholder
        cpu_percent = 20.0  # Placeholder

        # Calculate quality metrics
        total_tasks = len(request.task_ids) if hasattr(request, 'task_ids') else 0
        blocks_scheduled = len(solution.blocks) if solution else 0

        # Record metrics
        metrics = PerformanceMetrics(
            timestamp=self.timezone_manager.ensure_timezone_aware(datetime.now()),
            latency_ms=latency_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            concurrent_requests=len(self.active_requests),
            feasible=solution.feasible if solution else False,
            blocks_scheduled=blocks_scheduled,
            total_tasks=total_tasks,
            error_occurred=error is not None,
            error_type=type(error).__name__ if error else None
        )

        self.metrics_history.append(metrics)

        logger.debug(
            f"Recorded metrics for {request_id}: "
            f"latency={latency_ms}ms, feasible={metrics.feasible}, "
            f"blocks={blocks_scheduled}/{total_tasks}"
        )

    async def _update_slo_status(self):
        """Update current SLO status based on recent metrics."""
        if not self.metrics_history:
            return

        now = self.timezone_manager.ensure_timezone_aware(datetime.now())

        # Calculate windowed metrics
        latency_metrics = self._get_windowed_metrics(
            now, timedelta(minutes=self.config.latency_window_minutes)
        )

        quality_metrics = self._get_windowed_metrics(
            now, timedelta(minutes=self.config.quality_window_minutes)
        )

        # Calculate percentiles
        if latency_metrics:
            latencies = [m.latency_ms for m in latency_metrics]
            latencies.sort()
            n = len(latencies)
            p50 = latencies[int(n * 0.5)] if n > 0 else 0
            p95 = latencies[int(n * 0.95)] if n > 0 else 0
            p99 = latencies[int(n * 0.99)] if n > 0 else 0
        else:
            p50 = p95 = p99 = 0

        # Calculate quality metrics
        if quality_metrics:
            feasible_count = sum(1 for m in quality_metrics if m.feasible)
            feasibility_rate = feasible_count / len(quality_metrics)

            total_blocks = sum(m.blocks_scheduled for m in quality_metrics)
            total_tasks = sum(m.total_tasks for m in quality_metrics)
            blocks_ratio = total_blocks / max(1, total_tasks)
        else:
            feasibility_rate = 1.0
            blocks_ratio = 1.0

        # Determine SLO level
        violations = []

        if p95 > self.config.p95_latency_ms:
            violations.append(f"P95 latency: {p95}ms > {self.config.p95_latency_ms}ms")

        if p99 > self.config.p99_latency_ms:
            violations.append(f"P99 latency: {p99}ms > {self.config.p99_latency_ms}ms")

        if feasibility_rate < self.config.min_feasibility_rate:
            violations.append(f"Feasibility rate: {feasibility_rate:.2f} < {self.config.min_feasibility_rate:.2f}")

        if blocks_ratio < self.config.min_blocks_scheduled_ratio:
            violations.append(f"Blocks scheduled ratio: {blocks_ratio:.2f} < {self.config.min_blocks_scheduled_ratio:.2f}")

        # Determine level based on severity
        if len(violations) == 0:
            level = SLOLevel.GREEN
            self.consecutive_violations = 0
        elif len(violations) <= 1 and p99 <= self.config.p99_latency_ms:
            level = SLOLevel.YELLOW
            self.consecutive_violations += 1
        elif len(violations) <= 2 or p99 > self.config.p99_latency_ms:
            level = SLOLevel.ORANGE
            self.consecutive_violations += 1
        else:
            level = SLOLevel.RED
            self.consecutive_violations += 1

        # Update status
        old_level = self.current_status.level
        self.current_status = SLOStatus(
            level=level,
            violations=violations,
            recommendations=self.coarsening_strategies.get(level, []),
            current_latency_p95=p95,
            current_throughput=len(latency_metrics),
            current_feasibility_rate=feasibility_rate,
            auto_coarsening_enabled=level != SLOLevel.GREEN
        )

        # Log level changes
        if old_level != level:
            logger.warning(
                f"SLO level changed: {old_level.value} -> {level.value} "
                f"(violations: {len(violations)}, consecutive: {self.consecutive_violations})"
            )

    def _get_windowed_metrics(
        self, now: datetime, window: timedelta
    ) -> List[PerformanceMetrics]:
        """Get metrics within the specified time window."""
        cutoff = now - window
        return [
            m for m in self.metrics_history
            if m.timestamp >= cutoff
        ]

    def _get_coarsening_parameters(self) -> Dict[str, Any]:
        """Get coarsening parameters based on current SLO level."""
        if self.current_status.level == SLOLevel.GREEN:
            return {}

        params = {}
        strategies = self.current_status.recommendations

        if CoarseningStrategy.REDUCE_HORIZON in strategies:
            # Reduce horizon from default days to emergency minimum
            params['max_horizon_days'] = max(1, 3 - self.consecutive_violations)

        if CoarseningStrategy.INCREASE_GRANULARITY in strategies:
            # Use 60-minute slots instead of 30-minute
            params['force_granularity_minutes'] = 60

        if CoarseningStrategy.SIMPLIFY_CONSTRAINTS in strategies:
            # Disable soft constraints, focus on hard constraints only
            params['disable_soft_constraints'] = True
            params['disable_preference_optimization'] = True

        if CoarseningStrategy.LIMIT_ITERATIONS in strategies:
            # Reduce solver time limit
            severity_factor = min(4, self.consecutive_violations)
            params['max_solve_time_seconds'] = max(1, 10 - severity_factor * 2)

        if CoarseningStrategy.DISABLE_LEARNING in strategies:
            # Skip ML feature computation
            params['disable_ml_features'] = True
            params['disable_completion_prediction'] = True
            params['use_simple_utilities'] = True

        return params

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health and SLO status."""
        recent_metrics = self._get_windowed_metrics(
            self.timezone_manager.ensure_timezone_aware(datetime.now()),
            timedelta(minutes=5)
        )

        if recent_metrics:
            avg_latency = sum(m.latency_ms for m in recent_metrics) / len(recent_metrics)
            error_rate = sum(1 for m in recent_metrics if m.error_occurred) / len(recent_metrics)
        else:
            avg_latency = 0
            error_rate = 0

        return {
            'slo_level': self.current_status.level.value,
            'violations': self.current_status.violations,
            'consecutive_violations': self.consecutive_violations,
            'auto_coarsening_enabled': self.current_status.auto_coarsening_enabled,
            'recommendations': [s.value for s in self.current_status.recommendations],
            'metrics': {
                'current_latency_p95': self.current_status.current_latency_p95,
                'avg_latency_5min': avg_latency,
                'error_rate_5min': error_rate,
                'concurrent_requests': len(self.active_requests),
                'metrics_collected': len(self.metrics_history)
            }
        }


class SLOViolationError(Exception):
    """Raised when SLO violations prevent request processing."""
    pass


# Global SLO gate instance
_slo_gate = None

def get_slo_gate() -> SLOGate:
    """Get global SLO gate instance."""
    global _slo_gate
    if _slo_gate is None:
        _slo_gate = SLOGate()
    return _slo_gate


def configure_slo_gate(config: SLOConfig):
    """Configure global SLO gate with custom settings."""
    global _slo_gate
    _slo_gate = SLOGate(config)

