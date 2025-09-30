"""
Constraint analysis system for identifying scheduling bottlenecks and limitations.

Provides detailed analysis of why tasks couldn't be scheduled optimally,
what constraints are most limiting, and suggestions for improvement.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.domain import Task, Todo, BusyEvent
from ..io.dto import ScheduleRequest
from ..schemas.enhanced_results import ConstraintType, ConstraintViolation
from ...core.utils.timezone_utils import TimezoneManager


class BottleneckSeverity(Enum):
    """Severity levels for scheduling bottlenecks."""
    CRITICAL = "critical"    # Prevents any scheduling
    HIGH = "high"           # Severely limits options
    MEDIUM = "medium"       # Moderately constraining
    LOW = "low"            # Minor impact


@dataclass
class ConstraintPressure:
    """Measures how much a constraint is limiting scheduling options."""
    constraint_type: ConstraintType
    affected_tasks: List[str]
    severity: BottleneckSeverity
    pressure_score: float  # 0.0 to 1.0
    description: str
    time_windows_blocked: int
    alternative_slots_eliminated: int

    # Specific constraint details
    constraint_details: Dict[str, Any] = field(default_factory=dict)

    # Impact analysis
    scheduling_impact: str = ""
    user_impact: str = ""

    # Mitigation suggestions
    mitigation_strategies: List[str] = field(default_factory=list)


@dataclass
class ResourceContention:
    """Analysis of resource conflicts and competition."""
    resource_name: str
    competing_tasks: List[str]
    contention_periods: List[Tuple[datetime, datetime]]
    resolution_strategy: str
    priority_resolution: Dict[str, int]  # task_id -> priority used

    # Metrics
    demand_vs_supply_ratio: float
    peak_contention_time: Optional[datetime]
    contention_duration_minutes: int


@dataclass
class TimeConstraintAnalysis:
    """Detailed analysis of temporal constraints and their interactions."""

    # Deadline analysis
    deadline_pressure: Dict[str, float]  # task_id -> pressure (0.0 to 1.0)
    critical_path_tasks: List[str]
    deadline_conflicts: List[Tuple[str, str]]  # (task1, task2) with conflicting deadlines

    # Availability analysis
    availability_fragmentation: float  # How fragmented the available time is
    largest_available_block: int  # In minutes
    scheduling_efficiency: float  # Actual vs theoretical optimal utilization

    # Prerequisite analysis
    dependency_chains: List[List[str]]  # Chains of dependent tasks
    circular_dependencies: List[List[str]]  # Any circular dependency loops
    longest_chain_length: int

    # Time distribution
    morning_hours_pressure: float
    afternoon_hours_pressure: float
    evening_hours_pressure: float


@dataclass
class ConstraintInteractionAnalysis:
    """Analysis of how multiple constraints interact and compound."""

    # Interaction matrix: how constraints reinforce each other
    constraint_synergies: Dict[Tuple[ConstraintType, ConstraintType], float]

    # Constraint conflict analysis
    conflicting_constraints: List[Tuple[str, str, str]]  # (task_id, constraint1, constraint2)

    # Compound effects
    compound_bottlenecks: List[str]  # Tasks affected by multiple severe constraints
    constraint_cascade_effects: Dict[str, List[str]]  # How one constraint triggers others


class ConstraintAnalyzer:
    """Analyzes scheduling constraints to identify bottlenecks and improvement opportunities."""

    def __init__(self):
        self.timezone_manager = TimezoneManager()

    def analyze_constraints(
        self,
        request: ScheduleRequest,
        scheduled_blocks: List[Any],
        unscheduled_tasks: List[str],
        busy_events: List[BusyEvent],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive constraint analysis."""

        all_tasks = self._get_all_tasks(request)

        # Analyze different constraint categories
        constraint_pressures = self._analyze_constraint_pressures(
            all_tasks, scheduled_blocks, unscheduled_tasks, busy_events, preferences
        )

        resource_contentions = self._analyze_resource_contention(
            all_tasks, scheduled_blocks, busy_events
        )

        time_analysis = self._analyze_time_constraints(
            all_tasks, scheduled_blocks, unscheduled_tasks, busy_events
        )

        interaction_analysis = self._analyze_constraint_interactions(
            all_tasks, constraint_pressures
        )

        # Generate bottleneck summary
        bottleneck_summary = self._generate_bottleneck_summary(
            constraint_pressures, resource_contentions, time_analysis
        )

        # Generate improvement recommendations
        recommendations = self._generate_recommendations(
            constraint_pressures, time_analysis, interaction_analysis
        )

        return {
            "constraint_pressures": constraint_pressures,
            "resource_contentions": resource_contentions,
            "time_analysis": time_analysis,
            "interaction_analysis": interaction_analysis,
            "bottleneck_summary": bottleneck_summary,
            "recommendations": recommendations,
            "overall_constraint_score": self._calculate_overall_constraint_score(constraint_pressures)
        }

    def _get_all_tasks(self, request: ScheduleRequest) -> List[Task]:
        """Extract all tasks from the scheduling request."""
        all_tasks = []

        # Add regular tasks
        if hasattr(request, 'tasks') and request.tasks:
            all_tasks.extend(request.tasks)

        # Add todos converted to tasks
        if hasattr(request, 'todos') and request.todos:
            for todo in request.todos:
                # Convert todo to task-like object for analysis
                task = Task(
                    id=todo.id,
                    title=todo.title,
                    description=todo.description or "",
                    duration_minutes=getattr(todo, 'estimated_duration_minutes', 30),
                    deadline=getattr(todo, 'due_date', None),
                    priority=getattr(todo, 'priority', 3),
                    created_at=todo.created_at,
                    updated_at=todo.updated_at,
                    user_id=todo.user_id
                )
                all_tasks.append(task)

        return all_tasks

    def _analyze_constraint_pressures(
        self,
        tasks: List[Task],
        scheduled_blocks: List[Any],
        unscheduled_tasks: List[str],
        busy_events: List[BusyEvent],
        preferences: Dict[str, Any]
    ) -> List[ConstraintPressure]:
        """Analyze pressure from different constraint types."""
        pressures = []

        # Deadline pressure analysis
        deadline_pressure = self._analyze_deadline_pressure(tasks, unscheduled_tasks)
        if deadline_pressure:
            pressures.append(deadline_pressure)

        # Availability pressure analysis
        availability_pressure = self._analyze_availability_pressure(tasks, busy_events)
        if availability_pressure:
            pressures.append(availability_pressure)

        # Prerequisite pressure analysis
        prereq_pressure = self._analyze_prerequisite_pressure(tasks, scheduled_blocks, unscheduled_tasks)
        if prereq_pressure:
            pressures.append(prereq_pressure)

        # Preference pressure analysis
        preference_pressure = self._analyze_preference_pressure(tasks, preferences)
        if preference_pressure:
            pressures.append(preference_pressure)

        return pressures

    def _analyze_deadline_pressure(self, tasks: List[Task], unscheduled_tasks: List[str]) -> Optional[ConstraintPressure]:
        """Analyze pressure from deadline constraints."""
        now = self.timezone_manager.get_user_now()
        deadline_tasks = [t for t in tasks if t.deadline and t.id in unscheduled_tasks]

        if not deadline_tasks:
            return None

        # Calculate deadline pressure for each task
        high_pressure_tasks = []
        total_pressure = 0.0

        for task in deadline_tasks:
            if task.deadline:
                time_until_deadline = (task.deadline - now).total_seconds() / 3600  # hours
                required_time = task.duration_minutes / 60  # hours

                # Pressure increases as deadline approaches relative to required time
                if time_until_deadline <= 0:
                    pressure = 1.0  # Past deadline
                elif time_until_deadline < required_time:
                    pressure = 0.9  # Not enough time
                elif time_until_deadline < required_time * 2:
                    pressure = 0.7  # Very tight
                elif time_until_deadline < required_time * 4:
                    pressure = 0.5  # Moderate pressure
                else:
                    pressure = 0.2  # Low pressure

                total_pressure += pressure
                if pressure >= 0.7:
                    high_pressure_tasks.append(task.id)

        avg_pressure = total_pressure / len(deadline_tasks)
        severity = self._pressure_to_severity(avg_pressure)

        mitigation_strategies = []
        if high_pressure_tasks:
            mitigation_strategies.extend([
                "Consider extending deadlines for high-pressure tasks",
                "Break large tasks into smaller chunks",
                "Reschedule lower-priority activities",
                "Focus on critical path tasks first"
            ])

        return ConstraintPressure(
            constraint_type=ConstraintType.DEADLINE,
            affected_tasks=[t.id for t in deadline_tasks],
            severity=severity,
            pressure_score=avg_pressure,
            description=f"Deadline pressure affecting {len(deadline_tasks)} tasks",
            time_windows_blocked=0,  # Deadlines don't block windows directly
            alternative_slots_eliminated=len(high_pressure_tasks) * 10,  # Estimated
            constraint_details={"high_pressure_tasks": high_pressure_tasks},
            scheduling_impact=f"Forces scheduling of {len(high_pressure_tasks)} urgent tasks",
            user_impact="May require working in suboptimal time slots",
            mitigation_strategies=mitigation_strategies
        )

    def _analyze_availability_pressure(self, tasks: List[Task], busy_events: List[BusyEvent]) -> Optional[ConstraintPressure]:
        """Analyze pressure from availability constraints."""
        if not busy_events:
            return None

        # Calculate total busy time and fragmentation
        total_busy_minutes = sum(
            int((event.end - event.start).total_seconds() / 60)
            for event in busy_events
        )

        # Estimate available time in a typical day (assuming 16 waking hours)
        total_waking_minutes = 16 * 60
        availability_ratio = 1.0 - (total_busy_minutes / total_waking_minutes)

        # Calculate fragmentation (number of separate busy periods)
        fragmentation_score = len(busy_events) / 10.0  # Normalize

        pressure_score = max(0.0, min(1.0, 1.0 - availability_ratio + fragmentation_score))
        severity = self._pressure_to_severity(pressure_score)

        affected_tasks = [t.id for t in tasks]  # All tasks affected by availability

        mitigation_strategies = [
            "Consider shorter time blocks for better fitting",
            "Look for gaps between existing commitments",
            "Evaluate if some existing commitments can be moved"
        ]

        if fragmentation_score > 0.5:
            mitigation_strategies.append("Try to consolidate fragmented time periods")

        return ConstraintPressure(
            constraint_type=ConstraintType.AVAILABILITY,
            affected_tasks=affected_tasks,
            severity=severity,
            pressure_score=pressure_score,
            description=f"Limited availability with {len(busy_events)} existing commitments",
            time_windows_blocked=len(busy_events),
            alternative_slots_eliminated=int(total_busy_minutes / 30),  # Estimate 30-min slots
            constraint_details={
                "total_busy_minutes": total_busy_minutes,
                "fragmentation_score": fragmentation_score,
                "availability_ratio": availability_ratio
            },
            scheduling_impact="Reduces available time windows significantly",
            user_impact="May need to work around existing commitments",
            mitigation_strategies=mitigation_strategies
        )

    def _analyze_prerequisite_pressure(
        self,
        tasks: List[Task],
        scheduled_blocks: List[Any],
        unscheduled_tasks: List[str]
    ) -> Optional[ConstraintPressure]:
        """Analyze pressure from prerequisite constraints."""
        # Find tasks with prerequisites
        prerequisite_tasks = []
        blocked_tasks = []

        scheduled_task_ids = {block.task_id for block in scheduled_blocks}

        for task in tasks:
            if hasattr(task, 'prerequisites') and task.prerequisites:
                prerequisite_tasks.append(task.id)

                # Check if any prerequisites are unscheduled
                unscheduled_prereqs = set(task.prerequisites) & set(unscheduled_tasks)
                if unscheduled_prereqs and task.id in unscheduled_tasks:
                    blocked_tasks.append(task.id)

        if not prerequisite_tasks:
            return None

        # Calculate pressure based on blocking
        pressure_score = len(blocked_tasks) / len(prerequisite_tasks) if prerequisite_tasks else 0.0
        severity = self._pressure_to_severity(pressure_score)

        mitigation_strategies = []
        if blocked_tasks:
            mitigation_strategies.extend([
                "Prioritize prerequisite tasks for scheduling",
                "Consider parallel work where dependencies allow",
                "Break down tasks to reduce dependencies",
                "Re-evaluate if all prerequisites are truly necessary"
            ])

        return ConstraintPressure(
            constraint_type=ConstraintType.PREREQUISITE,
            affected_tasks=prerequisite_tasks,
            severity=severity,
            pressure_score=pressure_score,
            description=f"Prerequisite dependencies affecting {len(prerequisite_tasks)} tasks",
            time_windows_blocked=0,  # Prerequisites don't block specific windows
            alternative_slots_eliminated=len(blocked_tasks) * 5,  # Estimated
            constraint_details={
                "blocked_tasks": blocked_tasks,
                "dependency_count": len(prerequisite_tasks)
            },
            scheduling_impact=f"Blocks scheduling of {len(blocked_tasks)} dependent tasks",
            user_impact="Creates ordering constraints on task execution",
            mitigation_strategies=mitigation_strategies
        )

    def _analyze_preference_pressure(self, tasks: List[Task], preferences: Dict[str, Any]) -> Optional[ConstraintPressure]:
        """Analyze pressure from user preferences."""
        if not preferences:
            return None

        # Analyze common preference conflicts
        preference_conflicts = 0
        affected_tasks = []

        # Check for time-of-day preferences
        morning_tasks = [t.id for t in tasks if getattr(t, 'preferred_time', None) == 'morning']
        afternoon_tasks = [t.id for t in tasks if getattr(t, 'preferred_time', None) == 'afternoon']
        evening_tasks = [t.id for t in tasks if getattr(t, 'preferred_time', None) == 'evening']

        # Simple conflict detection: too many tasks preferring same time
        time_slot_capacity = 4  # Assume 4 hours per time slot
        avg_task_duration = sum(t.duration_minutes for t in tasks) / len(tasks) / 60 if tasks else 1

        conflicts = 0
        if len(morning_tasks) * avg_task_duration > time_slot_capacity:
            conflicts += len(morning_tasks) - int(time_slot_capacity / avg_task_duration)
            affected_tasks.extend(morning_tasks)

        if len(afternoon_tasks) * avg_task_duration > time_slot_capacity:
            conflicts += len(afternoon_tasks) - int(time_slot_capacity / avg_task_duration)
            affected_tasks.extend(afternoon_tasks)

        if len(evening_tasks) * avg_task_duration > time_slot_capacity:
            conflicts += len(evening_tasks) - int(time_slot_capacity / avg_task_duration)
            affected_tasks.extend(evening_tasks)

        if conflicts == 0:
            return None

        pressure_score = min(1.0, conflicts / len(tasks))
        severity = self._pressure_to_severity(pressure_score)

        return ConstraintPressure(
            constraint_type=ConstraintType.PREFERENCE,
            affected_tasks=list(set(affected_tasks)),
            severity=severity,
            pressure_score=pressure_score,
            description=f"Time preference conflicts for {len(set(affected_tasks))} tasks",
            time_windows_blocked=0,
            alternative_slots_eliminated=conflicts * 2,
            constraint_details={"preference_conflicts": conflicts},
            scheduling_impact="May force tasks into non-preferred time slots",
            user_impact="Some tasks may be scheduled outside preferred times",
            mitigation_strategies=[
                "Consider more flexible time preferences",
                "Spread tasks across different time periods",
                "Identify which preferences are most important"
            ]
        )

    def _analyze_resource_contention(
        self,
        tasks: List[Task],
        scheduled_blocks: List[Any],
        busy_events: List[BusyEvent]
    ) -> List[ResourceContention]:
        """Analyze resource conflicts and competition."""
        # For now, focus on time as the primary resource
        # Future: add analysis for other resources (location, equipment, etc.)

        contentions = []

        # Analyze time resource contention
        time_contention = self._analyze_time_resource_contention(tasks, scheduled_blocks, busy_events)
        if time_contention:
            contentions.append(time_contention)

        return contentions

    def _analyze_time_resource_contention(
        self,
        tasks: List[Task],
        scheduled_blocks: List[Any],
        busy_events: List[BusyEvent]
    ) -> Optional[ResourceContention]:
        """Analyze contention for time resources."""
        if not tasks:
            return None

        # Calculate total demand vs supply
        total_demand_minutes = sum(t.duration_minutes for t in tasks)

        # Estimate available supply (assuming 8 productive hours per day)
        available_hours_per_day = 8
        planning_horizon_days = 7  # Assume week-long horizon
        total_supply_minutes = available_hours_per_day * 60 * planning_horizon_days

        # Subtract busy time
        busy_minutes = sum(
            int((event.end - event.start).total_seconds() / 60)
            for event in busy_events
        )

        effective_supply_minutes = total_supply_minutes - busy_minutes
        demand_vs_supply_ratio = total_demand_minutes / max(1, effective_supply_minutes)

        # Identify peak contention periods
        peak_contention_time = None
        if busy_events:
            # Find the busiest day (simplified)
            peak_contention_time = min(busy_events, key=lambda e: e.start).start

        resolution_strategy = "time_based_prioritization"
        if demand_vs_supply_ratio > 1.0:
            resolution_strategy = "demand_reduction_required"
        elif demand_vs_supply_ratio > 0.8:
            resolution_strategy = "tight_scheduling_required"

        return ResourceContention(
            resource_name="time",
            competing_tasks=[t.id for t in tasks],
            contention_periods=[(event.start, event.end) for event in busy_events],
            resolution_strategy=resolution_strategy,
            priority_resolution={t.id: getattr(t, 'priority', 3) for t in tasks},
            demand_vs_supply_ratio=demand_vs_supply_ratio,
            peak_contention_time=peak_contention_time,
            contention_duration_minutes=busy_minutes
        )

    def _analyze_time_constraints(
        self,
        tasks: List[Task],
        scheduled_blocks: List[Any],
        unscheduled_tasks: List[str],
        busy_events: List[BusyEvent]
    ) -> TimeConstraintAnalysis:
        """Perform detailed time constraint analysis."""
        now = self.timezone_manager.get_user_now()

        # Deadline pressure analysis
        deadline_pressure = {}
        critical_path_tasks = []

        for task in tasks:
            if task.deadline:
                time_until_deadline = (task.deadline - now).total_seconds() / 3600
                required_time = task.duration_minutes / 60
                pressure = min(1.0, required_time / max(0.1, time_until_deadline))
                deadline_pressure[task.id] = pressure

                if pressure > 0.8:
                    critical_path_tasks.append(task.id)

        # Availability analysis
        total_available_time = 16 * 60  # 16 hours in minutes
        busy_time = sum(int((event.end - event.start).total_seconds() / 60) for event in busy_events)
        availability_fragmentation = len(busy_events) / 10.0  # Normalized fragmentation

        # Find largest available block
        largest_available_block = self._find_largest_available_block(busy_events)

        # Calculate scheduling efficiency
        scheduled_time = sum(getattr(block, 'duration_minutes', 0) for block in scheduled_blocks)
        total_task_time = sum(t.duration_minutes for t in tasks)
        scheduling_efficiency = scheduled_time / max(1, total_task_time)

        # Time distribution pressure (simplified)
        morning_pressure = len([t for t in tasks if getattr(t, 'preferred_time', None) == 'morning']) / max(1, len(tasks))
        afternoon_pressure = len([t for t in tasks if getattr(t, 'preferred_time', None) == 'afternoon']) / max(1, len(tasks))
        evening_pressure = len([t for t in tasks if getattr(t, 'preferred_time', None) == 'evening']) / max(1, len(tasks))

        return TimeConstraintAnalysis(
            deadline_pressure=deadline_pressure,
            critical_path_tasks=critical_path_tasks,
            deadline_conflicts=[],  # Simplified for now
            availability_fragmentation=availability_fragmentation,
            largest_available_block=largest_available_block,
            scheduling_efficiency=scheduling_efficiency,
            dependency_chains=[],  # Would need prerequisite analysis
            circular_dependencies=[],
            longest_chain_length=0,
            morning_hours_pressure=morning_pressure,
            afternoon_hours_pressure=afternoon_pressure,
            evening_hours_pressure=evening_pressure
        )

    def _find_largest_available_block(self, busy_events: List[BusyEvent]) -> int:
        """Find the largest continuous available time block."""
        if not busy_events:
            return 8 * 60  # 8 hours if no conflicts

        # Sort events by start time
        sorted_events = sorted(busy_events, key=lambda e: e.start)

        # Find gaps between events
        largest_gap = 0

        for i in range(len(sorted_events) - 1):
            gap_start = sorted_events[i].end
            gap_end = sorted_events[i + 1].start
            gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
            largest_gap = max(largest_gap, gap_minutes)

        return largest_gap

    def _analyze_constraint_interactions(
        self,
        tasks: List[Task],
        constraint_pressures: List[ConstraintPressure]
    ) -> ConstraintInteractionAnalysis:
        """Analyze how constraints interact and compound."""
        # Simplified interaction analysis
        constraint_synergies = {}
        conflicting_constraints = []
        compound_bottlenecks = []

        # Find tasks affected by multiple high-pressure constraints
        high_pressure_constraints = [cp for cp in constraint_pressures if cp.severity in [BottleneckSeverity.HIGH, BottleneckSeverity.CRITICAL]]

        task_constraint_count = {}
        for constraint in high_pressure_constraints:
            for task_id in constraint.affected_tasks:
                task_constraint_count[task_id] = task_constraint_count.get(task_id, 0) + 1

        compound_bottlenecks = [task_id for task_id, count in task_constraint_count.items() if count > 1]

        return ConstraintInteractionAnalysis(
            constraint_synergies=constraint_synergies,
            conflicting_constraints=conflicting_constraints,
            compound_bottlenecks=compound_bottlenecks,
            constraint_cascade_effects={}
        )

    def _generate_bottleneck_summary(
        self,
        constraint_pressures: List[ConstraintPressure],
        resource_contentions: List[ResourceContention],
        time_analysis: TimeConstraintAnalysis
    ) -> Dict[str, Any]:
        """Generate a summary of the main bottlenecks."""
        # Find the most severe constraints
        critical_constraints = [cp for cp in constraint_pressures if cp.severity == BottleneckSeverity.CRITICAL]
        high_constraints = [cp for cp in constraint_pressures if cp.severity == BottleneckSeverity.HIGH]

        primary_bottleneck = None
        if critical_constraints:
            primary_bottleneck = max(critical_constraints, key=lambda cp: cp.pressure_score)
        elif high_constraints:
            primary_bottleneck = max(high_constraints, key=lambda cp: cp.pressure_score)

        # Overall constraint severity
        avg_pressure = sum(cp.pressure_score for cp in constraint_pressures) / max(1, len(constraint_pressures))

        return {
            "primary_bottleneck": primary_bottleneck.constraint_type.value if primary_bottleneck else None,
            "critical_constraints_count": len(critical_constraints),
            "high_constraints_count": len(high_constraints),
            "overall_pressure_score": avg_pressure,
            "most_constrained_tasks": time_analysis.critical_path_tasks,
            "resource_contention_level": "high" if resource_contentions and resource_contentions[0].demand_vs_supply_ratio > 1.0 else "moderate"
        }

    def _generate_recommendations(
        self,
        constraint_pressures: List[ConstraintPressure],
        time_analysis: TimeConstraintAnalysis,
        interaction_analysis: ConstraintInteractionAnalysis
    ) -> List[str]:
        """Generate actionable recommendations for improving scheduling."""
        recommendations = []

        # General recommendations based on constraint types
        constraint_types = {cp.constraint_type for cp in constraint_pressures}

        if ConstraintType.DEADLINE in constraint_types:
            recommendations.append("Consider extending deadlines for non-critical tasks")
            recommendations.append("Break large tasks into smaller, manageable chunks")

        if ConstraintType.AVAILABILITY in constraint_types:
            recommendations.append("Look for opportunities to reschedule existing commitments")
            recommendations.append("Consider shorter time blocks for better calendar fitting")

        if ConstraintType.PREREQUISITE in constraint_types:
            recommendations.append("Prioritize prerequisite tasks to unblock dependent work")
            recommendations.append("Evaluate if all dependencies are truly necessary")

        # Recommendations based on time analysis
        if time_analysis.availability_fragmentation > 0.7:
            recommendations.append("Try to consolidate fragmented time periods")

        if time_analysis.scheduling_efficiency < 0.5:
            recommendations.append("Consider more flexible task durations")

        # Recommendations for compound bottlenecks
        if interaction_analysis.compound_bottlenecks:
            recommendations.append("Focus on tasks affected by multiple constraints first")

        return recommendations

    def _pressure_to_severity(self, pressure_score: float) -> BottleneckSeverity:
        """Convert pressure score to severity level."""
        if pressure_score >= 0.8:
            return BottleneckSeverity.CRITICAL
        elif pressure_score >= 0.6:
            return BottleneckSeverity.HIGH
        elif pressure_score >= 0.4:
            return BottleneckSeverity.MEDIUM
        else:
            return BottleneckSeverity.LOW

    def _calculate_overall_constraint_score(self, constraint_pressures: List[ConstraintPressure]) -> float:
        """Calculate overall constraint pressure score."""
        if not constraint_pressures:
            return 0.0

        # Weight by severity
        severity_weights = {
            BottleneckSeverity.CRITICAL: 1.0,
            BottleneckSeverity.HIGH: 0.8,
            BottleneckSeverity.MEDIUM: 0.6,
            BottleneckSeverity.LOW: 0.4
        }

        weighted_sum = sum(
            cp.pressure_score * severity_weights[cp.severity]
            for cp in constraint_pressures
        )
        total_weight = sum(severity_weights[cp.severity] for cp in constraint_pressures)

        return weighted_sum / max(1, total_weight)

