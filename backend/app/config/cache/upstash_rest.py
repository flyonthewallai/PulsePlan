"""
Upstash REST API Client
Provides a Redis-compatible interface using Upstash REST API
"""
import httpx
import json
import logging
from typing import Any, Optional, List

logger = logging.getLogger(__name__)


class UpstashRestClient:
    """Redis-compatible client using Upstash REST API"""
    
    def __init__(self, url: str, token: str):
        self.base_url = url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def _execute(self, command: str, *args) -> Any:
        """Execute a Redis command via REST API"""
        payload = [command] + list(args)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Upstash API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Handle Upstash response format
            if "result" in result:
                return result["result"]
            elif "error" in result:
                raise Exception(f"Redis error: {result['error']}")
            else:
                return result
    
    async def ping(self) -> bool:
        """Test connection"""
        result = await self._execute("PING")
        return result == "PONG"
    
    async def get(self, key: str) -> Optional[str]:
        """Get string value"""
        result = await self._execute("GET", key)
        return result if result is not None else None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set string value with optional expiration"""
        if ex:
            result = await self._execute("SETEX", key, ex, value)
        else:
            result = await self._execute("SET", key, value)
        return result == "OK"
    
    async def delete(self, *keys: str) -> int:
        """Delete keys"""
        if not keys:
            return 0
        result = await self._execute("DEL", *keys)
        return int(result) if result is not None else 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        result = await self._execute("EXISTS", key)
        return bool(result)
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        result = await self._execute("INCR", key)
        return int(result)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        result = await self._execute("EXPIRE", key, seconds)
        return bool(result)
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        result = await self._execute("KEYS", pattern)
        return result if result is not None else []
    
    async def scan_iter(self, match: str = "*", count: int = 10):
        """Async iterator for scanning keys (simplified version for Upstash)"""
        # For simplicity, just get all keys matching the pattern
        # In production, you'd want proper cursor-based scanning
        keys = await self.keys(match)
        for key in keys:
            yield key
    
    async def close(self):
        """Close connection (no-op for REST)"""
        pass
    
    def pipeline(self):
        """Get pipeline for batch operations"""
        return UpstashRestPipeline(self)


class UpstashRestPipeline:
    """Pipeline implementation for Upstash REST"""
    
    def __init__(self, client: UpstashRestClient):
        self.client = client
        self.commands = []
    
    def zremrangebyscore(self, key: str, min_val: float, max_val: float):
        """Remove elements by score range"""
        self.commands.append(("ZREMRANGEBYSCORE", key, min_val, max_val))
        return self
    
    def zcard(self, key: str):
        """Get sorted set cardinality"""
        self.commands.append(("ZCARD", key))
        return self
    
    def zadd(self, key: str, mapping: dict):
        """Add elements to sorted set"""
        args = []
        for score, member in mapping.items():
            args.extend([score, member])
        self.commands.append(("ZADD", key, *args))
        return self
    
    def expire(self, key: str, seconds: int):
        """Set expiration"""
        self.commands.append(("EXPIRE", key, seconds))
        return self
    
    async def execute(self) -> List[Any]:
        """Execute all commands in pipeline"""
        if not self.commands:
            return []
        
        results = []
        for command, *args in self.commands:
            try:
                result = await self.client._execute(command, *args)
                results.append(result)
            except Exception as e:
                logger.error(f"Pipeline command {command} failed: {e}")
                results.append(None)
        
        self.commands.clear()
        return results