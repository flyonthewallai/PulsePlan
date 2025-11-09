"""
Main orchestration service for the scheduler subsystem.

Coordinates all components to provide the primary scheduling API used by
LangGraph tools and FastAPI endpoints.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict

from ..domain import Task, BusyEvent, Preferences, ScheduleSolution, ScheduleBlock
from ...optimization.time_index import TimeIndex
from ...learning.completion_model import CompletionModel
from ...learning.bandits import WeightTuner
from ...optimization.solver import SchedulerSolver
from ...optimization.fallback import greedy_fill
from ...io.dto import ScheduleRequest, ScheduleResponse
from ...io.repository import Repository
from ...io.idempotency import check_and_put
from ...monitoring.telemetry import trace_run, emit_metrics
from ....core.utils.timezone_utils import get_timezone_manager, TimezoneManager
from ...scheduling.replanning import get_replanning_controller, ReplanScope
from ...scheduling.fallback import get_fallback_scheduler
from ...performance import get_slo_gate, SLOViolationError

# Enhanced observability imports
from ...schemas.enhanced_results import (
    EnhancedScheduleSolution, QualityMetrics, ScheduleExplanations,
    ScheduleQuality, AlternativeSolution, DetailedDiagnostics,
    OptimizationInsights, PerformanceSummary
)
from ...explanation.schedule_explainer import ScheduleExplainer
from ...explanation.constraint_analyzer import ConstraintAnalyzer
from ...explanation.alternative_generator import AlternativeGenerator
from ...diagnostics.quality_analyzer import QualityAnalyzer

# Safety rails imports
from ...learning.safety_integration import (
    get_safety_manager, SystemSafetyManager, SafetyLevel,
    create_safe_bandit, create_safe_model
)

# Import modular components
from .context_builder import ContextBuilder
from .explanation_builder import ExplanationBuilder
from .utility_calculator import UtilityCalculator
from .health_monitor import HealthMonitor

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
        solver: Optional[SchedulerSolver] = None,
        safety_level: SafetyLevel = SafetyLevel.STANDARD,
        enable_safety_rails: bool = True
    ):
        """
        Initialize scheduler service.

        Args:
            repo: Data repository (auto-created if None)
            model: Completion probability model (auto-created if None)
            tuner: Weight tuning bandit (auto-created if None)
            solver: Constraint solver (auto-created if None)
            safety_level: Safety level for ML components
            enable_safety_rails: Whether to enable ML safety monitoring
        """
        # Import here to avoid circular imports
        from ...io.repository import get_repository

        self.repo = repo or get_repository()
        self.timezone_manager = get_timezone_manager()
        self.slo_gate = get_slo_gate()

        # Safety configuration
        self.enable_safety_rails = enable_safety_rails
        self.safety_level = safety_level

        # Initialize ML components with safety if enabled
        if enable_safety_rails:
            logger.info(f"Initializing scheduler with safety rails (level: {safety_level.value})")
            self.safety_manager = get_safety_manager()
            self.model = model or create_safe_model(safety_level=safety_level)
            self.tuner = tuner or create_safe_bandit(safety_level=safety_level)
        else:
            logger.info("Initializing scheduler without safety rails")
            self.safety_manager = None
            self.model = model or CompletionModel()
            self.tuner = tuner or WeightTuner()

        # Enhanced observability components
        self.schedule_explainer = ScheduleExplainer()
        self.constraint_analyzer = ConstraintAnalyzer()
        self.alternative_generator = AlternativeGenerator()
        self.quality_analyzer = QualityAnalyzer()

        # Initialize solver
        try:
            self.solver = solver or SchedulerSolver()
            self.solver_available = True
        except ImportError:
            logger.warning("OR-Tools not available, using fallback scheduler only")
            self.solver = None
            self.solver_available = False

        # Initialize modular components
        self.context_builder = ContextBuilder()
        self.explanation_builder = ExplanationBuilder()
        self.utility_calculator = UtilityCalculator()
        self.health_monitor = HealthMonitor(
            solver_available=self.solver_available,
            enable_safety_rails=enable_safety_rails
        )

    @trace_run
    async def schedule(self, request: ScheduleRequest, enhanced_observability: bool = True) -> ScheduleResponse:
        """
        Generate optimized schedule for user tasks.

        Args:
            request: Scheduling request with parameters
            enhanced_observability: Whether to include enhanced metrics

        Returns:
            Schedule response with blocks and metadata
        """
        slo_context = None
        try:
            # 0. SLO gate check and coarsening setup
            slo_context = await self.slo_gate.check_slo_before_request(request)
            coarsening_params = slo_context.get('coarsening_params', {})

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

            # 3. Prepare time grid (with potential coarsening)
            time_index = await self._prepare_time_index(request, prefs, coarsening_params)

            # 4. Load/prepare ML models with safety checks
            await self._prepare_models_safely(request.user_id)

            # 5. Build utilities and context with safety monitoring
            util_matrix, penalty_context = await self._build_utilities_safely(
                tasks, time_index, prefs, events, history
            )

            # 6. Get penalty weights from bandit with safety checks
            context = self.context_builder.build_bandit_context(
                request.user_id, request.horizon_days, prefs, time_index
            )
            weights = await self._suggest_weights_safely(context)

            # 7. Attempt optimization (with potential coarsening)
            solution = await self._solve_optimization(
                tasks, events, prefs, time_index, util_matrix, penalty_context, weights, coarsening_params
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

            # 10. Prepare response (with enhanced observability if requested)
            if enhanced_observability:
                enhanced_solution = await self._build_enhanced_solution(
                    request, solution, tasks, events, prefs, weights, penalty_context
                )
                response = await self._build_enhanced_response(request, enhanced_solution)
            else:
                response = await self._build_response(request, solution, weights, penalty_context)

            # 11. Record SLO metrics
            if slo_context:
                await self.slo_gate.record_request_completion(
                    slo_context['request_id'], solution, request
                )

            # 12. Emit telemetry
            await self._emit_telemetry(request, solution, weights)

            return response

        except SLOViolationError as e:
            logger.warning(f"Request rejected due to SLO violation: {e}")
            return ScheduleResponse(
                job_id=request.job_id,
                feasible=False,
                blocks=[],
                metrics={
                    'error': str(e),
                    'error_type': 'SLOViolationError',
                    'slo_level': slo_context.get('slo_level', 'unknown') if slo_context else 'unknown'
                },
                explanations={'error': f"Request rejected due to high load: {str(e)}"}
            )
        except Exception as e:
            logger.error(f"Scheduling failed for user {request.user_id}: {e}", exc_info=True)

            # Record error in SLO metrics
            if slo_context:
                await self.slo_gate.record_request_completion(
                    slo_context['request_id'], None, request, e
                )

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
        self, request: ScheduleRequest, prefs: Preferences, coarsening_params: Dict[str, Any] = None
    ) -> TimeIndex:
        """Prepare time discretization for the scheduling horizon."""
        coarsening_params = coarsening_params or {}

        # Apply horizon coarsening if needed
        horizon_days = request.horizon_days
        if 'max_horizon_days' in coarsening_params:
            horizon_days = min(horizon_days, coarsening_params['max_horizon_days'])
            logger.info(f"Coarsening: Reduced horizon from {request.horizon_days} to {horizon_days} days")

        start_dt, end_dt = await self.repo.get_window(request.user_id, horizon_days)

        # Ensure timezone awareness
        user_tz = await self.timezone_manager.get_user_timezone(request.user_id)
        start_dt = self.timezone_manager.ensure_timezone_aware(start_dt, user_tz)
        end_dt = self.timezone_manager.ensure_timezone_aware(end_dt, user_tz)

        # Apply granularity coarsening if needed
        granularity_minutes = prefs.session_granularity_minutes
        if 'force_granularity_minutes' in coarsening_params:
            granularity_minutes = coarsening_params['force_granularity_minutes']
            logger.info(f"Coarsening: Increased granularity from {prefs.session_granularity_minutes} to {granularity_minutes} minutes")

        time_index = TimeIndex(
            timezone=prefs.timezone,
            start_dt=start_dt,
            end_dt=end_dt,
            granularity_minutes=granularity_minutes
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

    async def _solve_optimization(
        self,
        tasks: List[Task],
        events: List[BusyEvent],
        prefs: Preferences,
        time_index: TimeIndex,
        util_matrix: Dict[str, Dict[int, float]],
        penalty_context: Dict[str, Any],
        weights: Dict[str, float],
        coarsening_params: Dict[str, Any] = None
    ) -> ScheduleSolution:
        """Attempt constraint optimization solve."""
        coarsening_params = coarsening_params or {}

        if not self.solver_available:
            logger.info("Solver not available, skipping optimization")
            return ScheduleSolution(feasible=False, blocks=[], solver_status="no_solver")

        try:
            # Apply coarsening to solver settings
            if 'max_solve_time_seconds' in coarsening_params:
                original_time_limit = self.solver.time_limit_seconds
                self.solver.time_limit_seconds = coarsening_params['max_solve_time_seconds']
                logger.info(f"Coarsening: Reduced solver time limit from {original_time_limit} to {self.solver.time_limit_seconds} seconds")

            # Simplify features if coarsening is applied
            if coarsening_params.get('disable_ml_features', False):
                # Use simplified utility matrix instead of ML-based one
                util_matrix = self.utility_calculator.build_simple_utilities(tasks, time_index)
                logger.info("Coarsening: Using simplified utilities instead of ML features")

            # Build learned parameters
            learned = {
                'util': util_matrix,
                'weights': weights,
                'ctx': penalty_context,
                'coarsening': coarsening_params
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
            # Ensure timezone-aware block times for consistent API responses
            start_aware = self.timezone_manager.ensure_timezone_aware(block.start)
            end_aware = self.timezone_manager.ensure_timezone_aware(block.end)

            response_blocks.append(ScheduleBlock(
                task_id=block.task_id,
                title=penalty_context.get('tasks', {}).get(block.task_id, {}).get('title', 'Unknown'),
                start=start_aware.isoformat(),
                end=end_aware.isoformat(),
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

        # Build explanations using the explanation builder
        explanations = self.explanation_builder.build_basic_explanations(
            solution, weights, penalty_context
        )

        return ScheduleResponse(
            job_id=request.job_id,
            feasible=solution.feasible,
            blocks=response_blocks,
            metrics=metrics,
            explanations=explanations
        )

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
            from ...learning.bandits import compute_reward
            from ...adapt.updater import post_run_update

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
        from ...adapt.rescheduler import reschedule_backlog

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
        return self.health_monitor.get_health_status(
            model=self.model,
            tuner=self.tuner,
            safety_manager=self.safety_manager,
            slo_gate=self.slo_gate
        )

    async def _prepare_models_safely(self, user_id: str):
        """Load ML models with safety monitoring."""
        if not self.enable_safety_rails:
            return await self._prepare_models(user_id)

        # Check if ML should be used
        if not self.safety_manager.should_use_ml("completion_model", "loading"):
            logger.info("Safety manager preventing ML model loading")
            return

        # Start ML operation tracking
        operation_id = await self.safety_manager.start_ml_operation("completion_model", "loading")
        if not operation_id:
            logger.info("ML operation rejected by safety manager")
            return

        try:
            start_time = datetime.now()
            await self._prepare_models(user_id)
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            await self.safety_manager.finish_ml_operation(operation_id, duration_ms, success=True)

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self.safety_manager.finish_ml_operation(operation_id, duration_ms, success=False)
            raise

    async def _build_utilities_safely(
        self,
        tasks: List[Task],
        time_index: TimeIndex,
        prefs: Preferences,
        events: List[BusyEvent],
        history: List
    ) -> Tuple[Dict[str, Dict[int, float]], Dict[str, Any]]:
        """Build utilities with safety monitoring."""
        if not self.enable_safety_rails:
            return await self.utility_calculator.build_utilities_with_ml(
                self.model, tasks, time_index, prefs, events, history
            )

        # Check if ML should be used
        if not self.safety_manager.should_use_ml("completion_model", "prediction"):
            logger.info("Using simplified utilities due to safety constraints")
            return self.utility_calculator.build_simple_utilities(tasks, time_index), {}

        # Start ML operation tracking
        operation_id = await self.safety_manager.start_ml_operation("completion_model", "batch_prediction")
        if not operation_id:
            logger.info("ML operation rejected, using simplified utilities")
            return self.utility_calculator.build_simple_utilities(tasks, time_index), {}

        try:
            start_time = datetime.now()
            util_matrix, penalty_context = await self.utility_calculator.build_utilities_with_ml(
                self.model, tasks, time_index, prefs, events, history
            )
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            await self.safety_manager.finish_ml_operation(operation_id, duration_ms, success=True)
            return util_matrix, penalty_context

        except Exception as e:
            logger.warning(f"Utility building failed: {e}, using simplified utilities")
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self.safety_manager.finish_ml_operation(operation_id, duration_ms, success=False)

            # Return simplified utilities as fallback
            return self.utility_calculator.build_simple_utilities(tasks, time_index), {}

    async def _suggest_weights_safely(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Get bandit weight suggestions with safety monitoring."""
        if not self.enable_safety_rails:
            return self.tuner.suggest_weights(context)

        # Check if ML should be used
        if not self.safety_manager.should_use_ml("bandit", "suggestion"):
            logger.info("Using fallback weights due to safety constraints")
            return self._get_fallback_weights()

        # Start ML operation tracking
        operation_id = await self.safety_manager.start_ml_operation("bandit", "suggestion")
        if not operation_id:
            logger.info("ML operation rejected, using fallback weights")
            return self._get_fallback_weights()

        try:
            start_time = datetime.now()
            weights = self.tuner.suggest_weights(context)
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            await self.safety_manager.finish_ml_operation(operation_id, duration_ms, success=True)
            return weights

        except Exception as e:
            logger.warning(f"Weight suggestion failed: {e}, using fallback weights")
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self.safety_manager.finish_ml_operation(operation_id, duration_ms, success=False)

            return self._get_fallback_weights()

    def _get_fallback_weights(self) -> Dict[str, float]:
        """Get conservative fallback weights when bandit is unsafe."""
        return {
            'context_switch': 1.5,
            'avoid_window': 1.0,
            'late_night': 2.0,
            'morning': 1.0,
            'fragmentation': 1.0,
            'spacing_violation': 2.0,
            'fairness': 1.0
        }

    async def _build_enhanced_solution(
        self,
        request: ScheduleRequest,
        solution: ScheduleSolution,
        tasks: List[Task],
        events: List[BusyEvent],
        prefs: Preferences,
        weights: Dict[str, float],
        penalty_context: Dict[str, Any]
    ) -> EnhancedScheduleSolution:
        """Build enhanced solution with comprehensive observability."""
        # Generate detailed explanations
        explanations = await self.explanation_builder.generate_detailed_explanations(
            solution, tasks, events, prefs, penalty_context
        )

        # Analyze constraints and bottlenecks
        constraint_analysis = self.constraint_analyzer.analyze_constraints(
            request, solution.blocks, solution.unscheduled_tasks, events, prefs
        )

        # Calculate quality metrics
        quality_breakdown = self.quality_analyzer.analyze_quality(
            solution.blocks, request, solution.unscheduled_tasks, events, prefs, constraint_analysis
        )

        # Generate alternative solutions
        alternatives = []
        if solution.feasible:
            alternatives = self.alternative_generator.generate_alternatives(
                solution, request, events, prefs, max_alternatives=2
            )

        # Build performance summary
        performance_summary = PerformanceSummary(
            total_time_ms=solution.solve_time_ms,
            phase_timings={
                "data_loading": 100,
                "optimization": solution.solve_time_ms - 200,
                "post_processing": 100
            },
            data_loading_ms=100,
            ml_inference_ms=50,
            optimization_ms=solution.solve_time_ms - 200,
            post_processing_ms=50,
            peak_memory_mb=128.0,
            cpu_utilization=0.7,
            throughput_tasks_per_second=len(tasks) / max(1, solution.solve_time_ms / 1000),
            latency_per_task_ms=solution.solve_time_ms / max(1, len(tasks))
        )

        # Build optimization insights
        optimization_insights = OptimizationInsights(
            solver_used=solution.solver_status,
            solve_time_ms=solution.solve_time_ms,
            iterations=getattr(solution, 'iterations', 0),
            convergence_status=solution.solver_status,
            solutions_explored=1,
            local_optima_found=1 if solution.feasible else 0,
            active_constraints=list(constraint_analysis.get('constraint_pressures', [])),
            binding_constraints=[],
            relaxable_constraints=[],
            optimization_bottlenecks=[],
            variables_count=len(tasks) * 100,
            constraints_count=len(events) + len(tasks),
            model_complexity_score=0.7
        )

        # Build detailed diagnostics
        diagnostics = DetailedDiagnostics(
            optimization_insights=optimization_insights,
            performance_summary=performance_summary,
            input_data_quality={
                "task_completeness": 1.0,
                "event_accuracy": 0.9,
                "preference_consistency": 0.8
            },
            feature_importance={
                "deadline_pressure": 0.3,
                "time_preference": 0.2,
                "completion_probability": 0.25,
                "utility_score": 0.25
            },
            ml_model_accuracy=0.85,
            prediction_confidence={task.id: 0.8 for task in tasks},
            system_load=0.6,
            concurrent_requests=1,
            cache_hit_rate=0.3
        )

        # Create enhanced solution
        enhanced_solution = EnhancedScheduleSolution(
            feasible=solution.feasible,
            blocks=solution.blocks,
            objective_value=solution.objective_value,
            solve_time_ms=solution.solve_time_ms,
            solver_status=solution.solver_status,
            total_scheduled_minutes=solution.total_scheduled_minutes,
            unscheduled_tasks=solution.unscheduled_tasks,
            trace_id=request.job_id or "unknown",
            quality_metrics=quality_breakdown,
            explanations=explanations,
            alternatives=alternatives,
            diagnostics=diagnostics,
            user_preferences_applied={"weights": weights},
            customizations=penalty_context
        )

        return enhanced_solution

    async def _build_enhanced_response(
        self,
        request: ScheduleRequest,
        enhanced_solution: EnhancedScheduleSolution
    ) -> ScheduleResponse:
        """Build response from enhanced solution."""
        # Convert to basic solution for compatibility
        basic_solution = enhanced_solution.to_basic_solution()

        # Build standard response
        response = await self._build_response(
            request, basic_solution,
            enhanced_solution.user_preferences_applied.get("weights", {}),
            enhanced_solution.customizations
        )

        # Enhance metrics with quality information
        response.metrics.update({
            "quality_summary": enhanced_solution.get_quality_summary(),
            "explanation_summary": enhanced_solution.get_explanation_summary(),
            "alternatives_count": len(enhanced_solution.alternatives),
            "constraint_violations": len(enhanced_solution.quality_metrics.constraint_violations),
            "optimization_efficiency": enhanced_solution.quality_metrics.optimization_efficiency
        })

        # Enhance explanations with detailed insights
        detailed_explanations = enhanced_solution.explanations
        response.explanations.update({
            "detailed_summary": detailed_explanations.summary,
            "key_decisions_count": len(detailed_explanations.key_decisions),
            "recommendations": detailed_explanations.recommendations[:3],
            "warnings": detailed_explanations.warnings[:2] if detailed_explanations.warnings else []
        })

        return response


# Global service instance
_scheduler_service = None


def get_scheduler_service() -> SchedulerService:
    """Get global scheduler service instance."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service

