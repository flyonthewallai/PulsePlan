"""
Schedule quality evaluation and metrics.

Evaluates schedule quality, user satisfaction, and provides feedback
for continuous improvement of the scheduling algorithm.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
from enum import Enum

from ..core.domain import Task, ScheduleBlock, ScheduleSolution, Preferences
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of schedule quality metrics."""
    COMPLETION_RATE = "completion_rate"
    TIME_UTILIZATION = "time_utilization"
    DEADLINE_ADHERENCE = "deadline_adherence"
    USER_SATISFACTION = "user_satisfaction"
    FRAGMENTATION = "fragmentation"
    PREFERENCE_ALIGNMENT = "preference_alignment"
    WORKLOAD_BALANCE = "workload_balance"


@dataclass
class ScheduleMetric:
    """Individual schedule quality metric."""
    name: str
    value: float
    max_value: float
    description: str
    weight: float = 1.0
    
    @property
    def normalized_score(self) -> float:
        """Get normalized score (0-1)."""
        if self.max_value == 0:
            return 0.0
        return min(1.0, self.value / self.max_value)
    
    @property
    def weighted_score(self) -> float:
        """Get weighted normalized score."""
        return self.normalized_score * self.weight


@dataclass
class ScheduleEvaluation:
    """Complete evaluation of a schedule."""
    user_id: str
    evaluation_time: datetime
    metrics: List[ScheduleMetric]
    overall_score: float
    recommendations: List[str]
    context: Dict[str, Any]
    
    def get_metric(self, metric_type: MetricType) -> Optional[ScheduleMetric]:
        """Get specific metric by type."""
        for metric in self.metrics:
            if metric.name == metric_type.value:
                return metric
        return None
    
    def get_score_breakdown(self) -> Dict[str, float]:
        """Get breakdown of scores by metric."""
        return {
            metric.name: metric.normalized_score 
            for metric in self.metrics
        }


class ScheduleEvaluator:
    """
    Evaluates schedule quality across multiple dimensions.
    
    Provides comprehensive assessment of scheduling effectiveness
    and identifies areas for improvement.
    """
    
    def __init__(self):
        """Initialize schedule evaluator."""
        # Default metric weights
        self.metric_weights = {
            MetricType.COMPLETION_RATE: 3.0,
            MetricType.DEADLINE_ADHERENCE: 2.5,
            MetricType.USER_SATISFACTION: 2.0,
            MetricType.TIME_UTILIZATION: 1.5,
            MetricType.PREFERENCE_ALIGNMENT: 1.5,
            MetricType.WORKLOAD_BALANCE: 1.0,
            MetricType.FRAGMENTATION: 1.0
        }
    
    async def evaluate_schedule(
        self,
        user_id: str,
        solution: ScheduleSolution,
        tasks: List[Task],
        preferences: Preferences,
        actual_outcomes: Optional[Dict[str, Any]] = None
    ) -> ScheduleEvaluation:
        """
        Perform comprehensive schedule evaluation.
        
        Args:
            user_id: User identifier
            solution: Schedule solution to evaluate
            tasks: Original tasks
            preferences: User preferences
            actual_outcomes: Actual completion data (if available)
            
        Returns:
            Complete schedule evaluation
        """
        metrics = []
        
        # Completion rate
        completion_metric = await self._evaluate_completion_rate(
            solution.blocks, actual_outcomes
        )
        metrics.append(completion_metric)
        
        # Time utilization
        utilization_metric = await self._evaluate_time_utilization(
            solution.blocks, preferences
        )
        metrics.append(utilization_metric)
        
        # Deadline adherence
        deadline_metric = await self._evaluate_deadline_adherence(
            solution.blocks, tasks
        )
        metrics.append(deadline_metric)
        
        # Preference alignment
        preference_metric = await self._evaluate_preference_alignment(
            solution.blocks, tasks, preferences
        )
        metrics.append(preference_metric)
        
        # Fragmentation
        fragmentation_metric = await self._evaluate_fragmentation(
            solution.blocks, tasks
        )
        metrics.append(fragmentation_metric)
        
        # Workload balance
        balance_metric = await self._evaluate_workload_balance(
            solution.blocks, preferences
        )
        metrics.append(balance_metric)
        
        # User satisfaction (if actual outcomes available)
        if actual_outcomes:
            satisfaction_metric = await self._evaluate_user_satisfaction(
                actual_outcomes
            )
            metrics.append(satisfaction_metric)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, solution)
        
        evaluation = ScheduleEvaluation(
            user_id=user_id,
            evaluation_time=datetime.now(),
            metrics=metrics,
            overall_score=overall_score,
            recommendations=recommendations,
            context={
                'total_blocks': len(solution.blocks),
                'total_tasks': len(tasks),
                'feasible': solution.feasible,
                'solver_status': solution.solver_status,
                'solve_time_ms': solution.solve_time_ms
            }
        )
        
        logger.debug(f"Schedule evaluation completed for {user_id}: score={overall_score:.3f}")
        
        return evaluation
    
    async def _evaluate_completion_rate(
        self,
        blocks: List[ScheduleBlock],
        actual_outcomes: Optional[Dict[str, Any]]
    ) -> ScheduleMetric:
        """Evaluate task completion rate."""
        if not actual_outcomes or not blocks:
            # Use predicted completion rate
            total_blocks = len(blocks)
            predicted_completions = sum(
                getattr(block, 'estimated_completion_probability', 0.7)
                for block in blocks
            )
            completion_rate = predicted_completions / max(1, total_blocks)
        else:
            # Use actual completion data
            completed_tasks = actual_outcomes.get('completed_tasks', [])
            missed_tasks = actual_outcomes.get('missed_tasks', [])
            total_tasks = len(completed_tasks) + len(missed_tasks)
            
            if total_tasks > 0:
                completion_rate = len(completed_tasks) / total_tasks
            else:
                completion_rate = 0.0
        
        return ScheduleMetric(
            name=MetricType.COMPLETION_RATE.value,
            value=completion_rate,
            max_value=1.0,
            description="Proportion of scheduled tasks completed",
            weight=self.metric_weights[MetricType.COMPLETION_RATE]
        )
    
    async def _evaluate_time_utilization(
        self,
        blocks: List[ScheduleBlock],
        preferences: Preferences
    ) -> ScheduleMetric:
        """Evaluate time utilization efficiency."""
        if not blocks:
            return ScheduleMetric(
                name=MetricType.TIME_UTILIZATION.value,
                value=0.0,
                max_value=1.0,
                description="Efficiency of time slot usage",
                weight=self.metric_weights[MetricType.TIME_UTILIZATION]
            )
        
        # Calculate scheduled time vs available time
        total_scheduled_minutes = sum(block.duration_minutes for block in blocks)
        
        # Estimate available time per day
        available_minutes_per_day = preferences.max_daily_effort_minutes
        
        # Get unique days spanned by schedule
        if blocks:
            start_date = min(block.start.date() for block in blocks)
            end_date = max(block.end.date() for block in blocks)
            days_spanned = (end_date - start_date).days + 1
        else:
            days_spanned = 1
        
        total_available_minutes = available_minutes_per_day * days_spanned
        utilization_rate = total_scheduled_minutes / max(1, total_available_minutes)
        
        return ScheduleMetric(
            name=MetricType.TIME_UTILIZATION.value,
            value=utilization_rate,
            max_value=1.0,
            description="Ratio of scheduled time to available time",
            weight=self.metric_weights[MetricType.TIME_UTILIZATION]
        )
    
    async def _evaluate_deadline_adherence(
        self,
        blocks: List[ScheduleBlock],
        tasks: List[Task]
    ) -> ScheduleMetric:
        """Evaluate adherence to task deadlines."""
        task_lookup = {task.id: task for task in tasks}
        
        tasks_with_deadlines = [
            task for task in tasks 
            if task.deadline is not None
        ]
        
        if not tasks_with_deadlines:
            return ScheduleMetric(
                name=MetricType.DEADLINE_ADHERENCE.value,
                value=1.0,
                max_value=1.0,
                description="Proportion of tasks scheduled before deadlines",
                weight=self.metric_weights[MetricType.DEADLINE_ADHERENCE]
            )
        
        adherent_tasks = 0
        
        for task in tasks_with_deadlines:
            task_blocks = [block for block in blocks if block.task_id == task.id]
            
            if task_blocks:
                # Check if all blocks for this task are before deadline
                latest_block_end = max(block.end for block in task_blocks)
                if latest_block_end <= task.deadline:
                    adherent_tasks += 1
        
        adherence_rate = adherent_tasks / len(tasks_with_deadlines)
        
        return ScheduleMetric(
            name=MetricType.DEADLINE_ADHERENCE.value,
            value=adherence_rate,
            max_value=1.0,
            description="Proportion of tasks scheduled before deadlines",
            weight=self.metric_weights[MetricType.DEADLINE_ADHERENCE]
        )
    
    async def _evaluate_preference_alignment(
        self,
        blocks: List[ScheduleBlock],
        tasks: List[Task],
        preferences: Preferences
    ) -> ScheduleMetric:
        """Evaluate alignment with user preferences."""
        if not blocks:
            return ScheduleMetric(
                name=MetricType.PREFERENCE_ALIGNMENT.value,
                value=0.0,
                max_value=1.0,
                description="Alignment with user time preferences",
                weight=self.metric_weights[MetricType.PREFERENCE_ALIGNMENT]
            )
        
        task_lookup = {task.id: task for task in tasks}
        alignment_scores = []
        
        for block in blocks:
            task = task_lookup.get(block.task_id)
            if not task:
                continue
            
            block_score = 0.0
            
            # Check preferred windows
            if task.preferred_windows:
                in_preferred = any(
                    self._time_in_window(block.start, window)
                    for window in task.preferred_windows
                )
                if in_preferred:
                    block_score += 1.0
            else:
                block_score += 0.5  # Neutral if no preferences
            
            # Check avoid windows
            if task.avoid_windows:
                in_avoided = any(
                    self._time_in_window(block.start, window)
                    for window in task.avoid_windows
                )
                if in_avoided:
                    block_score -= 0.5
            
            # Check workday hours
            workday_start = self._parse_time(preferences.workday_start)
            workday_end = self._parse_time(preferences.workday_end)
            block_time = block.start.time()
            
            if workday_start <= block_time <= workday_end:
                block_score += 0.3
            
            alignment_scores.append(max(0.0, min(1.0, block_score)))
        
        average_alignment = np.mean(alignment_scores) if alignment_scores else 0.0
        
        return ScheduleMetric(
            name=MetricType.PREFERENCE_ALIGNMENT.value,
            value=average_alignment,
            max_value=1.0,
            description="Alignment with user time preferences",
            weight=self.metric_weights[MetricType.PREFERENCE_ALIGNMENT]
        )
    
    async def _evaluate_fragmentation(
        self,
        blocks: List[ScheduleBlock],
        tasks: List[Task]
    ) -> ScheduleMetric:
        """Evaluate task fragmentation (prefer fewer, longer blocks)."""
        if not blocks:
            return ScheduleMetric(
                name=MetricType.FRAGMENTATION.value,
                value=1.0,  # Perfect score for no fragmentation
                max_value=1.0,
                description="Inverse of task fragmentation",
                weight=self.metric_weights[MetricType.FRAGMENTATION]
            )
        
        # Group blocks by task
        task_blocks = {}
        for block in blocks:
            if block.task_id not in task_blocks:
                task_blocks[block.task_id] = []
            task_blocks[block.task_id].append(block)
        
        fragmentation_penalties = []
        
        for task_id, task_block_list in task_blocks.items():
            if len(task_block_list) <= 1:
                # No fragmentation for single blocks
                fragmentation_penalties.append(0.0)
                continue
            
            # Calculate fragmentation penalty
            num_blocks = len(task_block_list)
            total_duration = sum(block.duration_minutes for block in task_block_list)
            
            if total_duration > 0:
                # Penalty increases with number of blocks relative to total time
                fragmentation_penalty = (num_blocks - 1) / (total_duration / 60)  # per hour
                fragmentation_penalties.append(min(1.0, fragmentation_penalty))
            else:
                fragmentation_penalties.append(0.0)
        
        average_penalty = np.mean(fragmentation_penalties) if fragmentation_penalties else 0.0
        fragmentation_score = 1.0 - average_penalty  # Invert so higher is better
        
        return ScheduleMetric(
            name=MetricType.FRAGMENTATION.value,
            value=fragmentation_score,
            max_value=1.0,
            description="Inverse of task fragmentation",
            weight=self.metric_weights[MetricType.FRAGMENTATION]
        )
    
    async def _evaluate_workload_balance(
        self,
        blocks: List[ScheduleBlock],
        preferences: Preferences
    ) -> ScheduleMetric:
        """Evaluate daily workload balance."""
        if not blocks:
            return ScheduleMetric(
                name=MetricType.WORKLOAD_BALANCE.value,
                value=1.0,
                max_value=1.0,
                description="Balance of workload across days",
                weight=self.metric_weights[MetricType.WORKLOAD_BALANCE]
            )
        
        # Group blocks by date
        daily_workloads = {}
        for block in blocks:
            date = block.start.date()
            if date not in daily_workloads:
                daily_workloads[date] = 0
            daily_workloads[date] += block.duration_minutes
        
        if len(daily_workloads) <= 1:
            return ScheduleMetric(
                name=MetricType.WORKLOAD_BALANCE.value,
                value=1.0,
                max_value=1.0,
                description="Balance of workload across days",
                weight=self.metric_weights[MetricType.WORKLOAD_BALANCE]
            )
        
        # Calculate coefficient of variation (lower is better)
        workloads = list(daily_workloads.values())
        mean_workload = np.mean(workloads)
        std_workload = np.std(workloads)
        
        if mean_workload > 0:
            cv = std_workload / mean_workload
            balance_score = max(0.0, 1.0 - cv)  # Convert to score (higher is better)
        else:
            balance_score = 1.0
        
        return ScheduleMetric(
            name=MetricType.WORKLOAD_BALANCE.value,
            value=balance_score,
            max_value=1.0,
            description="Balance of workload across days",
            weight=self.metric_weights[MetricType.WORKLOAD_BALANCE]
        )
    
    async def _evaluate_user_satisfaction(
        self,
        actual_outcomes: Dict[str, Any]
    ) -> ScheduleMetric:
        """Evaluate user satisfaction from feedback."""
        satisfaction_score = actual_outcomes.get('satisfaction_score', 0.0)
        
        # Convert from -1,1 range to 0,1 range
        normalized_satisfaction = (satisfaction_score + 1.0) / 2.0
        
        return ScheduleMetric(
            name=MetricType.USER_SATISFACTION.value,
            value=normalized_satisfaction,
            max_value=1.0,
            description="User-reported satisfaction with schedule",
            weight=self.metric_weights[MetricType.USER_SATISFACTION]
        )
    
    def _calculate_overall_score(self, metrics: List[ScheduleMetric]) -> float:
        """Calculate weighted overall score."""
        if not metrics:
            return 0.0
        
        total_weighted_score = sum(metric.weighted_score for metric in metrics)
        total_weight = sum(metric.weight for metric in metrics)
        
        return total_weighted_score / max(1.0, total_weight)
    
    def _generate_recommendations(
        self,
        metrics: List[ScheduleMetric],
        solution: ScheduleSolution
    ) -> List[str]:
        """Generate recommendations based on evaluation."""
        recommendations = []
        
        # Check each metric for improvement opportunities
        for metric in metrics:
            if metric.normalized_score < 0.6:  # Below 60% threshold
                recommendations.append(
                    self._get_improvement_recommendation(metric, solution)
                )
        
        # General recommendations
        if solution.solve_time_ms > 15000:  # Over 15 seconds
            recommendations.append(
                "Consider reducing solver time limit or using simpler constraints"
            )
        
        if len(solution.unscheduled_tasks) > 0:
            recommendations.append(
                f"Unable to schedule {len(solution.unscheduled_tasks)} tasks - "
                "consider adjusting deadlines or time estimates"
            )
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _get_improvement_recommendation(
        self,
        metric: ScheduleMetric,
        solution: ScheduleSolution
    ) -> str:
        """Get specific recommendation for a low-scoring metric."""
        metric_recommendations = {
            MetricType.COMPLETION_RATE.value: (
                "Improve completion rates by scheduling tasks at historically "
                "successful times or reducing task duration estimates"
            ),
            MetricType.TIME_UTILIZATION.value: (
                "Increase time utilization by scheduling more tasks or "
                "extending daily effort limits"
            ),
            MetricType.DEADLINE_ADHERENCE.value: (
                "Improve deadline adherence by prioritizing urgent tasks "
                "or extending deadlines where possible"
            ),
            MetricType.PREFERENCE_ALIGNMENT.value: (
                "Better align with preferences by updating preferred/avoided "
                "time windows or adjusting penalty weights"
            ),
            MetricType.FRAGMENTATION.value: (
                "Reduce fragmentation by increasing minimum block sizes "
                "or reducing context switch penalties"
            ),
            MetricType.WORKLOAD_BALANCE.value: (
                "Improve workload balance by distributing tasks more evenly "
                "across days or adjusting daily effort limits"
            ),
            MetricType.USER_SATISFACTION.value: (
                "Improve satisfaction by gathering more user feedback "
                "and adjusting scheduling parameters accordingly"
            )
        }
        
        return metric_recommendations.get(
            metric.name,
            f"Improve {metric.name} metric (currently {metric.normalized_score:.1%})"
        )
    
    def _time_in_window(self, dt: datetime, window: Dict) -> bool:
        """Check if datetime falls within a time window."""
        # Simplified implementation
        dow = window.get('dow')
        if dow is not None and dt.weekday() != dow:
            return False
        
        start_time = window.get('start')
        end_time = window.get('end')
        
        if start_time and end_time:
            try:
                start = datetime.strptime(start_time, '%H:%M').time()
                end = datetime.strptime(end_time, '%H:%M').time()
                dt_time = dt.time()
                
                if start <= end:
                    return start <= dt_time <= end
                else:
                    return dt_time >= start or dt_time <= end
            except:
                return False
        
        return True
    
    def _parse_time(self, time_str: str) -> datetime.time:
        """Parse time string to time object."""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except:
            return datetime.strptime('12:00', '%H:%M').time()


async def evaluate_schedule_regret(
    current_evaluation: ScheduleEvaluation,
    alternative_evaluations: List[ScheduleEvaluation]
) -> float:
    """
    Calculate regret by comparing current schedule to alternatives.
    
    Args:
        current_evaluation: Evaluation of chosen schedule
        alternative_evaluations: Evaluations of alternative schedules
        
    Returns:
        Regret value (0 = no regret, higher = more regret)
    """
    if not alternative_evaluations:
        return 0.0
    
    best_alternative_score = max(
        eval.overall_score for eval in alternative_evaluations
    )
    
    regret = max(0.0, best_alternative_score - current_evaluation.overall_score)
    
    return regret


class QualityTracker:
    """Track schedule quality over time for trend analysis."""
    
    def __init__(self):
        """Initialize quality tracker."""
        self.evaluations = []
    
    def add_evaluation(self, evaluation: ScheduleEvaluation):
        """Add a new evaluation to the history."""
        self.evaluations.append(evaluation)
        
        # Keep only recent evaluations
        cutoff_date = datetime.now() - timedelta(days=90)
        self.evaluations = [
            eval for eval in self.evaluations
            if eval.evaluation_time >= cutoff_date
        ]
    
    def get_trends(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get quality trends over time."""
        evaluations = self.evaluations
        if user_id:
            evaluations = [e for e in evaluations if e.user_id == user_id]
        
        if len(evaluations) < 2:
            return {'insufficient_data': True}
        
        # Sort by time
        evaluations.sort(key=lambda e: e.evaluation_time)
        
        # Calculate trends
        scores = [e.overall_score for e in evaluations]
        
        # Simple linear trend
        x = np.arange(len(scores))
        if len(scores) > 1:
            slope = np.polyfit(x, scores, 1)[0]
        else:
            slope = 0.0
        
        return {
            'total_evaluations': len(evaluations),
            'latest_score': scores[-1],
            'average_score': np.mean(scores),
            'trend_slope': slope,
            'improving': slope > 0.01,
            'score_history': scores[-10:]  # Last 10 scores
        }


# Global quality tracker
_quality_tracker = QualityTracker()

def get_quality_tracker() -> QualityTracker:
    """Get global quality tracker instance."""
    return _quality_tracker


