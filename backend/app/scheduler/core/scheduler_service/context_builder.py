"""
Context building for bandit weight selection.

Builds the contextual features used by the multi-armed bandit to select
appropriate penalty weights for the scheduler.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..domain import Preferences
from ...optimization.time_index import TimeIndex
from ....core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds context for bandit weight selection."""

    def __init__(self):
        """Initialize context builder."""
        self.timezone_manager = get_timezone_manager()

    def build_bandit_context(
        self,
        user_id: str,
        horizon_days: int,
        prefs: Preferences,
        time_index: TimeIndex
    ) -> Dict[str, Any]:
        """
        Build context for bandit weight selection.

        Args:
            user_id: User identifier
            horizon_days: Number of days in scheduling horizon
            prefs: User preferences
            time_index: Time discretization index

        Returns:
            Context dictionary with features for bandit
        """
        # Ensure timezone-aware datetime for context
        context_dt = self.timezone_manager.ensure_timezone_aware(time_index.start_dt)

        context = {
            'user_id': user_id,
            'horizon_days': horizon_days,
            'dow': context_dt.weekday(),
            'hour': context_dt.hour,
            'timezone': prefs.timezone,
            'workday_hours': (prefs.workday_start, prefs.workday_end),
            'max_daily_effort': prefs.max_daily_effort_minutes,
            'granularity': prefs.session_granularity_minutes
        }

        logger.debug(
            f"Built bandit context for user {user_id}: "
            f"dow={context['dow']}, hour={context['hour']}, "
            f"horizon={horizon_days} days"
        )

        return context

    def build_extended_context(
        self,
        user_id: str,
        horizon_days: int,
        prefs: Preferences,
        time_index: TimeIndex,
        additional_features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build extended context with additional features.

        Args:
            user_id: User identifier
            horizon_days: Number of days in scheduling horizon
            prefs: User preferences
            time_index: Time discretization index
            additional_features: Optional additional context features

        Returns:
            Extended context dictionary
        """
        # Start with base context
        context = self.build_bandit_context(user_id, horizon_days, prefs, time_index)

        # Add additional features if provided
        if additional_features:
            context.update(additional_features)
            logger.debug(
                f"Extended context with {len(additional_features)} additional features"
            )

        return context

    def extract_temporal_features(self, dt: datetime) -> Dict[str, Any]:
        """
        Extract temporal features from a datetime.

        Args:
            dt: Datetime to extract features from

        Returns:
            Dictionary of temporal features
        """
        dt_aware = self.timezone_manager.ensure_timezone_aware(dt)

        features = {
            'hour': dt_aware.hour,
            'dow': dt_aware.weekday(),
            'is_weekend': dt_aware.weekday() >= 5,
            'is_morning': 6 <= dt_aware.hour < 12,
            'is_afternoon': 12 <= dt_aware.hour < 17,
            'is_evening': 17 <= dt_aware.hour < 22,
            'is_night': dt_aware.hour >= 22 or dt_aware.hour < 6,
            'day_of_month': dt_aware.day,
            'month': dt_aware.month,
            'week_of_year': dt_aware.isocalendar()[1]
        }

        return features

    def extract_workload_features(
        self,
        n_tasks: int,
        n_events: int,
        horizon_days: int,
        prefs: Preferences
    ) -> Dict[str, Any]:
        """
        Extract workload-related features.

        Args:
            n_tasks: Number of tasks to schedule
            n_events: Number of busy events
            horizon_days: Scheduling horizon in days
            prefs: User preferences

        Returns:
            Dictionary of workload features
        """
        # Calculate available hours per day
        workday_hours = prefs.workday_end - prefs.workday_start
        total_available_hours = workday_hours * horizon_days

        # Calculate load metrics
        avg_tasks_per_day = n_tasks / max(1, horizon_days)
        avg_events_per_day = n_events / max(1, horizon_days)

        features = {
            'n_tasks': n_tasks,
            'n_events': n_events,
            'avg_tasks_per_day': avg_tasks_per_day,
            'avg_events_per_day': avg_events_per_day,
            'workload_density': (n_tasks + n_events) / max(1, total_available_hours),
            'max_daily_effort_hours': prefs.max_daily_effort_minutes / 60,
            'is_high_workload': avg_tasks_per_day > 10,
            'is_high_event_density': avg_events_per_day > 5
        }

        return features

    def merge_contexts(
        self,
        *contexts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge multiple context dictionaries.

        Args:
            *contexts: Variable number of context dictionaries

        Returns:
            Merged context dictionary
        """
        merged = {}

        for context in contexts:
            if context:
                merged.update(context)

        return merged


def get_context_builder() -> ContextBuilder:
    """Get a context builder instance."""
    return ContextBuilder()
