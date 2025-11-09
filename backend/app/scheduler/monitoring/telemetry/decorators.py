"""
Decorator utilities for telemetry.

Provides decorators for tracing and performance monitoring.
"""

import logging
import time
import asyncio
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


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
        # Import here to avoid circular dependencies
        from .telemetry import get_tracer, get_exporter, get_scheduler_logger

        try:
            from opentelemetry.trace import Status, StatusCode
            OTEL_AVAILABLE = True
        except ImportError:
            OTEL_AVAILABLE = False

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
        if otel_tracer and OTEL_AVAILABLE:
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
        # Import here to avoid circular dependencies
        from .telemetry import get_scheduler_logger

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
            # Import here to avoid circular dependencies
            from .telemetry import get_metrics

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
            # Import here to avoid circular dependencies
            from .telemetry import get_metrics

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
