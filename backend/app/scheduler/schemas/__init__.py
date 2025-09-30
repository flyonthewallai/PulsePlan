"""
Enhanced schema definitions for comprehensive scheduler observability.

This package provides rich data structures for detailed scheduling insights,
quality metrics, explanations, and diagnostic information.
"""

from .enhanced_results import (
    EnhancedScheduleSolution,
    QualityMetrics,
    ScheduleExplanations,
    ScheduleQuality,
    AlternativeSolution,
    DetailedDiagnostics,
    OptimizationInsights,
    PerformanceSummary,
    ConstraintType,
    ConstraintViolation,
    SchedulingDecision,
    DecisionReason
)

__all__ = [
    'EnhancedScheduleSolution',
    'QualityMetrics',
    'ScheduleExplanations',
    'ScheduleQuality',
    'AlternativeSolution',
    'DetailedDiagnostics',
    'OptimizationInsights',
    'PerformanceSummary',
    'ConstraintType',
    'ConstraintViolation',
    'SchedulingDecision',
    'DecisionReason'
]