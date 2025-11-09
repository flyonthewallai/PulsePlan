"""
Time distribution analysis for schedule quality assessment.

Analyzes time allocation patterns, fragmentation, gaps, and rhythm.
"""

from typing import List
import statistics

from ...core.domain import ScheduleBlock, BusyEvent
from .models import TimeDistributionAnalysis


class TimeAnalyzer:
    """Analyzes time distribution patterns in schedules."""

    def analyze_time_distribution(
        self,
        blocks: List[ScheduleBlock],
        busy_events: List[BusyEvent]
    ) -> TimeDistributionAnalysis:
        """Analyze time distribution patterns."""

        if not blocks:
            return TimeDistributionAnalysis(
                total_scheduled_time=0,
                total_available_time=0,
                utilization_ratio=0.0,
                morning_allocation=0.0,
                afternoon_allocation=0.0,
                evening_allocation=0.0,
                number_of_blocks=0,
                average_block_size=0.0,
                block_size_variance=0.0,
                largest_continuous_block=0,
                total_gaps=0,
                average_gap_size=0.0,
                productive_gap_ratio=0.0,
                context_switches=0,
                similar_task_clustering=0.0,
                energy_level_alignment=0.0
            )

        # Basic time calculations
        total_scheduled_time = sum(block.duration_minutes for block in blocks)

        # Estimate available time (assuming 16-hour day)
        total_available_time = 16 * 60  # 16 hours in minutes
        busy_time = sum(int((event.end - event.start).total_seconds() / 60) for event in busy_events)
        effective_available_time = total_available_time - busy_time
        utilization_ratio = total_scheduled_time / max(1, effective_available_time)

        # Time of day distribution
        morning_time = sum(
            block.duration_minutes for block in blocks
            if 6 <= block.start_time.hour < 12
        )
        afternoon_time = sum(
            block.duration_minutes for block in blocks
            if 12 <= block.start_time.hour < 18
        )
        evening_time = sum(
            block.duration_minutes for block in blocks
            if 18 <= block.start_time.hour < 22
        )

        morning_allocation = morning_time / max(1, total_scheduled_time)
        afternoon_allocation = afternoon_time / max(1, total_scheduled_time)
        evening_allocation = evening_time / max(1, total_scheduled_time)

        # Block analysis
        block_sizes = [block.duration_minutes for block in blocks]
        average_block_size = statistics.mean(block_sizes) if block_sizes else 0.0
        block_size_variance = statistics.variance(block_sizes) if len(block_sizes) > 1 else 0.0
        largest_continuous_block = max(block_sizes) if block_sizes else 0

        # Gap analysis
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        gaps = []
        for i in range(len(sorted_blocks) - 1):
            gap_start = sorted_blocks[i].end_time
            gap_end = sorted_blocks[i + 1].start_time
            gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
            if gap_minutes > 0:
                gaps.append(gap_minutes)

        total_gaps = len(gaps)
        average_gap_size = statistics.mean(gaps) if gaps else 0.0
        productive_gap_ratio = len([g for g in gaps if g >= 30]) / max(1, len(gaps))

        # Context switches (simplified)
        context_switches = max(0, len(blocks) - 1)

        # Task clustering (simplified - would need task categories)
        similar_task_clustering = 0.7  # Default placeholder

        # Energy alignment (simplified - would need user energy patterns)
        energy_level_alignment = 0.6  # Default placeholder

        return TimeDistributionAnalysis(
            total_scheduled_time=total_scheduled_time,
            total_available_time=effective_available_time,
            utilization_ratio=utilization_ratio,
            morning_allocation=morning_allocation,
            afternoon_allocation=afternoon_allocation,
            evening_allocation=evening_allocation,
            number_of_blocks=len(blocks),
            average_block_size=average_block_size,
            block_size_variance=block_size_variance,
            largest_continuous_block=largest_continuous_block,
            total_gaps=total_gaps,
            average_gap_size=average_gap_size,
            productive_gap_ratio=productive_gap_ratio,
            context_switches=context_switches,
            similar_task_clustering=similar_task_clustering,
            energy_level_alignment=energy_level_alignment
        )

    def analyze_time_utilization(
        self,
        blocks: List[ScheduleBlock],
        busy_events: List[BusyEvent]
    ) -> tuple[float, float]:
        """
        Analyze time utilization efficiency.

        Returns:
            Tuple of (utilization_ratio, utilization_score)
        """
        if not blocks:
            return 0.0, 0.0

        total_scheduled = sum(block.duration_minutes for block in blocks)
        total_available = 8 * 60  # Assume 8-hour workday
        busy_time = sum(int((event.end - event.start).total_seconds() / 60) for event in busy_events)
        effective_available = total_available - busy_time

        utilization = total_scheduled / max(1, effective_available)
        utilization_score = min(1.0, utilization)  # Cap at 1.0

        return utilization, utilization_score

    def analyze_block_sizes(
        self,
        blocks: List[ScheduleBlock]
    ) -> tuple[float, float]:
        """
        Analyze block size distribution.

        Returns:
            Tuple of (average_size, size_efficiency_score)
        """
        if not blocks:
            return 0.0, 0.0

        block_sizes = [block.duration_minutes for block in blocks]
        avg_block_size = statistics.mean(block_sizes) if block_sizes else 0

        # Optimal block size is typically 60-90 minutes for deep work
        optimal_size = 75
        size_efficiency = 1.0 - abs(avg_block_size - optimal_size) / optimal_size
        size_efficiency = max(0.0, min(1.0, size_efficiency))

        return avg_block_size, size_efficiency

    def count_context_switches(self, blocks: List[ScheduleBlock]) -> int:
        """Count the number of context switches in the schedule."""
        return max(0, len(blocks) - 1)

    def calculate_gap_statistics(
        self,
        blocks: List[ScheduleBlock]
    ) -> tuple[int, float, float]:
        """
        Calculate gap statistics between blocks.

        Returns:
            Tuple of (total_gaps, average_gap_size, productive_gap_ratio)
        """
        if len(blocks) < 2:
            return 0, 0.0, 0.0

        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        gaps = []

        for i in range(len(sorted_blocks) - 1):
            gap_start = sorted_blocks[i].end_time
            gap_end = sorted_blocks[i + 1].start_time
            gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
            if gap_minutes > 0:
                gaps.append(gap_minutes)

        if not gaps:
            return 0, 0.0, 0.0

        total_gaps = len(gaps)
        average_gap_size = statistics.mean(gaps)
        productive_gap_ratio = len([g for g in gaps if g >= 30]) / len(gaps)

        return total_gaps, average_gap_size, productive_gap_ratio
