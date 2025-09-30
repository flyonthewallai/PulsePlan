"""
Integration module for ML safety rails across the scheduler system.

Provides centralized safety management, monitoring, and coordination
between different ML components with unified safety policies.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from .safety_rails import SafetyMonitor, SafetyConfig, SafeGuardedBandit
from .safe_models import SafeCompletionModel, ModelEnsemble
from .bandits import WeightTuner
from .completion_model import CompletionModel
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """System-wide safety levels."""
    MINIMAL = "minimal"       # Basic bounds checking only
    STANDARD = "standard"     # Standard safety monitoring
    STRICT = "strict"         # Strict safety with aggressive fallbacks
    PARANOID = "paranoid"     # Maximum safety, minimal ML usage


@dataclass
class SystemSafetyConfig:
    """System-wide safety configuration."""

    # Global safety level
    safety_level: SafetyLevel = SafetyLevel.STANDARD

    # Component-specific configs
    bandit_safety_config: Optional[SafetyConfig] = None
    model_safety_config: Optional[SafetyConfig] = None

    # Global intervention thresholds
    global_warning_threshold: float = 0.4
    global_intervention_threshold: float = 0.7
    global_emergency_threshold: float = 0.9

    # Coordination settings
    cross_component_monitoring: bool = True
    unified_fallback_mode: bool = True
    safety_reporting_enabled: bool = True

    # Performance limits
    max_total_ml_time_ms: float = 10000  # 10 seconds total ML time
    max_concurrent_ml_operations: int = 3

    # Recovery settings
    auto_recovery_enabled: bool = True
    recovery_cooldown_minutes: int = 15
    max_recovery_attempts: int = 3


class SystemSafetyManager:
    """Centralized safety management for all ML components."""

    def __init__(self, config: SystemSafetyConfig = None):
        self.config = config or SystemSafetyConfig()
        self.timezone_manager = get_timezone_manager()

        # Component safety monitors
        self.component_monitors: Dict[str, SafetyMonitor] = {}
        self.component_health: Dict[str, Dict[str, Any]] = {}

        # Global state tracking
        self.global_safety_mode = False
        self.active_ml_operations = 0
        self.total_ml_time_ms = 0.0
        self.last_global_intervention = None
        self.recovery_attempts = 0

        # Event tracking
        self.safety_events = []
        self.performance_metrics = {}

        # Initialize component-specific configs
        self._initialize_component_configs()

    def _initialize_component_configs(self):
        """Initialize safety configs for different components."""

        base_config = SafetyConfig()

        # Adjust configs based on safety level
        if self.config.safety_level == SafetyLevel.MINIMAL:
            base_config.intervention_threshold = 0.9
            base_config.emergency_threshold = 0.95

        elif self.config.safety_level == SafetyLevel.STRICT:
            base_config.intervention_threshold = 0.5
            base_config.emergency_threshold = 0.7
            base_config.max_weight = 5.0  # More conservative

        elif self.config.safety_level == SafetyLevel.PARANOID:
            base_config.intervention_threshold = 0.3
            base_config.emergency_threshold = 0.5
            base_config.max_weight = 3.0
            base_config.reward_degradation_window = 5

        self.config.bandit_safety_config = self.config.bandit_safety_config or base_config
        self.config.model_safety_config = self.config.model_safety_config or base_config

    def register_component(self, component_name: str, component_type: str) -> SafetyMonitor:
        """Register a component for safety monitoring."""

        if component_type == "bandit":
            config = self.config.bandit_safety_config
        elif component_type == "model":
            config = self.config.model_safety_config
        else:
            config = SafetyConfig()

        monitor = SafetyMonitor(config)
        self.component_monitors[component_name] = monitor
        self.component_health[component_name] = {"status": "healthy", "last_check": datetime.now()}

        logger.info(f"Registered {component_type} component '{component_name}' for safety monitoring")
        return monitor

    async def check_global_safety(self) -> Dict[str, Any]:
        """Check system-wide safety status."""

        # Collect status from all components
        component_statuses = {}
        global_violations = []
        max_severity = 0.0

        for name, monitor in self.component_monitors.items():
            status = monitor.get_safety_status()
            component_statuses[name] = status

            # Check for violations
            recent_violations = [
                v for v in monitor.violations
                if (self.timezone_manager.get_user_now() - v.detected_at).total_seconds() < 300  # 5 min
            ]

            if recent_violations:
                max_component_severity = max(v.severity for v in recent_violations)
                max_severity = max(max_severity, max_component_severity)
                global_violations.extend(recent_violations)

        # Check global constraints
        global_constraint_violations = self._check_global_constraints()
        global_violations.extend(global_constraint_violations)

        if global_constraint_violations:
            max_severity = max(max_severity, max(v.severity for v in global_constraint_violations))

        # Determine global safety status
        global_status = "healthy"
        if max_severity >= self.config.global_emergency_threshold:
            global_status = "emergency"
        elif max_severity >= self.config.global_intervention_threshold:
            global_status = "intervention_needed"
        elif max_severity >= self.config.global_warning_threshold:
            global_status = "warning"

        # Take action if needed
        if global_status in ["intervention_needed", "emergency"] and not self.global_safety_mode:
            await self._activate_global_safety_mode(global_violations)
        elif global_status == "healthy" and self.global_safety_mode:
            await self._deactivate_global_safety_mode()

        return {
            "global_status": global_status,
            "global_safety_mode": self.global_safety_mode,
            "max_severity": max_severity,
            "component_statuses": component_statuses,
            "recent_violations": len(global_violations),
            "total_ml_time_ms": self.total_ml_time_ms,
            "active_ml_operations": self.active_ml_operations,
            "recovery_attempts": self.recovery_attempts,
            "last_intervention": self.last_global_intervention.isoformat() if self.last_global_intervention else None
        }

    def should_use_ml(self, component_name: str, operation_type: str = "prediction") -> bool:
        """Determine if ML should be used for a specific operation."""

        # Global safety mode overrides everything
        if self.global_safety_mode:
            return False

        # Check safety level
        if self.config.safety_level == SafetyLevel.PARANOID:
            return False  # No ML in paranoid mode

        # Check component-specific safety
        if component_name in self.component_monitors:
            monitor = self.component_monitors[component_name]
            if monitor.should_use_fallback():
                return False

        # Check resource limits
        if self.active_ml_operations >= self.config.max_concurrent_ml_operations:
            return False

        if self.total_ml_time_ms >= self.config.max_total_ml_time_ms:
            return False

        return True

    async def start_ml_operation(self, component_name: str, operation_type: str) -> Optional[str]:
        """Start tracking an ML operation."""

        if not self.should_use_ml(component_name, operation_type):
            return None

        operation_id = f"{component_name}_{operation_type}_{datetime.now().timestamp()}"
        self.active_ml_operations += 1

        logger.debug(f"Started ML operation: {operation_id}")
        return operation_id

    async def finish_ml_operation(
        self,
        operation_id: str,
        duration_ms: float,
        success: bool = True,
        violations: List[Any] = None
    ):
        """Finish tracking an ML operation."""

        self.active_ml_operations = max(0, self.active_ml_operations - 1)
        self.total_ml_time_ms += duration_ms

        # Record performance
        component_name = operation_id.split('_')[0]
        if component_name not in self.performance_metrics:
            self.performance_metrics[component_name] = {
                "total_operations": 0,
                "total_time_ms": 0.0,
                "success_rate": 1.0,
                "avg_duration_ms": 0.0
            }

        metrics = self.performance_metrics[component_name]
        metrics["total_operations"] += 1
        metrics["total_time_ms"] += duration_ms
        metrics["avg_duration_ms"] = metrics["total_time_ms"] / metrics["total_operations"]

        if success:
            metrics["success_rate"] = (
                (metrics["success_rate"] * (metrics["total_operations"] - 1) + 1.0) /
                metrics["total_operations"]
            )
        else:
            metrics["success_rate"] = (
                (metrics["success_rate"] * (metrics["total_operations"] - 1)) /
                metrics["total_operations"]
            )

        logger.debug(f"Finished ML operation: {operation_id} ({duration_ms:.1f}ms, success={success})")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""

        return {
            "system_config": {
                "safety_level": self.config.safety_level.value,
                "global_safety_mode": self.global_safety_mode,
                "auto_recovery_enabled": self.config.auto_recovery_enabled
            },
            "resource_usage": {
                "total_ml_time_ms": self.total_ml_time_ms,
                "active_operations": self.active_ml_operations,
                "max_concurrent_allowed": self.config.max_concurrent_ml_operations
            },
            "component_performance": self.performance_metrics,
            "component_health": {
                name: health for name, health in self.component_health.items()
            },
            "recent_events": len(self.safety_events),
            "recovery_status": {
                "attempts": self.recovery_attempts,
                "max_attempts": self.config.max_recovery_attempts,
                "last_intervention": self.last_global_intervention.isoformat() if self.last_global_intervention else None
            }
        }

    async def _activate_global_safety_mode(self, violations: List[Any]):
        """Activate global safety mode."""

        self.global_safety_mode = True
        self.last_global_intervention = self.timezone_manager.get_user_now()
        self.recovery_attempts += 1

        logger.warning(f"Global safety mode activated (attempt {self.recovery_attempts})")

        # Record safety event
        self.safety_events.append({
            "timestamp": self.last_global_intervention,
            "event_type": "global_safety_activation",
            "violations": len(violations),
            "max_severity": max(v.severity for v in violations) if violations else 0.0
        })

        # Notify all component monitors
        for monitor in self.component_monitors.values():
            monitor.activate_safety_mode("Global safety intervention")

    async def _deactivate_global_safety_mode(self):
        """Deactivate global safety mode if conditions are good."""

        if not self.global_safety_mode:
            return

        # Check cooldown
        if self.last_global_intervention:
            time_since_intervention = (
                self.timezone_manager.get_user_now() - self.last_global_intervention
            ).total_seconds() / 60  # minutes

            if time_since_intervention < self.config.recovery_cooldown_minutes:
                return

        # Check if all components are healthy
        all_healthy = all(
            not monitor.safety_mode_active
            for monitor in self.component_monitors.values()
        )

        if all_healthy:
            self.global_safety_mode = False
            logger.info("Global safety mode deactivated - system recovered")

            # Record recovery event
            self.safety_events.append({
                "timestamp": self.timezone_manager.get_user_now(),
                "event_type": "global_safety_recovery",
                "recovery_time_minutes": time_since_intervention if self.last_global_intervention else 0
            })

    def _check_global_constraints(self) -> List[Any]:
        """Check system-wide constraints and resource limits."""

        violations = []

        # Check total ML time usage
        if self.total_ml_time_ms > self.config.max_total_ml_time_ms:
            from .safety_rails import SafetyViolation, SafetyViolationType
            violation = SafetyViolation(
                violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                severity=min(1.0, self.total_ml_time_ms / (self.config.max_total_ml_time_ms * 2)),
                description=f"Total ML time {self.total_ml_time_ms:.0f}ms exceeds limit {self.config.max_total_ml_time_ms:.0f}ms",
                detected_at=self.timezone_manager.get_user_now(),
                context={"total_time": self.total_ml_time_ms, "limit": self.config.max_total_ml_time_ms},
                suggested_action="Reset ML time usage or increase limits"
            )
            violations.append(violation)

        # Check concurrent operations
        if self.active_ml_operations > self.config.max_concurrent_ml_operations:
            from .safety_rails import SafetyViolation, SafetyViolationType
            violation = SafetyViolation(
                violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                severity=0.8,
                description=f"Active ML operations {self.active_ml_operations} exceeds limit {self.config.max_concurrent_ml_operations}",
                detected_at=self.timezone_manager.get_user_now(),
                context={"active_ops": self.active_ml_operations, "limit": self.config.max_concurrent_ml_operations},
                suggested_action="Wait for operations to complete or increase limits"
            )
            violations.append(violation)

        # Check recovery attempts
        if self.recovery_attempts >= self.config.max_recovery_attempts:
            from .safety_rails import SafetyViolation, SafetyViolationType
            violation = SafetyViolation(
                violation_type=SafetyViolationType.PERFORMANCE_REGRESSION,
                severity=1.0,
                description=f"Maximum recovery attempts {self.config.max_recovery_attempts} reached",
                detected_at=self.timezone_manager.get_user_now(),
                context={"attempts": self.recovery_attempts, "max_attempts": self.config.max_recovery_attempts},
                suggested_action="Manual intervention required - disable ML or investigate root cause"
            )
            violations.append(violation)

        return violations

    def reset_resource_usage(self):
        """Reset resource usage counters (typically called daily)."""

        self.total_ml_time_ms = 0.0
        self.recovery_attempts = 0

        # Clear old events (keep last 24 hours)
        cutoff_time = self.timezone_manager.get_user_now() - timedelta(hours=24)
        self.safety_events = [
            event for event in self.safety_events
            if event["timestamp"] > cutoff_time
        ]

        logger.info("Reset ML resource usage counters")


# Global safety manager instance
_global_safety_manager = None


def get_safety_manager() -> SystemSafetyManager:
    """Get global safety manager instance."""
    global _global_safety_manager
    if _global_safety_manager is None:
        _global_safety_manager = SystemSafetyManager()
    return _global_safety_manager


def create_safe_bandit(safety_level: SafetyLevel = SafetyLevel.STANDARD, **kwargs) -> SafeGuardedBandit:
    """Create a bandit with appropriate safety level."""

    safety_manager = get_safety_manager()
    safety_monitor = safety_manager.register_component("bandit", "bandit")

    return SafeGuardedBandit(safety_monitor=safety_monitor, **kwargs)


def create_safe_model(safety_level: SafetyLevel = SafetyLevel.STANDARD, **kwargs) -> SafeCompletionModel:
    """Create a completion model with appropriate safety level."""

    safety_manager = get_safety_manager()
    safety_monitor = safety_manager.register_component("completion_model", "model")

    return SafeCompletionModel(safety_monitor=safety_monitor, **kwargs)

