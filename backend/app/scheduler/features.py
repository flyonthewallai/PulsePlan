"""
Feature extraction for ML-driven scheduling optimization.

Builds feature matrices for completion probability prediction and utility calculation.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .domain import Task, BusyEvent, Preferences, CompletionEvent
from .optimization.time_index import TimeIndex


@dataclass
class FeatureConfig:
    """Configuration for feature extraction."""
    include_time_features: bool = True
    include_task_features: bool = True
    include_context_features: bool = True
    include_historical_features: bool = True
    lookback_days: int = 60
    min_historical_samples: int = 5


class FeatureExtractor:
    """
    Extracts features for machine learning models in scheduling.
    
    Generates (task, slot) feature matrices for completion probability
    prediction and utility calculation.
    """
    
    def __init__(self, config: FeatureConfig = None):
        """Initialize feature extractor with configuration."""
        self.config = config or FeatureConfig()
        self.feature_names = []
        
    def extract_features(
        self,
        tasks: List[Task],
        time_index: TimeIndex,
        prefs: Preferences,
        busy_events: List[BusyEvent],
        history: List[CompletionEvent]
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """
        Extract feature matrix for all (task, slot) combinations.
        
        Args:
            tasks: List of tasks to schedule
            time_index: Time discretization index
            prefs: User preferences
            busy_events: Calendar events
            history: Historical completion data
            
        Returns:
            (feature_matrix, feature_names, metadata)
            feature_matrix shape: (n_tasks * n_slots, n_features)
        """
        n_tasks = len(tasks)
        n_slots = len(time_index)
        
        # Build task lookup
        task_lookup = {task.id: task for task in tasks}
        
        # Initialize feature collectors
        feature_lists = []
        self.feature_names = []
        
        # Time-based features
        if self.config.include_time_features:
            time_features = self._extract_time_features(time_index, prefs)
            feature_lists.append(time_features)
            
        # Task-based features  
        if self.config.include_task_features:
            task_features = self._extract_task_features(tasks, time_index)
            feature_lists.append(task_features)
            
        # Context features (calendar, preferences)
        if self.config.include_context_features:
            context_features = self._extract_context_features(
                tasks, time_index, prefs, busy_events
            )
            feature_lists.append(context_features)
            
        # Historical features
        if self.config.include_historical_features and history:
            hist_features = self._extract_historical_features(
                tasks, time_index, prefs, history
            )
            feature_lists.append(hist_features)
        
        # Combine all features
        if feature_lists:
            feature_matrix = np.hstack(feature_lists)
        else:
            feature_matrix = np.zeros((n_tasks * n_slots, 1))
            self.feature_names = ['bias']
            
        metadata = {
            'n_tasks': n_tasks,
            'n_slots': n_slots,
            'n_features': feature_matrix.shape[1],
            'tasks': [task.id for task in tasks],
            'time_range': (time_index.start_dt, time_index.end_dt)
        }
        
        return feature_matrix, self.feature_names, metadata
    
    def _extract_time_features(
        self, 
        time_index: TimeIndex, 
        prefs: Preferences
    ) -> np.ndarray:
        """Extract time-based features for each slot."""
        n_slots = len(time_index)
        features = []
        feature_names = []
        
        for slot_idx in range(n_slots):
            slot_context = time_index.get_slot_context(slot_idx)
            slot_dt = slot_context['datetime']
            
            slot_features = []
            
            # Hour of day (0-23)
            hour = slot_context['hour']
            slot_features.append(hour / 23.0)  # Normalized
            
            # Day of week (0-6, Monday=0)
            dow = slot_context['day_of_week']
            slot_features.append(dow / 6.0)  # Normalized
            
            # Time of day categories (one-hot)
            slot_features.extend([
                1.0 if slot_context['is_morning'] else 0.0,
                1.0 if slot_context['is_afternoon'] else 0.0,
                1.0 if slot_context['is_evening'] else 0.0
            ])
            
            # Weekend indicator
            slot_features.append(1.0 if slot_context['is_weekend'] else 0.0)
            
            # Distance from workday bounds
            workday_start_hour = self._parse_time_hour(prefs.workday_start)
            workday_end_hour = self._parse_time_hour(prefs.workday_end)
            
            # Distance from workday start/end (normalized)
            dist_from_start = abs(hour - workday_start_hour) / 24.0
            dist_from_end = abs(hour - workday_end_hour) / 24.0
            slot_features.extend([dist_from_start, dist_from_end])
            
            # In workday hours
            in_workday = 1.0 if workday_start_hour <= hour < workday_end_hour else 0.0
            slot_features.append(in_workday)
            
            features.append(slot_features)
        
        # Feature names (only set once)
        if not self.feature_names:
            feature_names = [
                'hour_norm', 'dow_norm', 'is_morning', 'is_afternoon', 
                'is_evening', 'is_weekend', 'dist_from_workday_start',
                'dist_from_workday_end', 'in_workday'
            ]
            self.feature_names.extend(feature_names)
        
        # Tile for all tasks
        slot_features = np.array(features)  # (n_slots, n_time_features)
        n_tasks = 1  # This will be broadcast correctly when combined
        
        return slot_features
    
    def _extract_task_features(
        self, 
        tasks: List[Task], 
        time_index: TimeIndex
    ) -> np.ndarray:
        """Extract task-specific features."""
        n_tasks = len(tasks)
        n_slots = len(time_index)
        features = []
        feature_names = []
        
        for task in tasks:
            task_features = []
            
            # Task duration (normalized by max)
            max_duration = max(t.estimated_minutes for t in tasks) or 1
            duration_norm = task.estimated_minutes / max_duration
            task_features.append(duration_norm)
            
            # Task weight (normalized)
            max_weight = max(t.weight for t in tasks) or 1
            weight_norm = task.weight / max_weight
            task_features.append(weight_norm)
            
            # Min/max block constraints
            min_block_norm = task.min_block_minutes / max_duration
            max_block_norm = task.max_block_minutes / max_duration
            task_features.extend([min_block_norm, max_block_norm])
            
            # Task kind (one-hot encoding)
            task_kinds = ['study', 'assignment', 'exam', 'reading', 'project', 'hobby', 'admin']
            task_kind_features = [1.0 if task.kind == kind else 0.0 for kind in task_kinds]
            task_features.extend(task_kind_features)
            
            # Has deadline
            has_deadline = 1.0 if task.deadline else 0.0
            task_features.append(has_deadline)
            
            # Deadline urgency (days remaining, normalized)
            if task.deadline:
                days_remaining = (task.deadline - time_index.start_dt).days
                urgency = max(0, 14 - days_remaining) / 14.0  # Higher urgency = closer deadline
            else:
                urgency = 0.0
            task_features.append(urgency)
            
            # Has prerequisites
            has_prereqs = 1.0 if task.prerequisites else 0.0
            task_features.append(has_prereqs)
            
            # Is exam (special handling)
            is_exam = 1.0 if task.kind == 'exam' else 0.0
            task_features.append(is_exam)
            
            # Tags (common ones)
            common_tags = ['deep_work', 'shallow', 'creative', 'analytical']
            tag_features = [1.0 if tag in task.tags else 0.0 for tag in common_tags]
            task_features.extend(tag_features)
            
            features.append(task_features)
        
        # Feature names (only set once)
        if 'duration_norm' not in self.feature_names:
            feature_names = [
                'duration_norm', 'weight_norm', 'min_block_norm', 'max_block_norm'
            ] + [f'kind_{kind}' for kind in task_kinds] + [
                'has_deadline', 'urgency', 'has_prereqs', 'is_exam'
            ] + [f'tag_{tag}' for tag in common_tags]
            self.feature_names.extend(feature_names)
        
        # Repeat task features for each slot
        task_features_array = np.array(features)  # (n_tasks, n_task_features)
        
        # Create (n_tasks * n_slots, n_task_features) by repeating each task for all slots
        repeated_features = np.repeat(task_features_array, n_slots, axis=0)
        
        return repeated_features
    
    def _extract_context_features(
        self,
        tasks: List[Task],
        time_index: TimeIndex,
        prefs: Preferences,
        busy_events: List[BusyEvent]
    ) -> np.ndarray:
        """Extract contextual features based on calendar and preferences."""
        n_tasks = len(tasks)
        n_slots = len(time_index)
        features = []
        
        # Get blocked slots
        blocked_slots = time_index.filter_busy_slots(busy_events)
        
        for task_idx, task in enumerate(tasks):
            for slot_idx in range(n_slots):
                slot_features = []
                slot_context = time_index.get_slot_context(slot_idx)
                
                # Slot availability
                is_blocked = 1.0 if slot_idx in blocked_slots else 0.0
                slot_features.append(is_blocked)
                
                # Preferred/avoided windows for this task
                in_preferred = self._is_in_time_windows(
                    slot_context['datetime'], task.preferred_windows
                )
                in_avoided = self._is_in_time_windows(
                    slot_context['datetime'], task.avoid_windows
                )
                slot_features.extend([
                    1.0 if in_preferred else 0.0,
                    1.0 if in_avoided else 0.0
                ])
                
                # Deep work window alignment
                in_deep_work = self._is_in_time_windows(
                    slot_context['datetime'], prefs.deep_work_windows
                )
                slot_features.append(1.0 if in_deep_work else 0.0)
                
                # No study windows
                in_no_study = self._is_in_time_windows(
                    slot_context['datetime'], prefs.no_study_windows
                )
                slot_features.append(1.0 if in_no_study else 0.0)
                
                # Break context (time since last break would be nice, but complex)
                needs_break = self._estimate_break_need(slot_idx, prefs)
                slot_features.append(needs_break)
                
                # Calendar density (events nearby)
                nearby_density = self._calculate_calendar_density(
                    slot_idx, time_index, busy_events
                )
                slot_features.append(nearby_density)
                
                features.append(slot_features)
        
        # Feature names (only set once)
        if 'is_blocked' not in self.feature_names:
            context_names = [
                'is_blocked', 'in_preferred', 'in_avoided', 'in_deep_work',
                'in_no_study', 'needs_break', 'calendar_density'
            ]
            self.feature_names.extend(context_names)
        
        return np.array(features)
    
    def _extract_historical_features(
        self,
        tasks: List[Task],
        time_index: TimeIndex,
        prefs: Preferences,
        history: List[CompletionEvent]
    ) -> np.ndarray:
        """Extract features based on historical completion patterns."""
        n_tasks = len(tasks)
        n_slots = len(time_index)
        features = []
        
        # Build historical completion rate by hour/day patterns
        completion_stats = self._compute_completion_stats(history)
        
        for task_idx, task in enumerate(tasks):
            for slot_idx in range(n_slots):
                slot_features = []
                slot_context = time_index.get_slot_context(slot_idx)
                
                # Historical completion rate for this hour
                hour = slot_context['hour']
                dow = slot_context['day_of_week']
                
                hour_completion_rate = completion_stats.get(
                    ('hour', hour), 0.5
                )
                dow_completion_rate = completion_stats.get(
                    ('dow', dow), 0.5  
                )
                slot_features.extend([hour_completion_rate, dow_completion_rate])
                
                # Task kind completion rate
                kind_completion_rate = completion_stats.get(
                    ('kind', task.kind), 0.5
                )
                slot_features.append(kind_completion_rate)
                
                # Recent performance trend
                recent_performance = self._get_recent_performance(
                    history, slot_context['datetime'], days_back=7
                )
                slot_features.append(recent_performance)
                
                features.append(slot_features)
        
        # Feature names (only set once)
        if 'hour_completion_rate' not in self.feature_names:
            hist_names = [
                'hour_completion_rate', 'dow_completion_rate',
                'kind_completion_rate', 'recent_performance'
            ]
            self.feature_names.extend(hist_names)
        
        return np.array(features)
    
    def _parse_time_hour(self, time_str: str) -> float:
        """Parse 'HH:MM' time string to hour float."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour + minute / 60.0
        except:
            return 12.0  # Default to noon
    
    def _is_in_time_windows(self, dt: datetime, windows: List[Dict]) -> bool:
        """Check if datetime falls within any of the specified windows."""
        if not windows:
            return False
            
        for window in windows:
            if self._datetime_in_window(dt, window):
                return True
                
        return False
    
    def _datetime_in_window(self, dt: datetime, window: Dict) -> bool:
        """Check if datetime is within a single time window."""
        dow = window.get('dow')
        start_time = window.get('start')
        end_time = window.get('end')
        
        # Check day of week
        if dow is not None and dt.weekday() != dow:
            return False
            
        # Check time range
        if start_time and end_time:
            dt_time = dt.time()
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            
            if start <= end:
                return start <= dt_time <= end
            else:
                # Overnight window
                return dt_time >= start or dt_time <= end
                
        return True
    
    def _estimate_break_need(self, slot_idx: int, prefs: Preferences) -> float:
        """Estimate break need based on preferences (simplified)."""
        # This is a simplified version - in practice would track work streaks
        return 0.1  # Low break need by default
    
    def _calculate_calendar_density(
        self, 
        slot_idx: int, 
        time_index: TimeIndex, 
        busy_events: List[BusyEvent],
        window_hours: int = 2
    ) -> float:
        """Calculate density of calendar events around a slot."""
        slot_dt = time_index.index_to_datetime(slot_idx)
        if not slot_dt:
            return 0.0
            
        window_start = slot_dt - timedelta(hours=window_hours)
        window_end = slot_dt + timedelta(hours=window_hours)
        
        nearby_events = [
            event for event in busy_events
            if event.start < window_end and event.end > window_start
        ]
        
        # Return proportion of window occupied by events
        total_minutes = window_hours * 2 * 60
        occupied_minutes = sum(
            min(event.end, window_end) - max(event.start, window_start)
            for event in nearby_events
        )
        
        if isinstance(occupied_minutes, timedelta):
            occupied_minutes = occupied_minutes.total_seconds() / 60
            
        return min(1.0, occupied_minutes / total_minutes)
    
    def _compute_completion_stats(self, history: List[CompletionEvent]) -> Dict:
        """Compute completion rate statistics from historical data."""
        if not history:
            return {}
            
        stats = {}
        
        # Group by different dimensions
        by_hour = {}
        by_dow = {}
        by_kind = {}  # Would need task kind lookup
        
        for event in history:
            if event.completed_at is not None:
                # Successful completion
                hour = event.scheduled_slot.hour
                dow = event.scheduled_slot.weekday()
                
                by_hour.setdefault(hour, []).append(1)
                by_dow.setdefault(dow, []).append(1)
            else:
                # Failed/skipped
                hour = event.scheduled_slot.hour
                dow = event.scheduled_slot.weekday()
                
                by_hour.setdefault(hour, []).append(0)
                by_dow.setdefault(dow, []).append(0)
        
        # Compute completion rates
        for hour, completions in by_hour.items():
            stats[('hour', hour)] = np.mean(completions)
            
        for dow, completions in by_dow.items():
            stats[('dow', dow)] = np.mean(completions)
        
        return stats
    
    def _get_recent_performance(
        self, 
        history: List[CompletionEvent], 
        reference_dt: datetime,
        days_back: int = 7
    ) -> float:
        """Get recent completion performance trend."""
        cutoff_dt = reference_dt - timedelta(days=days_back)
        
        recent_events = [
            event for event in history
            if event.scheduled_slot >= cutoff_dt
        ]
        
        if not recent_events:
            return 0.5  # Neutral
            
        completions = [
            1 if event.completed_at is not None else 0
            for event in recent_events
        ]
        
        return np.mean(completions)


async def build_utilities(
    model,
    tasks: List[Task],
    time_index: TimeIndex,
    prefs: Preferences,
    events: List[BusyEvent],
    history: List[CompletionEvent]
) -> Tuple[Dict[str, Dict[int, float]], Dict[str, Any]]:
    """
    Build utility matrix and penalty context for optimization.
    
    Args:
        model: Completion probability model
        tasks: Tasks to schedule
        time_index: Time discretization
        prefs: User preferences
        events: Calendar events
        history: Historical completion data
        
    Returns:
        (utility_matrix, penalty_context)
        utility_matrix[task_id][slot_idx] = expected utility
    """
    # Extract features
    feature_extractor = FeatureExtractor()
    features, feature_names, metadata = feature_extractor.extract_features(
        tasks, time_index, prefs, events, history
    )
    
    # Get completion probabilities from model
    try:
        completion_probs = model.predict(features)
    except:
        # Fallback to uniform probabilities
        completion_probs = np.full(features.shape[0], 0.7)
    
    # Build utility matrix
    utility_matrix = {}
    n_slots = len(time_index)
    
    for task_idx, task in enumerate(tasks):
        task_utilities = {}
        
        for slot_idx in range(n_slots):
            feature_idx = task_idx * n_slots + slot_idx
            
            # Base utility = completion_prob * task_weight * slot_duration
            prob = completion_probs[feature_idx]
            base_utility = prob * task.weight * time_index.granularity_minutes
            
            task_utilities[slot_idx] = base_utility
            
        utility_matrix[task.id] = task_utilities
    
    # Penalty context for objective function
    penalty_context = {
        'time_index': time_index,
        'prefs': prefs,
        'tasks': {task.id: task for task in tasks},
        'busy_events': events,
        'features': features,
        'feature_names': feature_names,
        'metadata': metadata
    }
    
    return utility_matrix, penalty_context