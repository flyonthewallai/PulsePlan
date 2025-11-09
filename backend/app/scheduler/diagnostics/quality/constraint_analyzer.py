"""
Constraint compliance analysis for schedule quality assessment.

Analyzes coverage, satisfaction, balance, and stability factors.
"""

from typing import List, Dict, Any
from collections import defaultdict, Counter
import statistics

from ...core.domain import Task, ScheduleBlock, BusyEvent
from .models import QualityFactor, QualityDimension


class ConstraintAnalyzer:
    """Analyzes constraint satisfaction and schedule factors."""

    def analyze_coverage(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        unscheduled_tasks: List[str]
    ) -> List[QualityFactor]:
        """Analyze task coverage quality factors."""
        factors = []

        if not all_tasks:
            return factors

        # Task completion ratio
        scheduled_count = len(all_tasks) - len(unscheduled_tasks)
        completion_ratio = scheduled_count / len(all_tasks)

        coverage_factor = QualityFactor(
            name="task_completion_ratio",
            dimension=QualityDimension.COVERAGE,
            score=completion_ratio,
            description=f"{scheduled_count}/{len(all_tasks)} tasks scheduled",
            actual_value=completion_ratio,
            optimal_value=1.0
        )

        if completion_ratio < 0.8:
            coverage_factor.issues_identified.append("Significant number of unscheduled tasks")
            coverage_factor.improvement_suggestions.append("Consider extending schedule horizon or reducing task scope")

        factors.append(coverage_factor)

        # Priority coverage
        high_priority_tasks = [t for t in all_tasks if getattr(t, 'priority', 3) >= 4]
        if high_priority_tasks:
            scheduled_high_priority = [
                t for t in high_priority_tasks
                if t.id not in unscheduled_tasks
            ]
            priority_coverage = len(scheduled_high_priority) / len(high_priority_tasks)

            priority_factor = QualityFactor(
                name="priority_task_coverage",
                dimension=QualityDimension.COVERAGE,
                score=priority_coverage,
                weight=1.5,  # Higher weight for priority tasks
                description=f"{len(scheduled_high_priority)}/{len(high_priority_tasks)} high-priority tasks scheduled",
                actual_value=priority_coverage,
                optimal_value=1.0
            )

            if priority_coverage < 0.9:
                priority_factor.issues_identified.append("High-priority tasks not fully covered")
                priority_factor.improvement_suggestions.append("Prioritize high-importance tasks for scheduling")

            factors.append(priority_factor)

        return factors

    def analyze_efficiency(
        self,
        blocks: List[ScheduleBlock],
        busy_events: List[BusyEvent],
        all_tasks: List[Task]
    ) -> List[QualityFactor]:
        """Analyze scheduling efficiency factors."""
        factors = []

        if not blocks:
            return factors

        # Time utilization
        total_scheduled = sum(block.duration_minutes for block in blocks)
        total_available = 8 * 60  # Assume 8-hour workday
        busy_time = sum(int((event.end - event.start).total_seconds() / 60) for event in busy_events)
        effective_available = total_available - busy_time

        utilization = total_scheduled / max(1, effective_available)
        utilization_score = min(1.0, utilization)  # Cap at 1.0

        utilization_factor = QualityFactor(
            name="time_utilization",
            dimension=QualityDimension.EFFICIENCY,
            score=utilization_score,
            description=f"{utilization:.1%} of available time utilized",
            actual_value=utilization,
            optimal_value=0.8  # 80% is often optimal
        )

        if utilization < 0.5:
            utilization_factor.issues_identified.append("Low time utilization")
            utilization_factor.improvement_suggestions.append("Consider scheduling more tasks or longer blocks")
        elif utilization > 0.9:
            utilization_factor.issues_identified.append("Very high utilization may cause stress")
            utilization_factor.improvement_suggestions.append("Consider adding buffer time")

        factors.append(utilization_factor)

        # Block size efficiency
        block_sizes = [block.duration_minutes for block in blocks]
        avg_block_size = statistics.mean(block_sizes) if block_sizes else 0

        # Optimal block size is typically 60-90 minutes for deep work
        optimal_size = 75
        size_efficiency = 1.0 - abs(avg_block_size - optimal_size) / optimal_size
        size_efficiency = max(0.0, min(1.0, size_efficiency))

        block_size_factor = QualityFactor(
            name="block_size_efficiency",
            dimension=QualityDimension.EFFICIENCY,
            score=size_efficiency,
            description=f"Average block size: {avg_block_size:.1f} minutes",
            actual_value=avg_block_size,
            optimal_value=optimal_size
        )

        if avg_block_size < 30:
            block_size_factor.issues_identified.append("Blocks may be too short for effective work")
            block_size_factor.improvement_suggestions.append("Consider consolidating into longer blocks")
        elif avg_block_size > 120:
            block_size_factor.issues_identified.append("Blocks may be too long and tiring")
            block_size_factor.improvement_suggestions.append("Consider breaking into shorter sessions")

        factors.append(block_size_factor)

        return factors

    def analyze_satisfaction(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        preferences: Dict[str, Any]
    ) -> List[QualityFactor]:
        """Analyze preference satisfaction factors."""
        factors = []

        # Time preference satisfaction
        preferred_times = preferences.get('preferred_times', {})
        if preferred_times and blocks:
            satisfaction_score = 0.0
            total_weight = 0.0

            for block in blocks:
                hour = block.start_time.hour
                task_id = block.task_id

                # Simple preference matching (would be more sophisticated in practice)
                if 'morning' in preferred_times and 6 <= hour < 12:
                    satisfaction_score += 1.0
                    total_weight += 1.0
                elif 'afternoon' in preferred_times and 12 <= hour < 18:
                    satisfaction_score += 1.0
                    total_weight += 1.0
                elif 'evening' in preferred_times and 18 <= hour < 22:
                    satisfaction_score += 1.0
                    total_weight += 1.0
                else:
                    total_weight += 1.0

            preference_satisfaction = satisfaction_score / max(1, total_weight)

            preference_factor = QualityFactor(
                name="time_preference_satisfaction",
                dimension=QualityDimension.SATISFACTION,
                score=preference_satisfaction,
                description=f"{preference_satisfaction:.1%} of blocks match time preferences",
                actual_value=preference_satisfaction,
                optimal_value=0.8
            )

            if preference_satisfaction < 0.5:
                preference_factor.issues_identified.append("Many tasks scheduled outside preferred times")
                preference_factor.improvement_suggestions.append("Consider adjusting constraints to better match preferences")

            factors.append(preference_factor)

        # Deadline satisfaction
        deadline_tasks = [t for t in all_tasks if hasattr(t, 'deadline') and t.deadline]
        if deadline_tasks and blocks:
            scheduled_task_ids = {block.task_id for block in blocks}
            deadline_violations = 0

            for task in deadline_tasks:
                if task.id in scheduled_task_ids:
                    # Find the block for this task
                    task_blocks = [b for b in blocks if b.task_id == task.id]
                    if task_blocks:
                        latest_block = max(task_blocks, key=lambda b: b.end_time)
                        if latest_block.end_time > task.deadline:
                            deadline_violations += 1

            deadline_satisfaction = 1.0 - (deadline_violations / len(deadline_tasks))

            deadline_factor = QualityFactor(
                name="deadline_satisfaction",
                dimension=QualityDimension.SATISFACTION,
                score=deadline_satisfaction,
                description=f"{deadline_violations} deadline violations out of {len(deadline_tasks)} deadline tasks",
                actual_value=deadline_satisfaction,
                optimal_value=1.0
            )

            if deadline_violations > 0:
                deadline_factor.issues_identified.append(f"{deadline_violations} tasks scheduled past their deadlines")
                deadline_factor.improvement_suggestions.append("Reschedule tasks to meet deadlines or extend deadlines")

            factors.append(deadline_factor)

        return factors

    def analyze_balance(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> List[QualityFactor]:
        """Analyze workload balance factors."""
        factors = []

        if not blocks:
            return factors

        # Daily workload distribution
        daily_workload = defaultdict(int)
        for block in blocks:
            day = block.start_time.date()
            daily_workload[day] += block.duration_minutes

        if len(daily_workload) > 1:
            workloads = list(daily_workload.values())
            avg_workload = statistics.mean(workloads)
            workload_variance = statistics.variance(workloads) if len(workloads) > 1 else 0

            # Lower variance indicates better balance
            balance_score = 1.0 - min(1.0, workload_variance / (avg_workload ** 2))

            balance_factor = QualityFactor(
                name="daily_workload_balance",
                dimension=QualityDimension.BALANCE,
                score=balance_score,
                description=f"Workload varies by {workload_variance**0.5:.1f} minutes across days",
                actual_value=workload_variance**0.5,
                optimal_value=0.0
            )

            if workload_variance > (avg_workload * 0.5) ** 2:
                balance_factor.issues_identified.append("Uneven workload distribution across days")
                balance_factor.improvement_suggestions.append("Redistribute tasks for more even daily workload")

            factors.append(balance_factor)

        # Task priority balance
        scheduled_task_ids = {block.task_id for block in blocks}
        priority_distribution = Counter()

        for task in all_tasks:
            if task.id in scheduled_task_ids:
                priority = getattr(task, 'priority', 3)
                priority_distribution[priority] += 1

        if priority_distribution:
            # Check if there's a good mix of priorities
            priority_variety = len(priority_distribution) / 5.0  # Assuming 5 priority levels

            priority_factor = QualityFactor(
                name="priority_balance",
                dimension=QualityDimension.BALANCE,
                score=priority_variety,
                description=f"Tasks span {len(priority_distribution)} priority levels",
                actual_value=len(priority_distribution),
                optimal_value=3
            )

            factors.append(priority_factor)

        return factors

    def analyze_stability(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> List[QualityFactor]:
        """Analyze schedule stability factors."""
        factors = []

        # Buffer time analysis
        total_buffer = 0
        for i, block in enumerate(sorted(blocks, key=lambda b: b.start_time)):
            if i < len(blocks) - 1:
                next_block = sorted(blocks, key=lambda b: b.start_time)[i + 1]
                gap = (next_block.start_time - block.end_time).total_seconds() / 60
                if gap > 0:
                    total_buffer += gap

        avg_buffer = total_buffer / max(1, len(blocks) - 1)

        # Optimal buffer is 15-30 minutes between blocks
        if avg_buffer < 15:
            buffer_score = avg_buffer / 15
        elif avg_buffer > 30:
            buffer_score = 1.0 - min(1.0, (avg_buffer - 30) / 30)
        else:
            buffer_score = 1.0

        buffer_factor = QualityFactor(
            name="buffer_time_adequacy",
            dimension=QualityDimension.STABILITY,
            score=buffer_score,
            description=f"Average {avg_buffer:.1f} minutes buffer between blocks",
            actual_value=avg_buffer,
            optimal_value=22.5  # Midpoint of 15-30 range
        )

        if avg_buffer < 10:
            buffer_factor.issues_identified.append("Insufficient buffer time between tasks")
            buffer_factor.improvement_suggestions.append("Add more buffer time to handle delays")

        factors.append(buffer_factor)

        return factors
