"""
Utility calculation for task-time slot pairs.

Provides both ML-based and simplified utility calculations for
scheduling optimization, with safety fallbacks.
"""

import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime

from ..domain import Task, BusyEvent, Preferences
from ...optimization.time_index import TimeIndex
from ...learning.completion_model import CompletionModel
from ..features import build_utilities

logger = logging.getLogger(__name__)


class UtilityCalculator:
    """Calculates utility scores for task-time slot combinations."""

    def __init__(self):
        """Initialize utility calculator."""
        pass

    async def build_utilities_with_ml(
        self,
        model: CompletionModel,
        tasks: List[Task],
        time_index: TimeIndex,
        prefs: Preferences,
        events: List[BusyEvent],
        history: List
    ) -> Tuple[Dict[str, Dict[int, float]], Dict[str, Any]]:
        """
        Build utilities using ML-based features.

        Args:
            model: Trained completion probability model
            tasks: Tasks to schedule
            time_index: Time discretization
            prefs: User preferences
            events: Busy calendar events
            history: Historical completion data

        Returns:
            Tuple of (utility matrix, penalty context)
        """
        util_matrix, penalty_context = await build_utilities(
            model, tasks, time_index, prefs, events, history
        )

        logger.debug(
            f"Built ML utilities for {len(tasks)} tasks across "
            f"{len(time_index)} time slots"
        )

        return util_matrix, penalty_context

    def build_simple_utilities(
        self, tasks: List[Task], time_index: TimeIndex
    ) -> Dict[str, Dict[int, float]]:
        """
        Build simplified utility matrix for coarsening scenarios.

        Uses rule-based heuristics without ML:
        - Deadline proximity (linear urgency)
        - Time of day preferences (work hours)
        - Base utility

        Args:
            tasks: Tasks to schedule
            time_index: Time discretization

        Returns:
            Utility matrix mapping task_id -> {slot_idx -> utility}
        """
        util_matrix = {}

        for task in tasks:
            task_utils = {}

            # Simple utility based on deadline proximity and time of day
            for slot_idx in range(len(time_index)):
                slot_time = time_index.slot_to_datetime(slot_idx)

                # Base utility
                utility = 1.0

                # Deadline pressure (simple linear decay)
                if task.deadline:
                    time_to_deadline = (task.deadline - slot_time).total_seconds() / 3600  # hours
                    if time_to_deadline > 0:
                        # Higher utility closer to deadline
                        utility += min(2.0, 24.0 / max(1, time_to_deadline))

                # Time of day preference (prefer working hours)
                hour = slot_time.hour
                if 9 <= hour <= 17:  # Working hours
                    utility += 0.5
                elif 8 <= hour <= 8 or 18 <= hour <= 20:  # Extended hours
                    utility += 0.2

                task_utils[slot_idx] = utility

            util_matrix[task.id] = task_utils

        logger.debug(
            f"Built simple utilities for {len(tasks)} tasks "
            f"(fallback/coarsening mode)"
        )

        return util_matrix

    def build_deadline_based_utilities(
        self, tasks: List[Task], time_index: TimeIndex
    ) -> Dict[str, Dict[int, float]]:
        """
        Build utilities based primarily on deadline urgency.

        Args:
            tasks: Tasks to schedule
            time_index: Time discretization

        Returns:
            Utility matrix focused on deadline proximity
        """
        util_matrix = {}

        for task in tasks:
            task_utils = {}

            for slot_idx in range(len(time_index)):
                slot_time = time_index.slot_to_datetime(slot_idx)

                # Default utility
                utility = 0.5

                if task.deadline:
                    hours_until_deadline = (
                        (task.deadline - slot_time).total_seconds() / 3600
                    )

                    if hours_until_deadline > 0:
                        # Exponential urgency as deadline approaches
                        if hours_until_deadline < 24:
                            utility = 3.0
                        elif hours_until_deadline < 48:
                            utility = 2.0
                        elif hours_until_deadline < 72:
                            utility = 1.5
                        else:
                            utility = 1.0
                    else:
                        # Past deadline - very high urgency
                        utility = 4.0

                task_utils[slot_idx] = utility

            util_matrix[task.id] = task_utils

        return util_matrix

    def build_uniform_utilities(
        self, tasks: List[Task], time_index: TimeIndex, base_value: float = 1.0
    ) -> Dict[str, Dict[int, float]]:
        """
        Build uniform utilities (all slots equal value).

        Useful for testing or when no preferences exist.

        Args:
            tasks: Tasks to schedule
            time_index: Time discretization
            base_value: Base utility value for all slots

        Returns:
            Uniform utility matrix
        """
        util_matrix = {}

        for task in tasks:
            task_utils = {
                slot_idx: base_value
                for slot_idx in range(len(time_index))
            }
            util_matrix[task.id] = task_utils

        logger.debug(
            f"Built uniform utilities (value={base_value}) "
            f"for {len(tasks)} tasks"
        )

        return util_matrix

    def normalize_utilities(
        self, util_matrix: Dict[str, Dict[int, float]], method: str = "minmax"
    ) -> Dict[str, Dict[int, float]]:
        """
        Normalize utility values.

        Args:
            util_matrix: Raw utility matrix
            method: Normalization method ("minmax", "zscore", "sum")

        Returns:
            Normalized utility matrix
        """
        if method == "minmax":
            return self._normalize_minmax(util_matrix)
        elif method == "zscore":
            return self._normalize_zscore(util_matrix)
        elif method == "sum":
            return self._normalize_sum(util_matrix)
        else:
            logger.warning(f"Unknown normalization method: {method}")
            return util_matrix

    def _normalize_minmax(
        self, util_matrix: Dict[str, Dict[int, float]]
    ) -> Dict[str, Dict[int, float]]:
        """Min-max normalization to [0, 1] range."""
        normalized = {}

        for task_id, task_utils in util_matrix.items():
            values = list(task_utils.values())
            if not values:
                normalized[task_id] = {}
                continue

            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val

            if range_val == 0:
                # All values are the same
                normalized[task_id] = {k: 0.5 for k in task_utils.keys()}
            else:
                normalized[task_id] = {
                    k: (v - min_val) / range_val
                    for k, v in task_utils.items()
                }

        return normalized

    def _normalize_zscore(
        self, util_matrix: Dict[str, Dict[int, float]]
    ) -> Dict[str, Dict[int, float]]:
        """Z-score normalization."""
        import statistics

        normalized = {}

        for task_id, task_utils in util_matrix.items():
            values = list(task_utils.values())
            if not values or len(values) < 2:
                normalized[task_id] = task_utils
                continue

            mean = statistics.mean(values)
            stdev = statistics.stdev(values)

            if stdev == 0:
                normalized[task_id] = {k: 0.0 for k in task_utils.keys()}
            else:
                normalized[task_id] = {
                    k: (v - mean) / stdev
                    for k, v in task_utils.items()
                }

        return normalized

    def _normalize_sum(
        self, util_matrix: Dict[str, Dict[int, float]]
    ) -> Dict[str, Dict[int, float]]:
        """Normalize so each task's utilities sum to 1.0."""
        normalized = {}

        for task_id, task_utils in util_matrix.items():
            total = sum(task_utils.values())

            if total == 0:
                normalized[task_id] = task_utils
            else:
                normalized[task_id] = {
                    k: v / total
                    for k, v in task_utils.items()
                }

        return normalized


def get_utility_calculator() -> UtilityCalculator:
    """Get a utility calculator instance."""
    return UtilityCalculator()
