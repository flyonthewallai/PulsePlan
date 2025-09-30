"""
Agents infrastructure module - Agent infrastructure organized by domain.

This module provides organized access to all agent infrastructure functionality grouped by domain:
- core: Core infrastructure, enhanced schemas, and production integration
- performance: Connection pooling, optimization, and rate limiting  
- monitoring: Health checks and system monitoring
- security: Security validation, authentication, and threat detection
"""

# Re-export from modules for backward compatibility
from .core import *
from .performance import *
from .monitoring import *
from .security import *

__all__ = [
    # Core infrastructure
    "SchemaVersion",
    "WorkflowOperation",
    "TraceableBaseModel",
    "VersionedSchema",
    "EnhancedAgentSchema",
    "SchemaMigrator",
    "ValidationContext",
    "SchemaValidator",
    "AgentErrorHandler",
    "get_agent_error_handler",
    "AgentError",
    "ErrorContext",
    "ErrorSeverity",
    "ErrorRecoveryStrategy",
    "AgentCircuitBreaker",
    "ErrorMetricsCollector",
    "UserContextManager",
    "get_user_context_manager",
    "ContextData",
    "ContextProvider",
    "ContextCache",
    "ContextBuilder",
    "ContextValidator",
    "UserPreferencesService",
    "ProductionIntegrationManager",
    "get_production_manager",
    "IntegrationHealth",
    "IntegrationConfig",
    "ServiceDiscovery",
    "LoadBalancer",
    "CircuitBreakerService",
    "ProductionMetrics",
    
    # Performance optimization
    "ConnectionPoolManager",
    "get_connection_pool_manager",
    "PoolStats",
    "PoolConfiguration",
    "SupabaseConnectionPool",
    "AsyncPgConnectionPool",
    "PoolHealthCheck",
    "PoolMetrics",
    "ConnectionRetryManager",
    "PerformanceOptimizer",
    "get_performance_optimizer",
    "CacheStats",
    "BatchProcessor",
    "RedisCacheManager",
    "OptimizedQueryEngine",
    "PerformanceMetrics",
    "ThroughputMonitor",
    "ResourceOptimizer",
    "RateLimiter",
    "get_rate_limiter",
    "RateLimitConfig",
    "TokenBucket",
    "QuotaManager",
    "RequestThrottler",
    "RateLimitMetrics",
    "AdaptiveRateLimiting",
    "MultiTenantRateLimiting",
    
    # Monitoring
    "HealthChecker",
    "get_health_checker",
    "HealthStatus",
    "HealthCheckResult",
    "ComponentHealthCheck",
    "SystemHealthMonitor",
    "HealthMetrics",
    "HealthReporter",
    "CriticalHealthAlert",
    "MonitoringService",
    "get_monitoring_service",
    "MetricsCollector",
    "SystemMetrics",
    "PerformanceTracker",
    "AlertManager",
    "DashboardMetrics",
    "MonitoringDashboard",
    "SystemDiagnostics",
    
    # Security
    "AgentSecurityManager",
    "get_agent_security_manager",
    "ValidationResult",
    "SecurityConfig",
    "InputValidator",
    "PayloadSigner",
    "ReplayAttackPrevention",
    "SecurityMetrics",
    "ThreatDetection",
    "SecurityAuditor",
    "AgentAuthManager",
    "get_agent_auth_manager",
    "AuthenticationToken",
    "TokenValidator",
    "SessionManager",
    "PermissionChecker",
    "AccessControl",
    "SecurityPolicy",
    "AuditLogger",
]