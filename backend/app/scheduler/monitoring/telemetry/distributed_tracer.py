"""
Distributed tracing for scheduler operations.

Tracks request flows across components for debugging
and performance analysis.
"""

import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from datetime import datetime

from .models import TraceSpan


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
