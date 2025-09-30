"""
Performance monitoring and SLO management for the scheduler.

This module provides Service Level Objective (SLO) monitoring,
automatic performance degradation detection, and algorithm coarsening
to maintain scheduling responsiveness under load.
"""

from .slo_gates import (
    SLOGate,
    SLOLevel,
    SLOConfig,
    CoarseningStrategy,
    PerformanceMetrics,
    SLOStatus,
    SLOViolationError,
    get_slo_gate,
    configure_slo_gate
)

__all__ = [
    'SLOGate',
    'SLOLevel',
    'SLOConfig',
    'CoarseningStrategy',
    'PerformanceMetrics',
    'SLOStatus',
    'SLOViolationError',
    'get_slo_gate',
    'configure_slo_gate'
]