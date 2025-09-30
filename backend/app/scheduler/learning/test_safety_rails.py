"""
Test suite for ML safety rails functionality.

Demonstrates safety features and protection mechanisms.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

from .safety_rails import (
    SafetyMonitor, SafetyConfig, SafeGuardedBandit,
    SafetyViolationType, BottleneckSeverity
)
from .safe_models import SafeCompletionModel
from .safety_integration import (
    SystemSafetyManager, SafetyLevel,
    create_safe_bandit, create_safe_model
)


def test_safety_monitor_basic():
    """Test basic safety monitor functionality."""

    monitor = SafetyMonitor()

    # Test initial state
    status = monitor.get_safety_status()
    assert not status["safety_mode_active"]
    assert status["total_violations"] == 0

    # Test weight bounds checking
    bad_weights = {"test_weight": 15.0}  # Exceeds max_weight
    violations = monitor._check_weight_bounds(bad_weights)

    assert len(violations) == 1
    assert violations[0].violation_type == SafetyViolationType.EXTREME_WEIGHTS
    assert violations[0].severity > 0.5


def test_safety_monitor_reward_degradation():
    """Test reward degradation detection."""

    config = SafetyConfig(min_reward_threshold=-1.0, reward_degradation_window=3)
    monitor = SafetyMonitor(config)

    # Add consistently poor rewards
    for _ in range(3):
        monitor.recent_rewards.append(-1.5)

    violations = monitor._check_reward_degradation()

    assert len(violations) == 1
    assert violations[0].violation_type == SafetyViolationType.REWARD_DEGRADATION


def test_safe_guarded_bandit():
    """Test bandit with safety protection."""

    bandit = SafeGuardedBandit()

    # Test normal operation
    context = {"user_id": "test", "horizon_days": 7}
    weights = bandit.suggest_weights(context)

    assert isinstance(weights, dict)
    assert all(0.1 <= w <= 10.0 for w in weights.values())

    # Test safety fallback (simulate violations)
    bandit.safety_monitor.activate_safety_mode("Test violation")
    fallback_weights = bandit.suggest_weights(context)

    assert fallback_weights == bandit.fallback_weights


def test_safe_completion_model():
    """Test completion model with safety features."""

    model = SafeCompletionModel()

    # Test normal prediction
    task_features = {"duration_minutes": 60, "priority": 3}
    slot_features = {"hour": 10, "day_of_week": 1}
    user_features = {"user_id": "test"}

    prediction = model.predict_completion_probability(
        task_features, slot_features, user_features
    )

    assert 0.0 <= prediction <= 1.0

    # Test invalid input handling
    bad_task_features = {"duration_minutes": 1000}  # Invalid duration
    bad_prediction = model.predict_completion_probability(
        bad_task_features, slot_features, user_features
    )

    # Should use fallback
    assert 0.0 <= bad_prediction <= 1.0


def test_system_safety_manager():
    """Test system-wide safety management."""

    manager = SystemSafetyManager()

    # Test component registration
    monitor = manager.register_component("test_bandit", "bandit")
    assert "test_bandit" in manager.component_monitors
    assert isinstance(monitor, SafetyMonitor)

    # Test ML operation tracking
    assert manager.should_use_ml("test_bandit", "prediction")

    # Simulate resource exhaustion
    manager.total_ml_time_ms = manager.config.max_total_ml_time_ms + 1000
    violations = manager._check_global_constraints()

    assert len(violations) > 0
    assert any(v.violation_type == SafetyViolationType.RESOURCE_EXHAUSTION for v in violations)


def test_safety_levels():
    """Test different safety levels."""

    # Test paranoid level (should disable ML)
    manager = SystemSafetyManager()
    manager.config.safety_level = SafetyLevel.PARANOID
    manager._initialize_component_configs()

    assert not manager.should_use_ml("test_component", "prediction")

    # Test minimal level (should be permissive)
    manager.config.safety_level = SafetyLevel.MINIMAL
    manager._initialize_component_configs()

    assert manager.should_use_ml("test_component", "prediction")


def test_factory_functions():
    """Test factory functions for safe components."""

    # Test safe bandit creation
    bandit = create_safe_bandit(safety_level=SafetyLevel.STRICT)
    assert isinstance(bandit, SafeGuardedBandit)
    assert bandit.safety_monitor is not None

    # Test safe model creation
    model = create_safe_model(safety_level=SafetyLevel.STANDARD)
    assert isinstance(model, SafeCompletionModel)
    assert model.safety_monitor is not None


def test_violation_scenarios():
    """Test various safety violation scenarios."""

    monitor = SafetyMonitor()

    # Test oscillating weights
    for i in range(6):
        weights = {"test_weight": 1.0 if i % 2 == 0 else 5.0}
        monitor.weight_history.append(weights)

    violations = monitor._check_weight_oscillation()
    assert len(violations) > 0

    # Test context anomalies
    bad_context = {"horizon_days": 100}  # Outside expected range
    violations = monitor._check_context_anomalies(bad_context)
    assert len(violations) > 0


def test_performance_monitoring():
    """Test performance monitoring and reporting."""

    manager = SystemSafetyManager()

    # Simulate ML operations
    op_id = "test_op_123"
    manager.active_ml_operations = 1
    manager.performance_metrics["test_component"] = {
        "total_operations": 5,
        "total_time_ms": 500.0,
        "success_rate": 0.8,
        "avg_duration_ms": 100.0
    }

    report = manager.get_performance_report()

    assert "system_config" in report
    assert "resource_usage" in report
    assert "component_performance" in report
    assert report["resource_usage"]["active_operations"] == 1


def test_fallback_mechanisms():
    """Test fallback mechanisms under safety violations."""

    model = SafeCompletionModel()

    # Force consecutive failures
    model.consecutive_failures = model.max_consecutive_failures

    # Should use fallback
    task_features = {"duration_minutes": 60, "priority": 3}
    slot_features = {"hour": 10, "day_of_week": 1}
    user_features = {"user_id": "test"}

    prediction = model.predict_completion_probability(
        task_features, slot_features, user_features
    )

    # Should be fallback prediction
    assert prediction == model._get_fallback_prediction(task_features)


if __name__ == "__main__":
    # Run basic tests
    print("Testing safety rails...")

    test_safety_monitor_basic()
    print("Safety monitor: PASSED")

    test_safe_guarded_bandit()
    print("Safe bandit: PASSED")

    test_safe_completion_model()
    print("Safe model: PASSED")

    test_system_safety_manager()
    print("Safety manager: PASSED")

    test_safety_levels()
    print("Safety levels: PASSED")

    test_factory_functions()
    print("Factory functions: PASSED")

    print("All safety rail tests passed!")