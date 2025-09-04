"""
Data repository for scheduler persistence.

Handles loading and saving of tasks, preferences, schedules, and learning data.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, time
import json
import asyncio
from contextlib import asynccontextmanager

from ..domain import (
    Task, BusyEvent, Preferences, CompletionEvent, 
    ScheduleSolution, ScheduleBlock, SchedulerRun
)

logger = logging.getLogger(__name__)


class Repository:
    """
    Data repository for scheduler persistence.
    
    Abstracts database operations and provides caching for performance.
    """
    
    def __init__(self, backend: str = "memory"):
        """
        Initialize repository.
        
        Args:
            backend: Storage backend ('memory', 'database', 'file')
        """
        self.backend = backend
        
        # In-memory storage for development/testing
        self.memory_store = {
            'tasks': {},           # user_id -> List[Task]
            'events': {},          # user_id -> List[BusyEvent]
            'preferences': {},     # user_id -> Preferences
            'history': {},         # user_id -> List[CompletionEvent]
            'schedules': {},       # user_id -> List[ScheduleBlock]
            'runs': {},           # user_id -> List[SchedulerRun]
        }
        
        # Initialize with sample data for development
        if backend == "memory":
            self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample data for development."""
        sample_user = "user_123"
        
        # Sample preferences
        self.memory_store['preferences'][sample_user] = Preferences(
            timezone="America/New_York",
            workday_start="09:00",
            workday_end="18:00",
            max_daily_effort_minutes=480,
            session_granularity_minutes=30
        )
        
        # Sample tasks
        now = datetime.now()
        self.memory_store['tasks'][sample_user] = [
            Task(
                id="task_1",
                user_id=sample_user,
                title="Study Machine Learning",
                kind="study",
                estimated_minutes=120,
                min_block_minutes=60,
                max_block_minutes=120,
                deadline=now + timedelta(days=7),
                weight=2.0,
                course_id="cs_ml_101"
            ),
            Task(
                id="task_2", 
                user_id=sample_user,
                title="Complete Assignment 1",
                kind="assignment",
                estimated_minutes=90,
                min_block_minutes=45,
                max_block_minutes=90,
                deadline=now + timedelta(days=3),
                weight=3.0,
                course_id="cs_ml_101"
            ),
            Task(
                id="task_3",
                user_id=sample_user,
                title="Read Chapter 5",
                kind="reading",
                estimated_minutes=60,
                min_block_minutes=30,
                max_block_minutes=60,
                weight=1.0,
                course_id="cs_ml_101"
            )
        ]
        
        # Sample busy events
        self.memory_store['events'][sample_user] = [
            BusyEvent(
                id="event_1",
                source="google",
                start=now.replace(hour=10, minute=0),
                end=now.replace(hour=11, minute=0),
                title="Team Meeting",
                hard=True
            ),
            BusyEvent(
                id="event_2",
                source="google", 
                start=now.replace(hour=14, minute=0),
                end=now.replace(hour=15, minute=30),
                title="Doctor Appointment",
                hard=True
            )
        ]
        
        # Sample completion history
        self.memory_store['history'][sample_user] = [
            CompletionEvent(
                task_id="task_old_1",
                scheduled_slot=now - timedelta(hours=24),
                completed_at=now - timedelta(hours=23, minutes=45)
            ),
            CompletionEvent(
                task_id="task_old_2",
                scheduled_slot=now - timedelta(hours=48),
                completed_at=None,  # Missed
                skipped=True
            )
        ]
    
    async def load_tasks(self, user_id: str, horizon_days: int) -> List[Task]:
        """
        Load tasks for scheduling within the horizon.
        
        Args:
            user_id: User identifier
            horizon_days: Days ahead to consider
            
        Returns:
            List of tasks to schedule
        """
        try:
            if self.backend == "memory":
                tasks = self.memory_store['tasks'].get(user_id, [])
                
                # Filter tasks relevant to horizon
                horizon_end = datetime.now() + timedelta(days=horizon_days)
                relevant_tasks = []
                
                for task in tasks:
                    # Include if no deadline or deadline within extended horizon
                    if task.deadline is None or task.deadline <= horizon_end + timedelta(days=7):
                        relevant_tasks.append(task)
                
                logger.debug(f"Loaded {len(relevant_tasks)} tasks for user {user_id}")
                return relevant_tasks
            
            elif self.backend == "database":
                return await self._load_tasks_from_db(user_id, horizon_days)
            
            else:
                logger.warning(f"Unknown backend {self.backend}, returning empty tasks")
                return []
                
        except Exception as e:
            logger.error(f"Failed to load tasks for user {user_id}: {e}")
            return []
    
    async def load_calendar_busy(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """
        Load busy calendar events within the horizon.
        
        Args:
            user_id: User identifier  
            horizon_days: Days ahead to consider
            
        Returns:
            List of busy events
        """
        try:
            if self.backend == "memory":
                events = self.memory_store['events'].get(user_id, [])
                
                # Filter events within horizon
                now = datetime.now()
                horizon_start = now
                horizon_end = now + timedelta(days=horizon_days)
                
                relevant_events = [
                    event for event in events
                    if event.start < horizon_end and event.end > horizon_start
                ]
                
                logger.debug(f"Loaded {len(relevant_events)} events for user {user_id}")
                return relevant_events
                
            elif self.backend == "database":
                return await self._load_events_from_db(user_id, horizon_days)
            
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to load events for user {user_id}: {e}")
            return []
    
    async def load_preferences(self, user_id: str) -> Preferences:
        """
        Load user preferences for scheduling.
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences with defaults if not found
        """
        try:
            if self.backend == "memory":
                prefs = self.memory_store['preferences'].get(user_id)
                if prefs:
                    return prefs
                
                # Return defaults
                return Preferences(
                    timezone="UTC",
                    workday_start="09:00",
                    workday_end="17:00",
                    max_daily_effort_minutes=480,
                    session_granularity_minutes=30
                )
                
            elif self.backend == "database":
                return await self._load_preferences_from_db(user_id)
            
            else:
                return Preferences(timezone="UTC")
                
        except Exception as e:
            logger.error(f"Failed to load preferences for user {user_id}: {e}")
            return Preferences(timezone="UTC")
    
    async def load_history(self, user_id: str, horizon_days: int = 60) -> List[CompletionEvent]:
        """
        Load historical completion data for learning.
        
        Args:
            user_id: User identifier
            horizon_days: Days back to load history
            
        Returns:
            List of completion events
        """
        try:
            if self.backend == "memory":
                history = self.memory_store['history'].get(user_id, [])
                
                # Filter to recent history
                cutoff_date = datetime.now() - timedelta(days=horizon_days)
                recent_history = [
                    event for event in history
                    if event.scheduled_slot >= cutoff_date
                ]
                
                logger.debug(f"Loaded {len(recent_history)} history events for user {user_id}")
                return recent_history
                
            elif self.backend == "database":
                return await self._load_history_from_db(user_id, horizon_days)
            
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to load history for user {user_id}: {e}")
            return []
    
    async def get_window(self, user_id: str, horizon_days: int) -> Tuple[datetime, datetime]:
        """
        Get the time window for scheduling.
        
        Args:
            user_id: User identifier
            horizon_days: Days ahead to schedule
            
        Returns:
            (start_datetime, end_datetime) for scheduling
        """
        try:
            prefs = await self.load_preferences(user_id)
            
            # Start from beginning of current day in user timezone
            now = datetime.now()
            
            # For simplicity, use current timezone
            # In production, would use prefs.timezone
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=horizon_days)
            
            return start_dt, end_dt
            
        except Exception as e:
            logger.error(f"Failed to get window for user {user_id}: {e}")
            now = datetime.now()
            return now, now + timedelta(days=horizon_days)
    
    async def persist_schedule(
        self, 
        user_id: str, 
        solution: ScheduleSolution,
        job_id: Optional[str] = None
    ):
        """
        Persist schedule blocks to storage.
        
        Args:
            user_id: User identifier
            solution: Schedule solution with blocks
            job_id: Optional job identifier
        """
        try:
            if self.backend == "memory":
                # Store blocks in memory
                self.memory_store['schedules'][user_id] = solution.blocks
                logger.debug(f"Persisted {len(solution.blocks)} blocks for user {user_id}")
                
            elif self.backend == "database":
                await self._persist_schedule_to_db(user_id, solution, job_id)
            
        except Exception as e:
            logger.error(f"Failed to persist schedule for user {user_id}: {e}")
    
    async def persist_run_summary(
        self,
        user_id: str,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Persist summary of scheduler run for analysis.
        
        Args:
            user_id: User identifier
            solution: Schedule solution
            weights: Penalty weights used
            context: Additional context
        """
        try:
            run = SchedulerRun(
                id=f"run_{datetime.now().isoformat()}",
                user_id=user_id,
                horizon_days=7,  # Would get from context
                started_at=datetime.now() - timedelta(milliseconds=solution.solve_time_ms),
                finished_at=datetime.now(),
                feasible=solution.feasible,
                objective_value=solution.objective_value,
                weights=weights,
                diagnostics=solution.diagnostics or {}
            )
            
            if self.backend == "memory":
                if user_id not in self.memory_store['runs']:
                    self.memory_store['runs'][user_id] = []
                self.memory_store['runs'][user_id].append(run)
                
                # Keep only recent runs
                self.memory_store['runs'][user_id] = self.memory_store['runs'][user_id][-100:]
                
            elif self.backend == "database":
                await self._persist_run_to_db(run)
            
            logger.debug(f"Persisted run summary for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist run summary for user {user_id}: {e}")
    
    async def get_recent_schedules(
        self, user_id: str, days_back: int = 7
    ) -> List[ScheduleBlock]:
        """
        Get recently scheduled blocks for a user.
        
        Args:
            user_id: User identifier
            days_back: Days back to retrieve
            
        Returns:
            List of recent schedule blocks
        """
        try:
            if self.backend == "memory":
                blocks = self.memory_store['schedules'].get(user_id, [])
                
                # Filter to recent blocks
                cutoff_date = datetime.now() - timedelta(days=days_back)
                recent_blocks = [
                    block for block in blocks
                    if block.start >= cutoff_date
                ]
                
                return recent_blocks
                
            elif self.backend == "database":
                return await self._get_recent_schedules_from_db(user_id, days_back)
            
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get recent schedules for user {user_id}: {e}")
            return []
    
    async def update_task(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """
        Update task parameters.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            updates: Dictionary of field updates
        """
        try:
            if self.backend == "memory":
                tasks = self.memory_store['tasks'].get(user_id, [])
                
                for i, task in enumerate(tasks):
                    if task.id == task_id:
                        # Create updated task
                        task_dict = asdict(task)
                        task_dict.update(updates)
                        task_dict['updated_at'] = datetime.now()
                        
                        # Replace in list
                        tasks[i] = Task(**task_dict)
                        break
                        
            elif self.backend == "database":
                await self._update_task_in_db(user_id, task_id, updates)
            
            logger.debug(f"Updated task {task_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id} for user {user_id}: {e}")
    
    async def update_preferences(self, user_id: str, updates: Dict[str, Any]):
        """
        Update user preferences.
        
        Args:
            user_id: User identifier
            updates: Dictionary of preference updates
        """
        try:
            if self.backend == "memory":
                current_prefs = self.memory_store['preferences'].get(user_id)
                if current_prefs:
                    prefs_dict = asdict(current_prefs)
                    prefs_dict.update(updates)
                    self.memory_store['preferences'][user_id] = Preferences(**prefs_dict)
                else:
                    # Create new preferences
                    default_prefs = asdict(Preferences(timezone="UTC"))
                    default_prefs.update(updates)
                    self.memory_store['preferences'][user_id] = Preferences(**default_prefs)
                    
            elif self.backend == "database":
                await self._update_preferences_in_db(user_id, updates)
            
            logger.debug(f"Updated preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
    
    async def record_completion(
        self, user_id: str, task_id: str, scheduled_slot: datetime, 
        completed_at: Optional[datetime] = None, skipped: bool = False
    ):
        """
        Record task completion or miss for learning.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            scheduled_slot: When task was scheduled
            completed_at: When task was completed (None if missed)
            skipped: Whether task was explicitly skipped
        """
        try:
            completion_event = CompletionEvent(
                task_id=task_id,
                scheduled_slot=scheduled_slot,
                completed_at=completed_at,
                skipped=skipped
            )
            
            if self.backend == "memory":
                if user_id not in self.memory_store['history']:
                    self.memory_store['history'][user_id] = []
                self.memory_store['history'][user_id].append(completion_event)
                
                # Keep only recent history
                cutoff_date = datetime.now() - timedelta(days=90)
                self.memory_store['history'][user_id] = [
                    event for event in self.memory_store['history'][user_id]
                    if event.scheduled_slot >= cutoff_date
                ]
                
            elif self.backend == "database":
                await self._record_completion_in_db(completion_event)
            
            logger.debug(f"Recorded completion for task {task_id}, user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to record completion for task {task_id}, user {user_id}: {e}")
    
    # Database backend methods (stubs for future implementation)
    
    async def _load_tasks_from_db(self, user_id: str, horizon_days: int) -> List[Task]:
        """Load tasks from database."""
        # TODO: Implement database loading
        logger.warning("Database backend not implemented")
        return []
    
    async def _load_events_from_db(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """Load events from database."""
        # TODO: Implement database loading
        logger.warning("Database backend not implemented")
        return []
    
    async def _load_preferences_from_db(self, user_id: str) -> Preferences:
        """Load preferences from database."""
        # TODO: Implement database loading
        logger.warning("Database backend not implemented")
        return Preferences(timezone="UTC")
    
    async def _load_history_from_db(self, user_id: str, horizon_days: int) -> List[CompletionEvent]:
        """Load history from database."""
        # TODO: Implement database loading
        logger.warning("Database backend not implemented")
        return []
    
    async def _persist_schedule_to_db(
        self, user_id: str, solution: ScheduleSolution, job_id: Optional[str]
    ):
        """Persist schedule to database."""
        # TODO: Implement database persistence
        logger.warning("Database backend not implemented")
    
    async def _persist_run_to_db(self, run: SchedulerRun):
        """Persist run summary to database."""
        # TODO: Implement database persistence
        logger.warning("Database backend not implemented")
    
    async def _get_recent_schedules_from_db(
        self, user_id: str, days_back: int
    ) -> List[ScheduleBlock]:
        """Get recent schedules from database."""
        # TODO: Implement database loading
        logger.warning("Database backend not implemented")
        return []
    
    async def _update_task_in_db(self, user_id: str, task_id: str, updates: Dict[str, Any]):
        """Update task in database."""
        # TODO: Implement database update
        logger.warning("Database backend not implemented")
    
    async def _update_preferences_in_db(self, user_id: str, updates: Dict[str, Any]):
        """Update preferences in database."""
        # TODO: Implement database update
        logger.warning("Database backend not implemented")
    
    async def _record_completion_in_db(self, event: CompletionEvent):
        """Record completion in database."""
        # TODO: Implement database persistence
        logger.warning("Database backend not implemented")


# Global repository instance
_repository = None

def get_repository(backend: str = "memory") -> Repository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = Repository(backend=backend)
    return _repository