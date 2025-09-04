"""
Configuration management for the scheduler subsystem.

Provides centralized configuration with environment-based overrides,
validation, and runtime updates for production deployment.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class SolverConfig:
    """Configuration for the OR-Tools solver."""
    time_limit_seconds: int = 10
    num_search_workers: int = 4
    random_seed: int = 42
    use_hint_search: bool = True
    log_search_progress: bool = False
    
    def validate(self):
        """Validate solver configuration."""
        if self.time_limit_seconds < 1 or self.time_limit_seconds > 300:
            raise ValueError("time_limit_seconds must be between 1 and 300")
        if self.num_search_workers < 1 or self.num_search_workers > 16:
            raise ValueError("num_search_workers must be between 1 and 16")


@dataclass
class LearningConfig:
    """Configuration for machine learning components."""
    completion_model_lr: float = 0.05
    completion_model_regularization: float = 0.01
    bandit_algorithm: str = "thompson"
    bandit_exploration_rate: float = 0.1
    bandit_decay_rate: float = 0.995
    bandit_prior_mean: float = 0.0
    bandit_prior_variance: float = 1.0
    min_samples_for_update: int = 5
    update_frequency_hours: int = 24
    model_save_enabled: bool = True
    
    def validate(self):
        """Validate learning configuration."""
        if not 0.001 <= self.completion_model_lr <= 1.0:
            raise ValueError("completion_model_lr must be between 0.001 and 1.0")
        if not 0.0 <= self.bandit_exploration_rate <= 1.0:
            raise ValueError("bandit_exploration_rate must be between 0.0 and 1.0")
        if self.bandit_algorithm not in ["thompson", "ucb1", "exp3", "epsilon_greedy"]:
            raise ValueError("bandit_algorithm must be one of: thompson, ucb1, exp3, epsilon_greedy")


@dataclass
class DefaultWeights:
    """Default penalty weights for optimization."""
    context_switch: float = 2.0
    avoid_window: float = 1.5
    late_night: float = 3.0
    morning: float = 1.0
    fragmentation: float = 1.2
    spacing_violation: float = 2.5
    fairness: float = 1.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return asdict(self)
    
    def validate(self):
        """Validate weight values."""
        for weight_name, weight_value in asdict(self).items():
            if not 0.0 <= weight_value <= 10.0:
                raise ValueError(f"{weight_name} weight must be between 0.0 and 10.0")


@dataclass
class FeatureConfig:
    """Configuration for feature extraction."""
    include_time_features: bool = True
    include_task_features: bool = True
    include_context_features: bool = True
    include_historical_features: bool = True
    lookback_days: int = 60
    min_historical_samples: int = 5
    normalize_features: bool = True
    
    def validate(self):
        """Validate feature configuration."""
        if self.lookback_days < 1 or self.lookback_days > 365:
            raise ValueError("lookback_days must be between 1 and 365")
        if self.min_historical_samples < 1:
            raise ValueError("min_historical_samples must be at least 1")


@dataclass
class TelemetryConfig:
    """Configuration for telemetry and monitoring."""
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    export_enabled: bool = False
    export_destination: str = "default"
    export_batch_size: int = 100
    export_flush_interval_seconds: int = 60
    metrics_retention_hours: int = 24
    traces_retention_hours: int = 12
    log_level: str = "INFO"
    
    def validate(self):
        """Validate telemetry configuration."""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"log_level must be one of: {valid_log_levels}")
        if self.export_batch_size < 1 or self.export_batch_size > 10000:
            raise ValueError("export_batch_size must be between 1 and 10000")


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    backend: str = "memory"  # memory, redis, database
    ttl_minutes: int = 60
    max_size: int = 10000
    redis_url: Optional[str] = None
    
    def validate(self):
        """Validate cache configuration."""
        valid_backends = ["memory", "redis", "database"]
        if self.backend not in valid_backends:
            raise ValueError(f"backend must be one of: {valid_backends}")
        if self.backend == "redis" and not self.redis_url:
            raise ValueError("redis_url is required when backend is redis")
        if self.ttl_minutes < 1:
            raise ValueError("ttl_minutes must be at least 1")


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    backend: str = "memory"  # memory, postgresql, sqlite
    connection_string: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo_sql: bool = False
    
    def validate(self):
        """Validate database configuration."""
        valid_backends = ["memory", "postgresql", "sqlite"]
        if self.backend not in valid_backends:
            raise ValueError(f"backend must be one of: {valid_backends}")
        if self.backend != "memory" and not self.connection_string:
            raise ValueError("connection_string is required for non-memory backends")


@dataclass
class SchedulerConfig:
    """Main scheduler configuration."""
    environment: Environment = Environment.DEVELOPMENT
    
    # Component configurations
    solver: SolverConfig = field(default_factory=SolverConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)
    default_weights: DefaultWeights = field(default_factory=DefaultWeights)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Global settings
    time_granularity_minutes: int = 30
    max_horizon_days: int = 30
    default_horizon_days: int = 7
    enable_fallback_solver: bool = True
    enable_adaptive_rescheduling: bool = True
    rate_limit_requests_per_minute: int = 60
    
    def validate(self):
        """Validate all configuration components."""
        # Validate sub-components
        self.solver.validate()
        self.learning.validate()
        self.default_weights.validate()
        self.features.validate()
        self.telemetry.validate()
        self.cache.validate()
        self.database.validate()
        
        # Validate global settings
        if self.time_granularity_minutes not in [15, 30]:
            raise ValueError("time_granularity_minutes must be 15 or 30")
        if self.max_horizon_days < 1 or self.max_horizon_days > 90:
            raise ValueError("max_horizon_days must be between 1 and 90")
        if self.default_horizon_days < 1 or self.default_horizon_days > self.max_horizon_days:
            raise ValueError("default_horizon_days must be between 1 and max_horizon_days")
        if self.rate_limit_requests_per_minute < 1:
            raise ValueError("rate_limit_requests_per_minute must be at least 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchedulerConfig':
        """Create configuration from dictionary."""
        # Convert nested dictionaries to dataclasses
        config_data = data.copy()
        
        # Convert environment string to enum
        if 'environment' in config_data:
            config_data['environment'] = Environment(config_data['environment'])
        
        # Convert nested configs
        if 'solver' in config_data:
            config_data['solver'] = SolverConfig(**config_data['solver'])
        if 'learning' in config_data:
            config_data['learning'] = LearningConfig(**config_data['learning'])
        if 'default_weights' in config_data:
            config_data['default_weights'] = DefaultWeights(**config_data['default_weights'])
        if 'features' in config_data:
            config_data['features'] = FeatureConfig(**config_data['features'])
        if 'telemetry' in config_data:
            config_data['telemetry'] = TelemetryConfig(**config_data['telemetry'])
        if 'cache' in config_data:
            config_data['cache'] = CacheConfig(**config_data['cache'])
        if 'database' in config_data:
            config_data['database'] = DatabaseConfig(**config_data['database'])
        
        return cls(**config_data)


class ConfigManager:
    """
    Manages scheduler configuration with environment overrides.
    
    Loads configuration from files, environment variables, and
    provides runtime updates with validation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self._config = SchedulerConfig()
        self._config_file_path = config_path
        self._listeners = []
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file and environment."""
        # 1. Load from file if specified
        if self._config_file_path and os.path.exists(self._config_file_path):
            self._load_from_file(self._config_file_path)
        else:
            # Try default locations
            default_paths = [
                "config/scheduler.yaml",
                "config/scheduler.json",
                "scheduler.yaml",
                "scheduler.json"
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    self._load_from_file(path)
                    break
        
        # 2. Apply environment overrides
        self._apply_environment_overrides()
        
        # 3. Validate final configuration
        try:
            self._config.validate()
            logger.info("Configuration loaded and validated successfully")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def _load_from_file(self, file_path: str):
        """Load configuration from file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            self._config = SchedulerConfig.from_dict(data)
            logger.info(f"Configuration loaded from {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load configuration from {file_path}: {e}")
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        env_prefix = "SCHEDULER_"
        
        # Map environment variables to config paths
        env_mappings = {
            f"{env_prefix}ENVIRONMENT": "environment",
            f"{env_prefix}SOLVER_TIME_LIMIT": "solver.time_limit_seconds",
            f"{env_prefix}SOLVER_WORKERS": "solver.num_search_workers",
            f"{env_prefix}LEARNING_LR": "learning.completion_model_lr",
            f"{env_prefix}BANDIT_EXPLORATION": "learning.bandit_exploration_rate",
            f"{env_prefix}LOG_LEVEL": "telemetry.log_level",
            f"{env_prefix}CACHE_BACKEND": "cache.backend",
            f"{env_prefix}CACHE_TTL": "cache.ttl_minutes",
            f"{env_prefix}DB_BACKEND": "database.backend",
            f"{env_prefix}DB_CONNECTION": "database.connection_string",
            f"{env_prefix}REDIS_URL": "cache.redis_url",
            f"{env_prefix}GRANULARITY": "time_granularity_minutes",
            f"{env_prefix}MAX_HORIZON": "max_horizon_days",
            f"{env_prefix}RATE_LIMIT": "rate_limit_requests_per_minute"
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_config_value(config_path, value)
        
        # Special handling for boolean flags
        bool_mappings = {
            f"{env_prefix}METRICS_ENABLED": "telemetry.metrics_enabled",
            f"{env_prefix}TRACING_ENABLED": "telemetry.tracing_enabled",
            f"{env_prefix}CACHE_ENABLED": "cache.enabled",
            f"{env_prefix}FALLBACK_ENABLED": "enable_fallback_solver",
            f"{env_prefix}ADAPTIVE_ENABLED": "enable_adaptive_rescheduling"
        }
        
        for env_var, config_path in bool_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                bool_value = value.lower() in ('true', '1', 'yes', 'on')
                self._set_config_value(config_path, bool_value)
    
    def _set_config_value(self, path: str, value: Any):
        """Set configuration value by dot-separated path."""
        try:
            parts = path.split('.')
            obj = self._config
            
            # Navigate to parent object
            for part in parts[:-1]:
                obj = getattr(obj, part)
            
            # Get the final attribute name and current value
            attr_name = parts[-1]
            current_value = getattr(obj, attr_name)
            
            # Convert value to appropriate type
            if isinstance(current_value, bool):
                converted_value = isinstance(value, bool) and value or str(value).lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                converted_value = int(value)
            elif isinstance(current_value, float):
                converted_value = float(value)
            elif isinstance(current_value, Environment):
                converted_value = Environment(value)
            else:
                converted_value = str(value)
            
            # Set the value
            setattr(obj, attr_name, converted_value)
            logger.debug(f"Set {path} = {converted_value}")
            
        except Exception as e:
            logger.warning(f"Failed to set config value {path} = {value}: {e}")
    
    def get_config(self) -> SchedulerConfig:
        """Get current configuration."""
        return self._config
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration at runtime.
        
        Args:
            updates: Dictionary of configuration updates
        """
        try:
            # Create new config with updates
            current_dict = self._config.to_dict()
            updated_dict = self._deep_update(current_dict, updates)
            new_config = SchedulerConfig.from_dict(updated_dict)
            
            # Validate new configuration
            new_config.validate()
            
            # Apply updates
            old_config = self._config
            self._config = new_config
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    listener(old_config, new_config)
                except Exception as e:
                    logger.error(f"Config change listener failed: {e}")
            
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            raise
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively update nested dictionary."""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_update(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def add_change_listener(self, listener: Callable[[SchedulerConfig, SchedulerConfig], None]):
        """
        Add configuration change listener.
        
        Args:
            listener: Function called when configuration changes
        """
        self._listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable):
        """Remove configuration change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def export_config(self, format: str = "yaml") -> str:
        """
        Export current configuration.
        
        Args:
            format: Export format ('yaml' or 'json')
            
        Returns:
            Configuration as string
        """
        config_dict = self._config.to_dict()
        
        # Convert enum to string for serialization
        if 'environment' in config_dict:
            config_dict['environment'] = config_dict['environment'].value
        
        if format.lower() == 'yaml':
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        else:
            return json.dumps(config_dict, indent=2)
    
    def get_environment_specific_config(self) -> Dict[str, Any]:
        """Get configuration overrides for current environment."""
        env = self._config.environment
        
        overrides = {}
        
        if env == Environment.DEVELOPMENT:
            overrides.update({
                'telemetry.log_level': 'DEBUG',
                'solver.log_search_progress': True,
                'database.echo_sql': True,
                'cache.backend': 'memory'
            })
        
        elif env == Environment.TESTING:
            overrides.update({
                'telemetry.metrics_enabled': False,
                'telemetry.export_enabled': False,
                'cache.backend': 'memory',
                'database.backend': 'memory'
            })
        
        elif env == Environment.STAGING:
            overrides.update({
                'solver.time_limit_seconds': 8,
                'telemetry.export_enabled': True,
                'cache.backend': 'redis'
            })
        
        elif env == Environment.PRODUCTION:
            overrides.update({
                'telemetry.log_level': 'INFO',
                'solver.log_search_progress': False,
                'database.echo_sql': False,
                'telemetry.export_enabled': True,
                'cache.backend': 'redis'
            })
        
        return overrides


# Global configuration manager
_config_manager = None

def get_config() -> SchedulerConfig:
    """Get global scheduler configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()

def get_config_manager() -> ConfigManager:
    """Get global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def initialize_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Initialize global configuration.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configuration manager instance
    """
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager