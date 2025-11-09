"""
Configuration Management System
Production-ready configuration with validation and environment support
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    """
    Application settings with validation and environment-specific defaults
    """
    
    # Application Settings
    APP_NAME: str = "PulsePlan API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # Security Configuration
    SECRET_KEY: str = Field(..., description="Application secret key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8081", "http://localhost:5173", "http://localhost:5174"]
    HMAC_SECRET_KEY: str = Field(..., description="HMAC secret for payload signing")
    
    # API Security & Input Validation
    MAX_QUERY_LENGTH: int = 10000
    MAX_PARAMETER_LENGTH: int = 5000
    ENABLE_CONTENT_FILTERING: bool = True
    ENABLE_INPUT_VALIDATION: bool = True
    ENABLE_PAYLOAD_SIGNING: bool = True
    SIGNATURE_TTL_SECONDS: int = 300
    MAX_SUSPICIOUS_ACTIVITY_COUNT: int = 5
    SUSPICIOUS_ACTIVITY_WINDOW_SECONDS: int = 300
    ALLOWED_CHARACTERS_PATTERN: str = r'^[a-zA-Z0-9\s\.\,\!\?\-\_\@\#\$\%\^\&\*\(\)\[\]\{\}\:\;\'\"\+\=\/\\\|\`\~]*$'
    
    # Database Configuration (Supabase)
    SUPABASE_URL: str = Field(..., description="Supabase URL")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service key for server-side operations")
    
    # Redis Configuration (Unified Upstash + Redis)
    REDIS_URL: Optional[str] = Field(None, description="Primary Redis URL")
    UPSTASH_REDIS_REST_URL: Optional[str] = Field(None, description="Upstash REST API URL")
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = Field(None, description="Upstash REST API token")
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_POOL_SIZE: int = 10
    REDIS_TIMEOUT: int = 5
    REDIS_SSL_CERT_REQS: str = "required"
    REDIS_SSL_CHECK_HOSTNAME: bool = True
    REDIS_SSL_CA_CERTS: Optional[str] = None
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    
    # Rate Limiting Configuration
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 20
    RATE_LIMIT_PER_HOUR: int = 200
    RATE_LIMIT_PER_DAY: int = 2000
    RATE_LIMIT_BURST_ALLOWANCE: int = 10
    GLOBAL_RATE_LIMIT_PER_MINUTE: int = 2000
    GLOBAL_RATE_LIMIT_PER_HOUR: int = 20000
    
    # Workflow-Specific Rate Limits
    TODO_RATE_LIMIT_PER_MINUTE: int = 30
    TODO_RATE_LIMIT_PER_HOUR: int = 300
    TODO_RATE_LIMIT_PER_DAY: int = 3000
    CALENDAR_RATE_LIMIT_PER_MINUTE: int = 15
    CALENDAR_RATE_LIMIT_PER_HOUR: int = 150
    CALENDAR_RATE_LIMIT_PER_DAY: int = 1000
    EMAIL_RATE_LIMIT_PER_MINUTE: int = 10
    EMAIL_RATE_LIMIT_PER_HOUR: int = 100
    EMAIL_RATE_LIMIT_PER_DAY: int = 500
    LLM_RATE_LIMIT_PER_MINUTE: int = 25
    LLM_RATE_LIMIT_PER_HOUR: int = 250
    LLM_RATE_LIMIT_PER_DAY: int = 2000
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2
    LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    DB_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    DB_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CALENDAR_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CALENDAR_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 45
    EMAIL_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    EMAIL_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 45
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    BASE_RETRY_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 60.0
    RETRY_JITTER: bool = True
    LLM_MAX_RETRIES: int = 2
    DB_MAX_RETRIES: int = 3
    EXTERNAL_SERVICE_MAX_RETRIES: int = 3
    
    # Encryption Configuration
    TOKEN_ENCRYPTION_KEY: str = Field(..., description="Main encryption key")
    ENCRYPTION_KEY_VERSION: int = 1
    USE_KMS: bool = False  # Phase 1: false, Phase 2+: true
    
    # KMS Configuration (for future phases)
    AWS_REGION: str = "us-east-1"
    KMS_KEY_ID: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # OAuth Provider Configuration
    GOOGLE_CLIENT_ID: str = Field(..., description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., description="Google OAuth client secret")
    GOOGLE_REDIRECT_URL: str = Field(..., description="Google OAuth redirect URL")
    GOOGLE_WEBHOOK_VERIFICATION_TOKEN: str = Field(..., description="Google Calendar webhook verification token")

    MICROSOFT_CLIENT_ID: str = Field(..., description="Microsoft OAuth client ID")
    MICROSOFT_CLIENT_SECRET: str = Field(..., description="Microsoft OAuth client secret")
    MICROSOFT_REDIRECT_URL: str = Field(..., description="Microsoft OAuth redirect URL")
    MICROSOFT_TENANT_ID: str = "common"

    # API Base URL for webhooks
    API_BASE_URL: str = Field(..., description="Public API base URL for webhooks")
    
    # OpenAI/LLM Configuration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.0
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TIMEOUT: int = 30
    ENABLE_LLM_CACHING: bool = False  # Disabled for fresh responses
    LLM_CACHE_TTL_SECONDS: int = 0    # No TTL since caching is disabled

    # NLU Configuration (LLM-last pipeline)
    INTENT_MODEL_PATH: Optional[str] = Field(None, description="Path to ONNX intent classifier model")
    INTENT_LABELS: List[str] = Field(
        default=[
            "scheduling", "task_management", "calendar_event", "reminder",
            "search", "email", "briefing", "status", "greeting", "thanks",
            "confirm", "cancel", "help", "adjust_plan", "unknown"
        ],
        description="Ordered list of intent labels matching model output"
    )
    HF_TOKENIZER: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace tokenizer for ONNX classifier"
    )
    USE_LLM_FALLBACK: bool = Field(
        default=False,
        description="Use LLM for ambiguous cases (optional polish)"
    )
    TZ_DEFAULT: str = Field(
        default="America/Denver",
        description="Default timezone for date/time parsing"
    )

    # Additional LLM Providers
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    
    # Search Integration
    TAVILY_API_KEY: str = Field(..., description="Tavily search API key")
    
    # RevenueCat Integration
    REVENUECAT_WEBHOOK_SECRET: str = Field(default="", description="RevenueCat webhook authorization secret")

    # PostHog Analytics Configuration
    POSTHOG_API_KEY: str = Field(default="", description="PostHog API key for analytics")
    POSTHOG_HOST: str = Field(default="https://us.i.posthog.com", description="PostHog instance host")
    POSTHOG_ENABLED: bool = Field(default=True, description="Enable/disable PostHog analytics")

    # iOS Push Notifications (APNS)
    APNS_TEAM_ID: str = Field(default="", description="Apple Push Notification service Team ID")
    APNS_KEY_ID: str = Field(default="", description="Apple Push Notification service Key ID")
    APNS_PRIVATE_KEY: str = Field(default="AVo7IxR8u5GpL1TpS9M2Q3N4R5T6Y7U8O9P0A1S2D3F4G5H6J7K8L9Z7X6C5V4B3N2M1Q2W3E4R5T6Y7U8I9O0P1A2S3D4F5G6H7J8K9L0", description="Apple Push Notification service private key")
    APNS_BUNDLE_ID: str = Field(default="", description="Apple Push Notification service Bundle ID")
    APNS_ENVIRONMENT: str = Field(default="development", description="APNS environment (development/production)")
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    HEALTH_CHECK_TIMEOUT_SECONDS: int = 5
    DB_HEALTH_TIMEOUT_SECONDS: int = 10
    REDIS_HEALTH_TIMEOUT_SECONDS: int = 5
    LLM_HEALTH_TIMEOUT_SECONDS: int = 30
    
    # Memory Management
    MEMORY_WARNING_THRESHOLD: int = 80
    MEMORY_CRITICAL_THRESHOLD: int = 90
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    ENABLE_STRUCTURED_LOGGING: bool = True
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: str = "logs/app.log"
    
    # Observability
    SENTRY_DSN: Optional[str] = None
    
    # Email Configuration
    RESEND_API_KEY: str = Field(..., description="Resend API key for email")
    RESEND_FROM_EMAIL: str = Field(..., description="From email address")
    
    # Application URLs
    APP_URL: str = "http://localhost:5000"
    CLIENT_URL: str = "http://localhost:8081"
    
    # User Rate Limiting (simplified for Phase 1)
    USER_RATE_LIMIT: int = 60  # Requests per minute per user
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True
        extra = "ignore"  # Ignore extra environment variables
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v)
        return v
    
    @validator('REDIS_URL', 'UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN')
    def validate_redis_config(cls, v, values):
        """Validate that at least one Redis configuration method is provided"""
        # This runs for each field, so we need to check the overall configuration in __post_init_post_parse__
        return v
    
    def __post_init_post_parse__(self) -> None:
        """Post-initialization validation"""
        self._validate_redis_config()
        self._validate_security_config()
        self._validate_environment_specific_config()
    
    def _validate_redis_config(self):
        """Validate Redis configuration"""
        if not self.REDIS_URL and not (self.UPSTASH_REDIS_REST_URL and self.UPSTASH_REDIS_REST_TOKEN):
            raise ValueError(
                "Redis configuration required: set REDIS_URL or both UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN"
            )
    
    def _validate_security_config(self):
        """Validate security configuration"""
        if self.ENABLE_PAYLOAD_SIGNING and not self.HMAC_SECRET_KEY:
            raise ValueError("HMAC_SECRET_KEY required when ENABLE_PAYLOAD_SIGNING is True")
    
    def _validate_environment_specific_config(self):
        """Validate environment-specific configuration requirements"""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            # Production-specific validations
            if self.DEBUG:
                logger.warning("DEBUG mode is enabled in production - this should be disabled")
            if "*" in self.ALLOWED_HOSTS:
                logger.warning("ALLOWED_HOSTS contains '*' in production - consider restricting")
        
        elif self.ENVIRONMENT == Environment.TEST:
            # Test environment can have relaxed validation
            pass
    
    def get_workflow_rate_limit_config(self, workflow_type: str) -> Dict[str, int]:
        """Get rate limit configuration for specific workflow types"""
        workflow_configs = {
            "todo": {
                "requests_per_minute": self.TODO_RATE_LIMIT_PER_MINUTE,
                "requests_per_hour": self.TODO_RATE_LIMIT_PER_HOUR,
                "requests_per_day": self.TODO_RATE_LIMIT_PER_DAY,
                "burst_allowance": self.RATE_LIMIT_BURST_ALLOWANCE,
                "global_requests_per_minute": self.GLOBAL_RATE_LIMIT_PER_MINUTE
            },
            "calendar": {
                "requests_per_minute": self.CALENDAR_RATE_LIMIT_PER_MINUTE,
                "requests_per_hour": self.CALENDAR_RATE_LIMIT_PER_HOUR,
                "requests_per_day": self.CALENDAR_RATE_LIMIT_PER_DAY,
                "burst_allowance": self.RATE_LIMIT_BURST_ALLOWANCE,
                "global_requests_per_minute": self.GLOBAL_RATE_LIMIT_PER_MINUTE
            },
            "email": {
                "requests_per_minute": self.EMAIL_RATE_LIMIT_PER_MINUTE,
                "requests_per_hour": self.EMAIL_RATE_LIMIT_PER_HOUR,
                "requests_per_day": self.EMAIL_RATE_LIMIT_PER_DAY,
                "burst_allowance": self.RATE_LIMIT_BURST_ALLOWANCE,
                "global_requests_per_minute": self.GLOBAL_RATE_LIMIT_PER_MINUTE
            },
            "llm": {
                "requests_per_minute": self.LLM_RATE_LIMIT_PER_MINUTE,
                "requests_per_hour": self.LLM_RATE_LIMIT_PER_HOUR,
                "requests_per_day": self.LLM_RATE_LIMIT_PER_DAY,
                "burst_allowance": self.RATE_LIMIT_BURST_ALLOWANCE,
                "global_requests_per_minute": self.GLOBAL_RATE_LIMIT_PER_MINUTE
            }
        }
        
        return workflow_configs.get(workflow_type, {
            "requests_per_minute": self.RATE_LIMIT_PER_MINUTE,
            "requests_per_hour": self.RATE_LIMIT_PER_HOUR,
            "requests_per_day": self.RATE_LIMIT_PER_DAY,
            "burst_allowance": self.RATE_LIMIT_BURST_ALLOWANCE,
            "global_requests_per_minute": self.GLOBAL_RATE_LIMIT_PER_MINUTE
        })
    
    def get_circuit_breaker_config(self, service_type: str) -> Dict[str, int]:
        """Get circuit breaker configuration for specific services"""
        service_configs = {
            "llm": {
                "failure_threshold": self.LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                "recovery_timeout": self.LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                "success_threshold": self.CIRCUIT_BREAKER_SUCCESS_THRESHOLD
            },
            "database": {
                "failure_threshold": self.DB_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                "recovery_timeout": self.DB_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                "success_threshold": self.CIRCUIT_BREAKER_SUCCESS_THRESHOLD
            },
            "calendar": {
                "failure_threshold": self.CALENDAR_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                "recovery_timeout": self.CALENDAR_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                "success_threshold": self.CIRCUIT_BREAKER_SUCCESS_THRESHOLD
            },
            "email": {
                "failure_threshold": self.EMAIL_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                "recovery_timeout": self.EMAIL_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                "success_threshold": self.CIRCUIT_BREAKER_SUCCESS_THRESHOLD
            }
        }
        
        return service_configs.get(service_type, {
            "failure_threshold": self.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "recovery_timeout": self.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            "success_threshold": self.CIRCUIT_BREAKER_SUCCESS_THRESHOLD
        })
    
    def get_retry_config(self, service_type: str) -> Dict[str, Union[int, float, bool]]:
        """Get retry configuration for specific services"""
        service_configs = {
            "llm": {
                "max_retries": self.LLM_MAX_RETRIES,
                "base_delay": self.BASE_RETRY_DELAY,
                "max_delay": self.MAX_RETRY_DELAY,
                "jitter": self.RETRY_JITTER
            },
            "database": {
                "max_retries": self.DB_MAX_RETRIES,
                "base_delay": self.BASE_RETRY_DELAY,
                "max_delay": self.MAX_RETRY_DELAY,
                "jitter": self.RETRY_JITTER
            },
            "external_service": {
                "max_retries": self.EXTERNAL_SERVICE_MAX_RETRIES,
                "base_delay": self.BASE_RETRY_DELAY,
                "max_delay": self.MAX_RETRY_DELAY,
                "jitter": self.RETRY_JITTER
            }
        }
        
        return service_configs.get(service_type, {
            "max_retries": self.MAX_RETRIES,
            "base_delay": self.BASE_RETRY_DELAY,
            "max_delay": self.MAX_RETRY_DELAY,
            "jitter": self.RETRY_JITTER
        })
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    def is_test(self) -> bool:
        """Check if running in test environment"""
        return self.ENVIRONMENT == Environment.TEST
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary with sensitive values masked"""
        config_dict = self.dict()
        
        # List of sensitive field patterns
        sensitive_patterns = ['key', 'secret', 'token', 'password', 'dsn']
        
        for key, value in config_dict.items():
            if any(pattern in key.lower() for pattern in sensitive_patterns):
                config_dict[key] = "***MASKED***"
            elif isinstance(value, Environment):
                config_dict[key] = value.value
        
        return config_dict


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance with caching
    """
    global _settings
    
    if _settings is None:
        _settings = Settings()
        logger.info(f"Configuration loaded for {_settings.ENVIRONMENT.value} environment")
        
        if _settings.DEBUG:
            logger.debug(f"Configuration summary: {_settings.to_safe_dict()}")
    
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings (useful for testing or config updates)
    """
    global _settings
    _settings = None
    return get_settings()


def get_legacy_settings():
    """
    Backward compatibility function to maintain existing imports
    """
    return get_settings()


# Backward compatibility exports
settings = get_settings()