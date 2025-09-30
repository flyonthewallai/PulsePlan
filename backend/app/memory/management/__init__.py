"""
Memory management and profiling tools.

This module contains memory management components including:
- Profile snapshot generation and user behavior tracking
- Memory lifecycle management and cleanup
- Memory analytics and statistics
"""

from .profile_snapshots import (
    BehaviorMetrics,
    WeeklyProfileService,
    get_weekly_profile_service
)

__all__ = [
    "BehaviorMetrics",
    "WeeklyProfileService", 
    "get_weekly_profile_service"
]
