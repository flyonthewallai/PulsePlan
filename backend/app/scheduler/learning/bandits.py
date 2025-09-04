"""
Contextual bandit algorithms for adaptive weight tuning.

Uses Thompson Sampling and other bandit algorithms to automatically tune
penalty weights in the scheduling objective function.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .model_store import ModelStore, get_model_store

logger = logging.getLogger(__name__)


class BanditAlgorithm(Enum):
    """Available bandit algorithms."""
    THOMPSON_SAMPLING = "thompson"
    UCB1 = "ucb1"
    EXP3 = "exp3"
    EPSILON_GREEDY = "epsilon_greedy"


@dataclass
class BanditArm:
    """Represents a bandit arm (weight configuration)."""
    weights: Dict[str, float]
    num_pulls: int = 0
    total_reward: float = 0.0
    reward_variance: float = 0.0
    last_pulled: Optional[datetime] = None
    
    @property
    def mean_reward(self) -> float:
        """Average reward for this arm."""
        return self.total_reward / max(1, self.num_pulls)
    
    def update(self, reward: float):
        """Update arm statistics with new reward."""
        old_mean = self.mean_reward
        self.num_pulls += 1
        self.total_reward += reward
        self.last_pulled = datetime.now()
        
        # Update variance (Welford's online algorithm)
        new_mean = self.mean_reward
        if self.num_pulls == 1:
            self.reward_variance = 0.0
        else:
            delta1 = reward - old_mean
            delta2 = reward - new_mean
            self.reward_variance += delta1 * delta2


@dataclass 
class ContextualBanditConfig:
    """Configuration for contextual bandit."""
    algorithm: BanditAlgorithm = BanditAlgorithm.THOMPSON_SAMPLING
    exploration_rate: float = 0.1
    decay_rate: float = 0.995
    prior_mean: float = 0.0
    prior_variance: float = 1.0
    context_weights: Dict[str, float] = field(default_factory=dict)
    arm_update_threshold: int = 5  # Min pulls before considering arm viable


class WeightTuner:
    """
    Contextual bandit for tuning scheduling penalty weights.
    
    Learns optimal weight configurations based on user feedback and
    scheduling outcomes (missed tasks, user edits, completion rates).
    """
    
    def __init__(
        self,
        config: ContextualBanditConfig = None,
        store: Optional[ModelStore] = None,
        weight_names: Optional[List[str]] = None
    ):
        """
        Initialize weight tuner.
        
        Args:
            config: Bandit configuration
            store: Model persistence store
            weight_names: Names of weights to tune
        """
        self.config = config or ContextualBanditConfig()
        self.store = store or get_model_store()
        
        # Default penalty weights to tune
        self.weight_names = weight_names or [
            'context_switch',
            'avoid_window', 
            'late_night',
            'morning',
            'fragmentation',
            'spacing_violation',
            'fairness'
        ]
        
        # Initialize arms with different weight configurations
        self.arms: List[BanditArm] = []
        self.context_history: List[Dict] = []
        self.reward_history: List[float] = []
        
        # Algorithm-specific state
        self.algorithm_state = {}
        
        # Initialize default arms
        self._initialize_arms()
    
    def _initialize_arms(self):
        """Initialize bandit arms with different weight configurations."""
        # Base configuration
        base_weights = {
            'context_switch': 2.0,
            'avoid_window': 1.5,
            'late_night': 3.0,
            'morning': 1.0,
            'fragmentation': 1.2,
            'spacing_violation': 2.5,
            'fairness': 1.0
        }
        
        # Create variations
        variations = [
            # Conservative (lower penalties)
            {name: weight * 0.5 for name, weight in base_weights.items()},
            
            # Balanced (base configuration)
            base_weights.copy(),
            
            # Aggressive (higher penalties)
            {name: weight * 1.5 for name, weight in base_weights.items()},
            
            # Focus on time preferences
            {**base_weights, 'late_night': 5.0, 'morning': 0.5, 'avoid_window': 3.0},
            
            # Focus on task continuity
            {**base_weights, 'context_switch': 4.0, 'fragmentation': 3.0},
            
            # Focus on fairness
            {**base_weights, 'fairness': 3.0, 'spacing_violation': 4.0},
            
            # Minimal constraints
            {name: 0.5 for name in base_weights.keys()},
            
            # High constraints
            {name: weight * 2.0 for name, weight in base_weights.items()}
        ]
        
        # Create arms
        self.arms = [BanditArm(weights=weights) for weights in variations]
        
        # Initialize algorithm-specific state
        if self.config.algorithm == BanditAlgorithm.EXP3:
            n_arms = len(self.arms)
            self.algorithm_state['weights'] = np.ones(n_arms) / n_arms
            self.algorithm_state['gamma'] = self.config.exploration_rate
        
        logger.info(f"Initialized {len(self.arms)} bandit arms")
    
    def suggest_weights(self, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Suggest penalty weights based on context using bandit algorithm.
        
        Args:
            context: Current context (user profile, time, etc.)
            
        Returns:
            Dictionary of penalty weights
        """
        try:
            # Select arm based on algorithm
            if self.config.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
                arm_idx = self._thompson_sampling_select(context)
            elif self.config.algorithm == BanditAlgorithm.UCB1:
                arm_idx = self._ucb1_select(context)
            elif self.config.algorithm == BanditAlgorithm.EXP3:
                arm_idx = self._exp3_select(context)
            elif self.config.algorithm == BanditAlgorithm.EPSILON_GREEDY:
                arm_idx = self._epsilon_greedy_select(context)
            else:
                arm_idx = 1  # Default to balanced configuration
            
            selected_arm = self.arms[arm_idx]
            
            # Store context for later reward assignment
            self.context_history.append({
                'context': context.copy(),
                'arm_idx': arm_idx,
                'timestamp': datetime.now(),
                'weights': selected_arm.weights.copy()
            })
            
            # Keep only recent history
            if len(self.context_history) > 1000:
                self.context_history = self.context_history[-1000:]
            
            logger.debug(f"Selected arm {arm_idx} with weights: {selected_arm.weights}")
            
            return selected_arm.weights.copy()
            
        except Exception as e:
            logger.error(f"Weight suggestion failed: {e}")
            # Fallback to balanced configuration
            return self.arms[1].weights.copy() if len(self.arms) > 1 else {}
    
    def update(
        self, 
        context: Dict[str, Any], 
        chosen_weights: Dict[str, float], 
        reward: float
    ):
        """
        Update bandit with reward feedback.
        
        Args:
            context: Context that was used for selection
            chosen_weights: Weights that were chosen
            reward: Reward signal (higher = better)
        """
        try:
            # Find the arm that was selected
            arm_idx = None
            for i, entry in enumerate(reversed(self.context_history)):
                if self._weights_match(entry['weights'], chosen_weights):
                    # Find actual arm index
                    for j, arm in enumerate(self.arms):
                        if self._weights_match(arm.weights, chosen_weights):
                            arm_idx = j
                            break
                    break
            
            if arm_idx is None:
                logger.warning("Could not find matching arm for reward update")
                return
            
            # Update arm
            self.arms[arm_idx].update(reward)
            
            # Update algorithm-specific state
            if self.config.algorithm == BanditAlgorithm.EXP3:
                self._exp3_update(arm_idx, reward)
            
            # Store reward
            self.reward_history.append(reward)
            if len(self.reward_history) > 1000:
                self.reward_history = self.reward_history[-1000:]
            
            logger.debug(f"Updated arm {arm_idx} with reward {reward:.3f}")
            
        except Exception as e:
            logger.error(f"Bandit update failed: {e}")
    
    def _thompson_sampling_select(self, context: Dict[str, Any]) -> int:
        """Select arm using Thompson Sampling."""
        samples = []
        
        for arm in self.arms:
            if arm.num_pulls == 0:
                # Use prior for unplayed arms
                mean = self.config.prior_mean
                variance = self.config.prior_variance
            else:
                # Use posterior based on observed rewards
                mean = arm.mean_reward
                # Bayesian update of variance
                variance = max(0.01, arm.reward_variance / arm.num_pulls + self.config.prior_variance)
            
            # Sample from posterior
            sample = np.random.normal(mean, np.sqrt(variance))
            samples.append(sample)
        
        return int(np.argmax(samples))
    
    def _ucb1_select(self, context: Dict[str, Any]) -> int:
        """Select arm using UCB1."""
        total_pulls = sum(arm.num_pulls for arm in self.arms)
        
        if total_pulls == 0:
            return 0
        
        ucb_values = []
        for arm in self.arms:
            if arm.num_pulls == 0:
                ucb_values.append(float('inf'))
            else:
                confidence = np.sqrt(2 * np.log(total_pulls) / arm.num_pulls)
                ucb = arm.mean_reward + confidence
                ucb_values.append(ucb)
        
        return int(np.argmax(ucb_values))
    
    def _exp3_select(self, context: Dict[str, Any]) -> int:
        """Select arm using EXP3."""
        weights = self.algorithm_state['weights']
        gamma = self.algorithm_state['gamma']
        
        # Add exploration component
        n_arms = len(self.arms)
        probs = (1 - gamma) * weights + gamma / n_arms
        
        # Sample from probability distribution
        return np.random.choice(len(self.arms), p=probs)
    
    def _exp3_update(self, arm_idx: int, reward: float):
        """Update EXP3 weights."""
        gamma = self.algorithm_state['gamma']
        weights = self.algorithm_state['weights']
        n_arms = len(self.arms)
        
        # Compute estimated reward
        probs = (1 - gamma) * weights + gamma / n_arms
        estimated_reward = reward / probs[arm_idx]
        
        # Update weights
        weights[arm_idx] *= np.exp(gamma * estimated_reward / n_arms)
        
        # Normalize
        weights /= weights.sum()
        
        self.algorithm_state['weights'] = weights
    
    def _epsilon_greedy_select(self, context: Dict[str, Any]) -> int:
        """Select arm using epsilon-greedy."""
        if np.random.random() < self.config.exploration_rate:
            # Explore: random arm
            return np.random.randint(len(self.arms))
        else:
            # Exploit: best arm
            mean_rewards = [arm.mean_reward for arm in self.arms]
            return int(np.argmax(mean_rewards))
    
    def _weights_match(self, weights1: Dict[str, float], weights2: Dict[str, float]) -> bool:
        """Check if two weight dictionaries match (within tolerance)."""
        if set(weights1.keys()) != set(weights2.keys()):
            return False
        
        for key in weights1:
            if abs(weights1[key] - weights2[key]) > 1e-6:
                return False
        
        return True
    
    def get_arm_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all arms."""
        stats = []
        for i, arm in enumerate(self.arms):
            stats.append({
                'arm_idx': i,
                'weights': arm.weights,
                'num_pulls': arm.num_pulls,
                'mean_reward': arm.mean_reward,
                'total_reward': arm.total_reward,
                'last_pulled': arm.last_pulled
            })
        return stats
    
    def get_best_arm(self) -> Tuple[int, BanditArm]:
        """Get the currently best performing arm."""
        if not self.arms:
            return 0, None
        
        # Filter arms with sufficient data
        viable_arms = [
            (i, arm) for i, arm in enumerate(self.arms)
            if arm.num_pulls >= self.config.arm_update_threshold
        ]
        
        if not viable_arms:
            # Fall back to any arm with data
            viable_arms = [(i, arm) for i, arm in enumerate(self.arms) if arm.num_pulls > 0]
        
        if not viable_arms:
            # Fall back to first arm
            return 0, self.arms[0]
        
        # Select arm with highest mean reward
        best_idx, best_arm = max(viable_arms, key=lambda x: x[1].mean_reward)
        return best_idx, best_arm
    
    async def save(self, user_id: str) -> bool:
        """Save bandit state to persistent storage."""
        try:
            bandit_state = {
                'arms': [
                    {
                        'weights': arm.weights,
                        'num_pulls': arm.num_pulls,
                        'total_reward': arm.total_reward,
                        'reward_variance': arm.reward_variance,
                        'last_pulled': arm.last_pulled.isoformat() if arm.last_pulled else None
                    }
                    for arm in self.arms
                ],
                'algorithm_state': self.algorithm_state,
                'config': {
                    'algorithm': self.config.algorithm.value,
                    'exploration_rate': self.config.exploration_rate,
                    'decay_rate': self.config.decay_rate,
                    'prior_mean': self.config.prior_mean,
                    'prior_variance': self.config.prior_variance
                },
                'weight_names': self.weight_names,
                'recent_rewards': self.reward_history[-100:],  # Last 100 rewards
            }
            
            metadata = {
                'model_type': 'bandit',
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'n_arms': len(self.arms),
                'total_pulls': sum(arm.num_pulls for arm in self.arms)
            }
            
            success = await self.store.save_model_params(
                user_id, 'bandit', bandit_state, metadata
            )
            
            if success:
                logger.info(f"Bandit state saved for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving bandit state for user {user_id}: {e}")
            return False
    
    async def load(self, user_id: str) -> bool:
        """Load bandit state from persistent storage."""
        try:
            bandit_state = await self.store.load_model_params(user_id, 'bandit')
            
            if not bandit_state:
                logger.info(f"No saved bandit state found for user {user_id}")
                return False
            
            # Restore arms
            self.arms = []
            for arm_data in bandit_state['arms']:
                arm = BanditArm(
                    weights=arm_data['weights'],
                    num_pulls=arm_data['num_pulls'],
                    total_reward=arm_data['total_reward'],
                    reward_variance=arm_data['reward_variance']
                )
                if arm_data['last_pulled']:
                    arm.last_pulled = datetime.fromisoformat(arm_data['last_pulled'])
                self.arms.append(arm)
            
            # Restore algorithm state
            self.algorithm_state = bandit_state.get('algorithm_state', {})
            
            # Restore configuration
            config_data = bandit_state.get('config', {})
            self.config.algorithm = BanditAlgorithm(config_data.get('algorithm', 'thompson'))
            self.config.exploration_rate = config_data.get('exploration_rate', 0.1)
            
            # Restore other data
            self.weight_names = bandit_state.get('weight_names', self.weight_names)
            self.reward_history = bandit_state.get('recent_rewards', [])
            
            logger.info(f"Bandit state loaded for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading bandit state for user {user_id}: {e}")
            return False


def compute_reward(
    schedule_outcome: Dict[str, Any],
    user_feedback: Optional[Dict[str, Any]] = None
) -> float:
    """
    Compute reward signal from scheduling outcome and user feedback.
    
    Args:
        schedule_outcome: Results from schedule execution
        user_feedback: Optional explicit user feedback
        
    Returns:
        Reward value (higher = better)
    """
    reward = 0.0
    
    # Completion rate component (0 to 1)
    completion_rate = schedule_outcome.get('completion_rate', 0.7)
    reward += completion_rate
    
    # Penalty for missed tasks
    missed_tasks = schedule_outcome.get('missed_tasks', 0)
    reward -= missed_tasks * 0.2
    
    # Penalty for user reschedules/edits
    user_edits = schedule_outcome.get('user_edits', 0)
    reward -= user_edits * 0.1
    
    # Bonus for on-time completion
    on_time_completions = schedule_outcome.get('on_time_completions', 0)
    reward += on_time_completions * 0.1
    
    # User satisfaction (if available)
    if user_feedback:
        satisfaction = user_feedback.get('satisfaction_score', 0)  # -1 to 1
        reward += satisfaction * 0.5
    
    # Feasibility bonus
    if schedule_outcome.get('feasible', False):
        reward += 0.2
    
    # Objective value (normalized)
    obj_value = schedule_outcome.get('objective_value', 0)
    max_possible_obj = schedule_outcome.get('max_possible_objective', 1)
    if max_possible_obj > 0:
        reward += (obj_value / max_possible_obj) * 0.3
    
    return max(-2.0, min(3.0, reward))  # Clip to reasonable range