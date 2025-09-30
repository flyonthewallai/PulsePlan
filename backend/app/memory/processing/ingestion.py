"""
Ingestion pipeline for converting various data sources into memory entries.
Handles normalization, briefing, and storage of content from different sources.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from ..retrieval.vector_memory import get_vector_memory_service, VectorMemoryService
from ..core.types import (
    VecMemoryCreate, Assignment, CalendarEvent, EmailThread, Document,
    UserPreference, WeeklyProfileSnapshot, Namespace
)

logger = logging.getLogger(__name__)

class IngestionService:
    """Service for ingesting data from various sources into memory"""
    
    def __init__(self, vector_service: Optional[VectorMemoryService] = None):
        self.vector_service = vector_service or get_vector_memory_service()
    
    async def ingest_assignment(self, user_id: str, assignment: Assignment) -> Optional[str]:
        """Ingest a Canvas assignment into memory"""
        try:
            # Create concise brief for the assignment
            brief = self._create_assignment_brief(assignment)
            
            # Prepare metadata
            metadata = {
                "course": assignment.course,
                "due_at": assignment.due_at,
                "effort_min": assignment.effort_min,
                "priority": assignment.priority or 1,
                "source": "canvas",
                "url": assignment.url,
                "title": assignment.title,
                "importance": min(assignment.priority or 1, 5) / 5.0 if assignment.priority else 0.2
            }
            
            # Create memory entry
            memory = VecMemoryCreate(
                user_id=user_id,
                namespace="task",
                doc_id=f"canvas:{assignment.id}",
                chunk_id=0,
                content=assignment.description,
                summary=brief,
                metadata=metadata
            )
            
            memory_id = await self.vector_service.upsert_memory(memory)
            logger.info(f"Ingested assignment {assignment.id} as memory {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to ingest assignment {assignment.id}: {e}")
            return None
    
    async def ingest_calendar_event(self, user_id: str, event: CalendarEvent) -> Optional[str]:
        """Ingest a calendar event into memory"""
        try:
            # Create event brief
            brief = self._create_event_brief(event)
            
            # Prepare metadata
            metadata = {
                "start_time": event.start_time,
                "end_time": event.end_time,
                "location": event.location,
                "source": event.calendar_source,
                "title": event.title,
                "event_type": "calendar_event"
            }
            
            # Create memory entry
            memory = VecMemoryCreate(
                user_id=user_id,
                namespace="calendar",
                doc_id=f"{event.calendar_source}:{event.id}",
                chunk_id=0,
                content=event.description,
                summary=brief,
                metadata=metadata
            )
            
            memory_id = await self.vector_service.upsert_memory(memory)
            logger.info(f"Ingested calendar event {event.id} as memory {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to ingest calendar event {event.id}: {e}")
            return None
    
    async def ingest_email_thread(self, user_id: str, thread: EmailThread) -> Optional[str]:
        """Ingest an email thread into memory"""
        try:
            # Create action-focused brief
            brief = self._create_email_brief(thread)
            
            # Prepare metadata
            metadata = {
                "participants": thread.participants,
                "message_count": len(thread.messages),
                "action_items": thread.action_items,
                "source": "email",
                "subject": thread.subject
            }
            
            # Create memory entry
            memory = VecMemoryCreate(
                user_id=user_id,
                namespace="email",
                doc_id=f"email:{thread.id}",
                chunk_id=0,
                content=self._extract_email_content(thread),
                summary=brief,
                metadata=metadata
            )
            
            memory_id = await self.vector_service.upsert_memory(memory)
            logger.info(f"Ingested email thread {thread.id} as memory {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to ingest email thread {thread.id}: {e}")
            return None
    
    async def ingest_document(self, user_id: str, document: Document) -> List[str]:
        """
        Ingest a document (PDF, Notion page, etc.) into memory.
        Chunks large documents and returns list of memory IDs.
        """
        try:
            # Chunk the document if it's too large
            chunks = self._chunk_document(document.content)
            memory_ids = []
            
            for i, chunk in enumerate(chunks):
                # Create brief for this chunk
                brief = self._create_document_brief(document, chunk, i)
                
                # Prepare metadata
                metadata = {
                    "source": document.source,
                    "course": document.course,
                    "url": document.url,
                    "title": document.title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "doc_type": "document"
                }
                
                # Create memory entry
                memory = VecMemoryCreate(
                    user_id=user_id,
                    namespace="doc",
                    doc_id=f"{document.source}:{document.id}",
                    chunk_id=i,
                    content=chunk,
                    summary=brief,
                    metadata=metadata
                )
                
                memory_id = await self.vector_service.upsert_memory(memory)
                if memory_id:
                    memory_ids.append(memory_id)
            
            logger.info(f"Ingested document {document.id} as {len(memory_ids)} chunks")
            return memory_ids
            
        except Exception as e:
            logger.error(f"Failed to ingest document {document.id}: {e}")
            return []
    
    async def ingest_weekly_snapshot(self, snapshot: WeeklyProfileSnapshot) -> Optional[str]:
        """Ingest a weekly behavior profile snapshot"""
        try:
            # Create behavioral brief
            brief = self._create_snapshot_brief(snapshot)
            
            # Prepare metadata
            metadata = {
                "week_start": snapshot.week_start,
                "on_time_rate": snapshot.on_time_rate,
                "avg_study_block_min": snapshot.avg_study_block_min,
                "preferred_start_local": snapshot.preferred_start_local,
                "preferred_days": snapshot.preferred_days,
                "total_study_minutes": snapshot.total_study_minutes,
                "tasks_completed": snapshot.tasks_completed,
                "tasks_planned": snapshot.tasks_planned,
                "source": "behavioral_analysis"
            }
            
            # Create memory entry
            memory = VecMemoryCreate(
                user_id=snapshot.user_id,
                namespace="profile_snapshot",
                doc_id=f"profile:{snapshot.week_start}",
                chunk_id=0,
                content=None,  # Brief contains all the info
                summary=brief,
                metadata=metadata
            )
            
            memory_id = await self.vector_service.upsert_memory(memory)
            logger.info(f"Ingested weekly snapshot for {snapshot.week_start} as memory {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to ingest weekly snapshot: {e}")
            return None
    
    # Helper methods for creating briefs
    
    def _create_assignment_brief(self, assignment: Assignment) -> str:
        """Create a concise brief for an assignment"""
        effort_text = f"{assignment.effort_min} minutes" if assignment.effort_min else "unknown effort"
        priority_text = f"Priority {assignment.priority}" if assignment.priority else "Priority 1"
        
        brief = (f"Assignment: {assignment.title} (Course {assignment.course}). "
                f"Due {assignment.due_at}. {effort_text}. {priority_text}. "
                f"Key details: {(assignment.description or '')[:200]}...")
        
        return brief[:300]  # Keep under 300 chars
    
    def _create_event_brief(self, event: CalendarEvent) -> str:
        """Create a brief for a calendar event"""
        location_text = f" at {event.location}" if event.location else ""
        description_text = f" - {event.description[:100]}..." if event.description else ""
        
        brief = (f"Event: {event.title} from {event.start_time} to {event.end_time}"
                f"{location_text}{description_text}")
        
        return brief[:300]
    
    def _create_email_brief(self, thread: EmailThread) -> str:
        """Create an action-focused brief for an email thread"""
        participants_text = ", ".join(thread.participants[:3])  # First 3 participants
        if len(thread.participants) > 3:
            participants_text += f" and {len(thread.participants) - 3} others"
        
        action_text = ""
        if thread.action_items:
            action_text = f" Action items: {'; '.join(thread.action_items[:2])}"
            if len(thread.action_items) > 2:
                action_text += f" and {len(thread.action_items) - 2} more"
        
        brief = (f"Email thread: {thread.subject}. Participants: {participants_text}. "
                f"{len(thread.messages)} messages.{action_text}")
        
        return brief[:300]
    
    def _create_document_brief(self, document: Document, chunk: str, chunk_index: int) -> str:
        """Create a brief for a document chunk"""
        course_text = f" (Course {document.course})" if document.course else ""
        chunk_preview = chunk[:150].replace('\n', ' ')
        
        brief = (f"Document: {document.title}{course_text}. "
                f"Chunk {chunk_index + 1}. Content: {chunk_preview}...")
        
        return brief[:300]
    
    # NOTE: _create_preference_brief removed - preferences handled by preferences_service
    
    def _create_snapshot_brief(self, snapshot: WeeklyProfileSnapshot) -> str:
        """Create a brief for a weekly behavioral snapshot"""
        brief = (f"Weekly study profile for {snapshot.week_start}: "
                f"On-time completion rate: {snapshot.on_time_rate*100:.0f}%. "
                f"Typical block length: {snapshot.avg_study_block_min} min. "
                f"Preferred start: {snapshot.preferred_start_local}. "
                f"Preferred days: {', '.join(snapshot.preferred_days)}. "
                f"Completed {snapshot.tasks_completed}/{snapshot.tasks_planned} tasks.")
        
        return brief[:300]
    
    def _extract_email_content(self, thread: EmailThread) -> str:
        """Extract and concatenate email message content"""
        content_parts = []
        for message in thread.messages:
            if isinstance(message, dict) and 'content' in message:
                content_parts.append(message['content'])
        
        return '\n\n---\n\n'.join(content_parts)
    
    def _chunk_document(self, content: str, max_tokens: int = 1000) -> List[str]:
        """
        Chunk a document into smaller pieces for embedding.
        Estimates tokens as ~4 characters per token.
        """
        max_chars = max_tokens * 4
        
        if len(content) <= max_chars:
            return [content]
        
        # Try to split on paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= max_chars:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
                else:
                    # Paragraph is too long, split by sentences
                    sentences = re.split(r'[.!?]+', paragraph)
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= max_chars:
                            current_chunk += sentence + '. '
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

# Global ingestion service instance
ingestion_service = IngestionService()

def get_ingestion_service() -> IngestionService:
    """Get the global ingestion service instance"""
    return ingestion_service