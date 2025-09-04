"""
Production Performance Optimization
Redis-based caching, batching, and connection pooling with cross-instance consistency
"""
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import logging
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class BatchRequestResult:
    """Result from batch request processing"""
    successful_results: List[Any]
    failed_requests: List[Tuple[int, str, Exception]]  # index, request, exception
    total_requests: int
    success_rate: float
    execution_time: float


class RedisLLMCache:
    """Redis-based LLM response caching with cross-instance consistency"""
    
    def __init__(self, redis_client, default_ttl: int = 1800):  # 30 minutes
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = "llm_cache"
        self.stats_key = f"{self.cache_prefix}:stats"
        
    def _build_cache_key(
        self, 
        prompt: str, 
        model: str, 
        temperature: float = 0.0,
        max_tokens: int = 1000,
        prompt_version: str = "1.0"
    ) -> str:
        """Build cache key tied to prompt version + model + parameters"""
        # Create deterministic hash of all parameters
        cache_data = {
            "prompt": prompt.strip(),
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt_version": prompt_version
        }
        
        # Create hash for consistent cache key
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()[:16]
        
        return f"{self.cache_prefix}:{cache_hash}"
    
    async def get(
        self, 
        prompt: str, 
        model: str, 
        temperature: float = 0.0,
        max_tokens: int = 1000,
        prompt_version: str = "1.0"
    ) -> Optional[Dict[str, Any]]:
        """Get cached LLM response"""
        try:
            cache_key = self._build_cache_key(prompt, model, temperature, max_tokens, prompt_version)
            
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                # Update hit stats
                await self.redis.hincrby(self.stats_key, "hits", 1)
                
                result = json.loads(cached_data)
                result["cache_hit"] = True
                result["cached_at"] = result.get("cached_at")
                
                logger.debug(f"LLM cache HIT for key: {cache_key[:20]}...")
                return result
            else:
                # Update miss stats
                await self.redis.hincrby(self.stats_key, "misses", 1)
                logger.debug(f"LLM cache MISS for key: {cache_key[:20]}...")
                return None
                
        except Exception as e:
            logger.error(f"LLM cache get error: {e}")
            return None
    
    async def set(
        self,
        prompt: str,
        model: str,
        response: Dict[str, Any],
        ttl: Optional[int] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        prompt_version: str = "1.0"
    ):
        """Cache LLM response with TTL"""
        try:
            cache_key = self._build_cache_key(prompt, model, temperature, max_tokens, prompt_version)
            ttl = ttl or self.default_ttl
            
            # Add cache metadata
            cache_data = {
                **response,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl": ttl,
                "cache_hit": False
            }
            
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            
            # Update cache size stats
            await self.redis.hincrby(self.stats_key, "size", 1)
            
            logger.debug(f"LLM response cached with TTL {ttl}s: {cache_key[:20]}...")
            
        except Exception as e:
            logger.error(f"LLM cache set error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            # Get all keys matching pattern
            keys = await self.redis.keys(f"{self.cache_prefix}:{pattern}*")
            
            if keys:
                await self.redis.delete(*keys)
                await self.redis.hincrby(self.stats_key, "evictions", len(keys))
                await self.redis.hincrby(self.stats_key, "size", -len(keys))
                
                logger.info(f"Invalidated {len(keys)} cache entries matching: {pattern}")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def get_stats(self) -> CacheStats:
        """Get cache performance statistics"""
        try:
            stats_data = await self.redis.hgetall(self.stats_key)
            return CacheStats(
                hits=int(stats_data.get("hits", 0)),
                misses=int(stats_data.get("misses", 0)),
                evictions=int(stats_data.get("evictions", 0)),
                size=int(stats_data.get("size", 0))
            )
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return CacheStats()


class BatchLLMProcessor:
    """Exception-safe batch LLM request processing"""
    
    def __init__(self, llm_client, max_concurrent: int = 5, timeout: float = 30.0):
        self.llm = llm_client
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_request(
        self, 
        index: int, 
        request: Dict[str, Any]
    ) -> Tuple[int, Any, Optional[Exception]]:
        """Process single LLM request with error isolation"""
        async with self.semaphore:
            try:
                # Add timeout to prevent hanging
                result = await asyncio.wait_for(
                    self.llm.ainvoke(request.get("prompt", "")),
                    timeout=self.timeout
                )
                return index, result, None
                
            except asyncio.TimeoutError as e:
                logger.warning(f"LLM request {index} timed out after {self.timeout}s")
                return index, None, e
            except Exception as e:
                logger.error(f"LLM request {index} failed: {e}")
                return index, None, e
    
    async def batch_process(
        self, 
        requests: List[Dict[str, Any]], 
        fail_fast: bool = False
    ) -> BatchRequestResult:
        """Process multiple LLM requests with exception safety"""
        start_time = time.time()
        
        if not requests:
            return BatchRequestResult([], [], 0, 1.0, 0.0)
        
        # Create tasks for all requests
        tasks = [
            self.process_single_request(i, request) 
            for i, request in enumerate(requests)
        ]
        
        try:
            # Execute all tasks
            if fail_fast:
                # Stop on first failure
                results = await asyncio.gather(*tasks, return_exceptions=False)
            else:
                # Continue even if some fail
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate successful and failed results
            successful_results = []
            failed_requests = []
            
            for result in results:
                if isinstance(result, Exception):
                    # Task itself failed
                    failed_requests.append((-1, "batch_error", result))
                else:
                    index, response, error = result
                    if error is None:
                        successful_results.append(response)
                    else:
                        failed_requests.append((index, requests[index], error))
            
            execution_time = time.time() - start_time
            success_rate = len(successful_results) / len(requests)
            
            logger.info(
                f"Batch processed {len(requests)} requests: "
                f"{len(successful_results)} successful, {len(failed_requests)} failed, "
                f"success rate: {success_rate:.2%}, time: {execution_time:.2f}s"
            )
            
            return BatchRequestResult(
                successful_results=successful_results,
                failed_requests=failed_requests,
                total_requests=len(requests),
                success_rate=success_rate,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Batch processing failed: {e}")
            
            return BatchRequestResult(
                successful_results=[],
                failed_requests=[(i, req, e) for i, req in enumerate(requests)],
                total_requests=len(requests),
                success_rate=0.0,
                execution_time=execution_time
            )


class UserContextCache:
    """User context caching with token versioning"""
    
    def __init__(self, redis_client, default_ttl: int = 300):  # 5 minutes
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = "user_context"
    
    def _build_context_key(self, user_id: str, token_version: Optional[str] = None) -> str:
        """Build cache key with optional token version"""
        if token_version:
            return f"{self.cache_prefix}:{user_id}:v{token_version}"
        else:
            return f"{self.cache_prefix}:{user_id}"
    
    async def get(self, user_id: str, token_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached user context"""
        try:
            cache_key = self._build_context_key(user_id, token_version)
            
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                context = json.loads(cached_data)
                context["cache_hit"] = True
                context["cached_at"] = context.get("cached_at")
                
                logger.debug(f"User context cache HIT for: {user_id}")
                return context
            else:
                logger.debug(f"User context cache MISS for: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"User context cache get error: {e}")
            return None
    
    async def set(
        self, 
        user_id: str, 
        context: Dict[str, Any], 
        token_version: Optional[str] = None,
        ttl: Optional[int] = None
    ):
        """Cache user context with optional token version"""
        try:
            cache_key = self._build_context_key(user_id, token_version)
            ttl = ttl or self.default_ttl
            
            # Add cache metadata
            cache_data = {
                **context,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl": ttl,
                "token_version": token_version,
                "cache_hit": False
            }
            
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            
            logger.debug(f"User context cached for: {user_id} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"User context cache set error: {e}")
    
    async def invalidate_user(self, user_id: str):
        """Invalidate all cached contexts for a user (all token versions)"""
        try:
            # Get all keys for this user
            pattern = f"{self.cache_prefix}:{user_id}*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} context entries for user: {user_id}")
                
        except Exception as e:
            logger.error(f"User context invalidation error: {e}")
    
    async def preload_context(
        self, 
        user_id: str, 
        context_loader: Callable,
        token_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Preload user context with cache-aside pattern"""
        
        # Try cache first
        cached_context = await self.get(user_id, token_version)
        if cached_context:
            return cached_context
        
        # Load from source
        try:
            context = await context_loader(user_id)
            
            # Cache for future requests
            await self.set(user_id, context, token_version)
            
            context["cache_hit"] = False
            return context
            
        except Exception as e:
            logger.error(f"Failed to preload context for user {user_id}: {e}")
            return {"error": f"Failed to load context: {e}", "cache_hit": False}


class DatabaseQueryCache:
    """Database query caching with write invalidation"""
    
    def __init__(self, redis_client, default_ttl: int = 600):  # 10 minutes
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = "db_query"
        
    def _build_query_key(self, query_hash: str, user_id: str = None) -> str:
        """Build cache key for database query"""
        if user_id:
            return f"{self.cache_prefix}:{user_id}:{query_hash}"
        else:
            return f"{self.cache_prefix}:global:{query_hash}"
    
    def _hash_query(self, query: str, params: Dict[str, Any] = None) -> str:
        """Create deterministic hash for query + parameters"""
        query_data = {
            "query": query.strip(),
            "params": params or {}
        }
        query_string = json.dumps(query_data, sort_keys=True)
        return hashlib.sha256(query_string.encode()).hexdigest()[:16]
    
    async def get_cached_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None,
        user_id: str = None
    ) -> Optional[Any]:
        """Get cached database query result"""
        try:
            query_hash = self._hash_query(query, params)
            cache_key = self._build_query_key(query_hash, user_id)
            
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                logger.debug(f"DB query cache HIT: {query_hash}")
                return result.get("data")
            else:
                logger.debug(f"DB query cache MISS: {query_hash}")
                return None
                
        except Exception as e:
            logger.error(f"DB query cache get error: {e}")
            return None
    
    async def cache_query_result(
        self,
        query: str,
        params: Dict[str, Any] = None,
        result: Any = None,
        user_id: str = None,
        ttl: Optional[int] = None,
        invalidation_tags: List[str] = None
    ):
        """Cache database query result with invalidation tags"""
        try:
            query_hash = self._hash_query(query, params)
            cache_key = self._build_query_key(query_hash, user_id)
            ttl = ttl or self.default_ttl
            
            cache_data = {
                "data": result,
                "cached_at": datetime.utcnow().isoformat(),
                "query_hash": query_hash,
                "user_id": user_id,
                "invalidation_tags": invalidation_tags or []
            }
            
            # Cache the result
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            
            # Add to invalidation tag sets
            if invalidation_tags:
                for tag in invalidation_tags:
                    tag_key = f"{self.cache_prefix}:tags:{tag}"
                    await self.redis.sadd(tag_key, cache_key)
                    await self.redis.expire(tag_key, ttl)
            
            logger.debug(f"DB query cached: {query_hash} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"DB query cache set error: {e}")
    
    async def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cached queries by tags (for write operations)"""
        try:
            keys_to_delete = set()
            
            # Get all cache keys associated with these tags
            for tag in tags:
                tag_key = f"{self.cache_prefix}:tags:{tag}"
                cache_keys = await self.redis.smembers(tag_key)
                keys_to_delete.update(cache_keys)
                
                # Also delete the tag set
                keys_to_delete.add(tag_key)
            
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} cached queries for tags: {tags}")
                
        except Exception as e:
            logger.error(f"DB cache invalidation error: {e}")
    
    async def invalidate_user_queries(self, user_id: str):
        """Invalidate all cached queries for a specific user"""
        try:
            pattern = f"{self.cache_prefix}:{user_id}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cached queries for user: {user_id}")
                
        except Exception as e:
            logger.error(f"User query cache invalidation error: {e}")


class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self, redis_client, llm_client, db_connection_pool=None):
        self.llm_cache = RedisLLMCache(redis_client)
        self.batch_processor = BatchLLMProcessor(llm_client)
        self.user_cache = UserContextCache(redis_client)
        self.query_cache = DatabaseQueryCache(redis_client)
        self.db_pool = db_connection_pool
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            llm_cache_stats = await self.llm_cache.get_stats()
            
            return {
                "llm_cache": {
                    "hits": llm_cache_stats.hits,
                    "misses": llm_cache_stats.misses,
                    "hit_rate": llm_cache_stats.hit_rate,
                    "size": llm_cache_stats.size
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {"error": str(e)}
    
    async def clear_all_caches(self):
        """Clear all performance caches (for testing/debugging)"""
        try:
            # This would clear all cache prefixes
            await self.llm_cache.invalidate_pattern("*")
            logger.info("All performance caches cleared")
            
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")