"""
Chat session loop that integrates ephemeral memory, persistent memory, and LLM completions.
Handles the full conversation flow with context building and memory storage.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from .chat_memory import get_chat_memory_service, ChatTurn, ChatMemoryService
from .retrieval import get_retrieval_service, RetrievalService
from .types import Namespace

logger = logging.getLogger(__name__)

class ChatLoopService:
    """Service for managing complete chat conversation loops"""
    
    def __init__(
        self,
        chat_service: Optional[ChatMemoryService] = None,
        retrieval_service: Optional[RetrievalService] = None
    ):
        self.chat_service = chat_service or get_chat_memory_service()
        self.retrieval_service = retrieval_service or get_retrieval_service()
    
    async def process_user_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        context_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the complete chat loop:
        1. Store user message in ephemeral memory
        2. Build context from recent chat + relevant memories
        3. Generate LLM response (placeholder for now)
        4. Store assistant response in ephemeral memory
        5. Return response with metadata
        """
        try:
            start_time = datetime.utcnow()
            
            # Default context configuration
            if context_config is None:
                context_config = {
                    "token_budget": 2000,
                    "include_namespaces": [
                        "task", "doc", "email", "calendar", 
                        "course", "preference", "chat_summary"
                    ]
                }
            
            # 1. Store user message in ephemeral memory
            user_turn = ChatTurn(role="user", text=message)
            await self.chat_service.push_chat_turn(user_id, session_id, user_turn)
            
            # 2. Build comprehensive context
            context = await self.retrieval_service.build_chat_context(
                user_id=user_id,
                session_id=session_id,
                user_message=message,
                token_budget=context_config.get("token_budget", 2000),
                include_namespaces=context_config.get("include_namespaces")
            )
            
            # 3. Generate LLM response (placeholder - integrate with your LLM service)
            assistant_message = await self._generate_response(
                user_message=message,
                context=context,
                user_id=user_id
            )
            
            # 4. Store assistant response in ephemeral memory
            assistant_turn = ChatTurn(role="assistant", text=assistant_message)
            await self.chat_service.push_chat_turn(user_id, session_id, assistant_turn)
            
            # 5. Collect metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response_data = {
                "message": assistant_message,
                "context_used": len(context) > 0,
                "context_length": len(context),
                "processing_time_seconds": processing_time,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processed message for user {user_id}, session {session_id} in {processing_time:.2f}s")
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to process user message: {e}")
            # Return error response
            return {
                "message": "I'm sorry, I encountered an error processing your message. Please try again.",
                "error": True,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _generate_response(
        self,
        user_message: str,
        context: str,
        user_id: str
    ) -> str:
        """
        Generate LLM response using context and user message.
        This is a placeholder - integrate with your actual LLM service.
        """
        try:
            # PLACEHOLDER IMPLEMENTATION
            # In production, replace this with actual LLM API calls
            
            system_prompt = """You are Pulse, a focused academic planning agent. 
            Use the retrieved memory context faithfully and prefer recent, due-soon tasks.
            Be concise and actionable in your responses."""
            
            # For now, return a simple response acknowledging the message
            # In production, this would call OpenAI/other LLM service
            if "schedule" in user_message.lower() or "plan" in user_message.lower():
                response = "I can help you create a study schedule. Based on your upcoming assignments and preferences, I'll suggest optimal time blocks for your work."
            elif "task" in user_message.lower() or "assignment" in user_message.lower():
                response = "I see you're asking about tasks or assignments. Let me check your current workload and deadlines to provide the most relevant information."
            elif "calendar" in user_message.lower() or "event" in user_message.lower():
                response = "I can help you with calendar-related questions. I have access to your events and can help with scheduling conflicts or time management."
            else:
                response = "I'm here to help with your academic planning. I can assist with scheduling, task management, and optimizing your study routine based on your patterns and preferences."
            
            # Add context awareness if context was used
            if context:
                response += "\n\n(I've reviewed your recent conversations and relevant information to provide this response.)"
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."
    
    async def get_session_overview(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get an overview of the current chat session"""
        try:
            # Get session stats
            session_stats = await self.chat_service.get_session_stats(user_id, session_id)
            
            # Get recent turns for analysis
            recent_turns = await self.chat_service.get_recent_turns(user_id, session_id)
            
            # Analyze conversation topics
            topics = self._analyze_conversation_topics(recent_turns)
            
            # Get context availability
            context_summary = await self.retrieval_service.get_context_summary(
                user_id, session_id
            )
            
            return {
                "session_stats": session_stats,
                "conversation_topics": topics,
                "context_availability": context_summary,
                "recent_turn_count": len(recent_turns)
            }
            
        except Exception as e:
            logger.error(f"Failed to get session overview: {e}")
            return {}
    
    async def clear_session(self, user_id: str, session_id: str) -> bool:
        """Clear the chat session"""
        try:
            await self.chat_service.clear_session(user_id, session_id)
            logger.info(f"Cleared chat session for user {user_id}, session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
    
    async def extend_session_ttl(
        self,
        user_id: str,
        session_id: str,
        additional_hours: int = 12
    ) -> bool:
        """Extend the TTL of a chat session"""
        try:
            additional_seconds = additional_hours * 3600
            await self.chat_service.extend_session_ttl(
                user_id, session_id, additional_seconds
            )
            logger.info(f"Extended session TTL for user {user_id}, session {session_id} by {additional_hours}h")
            return True
        except Exception as e:
            logger.error(f"Failed to extend session TTL: {e}")
            return False
    
    def _analyze_conversation_topics(self, turns: List[ChatTurn]) -> List[str]:
        """Simple topic analysis of conversation turns"""
        if not turns:
            return []
        
        # Simple keyword-based topic detection
        topics = set()
        topic_keywords = {
            "scheduling": ["schedule", "plan", "calendar", "time", "when"],
            "assignments": ["assignment", "homework", "due", "deadline", "task"],
            "courses": ["class", "course", "exam", "test", "quiz"],
            "productivity": ["focus", "productivity", "break", "study", "work"],
            "preferences": ["prefer", "like", "settings", "options", "config"]
        }
        
        # Combine all turn text
        all_text = " ".join([turn.text.lower() for turn in turns if turn.role == "user"])
        
        # Check for topic keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                topics.add(topic)
        
        return list(topics)
    
    async def batch_process_messages(
        self,
        user_id: str,
        session_id: str,
        messages: List[str],
        delay_between_messages: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Process multiple messages in sequence with optional delays"""
        results = []
        
        for i, message in enumerate(messages):
            try:
                result = await self.process_user_message(user_id, session_id, message)
                results.append(result)
                
                # Add delay between messages if requested
                if delay_between_messages > 0 and i < len(messages) - 1:
                    await asyncio.sleep(delay_between_messages)
                    
            except Exception as e:
                logger.error(f"Failed to process message {i+1}/{len(messages)}: {e}")
                results.append({
                    "error": True,
                    "error_message": str(e),
                    "message_index": i
                })
        
        return results

# Global chat loop service instance
chat_loop_service = ChatLoopService()

def get_chat_loop_service() -> ChatLoopService:
    """Get the global chat loop service instance"""
    return chat_loop_service