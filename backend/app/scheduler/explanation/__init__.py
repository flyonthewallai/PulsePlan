"""
Explanation and insight generation components for scheduler transparency.

This package provides tools for generating human-readable explanations
of scheduling decisions, constraint analysis, and alternative scenarios.
"""

from .schedule_explainer import ScheduleExplainer
from .constraint_analyzer import ConstraintAnalyzer
from .alternative_generator import AlternativeGenerator

__all__ = ['ScheduleExplainer', 'ConstraintAnalyzer', 'AlternativeGenerator']