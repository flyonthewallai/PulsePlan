"""
Retrieval fusion system that combines ephemeral chat memory and persistent vector memory.
Implements MMR (Maximal Marginal Relevance) reranking for diverse, relevant results.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass

from .chat_memory import get_chat_memory_service, ChatTurn, ChatMemoryService
from .vector_memory import get_vector_memory_service, VectorMemoryService
from .embeddings import embed_batch, cosine_similarity
from .types import SearchOptions, SearchResult, Namespace

logger = logging.getLogger(__name__)

@dataclass
class ContextItem:
    """Unified representation for both chat turns and memory hits"""
    kind: str  # "turn" or "memory"
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: Optional[str] = None
    score: float = 0.0

class RetrievalService:
    """Service for retrieval fusion and context building"""
    
    def __init__(
        self,
        chat_service: Optional[ChatMemoryService] = None,
        vector_service: Optional[VectorMemoryService] = None
    ):
        self.chat_service = chat_service or get_chat_memory_service()
        self.vector_service = vector_service or get_vector_memory_service()
    
    async def build_chat_context(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        token_budget: int = 2000,
        include_namespaces: Optional[List[Namespace]] = None
    ) -> str:
        """
        Build comprehensive chat context by fusing recent turns and relevant memories.
        Returns formatted context string for prompt inclusion.
        """
        try:
            if include_namespaces is None:
                include_namespaces = [
                    "task", "doc", "email", "calendar", "course", 
                    "chat_summary"
                ]
            
            # 1. Get recent chat turns from Redis
            recent_turns = await self.chat_service.get_recent_turns(
                user_id, session_id, limit=32
            )
            
            # 2. Search vector memory for relevant long-term context
            search_options = SearchOptions(
                user_id=user_id,
                namespaces=include_namespaces,
                query=user_message,
                limit=40
            )
            
            memory_hits = await self.vector_service.search_memory(search_options)
            
            # 3. Generate embeddings for chat turns
            turn_texts = [f"{turn.role}: {turn.text}" for turn in recent_turns]
            turn_embeddings = await embed_batch(turn_texts) if turn_texts else []
            
            # 4. Convert to unified context items
            context_items = []
            
            # Add chat turns
            for i, turn in enumerate(recent_turns):
                if i < len(turn_embeddings):
                    item = ContextItem(
                        kind="turn",
                        content=turn.text,
                        embedding=turn_embeddings[i],
                        metadata={
                            "role": turn.role,
                            "timestamp": turn.ts
                        },
                        timestamp=turn.ts
                    )
                    context_items.append(item)
            
            # Add memory hits
            for hit in memory_hits:
                item = ContextItem(
                    kind="memory",
                    content=hit.summary or hit.content or "",
                    embedding=[],  # Already embedded in search
                    metadata={
                        "namespace": hit.namespace,
                        "doc_id": hit.doc_id,
                        "similarity": hit.similarity,
                        "urgency": hit.urgency,
                        "final_score": hit.final_score,
                        **hit.metadata
                    },
                    timestamp=hit.updated_at.isoformat(),
                    score=hit.final_score
                )
                context_items.append(item)
            
            # 5. Apply MMR reranking for diversity
            selected_items = await self._mmr_rerank(
                context_items, user_message, k=24, lambda_param=0.65
            )
            
            # 6. Format into context string within token budget
            context_lines = []
            for item in selected_items:
                line = self._format_context_item(item)
                
                # Check if adding this line would exceed budget
                test_context = "\n".join(context_lines + [line])
                if self._estimate_tokens(test_context) > token_budget:
                    break
                
                context_lines.append(line)
            
            final_context = "\n".join(context_lines)
            
            logger.debug(f"Built context with {len(context_lines)} items, "
                        f"~{self._estimate_tokens(final_context)} tokens")
            
            return final_context
            
        except Exception as e:
            logger.error(f"Failed to build chat context: {e}")
            return ""
    
    async def _mmr_rerank(
        self,
        items: List[ContextItem],
        query: str,
        k: int,
        lambda_param: float = 0.6
    ) -> List[ContextItem]:
        """
        Apply Maximal Marginal Relevance reranking for diversity.
        
        Args:
            items: List of context items to rerank
            query: Original user query for relevance calculation
            k: Number of items to select
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
        """
        if not items:
            return []
        
        try:
            # Get query embedding for relevance calculation
            query_embedding = (await embed_batch([query]))[0]
            
            selected = []
            remaining = list(items)
            
            while len(selected) < min(k, len(items)) and remaining:
                best_score = float('-inf')
                best_idx = 0
                
                for i, item in enumerate(remaining):
                    # Calculate relevance score
                    if item.kind == "memory":
                        # Use precomputed score for memory items
                        relevance = item.score
                    else:
                        # Calculate cosine similarity for chat turns
                        if item.embedding:
                            relevance = cosine_similarity(query_embedding, item.embedding)
                        else:
                            relevance = 0.5  # Default relevance for items without embeddings
                    
                    # Calculate diversity penalty (max similarity to already selected items)
                    diversity_penalty = 0.0
                    if selected:
                        max_similarity = 0.0
                        for selected_item in selected:
                            if item.embedding and selected_item.embedding:
                                similarity = cosine_similarity(item.embedding, selected_item.embedding)
                                max_similarity = max(max_similarity, similarity)
                        diversity_penalty = max_similarity
                    
                    # MMR score: balance relevance and diversity
                    mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
                    
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = i
                
                # Move best item to selected
                selected.append(remaining.pop(best_idx))
            
            return selected
            
        except Exception as e:
            logger.error(f"MMR reranking failed: {e}")
            # Fallback to original order with limit
            return items[:k]
    
    def _format_context_item(self, item: ContextItem) -> str:
        """Format a context item for prompt inclusion"""
        if item.kind == "turn":
            role = item.metadata.get("role", "unknown")
            timestamp = item.metadata.get("timestamp", "")
            return f"[chat {role} @ {timestamp}] {item.content}"
        
        elif item.kind == "memory":
            namespace = item.metadata.get("namespace", "unknown")
            due_info = ""
            if item.metadata.get("due_at"):
                due_info = f" (due {item.metadata['due_at']})"
            
            title = (item.metadata.get("title") or 
                    item.metadata.get("url") or 
                    item.metadata.get("subject") or
                    namespace)
            
            return f"[memory {namespace}{due_info}] {title}: {item.content}"
        
        return f"[{item.kind}] {item.content}"
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 characters per token)"""
        return len(text) // 4
    
    async def search_similar_context(
        self,
        user_id: str,
        query: str,
        namespaces: Optional[List[Namespace]] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        Search for similar context across memory namespaces.
        Useful for finding related information without session context.
        """
        try:
            if namespaces is None:
                namespaces = ["task", "doc", "email", "calendar", "course"]
            
            search_options = SearchOptions(
                user_id=user_id,
                namespaces=namespaces,
                query=query,
                limit=limit
            )
            
            results = await self.vector_service.search_memory(search_options)
            logger.debug(f"Found {len(results)} similar context items")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar context: {e}")
            return []
    
    async def get_context_summary(
        self,
        user_id: str,
        session_id: str,
        namespace_filter: Optional[List[Namespace]] = None
    ) -> Dict[str, Any]:
        """Get summary statistics about available context"""
        try:
            # Get chat session stats
            chat_stats = await self.chat_service.get_session_stats(user_id, session_id)
            
            # Get memory stats
            memory_stats = await self.vector_service.get_memory_stats(user_id)
            
            # Filter by namespaces if requested
            if namespace_filter:
                filtered_counts = {
                    ns: memory_stats.get("entries_by_namespace", {}).get(ns, 0)
                    for ns in namespace_filter
                }
                memory_stats["entries_by_namespace"] = filtered_counts
            
            return {
                "chat_context": chat_stats,
                "memory_context": memory_stats,
                "total_context_sources": (
                    chat_stats.get("total_turns", 0) + 
                    memory_stats.get("total_entries", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get context summary: {e}")
            return {}

# Global retrieval service instance
retrieval_service = RetrievalService()

def get_retrieval_service() -> RetrievalService:
    """Get the global retrieval service instance"""
    return retrieval_service