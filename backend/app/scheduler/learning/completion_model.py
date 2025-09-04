"""
Completion probability prediction model.

Uses logistic regression to predict the probability that a user will complete
a task when scheduled in a specific time slot.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss, accuracy_score

from .model_store import ModelStore, get_model_store
from ..domain import CompletionEvent

logger = logging.getLogger(__name__)


class CompletionModel:
    """
    Predicts task completion probability using logistic regression.
    
    Features include time-of-day, task characteristics, user preferences,
    and historical completion patterns.
    """
    
    def __init__(
        self, 
        store: Optional[ModelStore] = None,
        learning_rate: float = 0.05,
        regularization: float = 0.01,
        random_state: int = 42
    ):
        """
        Initialize completion model.
        
        Args:
            store: Model persistence store
            learning_rate: SGD learning rate
            regularization: L2 regularization strength
            random_state: Random seed for reproducibility
        """
        self.store = store or get_model_store()
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.random_state = random_state
        
        # Initialize model components
        self.model = SGDClassifier(
            loss='log_loss',  # logistic regression
            learning_rate='constant',
            eta0=learning_rate,
            alpha=regularization,
            random_state=random_state,
            max_iter=1000,
            warm_start=True  # Allow incremental learning
        )
        
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []
        self.training_history = []
        
    async def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict completion probabilities.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Array of completion probabilities
        """
        if not self.is_fitted:
            # Return default probabilities based on simple heuristics
            return self._default_predictions(X)
        
        try:
            # Scale features and predict
            X_scaled = self.scaler.transform(X)
            probs = self.model.predict_proba(X_scaled)
            
            # Return probability of positive class (completion)
            if probs.shape[1] == 2:
                return probs[:, 1]
            else:
                return probs[:, 0]
                
        except Exception as e:
            logger.warning(f"Prediction failed, using defaults: {e}")
            return self._default_predictions(X)
    
    async def partial_fit(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Incrementally update model with new training data.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary target (1=completed, 0=not completed)
            feature_names: Names of features (for first call)
            
        Returns:
            Training metrics
        """
        try:
            if len(X) == 0:
                return {'samples': 0}
            
            # Store feature names on first call
            if feature_names and not self.feature_names:
                self.feature_names = feature_names
            
            # Initialize or update scaler
            if not self.is_fitted:
                X_scaled = self.scaler.fit_transform(X)
                classes = np.array([0, 1])  # Binary classification
                self.model.partial_fit(X_scaled, y, classes=classes)
                self.is_fitted = True
            else:
                X_scaled = self.scaler.partial_fit_transform(X)
                self.model.partial_fit(X_scaled, y)
            
            # Calculate metrics
            metrics = self._calculate_metrics(X_scaled, y)
            metrics['samples'] = len(X)
            
            # Store training history
            self.training_history.append({
                'timestamp': datetime.now(),
                'samples': len(X),
                'metrics': metrics
            })
            
            # Keep only recent history
            if len(self.training_history) > 100:
                self.training_history = self.training_history[-100:]
            
            logger.info(f"Model updated with {len(X)} samples. Accuracy: {metrics.get('accuracy', 0):.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Partial fit failed: {e}")
            return {'error': str(e)}
    
    async def fit_batch(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Fit model on a batch of data (replaces existing model).
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary target (1=completed, 0=not completed)
            feature_names: Names of features
            
        Returns:
            Training metrics
        """
        try:
            if len(X) == 0:
                return {'samples': 0}
            
            # Store feature names
            if feature_names:
                self.feature_names = feature_names
            
            # Fit scaler and model from scratch
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_fitted = True
            
            # Calculate metrics
            metrics = self._calculate_metrics(X_scaled, y)
            metrics['samples'] = len(X)
            
            logger.info(f"Model fitted on {len(X)} samples. Accuracy: {metrics.get('accuracy', 0):.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Batch fit failed: {e}")
            return {'error': str(e)}
    
    def _calculate_metrics(self, X_scaled: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Calculate training metrics."""
        try:
            # Predictions and probabilities
            y_pred = self.model.predict(X_scaled)
            y_proba = self.model.predict_proba(X_scaled)
            
            # Basic metrics
            accuracy = accuracy_score(y, y_pred)
            
            # Log loss (if we have probabilities for both classes)
            if y_proba.shape[1] == 2:
                logloss = log_loss(y, y_proba)
            else:
                logloss = 0.0
            
            # Class distribution
            pos_rate = np.mean(y)
            
            return {
                'accuracy': float(accuracy),
                'log_loss': float(logloss),
                'positive_rate': float(pos_rate),
                'n_features': X_scaled.shape[1]
            }
            
        except Exception as e:
            logger.warning(f"Metrics calculation failed: {e}")
            return {'accuracy': 0.0}
    
    def _default_predictions(self, X: np.ndarray) -> np.ndarray:
        """
        Generate default predictions when model is not fitted.
        
        Uses simple heuristics based on time-of-day patterns.
        """
        n_samples = X.shape[0]
        
        # If we have feature names, try to use time-based heuristics
        if self.feature_names and len(self.feature_names) <= X.shape[1]:
            try:
                # Look for hour and weekend features
                hour_idx = None
                weekend_idx = None
                workday_idx = None
                
                for i, name in enumerate(self.feature_names):
                    if 'hour' in name.lower():
                        hour_idx = i
                    elif 'weekend' in name.lower():
                        weekend_idx = i
                    elif 'workday' in name.lower() or 'in_workday' in name.lower():
                        workday_idx = i
                
                probs = np.full(n_samples, 0.7)  # Base probability
                
                # Adjust based on time features
                if hour_idx is not None:
                    hours = X[:, hour_idx] * 23  # De-normalize
                    # Lower probability for very early/late hours
                    probs = np.where(hours < 7, probs * 0.6, probs)
                    probs = np.where(hours > 22, probs * 0.5, probs)
                    # Higher probability for prime work hours
                    probs = np.where((hours >= 9) & (hours <= 17), probs * 1.2, probs)
                
                if weekend_idx is not None:
                    is_weekend = X[:, weekend_idx] > 0.5
                    probs = np.where(is_weekend, probs * 0.8, probs)  # Lower on weekends
                
                if workday_idx is not None:
                    in_workday = X[:, workday_idx] > 0.5
                    probs = np.where(~in_workday, probs * 0.6, probs)  # Much lower outside workday
                
                # Clip to valid probability range
                probs = np.clip(probs, 0.1, 0.95)
                
                return probs
                
            except Exception as e:
                logger.warning(f"Default prediction heuristics failed: {e}")
        
        # Fallback to uniform probabilities with slight variation
        base_prob = 0.7
        noise = np.random.RandomState(self.random_state).normal(0, 0.1, n_samples)
        probs = np.clip(base_prob + noise, 0.1, 0.95)
        
        return probs
    
    async def save(self, user_id: str) -> bool:
        """
        Save model state to persistent storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            if not self.is_fitted:
                logger.warning(f"Model not fitted, cannot save for user {user_id}")
                return False
            
            # Prepare model state
            model_params = {
                'model_coef': self.model.coef_.tolist(),
                'model_intercept': self.model.intercept_.tolist(),
                'model_classes': self.model.classes_.tolist(),
                'scaler_mean': self.scaler.mean_.tolist(),
                'scaler_scale': self.scaler.scale_.tolist(),
                'feature_names': self.feature_names,
                'is_fitted': self.is_fitted,
                'training_history': self.training_history[-10:],  # Recent history only
                'hyperparams': {
                    'learning_rate': self.learning_rate,
                    'regularization': self.regularization,
                    'random_state': self.random_state
                }
            }
            
            metadata = {
                'model_type': 'completion',
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'n_features': len(self.feature_names),
                'total_updates': len(self.training_history)
            }
            
            success = await self.store.save_model_params(
                user_id, 'completion', model_params, metadata
            )
            
            if success:
                logger.info(f"Completion model saved for user {user_id}")
            else:
                logger.error(f"Failed to save completion model for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving completion model for user {user_id}: {e}")
            return False
    
    async def load(self, user_id: str) -> bool:
        """
        Load model state from persistent storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            model_params = await self.store.load_model_params(user_id, 'completion')
            
            if not model_params:
                logger.info(f"No saved completion model found for user {user_id}")
                return False
            
            # Restore model state
            self.model.coef_ = np.array(model_params['model_coef'])
            self.model.intercept_ = np.array(model_params['model_intercept'])
            self.model.classes_ = np.array(model_params['model_classes'])
            
            # Restore scaler
            self.scaler.mean_ = np.array(model_params['scaler_mean'])
            self.scaler.scale_ = np.array(model_params['scaler_scale'])
            
            # Restore metadata
            self.feature_names = model_params['feature_names']
            self.is_fitted = model_params['is_fitted']
            self.training_history = model_params.get('training_history', [])
            
            # Restore hyperparameters if available
            hyperparams = model_params.get('hyperparams', {})
            self.learning_rate = hyperparams.get('learning_rate', self.learning_rate)
            self.regularization = hyperparams.get('regularization', self.regularization)
            
            logger.info(f"Completion model loaded for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading completion model for user {user_id}: {e}")
            return False
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_fitted or not self.feature_names:
            return None
        
        try:
            # Use absolute coefficients as importance scores
            importance_scores = np.abs(self.model.coef_[0])
            
            # Normalize to sum to 1
            if importance_scores.sum() > 0:
                importance_scores = importance_scores / importance_scores.sum()
            
            return dict(zip(self.feature_names, importance_scores))
            
        except Exception as e:
            logger.warning(f"Failed to compute feature importance: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics."""
        info = {
            'is_fitted': self.is_fitted,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'hyperparams': {
                'learning_rate': self.learning_rate,
                'regularization': self.regularization,
                'random_state': self.random_state
            },
            'training_updates': len(self.training_history)
        }
        
        if self.training_history:
            latest = self.training_history[-1]
            info['latest_metrics'] = latest.get('metrics', {})
            info['last_updated'] = latest.get('timestamp')
        
        return info


def build_training_data(
    completion_events: List[CompletionEvent],
    features: np.ndarray,
    feature_names: List[str],
    task_slot_mapping: Dict[str, List[int]]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build training data from completion events and features.
    
    Args:
        completion_events: Historical completion data
        features: Feature matrix from feature extraction
        feature_names: Names of features
        task_slot_mapping: Mapping from (task_id, slot_idx) to feature row
        
    Returns:
        (X, y) training data
    """
    X_list = []
    y_list = []
    
    for event in completion_events:
        # Find corresponding feature row
        # This requires mapping from event to task/slot indices
        # For now, we'll use a simplified approach
        
        # Create binary target
        y_val = 1 if event.completed_at is not None else 0
        
        # Would need proper mapping logic here
        # For now, skip this function as it requires more context
        pass
    
    if X_list:
        return np.array(X_list), np.array(y_list)
    else:
        return np.array([]).reshape(0, len(feature_names)), np.array([])