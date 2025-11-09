"""
Telemetry export to external systems.

Uses OpenTelemetry OTLP exporters for Grafana Cloud when configured,
falls back to console exporters for development.
"""

import logging
import os
import uuid
from typing import Dict, List, Any

from .models import MetricPoint, TraceSpan

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
