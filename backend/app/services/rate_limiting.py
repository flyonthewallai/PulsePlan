"""
Hierarchical Rate Limiting Service
Provides multi-level rate limiting for users, providers, and workflows
"""
import time
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from app.config.redis import get_redis_client
from app.config.settings import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitLevel(str, Enum):
    """Rate limit hierarchy levels"""
    USER = "user"
    PROVIDER = "provider"
    WORKFLOW = "workflow"
    GLOBAL = "global"


class RateLimitScope(str, Enum):
    """Rate limit time scopes"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    level: RateLimitLevel
    scope: RateLimitScope
    limit: int
    window_seconds: int
    
    def __post_init__(self):
        """Set window_seconds based on scope if not provided"""
        if not hasattr(self, 'window_seconds') or self.window_seconds == 0:
            scope_map = {
                RateLimitScope.MINUTE: 60,
                RateLimitScope.HOUR: 3600,
                RateLimitScope.DAY: 86400
            }
            self.window_seconds = scope_map.get(self.scope, 60)


@dataclass
class RateLimitViolation:
    """Rate limit violation information"""
    level: RateLimitLevel
    identifier: str
    limit: int
    current_count: int
    window_seconds: int
    reset_time: datetime
    violation_time: datetime


@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    allowed: bool
    violations: List[RateLimitViolation]
    current_limits: Dict[str, int]
    reset_times: Dict[str, datetime]


class HierarchicalRateLimiter:
    """
    Multi-level rate limiting system
    Enforces limits at user, provider, workflow, and global levels
    """
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.key_prefix = "rate_limit"
        
        # Default rate limit configurations
        self.default_limits = {
            # User-level limits (per user)
            RateLimitLevel.USER: {
                RateLimitScope.MINUTE: RateLimit(RateLimitLevel.USER, RateLimitScope.MINUTE, 100, 60),
                RateLimitScope.HOUR: RateLimit(RateLimitLevel.USER, RateLimitScope.HOUR, 1000, 3600),
                RateLimitScope.DAY: RateLimit(RateLimitLevel.USER, RateLimitScope.DAY, 10000, 86400)
            },
            # Provider-level limits (per user per provider)
            RateLimitLevel.PROVIDER: {
                RateLimitScope.MINUTE: RateLimit(RateLimitLevel.PROVIDER, RateLimitScope.MINUTE, 30, 60),
                RateLimitScope.HOUR: RateLimit(RateLimitLevel.PROVIDER, RateLimitScope.HOUR, 300, 3600),
                RateLimitScope.DAY: RateLimit(RateLimitLevel.PROVIDER, RateLimitScope.DAY, 2000, 86400)
            },
            # Workflow-level limits (per user per workflow type)
            RateLimitLevel.WORKFLOW: {
                RateLimitScope.MINUTE: RateLimit(RateLimitLevel.WORKFLOW, RateLimitScope.MINUTE, 20, 60),
                RateLimitScope.HOUR: RateLimit(RateLimitLevel.WORKFLOW, RateLimitScope.HOUR, 100, 3600),
                RateLimitScope.DAY: RateLimit(RateLimitLevel.WORKFLOW, RateLimitScope.DAY, 500, 86400)
            },
            # Global limits (across all users)
            RateLimitLevel.GLOBAL: {
                RateLimitScope.MINUTE: RateLimit(RateLimitLevel.GLOBAL, RateLimitScope.MINUTE, 1000, 60),
                RateLimitScope.HOUR: RateLimit(RateLimitLevel.GLOBAL, RateLimitScope.HOUR, 10000, 3600),
                RateLimitScope.DAY: RateLimit(RateLimitLevel.GLOBAL, RateLimitScope.DAY, 100000, 86400)
            }
        }
        
        # Custom limits can override defaults
        self.custom_limits: Dict[str, Dict[RateLimitScope, RateLimit]] = {}
    
    def _get_redis_key(self, level: RateLimitLevel, identifier: str, scope: RateLimitScope) -> str:
        """Generate Redis key for rate limiting"""
        timestamp = int(time.time())
        window_start = timestamp - (timestamp % self._get_scope_seconds(scope))
        return f"{self.key_prefix}:{level.value}:{identifier}:{scope.value}:{window_start}"
    
    def _get_scope_seconds(self, scope: RateLimitScope) -> int:
        """Get seconds for scope"""
        scope_map = {
            RateLimitScope.MINUTE: 60,
            RateLimitScope.HOUR: 3600,
            RateLimitScope.DAY: 86400
        }
        return scope_map.get(scope, 60)
    
    def _get_rate_limit(self, level: RateLimitLevel, identifier: str, scope: RateLimitScope) -> RateLimit:
        """Get rate limit for specific level and scope"""
        # Check for custom limits first
        if identifier in self.custom_limits and scope in self.custom_limits[identifier]:
            return self.custom_limits[identifier][scope]
        
        # Use default limits
        return self.default_limits[level][scope]
    
    async def _check_single_limit(
        self, 
        level: RateLimitLevel, 
        identifier: str, 
        scope: RateLimitScope
    ) -> Tuple[bool, Optional[RateLimitViolation]]:
        """Check a single rate limit"""
        rate_limit = self._get_rate_limit(level, identifier, scope)
        redis_key = self._get_redis_key(level, identifier, scope)
        
        try:
            # Get current count
            current_count = await self.redis_client.get(redis_key)
            current_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            if current_count >= rate_limit.limit:
                # Calculate reset time
                timestamp = int(time.time())
                window_start = timestamp - (timestamp % rate_limit.window_seconds)
                reset_time = datetime.fromtimestamp(window_start + rate_limit.window_seconds)
                
                violation = RateLimitViolation(
                    level=level,
                    identifier=identifier,
                    limit=rate_limit.limit,
                    current_count=current_count,
                    window_seconds=rate_limit.window_seconds,
                    reset_time=reset_time,
                    violation_time=datetime.utcnow()
                )
                
                return False, violation
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking rate limit {redis_key}: {str(e)}")
            # On Redis error, allow the request but log the issue
            return True, None
    
    async def _increment_counter(self, level: RateLimitLevel, identifier: str, scope: RateLimitScope):
        """Increment counter for rate limit"""
        rate_limit = self._get_rate_limit(level, identifier, scope)
        redis_key = self._get_redis_key(level, identifier, scope)
        
        try:
            # Increment counter and set expiry
            pipe = self.redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, rate_limit.window_seconds)
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Error incrementing rate limit counter {redis_key}: {str(e)}")
    
    async def check_rate_limits(
        self, 
        user_id: str, 
        provider: Optional[str] = None,
        workflow_type: Optional[str] = None
    ) -> RateLimitStatus:
        """
        Check all applicable rate limits
        
        Args:
            user_id: User identifier
            provider: Provider name (google, microsoft, etc.)
            workflow_type: Type of workflow being executed
            
        Returns:
            RateLimitStatus with violation information
        """
        violations = []
        current_limits = {}
        reset_times = {}
        
        # Define checks to perform
        checks = [
            # User-level limits
            (RateLimitLevel.USER, user_id, RateLimitScope.MINUTE),
            (RateLimitLevel.USER, user_id, RateLimitScope.HOUR),
            (RateLimitLevel.USER, user_id, RateLimitScope.DAY),
            
            # Global limits
            (RateLimitLevel.GLOBAL, "all", RateLimitScope.MINUTE),
            (RateLimitLevel.GLOBAL, "all", RateLimitScope.HOUR),
            (RateLimitLevel.GLOBAL, "all", RateLimitScope.DAY)
        ]
        
        # Add provider-specific checks if provider specified
        if provider:
            provider_id = f"{user_id}:{provider}"
            checks.extend([
                (RateLimitLevel.PROVIDER, provider_id, RateLimitScope.MINUTE),
                (RateLimitLevel.PROVIDER, provider_id, RateLimitScope.HOUR),
                (RateLimitLevel.PROVIDER, provider_id, RateLimitScope.DAY)
            ])
        
        # Add workflow-specific checks if workflow_type specified
        if workflow_type:
            workflow_id = f"{user_id}:{workflow_type}"
            checks.extend([
                (RateLimitLevel.WORKFLOW, workflow_id, RateLimitScope.MINUTE),
                (RateLimitLevel.WORKFLOW, workflow_id, RateLimitScope.HOUR),
                (RateLimitLevel.WORKFLOW, workflow_id, RateLimitScope.DAY)
            ])
        
        # Perform all checks
        for level, identifier, scope in checks:
            allowed, violation = await self._check_single_limit(level, identifier, scope)
            
            if not allowed and violation:
                violations.append(violation)
            
            # Store current limit info
            rate_limit = self._get_rate_limit(level, identifier, scope)
            limit_key = f"{level.value}:{scope.value}"
            current_limits[limit_key] = rate_limit.limit
            
            if violation:
                reset_times[limit_key] = violation.reset_time
        
        return RateLimitStatus(
            allowed=len(violations) == 0,
            violations=violations,
            current_limits=current_limits,
            reset_times=reset_times
        )
    
    async def record_request(
        self, 
        user_id: str, 
        provider: Optional[str] = None,
        workflow_type: Optional[str] = None
    ):
        """
        Record a request by incrementing all applicable counters
        Only call this after checking rate limits and confirming the request is allowed
        """
        # Increment user counters
        for scope in [RateLimitScope.MINUTE, RateLimitScope.HOUR, RateLimitScope.DAY]:
            await self._increment_counter(RateLimitLevel.USER, user_id, scope)
        
        # Increment global counters
        for scope in [RateLimitScope.MINUTE, RateLimitScope.HOUR, RateLimitScope.DAY]:
            await self._increment_counter(RateLimitLevel.GLOBAL, "all", scope)
        
        # Increment provider counters if applicable
        if provider:
            provider_id = f"{user_id}:{provider}"
            for scope in [RateLimitScope.MINUTE, RateLimitScope.HOUR, RateLimitScope.DAY]:
                await self._increment_counter(RateLimitLevel.PROVIDER, provider_id, scope)
        
        # Increment workflow counters if applicable
        if workflow_type:
            workflow_id = f"{user_id}:{workflow_type}"
            for scope in [RateLimitScope.MINUTE, RateLimitScope.HOUR, RateLimitScope.DAY]:
                await self._increment_counter(RateLimitLevel.WORKFLOW, workflow_id, scope)
    
    async def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Get current rate limit status for a user"""
        status = await self.check_rate_limits(user_id)
        
        return {
            "user_id": user_id,
            "allowed": status.allowed,
            "violations": [asdict(v) for v in status.violations],
            "current_limits": status.current_limits,
            "reset_times": {k: v.isoformat() for k, v in status.reset_times.items()}
        }
    
    def set_custom_limit(
        self, 
        identifier: str, 
        level: RateLimitLevel, 
        scope: RateLimitScope, 
        limit: int
    ):
        """Set custom rate limit for specific identifier"""
        if identifier not in self.custom_limits:
            self.custom_limits[identifier] = {}
        
        window_seconds = self._get_scope_seconds(scope)
        self.custom_limits[identifier][scope] = RateLimit(
            level=level,
            scope=scope,
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def reset_user_limits(self, user_id: str):
        """Reset all rate limits for a user"""
        try:
            # Get all keys for the user
            patterns = [
                f"{self.key_prefix}:user:{user_id}:*",
                f"{self.key_prefix}:provider:{user_id}:*:*",
                f"{self.key_prefix}:workflow:{user_id}:*:*"
            ]
            
            keys_to_delete = []
            for pattern in patterns:
                keys = await self.redis_client.keys(pattern)
                keys_to_delete.extend(keys)
            
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
                logger.info(f"Reset {len(keys_to_delete)} rate limit keys for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error resetting rate limits for user {user_id}: {str(e)}")
    
    async def get_global_metrics(self) -> Dict[str, Any]:
        """Get global rate limiting metrics"""
        try:
            current_time = int(time.time())
            metrics = {
                "current_usage": {},
                "limits": {},
                "active_windows": 0
            }
            
            # Get global usage across all scopes
            for scope in [RateLimitScope.MINUTE, RateLimitScope.HOUR, RateLimitScope.DAY]:
                redis_key = self._get_redis_key(RateLimitLevel.GLOBAL, "all", scope)
                current_count = await self.redis_client.get(redis_key)
                current_count = int(current_count) if current_count else 0
                
                rate_limit = self.default_limits[RateLimitLevel.GLOBAL][scope]
                
                metrics["current_usage"][scope.value] = current_count
                metrics["limits"][scope.value] = rate_limit.limit
            
            # Count active rate limit keys
            all_keys = await self.redis_client.keys(f"{self.key_prefix}:*")
            metrics["active_windows"] = len(all_keys)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting global rate limit metrics: {str(e)}")
            return {"error": str(e)}


# Global rate limiter instance
hierarchical_rate_limiter = HierarchicalRateLimiter()