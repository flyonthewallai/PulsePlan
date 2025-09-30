"""
Safe wrappers for ML models with built-in protection mechanisms.

Provides safe versions of completion models and other ML components
with automatic fallback, validation, and monitoring.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import pickle
import warnings

from .completion_model import CompletionModel
from .safety_rails import SafetyMonitor, SafetyViolationType, SafetyViolation
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class SafeCompletionModel(CompletionModel):
    """Completion model with safety monitoring and fallback mechanisms."""

    def __init__(self, safety_monitor: Optional[SafetyMonitor] = None, **kwargs):
        super().__init__(**kwargs)
        self.safety_monitor = safety_monitor or SafetyMonitor()
        self.timezone_manager = get_timezone_manager()

        # Fallback predictions
        self.fallback_probability = 0.6  # Conservative default
        self.prediction_cache = {}
        self.last_safe_model_state = None

        # Model validation
        self.validation_errors = []
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

    def predict_completion_probability(
        self,
        task_features: Dict[str, Any],
        slot_features: Dict[str, Any],
        user_features: Dict[str, Any]
    ) -> float:
        """Predict completion probability with safety checks."""

        try:
            # Validate inputs
            if not self._validate_features(task_features, slot_features, user_features):
                logger.warning("Feature validation failed, using fallback prediction")
                return self._get_fallback_prediction(task_features)

            # Check if model is safe to use
            if not self._is_model_safe():
                logger.info("Model not safe, using fallback prediction")
                return self._get_fallback_prediction(task_features)

            # Get prediction with timing
            start_time = datetime.now()
            prediction = super().predict_completion_probability(
                task_features, slot_features, user_features
            )
            computation_time = (datetime.now() - start_time).total_seconds()

            # Validate prediction
            if not self._validate_prediction(prediction):
                logger.warning(f"Invalid prediction {prediction}, using fallback")
                return self._get_fallback_prediction(task_features)

            # Check safety violations
            violations = self.safety_monitor.check_model_safety(
                self, np.array([prediction]), computation_time=computation_time
            )

            # Use fallback if severe violations
            if any(v.severity >= 0.8 for v in violations):
                logger.warning("Severe safety violations detected, using fallback")
                return self._get_fallback_prediction(task_features)

            # Reset failure counter on success
            self.consecutive_failures = 0

            return prediction

        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            self.consecutive_failures += 1

            # Record the failure
            violation = SafetyViolation(
                violation_type=SafetyViolationType.MODEL_DIVERGENCE,
                severity=0.8,
                description=f"Model prediction failed: {str(e)}",
                detected_at=self.timezone_manager.get_user_now(),
                context={"error": str(e), "consecutive_failures": self.consecutive_failures},
                suggested_action="Use fallback predictions and check model integrity"
            )
            self.safety_monitor.violations.append(violation)

            return self._get_fallback_prediction(task_features)

    def batch_predict(
        self,
        feature_batch: List[Tuple[Dict, Dict, Dict]]
    ) -> List[float]:
        """Batch prediction with safety monitoring."""

        if not feature_batch:
            return []

        # Check batch size
        if len(feature_batch) > 1000:
            logger.warning(f"Large batch size {len(feature_batch)}, using smaller batches")
            # Process in smaller batches
            results = []
            for i in range(0, len(feature_batch), 500):
                batch_slice = feature_batch[i:i+500]
                results.extend(self.batch_predict(batch_slice))
            return results

        try:
            # Get predictions
            start_time = datetime.now()
            predictions = []

            for task_features, slot_features, user_features in feature_batch:
                pred = self.predict_completion_probability(
                    task_features, slot_features, user_features
                )
                predictions.append(pred)

            computation_time = (datetime.now() - start_time).total_seconds()

            # Check batch safety
            violations = self.safety_monitor.check_model_safety(
                self, np.array(predictions), computation_time=computation_time
            )

            # Log batch performance
            logger.debug(f"Batch prediction: {len(predictions)} items in {computation_time:.3f}s")

            return predictions

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            # Return fallback predictions for entire batch
            return [self._get_fallback_prediction(features[0]) for features in feature_batch]

    def update_model(
        self,
        task_outcomes: List[Dict[str, Any]],
        user_id: str
    ) -> bool:
        """Update model with safety checks."""

        try:
            # Validate training data
            if not self._validate_training_data(task_outcomes):
                logger.warning("Training data validation failed, skipping update")
                return False

            # Save current model state before update
            self.last_safe_model_state = self._serialize_model_state()

            # Perform update
            success = super().update_model(task_outcomes, user_id)

            if success:
                # Validate updated model
                if self._validate_updated_model(task_outcomes):
                    logger.info(f"Model updated successfully for user {user_id}")
                    return True
                else:
                    logger.warning("Updated model failed validation, reverting")
                    self._revert_model_state()
                    return False

            return False

        except Exception as e:
            logger.error(f"Model update failed: {e}")
            if self.last_safe_model_state:
                self._revert_model_state()
            return False

    def get_model_health(self) -> Dict[str, Any]:
        """Get comprehensive model health status."""

        try:
            health = {
                "is_fitted": self.is_fitted,
                "consecutive_failures": self.consecutive_failures,
                "is_safe": self._is_model_safe(),
                "validation_errors": len(self.validation_errors),
                "safety_status": self.safety_monitor.get_safety_status(),
                "model_age_hours": 0,  # Would track actual model age
                "prediction_cache_size": len(self.prediction_cache),
                "last_update": None  # Would track last update time
            }

            # Add model-specific metrics if available
            if hasattr(self, 'feature_importance_'):
                health["feature_importance"] = dict(zip(
                    self.feature_names_, self.feature_importance_
                )) if hasattr(self, 'feature_names_') else None

            return health

        except Exception as e:
            logger.error(f"Failed to get model health: {e}")
            return {"error": str(e), "is_safe": False}

    def _validate_features(
        self,
        task_features: Dict[str, Any],
        slot_features: Dict[str, Any],
        user_features: Dict[str, Any]
    ) -> bool:
        """Validate input features for safety."""

        required_task_features = ['duration_minutes', 'priority']
        required_slot_features = ['hour', 'day_of_week']
        required_user_features = ['user_id']

        # Check required features exist
        for feature in required_task_features:
            if feature not in task_features:
                logger.warning(f"Missing required task feature: {feature}")
                return False

        for feature in required_slot_features:
            if feature not in slot_features:
                logger.warning(f"Missing required slot feature: {feature}")
                return False

        for feature in required_user_features:
            if feature not in user_features:
                logger.warning(f"Missing required user feature: {feature}")
                return False

        # Validate feature values
        duration = task_features.get('duration_minutes', 0)
        if not (5 <= duration <= 480):  # 5 minutes to 8 hours
            logger.warning(f"Invalid duration: {duration}")
            return False

        priority = task_features.get('priority', 0)
        if not (1 <= priority <= 5):
            logger.warning(f"Invalid priority: {priority}")
            return False

        hour = slot_features.get('hour', 0)
        if not (0 <= hour <= 23):
            logger.warning(f"Invalid hour: {hour}")
            return False

        day_of_week = slot_features.get('day_of_week', 0)
        if not (0 <= day_of_week <= 6):
            logger.warning(f"Invalid day of week: {day_of_week}")
            return False

        return True

    def _validate_prediction(self, prediction: float) -> bool:
        """Validate a single prediction."""

        # Check if prediction is a valid probability
        if not isinstance(prediction, (int, float)):
            return False

        if np.isnan(prediction) or np.isinf(prediction):
            return False

        if not (0.0 <= prediction <= 1.0):
            return False

        return True

    def _validate_training_data(self, task_outcomes: List[Dict[str, Any]]) -> bool:
        """Validate training data quality."""

        if not task_outcomes:
            logger.warning("Empty training data")
            return False

        if len(task_outcomes) < 3:
            logger.warning("Insufficient training data")
            return False

        # Check data quality
        valid_outcomes = 0
        for outcome in task_outcomes:
            if not isinstance(outcome, dict):
                continue

            # Check required fields
            required_fields = ['task_id', 'completed', 'scheduled_time']
            if all(field in outcome for field in required_fields):
                valid_outcomes += 1

        if valid_outcomes / len(task_outcomes) < 0.8:
            logger.warning(f"Low quality training data: {valid_outcomes}/{len(task_outcomes)} valid")
            return False

        return True

    def _validate_updated_model(self, task_outcomes: List[Dict[str, Any]]) -> bool:
        """Validate model after update."""

        try:
            # Test predictions on a sample
            test_features = self._create_test_features()
            test_prediction = self.predict_completion_probability(
                test_features[0], test_features[1], test_features[2]
            )

            # Check if prediction is reasonable
            if not self._validate_prediction(test_prediction):
                return False

            # Check if model still makes sense
            # For example, higher priority tasks should generally have higher completion probability
            high_priority_pred = self.predict_completion_probability(
                {**test_features[0], 'priority': 5},
                test_features[1],
                test_features[2]
            )

            low_priority_pred = self.predict_completion_probability(
                {**test_features[0], 'priority': 1},
                test_features[1],
                test_features[2]
            )

            # Sanity check: high priority should generally be more likely to complete
            if high_priority_pred < low_priority_pred - 0.3:  # Allow some tolerance
                logger.warning("Model sanity check failed: high priority less likely than low priority")
                return False

            return True

        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False

    def _get_fallback_prediction(self, task_features: Dict[str, Any]) -> float:
        """Get fallback prediction based on simple heuristics."""

        # Cache key
        cache_key = f"{task_features.get('priority', 3)}_{task_features.get('duration_minutes', 60)}"

        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]

        # Simple heuristic based on priority and duration
        priority = task_features.get('priority', 3)
        duration = task_features.get('duration_minutes', 60)

        # Base probability
        base_prob = self.fallback_probability

        # Adjust for priority (1-5 scale)
        priority_adjustment = (priority - 3) * 0.1  # +/- 0.2 for extreme priorities

        # Adjust for duration (shorter tasks more likely to complete)
        if duration <= 30:
            duration_adjustment = 0.1
        elif duration <= 60:
            duration_adjustment = 0.0
        elif duration <= 120:
            duration_adjustment = -0.1
        else:
            duration_adjustment = -0.2

        prediction = max(0.1, min(0.9, base_prob + priority_adjustment + duration_adjustment))

        # Cache the result
        self.prediction_cache[cache_key] = prediction

        return prediction

    def _is_model_safe(self) -> bool:
        """Check if model is safe to use."""

        # Too many consecutive failures
        if self.consecutive_failures >= self.max_consecutive_failures:
            return False

        # Safety monitor says not safe
        if self.safety_monitor.should_use_fallback():
            return False

        # Model not properly fitted
        if not self.is_fitted:
            return False

        return True

    def _serialize_model_state(self) -> Optional[bytes]:
        """Serialize current model state for backup."""

        try:
            if hasattr(self, 'model') and self.model is not None:
                return pickle.dumps({
                    'model': self.model,
                    'is_fitted': self.is_fitted,
                    'feature_names': getattr(self, 'feature_names_', None)
                })
        except Exception as e:
            logger.warning(f"Failed to serialize model state: {e}")

        return None

    def _revert_model_state(self):
        """Revert to last safe model state."""

        try:
            if self.last_safe_model_state:
                state = pickle.loads(self.last_safe_model_state)
                self.model = state['model']
                self.is_fitted = state['is_fitted']
                if state['feature_names']:
                    self.feature_names_ = state['feature_names']

                logger.info("Reverted to last safe model state")

        except Exception as e:
            logger.error(f"Failed to revert model state: {e}")

    def _create_test_features(self) -> Tuple[Dict, Dict, Dict]:
        """Create test features for model validation."""

        return (
            {'duration_minutes': 60, 'priority': 3},
            {'hour': 10, 'day_of_week': 1},
            {'user_id': 'test_user'}
        )


class ModelEnsemble:
    """Ensemble of models with voting and safety mechanisms."""

    def __init__(self, models: List[SafeCompletionModel], voting_strategy: str = "average"):
        self.models = models
        self.voting_strategy = voting_strategy
        self.model_weights = [1.0] * len(models)  # Equal weights initially
        self.safety_monitor = SafetyMonitor()

    def predict_completion_probability(
        self,
        task_features: Dict[str, Any],
        slot_features: Dict[str, Any],
        user_features: Dict[str, Any]
    ) -> float:
        """Ensemble prediction with safety checks."""

        predictions = []
        weights = []

        for i, model in enumerate(self.models):
            try:
                if model._is_model_safe():
                    pred = model.predict_completion_probability(
                        task_features, slot_features, user_features
                    )
                    predictions.append(pred)
                    weights.append(self.model_weights[i])
            except Exception as e:
                logger.warning(f"Model {i} failed: {e}")

        if not predictions:
            # All models failed, use fallback
            logger.warning("All ensemble models failed, using fallback")
            return 0.6

        # Weighted average
        if self.voting_strategy == "average":
            weighted_sum = sum(p * w for p, w in zip(predictions, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight

        # Median voting
        elif self.voting_strategy == "median":
            return np.median(predictions)

        # Conservative (minimum)
        elif self.voting_strategy == "conservative":
            return min(predictions)

        else:
            return np.mean(predictions)

    def update_model_weights(self, model_performances: List[float]):
        """Update ensemble weights based on model performance."""

        if len(model_performances) != len(self.models):
            logger.warning("Performance list length mismatch")
            return

        # Normalize performances to weights
        total_performance = sum(max(0.1, p) for p in model_performances)
        self.model_weights = [max(0.1, p) / total_performance for p in model_performances]

        logger.info(f"Updated ensemble weights: {self.model_weights}")


# Factory functions
def create_safe_completion_model(**kwargs) -> SafeCompletionModel:
    """Create a safe completion model with monitoring."""
    return SafeCompletionModel(**kwargs)


def create_model_ensemble(num_models: int = 3, **kwargs) -> ModelEnsemble:
    """Create an ensemble of safe models."""
    models = [create_safe_completion_model(**kwargs) for _ in range(num_models)]
    return ModelEnsemble(models)

