"""
Production Rate Limiting with Redis
Per-user + global caps with retry-after information
"""
import asyncio
import time
import json
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    retry_after_seconds: Optional[int] = None
    remaining_requests: int = 0
    window_reset_time: Optional[datetime] = None
    limit_type: str = "user"  # "user", "global", or "service"
    current_usage: int = 0
    limit: int = 0


@dataclass  
class RateLimitConfig:
    """Rate limit configuration for a specific endpoint/service"""
    requests_per_minute: int = 10
    requests_per_hour: int = 100  
    requests_per_day: int = 1000
    burst_allowance: int = 5  # Allow short bursts above per-minute limit
    global_requests_per_minute: int = 1000  # Global cap across all users
    

class ProductionRateLimiter:
    """Production-grade rate limiting with Redis sliding windows"""
    
    def __init__(self, redis_client: redis.Redis, production_config=None):
        self.redis = redis_client
        
        # Load configuration from environment or use provided config
        if production_config:
            self.production_config = production_config
        else:
            from ...config.production_config import get_config
            self.production_config = get_config()
        
        # Build rate limit configs from environment variables
        self.configs = {
            "todo": RateLimitConfig(
                requests_per_minute=self.production_config.rate_limit.todo_requests_per_minute,
                requests_per_hour=self.production_config.rate_limit.todo_requests_per_hour,
                requests_per_day=self.production_config.rate_limit.todo_requests_per_day,
                burst_allowance=self.production_config.rate_limit.default_burst_allowance,
                global_requests_per_minute=self.production_config.rate_limit.global_requests_per_minute
            ),
            "calendar": RateLimitConfig(
                requests_per_minute=self.production_config.rate_limit.calendar_requests_per_minute,
                requests_per_hour=self.production_config.rate_limit.calendar_requests_per_hour,
                requests_per_day=self.production_config.rate_limit.calendar_requests_per_day,
                burst_allowance=self.production_config.rate_limit.default_burst_allowance,
                global_requests_per_minute=self.production_config.rate_limit.global_requests_per_minute
            ),
            "email": RateLimitConfig(
                requests_per_minute=self.production_config.rate_limit.email_requests_per_minute,
                requests_per_hour=self.production_config.rate_limit.email_requests_per_hour,
                requests_per_day=self.production_config.rate_limit.email_requests_per_day,
                burst_allowance=self.production_config.rate_limit.default_burst_allowance,
                global_requests_per_minute=self.production_config.rate_limit.global_requests_per_minute
            ),
            "llm": RateLimitConfig(
                requests_per_minute=self.production_config.rate_limit.llm_requests_per_minute,
                requests_per_hour=self.production_config.rate_limit.llm_requests_per_hour,
                requests_per_day=self.production_config.rate_limit.llm_requests_per_day,
                burst_allowance=self.production_config.rate_limit.default_burst_allowance,
                global_requests_per_minute=self.production_config.rate_limit.global_requests_per_minute
            ),
            "default": RateLimitConfig(
                requests_per_minute=self.production_config.rate_limit.default_requests_per_minute,
                requests_per_hour=self.production_config.rate_limit.default_requests_per_hour,
                requests_per_day=self.production_config.rate_limit.default_requests_per_day,
                burst_allowance=self.production_config.rate_limit.default_burst_allowance,
                global_requests_per_minute=self.production_config.rate_limit.global_requests_per_minute
            )
        }
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        workflow_type: str,
        endpoint: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check multiple rate limit windows and return comprehensive result
        """
        config = self.configs.get(workflow_type, self.configs["default"])
        now = time.time()
        
        # Check different time windows
        checks = [
            await self._check_sliding_window(
                f"user:{user_id}:{workflow_type}:minute", 
                60, config.requests_per_minute, now
            ),
            await self._check_sliding_window(
                f"user:{user_id}:{workflow_type}:hour",
                3600, config.requests_per_hour, now  
            ),
            await self._check_sliding_window(
                f"user:{user_id}:{workflow_type}:day",
                86400, config.requests_per_day, now
            ),
            await self._check_sliding_window(
                f"global:{workflow_type}:minute",
                60, config.global_requests_per_minute, now
            )
        ]
        
        # Check burst allowance (short-term spike protection)
        burst_check = await self._check_burst_limit(
            f"user:{user_id}:{workflow_type}:burst",
            config.burst_allowance, now
        )
        
        # Find the most restrictive limit
        all_checks = checks + [burst_check]
        failed_checks = [check for check in all_checks if not check.allowed]
        
        if failed_checks:
            # Return the check with the longest retry time
            most_restrictive = max(failed_checks, key=lambda x: x.retry_after_seconds or 0)
            return most_restrictive
        
        # All checks passed - record the request
        await self._record_request(user_id, workflow_type, now)
        
        # Return success with remaining quota info
        minute_check = checks[0]
        return RateLimitResult(
            allowed=True,
            remaining_requests=minute_check.remaining_requests,
            window_reset_time=minute_check.window_reset_time,
            limit_type="user",
            current_usage=minute_check.current_usage,
            limit=minute_check.limit
        )
    
    async def _check_sliding_window(
        self,
        key: str,
        window_seconds: int,
        limit: int,
        now: float
    ) -> RateLimitResult:
        """Check sliding window rate limit using Redis ZSET"""
        
        # Remove expired entries
        await self.redis.zremrangebyscore(key, 0, now - window_seconds)
        
        # Get current count
        current_count = await self.redis.zcard(key)
        
        if current_count >= limit:
            # Rate limited - calculate retry after
            oldest_entry = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest_entry:
                oldest_timestamp = oldest_entry[0][1]
                retry_after = int((oldest_timestamp + window_seconds) - now)
                retry_after = max(1, retry_after)  # At least 1 second
            else:
                retry_after = window_seconds
            
            window_reset = datetime.fromtimestamp(now + retry_after)
            
            return RateLimitResult(
                allowed=False,
                retry_after_seconds=retry_after,
                remaining_requests=0,
                window_reset_time=window_reset,
                limit_type=self._get_limit_type_from_key(key),
                current_usage=current_count,
                limit=limit
            )
        
        # Within limits
        remaining = limit - current_count
        next_reset = datetime.fromtimestamp(now + window_seconds)
        
        return RateLimitResult(
            allowed=True,
            remaining_requests=remaining,
            window_reset_time=next_reset,
            limit_type=self._get_limit_type_from_key(key),
            current_usage=current_count,
            limit=limit
        )
    
    async def _check_burst_limit(
        self,
        key: str,
        burst_limit: int,
        now: float
    ) -> RateLimitResult:
        """Check burst limit (last 10 seconds)"""
        burst_window = 10  # 10 seconds
        return await self._check_sliding_window(key, burst_window, burst_limit, now)
    
    async def _record_request(self, user_id: str, workflow_type: str, timestamp: float):
        """Record request in all relevant windows"""
        request_id = f"{timestamp}:{user_id}"
        
        keys_to_update = [
            f"user:{user_id}:{workflow_type}:minute",
            f"user:{user_id}:{workflow_type}:hour", 
            f"user:{user_id}:{workflow_type}:day",
            f"user:{user_id}:{workflow_type}:burst",
            f"global:{workflow_type}:minute"
        ]
        
        # Use pipeline for atomic updates
        pipe = self.redis.pipeline()
        
        for key in keys_to_update:
            pipe.zadd(key, {request_id: timestamp})
            
            # Set expiration based on key type
            if ":minute" in key or ":burst" in key:
                pipe.expire(key, 120)  # 2 minutes
            elif ":hour" in key:
                pipe.expire(key, 7200)  # 2 hours  
            elif ":day" in key:
                pipe.expire(key, 172800)  # 2 days
        
        await pipe.execute()
    
    def _get_limit_type_from_key(self, key: str) -> str:
        """Extract limit type from Redis key"""
        if key.startswith("global:"):
            return "global"
        elif ":burst" in key:
            return "burst"
        else:
            return "user"
    
    async def get_user_usage_stats(
        self, 
        user_id: str, 
        workflow_type: str
    ) -> Dict[str, Any]:
        """Get comprehensive usage statistics for a user"""
        config = self.configs.get(workflow_type, self.configs["default"])
        now = time.time()
        
        # Get usage across different windows
        minute_usage = await self.redis.zcount(
            f"user:{user_id}:{workflow_type}:minute", now - 60, now
        )
        hour_usage = await self.redis.zcount(
            f"user:{user_id}:{workflow_type}:hour", now - 3600, now
        )
        day_usage = await self.redis.zcount(
            f"user:{user_id}:{workflow_type}:day", now - 86400, now
        )
        
        return {
            "user_id": user_id,
            "workflow_type": workflow_type,
            "current_usage": {
                "per_minute": minute_usage,
                "per_hour": hour_usage, 
                "per_day": day_usage
            },
            "limits": {
                "per_minute": config.requests_per_minute,
                "per_hour": config.requests_per_hour,
                "per_day": config.requests_per_day
            },
            "remaining": {
                "per_minute": max(0, config.requests_per_minute - minute_usage),
                "per_hour": max(0, config.requests_per_hour - hour_usage),
                "per_day": max(0, config.requests_per_day - day_usage)
            },
            "utilization_percent": {
                "per_minute": round((minute_usage / config.requests_per_minute) * 100, 1),
                "per_hour": round((hour_usage / config.requests_per_hour) * 100, 1),
                "per_day": round((day_usage / config.requests_per_day) * 100, 1)
            }
        }
    
    async def get_global_usage_stats(self, workflow_type: str) -> Dict[str, Any]:
        """Get global usage statistics"""
        config = self.configs.get(workflow_type, self.configs["default"])
        now = time.time()
        
        global_minute_usage = await self.redis.zcount(
            f"global:{workflow_type}:minute", now - 60, now
        )
        
        return {
            "workflow_type": workflow_type,
            "global_usage_per_minute": global_minute_usage,
            "global_limit_per_minute": config.global_requests_per_minute,
            "global_remaining_per_minute": max(0, config.global_requests_per_minute - global_minute_usage),
            "global_utilization_percent": round((global_minute_usage / config.global_requests_per_minute) * 100, 1)
        }
    
    async def reset_user_limits(self, user_id: str, workflow_type: str):
        """Reset rate limits for a user (admin function)"""
        keys_to_delete = [
            f"user:{user_id}:{workflow_type}:minute",
            f"user:{user_id}:{workflow_type}:hour",
            f"user:{user_id}:{workflow_type}:day",
            f"user:{user_id}:{workflow_type}:burst"
        ]
        
        await self.redis.delete(*keys_to_delete)
        logger.info(f"Reset rate limits for user {user_id}, workflow {workflow_type}")
    
    async def update_config(self, workflow_type: str, new_config: RateLimitConfig):
        """Update rate limit configuration"""
        self.configs[workflow_type] = new_config
        logger.info(f"Updated rate limit config for {workflow_type}: {new_config}")
    
    async def get_top_users_by_usage(self, workflow_type: str, limit: int = 10) -> List[Dict]:
        """Get top users by usage (for monitoring)"""
        # This would require additional tracking in a real implementation
        # For now, return empty list as this requires more complex Redis operations
        return []
    
    async def cleanup_expired_keys(self):
        """Clean up expired rate limit keys (maintenance function)"""
        # Redis will automatically expire keys, but this can force cleanup
        # In practice, you might run this as a scheduled task
        pass


class RateLimitMiddleware:
    """Middleware to apply rate limiting to requests"""
    
    def __init__(self, rate_limiter: ProductionRateLimiter):
        self.rate_limiter = rate_limiter
    
    async def check_and_apply_rate_limit(
        self,
        user_id: str,
        workflow_type: str,
        endpoint: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check rate limit and return error response if exceeded
        Returns None if allowed, error dict if rate limited
        """
        try:
            result = await self.rate_limiter.check_rate_limit(user_id, workflow_type, endpoint)
            
            if not result.allowed:
                return {
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded for {workflow_type}",
                    "retry_after_seconds": result.retry_after_seconds,
                    "window_reset_time": result.window_reset_time.isoformat() if result.window_reset_time else None,
                    "limit_type": result.limit_type,
                    "current_usage": result.current_usage,
                    "limit": result.limit,
                    "alternatives": [
                        f"Please wait {result.retry_after_seconds} seconds before trying again",
                        "Consider upgrading your plan for higher limits",
                        "Try using a different workflow type if applicable"
                    ]
                }
            
            return None  # Request allowed
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow the request (fail open) but log the issue
            return None