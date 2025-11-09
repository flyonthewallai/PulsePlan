"""
Schedule quality analysis system for comprehensive assessment.

Provides detailed quality metrics, identifies improvement opportunities,
and generates actionable insights for schedule optimization.

This is a compatibility wrapper - the implementation has been modularized
into the quality/ package for better maintainability.
"""

# Re-export everything from the modular implementation
from .quality import (
    QualityDimension,
    QualityFactor,
    QualityBreakdown,
    TimeDistributionAnalysis,
    ConstraintComplianceAnalysis,
    UserExperienceAnalysis,
    QualityAnalyzer
)

__all__ = [
    'QualityDimension',
    'QualityFactor',
    'QualityBreakdown',
    'TimeDistributionAnalysis',
    'ConstraintComplianceAnalysis',
    'UserExperienceAnalysis',
    'QualityAnalyzer',
]
