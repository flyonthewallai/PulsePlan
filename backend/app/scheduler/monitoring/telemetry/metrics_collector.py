"""
Metrics collection for scheduler telemetry.

Provides counters, gauges, histograms, and timers for
comprehensive performance monitoring.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .models import MetricPoint

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics for the scheduler.

    Provides counters, gauges, histograms, and timers for
    comprehensive performance monitoring.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = []
        self.counters = {}
        self.gauges = {}
        self.histograms = {}

        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

    def counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            New counter value
        """
        key = self._make_key(name, tags or {})
        self.counters[key] = self.counters.get(key, 0) + 1

        metric = MetricPoint(
            name=name,
            value=self.counters[key],
            tags=tags or {},
            unit="count"
        )
        self.metrics.append(metric)

        return self.counters[key]

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.

        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags
        """
        key = self._make_key(name, tags or {})
        self.gauges[key] = value

        metric = MetricPoint(
            name=name,
            value=value,
            tags=tags or {},
            unit="gauge"
        )
        self.metrics.append(metric)

    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a histogram value.

        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags
        """
        key = self._make_key(name, tags or {})
        if key not in self.histograms:
            self.histograms[key] = []

        self.histograms[key].append(value)

        # Keep only recent values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]

        metric = MetricPoint(
            name=name,
            value=value,
            tags=tags or {},
            unit="histogram"
        )
        self.metrics.append(metric)

    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Create a context manager timer.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Context manager that times the enclosed block
        """
        return TimerContext(self, name, tags or {})

    def _make_key(self, name: str, tags: Dict[str, str]) -> str:
        """Make cache key from name and tags."""
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}:{tag_str}" if tag_str else name

    def get_metrics(self, since: Optional[datetime] = None) -> List[MetricPoint]:
        """
        Get metrics since specified time.

        Args:
            since: Only return metrics after this time

        Returns:
            List of metric points
        """
        if since is None:
            return self.metrics.copy()

        return [m for m in self.metrics if m.timestamp >= since]

    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        key = self._make_key(name, tags or {})
        values = self.histograms.get(key, [])

        if not values:
            return {}

        import numpy as np
        return {
            'count': len(values),
            'mean': np.mean(values),
            'median': np.median(values),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99),
            'min': np.min(values),
            'max': np.max(values)
        }

    def _start_cleanup_task(self):
        """Start background cleanup task."""
        async def cleanup():
            while True:
                try:
                    await asyncio.sleep(300)  # 5 minutes
                    await self._cleanup_old_metrics()
                except Exception as e:
                    logger.error(f"Metrics cleanup failed: {e}")

        try:
            if asyncio.get_event_loop().is_running():
                self._cleanup_task = asyncio.create_task(cleanup())
        except RuntimeError:
            # No event loop running
            pass

    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Clean metrics list
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        # Clean histograms
        for key in list(self.histograms.keys()):
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-500:]  # Keep recent half

        logger.debug(f"Cleaned up metrics: {len(self.metrics)} points remaining")


class TimerContext:
    """Context manager for timing operations."""

    def __init__(self, collector: MetricsCollector, name: str, tags: Dict[str, str]):
        """Initialize timer context."""
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record metric."""
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.histogram(f"{self.name}.duration", duration_ms, self.tags)
            self.collector.histogram(f"{self.name}.duration_ms", duration_ms, self.tags)
