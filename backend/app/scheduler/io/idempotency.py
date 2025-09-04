"""
Idempotency handling for scheduler operations.

Ensures that repeated scheduling requests with identical parameters
return consistent results without recomputation.
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from .dto import ScheduleRequest, ScheduleResponse

logger = logging.getLogger(__name__)


class IdempotencyManager:
    """
    Manages idempotency for scheduling operations.
    
    Uses content-based hashing to detect duplicate requests and
    caches responses for a configurable time period.
    """
    
    def __init__(self, cache_ttl_minutes: int = 60):
        """
        Initialize idempotency manager.
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self.cache = {}  # In-memory cache for development
        
    def generate_effect_hash(self, request: ScheduleRequest) -> str:
        """
        Generate a hash representing the scheduling request effect.
        
        Args:
            request: Scheduling request
            
        Returns:
            Hash string uniquely identifying the request
        """
        # Build normalized request representation
        hash_input = {
            'user_id': request.user_id,
            'horizon_days': request.horizon_days,
            'dry_run': request.dry_run,
            'lock_existing': request.lock_existing,
            'options': request.options
        }
        
        # Add timestamp bucketing to allow for some temporal variation
        # Bucket requests by hour to balance idempotency with freshness
        now = datetime.now()
        time_bucket = now.replace(minute=0, second=0, microsecond=0)
        hash_input['time_bucket'] = time_bucket.isoformat()
        
        # Serialize and hash
        serialized = json.dumps(hash_input, sort_keys=True, default=str)
        hash_obj = hashlib.sha256(serialized.encode('utf-8'))
        
        return hash_obj.hexdigest()[:16]  # Use first 16 chars for brevity
    
    async def check_and_put(
        self, request: ScheduleRequest
    ) -> Tuple[bool, Optional[ScheduleResponse]]:
        """
        Check for existing response and mark request as in-progress.
        
        Args:
            request: Scheduling request
            
        Returns:
            (is_duplicate, cached_response) tuple
        """
        if request.dry_run:
            # Never cache dry runs
            return False, None
            
        effect_hash = self.generate_effect_hash(request)
        
        # Check cache
        cached_entry = self.cache.get(effect_hash)
        
        if cached_entry:
            # Check if cache entry is still valid
            cached_at = cached_entry.get('cached_at')
            if cached_at:
                cache_age = datetime.now() - cached_at
                if cache_age < timedelta(minutes=self.cache_ttl_minutes):
                    response = cached_entry.get('response')
                    if response:
                        logger.info(f"Returning cached response for hash {effect_hash}")
                        return True, response
                else:
                    # Cache expired, remove entry
                    del self.cache[effect_hash]
        
        # Mark as in-progress
        self.cache[effect_hash] = {
            'status': 'in_progress',
            'started_at': datetime.now(),
            'request': request
        }
        
        return False, None
    
    async def store_response(
        self, request: ScheduleRequest, response: ScheduleResponse
    ):
        """
        Store response in cache for future duplicate requests.
        
        Args:
            request: Original scheduling request
            response: Generated response
        """
        if request.dry_run:
            return  # Don't cache dry runs
            
        effect_hash = self.generate_effect_hash(request)
        
        # Store response in cache
        self.cache[effect_hash] = {
            'status': 'completed',
            'cached_at': datetime.now(),
            'request': request,
            'response': response
        }
        
        # Clean up old cache entries
        await self._cleanup_cache()
        
        logger.debug(f"Cached response for hash {effect_hash}")
    
    async def _cleanup_cache(self):
        """Remove expired cache entries."""
        cutoff_time = datetime.now() - timedelta(minutes=self.cache_ttl_minutes * 2)
        
        expired_keys = []
        for key, entry in self.cache.items():
            cached_at = entry.get('cached_at') or entry.get('started_at')
            if cached_at and cached_at < cutoff_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        total_entries = len(self.cache)
        completed_entries = sum(1 for entry in self.cache.values() 
                               if entry.get('status') == 'completed')
        in_progress_entries = sum(1 for entry in self.cache.values() 
                                 if entry.get('status') == 'in_progress')
        
        return {
            'total_entries': total_entries,
            'completed_entries': completed_entries,
            'in_progress_entries': in_progress_entries,
            'cache_ttl_minutes': self.cache_ttl_minutes
        }


# Global idempotency manager
_idempotency_manager = None

def get_idempotency_manager() -> IdempotencyManager:
    """Get global idempotency manager instance."""
    global _idempotency_manager
    if _idempotency_manager is None:
        _idempotency_manager = IdempotencyManager()
    return _idempotency_manager


async def check_and_put(
    request: ScheduleRequest
) -> Tuple[bool, Optional[ScheduleResponse]]:
    """
    Convenience function for idempotency check.
    
    Args:
        request: Scheduling request
        
    Returns:
        (is_duplicate, cached_response) tuple
    """
    manager = get_idempotency_manager()
    return await manager.check_and_put(request)


async def store_response(request: ScheduleRequest, response: ScheduleResponse):
    """
    Convenience function for storing response.
    
    Args:
        request: Original request
        response: Generated response
    """
    manager = get_idempotency_manager()
    await manager.store_response(request, response)


def generate_job_id(request: ScheduleRequest) -> str:
    """
    Generate a unique job ID for tracking.
    
    Args:
        request: Scheduling request
        
    Returns:
        Unique job identifier
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    effect_hash = get_idempotency_manager().generate_effect_hash(request)
    
    return f"job_{timestamp}_{effect_hash}"


class RequestDeduplicator:
    """
    Advanced request deduplication with configurable strategies.
    """
    
    def __init__(self, strategy: str = "content_hash"):
        """
        Initialize deduplicator.
        
        Args:
            strategy: Deduplication strategy ('content_hash', 'user_time', 'exact')
        """
        self.strategy = strategy
        self.pending_requests = {}  # Track in-flight requests
    
    async def should_process(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """
        Determine if request should be processed or is duplicate.
        
        Args:
            request: Scheduling request
            
        Returns:
            (should_process, duplicate_job_id) tuple
        """
        if self.strategy == "content_hash":
            return await self._check_content_hash(request)
        elif self.strategy == "user_time":
            return await self._check_user_time(request)
        elif self.strategy == "exact":
            return await self._check_exact_match(request)
        else:
            return True, None  # Default: always process
    
    async def _check_content_hash(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """Check based on content hash of significant fields."""
        # Use idempotency manager's hash function
        manager = get_idempotency_manager()
        effect_hash = manager.generate_effect_hash(request)
        
        # Check if already processing
        if effect_hash in self.pending_requests:
            existing_job = self.pending_requests[effect_hash]
            return False, existing_job.get('job_id')
        
        # Mark as processing
        job_id = generate_job_id(request)
        self.pending_requests[effect_hash] = {
            'job_id': job_id,
            'started_at': datetime.now(),
            'request': request
        }
        
        return True, job_id
    
    async def _check_user_time(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """Check based on user and time window."""
        # Group by user and hour
        time_key = datetime.now().replace(minute=0, second=0, microsecond=0)
        dedup_key = f"{request.user_id}:{time_key.isoformat()}"
        
        if dedup_key in self.pending_requests:
            existing_job = self.pending_requests[dedup_key]
            return False, existing_job.get('job_id')
        
        job_id = generate_job_id(request)
        self.pending_requests[dedup_key] = {
            'job_id': job_id,
            'started_at': datetime.now(),
            'request': request
        }
        
        return True, job_id
    
    async def _check_exact_match(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """Check for exact request match."""
        # Serialize request for exact comparison
        request_dict = request.dict()
        request_str = json.dumps(request_dict, sort_keys=True, default=str)
        request_hash = hashlib.md5(request_str.encode()).hexdigest()
        
        if request_hash in self.pending_requests:
            existing_job = self.pending_requests[request_hash]
            return False, existing_job.get('job_id')
        
        job_id = generate_job_id(request)
        self.pending_requests[request_hash] = {
            'job_id': job_id,
            'started_at': datetime.now(),
            'request': request
        }
        
        return True, job_id
    
    async def mark_completed(self, job_id: str):
        """Mark a job as completed and clean up tracking."""
        # Find and remove from pending requests
        for key, job_info in list(self.pending_requests.items()):
            if job_info.get('job_id') == job_id:
                del self.pending_requests[key]
                break
    
    async def cleanup_expired(self, max_age_minutes: int = 30):
        """Clean up expired pending requests."""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        expired_keys = []
        for key, job_info in self.pending_requests.items():
            started_at = job_info.get('started_at')
            if started_at and started_at < cutoff_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.pending_requests[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired pending requests")