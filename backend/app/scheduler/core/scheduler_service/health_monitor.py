"""
Health monitoring and status reporting for the scheduler service.

Tracks component availability, ML model status, safety system health,
and overall scheduler readiness.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors health and status of scheduler components."""

    def __init__(
        self,
        solver_available: bool,
        enable_safety_rails: bool = True
    ):
        """
        Initialize health monitor.

        Args:
            solver_available: Whether constraint solver is available
            enable_safety_rails: Whether safety rails are enabled
        """
        self.solver_available = solver_available
        self.enable_safety_rails = enable_safety_rails
        self._last_check_time = None
        self._cached_status = None

    def get_health_status(
        self,
        model,
        tuner,
        safety_manager=None,
        slo_gate=None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive health status of scheduler components.

        Args:
            model: Completion model instance
            tuner: Weight tuning bandit instance
            safety_manager: Optional safety manager instance
            slo_gate: Optional SLO gate instance
            force_refresh: Force refresh of cached status

        Returns:
            Dictionary with health status information
        """
        # Return cached status if recent (within 30 seconds)
        if not force_refresh and self._is_cache_valid():
            logger.debug("Returning cached health status")
            return self._cached_status

        # Build fresh status
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'solver_available': self.solver_available,
            'model_fitted': model.is_fitted if hasattr(model, 'is_fitted') else False,
            'bandit_arms': len(tuner.arms) if hasattr(tuner, 'arms') and tuner.arms else 0,
            'repository_connected': True,  # Would check actual connection in production
            'version': '1.0.0',
            'safety_rails_enabled': self.enable_safety_rails
        }

        # Add SLO status if available
        if slo_gate:
            try:
                slo_status = slo_gate.get_health_status()
                status['slo'] = slo_status
            except Exception as e:
                logger.warning(f"Failed to get SLO status: {e}")
                status['slo'] = {'error': str(e)}

        # Add safety status if enabled
        if self.enable_safety_rails and safety_manager:
            try:
                safety_status = safety_manager.check_global_safety()
                status['safety'] = safety_status
            except Exception as e:
                logger.warning(f"Failed to get safety status: {e}")
                status['safety'] = {'error': str(e)}

        # Overall health determination
        status['healthy'] = self._determine_overall_health(status)

        # Cache the result
        self._cached_status = status
        self._last_check_time = datetime.utcnow()

        logger.info(f"Health check: healthy={status['healthy']}")

        return status

    def get_component_status(
        self,
        component_name: str,
        component_instance: Any
    ) -> Dict[str, Any]:
        """
        Get status for a specific component.

        Args:
            component_name: Name of the component
            component_instance: Instance of the component

        Returns:
            Component-specific status dictionary
        """
        status = {
            'name': component_name,
            'available': component_instance is not None,
            'timestamp': datetime.utcnow().isoformat()
        }

        if component_instance is None:
            status['status'] = 'unavailable'
            return status

        # Component-specific checks
        if component_name == 'model':
            status['fitted'] = getattr(component_instance, 'is_fitted', False)
            status['status'] = 'ready' if status['fitted'] else 'untrained'

        elif component_name == 'bandit':
            arms = getattr(component_instance, 'arms', None)
            status['arm_count'] = len(arms) if arms else 0
            status['status'] = 'ready' if status['arm_count'] > 0 else 'initializing'

        elif component_name == 'solver':
            status['status'] = 'ready' if self.solver_available else 'unavailable'

        else:
            status['status'] = 'unknown'

        return status

    def check_ml_readiness(
        self,
        model,
        tuner
    ) -> Dict[str, Any]:
        """
        Check if ML components are ready for use.

        Args:
            model: Completion model instance
            tuner: Weight tuning bandit instance

        Returns:
            ML readiness status
        """
        model_ready = getattr(model, 'is_fitted', False)
        bandit_ready = (
            hasattr(tuner, 'arms') and
            tuner.arms is not None and
            len(tuner.arms) > 0
        )

        ml_ready = model_ready and bandit_ready

        status = {
            'ml_ready': ml_ready,
            'model_ready': model_ready,
            'bandit_ready': bandit_ready,
            'timestamp': datetime.utcnow().isoformat()
        }

        if not ml_ready:
            reasons = []
            if not model_ready:
                reasons.append("completion model not fitted")
            if not bandit_ready:
                reasons.append("bandit not initialized")
            status['not_ready_reason'] = "; ".join(reasons)

        return status

    def check_solver_availability(self) -> Dict[str, Any]:
        """
        Check solver availability and capabilities.

        Returns:
            Solver availability status
        """
        return {
            'available': self.solver_available,
            'fallback_available': True,  # Greedy fallback always available
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'ready' if self.solver_available else 'fallback_only'
        }

    def get_performance_metrics(
        self,
        recent_runs: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for recent scheduler runs.

        Args:
            recent_runs: Optional list of recent run results

        Returns:
            Performance metrics dictionary
        """
        if not recent_runs:
            return {
                'runs_analyzed': 0,
                'message': 'No recent runs available'
            }

        # Calculate aggregate metrics
        total_runs = len(recent_runs)
        successful_runs = sum(1 for r in recent_runs if r.get('feasible', False))
        avg_solve_time = sum(r.get('solve_time_ms', 0) for r in recent_runs) / total_runs

        metrics = {
            'runs_analyzed': total_runs,
            'success_rate': successful_runs / total_runs if total_runs > 0 else 0,
            'avg_solve_time_ms': avg_solve_time,
            'timestamp': datetime.utcnow().isoformat()
        }

        return metrics

    def _determine_overall_health(self, status: Dict[str, Any]) -> bool:
        """
        Determine overall system health from component statuses.

        Args:
            status: Component status dictionary

        Returns:
            True if system is healthy, False otherwise
        """
        # Critical: Repository must be connected
        if not status.get('repository_connected', False):
            return False

        # Important: Either solver or fallback should work
        # (fallback always available, so this is always true)

        # Safety checks if enabled
        if self.enable_safety_rails and 'safety' in status:
            safety_status = status['safety']
            if isinstance(safety_status, dict):
                if safety_status.get('status') == 'critical_failure':
                    return False

        # SLO checks if available
        if 'slo' in status:
            slo_status = status['slo']
            if isinstance(slo_status, dict):
                if slo_status.get('status') == 'overloaded':
                    logger.warning("SLO system overloaded")
                    # Don't fail health check, but log warning

        # System is healthy
        return True

    def _is_cache_valid(self, max_age_seconds: int = 30) -> bool:
        """
        Check if cached health status is still valid.

        Args:
            max_age_seconds: Maximum age for cache validity

        Returns:
            True if cache is valid, False otherwise
        """
        if self._last_check_time is None or self._cached_status is None:
            return False

        age = (datetime.utcnow() - self._last_check_time).total_seconds()
        return age < max_age_seconds

    def invalidate_cache(self):
        """Invalidate cached health status."""
        self._cached_status = None
        self._last_check_time = None
        logger.debug("Health status cache invalidated")


def get_health_monitor(
    solver_available: bool,
    enable_safety_rails: bool = True
) -> HealthMonitor:
    """
    Get a health monitor instance.

    Args:
        solver_available: Whether constraint solver is available
        enable_safety_rails: Whether safety rails are enabled

    Returns:
        Health monitor instance
    """
    return HealthMonitor(solver_available, enable_safety_rails)
