"""
LangGraph tools for scheduler integration.

Provides tools that can be used within LangGraph workflows
for intelligent scheduling operations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..core.service import get_scheduler_service
from ..io.dto import ScheduleRequest, ScheduleResponse
from ..core.config import get_config
from ..monitoring.telemetry import monitor_performance, get_scheduler_logger

logger = get_scheduler_logger()


@monitor_performance("langgraph_scheduling_tool")
async def scheduling_tool(
    user_id: str,
    horizon_days: int = 7,
    dry_run: bool = False,
    lock_existing: bool = True,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    LangGraph tool for intelligent task scheduling.
    
    Generates optimized schedules using constraint satisfaction,
    machine learning, and user preferences.
    
    Args:
        user_id: User identifier for scheduling
        horizon_days: Number of days to schedule ahead (1-30)
        dry_run: If True, preview only without persisting
        lock_existing: If True, preserve existing schedule blocks
        options: Additional options for scheduling
        
    Returns:
        Dictionary with scheduling results and metadata
    """
    try:
        # Validate inputs
        config = get_config()
        if not 1 <= horizon_days <= config.max_horizon_days:
            return {
                "success": False,
                "error": f"horizon_days must be between 1 and {config.max_horizon_days}",
                "error_type": "validation_error"
            }
        
        # Create scheduling request
        request = ScheduleRequest(
            user_id=user_id,
            horizon_days=horizon_days,
            dry_run=dry_run,
            lock_existing=lock_existing,
            options=options or {}
        )
        
        # Execute scheduling
        scheduler = get_scheduler_service()
        response = await scheduler.schedule(request)
        
        # Convert response to tool output format
        result = {
            "success": True,
            "feasible": response.feasible,
            "schedule": {
                "blocks": [
                    {
                        "task_id": block.task_id,
                        "title": block.title,
                        "start": block.start,
                        "end": block.end,
                        "duration_minutes": block.duration_minutes,
                        "metadata": block.metadata
                    }
                    for block in response.blocks
                ],
                "total_scheduled_minutes": response.total_scheduled_minutes,
                "total_blocks": len(response.blocks)
            },
            "metrics": {
                "solver_status": response.metrics.get("solver_status"),
                "solve_time_ms": response.metrics.get("solve_time_ms"),
                "objective_value": response.metrics.get("objective_value"),
                "unscheduled_tasks": response.metrics.get("unscheduled_tasks", 0)
            },
            "explanations": response.explanations
        }
        
        # Add scheduling insights
        if response.feasible:
            result["insights"] = _generate_scheduling_insights(response)
        else:
            result["failure_analysis"] = _analyze_scheduling_failure(response)
        
        logger.info(
            f"Scheduling tool completed for user {user_id}: "
            f"feasible={response.feasible}, blocks={len(response.blocks)}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Scheduling tool failed for user {user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@monitor_performance("langgraph_reschedule_tool")
async def reschedule_tool(
    user_id: str,
    horizon_days: int = 3,
    reason: str = "missed_tasks"
) -> Dict[str, Any]:
    """
    LangGraph tool for rescheduling missed or problematic tasks.
    
    Analyzes scheduling issues and generates updated schedules
    with appropriate urgency adjustments.
    
    Args:
        user_id: User identifier
        horizon_days: Days ahead to reschedule (1-14)
        reason: Reason for rescheduling ("missed_tasks", "conflicts", "preferences")
        
    Returns:
        Dictionary with rescheduling results
    """
    try:
        # Validate inputs
        if not 1 <= horizon_days <= 14:
            return {
                "success": False,
                "error": "horizon_days must be between 1 and 14 for rescheduling",
                "error_type": "validation_error"
            }
        
        # Execute rescheduling
        scheduler = get_scheduler_service()
        response = await scheduler.reschedule_missed_tasks(user_id, horizon_days)
        
        # Convert to tool output
        result = {
            "success": True,
            "feasible": response.feasible,
            "rescheduling_reason": reason,
            "schedule": {
                "blocks": [
                    {
                        "task_id": block.task_id,
                        "title": block.title,
                        "start": block.start,
                        "end": block.end,
                        "duration_minutes": block.duration_minutes
                    }
                    for block in response.blocks
                ],
                "total_blocks": len(response.blocks)
            },
            "changes": {
                "blocks_added": len(response.blocks),
                "reschedule_type": response.explanations.get("reschedule_type", "unknown")
            },
            "explanations": response.explanations
        }
        
        logger.info(
            f"Reschedule tool completed for user {user_id}: "
            f"reason={reason}, blocks={len(response.blocks)}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Reschedule tool failed for user {user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@monitor_performance("langgraph_schedule_analysis_tool")
async def schedule_analysis_tool(
    user_id: str,
    analysis_type: str = "overview"
) -> Dict[str, Any]:
    """
    LangGraph tool for analyzing schedule performance and quality.
    
    Provides insights into scheduling effectiveness, user satisfaction,
    and optimization opportunities.
    
    Args:
        user_id: User identifier
        analysis_type: Type of analysis ("overview", "performance", "quality")
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    try:
        # Get various metrics and statistics
        from .adapt.evaluator import get_quality_tracker
        from .adapt.updater import get_performance_monitor, get_feedback_processor
        from .adapt.rescheduler import get_reschedule_metrics
        
        quality_tracker = get_quality_tracker()
        performance_monitor = get_performance_monitor()
        feedback_processor = get_feedback_processor()
        reschedule_metrics = get_reschedule_metrics()
        
        # Gather analysis data
        analysis_data = {}
        
        if analysis_type in ["overview", "quality"]:
            quality_trends = quality_tracker.get_trends(user_id)
            analysis_data["quality"] = quality_trends
        
        if analysis_type in ["overview", "performance"]:
            performance_trends = performance_monitor.get_performance_trends(user_id)
            analysis_data["performance"] = performance_trends
        
        if analysis_type in ["overview"]:
            feedback_summary = feedback_processor.get_feedback_summary(user_id)
            reschedule_stats = reschedule_metrics.get_stats(user_id)
            analysis_data["feedback"] = feedback_summary
            analysis_data["rescheduling"] = reschedule_stats
        
        # Generate insights and recommendations
        insights = _generate_analysis_insights(analysis_data, analysis_type)
        recommendations = _generate_optimization_recommendations(analysis_data)
        
        result = {
            "success": True,
            "analysis_type": analysis_type,
            "data": analysis_data,
            "insights": insights,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Schedule analysis completed for user {user_id}: type={analysis_type}")
        
        return result
        
    except Exception as e:
        logger.error(f"Schedule analysis tool failed for user {user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@monitor_performance("langgraph_preference_update_tool")
async def preference_update_tool(
    user_id: str,
    preference_updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    LangGraph tool for updating user scheduling preferences.
    
    Updates preferences and optionally triggers rescheduling
    if changes significantly impact existing schedules.
    
    Args:
        user_id: User identifier
        preference_updates: Dictionary of preference updates
        
    Returns:
        Dictionary with update results and impact analysis
    """
    try:
        from .io.repository import get_repository
        
        repository = get_repository()
        
        # Update preferences
        await repository.update_preferences(user_id, preference_updates)
        
        # Analyze impact and determine if rescheduling is needed
        impact_analysis = _analyze_preference_impact(preference_updates)
        
        result = {
            "success": True,
            "updated_preferences": preference_updates,
            "impact_analysis": impact_analysis
        }
        
        # Trigger rescheduling if significant impact
        if impact_analysis.get("requires_rescheduling", False):
            scheduler = get_scheduler_service()
            reschedule_response = await scheduler.reschedule_missed_tasks(
                user_id, horizon_days=5
            )
            
            result["rescheduling"] = {
                "triggered": True,
                "feasible": reschedule_response.feasible,
                "blocks_affected": len(reschedule_response.blocks)
            }
        else:
            result["rescheduling"] = {"triggered": False}
        
        logger.info(f"Preference update completed for user {user_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Preference update tool failed for user {user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# Helper functions

def _generate_scheduling_insights(response: ScheduleResponse) -> Dict[str, Any]:
    """Generate insights from successful scheduling."""
    insights = {}
    
    # Time utilization
    total_minutes = response.total_scheduled_minutes
    if total_minutes > 0:
        insights["time_utilization"] = {
            "total_scheduled_minutes": total_minutes,
            "total_scheduled_hours": total_minutes / 60,
            "average_block_duration": total_minutes / max(1, len(response.blocks))
        }
    
    # Schedule distribution
    if response.blocks:
        # Group by date
        blocks_by_date = {}
        for block in response.blocks:
            date = datetime.fromisoformat(block.start.replace('Z', '+00:00')).date()
            blocks_by_date.setdefault(str(date), []).append(block)
        
        insights["distribution"] = {
            "days_with_tasks": len(blocks_by_date),
            "average_blocks_per_day": len(response.blocks) / max(1, len(blocks_by_date)),
            "date_breakdown": {
                date: len(blocks) for date, blocks in blocks_by_date.items()
            }
        }
    
    # Quality indicators
    solver_status = response.metrics.get("solver_status", "unknown")
    solve_time = response.metrics.get("solve_time_ms", 0)
    
    insights["quality"] = {
        "solver_status": solver_status,
        "solve_time_ms": solve_time,
        "optimization_quality": "high" if solver_status == "optimal" else "moderate"
    }
    
    return insights


def _analyze_scheduling_failure(response: ScheduleResponse) -> Dict[str, Any]:
    """Analyze why scheduling failed."""
    analysis = {
        "primary_cause": "unknown",
        "contributing_factors": [],
        "suggested_solutions": []
    }
    
    # Check diagnostics for clues
    diagnostics = response.metrics.get("diagnostics", {})
    
    if "infeasible_reason" in diagnostics:
        analysis["primary_cause"] = "constraints_too_strict"
        analysis["contributing_factors"].append(diagnostics["infeasible_reason"])
        analysis["suggested_solutions"].append("Relax deadlines or reduce task estimates")
    
    if response.metrics.get("solver_status") == "timeout":
        analysis["primary_cause"] = "complexity_too_high"
        analysis["suggested_solutions"].append("Reduce scheduling horizon or simplify constraints")
    
    unscheduled_count = response.metrics.get("unscheduled_tasks", 0)
    if unscheduled_count > 0:
        analysis["contributing_factors"].append(f"{unscheduled_count} tasks could not be scheduled")
        analysis["suggested_solutions"].append("Review task priorities and time estimates")
    
    if not analysis["suggested_solutions"]:
        analysis["suggested_solutions"].append("Contact support for detailed analysis")
    
    return analysis


def _generate_analysis_insights(data: Dict[str, Any], analysis_type: str) -> List[str]:
    """Generate insights from analysis data."""
    insights = []
    
    # Quality insights
    quality_data = data.get("quality", {})
    if not quality_data.get("insufficient_data", True):
        latest_score = quality_data.get("latest_score", 0)
        if latest_score > 0.8:
            insights.append("Schedule quality is excellent - user preferences well-aligned")
        elif latest_score > 0.6:
            insights.append("Schedule quality is good with room for improvement")
        else:
            insights.append("Schedule quality is below target - review constraints and preferences")
    
    # Performance insights
    performance_data = data.get("performance", {})
    if not performance_data.get("insufficient_data", True):
        trends = performance_data.get("trends", {})
        improving_metrics = [name for name, trend in trends.items() if trend.get("improving", False)]
        if improving_metrics:
            insights.append(f"Performance improving in: {', '.join(improving_metrics)}")
    
    # Feedback insights
    feedback_data = data.get("feedback", {})
    if not feedback_data.get("no_feedback", True):
        avg_satisfaction = feedback_data.get("avg_satisfaction", 0)
        if avg_satisfaction > 0.5:
            insights.append("User satisfaction is positive")
        elif avg_satisfaction < -0.3:
            insights.append("User satisfaction is low - schedule adjustments needed")
    
    return insights[:5]  # Limit to top 5 insights


def _generate_optimization_recommendations(data: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations from analysis data."""
    recommendations = []
    
    # Quality-based recommendations
    quality_data = data.get("quality", {})
    if quality_data.get("latest_score", 1.0) < 0.7:
        recommendations.append("Consider updating time preferences or relaxing constraints")
    
    # Performance-based recommendations
    performance_data = data.get("performance", {})
    trends = performance_data.get("trends", {})
    
    if "completion_rate" in trends and not trends["completion_rate"].get("improving", True):
        recommendations.append("Review task time estimates - they may be too optimistic")
    
    # Rescheduling-based recommendations
    reschedule_data = data.get("rescheduling", {})
    total_reschedules = reschedule_data.get("total_reschedules", 0)
    
    if total_reschedules > 5:
        success_rate = reschedule_data.get("success_rate", 1.0)
        if success_rate < 0.8:
            recommendations.append("High rescheduling frequency - consider more realistic scheduling")
    
    # Default recommendation
    if not recommendations:
        recommendations.append("Scheduler is performing well - continue current usage patterns")
    
    return recommendations[:3]  # Limit to top 3 recommendations


def _analyze_preference_impact(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze impact of preference updates."""
    impact = {
        "impact_level": "low",
        "requires_rescheduling": False,
        "affected_areas": []
    }
    
    # High impact changes
    high_impact_prefs = [
        "workday_start", "workday_end", "max_daily_effort_minutes",
        "session_granularity_minutes"
    ]
    
    # Medium impact changes
    medium_impact_prefs = [
        "deep_work_windows", "no_study_windows", "break_every_minutes"
    ]
    
    for pref_name in updates.keys():
        if pref_name in high_impact_prefs:
            impact["impact_level"] = "high"
            impact["requires_rescheduling"] = True
            impact["affected_areas"].append(pref_name)
        elif pref_name in medium_impact_prefs:
            if impact["impact_level"] == "low":
                impact["impact_level"] = "medium"
            impact["affected_areas"].append(pref_name)
    
    return impact


# Tool registration for LangGraph
SCHEDULER_TOOLS = {
    "scheduling_tool": {
        "name": "scheduling_tool",
        "description": "Generate optimized task schedules using AI-powered constraint satisfaction",
        "function": scheduling_tool,
        "parameters": {
            "user_id": "string",
            "horizon_days": "integer (1-30)",
            "dry_run": "boolean",
            "lock_existing": "boolean", 
            "options": "object"
        }
    },
    "reschedule_tool": {
        "name": "reschedule_tool", 
        "description": "Reschedule missed or problematic tasks with urgency adjustments",
        "function": reschedule_tool,
        "parameters": {
            "user_id": "string",
            "horizon_days": "integer (1-14)",
            "reason": "string"
        }
    },
    "schedule_analysis_tool": {
        "name": "schedule_analysis_tool",
        "description": "Analyze schedule performance and provide optimization insights",
        "function": schedule_analysis_tool,
        "parameters": {
            "user_id": "string", 
            "analysis_type": "string (overview|performance|quality)"
        }
    },
    "preference_update_tool": {
        "name": "preference_update_tool",
        "description": "Update user scheduling preferences with impact analysis",
        "function": preference_update_tool,
        "parameters": {
            "user_id": "string",
            "preference_updates": "object"
        }
    }
}