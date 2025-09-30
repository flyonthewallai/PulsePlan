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

from ..core.domain import (
    Task, BusyEvent, Preferences, CompletionEvent,
    ScheduleSolution, ScheduleBlock, SchedulerRun
)
from ...core.utils.timezone_utils import get_timezone_manager

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
        self.timezone_manager = get_timezone_manager()

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
        try:
            from app.config.database.supabase import get_supabase
            from datetime import datetime, timedelta
            
            supabase = get_supabase()
            
            # Calculate date range
            end_date = datetime.utcnow() + timedelta(days=horizon_days)
            
            # Query tasks from database 
            response = supabase.table("tasks").select("*").eq("user_id", user_id).eq("status", "pending").lte("due_date", end_date.isoformat()).execute()

            tasks = []
            for task_data in response.data:
                # Convert database task to scheduler Task 
                task = Task(
                    id=task_data["id"],
                    user_id=task_data["user_id"],
                    title=task_data["title"],
                    kind=task_data.get("kind", "task"),
                    estimated_minutes=task_data.get("estimated_minutes", 60),
                    min_block_minutes=task_data.get("min_block_minutes", 30),
                    max_block_minutes=task_data.get("max_block_minutes", 120),
                    deadline=datetime.fromisoformat(task_data["due_date"].replace('Z', '+00:00')) if task_data.get("due_date") else None,
                    earliest_start=datetime.fromisoformat(task_data["earliest_start"].replace('Z', '+00:00')) if task_data.get("earliest_start") else None,
                    preferred_windows=task_data.get("preferred_windows", []),
                    avoid_windows=task_data.get("avoid_windows", []),
                    fixed=task_data.get("fixed", False),
                    parent_task_id=task_data.get("parent_task_id"),
                    prerequisites=task_data.get("prerequisites", []),
                    weight=task_data.get("weight", 1.0),
                    course_id=task_data.get("course_id"),
                    must_finish_before=task_data.get("must_finish_before"),
                    tags=task_data.get("tags", []),
                    pinned_slots=task_data.get("pinned_slots", [])
                )
                tasks.append(task)
            
            logger.info(f"Loaded {len(tasks)} tasks from database for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to load tasks from database: {e}")
            return []
    
    async def _load_events_from_db(self, user_id: str, horizon_days: int) -> List[BusyEvent]:
        """Load events from database."""
        try:
            from app.config.database.supabase import get_supabase
            from datetime import datetime, timedelta
            
            supabase = get_supabase()
            
            # Calculate date range
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=horizon_days)
            
            # Query calendar events from database - first check calendar_events table, then tasks table for events
            calendar_response = supabase.table("calendar_events").select("*").eq("user_id", user_id).gte("start_time", start_date.isoformat()).lte("end_time", end_date.isoformat()).execute()

            # Also get events from consolidated tasks table
            tasks_response = supabase.table("tasks").select("*").eq("user_id", user_id).eq("task_type", "event").gte("start_date", start_date.isoformat()).lte("end_date", end_date.isoformat()).execute()
            
            events = []

            # Process calendar_events table data
            for event_data in calendar_response.data:
                # Convert database event to scheduler BusyEvent
                start_time = datetime.fromisoformat(event_data["start_time"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event_data["end_time"].replace('Z', '+00:00'))

                event = BusyEvent(
                    id=event_data["id"],
                    user_id=user_id,
                    title=event_data.get("title", "Calendar Event"),
                    start=start_time,
                    end=end_time,
                    source=event_data.get("provider", "calendar"),
                    hard=True,
                    location=event_data.get("location", ""),
                    metadata={"original_table": "calendar_events"}
                )
                events.append(event)

            # Process tasks table events
            for event_data in tasks_response.data:
                # Convert task event to scheduler BusyEvent
                start_time = datetime.fromisoformat(event_data["start_date"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event_data["end_date"].replace('Z', '+00:00')) if event_data.get("end_date") else start_time + timedelta(hours=1)

                event = BusyEvent(
                    id=event_data["id"],
                    user_id=user_id,
                    title=event_data.get("title", "Event"),
                    start=start_time,
                    end=end_time,
                    source=event_data.get("sync_source", "pulse"),
                    hard=True,
                    location=event_data.get("location", ""),
                    metadata={"original_table": "tasks", "task_type": event_data.get("task_type")}
                )
                events.append(event)
            
            logger.info(f"Loaded {len(events)} calendar events from database for user {user_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to load events from database: {e}")
            return []
    
    async def _load_preferences_from_db(self, user_id: str) -> Preferences:
        """Load preferences from database."""
        try:
            from app.config.database.supabase import get_supabase
            
            supabase = get_supabase()
            
            # Query user preferences from database
            response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
            
            prefs = {}
            for pref in response.data:
                key = pref["preference_key"]
                value = pref["value"]
                prefs[key] = value
            
            # Get user timezone from users table
            user_response = supabase.table("users").select("timezone").eq("id", user_id).single().execute()
            timezone = user_response.data.get("timezone", "UTC") if user_response.data else "UTC"
            
            # Create Preferences object with database data
            preferences = Preferences(
                timezone=timezone,
                working_hours_start=prefs.get("working_hours_start", 9),
                working_hours_end=prefs.get("working_hours_end", 17),
                break_duration_minutes=prefs.get("break_duration_minutes", 15),
                max_daily_work_hours=prefs.get("max_daily_work_hours", 8),
                preferred_work_days=prefs.get("preferred_work_days", [1, 2, 3, 4, 5]),  # Mon-Fri
                focus_time_blocks=prefs.get("focus_time_blocks", True)
            )
            
            logger.info(f"Loaded preferences from database for user {user_id}")
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to load preferences from database: {e}")
            return Preferences(timezone="UTC")
    
    async def _load_history_from_db(self, user_id: str, horizon_days: int) -> List[CompletionEvent]:
        """Load history from database."""
        try:
            from app.config.database.supabase import get_supabase
            from datetime import datetime, timedelta
            
            supabase = get_supabase()
            
            # Calculate date range (look back from current time)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=horizon_days)
            
            # Query completed tasks/task completions from database
            response = supabase.table("task_completions").select("*").eq("user_id", user_id).gte("completed_at", start_date.isoformat()).lte("completed_at", end_date.isoformat()).execute()
            
            history = []
            for completion_data in response.data:
                # Convert database completion to scheduler CompletionEvent
                completion_time = datetime.fromisoformat(completion_data["completed_at"].replace('Z', '+00:00'))
                
                completion = CompletionEvent(
                    task_id=completion_data["task_id"],
                    title=completion_data.get("task_title", "Completed Task"),
                    completed_at=completion_time,
                    actual_minutes=completion_data.get("actual_minutes", 60),
                    planned_minutes=completion_data.get("planned_minutes", 60),
                    quality_rating=completion_data.get("quality_rating", 5),
                    focus_rating=completion_data.get("focus_rating", 5),
                    difficulty_rating=completion_data.get("difficulty_rating", 3),
                    notes=completion_data.get("notes", "")
                )
                history.append(completion)
            
            logger.info(f"Loaded {len(history)} completion events from database for user {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to load history from database: {e}")
            return []
    
    async def _persist_schedule_to_db(
        self, user_id: str, solution: ScheduleSolution, job_id: Optional[str]
    ):
        """Persist schedule to database."""
        try:
            from app.config.database.supabase import get_supabase
            
            supabase = get_supabase()
            
            # Prepare schedule blocks for database storage
            blocks = []
            for block in solution.blocks:
                block_data = {
                    "id": f"{user_id}_{block.task_id}_{int(block.start.timestamp())}",
                    "user_id": user_id,
                    "job_id": job_id,
                    "task_id": block.task_id,
                    "task_title": block.title,
                    "start_time": block.start.isoformat(),
                    "end_time": block.end.isoformat(),
                    "duration_minutes": int((block.end - block.start).total_seconds() / 60),
                    "block_type": "task",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "solution_score": solution.objective_value if hasattr(solution, 'objective_value') else None,
                        "job_id": job_id
                    }
                }
                blocks.append(block_data)
            
            # Insert schedule blocks into database
            if blocks:
                response = supabase.table("schedule_blocks").insert(blocks).execute()
                logger.info(f"Persisted {len(blocks)} schedule blocks to database for user {user_id}")
            
            # Also persist schedule summary
            schedule_summary = {
                "id": job_id or f"schedule_{user_id}_{int(datetime.utcnow().timestamp())}",
                "user_id": user_id,
                "job_id": job_id,
                "total_blocks": len(solution.blocks),
                "total_tasks": len(set(block.task_id for block in solution.blocks)),
                "objective_value": solution.objective_value if hasattr(solution, 'objective_value') else None,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": solution.metadata if hasattr(solution, 'metadata') else {}
            }
            
            supabase.table("schedules").insert(schedule_summary).execute()
            logger.info(f"Persisted schedule summary to database for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist schedule to database: {e}")
    
    async def _persist_run_to_db(self, run: SchedulerRun):
        """Persist run summary to database."""
        try:
            from app.config.database.supabase import get_supabase
            
            supabase = get_supabase()
            
            # Prepare run data for database storage
            run_data = {
                "id": run.run_id,
                "user_id": run.user_id,
                "job_id": run.job_id,
                "status": run.status,
                "start_time": run.start_time.isoformat(),
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "duration_seconds": int(run.duration.total_seconds()) if run.duration else None,
                "tasks_loaded": len(run.tasks_loaded) if hasattr(run, 'tasks_loaded') else None,
                "events_loaded": len(run.events_loaded) if hasattr(run, 'events_loaded') else None,
                "blocks_scheduled": len(run.solution.blocks) if run.solution else None,
                "objective_value": run.solution.objective_value if run.solution and hasattr(run.solution, 'objective_value') else None,
                "error_message": run.error_message if hasattr(run, 'error_message') else None,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "solver_used": run.solver_used if hasattr(run, 'solver_used') else None,
                    "optimization_time": run.optimization_time if hasattr(run, 'optimization_time') else None,
                    "memory_usage": run.memory_usage if hasattr(run, 'memory_usage') else None
                }
            }
            
            # Insert run summary into database
            supabase.table("scheduler_runs").insert(run_data).execute()
            logger.info(f"Persisted scheduler run {run.run_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to persist run to database: {e}")
    
    async def _get_recent_schedules_from_db(
        self, user_id: str, days_back: int
    ) -> List[ScheduleBlock]:
        """Get recent schedules from database."""
        try:
            from app.config.database.supabase import get_supabase
            from datetime import datetime, timedelta
            
            supabase = get_supabase()
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Query recent schedule blocks from database
            response = supabase.table("schedule_blocks").select("*").eq("user_id", user_id).gte("start_time", start_date.isoformat()).lte("end_time", end_date.isoformat()).order("start_time").execute()
            
            blocks = []
            for block_data in response.data:
                # Convert database block to scheduler ScheduleBlock
                start_time = datetime.fromisoformat(block_data["start_time"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(block_data["end_time"].replace('Z', '+00:00'))
                
                block = ScheduleBlock(
                    task_id=block_data["task_id"],
                    title=block_data["task_title"],
                    start=start_time,
                    end=end_time
                )
                blocks.append(block)
            
            logger.info(f"Loaded {len(blocks)} recent schedule blocks from database for user {user_id}")
            return blocks
            
        except Exception as e:
            logger.error(f"Failed to load recent schedules from database: {e}")
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


