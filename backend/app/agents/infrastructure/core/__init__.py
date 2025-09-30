"""
Core agent infrastructure components.

This module contains core infrastructure components including:
- Enhanced schemas with versioning and validation
- Agent-specific error handling
- User context management
- Production integration utilities
"""

from .enhanced_schemas import (
    SchemaVersion,
    WorkflowOperation,
    TraceableBaseModel,
    VersionedSchema,
    EnhancedAgentSchema,
    SchemaMigrator,
    ValidationContext,
    SchemaValidator
)

from .agent_error_handling import (
    AgentErrorHandler,
    get_agent_error_handler,
    AgentError,
    ErrorContext,
    ErrorSeverity,
    ErrorRecoveryStrategy,
    AgentCircuitBreaker,
    ErrorMetricsCollector
)

from .user_context import (
    UserContextManager,
    get_user_context_manager,
    ContextData,
    ContextProvider,
    ContextCache,
    ContextBuilder,
    ContextValidator,
    UserPreferencesService
)

from .production_integration import (
    ProductionIntegrationManager,
    get_production_manager,
    IntegrationHealth,
    IntegrationConfig,
    ServiceDiscovery,
    LoadBalancer,
    CircuitBreakerService,
    ProductionMetrics
)

__all__ = [
    # Enhanced schemas
    "SchemaVersion",
    "WorkflowOperation",
    "TraceableBaseModel",
    "VersionedSchema",
    "EnhancedAgentSchema",
    "SchemaMigrator",
    "ValidationContext",
    "SchemaValidator",
    
    # Agent error handling
    "AgentErrorHandler",
    "get_agent_error_handler",
    "AgentError",
    "ErrorContext",
    "ErrorSeverity",
    "ErrorRecoveryStrategy",
    "AgentCircuitBreaker",
    "ErrorMetricsCollector",
    
    # User context
    "UserContextManager",
    "get_user_context_manager",
    "ContextData",
    "ContextProvider",
    "ContextCache",
    "ContextBuilder",
    "ContextValidator",
    "UserPreferencesService",
    
    # Production integration
    "ProductionIntegrationManager",
    "get_production_manager",
    "IntegrationHealth",
    "IntegrationConfig",
    "ServiceDiscovery",
    "LoadBalancer",
    "CircuitBreakerService",
    "ProductionMetrics",
]


