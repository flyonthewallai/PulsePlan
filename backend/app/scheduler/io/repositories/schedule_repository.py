"""
Schedule repository for scheduler data access.

Handles persisting and retrieving schedule solutions from various storage backends.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from .base_repository import BaseScheduleRepository
from ...core.domain import ScheduleSolution, ScheduleBlock, SchedulerRun

logger = logging.getLogger(__name__)


class ScheduleRepository(BaseScheduleRepository):
    """Repository for schedule data access operations."""

    def __init__(self, storage_backend):
        """
        Initialize schedule repository.

        Args:
            storage_backend: Storage backend instance
        """
        self.storage = storage_backend

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
            if self.storage.backend_type == "memory":
                await self._persist_schedule_to_memory(user_id, solution)
            elif self.storage.backend_type == "database":
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

            if self.storage.backend_type == "memory":
                await self._persist_run_to_memory(user_id, run)
            elif self.storage.backend_type == "database":
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
            if self.storage.backend_type == "memory":
                return await self._get_recent_schedules_from_memory(user_id, days_back)
            elif self.storage.backend_type == "database":
                return await self._get_recent_schedules_from_db(user_id, days_back)
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to get recent schedules for user {user_id}: {e}")
            return []

    async def _persist_schedule_to_memory(self, user_id: str, solution: ScheduleSolution):
        """Persist schedule to memory storage."""
        self.storage.set_schedules(user_id, solution.blocks)
        logger.debug(f"Persisted {len(solution.blocks)} blocks for user {user_id}")

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

    async def _persist_run_to_memory(self, user_id: str, run: SchedulerRun):
        """Persist run summary to memory storage."""
        runs = self.storage.get_runs(user_id)
        runs.append(run)

        # Keep only recent runs
        runs = runs[-100:]

        self.storage.set_runs(user_id, runs)

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

    async def _get_recent_schedules_from_memory(
        self, user_id: str, days_back: int
    ) -> List[ScheduleBlock]:
        """Get recent schedules from memory storage."""
        blocks = self.storage.get_schedules(user_id)

        # Filter to recent blocks
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_blocks = [
            block for block in blocks
            if block.start >= cutoff_date
        ]

        return recent_blocks

    async def _get_recent_schedules_from_db(
        self, user_id: str, days_back: int
    ) -> List[ScheduleBlock]:
        """Get recent schedules from database."""
        try:
            from app.config.database.supabase import get_supabase

            supabase = get_supabase()

            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # Query recent schedule blocks from database
            response = supabase.table("schedule_blocks").select("*").eq(
                "user_id", user_id
            ).gte("start_time", start_date.isoformat()).lte(
                "end_time", end_date.isoformat()
            ).order("start_time").execute()

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
