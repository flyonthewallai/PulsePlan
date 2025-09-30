"""
Chat summarization service for converting ephemeral chat sessions into persistent memory.
Handles end-of-session/day summarization and storage in vector memory.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from ..core.chat_memory import get_chat_memory_service, ChatTurn, ChatMemoryService
from ..retrieval.vector_memory import get_vector_memory_service, VectorMemoryService
from ..core.types import VecMemoryCreate

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for summarizing and persisting chat sessions"""
    
    def __init__(
        self,
        chat_service: Optional[ChatMemoryService] = None,
        vector_service: Optional[VectorMemoryService] = None
    ):
        self.chat_service = chat_service or get_chat_memory_service()
        self.vector_service = vector_service or get_vector_memory_service()
    
    async def summarize_and_persist_session(
        self,
        user_id: str,
        session_id: str,
        doc_id: Optional[str] = None,
        force_summarize: bool = False,
        min_turns_threshold: int = 4
    ) -> Optional[str]:
        """
        Summarize a chat session and persist it to vector memory.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            doc_id: Custom document ID (defaults to session-based ID)
            force_summarize: Summarize even if session seems too short
            min_turns_threshold: Minimum turns required for summarization
            
        Returns:
            Memory ID of the created summary, or None if failed/skipped
        """
        try:
            # Get chat turns from the session
            turns = await self.chat_service.get_recent_turns(user_id, session_id, limit=64)
            
            if not turns:
                logger.info(f"No turns found for session {session_id}, skipping summarization")
                return None
            
            # Check if session is substantial enough to summarize
            if len(turns) < min_turns_threshold and not force_summarize:
                logger.info(f"Session {session_id} has only {len(turns)} turns, skipping summarization")
                return None
            
            # Generate transcript
            transcript = self._create_transcript(turns)
            
            # Generate summary using LLM
            summary = await self._generate_chat_summary(transcript)
            
            if not summary:
                logger.warning(f"Failed to generate summary for session {session_id}")
                return None
            
            # Generate doc_id if not provided
            if not doc_id:
                date_str = datetime.utcnow().strftime("%Y-%m-%d")
                doc_id = f"chat:{session_id}:{date_str}"
            
            # Extract key information for metadata
            metadata = self._extract_session_metadata(turns, session_id)
            
            # Create memory entry
            memory = VecMemoryCreate(
                user_id=user_id,
                namespace="chat_summary",
                doc_id=doc_id,
                chunk_id=0,
                content=transcript,
                summary=summary,
                metadata=metadata
            )
            
            # Store in vector memory
            memory_id = await self.vector_service.upsert_memory(memory)
            
            if memory_id:
                logger.info(f"Successfully summarized session {session_id} as memory {memory_id}")
                return memory_id
            else:
                logger.error(f"Failed to store summary for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to summarize session {session_id}: {e}")
            return None
    
    async def _generate_chat_summary(self, transcript: str) -> Optional[str]:
        """
        Generate a concise summary of the chat transcript using LLM.
        This is a placeholder - integrate with your actual LLM service.
        """
        try:
            # PLACEHOLDER IMPLEMENTATION
            # In production, replace with actual LLM API call
            
            instruction = """Summarize this chat into a concise academic-planning memory:
            - Key decisions made
            - Deadlines and dates mentioned
            - Commitments and preferences discussed
            - Unresolved questions / next actions (bulleted)
            Keep under 250 tokens."""
            
            # Simple rule-based summary for demonstration
            # In production, this would call OpenAI or other LLM
            summary_parts = []
            
            # Extract key topics from transcript
            if "assignment" in transcript.lower() or "homework" in transcript.lower():
                summary_parts.append("- Discussed assignments and homework management")
            
            if "schedule" in transcript.lower() or "calendar" in transcript.lower():
                summary_parts.append("- Reviewed scheduling and calendar planning")
            
            if "exam" in transcript.lower() or "test" in transcript.lower():
                summary_parts.append("- Discussed exam preparation and testing")
            
            if "due" in transcript.lower() or "deadline" in transcript.lower():
                summary_parts.append("- Reviewed upcoming deadlines")
            
            # Default summary if no specific topics detected
            if not summary_parts:
                summary_parts.append("- General academic planning discussion")
            
            # Add session info
            lines = transcript.split('\n')
            turn_count = len([line for line in lines if line.strip().startswith('[chat')])
            summary_parts.append(f"- Session included {turn_count} conversation turns")
            
            # Add timestamp
            summary_parts.append(f"- Conversation on {datetime.utcnow().strftime('%Y-%m-%d')}")
            
            summary = "Chat session summary:\n" + "\n".join(summary_parts)
            
            return summary[:500]  # Limit to reasonable length
            
        except Exception as e:
            logger.error(f"Failed to generate chat summary: {e}")
            return None
    
    def _create_transcript(self, turns: List[ChatTurn]) -> str:
        """Create a formatted transcript from chat turns"""
        lines = []
        for turn in turns:
            lines.append(f"{turn.role}: {turn.text}")
        
        return "\n".join(lines)
    
    def _extract_session_metadata(self, turns: List[ChatTurn], session_id: str) -> Dict[str, Any]:
        """Extract metadata from chat session"""
        if not turns:
            return {}
        
        # Count turns by role
        user_turns = sum(1 for turn in turns if turn.role == "user")
        assistant_turns = sum(1 for turn in turns if turn.role == "assistant")
        
        # Get time range
        timestamps = [turn.ts for turn in turns if turn.ts]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None
        
        # Simple topic detection
        all_text = " ".join([turn.text.lower() for turn in turns])
        topics = []
        
        topic_keywords = {
            "scheduling": ["schedule", "calendar", "time", "plan"],
            "assignments": ["assignment", "homework", "due", "deadline"],
            "courses": ["class", "course", "exam", "test"],
            "productivity": ["focus", "productivity", "study", "work"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                topics.append(topic)
        
        return {
            "session_id": session_id,
            "kind": "daily_chat",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total_turns": len(turns),
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "start_time": start_time,
            "end_time": end_time,
            "topics": topics,
            "duration_minutes": self._calculate_duration(start_time, end_time)
        }
    
    def _calculate_duration(self, start_time: Optional[str], end_time: Optional[str]) -> Optional[int]:
        """Calculate session duration in minutes"""
        if not start_time or not end_time:
            return None
        
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end - start
            return int(duration.total_seconds() / 60)
        except Exception:
            return None
    
    async def summarize_daily_sessions(
        self,
        user_id: str,
        date: Optional[str] = None,
        session_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Summarize all chat sessions from a specific day.
        
        Args:
            user_id: User identifier
            date: Date string (YYYY-MM-DD), defaults to today
            session_ids: Specific session IDs to summarize (optional)
            
        Returns:
            List of memory IDs for created summaries
        """
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        memory_ids = []
        
        # If specific session IDs provided, summarize those
        if session_ids:
            for session_id in session_ids:
                try:
                    memory_id = await self.summarize_and_persist_session(
                        user_id=user_id,
                        session_id=session_id,
                        doc_id=f"daily_chat:{date}:{session_id}"
                    )
                    if memory_id:
                        memory_ids.append(memory_id)
                except Exception as e:
                    logger.error(f"Failed to summarize session {session_id}: {e}")
                    continue
        
        logger.info(f"Summarized {len(memory_ids)} sessions for user {user_id} on {date}")
        return memory_ids
    
    async def get_recent_summaries(
        self,
        user_id: str,
        days_back: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent chat summaries for a user"""
        try:
            # Search for chat summaries in vector memory
            from .types import SearchOptions
            
            search_options = SearchOptions(
                user_id=user_id,
                namespaces=["chat_summary"],
                query="chat session conversation",
                limit=limit
            )
            
            summaries = await self.vector_service.search_memory(search_options)
            
            # Filter by date range
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            recent_summaries = []
            
            for summary in summaries:
                if summary.created_at >= cutoff_date:
                    recent_summaries.append({
                        "id": summary.id,
                        "doc_id": summary.doc_id,
                        "summary": summary.summary,
                        "metadata": summary.metadata,
                        "created_at": summary.created_at.isoformat(),
                        "similarity": summary.similarity
                    })
            
            return recent_summaries
            
        except Exception as e:
            logger.error(f"Failed to get recent summaries: {e}")
            return []
    
    async def delete_session_summary(
        self,
        user_id: str,
        doc_id: str
    ) -> bool:
        """Delete a specific chat session summary"""
        try:
            deleted_count = await self.vector_service.delete_memories_by_doc_id(doc_id, user_id)
            logger.info(f"Deleted {deleted_count} summary entries for doc_id {doc_id}")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete session summary {doc_id}: {e}")
            return False

# Global summarization service instance
summarization_service = SummarizationService()

def get_summarization_service() -> SummarizationService:
    """Get the global summarization service instance"""
    return summarization_service