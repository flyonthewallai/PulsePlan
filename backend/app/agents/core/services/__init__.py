"""
Agent services and external service integrations.

This module contains service-related components including:
- LLM service with structured validation and response schemas
- User context service for personalization and context management
- Service orchestration and dependency management
"""

from .llm_service import (
    UnifiedLLMService,
    get_llm_service,
    ResponseSchema,
    IntentClassificationResponse,
    TaskExtractionResponse,
    ConversationResponse,
    UserContext,
    ConversationHistory,
    CacheConfig
)

from .user_context_service import (
    UserContextService,
    get_user_context_service,
    EnhancedUserContext,
    UserActivity,
    UserStats
)

__all__ = [
    # LLM service
    "UnifiedLLMService",
    "get_llm_service",
    "ResponseSchema",
    "IntentClassificationResponse",
    "TaskExtractionResponse",
    "ConversationResponse",
    "UserContext",
    "ConversationHistory",
    "CacheConfig",
    
    # User context service
    "UserContextService",
    "get_user_context_service",
    "EnhancedUserContext",
    "UserActivity",
    "UserStats",
]
