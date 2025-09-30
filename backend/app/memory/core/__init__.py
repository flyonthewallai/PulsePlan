"""
Core memory infrastructure and foundational components.

This module contains core memory system components including:
- Basic memory types and data structures
- Core memory persistence layer  
- Database utilities and connection management
"""

from .chat_memory import (
    ChatTurn,
    ChatMemoryService,
    get_chat_memory_service
)

from .types import (
    VecMemoryRow,
    VecMemoryCreate,
    VecMemoryUpdate,
    SearchOptions,
    SearchResult,
    MemoryStats,
    Assignment,
    CalendarEvent,
    EmailThread
)

from .database import MemoryDatabase

__all__ = [
    # Core chat memory
    "ChatTurn",
    "ChatMemoryService",
    "get_chat_memory_service",
    
    # Core types
    "VecMemoryRow",
    "VecMemoryCreate",
    "VecMemoryUpdate",
    "SearchOptions",
    "SearchResult",
    "MemoryStats",
    "Assignment",
    "CalendarEvent",
    "EmailThread",
    
    # Database utilities
    "MemoryDatabase",
]
