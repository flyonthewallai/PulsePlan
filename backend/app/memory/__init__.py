"""
Memory system package for PulsePlan.

This package provides:
- Ephemeral chat memory using Redis
- Persistent semantic memory using pgvector
- Retrieval fusion combining recent context and long-term memory
"""

from .chat_memory import (
    ChatTurn,
    ChatMemoryService,
    chat_memory_service,
    get_chat_memory_service
)

from .vector_memory import (
    VectorMemoryService,
    vector_memory_service,
    get_vector_memory_service
)

from .retrieval import (
    RetrievalService,
    retrieval_service,
    get_retrieval_service
)

from .ingestion import (
    IngestionService,
    ingestion_service,
    get_ingestion_service
)

from .summarization import (
    SummarizationService,
    summarization_service,
    get_summarization_service
)

from .profile_snapshots import (
    WeeklyProfileService,
    weekly_profile_service,
    get_weekly_profile_service
)

from .chat_loop import (
    ChatLoopService,
    chat_loop_service,
    get_chat_loop_service
)

from .embeddings import (
    EmbeddingService,
    embedding_service,
    get_embedding_service,
    embed,
    embed_batch
)

from .types import *
from .database import get_memory_database

__all__ = [
    # Chat Memory
    'ChatTurn',
    'ChatMemoryService', 
    'chat_memory_service',
    'get_chat_memory_service',
    
    # Vector Memory
    'VectorMemoryService',
    'vector_memory_service',
    'get_vector_memory_service',
    
    # Retrieval
    'RetrievalService',
    'retrieval_service',
    'get_retrieval_service',
    
    # Ingestion
    'IngestionService',
    'ingestion_service',
    'get_ingestion_service',
    
    # Summarization
    'SummarizationService',
    'summarization_service',
    'get_summarization_service',
    
    # Profile Snapshots
    'WeeklyProfileService',
    'weekly_profile_service',
    'get_weekly_profile_service',
    
    # Chat Loop
    'ChatLoopService',
    'chat_loop_service',
    'get_chat_loop_service',
    
    # Embeddings
    'EmbeddingService',
    'embedding_service',
    'get_embedding_service',
    'embed',
    'embed_batch',
    
    # Database
    'get_memory_database'
]