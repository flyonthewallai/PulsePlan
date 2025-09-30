"""
Memory retrieval and search capabilities.

This module contains memory retrieval components including:
- Vector embedding generation and management
- Advanced retrieval systems with MMR reranking
- Vector memory operations and similarity search
"""

from .embeddings import EmbeddingService

from .retrieval import (
    RetrievalService,
    get_retrieval_service,
    ContextItem
)

from .vector_memory import (
    VectorMemoryService,
    get_vector_memory_service
)

__all__ = [
    # Embedding operations
    "EmbeddingService",
    
    # Retrieval operations
    "RetrievalService",
    "get_retrieval_service",
    "ContextItem",
    
    # Vector memory operations
    "VectorMemoryService",
    "get_vector_memory_service",
]
