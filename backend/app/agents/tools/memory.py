"""
Memory management tool for PulsePlan agents.
Provides comprehensive access to the semantic memory system and chat context.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base import BaseTool, ToolResult, ToolError
from app.memory import (
    get_vector_memory_service,
    get_chat_memory_service,
    get_retrieval_service,
    get_ingestion_service,
    get_summarization_service,
    get_weekly_profile_service
)
from app.memory.types import (
    SearchOptions, VecMemoryCreate, Namespace,
    Assignment, CalendarEvent, EmailThread, Document
)

logger = logging.getLogger(__name__)

class MemoryTool(BaseTool):
    """
    Comprehensive memory management tool for PulsePlan agents.
    
    This tool provides agents with the ability to:
    1. Search for relevant information across all memory namespaces
    2. Store new information from conversations or data sources
    3. Retrieve context for chat sessions
    4. Analyze user behavior patterns
    5. Summarize and persist conversations
    """
    
    def __init__(self):
        super().__init__(
            name="memory",
            description="Access and manage user memory including semantic search, context retrieval, and behavior analysis"
        )
        
        # Initialize memory services
        self.vector_service = get_vector_memory_service()
        self.chat_service = get_chat_memory_service()
        self.retrieval_service = get_retrieval_service()
        self.ingestion_service = get_ingestion_service()
        self.summarization_service = get_summarization_service()
        self.profile_service = get_weekly_profile_service()
    
    def get_required_tokens(self) -> List[str]:
        """No OAuth tokens required - uses internal memory system"""
        return []
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for memory operations"""
        operation = input_data.get("operation")
        
        if not operation:
            return False
        
        valid_operations = {
            "search_memory", "store_memory", "get_context", 
            "analyze_behavior", "summarize_session", "ingest_data",
            "list_memories", "get_memory_stats", "search_similar"
        }
        
        return operation in valid_operations
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute memory operation based on input"""
        start_time = datetime.utcnow()
        
        try:
            operation = input_data.get("operation")
            user_id = context.get("user_id")
            
            if not user_id:
                raise ToolError("User ID required in context", self.name)
            
            # Route to appropriate operation
            if operation == "search_memory":
                result = await self._search_memory(input_data, user_id)
            elif operation == "store_memory":
                result = await self._store_memory(input_data, user_id)
            elif operation == "get_context":
                result = await self._get_context(input_data, user_id)
            elif operation == "analyze_behavior":
                result = await self._analyze_behavior(input_data, user_id)
            elif operation == "summarize_session":
                result = await self._summarize_session(input_data, user_id)
            elif operation == "ingest_data":
                result = await self._ingest_data(input_data, user_id)
            elif operation == "list_memories":
                result = await self._list_memories(input_data, user_id)
            elif operation == "get_memory_stats":
                result = await self._get_memory_stats(input_data, user_id)
            elif operation == "search_similar":
                result = await self._search_similar(input_data, user_id)
            else:
                raise ToolError(f"Unknown operation: {operation}", self.name)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            tool_result = ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": user_id
                }
            )
            
            self.log_execution(input_data, tool_result, context)
            return tool_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Memory tool execution failed: {e}")
            
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": context.get("user_id")
                }
            )
    
    async def _search_memory(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Search across memory namespaces for relevant information"""
        query = input_data.get("query", "")
        namespaces = input_data.get("namespaces", ["task", "doc", "email", "calendar", "course"])
        limit = input_data.get("limit", 20)
        course_filter = input_data.get("course")
        due_start = input_data.get("due_start")
        due_end = input_data.get("due_end")
        min_similarity = input_data.get("min_similarity", 0.0)
        
        if not query:
            raise ToolError("Query is required for memory search", self.name)
        
        # Validate namespaces (removed "preference" - use preferences tool instead)
        valid_namespaces = {
            "task", "doc", "email", "calendar", "course", 
            "chat_summary", "profile_snapshot", "web"
        }
        namespaces = [ns for ns in namespaces if ns in valid_namespaces]
        
        search_options = SearchOptions(
            user_id=user_id,
            namespaces=namespaces,
            query=query,
            limit=limit,
            course=course_filter,
            due_start=due_start,
            due_end=due_end,
            min_similarity=min_similarity
        )
        
        results = await self.vector_service.search_memory(search_options)
        
        # Format results for agent consumption
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "namespace": result.namespace,
                "doc_id": result.doc_id,
                "summary": result.summary,
                "content": result.content,
                "metadata": result.metadata,
                "similarity": result.similarity,
                "urgency": result.urgency,
                "final_score": result.final_score,
                "created_at": result.created_at.isoformat(),
                "updated_at": result.updated_at.isoformat()
            })
        
        return {
            "results": formatted_results,
            "query": query,
            "namespaces_searched": namespaces,
            "total_results": len(formatted_results)
        }
    
    async def _store_memory(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Store new memory entry"""
        namespace = input_data.get("namespace", "doc")
        doc_id = input_data.get("doc_id")
        content = input_data.get("content")
        summary = input_data.get("summary")
        metadata = input_data.get("metadata", {})
        chunk_id = input_data.get("chunk_id", 0)
        
        if not doc_id:
            raise ToolError("doc_id is required for storing memory", self.name)
        
        if not (content or summary):
            raise ToolError("Either content or summary is required", self.name)
        
        memory = VecMemoryCreate(
            user_id=user_id,
            namespace=namespace,
            doc_id=doc_id,
            chunk_id=chunk_id,
            content=content,
            summary=summary,
            metadata=metadata
        )
        
        memory_id = await self.vector_service.upsert_memory(memory)
        
        if not memory_id:
            raise ToolError("Failed to store memory", self.name)
        
        return {
            "memory_id": memory_id,
            "doc_id": doc_id,
            "namespace": namespace,
            "stored_at": datetime.utcnow().isoformat()
        }
    
    async def _get_context(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get chat context with memory fusion"""
        session_id = input_data.get("session_id")
        user_message = input_data.get("user_message", "")
        token_budget = input_data.get("token_budget", 2000)
        include_namespaces = input_data.get("namespaces", [
            "task", "doc", "email", "calendar", "course", "chat_summary"
        ])
        
        if not session_id:
            raise ToolError("session_id is required for context retrieval", self.name)
        
        # Build comprehensive context
        context = await self.retrieval_service.build_chat_context(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            token_budget=token_budget,
            include_namespaces=include_namespaces
        )
        
        # Get session stats
        session_stats = await self.chat_service.get_session_stats(user_id, session_id)
        
        return {
            "context": context,
            "context_length": len(context),
            "estimated_tokens": len(context) // 4,
            "session_stats": session_stats,
            "namespaces_included": include_namespaces
        }
    
    async def _analyze_behavior(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        weeks_back = input_data.get("weeks_back", 4)
        operation_type = input_data.get("type", "insights")  # "insights", "snapshots", "comparison"
        
        if operation_type == "insights":
            insights = await self.profile_service.generate_behavior_insights(user_id, weeks_back)
            return {
                "type": "behavior_insights",
                "insights": insights
            }
        
        elif operation_type == "snapshots":
            snapshots = await self.profile_service.get_recent_snapshots(user_id, weeks_back)
            return {
                "type": "weekly_snapshots",
                "snapshots": snapshots,
                "weeks_analyzed": weeks_back
            }
        
        elif operation_type == "comparison":
            snapshot1_id = input_data.get("snapshot1_id")
            snapshot2_id = input_data.get("snapshot2_id")
            
            if not (snapshot1_id and snapshot2_id):
                raise ToolError("Both snapshot IDs required for comparison", self.name)
            
            comparison = await self.profile_service.compare_snapshots(
                user_id, snapshot1_id, snapshot2_id
            )
            
            return {
                "type": "snapshot_comparison",
                "comparison": comparison
            }
        
        else:
            raise ToolError(f"Unknown analysis type: {operation_type}", self.name)
    
    async def _summarize_session(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Summarize and persist a chat session"""
        session_id = input_data.get("session_id")
        doc_id = input_data.get("doc_id")
        force_summarize = input_data.get("force_summarize", False)
        min_turns_threshold = input_data.get("min_turns_threshold", 4)
        
        if not session_id:
            raise ToolError("session_id is required for summarization", self.name)
        
        memory_id = await self.summarization_service.summarize_and_persist_session(
            user_id=user_id,
            session_id=session_id,
            doc_id=doc_id,
            force_summarize=force_summarize,
            min_turns_threshold=min_turns_threshold
        )
        
        if not memory_id:
            return {
                "summarized": False,
                "reason": "Session too short or insufficient content"
            }
        
        return {
            "summarized": True,
            "memory_id": memory_id,
            "session_id": session_id,
            "summarized_at": datetime.utcnow().isoformat()
        }
    
    async def _ingest_data(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Ingest data from various sources"""
        data_type = input_data.get("data_type")
        data = input_data.get("data")
        
        if not data_type or not data:
            raise ToolError("data_type and data are required for ingestion", self.name)
        
        memory_ids = []
        
        if data_type == "assignment":
            assignment = Assignment(**data)
            memory_id = await self.ingestion_service.ingest_assignment(user_id, assignment)
            if memory_id:
                memory_ids.append(memory_id)
        
        elif data_type == "calendar_event":
            event = CalendarEvent(**data)
            memory_id = await self.ingestion_service.ingest_calendar_event(user_id, event)
            if memory_id:
                memory_ids.append(memory_id)
        
        elif data_type == "email_thread":
            thread = EmailThread(**data)
            memory_id = await self.ingestion_service.ingest_email_thread(user_id, thread)
            if memory_id:
                memory_ids.append(memory_id)
        
        elif data_type == "document":
            document = Document(**data)
            memory_ids = await self.ingestion_service.ingest_document(user_id, document)
        
        # Note: user_preference data type removed - use preferences tool instead
        
        else:
            raise ToolError(f"Unknown data type: {data_type}", self.name)
        
        return {
            "data_type": data_type,
            "memory_ids": memory_ids,
            "ingested_count": len(memory_ids),
            "ingested_at": datetime.utcnow().isoformat()
        }
    
    async def _list_memories(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """List memory entries with filtering"""
        namespace = input_data.get("namespace")
        limit = input_data.get("limit", 50)
        offset = input_data.get("offset", 0)
        
        memories = await self.vector_service.list_memories(
            user_id=user_id,
            namespace=namespace,
            limit=limit,
            offset=offset
        )
        
        formatted_memories = []
        for memory in memories:
            formatted_memories.append({
                "id": memory.id,
                "namespace": memory.namespace,
                "doc_id": memory.doc_id,
                "chunk_id": memory.chunk_id,
                "summary": memory.summary,
                "metadata": memory.metadata,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat()
            })
        
        return {
            "memories": formatted_memories,
            "total_returned": len(formatted_memories),
            "namespace_filter": namespace,
            "limit": limit,
            "offset": offset
        }
    
    async def _get_memory_stats(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get memory statistics for the user"""
        stats = await self.vector_service.get_memory_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _search_similar(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Search for similar context without session dependency"""
        query = input_data.get("query", "")
        namespaces = input_data.get("namespaces", ["task", "doc", "email", "calendar", "course"])
        limit = input_data.get("limit", 20)
        
        if not query:
            raise ToolError("Query is required for similarity search", self.name)
        
        results = await self.retrieval_service.search_similar_context(
            user_id=user_id,
            query=query,
            namespaces=namespaces,
            limit=limit
        )
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "namespace": result.namespace,
                "doc_id": result.doc_id,
                "summary": result.summary,
                "content": result.content,
                "metadata": result.metadata,
                "similarity": result.similarity,
                "final_score": result.final_score
            })
        
        return {
            "results": formatted_results,
            "query": query,
            "namespaces_searched": namespaces,
            "total_results": len(formatted_results)
        }

# Create global instance
memory_tool = MemoryTool()