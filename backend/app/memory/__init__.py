"""
Memory module - Comprehensive memory system organized by domain.

This module provides organized access to all memory functionality grouped by domain:
- core: Core memory infrastructure, types, and database utilities
- processing: Chat processing, ingestion, and summarization workflows  
- retrieval: Embedding generation, vector search, and retrieval operations
- management: Profile management and memory lifecycle
"""

# Re-export from modules for backward compatibility
from .core import *
from .processing import *
from .retrieval import *
from .management import *

__all__ = [
    # Core memory infrastructure
    "ChatTurn",
    "ChatMemoryService",
    "get_chat_memory_service", 
    "create_chat_turn",
    "ChatTurnCache",
    "Namespace",
    "VecMemoryRow",
    "MemoryContext",
    "SearchOptions",
    "SearchResult",
    "MemoryResult",
    "EmbeddingResult",
    "IngestionResult",
    "RetrievalResult",
    "MemoryStats",
    "ProfileSnapshot",
    "ProfileMetrics",
    "MemoryDatabase",
    "get_memory_database",
    "create_memory_database_session",
    "initialize_memory_tables",
    "cleanup_old_memory_data",
    
    # Memory processing
    "ChatLoopService",
    "get_chat_loop_service",
    "process_chat_turn", 
    "build_conversation_context",
    "manage_memory_storage",
    "execute_chat_session",
    "IngestionService",
    "get_ingestion_service",
    "ingest_text_content",
    "ingest_documents",
    "process_content_chunks",
    "validate_ingestion_input",
    "SummarizationService",
    "get_summarization_service",
    "summarize_conversation",
    "summarize_memory_context",
    "create_profile_snapshot",
    "compress_memory_content",
    
    # Memory retrieval
    "EmbeddingService",
    "get_embedding_service",
    "embed_batch",
    "embed_text",
    "cosine_similarity",
    "calculate_vector_distance",
    "optimize_embedding_batch",
    "RetrievalService",
    "get_retrieval_service",
    "search_memory",
    "ContextItem",
    "execute_mmr_search",
    "rank_context_items",
    "fuse_search_results",
    "VectorMemoryService",
    "get_vector_memory_service",
    "store_vector_memory",
    "query_vector_memory",
    "manage_vector_storage",
    "optimize_vector_indexes",
    
    # Memory management
    "ProfileManager",
    "get_profile_manager",
    "generate_snapshot",
    "analyze_user_patterns",
    "track_behavior_metrics",
    "export_profile_data",
    "ProfileSnapshotService",
    "UserBehaviorAnalyzer",
]