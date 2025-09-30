"""
Telemetry and observability for the scheduler subsystem.

Provides comprehensive metrics, logging, tracing, and monitoring
for production deployment and performance analysis.

Integrates with Grafana Cloud via OpenTelemetry OTLP exporters when configured,
falls back to console logging for development.
"""

import logging
import time
import os
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import asyncio
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import uuid

# OpenTelemetry imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OpenTelemetry not available, using fallback telemetry")

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point."""
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'unit': self.unit
        }


@dataclass
class TraceSpan:
    """Distributed tracing span."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error, timeout

    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    def add_log(self, message: str, level: str = "info", **kwargs):
        """Add log entry to span."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logs.append(log_entry)

    def set_tag(self, key: str, value: str):
        """Set tag on span."""
        self.tags[key] = str(value)

    def finish(self, status: str = "ok"):
        """Finish the span."""
        self.end_time = datetime.now()
        self.status = status


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


class DistributedTracer:
    """
    Distributed tracing for scheduler operations.

    Tracks request flows across components for debugging
    and performance analysis.
    """

    def __init__(self):
        """Initialize distributed tracer."""
        self.active_spans = {}
        self.completed_spans = []

        # Cleanup configuration
        self.max_completed_spans = 10000

    def start_span(
        self,
        operation_name: str,
        parent_span: Optional[TraceSpan] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> TraceSpan:
        """
        Start a new trace span.

        Args:
            operation_name: Name of the operation
            parent_span: Parent span (if any)
            tags: Optional tags

        Returns:
            New trace span
        """
        trace_id = parent_span.trace_id if parent_span else str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_span_id = parent_span.span_id if parent_span else None

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            tags=tags or {}
        )

        self.active_spans[span_id] = span
        return span

    def finish_span(self, span: TraceSpan, status: str = "ok"):
        """
        Finish a trace span.

        Args:
            span: Span to finish
            status: Completion status
        """
        span.finish(status)

        # Move from active to completed
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]

        self.completed_spans.append(span)

        # Cleanup old spans
        if len(self.completed_spans) > self.max_completed_spans:
            self.completed_spans = self.completed_spans[-self.max_completed_spans // 2:]

    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """
        Get all spans for a trace.

        Args:
            trace_id: Trace identifier

        Returns:
            List of spans in the trace
        """
        spans = []

        # Check active spans
        for span in self.active_spans.values():
            if span.trace_id == trace_id:
                spans.append(span)

        # Check completed spans
        for span in self.completed_spans:
            if span.trace_id == trace_id:
                spans.append(span)

        # Sort by start time
        spans.sort(key=lambda s: s.start_time)
        return spans

    @asynccontextmanager
    async def trace_async(
        self,
        operation_name: str,
        parent_span: Optional[TraceSpan] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Async context manager for tracing.

        Args:
            operation_name: Name of the operation
            parent_span: Parent span (if any)
            tags: Optional tags

        Yields:
            Active trace span
        """
        span = self.start_span(operation_name, parent_span, tags)
        try:
            yield span
            self.finish_span(span, "ok")
        except Exception as e:
            span.add_log(f"Error: {str(e)}", "error")
            self.finish_span(span, "error")
            raise


class SchedulerLogger:
    """
    Structured logging for scheduler operations.

    Provides consistent, searchable logging with context
    and correlation IDs.
    """

    def __init__(self, logger_name: str = "scheduler"):
        """Initialize scheduler logger."""
        self.logger = logging.getLogger(logger_name)
        self._context_vars = {}

    def set_context(self, **kwargs):
        """Set logging context variables."""
        self._context_vars.update(kwargs)

    def clear_context(self):
        """Clear logging context."""
        self._context_vars.clear()

    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with context."""
        context = {**self._context_vars, **kwargs}

        if context:
            context_str = ' '.join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {context_str}"

        return message

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(message, **kwargs))

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message, **kwargs))


class TelemetryExporter:
    """
    Exports telemetry data to external systems.

    Uses OpenTelemetry OTLP exporters for Grafana Cloud when configured,
    falls back to console exporters for development.
    """

    def __init__(self):
        """Initialize telemetry exporter with OTLP integration."""
        self.export_queue = []
        self.export_config = {
            'enabled': True,
            'batch_size': 100,
            'flush_interval_seconds': 60,
            'max_queue_size': 10000
        }

        # OpenTelemetry setup
        self.otel_configured = False
        self.grafana_connected = False
        self._setup_opentelemetry()

    def _setup_opentelemetry(self):
        """Setup OpenTelemetry with Grafana Cloud or console exporters."""
        if not OTEL_AVAILABLE:
            logger.warning("OpenTelemetry not available, using fallback telemetry")
            return

        # Get Grafana Cloud configuration from environment
        grafana_endpoint = os.getenv('GRAFANA_OTLP_ENDPOINT')
        grafana_user = os.getenv('GRAFANA_OTLP_USER')
        grafana_api_key = os.getenv('GRAFANA_OTLP_API_KEY')

        # Create resource with service information
        resource = Resource.create({
            "service.name": "pulseplan-scheduler",
            "service.version": "1.0.0",
            "service.instance.id": str(uuid.uuid4()),
        })

        # Setup tracing
        self._setup_tracing(resource, grafana_endpoint, grafana_user, grafana_api_key)

        # Setup metrics
        self._setup_metrics(resource, grafana_endpoint, grafana_user, grafana_api_key)

        self.otel_configured = True
        logger.info(f"OpenTelemetry configured: Grafana={self.grafana_connected}")

    def _setup_tracing(self, resource, grafana_endpoint, grafana_user, grafana_api_key):
        """Setup OpenTelemetry tracing."""
        trace_provider = TracerProvider(resource=resource)

        if grafana_endpoint and grafana_user and grafana_api_key:
            # Configure OTLP exporter for Grafana Cloud
            try:
                otlp_trace_exporter = OTLPSpanExporter(
                    endpoint=grafana_endpoint,
                    headers={
                        "authorization": f"Basic {self._encode_basic_auth(grafana_user, grafana_api_key)}"
                    },
                    insecure=False
                )
                trace_provider.add_span_processor(
                    BatchSpanProcessor(otlp_trace_exporter)
                )
                self.grafana_connected = True
                logger.info("Grafana Cloud OTLP trace exporter configured")
            except Exception as e:
                logger.error(f"Failed to configure Grafana Cloud trace exporter: {e}")
                # Fall back to console exporter
                trace_provider.add_span_processor(
                    BatchSpanProcessor(ConsoleSpanExporter())
                )
        else:
            # Development: use console exporter
            trace_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
            logger.info("Using console trace exporter (development mode)")

        trace.set_tracer_provider(trace_provider)
        self.otel_tracer = trace.get_tracer("pulseplan-scheduler")

    def _setup_metrics(self, resource, grafana_endpoint, grafana_user, grafana_api_key):
        """Setup OpenTelemetry metrics."""
        if grafana_endpoint and grafana_user and grafana_api_key:
            # Configure OTLP exporter for Grafana Cloud
            try:
                otlp_metric_exporter = OTLPMetricExporter(
                    endpoint=grafana_endpoint,
                    headers={
                        "authorization": f"Basic {self._encode_basic_auth(grafana_user, grafana_api_key)}"
                    },
                    insecure=False
                )
                metric_reader = PeriodicExportingMetricReader(
                    exporter=otlp_metric_exporter,
                    export_interval_millis=30000  # 30 seconds
                )
                logger.info("Grafana Cloud OTLP metric exporter configured")
            except Exception as e:
                logger.error(f"Failed to configure Grafana Cloud metric exporter: {e}")
                # Fall back to console exporter
                metric_reader = PeriodicExportingMetricReader(
                    exporter=ConsoleMetricExporter(),
                    export_interval_millis=60000  # 60 seconds for console
                )
        else:
            # Development: use console exporter
            metric_reader = PeriodicExportingMetricReader(
                exporter=ConsoleMetricExporter(),
                export_interval_millis=60000  # 60 seconds
            )
            logger.info("Using console metric exporter (development mode)")

        metric_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(metric_provider)
        self.otel_meter = metrics.get_meter("pulseplan-scheduler")

        # Create commonly used instruments
        self._create_otel_instruments()

    def _create_otel_instruments(self):
        """Create OpenTelemetry metric instruments."""
        if not hasattr(self, 'otel_meter'):
            return

        # Counters
        self.otel_request_counter = self.otel_meter.create_counter(
            name="scheduler_requests_total",
            description="Total number of scheduling requests",
            unit="1"
        )

        self.otel_task_counter = self.otel_meter.create_counter(
            name="scheduler_tasks_processed_total",
            description="Total number of tasks processed",
            unit="1"
        )

        # Histograms
        self.otel_duration_histogram = self.otel_meter.create_histogram(
            name="scheduler_request_duration_ms",
            description="Scheduling request duration in milliseconds",
            unit="ms"
        )

        self.otel_solve_time_histogram = self.otel_meter.create_histogram(
            name="scheduler_solve_time_ms",
            description="Solver execution time in milliseconds",
            unit="ms"
        )

        # Gauges (using up-down counters as approximation)
        self.otel_active_requests_gauge = self.otel_meter.create_up_down_counter(
            name="scheduler_active_requests",
            description="Number of active scheduling requests",
            unit="1"
        )

    def _encode_basic_auth(self, username: str, password: str) -> str:
        """Encode basic auth credentials."""
        import base64
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return encoded_credentials

    async def export_metrics(self, metrics: List[MetricPoint], destination: str = "default"):
        """
        Export metrics to destination using OTLP or fallback.

        Args:
            metrics: List of metrics to export
            destination: Export destination
        """
        if not self.export_config['enabled']:
            return

        try:
            # Export via OpenTelemetry if available
            if self.otel_configured and hasattr(self, 'otel_meter'):
                await self._export_metrics_otlp(metrics)

            # Also maintain legacy export queue for backwards compatibility
            export_data = [metric.to_dict() for metric in metrics]
            self.export_queue.extend(export_data)

            # Flush if needed
            if len(self.export_queue) >= self.export_config['batch_size']:
                await self._flush_exports(destination)

        except Exception as e:
            logger.error(f"Metrics export failed: {e}")

    async def _export_metrics_otlp(self, metrics: List[MetricPoint]):
        """Export metrics via OpenTelemetry."""
        if not hasattr(self, 'otel_meter'):
            return

        for metric in metrics:
            try:
                # Map legacy metric types to OTLP instruments
                if metric.unit == "count":
                    # Use counter
                    if hasattr(self, 'otel_request_counter') and 'request' in metric.name:
                        self.otel_request_counter.add(metric.value, metric.tags)
                    elif hasattr(self, 'otel_task_counter') and 'task' in metric.name:
                        self.otel_task_counter.add(metric.value, metric.tags)
                    else:
                        # Create dynamic counter
                        counter = self.otel_meter.create_counter(
                            name=metric.name.replace('.', '_'),
                            description=f"Counter for {metric.name}",
                            unit="1"
                        )
                        counter.add(metric.value, metric.tags)

                elif metric.unit in ["histogram", "ms", "seconds"]:
                    # Use histogram
                    if hasattr(self, 'otel_duration_histogram') and 'duration' in metric.name:
                        self.otel_duration_histogram.record(metric.value, metric.tags)
                    elif hasattr(self, 'otel_solve_time_histogram') and 'solve' in metric.name:
                        self.otel_solve_time_histogram.record(metric.value, metric.tags)
                    else:
                        # Create dynamic histogram
                        histogram = self.otel_meter.create_histogram(
                            name=metric.name.replace('.', '_'),
                            description=f"Histogram for {metric.name}",
                            unit=metric.unit or "1"
                        )
                        histogram.record(metric.value, metric.tags)

                elif metric.unit == "gauge":
                    # Use up-down counter as gauge approximation
                    if hasattr(self, 'otel_active_requests_gauge') and 'active' in metric.name:
                        # For active requests, we need to track delta
                        pass  # Implement gauge logic as needed
                    else:
                        # Create dynamic gauge (using up-down counter)
                        gauge = self.otel_meter.create_up_down_counter(
                            name=metric.name.replace('.', '_'),
                            description=f"Gauge for {metric.name}",
                            unit=metric.unit or "1"
                        )
                        gauge.add(metric.value, metric.tags)

            except Exception as e:
                logger.debug(f"Failed to export metric {metric.name} via OTLP: {e}")

    async def export_traces(self, spans: List[TraceSpan], destination: str = "default"):
        """
        Export trace spans to destination using OTLP or fallback.

        Args:
            spans: List of spans to export
            destination: Export destination
        """
        if not self.export_config['enabled']:
            return

        try:
            # Export via OpenTelemetry is handled automatically by BatchSpanProcessor
            # when using the OTLP tracer - no manual export needed

            # Maintain legacy export for backwards compatibility
            export_data = []
            for span in spans:
                span_data = {
                    'trace_id': span.trace_id,
                    'span_id': span.span_id,
                    'parent_span_id': span.parent_span_id,
                    'operation_name': span.operation_name,
                    'start_time': span.start_time.isoformat(),
                    'end_time': span.end_time.isoformat() if span.end_time else None,
                    'duration_ms': span.duration_ms,
                    'status': span.status,
                    'tags': span.tags,
                    'logs': span.logs
                }
                export_data.append(span_data)

            # Export immediately for traces (usually smaller volume)
            await self._export_to_destination(export_data, destination, 'traces')

        except Exception as e:
            logger.error(f"Trace export failed: {e}")

    def get_otel_tracer(self):
        """Get OpenTelemetry tracer if available."""
        return getattr(self, 'otel_tracer', None)

    def get_otel_meter(self):
        """Get OpenTelemetry meter if available."""
        return getattr(self, 'otel_meter', None)

    async def _flush_exports(self, destination: str):
        """Flush queued exports."""
        if not self.export_queue:
            return

        batch = self.export_queue[:self.export_config['batch_size']]
        self.export_queue = self.export_queue[self.export_config['batch_size']:]

        await self._export_to_destination(batch, destination, 'metrics')

    async def _export_to_destination(self, data: List[Dict], destination: str, data_type: str):
        """
        Export data to specific destination.

        Args:
            data: Data to export
            destination: Destination name
            data_type: Type of data ('metrics' or 'traces')
        """
        # Log export for debugging (legacy behavior)
        logger.debug(f"Exported {len(data)} {data_type} to {destination}")

        # OpenTelemetry handles actual export automatically via:
        # - BatchSpanProcessor for traces
        # - PeriodicExportingMetricReader for metrics
        # Data is automatically sent to Grafana Cloud OTLP endpoint

    def get_connection_status(self) -> Dict[str, Any]:
        """Get OTLP connection status for health checks."""
        return {
            'otel_available': OTEL_AVAILABLE,
            'otel_configured': self.otel_configured,
            'grafana_cloud_connected': self.grafana_connected,
            'exporters': {
                'traces': 'otlp' if self.grafana_connected else 'console',
                'metrics': 'otlp' if self.grafana_connected else 'console'
            },
            'service_name': 'pulseplan-scheduler'
        }


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


def trace_run(func: Callable) -> Callable:
    """
    Decorator for tracing function execution with OpenTelemetry integration.

    Args:
        func: Function to trace

    Returns:
        Wrapped function with tracing
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        tracer = get_tracer()
        exporter = get_exporter()

        # Extract user_id if available for context
        user_id = None
        if args and hasattr(args[0], 'user_id'):
            user_id = args[0].user_id
        elif 'user_id' in kwargs:
            user_id = kwargs['user_id']

        tags = {'function': func.__name__}
        if user_id:
            tags['user_id'] = user_id

        # Use OpenTelemetry tracer if available
        otel_tracer = exporter.get_otel_tracer()
        if otel_tracer:
            with otel_tracer.start_as_current_span(func.__name__) as otel_span:
                # Set OpenTelemetry span attributes
                otel_span.set_attribute('function.name', func.__name__)
                if user_id:
                    otel_span.set_attribute('user.id', user_id)

                # Also use legacy tracer for compatibility
                async with tracer.trace_async(func.__name__, tags=tags) as span:
                    span.set_tag('function', func.__name__)

                    try:
                        result = await func(*args, **kwargs)
                        span.set_tag('success', 'true')
                        otel_span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_tag('success', 'false')
                        span.set_tag('error', str(e))
                        otel_span.set_status(Status(StatusCode.ERROR, str(e)))
                        otel_span.record_exception(e)
                        raise
        else:
            # Fallback to legacy tracer only
            async with tracer.trace_async(func.__name__, tags=tags) as span:
                span.set_tag('function', func.__name__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_tag('success', 'true')
                    return result
                except Exception as e:
                    span.set_tag('success', 'false')
                    span.set_tag('error', str(e))
                    raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # For sync functions, just add basic logging
        logger = get_scheduler_logger()

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(f"Function {func.__name__} completed in {duration_ms:.1f}ms")
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Function {func.__name__} failed after {duration_ms:.1f}ms: {e}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def monitor_performance(operation: str):
    """
    Decorator for monitoring operation performance.

    Args:
        operation: Operation name for metrics

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics()

            # Track operation start
            collector.counter(f"{operation}.started")

            with collector.timer(f"{operation}.duration"):
                try:
                    result = await func(*args, **kwargs)
                    collector.counter(f"{operation}.success")
                    return result
                except Exception as e:
                    collector.counter(f"{operation}.error")
                    collector.counter(f"{operation}.error.{type(e).__name__}")
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            collector = get_metrics()

            collector.counter(f"{operation}.started")

            with collector.timer(f"{operation}.duration"):
                try:
                    result = func(*args, **kwargs)
                    collector.counter(f"{operation}.success")
                    return result
                except Exception as e:
                    collector.counter(f"{operation}.error")
                    collector.counter(f"{operation}.error.{type(e).__name__}")
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


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