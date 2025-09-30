"""
Safety rails and protection mechanisms for ML components.

Provides safeguards against model degradation, adversarial inputs,
and ensures reliable fallback when ML models fail or perform poorly.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import deque, defaultdict

from .bandits import BanditArm, WeightTuner
from .completion_model import CompletionModel
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class SafetyViolationType(Enum):
    """Types of safety violations that can occur."""
    REWARD_DEGRADATION = "reward_degradation"        # Consistently poor rewards
    EXTREME_WEIGHTS = "extreme_weights"              # Weights outside safe bounds
    OSCILLATING_BEHAVIOR = "oscillating_behavior"   # Unstable weight selection
    MODEL_DIVERGENCE = "model_divergence"           # ML model performing poorly
    RESOURCE_EXHAUSTION = "resource_exhaustion"     # Too much computation
    INPUT_ANOMALY = "input_anomaly"                 # Unusual input patterns
    PERFORMANCE_REGRESSION = "performance_regression" # Worse than baseline


@dataclass
class SafetyViolation:
    """Represents a detected safety violation."""
    violation_type: SafetyViolationType
    severity: float  # 0.0 to 1.0
    description: str
    detected_at: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    # Mitigation info
    suggested_action: str = ""
    auto_mitigated: bool = False


@dataclass
class SafetyConfig:
    """Configuration for safety mechanisms."""

    # Weight bounds
    min_weight: float = 0.1
    max_weight: float = 10.0
    weight_change_limit: float = 2.0  # Max multiplier change per update

    # Performance thresholds
    min_reward_threshold: float = -2.0
    reward_degradation_window: int = 10  # Recent rewards to check
    performance_baseline_percentile: float = 0.2  # Bottom 20% triggers concern

    # Oscillation detection
    oscillation_window: int = 5
    oscillation_threshold: float = 0.5  # Variance threshold

    # Model validation
    model_confidence_threshold: float = 0.3
    prediction_variance_limit: float = 0.8

    # Resource limits
    max_computation_time_seconds: float = 5.0
    max_memory_mb: float = 512.0

    # Input validation
    context_value_bounds: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        'horizon_days': (1.0, 30.0),
        'max_daily_effort': (60.0, 960.0),  # 1-16 hours
        'granularity': (5.0, 120.0),  # 5 min to 2 hours
        'dow': (0.0, 6.0),  # Day of week
        'hour': (0.0, 23.0)
    })

    # Intervention thresholds
    warning_threshold: float = 0.3
    intervention_threshold: float = 0.7
    emergency_threshold: float = 0.9


class SafetyMonitor:
    """Monitors ML components for safety violations and performance issues."""

    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()
        self.timezone_manager = get_timezone_manager()

        # Violation tracking
        self.violations: List[SafetyViolation] = []
        self.recent_rewards = deque(maxlen=self.config.reward_degradation_window)
        self.weight_history = deque(maxlen=self.config.oscillation_window)

        # Performance baselines
        self.reward_baseline: Optional[float] = None
        self.historical_rewards = deque(maxlen=100)

        # Model performance tracking
        self.model_predictions = deque(maxlen=50)
        self.prediction_errors = deque(maxlen=50)

        # Resource monitoring
        self.computation_times = deque(maxlen=20)
        self.memory_usage = deque(maxlen=20)

        # Safety state
        self.safety_mode_active = False
        self.last_intervention = None

    def check_bandit_safety(
        self,
        bandit: WeightTuner,
        selected_weights: Dict[str, float],
        reward: Optional[float] = None,
        context: Dict[str, Any] = None
    ) -> List[SafetyViolation]:
        """Check bandit algorithm for safety violations."""
        violations = []

        # Check weight bounds
        weight_violations = self._check_weight_bounds(selected_weights)
        violations.extend(weight_violations)

        # Check reward degradation
        if reward is not None:
            self.recent_rewards.append(reward)
            reward_violations = self._check_reward_degradation()
            violations.extend(reward_violations)

        # Check for oscillating behavior
        self.weight_history.append(selected_weights.copy())
        oscillation_violations = self._check_weight_oscillation()
        violations.extend(oscillation_violations)

        # Check context anomalies
        if context:
            context_violations = self._check_context_anomalies(context)
            violations.extend(context_violations)

        # Record violations
        self.violations.extend(violations)

        return violations

    def check_model_safety(
        self,
        model: CompletionModel,
        predictions: np.ndarray,
        actual_outcomes: Optional[np.ndarray] = None,
        computation_time: Optional[float] = None
    ) -> List[SafetyViolation]:
        """Check ML model for safety violations."""
        violations = []

        # Check prediction confidence
        confidence_violations = self._check_prediction_confidence(predictions)
        violations.extend(confidence_violations)

        # Check for model divergence
        if actual_outcomes is not None:
            divergence_violations = self._check_model_divergence(predictions, actual_outcomes)
            violations.extend(divergence_violations)

        # Check computation resources
        if computation_time is not None:
            self.computation_times.append(computation_time)
            resource_violations = self._check_resource_usage(computation_time)
            violations.extend(resource_violations)

        # Record violations
        self.violations.extend(violations)

        return violations

    def get_safe_weights(
        self,
        proposed_weights: Dict[str, float],
        fallback_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Return safe version of proposed weights."""

        # Use fallback if safety mode is active
        if self.safety_mode_active and fallback_weights:
            logger.warning("Safety mode active, using fallback weights")
            return fallback_weights.copy()

        safe_weights = {}

        for name, weight in proposed_weights.items():
            # Clamp to safe bounds
            safe_weight = max(
                self.config.min_weight,
                min(self.config.max_weight, weight)
            )

            # Check for excessive changes from previous
            if self.weight_history:
                previous_weights = self.weight_history[-1]
                if name in previous_weights:
                    prev_weight = previous_weights[name]
                    max_change = prev_weight * self.config.weight_change_limit
                    min_change = prev_weight / self.config.weight_change_limit

                    safe_weight = max(min_change, min(max_change, safe_weight))

            safe_weights[name] = safe_weight

        return safe_weights

    def should_use_fallback(self) -> bool:
        """Determine if fallback mechanisms should be used."""

        # Check recent violation severity
        recent_violations = [
            v for v in self.violations
            if (self.timezone_manager.get_user_now() - v.detected_at).total_seconds() < 300  # 5 minutes
        ]

        if not recent_violations:
            return False

        # Calculate maximum recent severity
        max_severity = max(v.severity for v in recent_violations)

        return max_severity >= self.config.intervention_threshold

    def activate_safety_mode(self, reason: str):
        """Activate safety mode with fallback behaviors."""
        self.safety_mode_active = True
        self.last_intervention = self.timezone_manager.get_user_now()

        logger.warning(f"Safety mode activated: {reason}")

        # Create intervention violation
        violation = SafetyViolation(
            violation_type=SafetyViolationType.PERFORMANCE_REGRESSION,
            severity=1.0,
            description=f"Safety mode activated: {reason}",
            detected_at=self.last_intervention,
            suggested_action="Using conservative fallback weights",
            auto_mitigated=True
        )
        self.violations.append(violation)

    def deactivate_safety_mode(self):
        """Deactivate safety mode if conditions are good."""
        if not self.safety_mode_active:
            return

        # Check if it's safe to deactivate
        recent_good_performance = (
            len(self.recent_rewards) >= 3 and
            all(r > self.config.min_reward_threshold for r in list(self.recent_rewards)[-3:])
        )

        if recent_good_performance:
            self.safety_mode_active = False
            logger.info("Safety mode deactivated - performance recovered")

    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status and metrics."""

        # Recent violation summary
        recent_violations = [
            v for v in self.violations
            if (self.timezone_manager.get_user_now() - v.detected_at).total_seconds() < 3600  # 1 hour
        ]

        violation_counts = defaultdict(int)
        for violation in recent_violations:
            violation_counts[violation.violation_type.value] += 1

        # Performance metrics
        recent_reward_mean = np.mean(self.recent_rewards) if self.recent_rewards else 0.0
        recent_reward_std = np.std(self.recent_rewards) if len(self.recent_rewards) > 1 else 0.0

        return {
            "safety_mode_active": self.safety_mode_active,
            "last_intervention": self.last_intervention.isoformat() if self.last_intervention else None,
            "recent_violations": dict(violation_counts),
            "total_violations": len(self.violations),
            "recent_reward_mean": recent_reward_mean,
            "recent_reward_std": recent_reward_std,
            "baseline_reward": self.reward_baseline,
            "should_use_fallback": self.should_use_fallback(),
            "avg_computation_time": np.mean(self.computation_times) if self.computation_times else 0.0
        }

    def _check_weight_bounds(self, weights: Dict[str, float]) -> List[SafetyViolation]:
        """Check if weights are within safe bounds."""
        violations = []

        for name, weight in weights.items():
            if weight < self.config.min_weight or weight > self.config.max_weight:
                severity = min(1.0, abs(weight - 1.0) / 5.0)  # Scale severity

                violation = SafetyViolation(
                    violation_type=SafetyViolationType.EXTREME_WEIGHTS,
                    severity=severity,
                    description=f"Weight '{name}' = {weight:.2f} outside safe bounds [{self.config.min_weight}, {self.config.max_weight}]",
                    detected_at=self.timezone_manager.get_user_now(),
                    context={"weight_name": name, "weight_value": weight},
                    suggested_action="Clamp weight to safe bounds"
                )
                violations.append(violation)

        return violations

    def _check_reward_degradation(self) -> List[SafetyViolation]:
        """Check for consistent reward degradation."""
        violations = []

        if len(self.recent_rewards) < self.config.reward_degradation_window:
            return violations

        recent_mean = np.mean(self.recent_rewards)

        # Check against minimum threshold
        if recent_mean < self.config.min_reward_threshold:
            severity = min(1.0, abs(recent_mean / self.config.min_reward_threshold))

            violation = SafetyViolation(
                violation_type=SafetyViolationType.REWARD_DEGRADATION,
                severity=severity,
                description=f"Recent reward mean {recent_mean:.3f} below threshold {self.config.min_reward_threshold}",
                detected_at=self.timezone_manager.get_user_now(),
                context={"recent_mean": recent_mean, "threshold": self.config.min_reward_threshold},
                suggested_action="Review weight configuration or use fallback"
            )
            violations.append(violation)

        # Check against baseline if available
        if self.reward_baseline is not None:
            baseline_diff = self.reward_baseline - recent_mean
            if baseline_diff > 0.5:  # Significant degradation
                severity = min(1.0, baseline_diff / 2.0)

                violation = SafetyViolation(
                    violation_type=SafetyViolationType.PERFORMANCE_REGRESSION,
                    severity=severity,
                    description=f"Performance degraded by {baseline_diff:.3f} from baseline",
                    detected_at=self.timezone_manager.get_user_now(),
                    context={"baseline": self.reward_baseline, "current": recent_mean},
                    suggested_action="Consider reverting to previous configuration"
                )
                violations.append(violation)

        # Update baseline if performance is good
        elif recent_mean > 0.5:
            self.reward_baseline = recent_mean

        return violations

    def _check_weight_oscillation(self) -> List[SafetyViolation]:
        """Check for oscillating weight behavior."""
        violations = []

        if len(self.weight_history) < self.config.oscillation_window:
            return violations

        # Calculate variance across recent weight selections
        for weight_name in self.weight_history[0].keys():
            recent_values = [
                weights.get(weight_name, 0.0)
                for weights in self.weight_history
            ]

            if len(set(recent_values)) > 1:  # Only if there's variation
                variance = np.var(recent_values)

                if variance > self.config.oscillation_threshold:
                    severity = min(1.0, variance / (self.config.oscillation_threshold * 2))

                    violation = SafetyViolation(
                        violation_type=SafetyViolationType.OSCILLATING_BEHAVIOR,
                        severity=severity,
                        description=f"Weight '{weight_name}' oscillating with variance {variance:.3f}",
                        detected_at=self.timezone_manager.get_user_now(),
                        context={"weight_name": weight_name, "variance": variance, "recent_values": recent_values},
                        suggested_action="Increase exploration decay rate or use more conservative updates"
                    )
                    violations.append(violation)

        return violations

    def _check_context_anomalies(self, context: Dict[str, Any]) -> List[SafetyViolation]:
        """Check for anomalous context values."""
        violations = []

        for key, value in context.items():
            if key in self.config.context_value_bounds:
                min_val, max_val = self.config.context_value_bounds[key]

                if not isinstance(value, (int, float)):
                    continue

                if value < min_val or value > max_val:
                    severity = min(1.0, max(
                        abs(value - min_val) / abs(max_val - min_val),
                        abs(value - max_val) / abs(max_val - min_val)
                    ))

                    violation = SafetyViolation(
                        violation_type=SafetyViolationType.INPUT_ANOMALY,
                        severity=severity,
                        description=f"Context '{key}' = {value} outside expected range [{min_val}, {max_val}]",
                        detected_at=self.timezone_manager.get_user_now(),
                        context={"context_key": key, "value": value, "bounds": (min_val, max_val)},
                        suggested_action="Validate input data or expand expected ranges"
                    )
                    violations.append(violation)

        return violations

    def _check_prediction_confidence(self, predictions: np.ndarray) -> List[SafetyViolation]:
        """Check ML model prediction confidence."""
        violations = []

        # Assume predictions are probabilities between 0 and 1
        if len(predictions) == 0:
            return violations

        # Check for extreme predictions (too confident or too uncertain)
        extreme_predictions = np.sum((predictions < 0.1) | (predictions > 0.9))
        extreme_ratio = extreme_predictions / len(predictions)

        if extreme_ratio > 0.8:  # Too many extreme predictions
            severity = min(1.0, extreme_ratio)

            violation = SafetyViolation(
                violation_type=SafetyViolationType.MODEL_DIVERGENCE,
                severity=severity,
                description=f"{extreme_ratio:.1%} of predictions are extreme (< 0.1 or > 0.9)",
                detected_at=self.timezone_manager.get_user_now(),
                context={"extreme_ratio": extreme_ratio, "total_predictions": len(predictions)},
                suggested_action="Retrain model or use regularization"
            )
            violations.append(violation)

        # Check prediction variance
        prediction_variance = np.var(predictions)
        if prediction_variance > self.config.prediction_variance_limit:
            severity = min(1.0, prediction_variance / (self.config.prediction_variance_limit * 2))

            violation = SafetyViolation(
                violation_type=SafetyViolationType.MODEL_DIVERGENCE,
                severity=severity,
                description=f"Prediction variance {prediction_variance:.3f} too high",
                detected_at=self.timezone_manager.get_user_now(),
                context={"variance": prediction_variance, "limit": self.config.prediction_variance_limit},
                suggested_action="Check model stability or increase training data"
            )
            violations.append(violation)

        return violations

    def _check_model_divergence(self, predictions: np.ndarray, actuals: np.ndarray) -> List[SafetyViolation]:
        """Check for model performance divergence."""
        violations = []

        if len(predictions) != len(actuals) or len(predictions) == 0:
            return violations

        # Calculate prediction error
        mse = np.mean((predictions - actuals) ** 2)
        self.prediction_errors.append(mse)

        # Check if error is increasing
        if len(self.prediction_errors) >= 5:
            recent_errors = list(self.prediction_errors)[-5:]
            error_trend = np.polyfit(range(len(recent_errors)), recent_errors, 1)[0]

            if error_trend > 0.01:  # Error increasing
                severity = min(1.0, error_trend * 10)

                violation = SafetyViolation(
                    violation_type=SafetyViolationType.MODEL_DIVERGENCE,
                    severity=severity,
                    description=f"Model error increasing (trend: {error_trend:.4f})",
                    detected_at=self.timezone_manager.get_user_now(),
                    context={"error_trend": error_trend, "recent_mse": mse},
                    suggested_action="Consider model retraining or use fallback predictions"
                )
                violations.append(violation)

        return violations

    def _check_resource_usage(self, computation_time: float) -> List[SafetyViolation]:
        """Check resource usage violations."""
        violations = []

        # Check computation time
        if computation_time > self.config.max_computation_time_seconds:
            severity = min(1.0, computation_time / (self.config.max_computation_time_seconds * 2))

            violation = SafetyViolation(
                violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                severity=severity,
                description=f"Computation time {computation_time:.2f}s exceeds limit {self.config.max_computation_time_seconds}s",
                detected_at=self.timezone_manager.get_user_now(),
                context={"computation_time": computation_time, "limit": self.config.max_computation_time_seconds},
                suggested_action="Optimize algorithms or use faster fallback methods"
            )
            violations.append(violation)

        return violations


class SafeGuardedBandit(WeightTuner):
    """Bandit with integrated safety monitoring and protection."""

    def __init__(self, *args, safety_monitor: Optional[SafetyMonitor] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.safety_monitor = safety_monitor or SafetyMonitor()

        # Fallback weight configuration
        self.fallback_weights = {
            'context_switch': 1.5,
            'avoid_window': 1.0,
            'late_night': 2.0,
            'morning': 1.0,
            'fragmentation': 1.0,
            'spacing_violation': 2.0,
            'fairness': 1.0
        }

    def suggest_weights(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Suggest weights with safety monitoring."""

        # Check if we should use fallback
        if self.safety_monitor.should_use_fallback():
            logger.info("Using fallback weights due to safety concerns")
            return self.fallback_weights.copy()

        # Get normal suggestion
        proposed_weights = super().suggest_weights(context)

        # Apply safety constraints
        safe_weights = self.safety_monitor.get_safe_weights(
            proposed_weights, self.fallback_weights
        )

        # Check for violations
        violations = self.safety_monitor.check_bandit_safety(
            self, safe_weights, context=context
        )

        # Activate safety mode if needed
        severe_violations = [v for v in violations if v.severity >= 0.7]
        if severe_violations:
            self.safety_monitor.activate_safety_mode(
                f"Severe violations detected: {[v.violation_type.value for v in severe_violations]}"
            )
            return self.fallback_weights.copy()

        return safe_weights

    def update(self, context: Dict[str, Any], weights: Dict[str, float], reward: float):
        """Update with safety monitoring."""

        # Check safety before update
        violations = self.safety_monitor.check_bandit_safety(
            self, weights, reward=reward, context=context
        )

        # Only update if safe
        if not any(v.severity >= 0.9 for v in violations):
            super().update(context, weights, reward)
        else:
            logger.warning("Skipping bandit update due to safety violations")

        # Try to deactivate safety mode if performance is good
        self.safety_monitor.deactivate_safety_mode()


# Factory function
def create_safe_bandit(**kwargs) -> SafeGuardedBandit:
    """Create a bandit with safety monitoring."""
    return SafeGuardedBandit(**kwargs)

