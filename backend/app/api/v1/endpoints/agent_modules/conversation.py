"""
Conversation Management Module
Handles conversation-related operations for the agent system
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
from datetime import datetime

from app.config.database.supabase import get_supabase
from app.config.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)


async def get_user_active_conversation(user_id: str) -> Optional[str]:
    """Get user's most recent active conversation ID"""
    try:
        # First check Redis cache for quick access
        redis_client = await get_redis_client()
        cache_key = f"user_active_conversation:{user_id}"
        cached_conversation_id = await redis_client.get(cache_key)

        if cached_conversation_id:
            logger.debug(f"Found cached active conversation for user {user_id}: {cached_conversation_id}")
            # Ensure we return a string, not bytes
            if isinstance(cached_conversation_id, bytes):
                cached_conversation_id = cached_conversation_id.decode('utf-8')
            return cached_conversation_id

        # If not cached, get most recent conversation from database
        supabase = get_supabase()
        result = supabase.table("conversations").select("id").eq("user_id", user_id).eq("is_active", True).order("last_message_at", desc=True).limit(1).execute()

        if result.data and len(result.data) > 0:
            conversation_id = result.data[0]["id"]
            # Ensure conversation_id is a string
            if isinstance(conversation_id, bytes):
                conversation_id = conversation_id.decode('utf-8')
            # Cache it for 1 hour
            await redis_client.setex(cache_key, 3600, conversation_id)
            return conversation_id

        return None

    except Exception as e:
        logger.error(f"Failed to get active conversation for user {user_id}: {e}")
        return None


async def set_user_active_conversation(user_id: str, conversation_id: str) -> None:
    """Set user's active conversation ID"""
    try:
        redis_client = await get_redis_client()
        cache_key = f"user_active_conversation:{user_id}"
        # Cache for 1 hour
        await redis_client.setex(cache_key, 3600, conversation_id)
        logger.debug(f"Set active conversation for user {user_id}: {conversation_id}")

    except Exception as e:
        logger.error(f"Failed to set active conversation for user {user_id}: {e}")


