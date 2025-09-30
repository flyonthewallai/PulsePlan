"""
Conversation management and orchestration.

This module contains conversation-related components including:
- Conversation persistence and session management
- Conversation state tracking and context building
- WebSocket notifications for real-time conversation updates
"""

from .conversation_manager import (
    ConversationManager,
    get_conversation_manager,
    ChatTurn,
    Conversation,
    ConversationSummary
)

from .conversation_state_manager import (
    ConversationStateManager,
    get_conversation_state_manager,
    ConversationState,
    ClarificationRequest
)

from .websocket_notification_manager import (
    WebSocketNotificationManager,
    get_websocket_manager,
    ImmediateResponse,
    TaskCompletionResponse,
    ClarificationResponse,
    WorkflowSwitchResponse
)

__all__ = [
    # Conversation management
    "ConversationManager",
    "get_conversation_manager",
    "ChatTurn",
    "Conversation",
    "ConversationSummary",
    
    # Conversation state management
    "ConversationStateManager",
    "get_conversation_state_manager",
    "ConversationState",
    "ClarificationRequest",
    
    # WebSocket notifications
    "WebSocketNotificationManager",
    "get_websocket_manager",
    "ImmediateResponse",
    "TaskCompletionResponse",
    "ClarificationResponse",
    "WorkflowSwitchResponse",
]
