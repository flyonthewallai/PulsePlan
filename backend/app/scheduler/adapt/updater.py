"""
Post-run learning and model updates.

Updates ML models based on scheduling outcomes, user feedback,
and observed completion patterns.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import asyncio

from ..domain import Task, ScheduleBlock, CompletionEvent
from ..learning.completion_model import CompletionModel
from ..learning.bandits import WeightTuner, compute_reward
from .evaluator import ScheduleEvaluator, get_quality_tracker

logger = logging.getLogger(__name__)


class LearningUpdater:
    """
    Coordinates learning updates across all ML components.
    
    Processes scheduling outcomes and updates models to improve
    future scheduling performance.
    """
    
    def __init__(self):
        """Initialize learning updater."""
        self.evaluator = ScheduleEvaluator()
        
        # Update configuration
        self.min_samples_for_update = 5
        self.update_frequency_hours = 24
        self.confidence_threshold = 0.7
    
    async def post_run_update(
        self,
        tuner: WeightTuner,
        model: CompletionModel,
        user_id: str,
        schedule_outcome: Dict[str, Any],
        history: Optional[List[CompletionEvent]] = None
    ):
        """
        Perform post-run learning updates.
        
        Args:
            tuner: Weight tuning bandit
            model: Completion prediction model
            user_id: User identifier
            schedule_outcome: Results from schedule execution
            history: Historical completion data
        """
        try:
            logger.debug(f"Starting post-run update for user {user_id}")
            
            # Update bandit with reward signal
            await self._update_bandit(tuner, user_id, schedule_outcome)
            
            # Update completion model if sufficient data
            await self._update_completion_model(model, user_id, schedule_outcome, history)
            
            # Save updated models
            await self._save_models(tuner, model, user_id)
            
            logger.info(f"Post-run update completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Post-run update failed for user {user_id}: {e}", exc_info=True)
    
    async def _update_bandit(
        self,
        tuner: WeightTuner,
        user_id: str,
        schedule_outcome: Dict[str, Any]
    ):
        """Update bandit weights based on schedule outcome."""
        try:
            # Get context and weights from outcome
            context = schedule_outcome.get('context', {})
            weights = schedule_outcome.get('weights', {})
            
            if not context or not weights:
                logger.warning(f"Missing context or weights for bandit update: {user_id}")
                return
            
            # Compute reward signal
            reward = compute_reward(schedule_outcome)
            
            # Update bandit
            tuner.update(context, weights, reward)
            
            logger.debug(f"Updated bandit for user {user_id}: reward={reward:.3f}")
            
        except Exception as e:
            logger.error(f"Bandit update failed for user {user_id}: {e}")
    
    async def _update_completion_model(
        self,
        model: CompletionModel,
        user_id: str,
        schedule_outcome: Dict[str, Any],
        history: Optional[List[CompletionEvent]]
    ):
        """Update completion prediction model with new data."""
        try:
            # Extract completion events from outcome
            completion_events = self._extract_completion_events(schedule_outcome)
            
            if not completion_events:
                logger.debug(f"No completion events for model update: {user_id}")
                return
            
            # Check if we have enough data for update
            if len(completion_events) < self.min_samples_for_update:
                logger.debug(f"Insufficient samples for model update: {len(completion_events)}")
                return
            
            # Build training data
            X, y, feature_names = await self._build_training_data(
                completion_events, schedule_outcome
            )
            
            if len(X) == 0:
                logger.debug("No training data generated")
                return
            
            # Update model incrementally
            metrics = await model.partial_fit(X, y, feature_names)
            
            logger.info(
                f"Updated completion model for user {user_id}: "
                f"samples={len(X)}, accuracy={metrics.get('accuracy', 0):.3f}"
            )
            
        except Exception as e:
            logger.error(f"Completion model update failed for user {user_id}: {e}")
    
    def _extract_completion_events(
        self, schedule_outcome: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract completion events from schedule outcome."""
        events = []
        
        # From schedule blocks with outcomes
        scheduled_blocks = schedule_outcome.get('scheduled_blocks', [])
        completed_tasks = set(schedule_outcome.get('completed_tasks', []))
        missed_tasks = set(schedule_outcome.get('missed_tasks', []))
        
        for block in scheduled_blocks:
            task_id = block.get('task_id')
            if not task_id:
                continue
            
            event = {
                'task_id': task_id,
                'scheduled_start': block.get('start'),
                'scheduled_end': block.get('end'),
                'completed': task_id in completed_tasks,
                'missed': task_id in missed_tasks,
                'utility_score': block.get('utility_score', 0.0),
                'completion_probability': block.get('completion_probability', 0.7)
            }
            events.append(event)
        
        return events
    
    async def _build_training_data(
        self,
        completion_events: List[Dict[str, Any]],
        schedule_outcome: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Build training data from completion events."""
        # Simplified training data construction
        # In practice, would reconstruct feature matrix
        
        X_list = []
        y_list = []
        
        for event in completion_events:
            # Extract basic features (would be more comprehensive in practice)
            start_time = event.get('scheduled_start')
            if not start_time:
                continue
            
            # Convert start time to features
            if isinstance(start_time, str):
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except:
                    continue
            else:
                start_dt = start_time
            
            features = [
                start_dt.hour / 23.0,  # Normalized hour
                start_dt.weekday() / 6.0,  # Normalized day of week
                1.0 if start_dt.weekday() >= 5 else 0.0,  # Is weekend
                event.get('utility_score', 0.0),
                event.get('completion_probability', 0.7)
            ]
            
            # Target: was task completed?
            target = 1 if event.get('completed', False) else 0
            
            X_list.append(features)
            y_list.append(target)
        
        if X_list:
            X = np.array(X_list)
            y = np.array(y_list)
            feature_names = ['hour_norm', 'dow_norm', 'is_weekend', 'utility_score', 'completion_prob']
        else:
            X = np.array([]).reshape(0, 5)
            y = np.array([])
            feature_names = []
        
        return X, y, feature_names
    
    async def _save_models(
        self,
        tuner: WeightTuner,
        model: CompletionModel,
        user_id: str
    ):
        """Save updated models to storage."""
        try:
            # Save models in parallel
            save_tasks = [
                tuner.save(user_id),
                model.save(user_id)
            ]
            
            results = await asyncio.gather(*save_tasks, return_exceptions=True)
            
            # Check for save failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    model_name = "bandit" if i == 0 else "completion"
                    logger.error(f"Failed to save {model_name} model for user {user_id}: {result}")
            
        except Exception as e:
            logger.error(f"Model saving failed for user {user_id}: {e}")


class FeedbackProcessor:
    """
    Processes user feedback to improve scheduling.
    
    Analyzes explicit and implicit user feedback to identify
    areas for improvement in scheduling algorithms.
    """
    
    def __init__(self):
        """Initialize feedback processor."""
        self.feedback_history = []
    
    async def process_feedback(
        self,
        user_id: str,
        feedback: Dict[str, Any],
        schedule_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user feedback and extract insights.
        
        Args:
            user_id: User identifier
            feedback: User feedback data
            schedule_context: Context from original schedule
            
        Returns:
            Processed feedback insights
        """
        try:
            # Store feedback
            feedback_entry = {
                'user_id': user_id,
                'timestamp': datetime.now(),
                'feedback': feedback,
                'context': schedule_context or {}
            }
            self.feedback_history.append(feedback_entry)
            
            # Analyze feedback
            insights = await self._analyze_feedback(feedback_entry)
            
            # Update quality metrics
            await self._update_quality_metrics(user_id, feedback, insights)
            
            logger.debug(f"Processed feedback for user {user_id}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Feedback processing failed for user {user_id}: {e}")
            return {}
    
    async def _analyze_feedback(self, feedback_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback to extract actionable insights."""
        feedback = feedback_entry['feedback']
        insights = {}
        
        # Satisfaction analysis
        satisfaction = feedback.get('satisfaction_score', 0)
        if satisfaction < -0.3:
            insights['low_satisfaction'] = True
            insights['satisfaction_issues'] = self._identify_satisfaction_issues(feedback)
        
        # Completion analysis
        completed_tasks = feedback.get('completed_tasks', [])
        missed_tasks = feedback.get('missed_tasks', [])
        
        if missed_tasks:
            insights['missed_task_patterns'] = self._analyze_missed_patterns(
                missed_tasks, feedback_entry.get('context', {})
            )
        
        # Rescheduling analysis
        rescheduled_tasks = feedback.get('rescheduled_tasks', [])
        if len(rescheduled_tasks) > 2:
            insights['high_rescheduling'] = True
            insights['rescheduling_reasons'] = self._analyze_rescheduling_patterns(
                rescheduled_tasks
            )
        
        # Timing preferences
        if 'preferred_times' in feedback:
            insights['timing_preferences'] = feedback['preferred_times']
        
        return insights
    
    def _identify_satisfaction_issues(self, feedback: Dict[str, Any]) -> List[str]:
        """Identify potential causes of low satisfaction."""
        issues = []
        
        if feedback.get('missed_tasks'):
            issues.append("missed_tasks")
        
        if len(feedback.get('rescheduled_tasks', [])) > 2:
            issues.append("excessive_rescheduling")
        
        if feedback.get('time_pressure', False):
            issues.append("time_pressure")
        
        if feedback.get('poor_timing', False):
            issues.append("poor_timing")
        
        return issues
    
    def _analyze_missed_patterns(
        self, missed_tasks: List[str], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze patterns in missed tasks."""
        patterns = {
            'total_missed': len(missed_tasks),
            'missed_rate': len(missed_tasks) / max(1, context.get('total_scheduled', 1))
        }
        
        # Would analyze time patterns, task types, etc.
        # Simplified for this implementation
        
        return patterns
    
    def _analyze_rescheduling_patterns(self, rescheduled_tasks: List[str]) -> Dict[str, Any]:
        """Analyze patterns in user rescheduling."""
        return {
            'total_rescheduled': len(rescheduled_tasks),
            'rescheduling_rate': len(rescheduled_tasks)  # Would normalize
        }
    
    async def _update_quality_metrics(
        self,
        user_id: str,
        feedback: Dict[str, Any],
        insights: Dict[str, Any]
    ):
        """Update quality tracking with feedback."""
        try:
            # Would create a schedule evaluation from feedback
            # For now, just log the update
            logger.debug(f"Quality metrics updated for user {user_id}")
            
        except Exception as e:
            logger.error(f"Quality metrics update failed: {e}")
    
    def get_feedback_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of feedback for analysis."""
        feedback_entries = self.feedback_history
        if user_id:
            feedback_entries = [f for f in feedback_entries if f['user_id'] == user_id]
        
        if not feedback_entries:
            return {'no_feedback': True}
        
        # Calculate summary statistics
        satisfactions = [
            f['feedback'].get('satisfaction_score', 0)
            for f in feedback_entries
        ]
        
        return {
            'total_feedback': len(feedback_entries),
            'avg_satisfaction': np.mean(satisfactions),
            'recent_satisfaction': satisfactions[-5:] if satisfactions else [],
            'feedback_trend': 'improving' if len(satisfactions) > 1 and satisfactions[-1] > satisfactions[0] else 'stable'
        }


class PerformanceMonitor:
    """
    Monitors scheduling performance and triggers updates.
    
    Tracks key performance metrics and determines when
    model updates or recalibration are needed.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.performance_history = []
        self.alert_thresholds = {
            'completion_rate': 0.6,  # Below 60%
            'satisfaction_score': -0.3,  # Below -0.3
            'rescheduling_rate': 0.3,  # Above 30%
            'missed_rate': 0.2  # Above 20%
        }
    
    async def record_performance(
        self,
        user_id: str,
        metrics: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ):
        """Record performance metrics."""
        entry = {
            'user_id': user_id,
            'timestamp': datetime.now(),
            'metrics': metrics,
            'context': context or {}
        }
        
        self.performance_history.append(entry)
        
        # Check for alerts
        alerts = self._check_alerts(metrics)
        if alerts:
            logger.warning(f"Performance alerts for user {user_id}: {alerts}")
        
        # Clean old history
        cutoff_date = datetime.now() - timedelta(days=30)
        self.performance_history = [
            entry for entry in self.performance_history
            if entry['timestamp'] >= cutoff_date
        ]
    
    def _check_alerts(self, metrics: Dict[str, float]) -> List[str]:
        """Check for performance alerts."""
        alerts = []
        
        for metric_name, threshold in self.alert_thresholds.items():
            value = metrics.get(metric_name)
            if value is None:
                continue
            
            # Check threshold direction
            if metric_name in ['completion_rate', 'satisfaction_score']:
                # Higher is better
                if value < threshold:
                    alerts.append(f"{metric_name} below threshold: {value:.3f} < {threshold}")
            else:
                # Lower is better
                if value > threshold:
                    alerts.append(f"{metric_name} above threshold: {value:.3f} > {threshold}")
        
        return alerts
    
    def get_performance_trends(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance trends over time."""
        entries = self.performance_history
        if user_id:
            entries = [e for e in entries if e['user_id'] == user_id]
        
        if len(entries) < 2:
            return {'insufficient_data': True}
        
        # Calculate trends for each metric
        trends = {}
        metric_names = set()
        for entry in entries:
            metric_names.update(entry['metrics'].keys())
        
        for metric_name in metric_names:
            values = [
                entry['metrics'].get(metric_name)
                for entry in entries
                if metric_name in entry['metrics']
            ]
            
            if len(values) >= 2:
                # Simple trend calculation
                recent_avg = np.mean(values[-5:])  # Last 5 values
                overall_avg = np.mean(values)
                
                trends[metric_name] = {
                    'recent_average': recent_avg,
                    'overall_average': overall_avg,
                    'improving': recent_avg > overall_avg,
                    'values_count': len(values)
                }
        
        return {
            'total_entries': len(entries),
            'trends': trends,
            'latest_metrics': entries[-1]['metrics'] if entries else {}
        }


# Main entry point function
async def post_run_update(
    tuner: WeightTuner,
    model: CompletionModel,
    user_id: str,
    schedule_outcome: Dict[str, Any],
    history: Optional[List[CompletionEvent]] = None
):
    """
    Main entry point for post-run learning updates.
    
    Args:
        tuner: Weight tuning bandit
        model: Completion prediction model
        user_id: User identifier
        schedule_outcome: Results from schedule execution
        history: Historical completion data
    """
    updater = LearningUpdater()
    await updater.post_run_update(tuner, model, user_id, schedule_outcome, history)


# Global instances
_feedback_processor = FeedbackProcessor()
_performance_monitor = PerformanceMonitor()

def get_feedback_processor() -> FeedbackProcessor:
    """Get global feedback processor instance."""
    return _feedback_processor

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return _performance_monitor