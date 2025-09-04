"""
Smart Scheduling Assistant with AI-powered time blocking and context-aware optimization
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np

from .domain import Task, BusyEvent, Preferences, ScheduleBlock, ScheduleSolution
from .optimization.time_index import TimeIndex
from .learning.completion_model import CompletionModel
from .service import SchedulerService

logger = logging.getLogger(__name__)


@dataclass
class EnergyProfile:
    """User's energy and productivity patterns"""
    user_id: str
    peak_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 14, 15])  # Hours of day (0-23)
    low_energy_hours: List[int] = field(default_factory=lambda: [13, 16, 17, 20, 21])
    deep_work_capacity: Dict[int, float] = field(default_factory=dict)  # Hour -> capacity (0-1)
    shallow_work_capacity: Dict[int, float] = field(default_factory=dict)
    context_switch_penalty: Dict[int, float] = field(default_factory=dict)
    
    # Learning data
    completion_rates_by_hour: Dict[int, float] = field(default_factory=dict)
    productivity_scores_by_hour: Dict[int, float] = field(default_factory=dict)
    focus_duration_by_hour: Dict[int, int] = field(default_factory=dict)  # Minutes
    
    def get_energy_score(self, hour: int, task_complexity: str = "medium") -> float:
        """Get energy score for a given hour and task complexity"""
        base_score = 0.5
        
        if hour in self.peak_hours:
            base_score = 0.9
        elif hour in self.low_energy_hours:
            base_score = 0.3
        else:
            base_score = 0.6
        
        # Adjust for task complexity
        if task_complexity == "high" and hour not in self.peak_hours:
            base_score *= 0.7
        elif task_complexity == "low" and hour in self.low_energy_hours:
            base_score *= 1.2
        
        # Use learned data if available
        if hour in self.productivity_scores_by_hour:
            learned_score = self.productivity_scores_by_hour[hour]
            base_score = 0.3 * base_score + 0.7 * learned_score
        
        return max(0.1, min(1.0, base_score))


@dataclass
class LocationContext:
    """Location-based scheduling context"""
    name: str
    address: str
    coordinates: Optional[Tuple[float, float]] = None  # (lat, lng)
    travel_time_minutes: Dict[str, int] = field(default_factory=dict)  # location_name -> minutes
    suitable_for: List[str] = field(default_factory=list)  # ["deep_work", "meetings", "study"]
    available_hours: List[Tuple[int, int]] = field(default_factory=list)  # [(start_hour, end_hour)]


@dataclass
class TaskComplexityProfile:
    """AI assessment of task complexity and requirements"""
    task_id: str
    cognitive_load: float  # 0-1 (low to high)
    focus_requirement: float  # 0-1 (shallow to deep work)
    creativity_requirement: float  # 0-1 (routine to creative)
    collaboration_requirement: float  # 0-1 (solo to collaborative)
    
    # Context requirements
    requires_quiet_environment: bool = False
    requires_specific_tools: List[str] = field(default_factory=list)
    optimal_time_of_day: Optional[str] = None  # "morning", "afternoon", "evening"
    min_uninterrupted_duration: int = 30  # minutes
    
    # Learning-derived insights
    historical_completion_rate: float = 0.7
    typical_actual_duration: int = 60  # minutes
    procrastination_risk: float = 0.3  # 0-1


class SmartSchedulingAssistant:
    """
    AI-powered scheduling assistant that provides intelligent time blocking,
    context-aware scheduling, and energy-based optimization
    """
    
    def __init__(self, scheduler_service: SchedulerService):
        self.scheduler_service = scheduler_service
        self.energy_profiles: Dict[str, EnergyProfile] = {}
        self.location_contexts: Dict[str, LocationContext] = {}
        self.task_complexity_analyzer = TaskComplexityAnalyzer()
    
    async def create_smart_schedule(
        self,
        user_id: str,
        tasks: List[Task],
        preferences: Preferences,
        existing_events: List[BusyEvent],
        context: Dict[str, Any]
    ) -> ScheduleSolution:
        """
        Create an AI-optimized schedule with smart time blocking
        """
        try:
            # 1. Load user's energy profile
            energy_profile = await self.get_energy_profile(user_id)
            
            # 2. Analyze task complexity and requirements
            task_profiles = await self.analyze_task_complexity(tasks, user_id)
            
            # 3. Generate smart time blocks
            smart_blocks = await self.generate_smart_time_blocks(
                tasks, task_profiles, energy_profile, preferences, existing_events
            )
            
            # 4. Apply context-aware optimizations
            optimized_blocks = await self.apply_context_optimizations(
                smart_blocks, context, energy_profile, preferences
            )
            
            # 5. Create final solution
            solution = ScheduleSolution(
                feasible=True,
                blocks=optimized_blocks,
                objective_value=self._calculate_objective_value(optimized_blocks, energy_profile),
                diagnostics={
                    "smart_scheduling": True,
                    "energy_optimization": True,
                    "context_aware": True,
                    "num_optimizations": len(optimized_blocks)
                }
            )
            
            logger.info(f"Smart schedule created: {len(optimized_blocks)} blocks optimized")
            return solution
            
        except Exception as e:
            logger.error(f"Smart scheduling failed: {e}")
            # Fallback to regular scheduling
            return await self.scheduler_service.schedule({
                'user_id': user_id,
                'horizon_days': 7,
                'dry_run': False
            })
    
    async def get_energy_profile(self, user_id: str) -> EnergyProfile:
        """Get or create user's energy profile"""
        if user_id not in self.energy_profiles:
            # Load from database or create default
            profile = await self._load_energy_profile(user_id)
            if not profile:
                profile = EnergyProfile(user_id=user_id)
                await self._learn_energy_patterns(user_id, profile)
            self.energy_profiles[user_id] = profile
        
        return self.energy_profiles[user_id]
    
    async def analyze_task_complexity(
        self, tasks: List[Task], user_id: str
    ) -> Dict[str, TaskComplexityProfile]:
        """Analyze complexity and requirements for each task"""
        profiles = {}
        
        for task in tasks:
            profile = await self.task_complexity_analyzer.analyze_task(task, user_id)
            profiles[task.id] = profile
        
        return profiles
    
    async def generate_smart_time_blocks(
        self,
        tasks: List[Task],
        task_profiles: Dict[str, TaskComplexityProfile],
        energy_profile: EnergyProfile,
        preferences: Preferences,
        existing_events: List[BusyEvent]
    ) -> List[ScheduleBlock]:
        """Generate AI-optimized time blocks"""
        blocks = []
        
        # Sort tasks by complexity and energy requirements
        sorted_tasks = self._sort_tasks_by_energy_fit(tasks, task_profiles, energy_profile)
        
        # Create time index for available slots
        time_index = TimeIndex(
            timezone=preferences.timezone,
            start_dt=datetime.now(),
            end_dt=datetime.now() + timedelta(days=7),
            granularity_minutes=preferences.session_granularity_minutes
        )
        
        available_slots = time_index.get_free_slots(existing_events, preferences)
        
        for task in sorted_tasks:
            profile = task_profiles[task.id]
            
            # Find optimal time slots for this task
            optimal_slots = self._find_optimal_time_slots(
                task, profile, energy_profile, available_slots, preferences
            )
            
            if optimal_slots:
                # Create blocks for this task
                task_blocks = self._create_task_blocks(
                    task, optimal_slots, profile, energy_profile
                )
                
                blocks.extend(task_blocks)
                
                # Remove used slots from available slots
                available_slots = self._remove_used_slots(available_slots, task_blocks)
        
        return blocks
    
    async def apply_context_optimizations(
        self,
        blocks: List[ScheduleBlock],
        context: Dict[str, Any],
        energy_profile: EnergyProfile,
        preferences: Preferences
    ) -> List[ScheduleBlock]:
        """Apply context-aware optimizations"""
        optimized_blocks = blocks.copy()
        
        # 1. Location-based optimizations
        if 'locations' in context:
            optimized_blocks = self._optimize_for_locations(optimized_blocks, context['locations'])
        
        # 2. Travel time considerations
        if 'travel_requirements' in context:
            optimized_blocks = self._add_travel_buffers(optimized_blocks, context['travel_requirements'])
        
        # 3. Dependency-based grouping
        optimized_blocks = self._optimize_task_dependencies(optimized_blocks)
        
        # 4. Energy-based fine-tuning
        optimized_blocks = self._fine_tune_energy_alignment(optimized_blocks, energy_profile)
        
        return optimized_blocks
    
    def _sort_tasks_by_energy_fit(
        self, tasks: List[Task], profiles: Dict[str, TaskComplexityProfile], energy_profile: EnergyProfile
    ) -> List[Task]:
        """Sort tasks by how well they fit user's energy patterns"""
        
        def energy_fit_score(task: Task) -> float:
            profile = profiles.get(task.id)
            if not profile:
                return 0.5
            
            # High complexity tasks should be scheduled during peak energy
            if profile.cognitive_load > 0.7:
                return 1.0  # Schedule first during peak hours
            elif profile.cognitive_load < 0.3:
                return 0.3  # Can be scheduled during low energy
            else:
                return 0.6  # Medium priority
        
        return sorted(tasks, key=energy_fit_score, reverse=True)
    
    def _find_optimal_time_slots(
        self,
        task: Task,
        profile: TaskComplexityProfile,
        energy_profile: EnergyProfile,
        available_slots: List[Dict],
        preferences: Preferences
    ) -> List[Dict]:
        """Find optimal time slots for a task based on energy and requirements"""
        scored_slots = []
        
        for slot in available_slots:
            start_time = slot['start']
            duration = slot['duration_minutes']
            
            # Check if slot is long enough
            if duration < task.min_block_minutes:
                continue
            
            # Calculate energy alignment score
            hour = start_time.hour
            energy_score = energy_profile.get_energy_score(hour, self._get_complexity_level(profile))
            
            # Calculate time preference score
            time_pref_score = self._calculate_time_preference_score(start_time, profile, preferences)
            
            # Calculate focus requirement alignment
            focus_score = self._calculate_focus_alignment_score(start_time, profile, preferences)
            
            # Combined score
            total_score = (energy_score * 0.4 + time_pref_score * 0.3 + focus_score * 0.3)
            
            scored_slots.append({
                'slot': slot,
                'score': total_score,
                'energy_score': energy_score
            })
        
        # Sort by score and return top slots
        scored_slots.sort(key=lambda x: x['score'], reverse=True)
        
        # Return best slots that can accommodate the task
        needed_duration = task.estimated_minutes
        selected_slots = []
        total_duration = 0
        
        for scored_slot in scored_slots:
            if total_duration >= needed_duration:
                break
            
            slot = scored_slot['slot']
            available_duration = min(slot['duration_minutes'], task.max_block_minutes)
            
            if available_duration >= task.min_block_minutes:
                selected_slots.append(slot)
                total_duration += available_duration
        
        return selected_slots
    
    def _create_task_blocks(
        self,
        task: Task,
        time_slots: List[Dict],
        profile: TaskComplexityProfile,
        energy_profile: EnergyProfile
    ) -> List[ScheduleBlock]:
        """Create schedule blocks for a task in given time slots"""
        blocks = []
        remaining_minutes = task.estimated_minutes
        
        for slot in time_slots:
            if remaining_minutes <= 0:
                break
            
            start_time = slot['start']
            available_duration = slot['duration_minutes']
            
            # Determine block duration
            block_duration = min(
                remaining_minutes,
                available_duration,
                task.max_block_minutes
            )
            
            # Ensure minimum block size
            if block_duration < task.min_block_minutes:
                continue
            
            end_time = start_time + timedelta(minutes=block_duration)
            
            # Calculate utility scores
            hour = start_time.hour
            energy_score = energy_profile.get_energy_score(hour, self._get_complexity_level(profile))
            
            block = ScheduleBlock(
                task_id=task.id,
                start=start_time,
                end=end_time,
                estimated_completion_probability=profile.historical_completion_rate,
                utility_score=energy_score,
                penalties_applied={
                    'energy_alignment': 1.0 - energy_score,
                    'complexity_mismatch': abs(profile.cognitive_load - energy_score)
                }
            )
            
            blocks.append(block)
            remaining_minutes -= block_duration
        
        return blocks
    
    def _get_complexity_level(self, profile: TaskComplexityProfile) -> str:
        """Convert cognitive load to complexity level"""
        if profile.cognitive_load > 0.7:
            return "high"
        elif profile.cognitive_load < 0.3:
            return "low"
        else:
            return "medium"
    
    def _calculate_time_preference_score(
        self, start_time: datetime, profile: TaskComplexityProfile, preferences: Preferences
    ) -> float:
        """Calculate how well the time aligns with task and user preferences"""
        score = 0.5  # Base score
        
        hour = start_time.hour
        
        # Check task's optimal time preference
        if profile.optimal_time_of_day:
            if profile.optimal_time_of_day == "morning" and 6 <= hour <= 12:
                score += 0.3
            elif profile.optimal_time_of_day == "afternoon" and 12 <= hour <= 18:
                score += 0.3
            elif profile.optimal_time_of_day == "evening" and 18 <= hour <= 22:
                score += 0.3
        
        # Check against user's workday preferences
        workday_start = int(preferences.workday_start.split(':')[0])
        workday_end = int(preferences.workday_end.split(':')[0])
        
        if workday_start <= hour <= workday_end:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_focus_alignment_score(
        self, start_time: datetime, profile: TaskComplexityProfile, preferences: Preferences
    ) -> float:
        """Calculate alignment with focus requirements"""
        score = 0.5
        
        # Deep work tasks prefer quiet, uninterrupted times
        if profile.focus_requirement > 0.7:
            hour = start_time.hour
            # Prefer early morning or late afternoon for deep work
            if 7 <= hour <= 10 or 14 <= hour <= 16:
                score += 0.4
        
        return max(0.0, min(1.0, score))
    
    def _remove_used_slots(
        self, available_slots: List[Dict], used_blocks: List[ScheduleBlock]
    ) -> List[Dict]:
        """Remove time slots that have been used by scheduled blocks"""
        # This would implement logic to split/remove overlapping time slots
        # Simplified implementation for now
        return available_slots
    
    def _optimize_for_locations(
        self, blocks: List[ScheduleBlock], locations: Dict[str, LocationContext]
    ) -> List[ScheduleBlock]:
        """Optimize blocks considering location constraints"""
        # Implementation would group tasks by location and optimize travel
        return blocks
    
    def _add_travel_buffers(
        self, blocks: List[ScheduleBlock], travel_requirements: Dict
    ) -> List[ScheduleBlock]:
        """Add travel time buffers between blocks at different locations"""
        # Implementation would add buffer time based on travel requirements
        return blocks
    
    def _optimize_task_dependencies(self, blocks: List[ScheduleBlock]) -> List[ScheduleBlock]:
        """Optimize scheduling considering task dependencies"""
        # Implementation would reorder blocks to respect dependencies
        return blocks
    
    def _fine_tune_energy_alignment(
        self, blocks: List[ScheduleBlock], energy_profile: EnergyProfile
    ) -> List[ScheduleBlock]:
        """Fine-tune block timing for optimal energy alignment"""
        # Implementation would make small adjustments for better energy fit
        return blocks
    
    def _calculate_objective_value(
        self, blocks: List[ScheduleBlock], energy_profile: EnergyProfile
    ) -> float:
        """Calculate overall objective value for the schedule"""
        total_utility = sum(block.utility_score for block in blocks)
        return total_utility / max(1, len(blocks))
    
    async def _load_energy_profile(self, user_id: str) -> Optional[EnergyProfile]:
        """Load energy profile from database"""
        # Implementation would load from database
        return None
    
    async def _learn_energy_patterns(self, user_id: str, profile: EnergyProfile):
        """Learn user's energy patterns from historical data"""
        # Implementation would analyze completion rates, productivity scores, etc.
        pass


class TaskComplexityAnalyzer:
    """Analyzes tasks to determine complexity and requirements"""
    
    async def analyze_task(self, task: Task, user_id: str) -> TaskComplexityProfile:
        """Analyze a task to determine its complexity profile"""
        
        # Analyze based on task properties
        cognitive_load = self._analyze_cognitive_load(task)
        focus_requirement = self._analyze_focus_requirement(task)
        creativity_requirement = self._analyze_creativity_requirement(task)
        
        # Load historical data
        historical_data = await self._load_task_history(task, user_id)
        
        return TaskComplexityProfile(
            task_id=task.id,
            cognitive_load=cognitive_load,
            focus_requirement=focus_requirement,
            creativity_requirement=creativity_requirement,
            collaboration_requirement=0.0,  # Default for now
            requires_quiet_environment=focus_requirement > 0.7,
            optimal_time_of_day=self._determine_optimal_time(task),
            min_uninterrupted_duration=max(30, task.min_block_minutes),
            historical_completion_rate=historical_data.get('completion_rate', 0.7),
            typical_actual_duration=historical_data.get('avg_duration', task.estimated_minutes),
            procrastination_risk=historical_data.get('procrastination_risk', 0.3)
        )
    
    def _analyze_cognitive_load(self, task: Task) -> float:
        """Analyze cognitive load based on task properties"""
        load = 0.5  # Base load
        
        # Task type influences cognitive load
        if task.kind in ["exam", "project"]:
            load += 0.3
        elif task.kind in ["reading", "study"]:
            load += 0.2
        elif task.kind in ["admin", "hobby"]:
            load -= 0.2
        
        # Duration influences load
        if task.estimated_minutes > 120:
            load += 0.1
        
        # Keywords in title that suggest high cognitive load
        title_lower = task.title.lower()
        high_load_keywords = ["research", "analyze", "design", "complex", "difficult"]
        if any(keyword in title_lower for keyword in high_load_keywords):
            load += 0.2
        
        return max(0.1, min(1.0, load))
    
    def _analyze_focus_requirement(self, task: Task) -> float:
        """Analyze deep work vs shallow work requirement"""
        focus = 0.5
        
        if task.kind in ["exam", "study", "project"]:
            focus += 0.3
        elif task.kind in ["reading"]:
            focus += 0.2
        elif task.kind in ["admin"]:
            focus -= 0.3
        
        # Longer tasks typically need more focus
        if task.estimated_minutes > 90:
            focus += 0.2
        
        return max(0.1, min(1.0, focus))
    
    def _analyze_creativity_requirement(self, task: Task) -> float:
        """Analyze creativity requirement"""
        creativity = 0.3  # Default low creativity
        
        if task.kind in ["project"]:
            creativity += 0.4
        elif task.kind in ["hobby"]:
            creativity += 0.3
        
        # Keywords suggesting creativity
        title_lower = task.title.lower()
        creative_keywords = ["design", "create", "brainstorm", "innovate", "develop"]
        if any(keyword in title_lower for keyword in creative_keywords):
            creativity += 0.3
        
        return max(0.1, min(1.0, creativity))
    
    def _determine_optimal_time(self, task: Task) -> Optional[str]:
        """Determine optimal time of day for task"""
        if task.kind in ["study", "exam", "project"]:
            return "morning"  # Cognitive tasks better in morning
        elif task.kind in ["admin"]:
            return "afternoon"  # Administrative tasks better in afternoon
        else:
            return None
    
    async def _load_task_history(self, task: Task, user_id: str) -> Dict[str, float]:
        """Load historical data for similar tasks"""
        # Implementation would query database for historical performance
        return {
            'completion_rate': 0.7,
            'avg_duration': task.estimated_minutes,
            'procrastination_risk': 0.3
        }