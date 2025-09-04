"""
Redis-based ephemeral chat memory for session context.
Stores recent chat turns in capped lists with TTL.
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.config.redis import get_redis_client, RedisClient

logger = logging.getLogger(__name__)

# Configuration constants
MAX_TURNS = 48
TTL_SECONDS = 60 * 60 * 12  # 12 hours

class ChatTurn:
    """Represents a single chat turn"""
    def __init__(self, role: str, text: str, ts: Optional[str] = None):
        self.role = role  # "user" or "assistant"
        self.text = text
        self.ts = ts or datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "text": self.text,
            "ts": self.ts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ChatTurn":
        return cls(
            role=data["role"],
            text=data["text"],
            ts=data.get("ts")
        )

class ChatMemoryService:
    """Service for managing ephemeral chat memory in Redis"""
    
    def __init__(self):
        self.redis_client: RedisClient = get_redis_client()
    
    def _get_key(self, user_id: str, session_id: str) -> str:
        """Generate Redis key for chat context"""
        return f"chat:ctx:{user_id}:{session_id}"
    
    async def push_chat_turn(
        self, 
        user_id: str, 
        session_id: str, 
        turn: ChatTurn
    ) -> None:
        """
        Add a new chat turn to the session context.
        Maintains a capped list of recent turns.
        """
        try:
            key = self._get_key(user_id, session_id)
            turn_json = json.dumps(turn.to_dict())
            
            # Use Redis pipeline for atomic operations
            pipeline = self.redis_client.client.pipeline()
            
            # Add turn to front of list
            pipeline.lpush(key, turn_json)
            
            # Trim to maintain max size
            pipeline.ltrim(key, 0, MAX_TURNS - 1)
            
            # Set expiration
            pipeline.expire(key, TTL_SECONDS)
            
            await pipeline.execute()
            
            logger.debug(f"Pushed chat turn for user {user_id}, session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to push chat turn: {e}")
            raise
    
    async def get_recent_turns(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 32
    ) -> List[ChatTurn]:
        """
        Retrieve recent chat turns for a session.
        Returns turns in chronological order (oldest first).
        """
        try:
            key = self._get_key(user_id, session_id)
            
            # Get turns from Redis (newest first due to lpush)
            raw_turns = await self.redis_client.client.lrange(key, 0, limit - 1)
            
            if not raw_turns:
                return []
            
            # Parse JSON and create ChatTurn objects
            turns = []
            for raw_turn in reversed(raw_turns):  # Reverse to get chronological order
                try:
                    turn_data = json.loads(raw_turn)
                    turn = ChatTurn.from_dict(turn_data)
                    turns.append(turn)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse chat turn JSON: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(turns)} chat turns for user {user_id}, session {session_id}")
            return turns
            
        except Exception as e:
            logger.error(f"Failed to get recent turns: {e}")
            return []
    
    async def get_session_context(
        self, 
        user_id: str, 
        session_id: str,
        format_for_prompt: bool = True
    ) -> str:
        """
        Get formatted session context for prompt inclusion.
        Returns a string representation of recent chat history.
        """
        turns = await self.get_recent_turns(user_id, session_id)
        
        if not turns:
            return ""
        
        if format_for_prompt:
            # Format for LLM context
            lines = []
            for turn in turns:
                lines.append(f"[chat {turn.role} @ {turn.ts}] {turn.text}")
            return "\n".join(lines)
        else:
            # Return raw turn data
            return json.dumps([turn.to_dict() for turn in turns], indent=2)
    
    async def clear_session(self, user_id: str, session_id: str) -> None:
        """Clear all chat history for a session"""
        try:
            key = self._get_key(user_id, session_id)
            await self.redis_client.delete(key)
            logger.debug(f"Cleared chat session for user {user_id}, session {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            raise
    
    async def get_session_stats(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get statistics about a chat session"""
        try:
            key = self._get_key(user_id, session_id)
            
            # Get session length and TTL
            session_length = await self.redis_client.client.llen(key)
            ttl = await self.redis_client.client.ttl(key)
            
            turns = await self.get_recent_turns(user_id, session_id)
            
            user_turns = sum(1 for turn in turns if turn.role == "user")
            assistant_turns = sum(1 for turn in turns if turn.role == "assistant")
            
            return {
                "total_turns": session_length,
                "user_turns": user_turns,
                "assistant_turns": assistant_turns,
                "ttl_seconds": ttl,
                "oldest_turn_ts": turns[0].ts if turns else None,
                "newest_turn_ts": turns[-1].ts if turns else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def extend_session_ttl(
        self, 
        user_id: str, 
        session_id: str,
        additional_seconds: int = TTL_SECONDS
    ) -> None:
        """Extend the TTL of a chat session"""
        try:
            key = self._get_key(user_id, session_id)
            await self.redis_client.expire(key, additional_seconds)
            logger.debug(f"Extended TTL for session {session_id} by {additional_seconds} seconds")
        except Exception as e:
            logger.error(f"Failed to extend session TTL: {e}")
            raise
    
    async def get_session_messages(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get session messages formatted for user context system"""
        try:
            turns = await self.get_recent_turns(user_id, session_id, limit)
            
            messages = []
            for turn in turns:
                messages.append({
                    "role": turn.role,
                    "content": turn.text,
                    "timestamp": turn.ts
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []

# Global chat memory service instance
chat_memory_service = ChatMemoryService()

def get_chat_memory_service() -> ChatMemoryService:
    """Get the global chat memory service instance"""
    return chat_memory_service