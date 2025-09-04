"""
Vector memory operations for semantic storage and retrieval.
Handles upsert, search, and management of vector memory entries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_memory_database, MemoryDatabase
from .embeddings import embed
from .types import (
    VecMemoryRow, VecMemoryCreate, VecMemoryUpdate, 
    SearchResult, SearchOptions, Namespace
)

logger = logging.getLogger(__name__)

class VectorMemoryService:
    """Service for managing vector memory operations"""
    
    def __init__(self, db: Optional[MemoryDatabase] = None):
        self.db = db or get_memory_database()
    
    async def upsert_memory(self, memory: VecMemoryCreate) -> Optional[str]:
        """
        Upsert a memory entry into the vector database.
        Returns the ID of the created/updated entry.
        """
        try:
            # Generate embedding if not provided
            embedding = memory.embedding
            if not embedding:
                text_to_embed = (
                    memory.text_for_embedding or 
                    memory.summary or 
                    memory.content or 
                    ""
                )
                if text_to_embed:
                    embedding = await embed(text_to_embed)
                else:
                    logger.warning("No text provided for embedding generation")
                    embedding = [0.0] * 1536  # Zero vector
            
            # Prepare data for upsert
            upsert_data = {
                "user_id": memory.user_id,
                "namespace": memory.namespace,
                "doc_id": memory.doc_id,
                "chunk_id": memory.chunk_id,
                "content": memory.content,
                "summary": memory.summary,
                "embedding": embedding,
                "metadata": memory.metadata,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Perform upsert using the unique constraint on (user_id, doc_id, chunk_id)
            result = self.db.client.from_("vec_memory").upsert(
                upsert_data,
                on_conflict="user_id,doc_id,chunk_id"
            ).select("id").execute()
            
            if result.data and len(result.data) > 0:
                entry_id = result.data[0]["id"]
                logger.debug(f"Upserted memory entry {entry_id} for user {memory.user_id}")
                return entry_id
            else:
                logger.error("Upsert returned no data")
                return None
                
        except Exception as e:
            logger.error(f"Failed to upsert memory: {e}")
            raise
    
    async def search_memory(self, search_options: SearchOptions) -> List[SearchResult]:
        """
        Search vector memory using semantic similarity and scoring.
        Returns ranked results based on similarity, urgency, and other factors.
        """
        try:
            # Generate query embedding
            query_embedding = await embed(search_options.query)
            
            # Prepare search parameters
            search_params = {
                "p_user_id": search_options.user_id,
                "p_query_embedding": query_embedding,
                "p_namespaces": search_options.namespaces,
                "p_limit": search_options.limit,
                "p_course": search_options.course,
                "p_due_start": search_options.due_start,
                "p_due_end": search_options.due_end
            }
            
            # Execute search using stored procedure
            results = await self.db.execute_rpc("search_vec_memory", search_params)
            
            # Convert results to SearchResult objects
            search_results = []
            for row in results:
                try:
                    search_result = SearchResult(
                        id=row["id"],
                        user_id=row["user_id"],
                        namespace=row["namespace"],
                        doc_id=row["doc_id"],
                        chunk_id=row["chunk_id"],
                        content=row.get("content"),
                        summary=row.get("summary"),
                        metadata=row.get("metadata", {}),
                        created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00')),
                        similarity=row["similarity"],
                        urgency=row["urgency"],
                        final_score=row["final_score"]
                    )
                    
                    # Apply minimum similarity filter if specified
                    if search_result.similarity >= search_options.min_similarity:
                        search_results.append(search_result)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
                    continue
            
            logger.debug(f"Found {len(search_results)} memory entries for user {search_options.user_id}")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    
    async def get_memory_by_id(self, memory_id: str, user_id: str) -> Optional[VecMemoryRow]:
        """Get a specific memory entry by ID"""
        try:
            result = self.db.client.from_("vec_memory").select("*").eq(
                "id", memory_id
            ).eq("user_id", user_id).single().execute()
            
            if result.data:
                row = result.data
                return VecMemoryRow(
                    id=row["id"],
                    user_id=row["user_id"],
                    namespace=row["namespace"],
                    doc_id=row["doc_id"],
                    chunk_id=row["chunk_id"],
                    content=row.get("content"),
                    summary=row.get("summary"),
                    embedding=row["embedding"],
                    metadata=row.get("metadata", {}),
                    created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory by ID: {e}")
            return None
    
    async def update_memory(
        self, 
        memory_id: str, 
        user_id: str, 
        updates: VecMemoryUpdate
    ) -> bool:
        """Update an existing memory entry"""
        try:
            update_data = {}
            
            # Add fields that are being updated
            if updates.content is not None:
                update_data["content"] = updates.content
            if updates.summary is not None:
                update_data["summary"] = updates.summary
            if updates.metadata is not None:
                update_data["metadata"] = updates.metadata
            
            # Generate new embedding if text changed
            if updates.text_for_embedding or updates.embedding:
                if updates.embedding:
                    update_data["embedding"] = updates.embedding
                elif updates.text_for_embedding:
                    embedding = await embed(updates.text_for_embedding)
                    update_data["embedding"] = embedding
            
            if not update_data:
                logger.warning("No updates provided")
                return False
            
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.db.client.from_("vec_memory").update(update_data).eq(
                "id", memory_id
            ).eq("user_id", user_id).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return False
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete a memory entry"""
        try:
            result = self.db.client.from_("vec_memory").delete().eq(
                "id", memory_id
            ).eq("user_id", user_id).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def delete_memories_by_doc_id(self, doc_id: str, user_id: str) -> int:
        """Delete all memory entries for a specific document"""
        try:
            result = self.db.client.from_("vec_memory").delete().eq(
                "doc_id", doc_id
            ).eq("user_id", user_id).execute()
            
            return len(result.data) if result.data else 0
            
        except Exception as e:
            logger.error(f"Failed to delete memories by doc_id: {e}")
            return 0
    
    async def list_memories(
        self, 
        user_id: str, 
        namespace: Optional[Namespace] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[VecMemoryRow]:
        """List memory entries for a user"""
        try:
            query = self.db.client.from_("vec_memory").select(
                "*"
            ).eq("user_id", user_id)
            
            if namespace:
                query = query.eq("namespace", namespace)
            
            query = query.order("updated_at", desc=True).limit(limit).offset(offset)
            
            result = query.execute()
            
            memories = []
            if result.data:
                for row in result.data:
                    memory = VecMemoryRow(
                        id=row["id"],
                        user_id=row["user_id"],
                        namespace=row["namespace"],
                        doc_id=row["doc_id"],
                        chunk_id=row["chunk_id"],
                        content=row.get("content"),
                        summary=row.get("summary"),
                        embedding=row["embedding"],
                        metadata=row.get("metadata", {}),
                        created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
                    )
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return []
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about a user's memory"""
        try:
            # Get total count
            count_result = self.db.client.from_("vec_memory").select(
                "*", count="exact"
            ).eq("user_id", user_id).execute()
            
            total_count = count_result.count or 0
            
            # Get namespace distribution
            namespace_result = self.db.client.from_("vec_memory").select(
                "namespace"
            ).eq("user_id", user_id).execute()
            
            namespace_counts = {}
            if namespace_result.data:
                for row in namespace_result.data:
                    ns = row["namespace"]
                    namespace_counts[ns] = namespace_counts.get(ns, 0) + 1
            
            # Get date range
            date_result = self.db.client.from_("vec_memory").select(
                "created_at"
            ).eq("user_id", user_id).order("created_at").execute()
            
            oldest_entry = None
            newest_entry = None
            if date_result.data:
                oldest_entry = datetime.fromisoformat(date_result.data[0]["created_at"].replace('Z', '+00:00'))
                newest_entry = datetime.fromisoformat(date_result.data[-1]["created_at"].replace('Z', '+00:00'))
            
            return {
                "total_entries": total_count,
                "entries_by_namespace": namespace_counts,
                "oldest_entry": oldest_entry,
                "newest_entry": newest_entry
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {
                "total_entries": 0,
                "entries_by_namespace": {},
                "oldest_entry": None,
                "newest_entry": None
            }

# Global vector memory service instance
vector_memory_service = VectorMemoryService()

def get_vector_memory_service() -> VectorMemoryService:
    """Get the global vector memory service instance"""
    return vector_memory_service