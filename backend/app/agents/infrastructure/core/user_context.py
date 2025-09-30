"""
User Context Management System
Provides comprehensive user context for AI agents including profile, memory, and conversation history
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pydantic import BaseModel
import uuid

from app.config.cache.redis_client import get_redis_client
from app.config.database.supabase import get_supabase
from app.memory import get_vector_memory_service, get_chat_memory_service

logger = logging.getLogger(__name__)


@dataclass
class UserProfileData:
    """User profile and preferences data"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = "UTC"
    preferences: Optional[Dict[str, Any]] = None
    
    # Agent-specific context
    agent_description: Optional[str] = None
    agent_instructions: Optional[str] = None
    agent_persona: Optional[str] = None
    
    # Working preferences
    working_hours: Optional[Dict[str, Any]] = None
    study_preferences: Optional[Dict[str, Any]] = None


@dataclass
class ConversationMemory:
    """Recent conversation memory for context"""
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    turn_count: int = 0


@dataclass
class UserContextSnapshot:
    """Complete user context snapshot for AI agents"""
    profile: UserProfileData
    recent_conversations: List[ConversationMemory]
    relevant_memories: List[Dict[str, Any]]
    context_token_count: int
    generated_at: datetime
    cache_version: str


class UserContextService:
    """Service for building comprehensive user context for AI agents"""
    
    def __init__(self):
        self.redis = None
        self.supabase = None
        self.vector_service = None
        self.chat_service = None
        
    async def _ensure_services(self):
        """Lazy initialize services"""
        if not self.redis:
            self.redis = await get_redis_client()
        if not self.supabase:
            self.supabase = get_supabase()
        if not self.vector_service:
            self.vector_service = get_vector_memory_service()
        if not self.chat_service:
            self.chat_service = get_chat_memory_service()
    
    async def get_user_profile(self, user_id: str) -> UserProfileData:
        """Get comprehensive user profile data"""
        await self._ensure_services()
        
        try:
            # Get user data from users table only
            user_response = self.supabase.table("users").select("*").eq("id", user_id).execute()
            user_data = user_response.data[0] if user_response.data else {}

            # Check for agent context in user_preferences table
            agent_context = await self._get_agent_context(user_id)

            return UserProfileData(
                user_id=user_id,
                name=user_data.get("full_name") or user_data.get("name"),
                email=user_data.get("email"),
                city=user_data.get("city"),
                timezone=user_data.get("timezone", "UTC"),
                preferences=user_data.get("preferences", {}),
                agent_description=agent_context.get("description"),
                agent_instructions=agent_context.get("instructions"),
                agent_persona=agent_context.get("persona"),
                working_hours=user_data.get("working_hours"),
                study_preferences=user_data.get("study_preferences")
            )
            
        except Exception as e:
            logger.error(f"Error fetching user profile for {user_id}: {e}")
            # Return minimal profile on error
            return UserProfileData(user_id=user_id, name="User", timezone="UTC")
    
    async def _get_agent_context(self, user_id: str) -> Dict[str, Any]:
        """Get agent-specific context (description, instructions, persona)"""
        try:
            # Check user_preferences table for agent context
            prefs_response = self.supabase.table("user_preferences").select("*").eq("user_id", user_id).eq("category", "agent_context").execute()
            
            agent_context = {}
            if prefs_response.data:
                for pref in prefs_response.data:
                    key = pref.get("preference_key")
                    value = pref.get("value")
                    if key in ["description", "instructions", "persona"] and value:
                        # Extract string value from jsonb
                        agent_context[key] = value if isinstance(value, str) else value.get("value")
            
            return agent_context
            
        except Exception as e:
            logger.error(f"Error fetching agent context for {user_id}: {e}")
            return {}
    
    async def update_agent_context(
        self, 
        user_id: str, 
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        persona: Optional[str] = None
    ):
        """Update agent context preferences"""
        await self._ensure_services()
        
        try:
            updates = {}
            if description is not None:
                updates["description"] = description
            if instructions is not None:
                updates["instructions"] = instructions  
            if persona is not None:
                updates["persona"] = persona
            
            for key, value in updates.items():
                # Upsert agent context preferences
                self.supabase.table("user_preferences").upsert({
                    "user_id": user_id,
                    "category": "agent_context",
                    "preference_key": key,
                    "value": value,
                    "description": f"Agent {key} set by user",
                    "updated_at": datetime.utcnow().isoformat()
                }, on_conflict="user_id,category,preference_key").execute()
            
            # Invalidate cache
            cache_key = f"user_context:{user_id}"
            await self.redis.delete(cache_key)
            
            logger.info(f"Updated agent context for user {user_id}: {list(updates.keys())}")
            
        except Exception as e:
            logger.error(f"Error updating agent context for {user_id}: {e}")
            raise
    
    async def get_conversation_memory(self, user_id: str, session_id: str, limit: int = 20) -> ConversationMemory:
        """Get recent conversation memory for session"""
        await self._ensure_services()
        
        try:
            # Get recent messages from chat memory service
            messages = await self.chat_service.get_session_messages(user_id, session_id, limit=limit)
            
            conversation = ConversationMemory(
                session_id=session_id,
                messages=messages,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                turn_count=len(messages) // 2  # Approximate turns (user + assistant pairs)
            )
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error fetching conversation memory for {user_id}, session {session_id}: {e}")
            return ConversationMemory(
                session_id=session_id,
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    async def get_relevant_memories(
        self, 
        user_id: str, 
        query: str = "", 
        namespaces: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get relevant long-term memories using vector search"""
        await self._ensure_services()
        
        if not namespaces:
            namespaces = ["task", "doc", "email", "calendar", "course", "chat_summary"]
        
        try:
            from app.memory.types import SearchOptions
            
            search_options = SearchOptions(
                user_id=user_id,
                namespaces=namespaces,
                query=query,
                limit=limit,
                min_similarity=0.3  # Threshold for relevance
            )
            
            results = await self.vector_service.search_memory(search_options)
            
            # Format for context
            formatted_memories = []
            for result in results:
                formatted_memories.append({
                    "namespace": result.namespace,
                    "summary": result.summary,
                    "content": result.content[:500] if result.content else "",  # Truncate content
                    "metadata": result.metadata,
                    "similarity": result.similarity,
                    "created_at": result.created_at.isoformat()
                })
            
            return formatted_memories
            
        except Exception as e:
            logger.error(f"Error fetching relevant memories for {user_id}: {e}")
            return []
    
    async def build_comprehensive_context(
        self,
        user_id: str,
        session_id: str,
        current_message: str = "",
        include_memories: bool = True,
        memory_limit: int = 10,
        conversation_limit: int = 20
    ) -> UserContextSnapshot:
        """Build complete user context for AI agents"""
        await self._ensure_services()
        
        start_time = datetime.utcnow()
        
        try:
            # Build context components in parallel where possible
            profile = await self.get_user_profile(user_id)
            conversation = await self.get_conversation_memory(user_id, session_id, conversation_limit)
            
            relevant_memories = []
            if include_memories and (current_message or conversation.messages):
                # Use current message or recent conversation for memory search
                search_query = current_message
                if not search_query and conversation.messages:
                    # Use last user message
                    for msg in reversed(conversation.messages):
                        if msg.get("role") == "user":
                            search_query = msg.get("content", "")[:200]  # First 200 chars
                            break
                
                if search_query:
                    relevant_memories = await self.get_relevant_memories(
                        user_id, search_query, limit=memory_limit
                    )
            
            # Estimate token count
            context_size = self._estimate_token_count(profile, conversation, relevant_memories)
            
            # Create cache version for invalidation
            cache_version = f"{user_id}_{int(start_time.timestamp())}"
            
            context = UserContextSnapshot(
                profile=profile,
                recent_conversations=[conversation],
                relevant_memories=relevant_memories,
                context_token_count=context_size,
                generated_at=start_time,
                cache_version=cache_version
            )
            
            # Cache the context
            await self._cache_user_context(user_id, context)
            
            logger.info(f"Built user context for {user_id}: {context_size} tokens, {len(relevant_memories)} memories")
            return context
            
        except Exception as e:
            logger.error(f"Error building user context for {user_id}: {e}")
            # Return minimal context on error
            return UserContextSnapshot(
                profile=UserProfileData(user_id=user_id, name="User"),
                recent_conversations=[],
                relevant_memories=[],
                context_token_count=0,
                generated_at=start_time,
                cache_version="error"
            )
    
    def _estimate_token_count(
        self, 
        profile: UserProfileData, 
        conversation: ConversationMemory, 
        memories: List[Dict[str, Any]]
    ) -> int:
        """Estimate token count for context (rough approximation: 1 token = 4 characters)"""
        try:
            # Profile tokens
            profile_text = json.dumps(asdict(profile), default=str)
            profile_tokens = len(profile_text) // 4
            
            # Conversation tokens
            conversation_text = json.dumps([msg for msg in conversation.messages], default=str)
            conversation_tokens = len(conversation_text) // 4
            
            # Memory tokens
            memory_text = json.dumps(memories, default=str)
            memory_tokens = len(memory_text) // 4
            
            total = profile_tokens + conversation_tokens + memory_tokens
            return total
            
        except Exception as e:
            logger.error(f"Error estimating token count: {e}")
            return 1000  # Fallback estimate
    
    async def _cache_user_context(self, user_id: str, context: UserContextSnapshot):
        """Cache user context with TTL"""
        try:
            cache_key = f"user_context:{user_id}"
            cache_data = {
                "profile": asdict(context.profile),
                "recent_conversations": [asdict(conv) for conv in context.recent_conversations],
                "relevant_memories": context.relevant_memories,
                "context_token_count": context.context_token_count,
                "generated_at": context.generated_at.isoformat(),
                "cache_version": context.cache_version
            }
            
            # Cache for 10 minutes
            await self.redis.setex(cache_key, 600, json.dumps(cache_data, default=str))
            
        except Exception as e:
            logger.error(f"Error caching user context for {user_id}: {e}")
    
    async def get_cached_context(self, user_id: str) -> Optional[UserContextSnapshot]:
        """Get cached user context if available and valid"""
        await self._ensure_services()
        
        try:
            cache_key = f"user_context:{user_id}"
            cached_data = await self.redis.get(cache_key)
            
            if not cached_data:
                return None
            
            data = json.loads(cached_data)
            
            # Check if cache is still fresh (< 5 minutes old)
            generated_at = datetime.fromisoformat(data["generated_at"])
            if datetime.utcnow() - generated_at > timedelta(minutes=5):
                return None
            
            # Reconstruct context object
            profile = UserProfileData(**data["profile"])
            conversations = [ConversationMemory(
                session_id=conv["session_id"],
                messages=conv["messages"],
                created_at=datetime.fromisoformat(conv["created_at"]),
                updated_at=datetime.fromisoformat(conv["updated_at"]),
                turn_count=conv.get("turn_count", 0)
            ) for conv in data["recent_conversations"]]
            
            return UserContextSnapshot(
                profile=profile,
                recent_conversations=conversations,
                relevant_memories=data["relevant_memories"],
                context_token_count=data["context_token_count"],
                generated_at=generated_at,
                cache_version=data["cache_version"]
            )
            
        except Exception as e:
            logger.error(f"Error loading cached context for {user_id}: {e}")
            return None
    
    async def invalidate_user_context(self, user_id: str):
        """Invalidate cached user context"""
        await self._ensure_services()
        
        try:
            cache_key = f"user_context:{user_id}"
            await self.redis.delete(cache_key)
            logger.info(f"Invalidated user context cache for {user_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating context cache for {user_id}: {e}")

    def format_context_for_llm(self, context: UserContextSnapshot, include_memories: bool = True) -> str:
        """Format user context for LLM consumption"""
        
        sections = []
        
        # User Profile Section
        profile = context.profile
        profile_section = f"""USER PROFILE:
Name: {profile.name or 'User'}
Email: {profile.email or 'Not provided'}
Location: {profile.city or 'Not specified'}
Timezone: {profile.timezone}"""

        if profile.agent_description:
            profile_section += f"\nAgent Description: {profile.agent_description}"
        if profile.agent_instructions:
            profile_section += f"\nSpecial Instructions: {profile.agent_instructions}"
        if profile.agent_persona:
            profile_section += f"\nPreferred Persona: {profile.agent_persona}"
            
        if profile.working_hours:
            profile_section += f"\nWorking Hours: {json.dumps(profile.working_hours)}"
        if profile.study_preferences:
            profile_section += f"\nStudy Preferences: {json.dumps(profile.study_preferences)}"
        
        sections.append(profile_section)
        
        # Recent Conversation Section
        if context.recent_conversations and context.recent_conversations[0].messages:
            conv = context.recent_conversations[0]
            recent_messages = conv.messages[-10:]  # Last 10 messages
            
            conv_section = f"RECENT CONVERSATION (last {len(recent_messages)} messages):"
            for msg in recent_messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")[:300]  # Truncate long messages
                timestamp = msg.get("timestamp", "")
                conv_section += f"\n{role}: {content}"
                if timestamp:
                    conv_section += f" [{timestamp}]"
            
            sections.append(conv_section)
        
        # Long-term Memory Section
        if include_memories and context.relevant_memories:
            memory_section = f"RELEVANT LONG-TERM MEMORIES ({len(context.relevant_memories)} items):"
            for i, memory in enumerate(context.relevant_memories[:5], 1):  # Top 5 memories
                namespace = memory.get("namespace", "unknown").upper()
                summary = memory.get("summary", "")
                content = memory.get("content", "")[:200]  # Truncate content
                similarity = memory.get("similarity", 0)
                
                memory_section += f"\n{i}. [{namespace}] {summary}"
                if content:
                    memory_section += f" - {content}"
                memory_section += f" (relevance: {similarity:.2f})"
            
            sections.append(memory_section)
        
        # Context Stats
        stats_section = f"""CONTEXT STATS:
Generated: {context.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
Token Count: ~{context.context_token_count}
Conversation Turns: {context.recent_conversations[0].turn_count if context.recent_conversations else 0}
Memory Items: {len(context.relevant_memories)}"""
        
        sections.append(stats_section)
        
        return "\n\n".join(sections)


# Global service instance
_user_context_service: Optional[UserContextService] = None

async def get_user_context_service() -> UserContextService:
    """Get global user context service instance"""
    global _user_context_service
    
    if _user_context_service is None:
        _user_context_service = UserContextService()
    
    return _user_context_service

