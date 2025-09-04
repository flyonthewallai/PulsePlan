"""
FastAPI integration for the scheduler subsystem.

Provides REST API endpoints for scheduling operations, status monitoring,
and configuration management.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .service import get_scheduler_service, SchedulerService
from .io.dto import (
    ScheduleRequest, ScheduleResponse, ScheduleJobStatus,
    TaskUpdateRequest, PreferencesUpdateRequest, FeedbackRequest,
    DiagnosticsRequest, DiagnosticsResponse, ConfigUpdateRequest,
    SchedulerHealth
)
from .config import get_config, get_config_manager
from .telemetry import get_metrics, get_tracer, get_telemetry_health, monitor_performance
from .adapt.rescheduler import get_reschedule_metrics
from .adapt.evaluator import get_quality_tracker
from .adapt.updater import get_feedback_processor, get_performance_monitor

logger = logging.getLogger(__name__)

# Create router
scheduler_router = APIRouter(prefix="/schedule", tags=["scheduling"])

# Job tracking for background operations
background_jobs: Dict[str, Dict[str, Any]] = {}


def get_scheduler() -> SchedulerService:
    """Dependency to get scheduler service."""
    return get_scheduler_service()


@scheduler_router.post("/run", response_model=ScheduleResponse)
@monitor_performance("schedule_run")
async def run_scheduling(
    request: ScheduleRequest,
    background_tasks: BackgroundTasks,
    scheduler: SchedulerService = Depends(get_scheduler)
) -> ScheduleResponse:
    """
    Execute scheduling for a user.
    
    Generates an optimized schedule based on tasks, preferences,
    and calendar constraints.
    """
    try:
        # Validate request
        config = get_config()
        if request.horizon_days > config.max_horizon_days:
            raise HTTPException(
                status_code=400,
                detail=f"horizon_days cannot exceed {config.max_horizon_days}"
            )
        
        # Execute scheduling
        response = await scheduler.schedule(request)
        
        # Start background learning update if successful
        if response.feasible and not request.dry_run:
            background_tasks.add_task(
                _update_learning_models,
                scheduler,
                request.user_id,
                response
            )
        
        return response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Scheduling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal scheduling error")


@scheduler_router.post("/preview", response_model=ScheduleResponse)
@monitor_performance("schedule_preview")
async def preview_schedule(
    request: ScheduleRequest,
    scheduler: SchedulerService = Depends(get_scheduler)
) -> ScheduleResponse:
    """
    Preview a schedule without persisting changes.
    
    Useful for showing users what a schedule would look like
    before committing to it.
    """
    try:
        # Force dry run for preview
        preview_request = ScheduleRequest(
            user_id=request.user_id,
            horizon_days=request.horizon_days,
            dry_run=True,
            lock_existing=request.lock_existing,
            options=request.options
        )
        
        return await scheduler.get_schedule_preview(preview_request)
        
    except Exception as e:
        logger.error(f"Schedule preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Preview generation failed")


@scheduler_router.post("/reschedule", response_model=ScheduleResponse)
@monitor_performance("reschedule")
async def reschedule_missed_tasks(
    user_id: str,
    horizon_days: int = Query(default=3, ge=1, le=14),
    scheduler: SchedulerService = Depends(get_scheduler)
) -> ScheduleResponse:
    """
    Reschedule missed or problematic tasks.
    
    Analyzes missed tasks and schedule conflicts to generate
    an updated schedule with higher urgency for missed items.
    """
    try:
        return await scheduler.reschedule_missed_tasks(user_id, horizon_days)
        
    except Exception as e:
        logger.error(f"Rescheduling failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Rescheduling failed")


@scheduler_router.post("/feedback")
@monitor_performance("feedback_processing")
async def submit_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """
    Submit user feedback on schedule quality.
    
    Feedback is used to improve future scheduling through
    machine learning model updates.
    """
    try:
        # Process feedback in background
        background_tasks.add_task(
            _process_user_feedback,
            scheduler,
            feedback.dict()
        )
        
        return {"status": "feedback_received", "user_id": feedback.user_id}
        
    except Exception as e:
        logger.error(f"Feedback processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Feedback processing failed")


@scheduler_router.get("/jobs/{job_id}", response_model=ScheduleJobStatus)
async def get_job_status(job_id: str) -> ScheduleJobStatus:
    """
    Get status of a background scheduling job.
    
    Returns job progress, completion status, and results.
    """
    job = background_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ScheduleJobStatus(**job)


@scheduler_router.get("/health", response_model=SchedulerHealth)
async def get_health_status(
    scheduler: SchedulerService = Depends(get_scheduler)
) -> SchedulerHealth:
    """
    Get health status of scheduler components.
    
    Returns component status, version info, and basic metrics.
    """
    try:
        # Get component health
        health_data = scheduler.get_health_status()
        
        # Add telemetry health
        telemetry_health = await get_telemetry_health()
        health_data['telemetry'] = telemetry_health
        
        # Add metrics health
        metrics = get_metrics()
        recent_metrics = metrics.get_metrics(since=datetime.now().replace(hour=0, minute=0))
        health_data['metrics'] = {
            'total_metrics': len(recent_metrics),
            'counters': len(metrics.counters),
            'gauges': len(metrics.gauges)
        }
        
        # Determine overall status
        overall_status = "healthy"
        if not health_data.get('solver_available', True):
            overall_status = "degraded"
        
        return SchedulerHealth(
            status=overall_status,
            components=health_data,
            version="1.0.0",
            uptime_seconds=0.0,  # Would track actual uptime
            last_schedule_time=datetime.now()  # Would track last successful schedule
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return SchedulerHealth(
            status="unhealthy",
            components={"error": str(e)},
            version="1.0.0",
            uptime_seconds=0.0
        )


@scheduler_router.get("/diagnostics", response_model=DiagnosticsResponse)
async def get_diagnostics(
    request: DiagnosticsRequest = Depends(),
    scheduler: SchedulerService = Depends(get_scheduler)
) -> DiagnosticsResponse:
    """
    Get comprehensive diagnostics for troubleshooting.
    
    Returns performance metrics, model statistics, and
    optimization recommendations.
    """
    try:
        # Get performance metrics
        performance_monitor = get_performance_monitor()
        performance_trends = performance_monitor.get_performance_trends(request.user_id)
        
        # Get quality metrics
        quality_tracker = get_quality_tracker()
        quality_trends = quality_tracker.get_trends(request.user_id)
        
        # Get reschedule metrics
        reschedule_metrics = get_reschedule_metrics()
        reschedule_stats = reschedule_metrics.get_stats(request.user_id)
        
        # Build summary
        summary = {
            'performance': performance_trends,
            'quality': quality_trends,
            'rescheduling': reschedule_stats
        }
        
        # Generate recommendations
        recommendations = _generate_recommendations(summary)
        
        return DiagnosticsResponse(
            user_id=request.user_id,
            summary=summary,
            recent_runs=[],  # Would populate from actual data
            model_metrics=None,  # Would populate if requested
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Diagnostics failed for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Diagnostics generation failed")


@scheduler_router.get("/metrics")
async def get_metrics_data(
    since_hours: int = Query(default=1, ge=1, le=24),
    metric_names: Optional[List[str]] = Query(default=None)
):
    """
    Get scheduling metrics for monitoring.
    
    Returns performance and usage metrics for the specified time period.
    """
    try:
        metrics = get_metrics()
        since_time = datetime.now().replace(microsecond=0) - timedelta(hours=since_hours)
        
        recent_metrics = metrics.get_metrics(since=since_time)
        
        # Filter by metric names if specified
        if metric_names:
            recent_metrics = [
                m for m in recent_metrics 
                if any(name in m.name for name in metric_names)
            ]
        
        # Convert to response format
        metrics_data = [m.to_dict() for m in recent_metrics]
        
        return {
            "metrics": metrics_data,
            "total_count": len(metrics_data),
            "time_range": {
                "start": since_time.isoformat(),
                "end": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")


@scheduler_router.post("/config/update")
async def update_configuration(
    updates: ConfigUpdateRequest,
    background_tasks: BackgroundTasks
):
    """
    Update scheduler configuration at runtime.
    
    Allows dynamic configuration changes without restart.
    Only safe configuration changes are allowed.
    """
    try:
        config_manager = get_config_manager()
        
        # Convert request to update dictionary
        update_dict = {}
        if updates.solver_time_limit_seconds is not None:
            update_dict['solver'] = {'time_limit_seconds': updates.solver_time_limit_seconds}
        if updates.bandit_exploration_rate is not None:
            update_dict['learning'] = {'bandit_exploration_rate': updates.bandit_exploration_rate}
        if updates.default_weights is not None:
            update_dict['default_weights'] = updates.default_weights
        if updates.feature_config is not None:
            update_dict['features'] = updates.feature_config
        
        # Apply configuration update
        config_manager.update_config(update_dict)
        
        return {"status": "configuration_updated", "updates": update_dict}
        
    except Exception as e:
        logger.error(f"Configuration update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Configuration update failed")


@scheduler_router.get("/config/export")
async def export_configuration(format: str = Query(default="yaml")):
    """
    Export current configuration.
    
    Returns configuration in YAML or JSON format for backup/review.
    """
    try:
        config_manager = get_config_manager()
        config_string = config_manager.export_config(format)
        
        media_type = "application/x-yaml" if format == "yaml" else "application/json"
        
        return JSONResponse(
            content={"config": config_string},
            media_type=media_type
        )
        
    except Exception as e:
        logger.error(f"Configuration export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Configuration export failed")


# Background task functions

async def _update_learning_models(
    scheduler: SchedulerService,
    user_id: str,
    response: ScheduleResponse
):
    """Background task to update learning models."""
    try:
        # Build schedule outcome from response
        schedule_outcome = {
            'user_id': user_id,
            'feasible': response.feasible,
            'blocks_count': len(response.blocks),
            'objective_value': response.metrics.get('objective_value', 0),
            'context': response.metrics.get('context', {}),
            'weights': response.metrics.get('weights_used', {}),
            'scheduled_blocks': [block.dict() for block in response.blocks]
        }
        
        # Update learning models
        await scheduler.update_learning(user_id, schedule_outcome)
        
    except Exception as e:
        logger.error(f"Learning update failed for user {user_id}: {e}")


async def _process_user_feedback(
    scheduler: SchedulerService,
    feedback_data: Dict[str, Any]
):
    """Background task to process user feedback."""
    try:
        feedback_processor = get_feedback_processor()
        
        # Process feedback
        insights = await feedback_processor.process_feedback(
            feedback_data['user_id'],
            feedback_data
        )
        
        # Check if feedback triggers rescheduling
        if insights.get('low_satisfaction') or insights.get('high_rescheduling'):
            await scheduler.reschedule_missed_tasks(
                feedback_data['user_id'],
                horizon_days=3
            )
        
    except Exception as e:
        logger.error(f"Feedback processing failed: {e}")


def _generate_recommendations(summary: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations from diagnostics."""
    recommendations = []
    
    performance = summary.get('performance', {})
    quality = summary.get('quality', {})
    rescheduling = summary.get('rescheduling', {})
    
    # Performance recommendations
    if performance.get('insufficient_data'):
        recommendations.append("Insufficient performance data - continue using scheduler to gather metrics")
    else:
        trends = performance.get('trends', {})
        if 'completion_rate' in trends and not trends['completion_rate'].get('improving', True):
            recommendations.append("Completion rates declining - consider adjusting time estimates or preferences")
    
    # Quality recommendations
    if quality.get('insufficient_data'):
        recommendations.append("Insufficient quality data - provide feedback to improve recommendations")
    else:
        if quality.get('latest_score', 1.0) < 0.7:
            recommendations.append("Schedule quality below target - review preferences and constraints")
    
    # Rescheduling recommendations
    total_reschedules = rescheduling.get('total_reschedules', 0)
    if total_reschedules > 10:
        success_rate = rescheduling.get('success_rate', 1.0)
        if success_rate < 0.8:
            recommendations.append("High rescheduling frequency with low success - consider more realistic time estimates")
    
    # Default recommendation
    if not recommendations:
        recommendations.append("Scheduler performing well - no specific optimizations needed")
    
    return recommendations[:5]  # Limit to top 5 recommendations


# Note: Exception handlers should be registered on the main FastAPI app, not on routers