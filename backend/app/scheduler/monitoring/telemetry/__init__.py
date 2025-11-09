"""
Telemetry and observability for the scheduler subsystem.

Provides comprehensive metrics, logging, tracing, and monitoring
for production deployment and performance analysis.

Integrates with Grafana Cloud via OpenTelemetry OTLP exporters when configured,
falls back to console logging for development.
"""

# Import models
from .models import MetricPoint, TraceSpan

# Import core components
from .metrics_collector import MetricsCollector, TimerContext
from .distributed_tracer import DistributedTracer
from .scheduler_logger import SchedulerLogger
from .exporter import TelemetryExporter

# Import decorators
from .decorators import trace_run, monitor_performance

# Import factory functions and utilities
from .telemetry import (
    get_metrics,
    get_tracer,
    get_scheduler_logger,
    get_exporter,
    emit_metrics,
    get_telemetry_health
)

# Re-export all public interfaces
__all__ = [
    # Models
    'MetricPoint',
    'TraceSpan',

    # Core components
    'MetricsCollector',
    'TimerContext',
    'DistributedTracer',
    'SchedulerLogger',
    'TelemetryExporter',

    # Decorators
    'trace_run',
    'monitor_performance',

    # Factory functions
    'get_metrics',
    'get_tracer',
    'get_scheduler_logger',
    'get_exporter',

    # Utilities
    'emit_metrics',
    'get_telemetry_health',
]
