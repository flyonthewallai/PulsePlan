"""
Intelligent Task Prioritization System
Dynamic priority adjustment, workload balancing, and procrastination detection
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from ..core.domain import Task, Priority
from ..monitoring.smart_assistant import TaskComplexityProfile

logger = logging.getLogger(__name__)


class PriorityReason(Enum):
    """Reasons for priority adjustments"""
    DEADLINE_APPROACHING = "deadline_approaching"
    DEPENDENCY_BLOCKER = "dependency_blocker"
    WORKLOAD_BALANCING = "workload_balancing"
    PROCRASTINATION_RISK = "procrastination_risk"
    ENERGY_OPPORTUNITY = "energy_opportunity"
    TIME_AVAILABILITY = "time_availability"
    CONTEXT_SWITCH_OPTIMIZATION = "context_switch_optimization"
    COURSE_FAIRNESS = "course_fairness"


@dataclass
class PriorityAdjustment:
    """Represents a priority adjustment with reasoning"""
    task_id: str
    old_priority: Priority
    new_priority: Priority
    adjustment_score: float  # -1.0 to 1.0 (negative = lower priority, positive = higher)
    reason: PriorityReason
    explanation: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkloadMetrics:
    """Workload analysis for a time period"""
    period_start: datetime
    period_end: datetime
    total_estimated_minutes: int
    total_available_minutes: int
    overcommitment_ratio: float  # >1.0 means overcommitted
    high_priority_minutes: int
    medium_priority_minutes: int
    low_priority_minutes: int
    course_distribution: Dict[str, int]  # course_id -> minutes
    complexity_distribution: Dict[str, int]  # complexity_level -> minutes


@dataclass
class ProcrastinationIndicator:
    """Indicators that a task might be procrastinated"""
    task_id: str
    risk_score: float  # 0.0 to 1.0
    indicators: List[str]
    postponement_history: List[datetime]
    completion_avoidance_score: float
    complexity_anxiety_score: float
    suggested_strategies: List[str]


class IntelligentPrioritizer:
    """
    Intelligent task prioritization system that dynamically adjusts priorities
    based on deadlines, dependencies, workload, and procrastination patterns
    """
    
    def __init__(self):
        self.priority_weights = {
            'deadline_urgency': 0.25,
            'dependency_impact': 0.20,
            'workload_balance': 0.15,
            'procrastination_risk': 0.15,
            'energy_alignment': 0.10,
            'context_efficiency': 0.10,
            'course_fairness': 0.05
        }
        
        # Historical tracking for learning
        self.priority_history: Dict[str, List[PriorityAdjustment]] = {}
        self.workload_history: List[WorkloadMetrics] = []
        self.procrastination_patterns: Dict[str, List[ProcrastinationIndicator]] = {}
    
    async def analyze_and_adjust_priorities(
        self,
        tasks: List[Task],
        task_profiles: Dict[str, TaskComplexityProfile],
        user_context: Dict[str, Any],
        time_horizon_days: int = 7
    ) -> Tuple[List[Task], List[PriorityAdjustment]]:
        """
        Analyze tasks and dynamically adjust priorities based on multiple factors
        """
        adjustments = []
        adjusted_tasks = tasks.copy()
        
        # 1. Analyze current workload
        workload_metrics = await self._analyze_workload(tasks, time_horizon_days)
        
        # 2. Detect procrastination risks
        procrastination_risks = await self._detect_procrastination_risks(
            tasks, task_profiles, user_context
        )
        
        # 3. Analyze dependencies and blocking relationships
        dependency_impacts = self._analyze_dependency_impacts(tasks)
        
        # 4. Calculate deadline urgency scores
        urgency_scores = self._calculate_deadline_urgency(tasks)
        
        # 5. Assess workload balance needs
        balance_adjustments = self._assess_workload_balance(tasks, workload_metrics)
        
        # 6. Consider energy alignment opportunities
        energy_adjustments = await self._assess_energy_alignment_opportunities(
            tasks, task_profiles, user_context
        )
        
        # 7. Apply all adjustments
        for task in adjusted_tasks:
            adjustment = self._calculate_priority_adjustment(
                task,
                urgency_scores.get(task.id, 0),
                dependency_impacts.get(task.id, 0),
                balance_adjustments.get(task.id, 0),
                procrastination_risks.get(task.id, ProcrastinationIndicator(task.id, 0.0, [], [], 0.0, 0.0, [])),
                energy_adjustments.get(task.id, 0),
                task_profiles.get(task.id)
            )
            
            if adjustment and abs(adjustment.adjustment_score) > 0.1:  # Significant adjustment
                # Apply the adjustment
                old_weight = self._priority_to_weight(task.weight)
                new_weight = old_weight + adjustment.adjustment_score
                task.weight = max(0.1, min(5.0, new_weight))
                
                adjustments.append(adjustment)
        
        # 8. Apply course fairness balancing
        adjusted_tasks = self._apply_course_fairness_balancing(adjusted_tasks, workload_metrics)
        
        # 9. Store history for learning
        self._store_adjustment_history(adjustments)
        
        logger.info(f"Applied {len(adjustments)} priority adjustments")
        
        return adjusted_tasks, adjustments
    
    async def detect_overcommitment(
        self, tasks: List[Task], available_hours: Dict[str, int], horizon_days: int = 7
    ) -> Dict[str, Any]:
        """
        Detect overcommitment and suggest workload rebalancing
        """
        workload_metrics = await self._analyze_workload(tasks, horizon_days)
        
        overcommitment_analysis = {
            'is_overcommitted': workload_metrics.overcommitment_ratio > 1.1,
            'overcommitment_ratio': workload_metrics.overcommitment_ratio,
            'excess_hours': max(0, workload_metrics.total_estimated_minutes - workload_metrics.total_available_minutes) / 60,
            'workload_metrics': workload_metrics,
            'rebalancing_suggestions': []
        }
        
        if overcommitment_analysis['is_overcommitted']:
            suggestions = self._generate_rebalancing_suggestions(tasks, workload_metrics)
            overcommitment_analysis['rebalancing_suggestions'] = suggestions
        
        return overcommitment_analysis
    
    async def suggest_procrastination_strategies(
        self, task_id: str, user_context: Dict[str, Any]
    ) -> List[str]:
        """
        Suggest strategies to overcome procrastination for a specific task
        """
        if task_id not in self.procrastination_patterns:
            return []
        
        latest_indicator = self.procrastination_patterns[task_id][-1]
        
        strategies = []
        
        # High complexity anxiety - break down task
        if latest_indicator.complexity_anxiety_score > 0.7:
            strategies.extend([
                "Break this task into smaller, 15-30 minute subtasks",
                "Start with the easiest part to build momentum",
                "Use the '2-minute rule' - commit to just 2 minutes to get started"
            ])
        
        # High avoidance score - address resistance
        if latest_indicator.completion_avoidance_score > 0.6:
            strategies.extend([
                "Schedule this task during your peak energy hours",
                "Pair with a reward after completion",
                "Find an accountability partner or body doubling session",
                "Change your environment - try a different location"
            ])
        
        # Frequent postponements - structural changes
        if len(latest_indicator.postponement_history) > 3:
            strategies.extend([
                "Block dedicated time slots that you cannot reschedule",
                "Set up external commitments that depend on this task",
                "Use time-boxing: set a timer for focused work periods"
            ])
        
        # Add task-specific strategies
        strategies.extend(latest_indicator.suggested_strategies)
        
        return list(set(strategies))  # Remove duplicates
    
    def get_workload_distribution(
        self, tasks: List[Task], group_by: str = "priority"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get workload distribution analysis grouped by various factors
        """
        distribution = {}
        
        if group_by == "priority":
            priority_groups = {"low": [], "normal": [], "high": [], "critical": []}
            for task in tasks:
                priority = getattr(task, 'priority', 'normal')
                if priority in priority_groups:
                    priority_groups[priority].append(task)
            
            for priority, group_tasks in priority_groups.items():
                distribution[priority] = {
                    'count': len(group_tasks),
                    'total_minutes': sum(task.estimated_minutes for task in group_tasks),
                    'avg_minutes': sum(task.estimated_minutes for task in group_tasks) / max(1, len(group_tasks))
                }
        
        elif group_by == "course":
            course_groups = {}
            for task in tasks:
                course_id = task.course_id or "uncategorized"
                if course_id not in course_groups:
                    course_groups[course_id] = []
                course_groups[course_id].append(task)
            
            for course_id, group_tasks in course_groups.items():
                distribution[course_id] = {
                    'count': len(group_tasks),
                    'total_minutes': sum(task.estimated_minutes for task in group_tasks),
                    'avg_minutes': sum(task.estimated_minutes for task in group_tasks) / max(1, len(group_tasks))
                }
        
        elif group_by == "deadline":
            now = datetime.now()
            deadline_groups = {
                "overdue": [],
                "this_week": [],
                "next_week": [],
                "later": [],
                "no_deadline": []
            }
            
            for task in tasks:
                if not task.deadline:
                    deadline_groups["no_deadline"].append(task)
                elif task.deadline < now:
                    deadline_groups["overdue"].append(task)
                elif task.deadline < now + timedelta(days=7):
                    deadline_groups["this_week"].append(task)
                elif task.deadline < now + timedelta(days=14):
                    deadline_groups["next_week"].append(task)
                else:
                    deadline_groups["later"].append(task)
            
            for deadline_group, group_tasks in deadline_groups.items():
                distribution[deadline_group] = {
                    'count': len(group_tasks),
                    'total_minutes': sum(task.estimated_minutes for task in group_tasks),
                    'urgency_score': self._calculate_group_urgency(group_tasks)
                }
        
        return distribution
    
    async def _analyze_workload(self, tasks: List[Task], horizon_days: int) -> WorkloadMetrics:
        """Analyze workload for the given time horizon"""
        now = datetime.now()
        period_start = now
        period_end = now + timedelta(days=horizon_days)
        
        # Filter tasks that fall within the time horizon
        relevant_tasks = [
            task for task in tasks
            if not task.deadline or task.deadline <= period_end
        ]
        
        total_estimated = sum(task.estimated_minutes for task in relevant_tasks)
        
        # Estimate available minutes (simplified)
        weekdays = 0
        weekends = 0
        current = period_start
        while current <= period_end:
            if current.weekday() < 5:  # Monday-Friday
                weekdays += 1
            else:
                weekends += 1
            current += timedelta(days=1)
        
        # Assume 8 hours/day on weekdays, 6 hours/day on weekends for work
        total_available = weekdays * 480 + weekends * 360  # minutes
        
        # Calculate distributions
        high_priority = sum(task.estimated_minutes for task in relevant_tasks if task.weight > 2.0)
        medium_priority = sum(task.estimated_minutes for task in relevant_tasks if 1.0 <= task.weight <= 2.0)
        low_priority = sum(task.estimated_minutes for task in relevant_tasks if task.weight < 1.0)
        
        course_dist = {}
        for task in relevant_tasks:
            course_id = task.course_id or "uncategorized"
            course_dist[course_id] = course_dist.get(course_id, 0) + task.estimated_minutes
        
        return WorkloadMetrics(
            period_start=period_start,
            period_end=period_end,
            total_estimated_minutes=total_estimated,
            total_available_minutes=total_available,
            overcommitment_ratio=total_estimated / max(1, total_available),
            high_priority_minutes=high_priority,
            medium_priority_minutes=medium_priority,
            low_priority_minutes=low_priority,
            course_distribution=course_dist,
            complexity_distribution={}  # Would be populated with complexity analysis
        )
    
    async def _detect_procrastination_risks(
        self,
        tasks: List[Task],
        task_profiles: Dict[str, TaskComplexityProfile],
        user_context: Dict[str, Any]
    ) -> Dict[str, ProcrastinationIndicator]:
        """Detect tasks at risk of procrastination"""
        risks = {}
        
        for task in tasks:
            profile = task_profiles.get(task.id)
            if not profile:
                continue
            
            # Calculate risk factors
            complexity_anxiety = min(1.0, profile.cognitive_load * 0.7 + profile.focus_requirement * 0.3)
            
            # Historical avoidance (would be calculated from actual data)
            historical_avoidance = profile.procrastination_risk
            
            # Deadline pressure vs preparation time
            deadline_pressure = 0.0
            if task.deadline:
                days_until_deadline = (task.deadline - datetime.now()).days
                if days_until_deadline < 3:
                    deadline_pressure = 1.0 - (days_until_deadline / 3.0)
            
            # Task characteristics that increase procrastination risk
            size_intimidation = min(1.0, task.estimated_minutes / 240.0)  # Normalize to 4 hours
            
            # Overall risk score
            risk_score = (
                complexity_anxiety * 0.3 +
                historical_avoidance * 0.3 +
                deadline_pressure * 0.2 +
                size_intimidation * 0.2
            )
            
            indicators = []
            if complexity_anxiety > 0.6:
                indicators.append("High complexity may cause avoidance")
            if historical_avoidance > 0.5:
                indicators.append("Historical pattern of postponement")
            if deadline_pressure > 0.7:
                indicators.append("Deadline pressure may cause paralysis")
            if size_intimidation > 0.6:
                indicators.append("Large task may feel overwhelming")
            
            # Suggested strategies
            strategies = []
            if complexity_anxiety > 0.6:
                strategies.append("Break into smaller subtasks")
            if size_intimidation > 0.6:
                strategies.append("Use time-boxing to make progress manageable")
            if deadline_pressure > 0.5:
                strategies.append("Schedule dedicated work sessions immediately")
            
            risks[task.id] = ProcrastinationIndicator(
                task_id=task.id,
                risk_score=risk_score,
                indicators=indicators,
                postponement_history=[],  # Would be loaded from database
                completion_avoidance_score=historical_avoidance,
                complexity_anxiety_score=complexity_anxiety,
                suggested_strategies=strategies
            )
        
        return risks
    
    def _analyze_dependency_impacts(self, tasks: List[Task]) -> Dict[str, float]:
        """Analyze how much each task blocks others (dependency impact)"""
        impacts = {}
        
        # Build dependency graph
        task_map = {task.id: task for task in tasks}
        blocked_by = {}  # task_id -> list of tasks that depend on it
        
        for task in tasks:
            for prereq_id in task.prerequisites:
                if prereq_id not in blocked_by:
                    blocked_by[prereq_id] = []
                blocked_by[prereq_id].append(task)
        
        # Calculate impact scores
        for task in tasks:
            impact_score = 0.0
            
            # Direct blockers
            direct_blocked = len(blocked_by.get(task.id, []))
            impact_score += direct_blocked * 0.5
            
            # Indirect blockers (tasks that depend on tasks that depend on this)
            indirect_blocked = 0
            for blocked_task in blocked_by.get(task.id, []):
                indirect_blocked += len(blocked_by.get(blocked_task.id, []))
            impact_score += indirect_blocked * 0.2
            
            # Weight by importance of blocked tasks
            for blocked_task in blocked_by.get(task.id, []):
                impact_score += blocked_task.weight * 0.1
            
            impacts[task.id] = min(2.0, impact_score)  # Cap the impact
        
        return impacts
    
    def _calculate_deadline_urgency(self, tasks: List[Task]) -> Dict[str, float]:
        """Calculate urgency scores based on deadlines"""
        urgency_scores = {}
        now = datetime.now()
        
        for task in tasks:
            if not task.deadline:
                urgency_scores[task.id] = 0.0
                continue
            
            # Calculate days until deadline
            time_until = task.deadline - now
            days_until = time_until.days
            hours_until = time_until.total_seconds() / 3600
            
            # Estimate effort needed (in hours)
            effort_hours = task.estimated_minutes / 60.0
            
            # Urgency increases as deadline approaches and effort required is high
            if days_until <= 0:
                urgency = 2.0  # Overdue
            elif hours_until <= effort_hours:
                urgency = 1.8  # Not enough time left
            elif days_until <= 1:
                urgency = 1.5  # Due tomorrow
            elif days_until <= 3:
                urgency = 1.2  # Due this week
            elif days_until <= 7:
                urgency = 0.8  # Due next week
            else:
                urgency = max(0.1, 1.0 / (days_until / 7.0))  # Decreases with time
            
            # Adjust for task weight/importance
            urgency *= (0.5 + task.weight * 0.5)
            
            urgency_scores[task.id] = min(2.0, urgency)
        
        return urgency_scores
    
    def _assess_workload_balance(self, tasks: List[Task], workload_metrics: WorkloadMetrics) -> Dict[str, float]:
        """Assess what adjustments are needed for workload balance"""
        adjustments = {}
        
        # If overcommitted, lower priorities on less critical tasks
        if workload_metrics.overcommitment_ratio > 1.1:
            # Sort tasks by current priority and deadline
            sorted_tasks = sorted(tasks, key=lambda t: (t.weight, t.deadline or datetime.max))
            
            # Lower priority on bottom tasks
            total_tasks = len(sorted_tasks)
            for i, task in enumerate(sorted_tasks):
                if i < total_tasks * 0.3:  # Bottom 30%
                    adjustments[task.id] = -0.3
                elif i < total_tasks * 0.6:  # Middle 30%
                    adjustments[task.id] = -0.1
        
        # If undercommitted, might raise some priorities
        elif workload_metrics.overcommitment_ratio < 0.8:
            # Could increase priorities on important tasks
            for task in tasks:
                if task.weight > 1.5:  # Already important tasks
                    adjustments[task.id] = 0.1
        
        return adjustments
    
    async def _assess_energy_alignment_opportunities(
        self, tasks: List[Task], task_profiles: Dict[str, TaskComplexityProfile], user_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Assess opportunities to align high-energy times with complex tasks"""
        adjustments = {}
        
        # Get current time and user's energy patterns
        current_hour = datetime.now().hour
        
        # Simple energy model (would be more sophisticated in practice)
        peak_hours = user_context.get('peak_energy_hours', [9, 10, 11, 14, 15])
        
        for task in tasks:
            profile = task_profiles.get(task.id)
            if not profile:
                continue
            
            # High complexity tasks should get priority during peak hours
            if profile.cognitive_load > 0.7:
                if current_hour in peak_hours:
                    adjustments[task.id] = 0.2  # Boost priority if it's peak time
                else:
                    adjustments[task.id] = -0.1  # Slightly lower if not peak time
            
            # Low complexity tasks can be done anytime
            elif profile.cognitive_load < 0.3:
                adjustments[task.id] = 0.0  # No adjustment needed
        
        return adjustments
    
    def _calculate_priority_adjustment(
        self,
        task: Task,
        urgency_score: float,
        dependency_impact: float,
        balance_adjustment: float,
        procrastination_risk: ProcrastinationIndicator,
        energy_adjustment: float,
        task_profile: Optional[TaskComplexityProfile]
    ) -> Optional[PriorityAdjustment]:
        """Calculate overall priority adjustment for a task"""
        
        # Weighted combination of factors
        total_adjustment = (
            urgency_score * self.priority_weights['deadline_urgency'] +
            dependency_impact * self.priority_weights['dependency_impact'] +
            balance_adjustment * self.priority_weights['workload_balance'] +
            procrastination_risk.risk_score * self.priority_weights['procrastination_risk'] +
            energy_adjustment * self.priority_weights['energy_alignment']
        )
        
        # Determine the primary reason for adjustment
        max_factor = max([
            (urgency_score, PriorityReason.DEADLINE_APPROACHING),
            (dependency_impact, PriorityReason.DEPENDENCY_BLOCKER),
            (abs(balance_adjustment), PriorityReason.WORKLOAD_BALANCING),
            (procrastination_risk.risk_score, PriorityReason.PROCRASTINATION_RISK),
            (abs(energy_adjustment), PriorityReason.ENERGY_OPPORTUNITY)
        ], key=lambda x: x[0])
        
        primary_reason = max_factor[1]
        
        # Generate explanation
        explanations = {
            PriorityReason.DEADLINE_APPROACHING: f"Deadline urgency (score: {urgency_score:.2f})",
            PriorityReason.DEPENDENCY_BLOCKER: f"Blocks {int(dependency_impact)} other tasks",
            PriorityReason.WORKLOAD_BALANCING: "Workload rebalancing needed",
            PriorityReason.PROCRASTINATION_RISK: f"High procrastination risk ({procrastination_risk.risk_score:.2f})",
            PriorityReason.ENERGY_OPPORTUNITY: "Energy alignment opportunity"
        }
        
        if abs(total_adjustment) < 0.1:
            return None  # No significant adjustment needed
        
        old_priority = self._weight_to_priority(task.weight)
        new_weight = max(0.1, min(5.0, task.weight + total_adjustment))
        new_priority = self._weight_to_priority(new_weight)
        
        return PriorityAdjustment(
            task_id=task.id,
            old_priority=old_priority,
            new_priority=new_priority,
            adjustment_score=total_adjustment,
            reason=primary_reason,
            explanation=explanations[primary_reason],
            confidence=min(1.0, max_factor[0])  # Confidence based on strongest factor
        )
    
    def _apply_course_fairness_balancing(self, tasks: List[Task], workload_metrics: WorkloadMetrics) -> List[Task]:
        """Apply course fairness balancing to ensure no course is neglected"""
        
        # Identify courses with disproportionate workload
        total_minutes = sum(workload_metrics.course_distribution.values())
        num_courses = len(workload_metrics.course_distribution)
        
        if num_courses <= 1:
            return tasks
        
        avg_per_course = total_minutes / num_courses
        
        for course_id, course_minutes in workload_metrics.course_distribution.items():
            ratio = course_minutes / avg_per_course if avg_per_course > 0 else 1.0
            
            # If a course has significantly less work scheduled, boost its tasks
            if ratio < 0.6:  # Less than 60% of average
                for task in tasks:
                    if task.course_id == course_id:
                        task.weight *= 1.2  # Boost by 20%
            
            # If a course has too much work, slightly reduce priority
            elif ratio > 1.5:  # More than 150% of average
                for task in tasks:
                    if task.course_id == course_id:
                        task.weight *= 0.9  # Reduce by 10%
        
        return tasks
    
    def _generate_rebalancing_suggestions(self, tasks: List[Task], workload_metrics: WorkloadMetrics) -> List[str]:
        """Generate suggestions for rebalancing overcommitted workload"""
        suggestions = []
        
        excess_hours = (workload_metrics.total_estimated_minutes - workload_metrics.total_available_minutes) / 60
        
        suggestions.append(f"You're overcommitted by {excess_hours:.1f} hours.")
        
        # Identify tasks that could be postponed
        postponable_tasks = [t for t in tasks if not t.deadline or (t.deadline - datetime.now()).days > 7]
        if postponable_tasks:
            postponable_hours = sum(t.estimated_minutes for t in postponable_tasks) / 60
            suggestions.append(f"Consider postponing {len(postponable_tasks)} tasks ({postponable_hours:.1f} hours) to next week.")
        
        # Identify tasks that could be shortened
        large_tasks = [t for t in tasks if t.estimated_minutes > 120]
        if large_tasks:
            suggestions.append(f"Break down {len(large_tasks)} large tasks into smaller sessions.")
        
        # Identify low-priority tasks
        low_priority_tasks = [t for t in tasks if t.weight < 1.0]
        if low_priority_tasks:
            low_priority_hours = sum(t.estimated_minutes for t in low_priority_tasks) / 60
            suggestions.append(f"Consider deferring {len(low_priority_tasks)} low-priority tasks ({low_priority_hours:.1f} hours).")
        
        return suggestions
    
    def _calculate_group_urgency(self, tasks: List[Task]) -> float:
        """Calculate average urgency for a group of tasks"""
        if not tasks:
            return 0.0
        
        urgency_scores = self._calculate_deadline_urgency(tasks)
        return sum(urgency_scores.values()) / len(tasks)
    
    def _priority_to_weight(self, weight: float) -> Priority:
        """Convert numeric weight to priority enum"""
        if weight < 0.5:
            return "low"
        elif weight < 1.5:
            return "normal"
        elif weight < 2.5:
            return "high"
        else:
            return "critical"
    
    def _weight_to_priority(self, weight: float) -> Priority:
        """Convert numeric weight to priority enum (alias for consistency)"""
        return self._priority_to_weight(weight)
    
    def _store_adjustment_history(self, adjustments: List[PriorityAdjustment]):
        """Store priority adjustment history for learning"""
        for adjustment in adjustments:
            task_id = adjustment.task_id
            if task_id not in self.priority_history:
                self.priority_history[task_id] = []
            self.priority_history[task_id].append(adjustment)
            
            # Keep only recent history
            if len(self.priority_history[task_id]) > 50:
                self.priority_history[task_id] = self.priority_history[task_id][-50:]