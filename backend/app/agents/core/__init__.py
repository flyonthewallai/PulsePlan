"""
Agents core module - Core agent functionality organized by domain.

This module provides organized access to all agent core functionality grouped by domain:
- conversation: Conversation management, state tracking, and WebSocket notifications
- error: Error handling, boundaries, and recovery systems
- state: Workflow state management and container orchestration
- services: LLM service and user context management
- orchestration: Agent task management and intent processing
"""

# Re-export from modules for backward compatibility
from .conversation import *
from .error import *
from .state import *
from .services import *
from .orchestration import *

__all__ = [
    # Conversation management
    "ConversationManager",
    "get_conversation_manager",
    "ChatTurn",
    "ConversationSession",
    "create_conversation_session",
    "ConversationHistory",
    "ConversationContext",
    "ConversationStateManager",
    "get_conversation_state_manager",
    "ConversationState",
    "StateTransition",
    "StateValidation",
    "StateSnapshotRestore",
    "WebSocketNotificationManager",
    "get_websocket_manager",
    "ImmediateResponse",
    "NotificationEvent",
    "WebSocketConnection",
    "ConnectionPool",
    "NotificationHandler",
    "EventBroadcaster",
    
    # Error handling
    "ErrorBoundary",
    "get_error_boundary",
    "ErrorSeverity",
    "RecoveryStrategy",
    "CircuitBreakerState",
    "WorkflowErrorBoundary",
    "ErrorHandlingStrategy",
    "ErrorMetrics",
    "ErrorRecoveryPlan",
    "ErrorHandler",
    "get_error_handler",
    "ErrorType",
    "ErrorContext",
    "ErrorResponse",
    "ClientErrorHandler",
    "WebSocketErrorHandler",
    "DatabaseErrorHandler",
    "LLMErrorHandler",
    "RecoveryService",
    "get_recovery_service",
    "RecoveryTrigger",
    "RecoveryAttempt",
    "RecoveryStrategyPattern",
    "AutomatedRecovery",
    "RecoveryMetrics",
    "RecoveryScheduler",
    "StateRecoveryManager",
    
    # State management
    "StateManager",
    "get_state_manager",
    "StateStatus",
    "StateSnapshot",
    "StateTransitionHandler",
    "StateValidator",
    "StateIsolation",
    "StatePersistence",
    "WorkflowStateManager",
    "StateMetrics",
    "WorkflowContainer",
    "get_workflow_container",
    "ContainerState",
    "WorkflowLifecycle",
    "ContainerOrchestrator",
    "WorkflowIsolation",
    "ContainerMetrics",
    "WorkflowExecutionEnvironment",
    
    # Services
    "UnifiedLLMService",
    "get_unified_llm_service",
    "LLMResponse",
    "ResponseSchema",
    "LLMCache",
    "LLMMetrics",
    "StructuredResponseValidator",
    "LLMBatchProcessor",
    "LLMConfigurationManager",
    "UserContextService",
    "get_user_context_service",
    "UserContext",
    "ContextBuilder",
    "ContextValidator",
    "ContextManager",
    "UserPreferencesLookup",
    "ProfileService",
    
    # Orchestration
    "AgentTaskManager",
    "get_agent_task_manager",
    "TaskSession",
    "TaskLifecycle",
    "TaskCoordinator",
    "SessionManager",
    "TaskMetrics",
    "TaskValidator",
    "IntentProcessor",
    "get_intent_processor",
    "ActionType",
    "WorkflowType",
    "IntentResult",
    "IntentClassifier",
    "EntityExtractor",
    "ContextEnricher",
    "InferenceEngine",
]