"""
Telemetry and observability for the scheduler subsystem.

This is a thin wrapper that re-exports functionality from the modular telemetry package.
The implementation has been split into components in the telemetry/ subdirectory.

For the actual implementations, see:
- telemetry/models.py - Data models (MetricPoint, TraceSpan)
- telemetry/metrics_collector.py - Metrics collection
- telemetry/distributed_tracer.py - Distributed tracing
- telemetry/scheduler_logger.py - Structured logging
- telemetry/exporter.py - Telemetry export (OpenTelemetry/Grafana Cloud)
- telemetry/decorators.py - Decorator utilities
- telemetry/telemetry.py - Factory functions and utilities
"""

# Re-export everything from the telemetry package
from .telemetry import (
    # Models
    MetricPoint,
    TraceSpan,

    # Core components
    MetricsCollector,
    TimerContext,
    DistributedTracer,
    SchedulerLogger,
    TelemetryExporter,

    # Decorators
    trace_run,
    monitor_performance,

    # Factory functions
    get_metrics,
    get_tracer,
    get_scheduler_logger,
    get_exporter,

    # Utilities
    emit_metrics,
    get_telemetry_health,
)

# Maintain backward compatibility
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
