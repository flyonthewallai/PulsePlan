"""
Main telemetry module with factory functions.

Provides global access to telemetry components and convenience functions.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from .models import MetricPoint, TraceSpan
from .metrics_collector import MetricsCollector
from .distributed_tracer import DistributedTracer
from .scheduler_logger import SchedulerLogger
from .exporter import TelemetryExporter

logger = logging.getLogger(__name__)


# Global telemetry instances
_metrics_collector = MetricsCollector()
_tracer = DistributedTracer()
_scheduler_logger = SchedulerLogger()
_exporter = TelemetryExporter()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics_collector


def get_tracer() -> DistributedTracer:
    """Get global distributed tracer."""
    return _tracer


def get_scheduler_logger() -> SchedulerLogger:
    """Get global scheduler logger."""
    return _scheduler_logger


def get_exporter() -> TelemetryExporter:
    """Get global telemetry exporter."""
    return _exporter


# Convenience functions
async def emit_metrics(name: str, data: Dict[str, Any]):
    """
    Emit metrics for scheduler operation.

    Args:
        name: Metric name prefix
        data: Metric data
    """
    collector = get_metrics()

    for key, value in data.items():
        if isinstance(value, (int, float)):
            collector.gauge(f"{name}.{key}", value)
        elif isinstance(value, bool):
            collector.gauge(f"{name}.{key}", 1.0 if value else 0.0)


async def get_telemetry_health() -> Dict[str, Any]:
    """Get telemetry system health status."""
    collector = get_metrics()
    tracer = get_tracer()
    exporter = get_exporter()

    # Get recent metrics
    recent_metrics = collector.get_metrics(
        since=datetime.now() - timedelta(minutes=5)
    )

    # Get OTLP connection status
    connection_status = exporter.get_connection_status()

    return {
        'status': 'healthy',
        'metrics': {
            'total_collected': len(collector.metrics),
            'recent_metrics': len(recent_metrics),
            'active_counters': len(collector.counters),
            'active_gauges': len(collector.gauges),
            'active_histograms': len(collector.histograms)
        },
        'tracing': {
            'active_spans': len(tracer.active_spans),
            'completed_spans': len(tracer.completed_spans)
        },
        'export_queue': {
            'queued_items': len(exporter.export_queue),
            'export_enabled': exporter.export_config['enabled']
        },
        'opentelemetry': connection_status
    }
