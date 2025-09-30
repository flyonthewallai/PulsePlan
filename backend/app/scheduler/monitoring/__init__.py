"""
Monitoring, observability, and telemetry for the scheduler.
"""

from .telemetry import trace_run, emit_metrics
# Note: smart_assistant not imported here to avoid circular imports

__all__ = [
    'trace_run',
    'emit_metrics'
]