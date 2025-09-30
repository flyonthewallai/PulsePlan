"""
Conversation Manager
Manages persistent conversation history and context across sessions
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.config.database.supabase import get_supabase
from app.config.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class ChatTurn(BaseModel):
    """Individual chat turn/message"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    """Conversation with persistent history"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    turns: List[ChatTurn] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    """Conversation summary for context"""
    conversation_id: str
    summary: str
    key_topics: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    turn_count: int = 0


class ConversationManager:
    """
    Manages conversation lifecycle with persistent storage and context
    """

    def __init__(self, max_turns_in_memory: int = 20, summary_after_turns: int = 30):
        self.max_turns_in_memory = max_turns_in_memory
        self.summary_after_turns = summary_after_turns

    async def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """
        Get existing conversation or create new one
        """
        try:
            if conversation_id:
                logger.debug(f"Attempting to get existing conversation {conversation_id} for user {user_id}")
                # Try to get existing conversation
                conversation = await self._get_conversation(conversation_id, user_id)
                if conversation:
                    logger.debug(f"Successfully retrieved existing conversation {conversation_id}")
                    return conversation
                else:
                    logger.debug(f"Conversation {conversation_id} not found, will create new one")

            # Create new conversation
            logger.debug(f"Creating new conversation for user {user_id}")
            conversation = Conversation(user_id=user_id)

            # Persist to database
            await self._persist_conversation(conversation)

            logger.info(f"Created new conversation {conversation.id} for user {user_id}")
            return conversation

        except Exception as e:
            logger.error(f"Failed to get/create conversation: {e}")
            # Return fallback conversation
            return Conversation(user_id=user_id)

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatTurn:
        """
        Add message to conversation
        """
        try:
            # Create chat turn
            turn = ChatTurn(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata or {}
            )

            # Persist turn to database
            await self._persist_chat_turn(turn)

            # Update conversation last_message_at
            await self._update_conversation_timestamp(conversation_id)

            # Update Redis cache with recent turns
            await self._cache_recent_turns(conversation_id, turn)

            # Generate title if this is one of the first messages
            if role == "user":
                await self._maybe_generate_title(conversation_id, user_id, content)

            # Check if we need to summarize
            await self._maybe_summarize_conversation(conversation_id)

            logger.debug(f"Added {role} message to conversation {conversation_id}")
            return turn

        except Exception as e:
            logger.error(f"Failed to add message to conversation: {e}")
            raise

    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        include_summary: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for context
        """
        try:
            # First try Redis cache for recent turns
            recent_turns = await self._get_cached_recent_turns(conversation_id)

            if len(recent_turns) >= min(limit, self.max_turns_in_memory):
                turns = recent_turns[-limit:]
            else:
                # Get from database
                turns = await self._get_turns_from_database(conversation_id, user_id, limit)

            # Convert to simple format for LLM
            history = []
            for turn in turns:
                history.append({
                    "role": turn.get("role") if isinstance(turn, dict) else turn.role,
                    "content": turn.get("content") if isinstance(turn, dict) else turn.content
                })

            # Add summary if requested and available
            if include_summary:
                summary = await self._get_conversation_summary(conversation_id)
                if summary:
                    history.insert(0, {
                        "role": "system",
                        "content": f"Conversation Summary: {summary.summary}"
                    })

            return history

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get conversation context for processing
        """
        try:
            # Get conversation from database
            conversation = await self._get_conversation(conversation_id, user_id)
            if not conversation:
                return {}

            # Get recent history
            recent_history = await self.get_conversation_history(
                conversation_id, user_id, limit=10, include_summary=False
            )

            # Get summary
            summary = await self._get_conversation_summary(conversation_id)

            return {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "context": conversation.context,
                "recent_turns": recent_history,
                "summary": summary.summary if summary else None,
                "turn_count": len(recent_history),
                "last_message_at": conversation.last_message_at.isoformat(),
                "created_at": conversation.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return {"conversation_id": conversation_id}

    async def list_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[Conversation]:
        """
        List user's conversations
        """
        try:
            supabase = get_supabase()

            query = supabase.table("conversations").select("*").eq("user_id", user_id)

            if not include_inactive:
                query = query.eq("is_active", True)

            result = query.order("last_message_at", desc=True).limit(limit).execute()

            conversations = []
            for row in result.data or []:
                conversation = self._row_to_conversation(row)
                conversations.append(conversation)

            return conversations

        except Exception as e:
            logger.error(f"Failed to list conversations for user {user_id}: {e}")
            return []

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete conversation (soft or hard delete)
        """
        try:
            supabase = get_supabase()

            if soft_delete:
                # Soft delete - mark as inactive
                supabase.table("conversations").update({
                    "is_active": False,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", conversation_id).eq("user_id", user_id).execute()
            else:
                # Hard delete - remove from database
                supabase.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()

            # Clear cache
            await self._clear_conversation_cache(conversation_id)

            logger.info(f"{'Soft' if soft_delete else 'Hard'} deleted conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False

    async def _get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get conversation from database"""
        try:
            # Ensure conversation_id is a string
            if isinstance(conversation_id, bytes):
                conversation_id = conversation_id.decode('utf-8')

            logger.debug(f"Looking up conversation {conversation_id} (type: {type(conversation_id)}) for user {user_id}")
            supabase = get_supabase()

            # Use limit(1) and check for data instead of single() which throws on no results
            result = supabase.table("conversations").select("*").eq("id", conversation_id).eq("user_id", user_id).limit(1).execute()

            logger.debug(f"Supabase query result: {result}")
            if result.data and len(result.data) > 0:
                conversation_data = result.data[0]
                logger.debug(f"Found conversation {conversation_id} in database: {conversation_data}")
                return self._row_to_conversation(conversation_data)
            else:
                logger.debug(f"No conversation found with id {conversation_id} - result.data: {result.data}")

        except Exception as e:
            logger.error(f"Exception while looking up conversation {conversation_id}: {e}")
            logger.error(f"Exception type: {type(e)}")

        return None

    async def _persist_conversation(self, conversation: Conversation) -> None:
        """Persist conversation to database"""
        try:
            supabase = get_supabase()

            conversation_data = {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "context": conversation.context,
                "is_active": conversation.is_active,
                "last_message_at": conversation.last_message_at.isoformat(),
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }

            supabase.table("conversations").insert(conversation_data).execute()

        except Exception as e:
            logger.error(f"Failed to persist conversation {conversation.id}: {e}")

    async def _persist_chat_turn(self, turn: ChatTurn) -> None:
        """Persist chat turn to database"""
        try:
            supabase = get_supabase()

            turn_data = {
                "id": turn.id,
                "conversation_id": turn.conversation_id,
                "role": turn.role,
                "content": turn.content,
                "metadata": turn.metadata,
                "timestamp": turn.timestamp.isoformat(),
                "created_at": turn.timestamp.isoformat()
            }

            supabase.table("chat_turns").insert(turn_data).execute()

        except Exception as e:
            logger.error(f"Failed to persist chat turn: {e}")

    async def _update_conversation_timestamp(self, conversation_id: str) -> None:
        """Update conversation last_message_at"""
        try:
            supabase = get_supabase()
            supabase.table("conversations").update({
                "last_message_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", conversation_id).execute()

        except Exception as e:
            logger.error(f"Failed to update conversation timestamp: {e}")

    async def _cache_recent_turns(self, conversation_id: str, new_turn: ChatTurn) -> None:
        """Cache recent turns in Redis"""
        try:
            import json
            redis_client = await get_redis_client()
            cache_key = f"conversation_turns:{conversation_id}"

            # Get existing turns
            turns_data = await redis_client.get(cache_key)
            turns = []

            if turns_data:
                turns = json.loads(turns_data)

            # Add new turn
            turns.append({
                "id": new_turn.id,
                "role": new_turn.role,
                "content": new_turn.content,
                "timestamp": new_turn.timestamp.isoformat()
            })

            # Keep only recent turns
            if len(turns) > self.max_turns_in_memory:
                turns = turns[-self.max_turns_in_memory:]

            # Cache for 24 hours
            await redis_client.setex(cache_key, 86400, json.dumps(turns))

        except Exception as e:
            logger.error(f"Failed to cache recent turns: {e}")

    async def _get_cached_recent_turns(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get recent turns from Redis cache"""
        try:
            redis_client = await get_redis_client()
            cache_key = f"conversation_turns:{conversation_id}"

            turns_data = await redis_client.get(cache_key)
            if turns_data:
                import json
                return json.loads(turns_data)

        except Exception as e:
            logger.debug(f"Failed to get cached turns: {e}")

        return []

    async def _get_turns_from_database(
        self,
        conversation_id: str,
        user_id: str,
        limit: int
    ) -> List[ChatTurn]:
        """Get turns from database"""
        try:
            supabase = get_supabase()

            # Verify user owns conversation
            conv_result = supabase.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).single().execute()
            if not conv_result.data:
                return []

            # Get turns
            result = supabase.table("chat_turns").select("*").eq("conversation_id", conversation_id).order("timestamp", desc=False).limit(limit).execute()

            turns = []
            for row in result.data or []:
                turn = ChatTurn(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    role=row["role"],
                    content=row["content"],
                    metadata=row.get("metadata", {}),
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                turns.append(turn)

            return turns

        except Exception as e:
            logger.error(f"Failed to get turns from database: {e}")
            return []

    async def _maybe_generate_title(
        self,
        conversation_id: str,
        user_id: str,
        first_message: str
    ) -> None:
        """Generate conversation title from first message"""
        try:
            # Check if conversation already has a title
            supabase = get_supabase()
            result = supabase.table("conversations").select("title").eq("id", conversation_id).single().execute()

            if result.data and result.data.get("title"):
                return  # Already has title

            # Generate title from first message
            title = self._generate_title_from_message(first_message)

            # Update conversation
            supabase.table("conversations").update({
                "title": title,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", conversation_id).execute()

        except Exception as e:
            logger.error(f"Failed to generate conversation title: {e}")

    def _generate_title_from_message(self, message: str) -> str:
        """Generate title from message content"""
        # Simple title generation - could be enhanced with LLM
        words = message.split()
        if len(words) <= 5:
            return message.capitalize()
        else:
            return " ".join(words[:5]).capitalize() + "..."

    async def _maybe_summarize_conversation(self, conversation_id: str) -> None:
        """Summarize conversation if it's getting long"""
        try:
            # Count turns
            supabase = get_supabase()
            result = supabase.table("chat_turns").select("id", count="exact").eq("conversation_id", conversation_id).execute()

            turn_count = result.count or 0

            if turn_count >= self.summary_after_turns:
                # TODO: Implement conversation summarization with LLM
                # For now, just log that summarization is needed
                logger.info(f"Conversation {conversation_id} has {turn_count} turns - summarization recommended")

        except Exception as e:
            logger.error(f"Failed to check conversation length: {e}")

    async def _get_conversation_summary(self, conversation_id: str) -> Optional[ConversationSummary]:
        """Get conversation summary if available"""
        # TODO: Implement conversation summary storage and retrieval
        return None

    async def _clear_conversation_cache(self, conversation_id: str) -> None:
        """Clear conversation cache"""
        try:
            redis_client = await get_redis_client()
            cache_key = f"conversation_turns:{conversation_id}"
            await redis_client.delete(cache_key)

        except Exception as e:
            logger.error(f"Failed to clear conversation cache: {e}")

    def _row_to_conversation(self, row: Dict[str, Any]) -> Conversation:
        """Convert database row to Conversation object"""
        return Conversation(
            id=row["id"],
            user_id=row["user_id"],
            title=row.get("title"),
            context=row.get("context", {}),
            is_active=row.get("is_active", True),
            last_message_at=datetime.fromisoformat(row["last_message_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            turns=[]  # Turns loaded separately
        )


# Global service instance
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """Get global ConversationManager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager