"""
Main orchestration service for the scheduler subsystem.

Coordinates all components to provide the primary scheduling API used by
LangGraph tools and FastAPI endpoints.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from .domain import Task, BusyEvent, Preferences, ScheduleSolution, ScheduleBlock
from .optimization.time_index import TimeIndex
from .learning.completion_model import CompletionModel
from .learning.bandits import WeightTuner
from .optimization.solver import SchedulerSolver
from .optimization.fallback import greedy_fill
from .features import build_utilities
from .io.dto import ScheduleRequest, ScheduleResponse
from .io.repository import Repository
from .io.idempotency import check_and_put
from .telemetry import trace_run, emit_metrics

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Main orchestration service for intelligent task scheduling.
    
    Coordinates ML models, optimization, and persistence to provide
    production-grade scheduling capabilities.
    """
    
    def __init__(
        self,
        repo: Optional['Repository'] = None,
        model: Optional[CompletionModel] = None,
        tuner: Optional[WeightTuner] = None,
        solver: Optional[SchedulerSolver] = None
    ):
        """
        Initialize scheduler service.
        
        Args:
            repo: Data repository (auto-created if None)
            model: Completion probability model (auto-created if None)
            tuner: Weight tuning bandit (auto-created if None)
            solver: Constraint solver (auto-created if None)
        """
        # Import here to avoid circular imports
        from .io.repository import get_repository
        
        self.repo = repo or get_repository()
        self.model = model or CompletionModel()
        self.tuner = tuner or WeightTuner()
        
        try:
            self.solver = solver or SchedulerSolver()
            self.solver_available = True
        except ImportError:
            logger.warning("OR-Tools not available, using fallback scheduler only")
            self.solver = None
            self.solver_available = False
    
    @trace_run
    async def schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """
        Generate optimized schedule for user tasks.
        
        Args:
            request: Scheduling request with parameters
            
        Returns:
            Schedule response with blocks and metadata
        """
        try:
            # 1. Idempotency check
            if not request.dry_run:
                is_duplicate, cached_response = await check_and_put(request)
                if is_duplicate and cached_response:
                    logger.info(f"Returning cached schedule for user {request.user_id}")
                    return cached_response
            
            # 2. Load input data
            tasks, events, prefs, history = await self._load_inputs(request)
            
            if not tasks:
                return ScheduleResponse(
                    job_id=request.job_id,
                    feasible=True,
                    blocks=[],
                    metrics={'message': 'No tasks to schedule'},
                    explanations={}
                )
            
            # 3. Prepare time grid
            time_index = await self._prepare_time_index(request, prefs)
            
            # 4. Load/prepare ML models
            await self._prepare_models(request.user_id)
            
            # 5. Build utilities and context
            util_matrix, penalty_context = await build_utilities(
                self.model, tasks, time_index, prefs, events, history
            )
            
            # 6. Get penalty weights from bandit
            context = self._build_bandit_context(request, prefs, time_index)
            weights = self.tuner.suggest_weights(context)
            
            # 7. Attempt optimization
            solution = await self._solve_optimization(
                tasks, events, prefs, time_index, util_matrix, penalty_context, weights
            )
            
            # 8. Fallback if needed
            if not solution.feasible and self.solver_available:
                logger.warning("Optimization failed, trying fallback")
                solution = await self._solve_fallback(
                    tasks, events, prefs, time_index, util_matrix
                )
            
            # 9. Persist results
            if not request.dry_run and solution.feasible:
                await self._persist_results(request, solution, weights, penalty_context)
            
            # 10. Prepare response
            response = await self._build_response(request, solution, weights, penalty_context)
            
            # 11. Emit telemetry
            await self._emit_telemetry(request, solution, weights)
            
            return response
            
        except Exception as e:
            logger.error(f"Scheduling failed for user {request.user_id}: {e}", exc_info=True)
            
            # Return error response
            return ScheduleResponse(
                job_id=request.job_id,
                feasible=False,
                blocks=[],
                metrics={
                    'error': str(e),
                    'error_type': type(e).__name__
                },
                explanations={'error': f"Scheduling failed: {str(e)}"}
            )
    
    async def _load_inputs(
        self, request: ScheduleRequest
    ) -> tuple[List[Task], List[BusyEvent], Preferences, List]:
        """Load all input data needed for scheduling."""
        logger.debug(f"Loading inputs for user {request.user_id}")
        
        # Load data in parallel
        tasks_coro = self.repo.load_tasks(request.user_id, request.horizon_days)
        events_coro = self.repo.load_calendar_busy(request.user_id, request.horizon_days)
        prefs_coro = self.repo.load_preferences(request.user_id)
        history_coro = self.repo.load_history(request.user_id, horizon_days=60)
        
        tasks, events, prefs, history = await asyncio.gather(
            tasks_coro, events_coro, prefs_coro, history_coro
        )
        
        logger.debug(
            f"Loaded {len(tasks)} tasks, {len(events)} events, "
            f"{len(history)} history records"
        )
        
        return tasks, events, prefs, history
    
    async def _prepare_time_index(
        self, request: ScheduleRequest, prefs: Preferences
    ) -> TimeIndex:
        """Prepare time discretization for the scheduling horizon."""
        start_dt, end_dt = await self.repo.get_window(request.user_id, request.horizon_days)
        
        time_index = TimeIndex(
            timezone=prefs.timezone,
            start_dt=start_dt,
            end_dt=end_dt,
            granularity_minutes=prefs.session_granularity_minutes
        )
        
        logger.debug(f"Time index: {len(time_index)} slots over {time_index.horizon_days} days")
        
        return time_index
    
    async def _prepare_models(self, user_id: str):
        """Load or initialize ML models for the user."""
        # Load completion model
        model_loaded = await self.model.load(user_id)
        if not model_loaded:
            logger.info(f"No completion model found for user {user_id}, using defaults")
        
        # Load bandit state
        bandit_loaded = await self.tuner.load(user_id)
        if not bandit_loaded:
            logger.info(f"No bandit state found for user {user_id}, using defaults")
    
    def _build_bandit_context(
        self, request: ScheduleRequest, prefs: Preferences, time_index: TimeIndex
    ) -> Dict[str, Any]:
        """Build context for bandit weight selection."""
        return {
            'user_id': request.user_id,
            'horizon_days': request.horizon_days,
            'dow': time_index.start_dt.weekday(),
            'hour': time_index.start_dt.hour,
            'timezone': prefs.timezone,
            'workday_hours': (prefs.workday_start, prefs.workday_end),
            'max_daily_effort': prefs.max_daily_effort_minutes,
            'granularity': prefs.session_granularity_minutes
        }
    
    async def _solve_optimization(
        self,
        tasks: List[Task],
        events: List[BusyEvent],
        prefs: Preferences,
        time_index: TimeIndex,
        util_matrix: Dict[str, Dict[int, float]],
        penalty_context: Dict[str, Any],
        weights: Dict[str, float]
    ) -> ScheduleSolution:
        """Attempt constraint optimization solve."""
        if not self.solver_available:
            logger.info("Solver not available, skipping optimization")
            return ScheduleSolution(feasible=False, blocks=[], solver_status="no_solver")
        
        try:
            # Build learned parameters
            learned = {
                'util': util_matrix,
                'weights': weights,
                'ctx': penalty_context
            }
            
            # Build model
            model = self.solver.build(tasks, events, prefs, time_index, learned)
            
            # Solve
            solution = self.solver.solve(model)
            
            logger.info(
                f"Optimization completed: feasible={solution.feasible}, "
                f"status={solution.solver_status}, "
                f"blocks={len(solution.blocks)}, "
                f"time={solution.solve_time_ms}ms"
            )
            
            return solution
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}", exc_info=True)
            return ScheduleSolution(
                feasible=False, 
                blocks=[], 
                solver_status="error",
                diagnostics={'error': str(e)}
            )
    
    async def _solve_fallback(
        self,
        tasks: List[Task],
        events: List[BusyEvent],
        prefs: Preferences,
        time_index: TimeIndex,
        util_matrix: Dict[str, Dict[int, float]]
    ) -> ScheduleSolution:
        """Use fallback greedy solver."""
        try:
            # Get free slots
            free_slots = time_index.get_free_slots(events, prefs)
            
            # Run greedy scheduler
            solution = greedy_fill(tasks, free_slots, prefs, util_matrix, time_index)
            
            logger.info(
                f"Fallback scheduling completed: {len(solution.blocks)} blocks, "
                f"{len(solution.unscheduled_tasks)} unscheduled"
            )
            
            return solution
            
        except Exception as e:
            logger.error(f"Fallback scheduling failed: {e}", exc_info=True)
            return ScheduleSolution(
                feasible=False,
                blocks=[],
                solver_status="fallback_error",
                diagnostics={'fallback_error': str(e)}
            )
    
    async def _persist_results(
        self,
        request: ScheduleRequest,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        penalty_context: Dict[str, Any]
    ):
        """Persist scheduling results to database."""
        try:
            # Persist schedule blocks
            if solution.blocks:
                await self.repo.persist_schedule(
                    request.user_id, solution, job_id=request.job_id
                )
            
            # Persist run summary
            await self.repo.persist_run_summary(
                request.user_id, solution, weights, penalty_context
            )
            
            logger.debug(f"Persisted {len(solution.blocks)} blocks for user {request.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist results: {e}", exc_info=True)
    
    async def _build_response(
        self,
        request: ScheduleRequest,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        penalty_context: Dict[str, Any]
    ) -> ScheduleResponse:
        """Build final response object."""
        # Convert schedule blocks to DTO format
        response_blocks = []
        for block in solution.blocks:
            response_blocks.append(ScheduleBlock(
                task_id=block.task_id,
                title=penalty_context.get('tasks', {}).get(block.task_id, {}).get('title', 'Unknown'),
                start=block.start.isoformat(),
                end=block.end.isoformat(),
                provider="pulse",
                metadata={
                    'utility_score': block.utility_score,
                    'completion_probability': block.estimated_completion_probability,
                    'duration_minutes': block.duration_minutes
                }
            ))
        
        # Build metrics
        metrics = {
            'feasible': solution.feasible,
            'solver_status': solution.solver_status,
            'solve_time_ms': solution.solve_time_ms,
            'objective_value': solution.objective_value,
            'total_blocks': len(solution.blocks),
            'total_scheduled_minutes': solution.total_scheduled_minutes,
            'unscheduled_tasks': len(solution.unscheduled_tasks),
            'weights_used': weights
        }
        
        # Add diagnostics if available
        if solution.diagnostics:
            metrics.update(solution.diagnostics)
        
        # Build explanations
        explanations = self._build_explanations(solution, weights, penalty_context)
        
        return ScheduleResponse(
            job_id=request.job_id,
            feasible=solution.feasible,
            blocks=response_blocks,
            metrics=metrics,
            explanations=explanations
        )
    
    def _build_explanations(
        self,
        solution: ScheduleSolution,
        weights: Dict[str, float],
        penalty_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Build human-readable explanations for the schedule."""
        explanations = {}
        
        if solution.feasible:
            explanations['summary'] = (
                f"Successfully scheduled {len(solution.blocks)} blocks "
                f"across {solution.total_scheduled_minutes} minutes."
            )
            
            if solution.unscheduled_tasks:
                explanations['unscheduled'] = (
                    f"{len(solution.unscheduled_tasks)} tasks could not be scheduled. "
                    "This may be due to insufficient time or conflicting constraints."
                )
            
            # Explain key weights used
            key_weights = {k: v for k, v in weights.items() if v > 1.5}
            if key_weights:
                weight_desc = ", ".join(f"{k}={v:.1f}" for k, v in key_weights.items())
                explanations['optimization'] = f"Optimization emphasized: {weight_desc}"
                
        else:
            explanations['summary'] = "Could not generate a feasible schedule."
            
            # Try to explain why
            if 'infeasible_reason' in solution.diagnostics:
                explanations['reason'] = solution.diagnostics['infeasible_reason']
            elif solution.solver_status == "timeout":
                explanations['reason'] = "Optimization timed out before finding a solution."
            elif solution.solver_status == "no_solver":
                explanations['reason'] = "Constraint solver not available."
            else:
                explanations['reason'] = "Unknown scheduling failure."
        
        return explanations
    
    async def _emit_telemetry(
        self,
        request: ScheduleRequest,
        solution: ScheduleSolution,
        weights: Dict[str, float]
    ):
        """Emit telemetry metrics."""
        try:
            metrics = {
                'user_id': request.user_id,
                'horizon_days': request.horizon_days,
                'feasible': solution.feasible,
                'solver_status': solution.solver_status,
                'solve_time_ms': solution.solve_time_ms,
                'n_blocks': len(solution.blocks),
                'n_unscheduled': len(solution.unscheduled_tasks),
                'objective_value': solution.objective_value,
                'weights': weights
            }
            
            await emit_metrics('scheduler.run', metrics)
            
        except Exception as e:
            logger.warning(f"Failed to emit telemetry: {e}")
    
    async def update_learning(
        self,
        user_id: str,
        schedule_outcome: Dict[str, Any],
        user_feedback: Optional[Dict[str, Any]] = None
    ):
        """
        Update ML models based on scheduling outcomes.
        
        Args:
            user_id: User identifier
            schedule_outcome: Results from schedule execution
            user_feedback: Optional user satisfaction feedback
        """
        try:
            # Import here to avoid circular dependency
            from .learning.bandits import compute_reward
            from .adapt.updater import post_run_update
            
            # Compute reward signal
            reward = compute_reward(schedule_outcome, user_feedback)
            
            # Get recent context (would need to store from last schedule call)
            context = schedule_outcome.get('context', {})
            weights = schedule_outcome.get('weights', {})
            
            # Update bandit
            if context and weights:
                self.tuner.update(context, weights, reward)
                await self.tuner.save(user_id)
            
            # Update completion model if we have completion data
            await post_run_update(self.tuner, self.model, user_id, schedule_outcome)
            
            logger.info(f"Updated learning models for user {user_id}, reward={reward:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to update learning for user {user_id}: {e}", exc_info=True)
    
    async def get_schedule_preview(
        self, request: ScheduleRequest
    ) -> ScheduleResponse:
        """
        Get a preview of the schedule without persisting.
        
        Args:
            request: Schedule request with dry_run=True
            
        Returns:
            Schedule response for preview
        """
        preview_request = ScheduleRequest(
            user_id=request.user_id,
            horizon_days=request.horizon_days,
            dry_run=True,
            lock_existing=request.lock_existing,
            job_id=request.job_id
        )
        
        return await self.schedule(preview_request)
    
    async def reschedule_missed_tasks(
        self, user_id: str, horizon_days: int = 3
    ) -> ScheduleResponse:
        """
        Reschedule tasks that were missed or need adjustment.
        
        Args:
            user_id: User identifier
            horizon_days: Days ahead to reschedule
            
        Returns:
            New schedule for missed/rescheduled tasks
        """
        # Import here to avoid circular dependency
        from .adapt.rescheduler import reschedule_backlog
        
        try:
            response = await reschedule_backlog(user_id, horizon_days, self)
            logger.info(f"Rescheduled missed tasks for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to reschedule for user {user_id}: {e}", exc_info=True)
            
            return ScheduleResponse(
                job_id=None,
                feasible=False,
                blocks=[],
                metrics={'error': str(e)},
                explanations={'error': f"Rescheduling failed: {str(e)}"}
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of scheduler components."""
        return {
            'solver_available': self.solver_available,
            'model_fitted': self.model.is_fitted,
            'bandit_arms': len(self.tuner.arms) if self.tuner.arms else 0,
            'repository_connected': True,  # Would check actual connection
            'version': '1.0.0'
        }


# Global service instance
_scheduler_service = None

def get_scheduler_service() -> SchedulerService:
    """Get global scheduler service instance."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service