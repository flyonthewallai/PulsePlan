"""
Performance optimization and connection management.

This module contains performance-related components including:
- Connection pooling for database operations
- Redis-based performance optimization
- Rate limiting and throttling systems
- Performance monitoring and metrics
"""

from .connection_pooling import (
    ConnectionPoolManager,
    get_connection_pool_manager,
    PoolStats,
    PoolConfiguration,
    SupabaseConnectionPool,
    AsyncPgConnectionPool,
    PoolHealthCheck,
    PoolMetrics,
    ConnectionRetryManager
)

from .performance_optimization import (
    PerformanceOptimizer,
    get_performance_optimizer,
    CacheStats,
    BatchProcessor,
    RedisCacheManager,
    OptimizedQueryEngine,
    PerformanceMetrics,
    ThroughputMonitor,
    ResourceOptimizer
)

from .rate_limiting import (
    RateLimiter,
    get_rate_limiter,
    RateLimitConfig,
    TokenBucket,
    QuotaManager,
    RequestThrottler,
    RateLimitMetrics,
    AdaptiveRateLimiting,
    MultiTenantRateLimiting
)

__all__ = [
    # Connection pooling
    "ConnectionPoolManager",
    "get_connection_pool_manager",
    "PoolStats",
    "PoolConfiguration",
    "SupabaseConnectionPool",
    "AsyncPgConnectionPool",
    "PoolHealthCheck",
    "PoolMetrics",
    "ConnectionRetryManager",
    
    # Performance optimization
    "PerformanceOptimizer",
    "get_performance_optimizer",
    "CacheStats",
    "BatchProcessor",
    "RedisCacheManager",
    "OptimizedQueryEngine",
    "PerformanceMetrics",
    "ThroughputMonitor",
    "ResourceOptimizer",
    
    # Rate limiting
    "RateLimiter",
    "get_rate_limiter",
    "RateLimitConfig",
    "TokenBucket",
    "QuotaManager",
    "RequestThrottler",
    "RateLimitMetrics",
    "AdaptiveRateLimiting",
    "MultiTenantRateLimiting",
]


