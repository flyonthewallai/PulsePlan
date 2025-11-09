"""
User experience analysis for schedule quality assessment.

Analyzes cognitive load, stress, flow, and usability factors.
"""

from typing import List
from collections import defaultdict
import statistics

from ...core.domain import Task, ScheduleBlock, BusyEvent
from .models import QualityFactor, QualityDimension, UserExperienceAnalysis


class UXAnalyzer:
    """Analyzes user experience aspects of schedules."""

    def analyze_user_experience(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> UserExperienceAnalysis:
        """Analyze user experience aspects of the schedule."""

        # Cognitive load assessment
        cognitive_load = self._assess_cognitive_load(blocks, all_tasks)

        # Stress indicators
        stress_indicators = self._identify_stress_indicators(blocks, all_tasks, busy_events)

        # Flow opportunities
        flow_opportunities = len([b for b in blocks if b.duration_minutes >= 90])

        # Convenience factors
        travel_efficiency = 0.8  # Placeholder - would analyze location changes
        preparation_time = self._assess_preparation_time(blocks, busy_events)
        buffer_time = self._assess_buffer_time(blocks, busy_events)

        # Psychological factors
        variety_balance = self._assess_variety_balance(blocks, all_tasks)
        accomplishment_potential = self._assess_accomplishment_potential(blocks, all_tasks)
        flexibility_preservation = self._assess_flexibility_preservation(blocks, busy_events)

        # Practical considerations
        implementation_difficulty = self._assess_implementation_difficulty(blocks)
        discipline_level = self._assess_required_discipline(blocks, all_tasks)
        recovery_options = self._count_recovery_options(blocks, busy_events)

        return UserExperienceAnalysis(
            cognitive_load_score=cognitive_load,
            stress_indicators=stress_indicators,
            flow_opportunities=flow_opportunities,
            travel_efficiency=travel_efficiency,
            preparation_time_adequacy=preparation_time,
            buffer_time_adequacy=buffer_time,
            variety_balance=variety_balance,
            accomplishment_potential=accomplishment_potential,
            flexibility_preservation=flexibility_preservation,
            implementation_difficulty=implementation_difficulty,
            required_discipline_level=discipline_level,
            failure_recovery_options=recovery_options
        )

    def analyze_usability(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> List[QualityFactor]:
        """Analyze schedule usability factors."""
        factors = []

        if not blocks:
            return factors

        # Implementation complexity
        complexity_score = 1.0
        complexity_issues = []

        # Too many context switches reduce usability
        if len(blocks) > 8:
            complexity_score *= 0.8
            complexity_issues.append("High number of scheduled blocks may be overwhelming")

        # Very short blocks are harder to implement
        short_blocks = [b for b in blocks if b.duration_minutes < 30]
        if len(short_blocks) > len(blocks) * 0.3:
            complexity_score *= 0.7
            complexity_issues.append("Many short blocks may be difficult to execute effectively")

        complexity_factor = QualityFactor(
            name="implementation_complexity",
            dimension=QualityDimension.USABILITY,
            score=complexity_score,
            description=f"Schedule has {len(blocks)} blocks, {len(short_blocks)} under 30 minutes",
            issues_identified=complexity_issues
        )

        if complexity_score < 0.7:
            complexity_factor.improvement_suggestions.append("Simplify schedule by consolidating blocks")

        factors.append(complexity_factor)

        return factors

    def _assess_cognitive_load(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess cognitive load of the schedule."""
        # More blocks = higher cognitive load
        block_load = min(1.0, len(blocks) / 10.0)

        # Frequent context switches = higher load
        context_switches = max(0, len(blocks) - 1)
        switch_load = min(1.0, context_switches / 8.0)

        return (block_load + switch_load) / 2

    def _identify_stress_indicators(
        self,
        blocks: List[ScheduleBlock],
        all_tasks: List[Task],
        busy_events: List[BusyEvent]
    ) -> List[str]:
        """Identify potential stress indicators in the schedule."""
        indicators = []

        # Back-to-back scheduling
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            if gap < 5:
                indicators.append("Back-to-back scheduling with no breaks")
                break

        # Overloaded days
        daily_load = defaultdict(int)
        for block in blocks:
            daily_load[block.start_time.date()] += block.duration_minutes

        for day, minutes in daily_load.items():
            if minutes > 8 * 60:  # More than 8 hours
                indicators.append(f"Overloaded day: {day}")

        # Late evening work
        late_blocks = [b for b in blocks if b.start_time.hour >= 20]
        if late_blocks:
            indicators.append("Work scheduled late in the evening")

        return indicators

    def _assess_preparation_time(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> float:
        """Assess adequacy of preparation time."""
        # Simplified assessment - would be more sophisticated in practice
        return 0.7

    def _assess_buffer_time(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> float:
        """Assess adequacy of buffer time between activities."""
        # Calculate average gap between blocks
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        gaps = []

        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            gaps.append(gap)

        if not gaps:
            return 1.0

        avg_gap = statistics.mean(gaps)
        # 15-30 minutes is ideal buffer
        if 15 <= avg_gap <= 30:
            return 1.0
        elif avg_gap < 15:
            return avg_gap / 15
        else:
            return max(0.0, 1.0 - (avg_gap - 30) / 60)

    def _assess_variety_balance(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess variety and balance in scheduled activities."""
        # Simplified - would categorize tasks by type in practice
        return 0.6

    def _assess_accomplishment_potential(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess potential for feeling accomplished."""
        # More completed tasks = higher accomplishment potential
        completion_score = len(blocks) / max(1, len(all_tasks))

        # Longer blocks allow for deeper work and accomplishment
        avg_duration = statistics.mean([b.duration_minutes for b in blocks]) if blocks else 0
        depth_score = min(1.0, avg_duration / 90)  # 90 minutes for deep work

        return (completion_score + depth_score) / 2

    def _assess_flexibility_preservation(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> float:
        """Assess how much flexibility remains in the schedule."""
        total_scheduled = sum(b.duration_minutes for b in blocks)
        total_busy = sum(int((e.end - e.start).total_seconds() / 60) for e in busy_events)
        total_committed = total_scheduled + total_busy

        # Assume 16-hour waking day
        available_time = 16 * 60
        flexibility_ratio = 1.0 - (total_committed / available_time)

        return max(0.0, flexibility_ratio)

    def _assess_implementation_difficulty(self, blocks: List[ScheduleBlock]) -> float:
        """Assess how difficult the schedule would be to implement."""
        difficulty = 0.0

        # More blocks = higher difficulty
        difficulty += min(0.3, len(blocks) / 20)

        # Very short blocks = higher difficulty
        short_blocks = len([b for b in blocks if b.duration_minutes < 30])
        difficulty += min(0.3, short_blocks / len(blocks)) if blocks else 0

        # Tight scheduling = higher difficulty
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        tight_gaps = 0
        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            if gap < 10:
                tight_gaps += 1

        if blocks:
            difficulty += min(0.4, tight_gaps / (len(blocks) - 1)) if len(blocks) > 1 else 0

        return difficulty

    def _assess_required_discipline(self, blocks: List[ScheduleBlock], all_tasks: List[Task]) -> float:
        """Assess level of discipline required to follow the schedule."""
        # More precise timing = higher discipline required
        precision_requirement = len(blocks) / 10.0

        # Early morning starts = higher discipline
        early_blocks = len([b for b in blocks if b.start_time.hour < 7])
        early_discipline = early_blocks / max(1, len(blocks))

        return min(1.0, (precision_requirement + early_discipline) / 2)

    def _count_recovery_options(self, blocks: List[ScheduleBlock], busy_events: List[BusyEvent]) -> int:
        """Count options for recovering if schedule goes off track."""
        # Simplified - count gaps that could be used for catch-up
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)
        recovery_options = 0

        for i in range(len(sorted_blocks) - 1):
            gap = (sorted_blocks[i+1].start_time - sorted_blocks[i].end_time).total_seconds() / 60
            if gap >= 30:  # 30+ minute gaps can be used for recovery
                recovery_options += 1

        return recovery_options
