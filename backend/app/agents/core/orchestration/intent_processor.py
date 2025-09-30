"""
Unified Intent Processor
Single-point processing for all user queries with intent classification, entity extraction, and action routing
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from ..services.llm_service import (
    get_llm_service,
    IntentClassificationResponse,
    TaskExtractionResponse,
    ConversationResponse,
    UserContext
)
from ..services.user_context_service import get_user_context_service, EnhancedUserContext
from .agent_task_manager import get_agent_task_manager, TaskType

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Available action types"""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    LIST_TASKS = "list_tasks"
    COMPLETE_TASK = "complete_task"

    SCHEDULE_EVENT = "schedule_event"
    BLOCK_TIME = "block_time"
    RESCHEDULE_DAY = "reschedule_day"

    WEB_SEARCH = "web_search"

    SEND_EMAIL = "send_email"
    READ_EMAILS = "read_emails"

    DAILY_BRIEFING = "daily_briefing"
    WEEKLY_SUMMARY = "weekly_summary"

    GENERATE_RESPONSE = "generate_response"
    CASUAL_CONVERSATION = "casual_conversation"


class DialogAct(BaseModel):
    """Dialog act for conversation management"""
    type: str  # "INVOKE", "ASK", "CANCEL", "SWITCH", "CONTINUE"
    action: str
    confidence: float
    params: Dict[str, Any] = Field(default_factory=dict)
    refs: Dict[str, Any] = Field(default_factory=dict)
    requires_clarification: bool = False
    clarification_question: Optional[str] = None

class IntentResult(BaseModel):
    """Enhanced intent processing result with dialog management"""
    intent: str
    action: ActionType
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    task_info: Optional[TaskExtractionResponse] = None
    conversation_response: Optional[ConversationResponse] = None
    workflow_type: Optional[str] = None
    requires_task_card: bool = True
    immediate_response: Optional[str] = None
    
    # Enhanced dialog management
    dialog_acts: List[DialogAct] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    can_switch_workflow: bool = False
    suggested_workflows: List[str] = Field(default_factory=list)
    workflow_params: Dict[str, Any] = Field(default_factory=dict)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UnifiedIntentProcessor:
    """
    Unified processor for all user intents and actions
    Replaces the dual classification system with a single, optimized approach
    """

    def __init__(self):
        self.llm_service = get_llm_service()
        self.user_context_service = get_user_context_service()
        self.task_manager = get_agent_task_manager()

    async def process_user_query(
        self,
        user_query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResult:
        """
        Process user query with full context and unified intent classification
        """
        try:
            logger.info(f"Processing query for user {user_id}: {user_query[:100]}...")

            # Check for pending clarifications first (before any other processing)
            if conversation_id:
                logger.info(f"Checking for pending clarifications in conversation {conversation_id}")
                from ..conversation.conversation_state_manager import get_conversation_state_manager
                state_manager = get_conversation_state_manager()
                conversation_state = await state_manager.get_conversation_state(conversation_id, user_id)
                
                logger.info(f"Conversation state has {len(conversation_state.pending_clarifications)} pending clarifications")
                
                # If there are pending clarifications, check if this is a relevant response
                if conversation_state.pending_clarifications:
                    logger.info(f"Found {len(conversation_state.pending_clarifications)} pending clarifications")
                    
                    # Check if the user query is a relevant response to the clarification
                    if self._is_clarification_response(user_query, conversation_state.pending_clarifications[-1]):
                        logger.info(f"Query appears to be a clarification response, handling as such")
                        # Get user context for clarification handling
                        user_context = await self.user_context_service.get_user_context(user_id)
                        return await self._handle_clarification_response(
                            user_query=user_query,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            conversation_state=conversation_state,
                            user_context=user_context
                        )
                    else:
                        logger.info(f"Query does not appear to be a clarification response, clearing pending clarifications")
                        # Clear pending clarifications and process as normal request
                        conversation_state.pending_clarifications.clear()
                        await state_manager.update_conversation_state(conversation_state)
                        logger.info(f"Cleared all pending clarifications for unrelated request")

            # Get user context
            user_context = await self.user_context_service.get_user_context(user_id)

            # Build conversation history, extracting summary if present as first system turn
            from ..services.llm_service import ConversationHistory
            summary_text = None
            turns_only = conversation_history or []
            if turns_only and isinstance(turns_only[0], dict):
                first = turns_only[0]
                role = first.get("role")
                content = first.get("content", "") or ""
                if role == "system" and content.startswith("Conversation Summary:"):
                    try:
                        summary_text = content.split(":", 1)[1].strip()
                    except Exception:
                        summary_text = content
                    turns_only = turns_only[1:]

            conv_history = ConversationHistory(
                turns=turns_only,
                summary=summary_text,
                context={"conversation_id": conversation_id}
            )

            # Fast path for simple conversational queries - single LLM call
            if self._is_simple_conversation(user_query):
                logger.info(f"🚀 [FAST-PATH] Using single LLM call for simple conversation")
                conversation_response = await self.llm_service.generate_conversation_response(
                    user_query=user_query,
                    user_context=user_context,
                    conversation_history=conv_history
                )
                
                return IntentResult(
                    intent="casual_conversation",
                    action=ActionType.CASUAL_CONVERSATION,
                    confidence=0.9,
                    entities={},
                    conversation_response=conversation_response,
                    immediate_response=conversation_response.message,
                    requires_task_card=False,
                    workflow_type=None,
                    metadata={"fast_path": True}
                )

            # Single LLM call for intent classification
            intent_response = await self.llm_service.classify_intent_with_context(
                user_query=user_query,
                user_context=user_context,
                conversation_history=conv_history
            )

            # Determine action and workflow
            action, workflow_type = self._map_intent_to_action(intent_response)

            # Initialize result
            result = IntentResult(
                intent=intent_response.intent,
                action=action,
                confidence=intent_response.confidence,
                entities=intent_response.entities,
                workflow_type=workflow_type,
                metadata={
                    "reasoning": intent_response.reasoning,
                    "requires_disambiguation": intent_response.requires_disambiguation,
                    "alternative_intents": intent_response.alternative_intents
                }
            )

            # Process based on intent type with enhanced dialog management
            if self._is_task_management_intent(intent_response.intent):
                await self._process_task_intent(result, user_query, user_context, intent_response, conv_history)
            elif self._is_conversation_intent(intent_response.intent):
                await self._process_conversation_intent(result, user_query, user_context, conv_history)
            else:
                # Other workflow intents (calendar, search, email, etc.)
                await self._process_workflow_intent(result, user_query, user_context)
            
            # Add dialog management
            await self._add_dialog_management(result, user_query, user_context, conv_history)

            logger.info(f"Processed intent: {result.intent} -> {result.action} (confidence: {result.confidence:.2f})")
            return result

        except Exception as e:
            logger.error(f"Failed to process user query: {e}")
            return self._create_fallback_result(user_query, str(e))

    def _map_intent_to_action(self, intent_response: IntentClassificationResponse) -> Tuple[ActionType, Optional[str]]:
        """
        Map classified intent to specific action and workflow type
        """
        intent = intent_response.intent
        action = intent_response.action

        # Direct mapping from action to ActionType
        action_mapping = {
            "create_task": (ActionType.CREATE_TASK, "tasks"),
            "update_task": (ActionType.UPDATE_TASK, None),  # Go through direct CRUD execution
            "delete_task": (ActionType.DELETE_TASK, None),  # Go through direct CRUD execution  
            "list_tasks": (ActionType.LIST_TASKS, "tasks"),
            "complete_task": (ActionType.COMPLETE_TASK, None),  # Go through direct CRUD execution
            "schedule_event": (ActionType.SCHEDULE_EVENT, "calendar"),
            "block_time": (ActionType.BLOCK_TIME, "calendar"),
            "reschedule_day": (ActionType.RESCHEDULE_DAY, "scheduling"),
            "web_search": (ActionType.WEB_SEARCH, "search"),
            "daily_briefing": (ActionType.DAILY_BRIEFING, "briefing"),
            "weekly_summary": (ActionType.WEEKLY_SUMMARY, "briefing"),
            "generate_response": (ActionType.GENERATE_RESPONSE, None),
            "casual_conversation": (ActionType.GENERATE_RESPONSE, None),  # Map to generate_response
            "send_email": (ActionType.SEND_EMAIL, "email"),
            "read_emails": (ActionType.READ_EMAILS, "email"),
            "sync_canvas": (ActionType.GENERATE_RESPONSE, None),  # Map to generate_response for now
        }

        # Direct lookup - no fuzzy matching needed!
        if action in action_mapping:
            return action_mapping[action]

        # Fallback based on intent
        fallback_mapping = {
            "task_management": (ActionType.CREATE_TASK, "tasks"),
            "calendar": (ActionType.SCHEDULE_EVENT, "calendar"),
            "search": (ActionType.WEB_SEARCH, "search"),
            "email": (ActionType.READ_EMAILS, "email"),
            "briefing": (ActionType.DAILY_BRIEFING, "briefing"),
            "chat": (ActionType.GENERATE_RESPONSE, None),
        }

        return fallback_mapping.get(intent, (ActionType.GENERATE_RESPONSE, None))

    async def _process_task_intent(
        self,
        result: IntentResult,
        user_query: str,
        user_context: EnhancedUserContext,
        intent_response: IntentClassificationResponse,
        conv_history
    ) -> None:
        """
        Process task management intents
        """
        try:
            # Check if disambiguation is required first
            if intent_response.requires_disambiguation:
                logger.info(f"Disambiguation required for task intent: {intent_response.suggested_action}")
                result.requires_clarification = True
                result.clarification_question = intent_response.suggested_action or "Could you please provide more details?"
                result.requires_task_card = False
                result.immediate_response = result.clarification_question
                return
            
            # For simple flows, avoid separate extraction; synthesize task_info from entities when present
            if result.action == ActionType.CREATE_TASK:
                # Check for batch task creation
                task_names = intent_response.entities.get("task_names", [])
                single_task_name = (
                    intent_response.entities.get("task_name") or
                    intent_response.entities.get("task_title") or
                    intent_response.entities.get("target_task")
                )
                
                # Handle batch task creation
                if task_names:
                    # Multiple tasks - store them in metadata for batch processing
                    result.metadata["batch_tasks"] = []
                    for task_name in task_names:
                        task_info = TaskExtractionResponse(
                            success=True,
                            timestamp=datetime.utcnow().isoformat(),
                            task_title=task_name,
                            task_description=intent_response.entities.get("description"),
                            due_date=intent_response.entities.get("due_date"),
                            priority=intent_response.entities.get("priority", "medium"),
                            estimated_duration=intent_response.entities.get("estimated_duration"),
                            tags=intent_response.entities.get("tags", []),
                            category=intent_response.entities.get("category", "general")
                        )
                        result.metadata["batch_tasks"].append(task_info)
                    
                    # Set the first task as the primary task_info for compatibility
                    result.task_info = result.metadata["batch_tasks"][0]
                    
                elif single_task_name:
                    # Single task creation
                    result.task_info = TaskExtractionResponse(
                        success=True,
                        timestamp=datetime.utcnow().isoformat(),
                        task_title=single_task_name,
                        task_description=intent_response.entities.get("description"),
                        due_date=intent_response.entities.get("due_date"),
                        priority=intent_response.entities.get("priority", "medium"),
                        estimated_duration=intent_response.entities.get("estimated_duration"),
                        tags=intent_response.entities.get("tags", []),
                        category=intent_response.entities.get("category", "general")
                    )
                    
                    # Apply regex-based fallbacks for common patterns if LLM didn't extract them
                    self._apply_regex_fallbacks(result.task_info, user_query)
                else:
                    # No task name extracted - request clarification
                    logger.info(f"No task name extracted for CREATE_TASK. Entities: {intent_response.entities}")
                    result.requires_clarification = True
                    result.clarification_question = "What task would you like me to create? Please provide a specific task name or description."
                    result.requires_task_card = False
                    result.immediate_response = result.clarification_question
                    return

            # Handle batch operations for delete/update/complete tasks
            elif result.action in [ActionType.DELETE_TASK, ActionType.UPDATE_TASK, ActionType.COMPLETE_TASK]:
                # Check for batch task operations
                target_tasks = intent_response.entities.get("target_tasks", [])
                single_target_task = intent_response.entities.get("target_task")
                
                if target_tasks:
                    # Multiple tasks - store them in metadata for batch processing
                    result.metadata["batch_tasks"] = []
                    for task_name in target_tasks:
                        task_info = TaskExtractionResponse(
                            success=True,
                            timestamp=datetime.utcnow().isoformat(),
                            task_title=task_name,
                            task_description=intent_response.entities.get("description"),
                            due_date=intent_response.entities.get("due_date"),
                            priority=intent_response.entities.get("priority", "medium"),
                            estimated_duration=intent_response.entities.get("estimated_duration"),
                            tags=intent_response.entities.get("tags", []),
                            category=intent_response.entities.get("category", "general")
                        )
                        result.metadata["batch_tasks"].append(task_info)
                    
                    # Set the first task as the primary task_info for compatibility
                    result.task_info = result.metadata["batch_tasks"][0]
                    
                elif single_target_task:
                    # Single task operation
                    result.task_info = TaskExtractionResponse(
                        success=True,
                        timestamp=datetime.utcnow().isoformat(),
                        task_title=single_target_task,
                        task_description=intent_response.entities.get("description"),
                        due_date=intent_response.entities.get("due_date"),
                        priority=intent_response.entities.get("priority", "medium"),
                        estimated_duration=intent_response.entities.get("estimated_duration"),
                        tags=intent_response.entities.get("tags", []),
                        category=intent_response.entities.get("category", "general")
                    )

            # Determine if task card is needed
            result.requires_task_card = result.action not in [ActionType.LIST_TASKS, ActionType.CREATE_TASK, ActionType.UPDATE_TASK, ActionType.DELETE_TASK, ActionType.COMPLETE_TASK]

            # Set immediate response for quick actions
            if result.action == ActionType.DELETE_TASK:
                result.immediate_response = None  # Skip immediate response, go straight to success card
                result.requires_task_card = False  # Use success card instead
            elif result.action == ActionType.LIST_TASKS:
                result.immediate_response = None  # Skip immediate response, go straight to success card
                result.requires_task_card = False  # Use success card instead
                
                # Extract filters for task listing
                filters = {}
                if intent_response.entities.get("status"):
                    filters["status"] = intent_response.entities["status"]
                if intent_response.entities.get("priority"):
                    filters["priority"] = intent_response.entities["priority"]
                if intent_response.entities.get("due_date"):
                    filters["due_before"] = intent_response.entities["due_date"]
                if intent_response.entities.get("tags"):
                    filters["tags"] = intent_response.entities["tags"]
                if intent_response.entities.get("project"):
                    filters["project_id"] = intent_response.entities["project"]
                
                # Add quantity limit if specified
                if intent_response.quantity:
                    filters["limit"] = intent_response.quantity
                
                result.workflow_params["filters"] = filters

        except Exception as e:
            logger.error(f"Failed to process task intent: {e}")

    async def _process_conversation_intent(
        self,
        result: IntentResult,
        user_query: str,
        user_context: EnhancedUserContext,
        conv_history
    ) -> None:
        """
        Process conversation intents
        """
        try:
            # Generate conversational response
            conversation_response = await self.llm_service.generate_conversation_response(
                user_query=user_query,
                user_context=user_context,
                conversation_history=conv_history
            )

            result.conversation_response = conversation_response
            result.immediate_response = conversation_response.message
            result.requires_task_card = False  # Pure conversation doesn't need task cards

        except Exception as e:
            logger.error(f"Failed to process conversation intent: {e}")

    async def _process_workflow_intent(
        self,
        result: IntentResult,
        user_query: str,
        user_context: EnhancedUserContext
    ) -> None:
        """
        Process workflow intents (search, calendar, email, briefing)
        """
        try:
            # Set appropriate immediate responses and task requirements
            if result.action == ActionType.WEB_SEARCH:
                search_query = result.entities.get("search_query", user_query)
                result.immediate_response = f"I'll search for '{search_query}' for you."

            elif result.action == ActionType.DAILY_BRIEFING:
                result.immediate_response = "I'm preparing your daily briefing."

            elif result.action == ActionType.SCHEDULE_EVENT:
                event_title = result.entities.get("event_title", "your event")
                result.immediate_response = f"I'll help you schedule '{event_title}'."

            elif result.action == ActionType.READ_EMAILS:
                result.immediate_response = "I'll check your recent emails."

            # All workflow intents require task cards for progress tracking
            result.requires_task_card = True

        except Exception as e:
            logger.error(f"Failed to process workflow intent: {e}")

    def _is_task_management_intent(self, intent: str) -> bool:
        """Check if intent is task management related"""
        return intent in ["task_management", "tasks"]

    def _is_conversation_intent(self, intent: str) -> bool:
        """Check if intent is conversational"""
        return intent in ["chat", "conversation", "greeting"]

    def _create_fallback_result(self, user_query: str, error_message: str) -> IntentResult:
        """Create fallback result for processing errors"""
        return IntentResult(
            intent="chat",
            action=ActionType.GENERATE_RESPONSE,
            confidence=0.1,
            requires_task_card=False,
            immediate_response="I'm sorry, I had trouble understanding your request. Could you please rephrase it?",
            metadata={
                "error": error_message,
                "fallback": True
            }
        )

    async def create_task_card_if_needed(
        self,
        result: IntentResult,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create task card if the intent requires progress tracking
        """
        try:
            if not result.requires_task_card:
                return None

            # Determine task title and description
            if result.task_info:
                title = result.task_info.task_title
                description = result.task_info.task_description
            else:
                title = self._generate_task_title(result)
                description = result.immediate_response

            # Create appropriate task card
            if result.workflow_type:
                task_card = await self.task_manager.create_workflow_task(
                    user_id=user_id,
                    workflow_type=result.workflow_type,
                    title=title,
                    description=description,
                    conversation_id=conversation_id,
                    estimated_duration=self._estimate_duration(result.action)
                )
                return task_card.id

        except Exception as e:
            logger.error(f"Failed to create task card: {e}")

        return None

    async def _add_dialog_management(self, result: IntentResult, user_query: str, user_context, conv_history) -> None:
        """Add dialog management capabilities to the result"""
        try:
            # Check if clarification is needed
            if self._needs_clarification(result, user_query):
                result.requires_clarification = True
                result.clarification_question = self._generate_clarification_question(result, user_query)
                result.immediate_response = result.clarification_question
                result.requires_task_card = False
                
                # Add ASK dialog act
                result.dialog_acts.append(DialogAct(
                    type="ASK",
                    action="ask_clarification",
                    confidence=0.9,
                    clarification_question=result.clarification_question,
                    requires_clarification=True
                ))
            
            # Check if workflow switching is possible
            if self._can_switch_workflow(result, user_query):
                result.can_switch_workflow = True
                result.suggested_workflows = self._get_suggested_workflows(result, user_query)
                
                # Add SWITCH dialog act
                result.dialog_acts.append(DialogAct(
                    type="SWITCH",
                    action="switch_workflow",
                    confidence=0.8,
                    params={"suggested_workflows": result.suggested_workflows}
                ))
            
            # Add INVOKE dialog act for the main action
            result.dialog_acts.append(DialogAct(
                type="INVOKE",
                action=result.action.value,
                confidence=result.confidence,
                params=result.workflow_params,
                refs=result.entities
            ))
            
        except Exception as e:
            logger.error(f"Failed to add dialog management: {e}")

    def _is_clarification_response(self, user_query: str, clarification_request) -> bool:
        """
        Check if the user query is a relevant response to the pending clarification
        """
        query_lower = user_query.lower().strip()
        
        # Get the original action from the clarification context
        original_action = clarification_request.context.get("action", "")
        
        # For CREATE_TASK clarifications, check if the response contains a task name
        if original_action == "create_task":
            # If the query is just a greeting or unrelated, it's not a clarification response
            unrelated_patterns = [
                "hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "yes", "no",
                "what", "how", "when", "where", "why", "help", "search", "find", "show"
            ]
            
            # If it's a single unrelated word, not a clarification response
            if query_lower in unrelated_patterns:
                return False
            
            # If it starts with unrelated words and doesn't contain task-related keywords, not a clarification
            if any(query_lower.startswith(pattern) for pattern in ["search", "find", "show", "list", "get"]):
                return False
            
            # If it starts with task creation phrases, it's a new request, not a clarification response
            if any(query_lower.startswith(pattern) for pattern in ["make a task", "create a task", "add a task", "create task", "make task", "add task"]):
                return False
            
            # If it contains task creation keywords or seems like a task name, it's likely a clarification response
            task_keywords = ["task", "todo", "create", "add", "make"]
            if any(keyword in query_lower for keyword in task_keywords):
                return True
            
            # If it's a multi-word phrase, likely a task description
            if len(query_lower.split()) >= 2:
                return True
            
            # Single word that's not in unrelated patterns - could be a task name
            # Only exclude if it's clearly unrelated
            if len(query_lower.split()) == 1 and query_lower not in unrelated_patterns:
                return True
            
            return False
        
        # For other clarifications, be more conservative and assume it's a response
        return True

    def _needs_clarification(self, result: IntentResult, user_query: str) -> bool:
        """Check if the query needs clarification using slot-level confidence"""
        query_lower = user_query.lower().strip()
        
        # Check for ambiguous task operations
        if result.action in [ActionType.DELETE_TASK, ActionType.UPDATE_TASK, ActionType.COMPLETE_TASK]:
            # Check for single task operations
            single_target_task = result.entities.get("target_task")
            # Check for batch task operations
            target_tasks = result.entities.get("target_tasks", [])
            
            # If no specific task name(s) are mentioned
            if not single_target_task and not target_tasks:
                return True
        
        # Check for ambiguous CREATE_TASK operations with slot-level confidence
        if result.action == ActionType.CREATE_TASK:
            return self._needs_task_clarification(result.entities, user_query)
        
        # Check for ambiguous calendar operations
        if result.action in [ActionType.SCHEDULE_EVENT, ActionType.RESCHEDULE_DAY]:
            if not result.entities.get("event_title") and not result.entities.get("event_name"):
                return True
        
        # Check for very vague queries
        vague_patterns = [
            "delete my task", "remove my task", "complete my task",
            "schedule something", "add an event", "block time",
            "create a task", "add a task", "make a task", "new task", 
        ]
        
        for pattern in vague_patterns:
            if pattern in query_lower:
                return True
                
        return False

    def _generate_clarification_question(self, result: IntentResult, user_query: str) -> str:
        """Generate appropriate clarification question"""
        if result.action == ActionType.DELETE_TASK:
            return "Which task would you like me to delete?"
        elif result.action == ActionType.UPDATE_TASK:
            return "Which task would you like me to update?"
        elif result.action == ActionType.COMPLETE_TASK:
            return "Which task would you like me to mark as complete?"
        elif result.action == ActionType.CREATE_TASK:
            return "What task would you like me to create? Please provide a specific task name or description."
        elif result.action == ActionType.SCHEDULE_EVENT:
            return "What event would you like me to schedule?"
        elif result.action == ActionType.RESCHEDULE_DAY:
            return "What would you like me to reschedule?"
        else:
            return "Could you provide more details about what you'd like me to do?"

    def _can_switch_workflow(self, result: IntentResult, user_query: str) -> bool:
        """Check if workflow switching is possible"""
        query_lower = user_query.lower().strip()
        
        # Allow switching if user mentions different workflow keywords
        switch_keywords = {
            "calendar": ["event", "schedule", "meeting", "appointment"],
            "tasks": ["task", "todo", "assignment", "homework"],
            "search": ["search", "find", "look up", "google"],
            "email": ["email", "message", "send", "reply"]
        }
        
        current_workflow = result.workflow_type
        for workflow, keywords in switch_keywords.items():
            if workflow != current_workflow:
                if any(keyword in query_lower for keyword in keywords):
                    return True
        
        return False

    def _get_suggested_workflows(self, result: IntentResult, user_query: str) -> List[str]:
        """Get suggested workflows for switching"""
        query_lower = user_query.lower().strip()
        suggestions = []
        
        if any(word in query_lower for word in ["event", "schedule", "meeting", "appointment"]):
            suggestions.append("calendar")
        if any(word in query_lower for word in ["task", "todo", "assignment", "homework"]):
            suggestions.append("tasks")
        if any(word in query_lower for word in ["search", "find", "look up"]):
            suggestions.append("search")
        if any(word in query_lower for word in ["email", "message", "send"]):
            suggestions.append("email")
            
        return suggestions

    def _is_simple_conversation(self, user_query: str) -> bool:
        """Check if query is a simple conversational request that doesn't need intent classification"""
        query_lower = user_query.lower().strip()
        
        # Simple greeting patterns
        greeting_patterns = [
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'how are you doing', 'what\'s up', 'how\'s it going',
            'nice to meet you', 'pleased to meet you', 'good to see you'
        ]
        
        # Simple question patterns
        question_patterns = [
            'how are you', 'how are you doing', 'what\'s up', 'how\'s it going',
            'how was your day', 'how was your weekend', 'how\'s everything',
            'what are you up to', 'what\'s new', 'how do you feel'
        ]
        
        # Check for exact matches or starts with
        for pattern in greeting_patterns + question_patterns:
            if query_lower == pattern or query_lower.startswith(pattern + ' '):
                return True
        
        # Check for very short queries (likely conversational)
        if len(query_lower.split()) <= 3 and not any(word in query_lower for word in ['task', 'create', 'delete', 'schedule', 'search', 'email']):
            return True
            
        return False

    def _generate_task_title(self, result: IntentResult) -> str:
        """Generate appropriate task title based on action"""
        action_titles = {
            ActionType.WEB_SEARCH: "Web Search",
            ActionType.DAILY_BRIEFING: "Daily Briefing",
            ActionType.WEEKLY_SUMMARY: "Weekly Summary",
            ActionType.SCHEDULE_EVENT: "Schedule Event",
            ActionType.BLOCK_TIME: "Block Time",
            ActionType.RESCHEDULE_DAY: "Reschedule Day",
            ActionType.READ_EMAILS: "Check Emails",
            ActionType.SEND_EMAIL: "Send Email",
            ActionType.CREATE_TASK: "Create Task",
            ActionType.UPDATE_TASK: "Update Task",
            ActionType.DELETE_TASK: "Delete Task",
        }
        return action_titles.get(result.action, "Processing Request")

    def _estimate_duration(self, action: ActionType) -> int:
        """Estimate task duration in seconds based on action type"""
        duration_estimates = {
            ActionType.WEB_SEARCH: 15,
            ActionType.DAILY_BRIEFING: 30,
            ActionType.WEEKLY_SUMMARY: 45,
            ActionType.CREATE_TASK: 5,
            ActionType.DELETE_TASK: 3,
            ActionType.UPDATE_TASK: 5,
            ActionType.LIST_TASKS: 2,
            ActionType.SCHEDULE_EVENT: 10,
            ActionType.READ_EMAILS: 20,
            ActionType.SEND_EMAIL: 15,
        }
        return duration_estimates.get(action, 15)

    async def _handle_clarification_response(
        self,
        user_query: str,
        user_id: str,
        conversation_id: str,
        conversation_state,
        user_context
    ) -> IntentResult:
        """
        Handle user response to a clarification question
        """
        try:
            # Get the most recent clarification request
            clarification = conversation_state.pending_clarifications[-1]
            
            logger.info(f"Handling clarification response: '{user_query}' for question: '{clarification.question}'")
            
            # Resolve the clarification
            from ..conversation.conversation_state_manager import get_conversation_state_manager
            state_manager = get_conversation_state_manager()
            resolved_clarification = await state_manager.resolve_clarification(
                conversation_id=conversation_id,
                user_id=user_id,
                clarification_id=clarification.id,
                user_response=user_query
            )
            
            if not resolved_clarification:
                logger.warning("Failed to resolve clarification, falling back to normal processing")
                return await self._create_fallback_result(user_query, "Failed to resolve clarification")
            
            # Update the conversation state to reflect the resolved clarification
            conversation_state = await state_manager.get_conversation_state(conversation_id, user_id)
            logger.info(f"After clarification resolution: {len(conversation_state.pending_clarifications)} pending clarifications remaining")
            
            # Extract the original intent context from the clarification
            original_intent = resolved_clarification.context.get("intent")
            original_action = resolved_clarification.context.get("action")
            
            # Create a new intent result with the clarified information
            if original_action == "delete_task":
                # User provided the task name to delete
                return IntentResult(
                    intent="task_management",
                    action=ActionType.DELETE_TASK,
                    confidence=0.9,
                    entities={"task_name": user_query},
                    immediate_response=f"I'll delete the task '{user_query}' for you.",
                    requires_task_card=False,  # Use success card instead
                    workflow_type="tasks",
                    metadata={
                        "clarification_resolved": True,
                        "original_intent": original_intent,
                        "clarification_question": clarification.question
                    }
                )
            elif original_action == "update_task":
                # User provided the task name to update
                return IntentResult(
                    intent="task_management",
                    action=ActionType.UPDATE_TASK,
                    confidence=0.9,
                    entities={"task_name": user_query},
                    immediate_response=f"I'll update the task '{user_query}' for you.",
                    requires_task_card=True,
                    workflow_type="tasks",
                    metadata={
                        "clarification_resolved": True,
                        "original_intent": original_intent,
                        "clarification_question": clarification.question
                    }
                )
            elif original_action == "complete_task":
                # User provided the task name to complete
                return IntentResult(
                    intent="task_management",
                    action=ActionType.COMPLETE_TASK,
                    confidence=0.9,
                    entities={"task_name": user_query},
                    immediate_response=f"I'll mark the task '{user_query}' as completed.",
                    requires_task_card=False,  # Use success card instead
                    workflow_type="tasks",
                    metadata={
                        "clarification_resolved": True,
                        "original_intent": original_intent,
                        "clarification_question": clarification.question
                    }
                )
            elif original_action == "create_task":
                # Use dedicated clarification completion LLM call
                task_info = await self.llm_service.complete_clarification_task(
                    user_response=user_query,
                    original_request=resolved_clarification.context,
                    clarification_context={
                        "action": original_action,
                        "question": clarification.question
                    },
                    user_context=user_context
                )
                
                return IntentResult(
                    intent="task_management",
                    action=ActionType.CREATE_TASK,
                    confidence=0.9,
                    entities={"task_name": task_info.task_title},
                    task_info=task_info,
                    immediate_response=f"I'll create the task '{task_info.task_title}' for you.",
                    requires_task_card=False,  # Use success card instead
                    workflow_type="tasks",
                    metadata={
                        "clarification_resolved": True,
                        "original_intent": original_intent,
                        "clarification_question": clarification.question
                    }
                )
            else:
                # Generic clarification handling
                return IntentResult(
                    intent=original_intent or "task_management",
                    action=ActionType.GENERATE_RESPONSE,
                    confidence=0.8,
                    entities={"clarification_response": user_query},
                    immediate_response=f"Thank you for clarifying. I understand you meant '{user_query}'.",
                    requires_task_card=False,
                    workflow_type=None,
                    metadata={
                        "clarification_resolved": True,
                        "original_intent": original_intent,
                        "clarification_question": clarification.question
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to handle clarification response: {e}")
            return await self._create_fallback_result(user_query, str(e))

    def _apply_regex_fallbacks(self, task_info: TaskExtractionResponse, user_query: str) -> None:
        """Apply regex-based fallbacks for common task metadata patterns"""
        import re
        from datetime import datetime, timedelta
        
        query_lower = user_query.lower()
        
        # Typo correction fallbacks
        self._correct_common_typos(task_info, query_lower)
        
        # Priority fallbacks
        if task_info.priority == "medium":  # Only apply if LLM didn't extract priority
            if any(word in query_lower for word in ["urgent", "asap", "immediately", "critical"]):
                task_info.priority = "urgent"
            elif any(word in query_lower for word in ["high priority", "important", "priority"]):
                task_info.priority = "high"
            elif any(word in query_lower for word in ["low priority", "whenever", "sometime"]):
                task_info.priority = "low"
        
        # Duration fallbacks (convert to minutes)
        if not task_info.estimated_duration:
            duration_match = re.search(r'(\d+)[\s-]*(hour|hr|minute|min)', query_lower)
            if duration_match:
                value, unit = duration_match.groups()
                if unit in ["hour", "hr"]:
                    task_info.estimated_duration = int(value) * 60
                else:
                    task_info.estimated_duration = int(value)

    def _correct_common_typos(self, task_info: TaskExtractionResponse, query_lower: str) -> None:
        """Correct common typos in task titles"""
        common_typos = {
            "tasj": "task",
            "homwork": "homework", 
            "studdy": "study",
            "examm": "exam",
            "projct": "project",
            "assigment": "assignment",
            "presntation": "presentation",
            "reserch": "research",
            "repor": "report",
            "essay": "essay",  # Already correct
            "quiz": "quiz",    # Already correct
            "test": "test"     # Already correct
        }
        
        # Check if task title contains common typos
        if task_info.task_title:
            title_lower = task_info.task_title.lower()
            for typo, correction in common_typos.items():
                if typo in title_lower:
                    # Replace the typo with the correction
                    corrected_title = title_lower.replace(typo, correction)
                    # Preserve original capitalization
                    if task_info.task_title.isupper():
                        task_info.task_title = corrected_title.upper()
                    elif task_info.task_title.istitle():
                        task_info.task_title = corrected_title.title()
                    else:
                        task_info.task_title = corrected_title
                    logger.info(f"Corrected typo '{typo}' to '{correction}' in task title")
                    break

    def _is_generic_title(self, title: str) -> bool:
        """Check if task title is too generic using regex patterns"""
        import re
        
        s = title.lower().strip()
        
        # Regex patterns for generic titles
        generic_patterns = [
            r"^\s*(task|todo|to[-\s]?do|item|thing|something)\s*$",
            r"\b(make|create|add|new)\s+(a\s+)?(task|todo|to[-\s]?do|item|thing)\b",
            r"^\s*(make|create|add)\s+(one|some|something)\s*$",
            r"^\s*(task|todo)\s+(for|about)\s+me\s*$",
            r"\b(add|make|create)\s+(one|some)\s+(for|about)\s+me\b",
            r"\b(todo|task)\s+(for|about|regarding)\s+\w+\s*$",
        ]
        
        # Check exact matches first (fast)
        exact_matches = {
            "task", "todo", "to do", "to-do", "item", "thing", "something",
            "task creation", "create task", "create a task", "new task",
            "add task", "add a task", "make task", "make a task",
            "make one", "add one", "create one", "task management"
        }
        
        if s in exact_matches:
            return True
        
        # Check regex patterns
        return any(re.search(pattern, s) for pattern in generic_patterns)

    def _needs_task_clarification(self, entities: Dict[str, Any], user_query: str) -> bool:
        """Check if task creation needs clarification based on slot-level confidence"""
        
        # Slot confidence thresholds
        SLOT_THRESHOLDS = {
            "task_title": 0.8,
            "due_date": 0.6,
            "priority": 0.7,
            "estimated_duration": 0.7,
        }
        
        # Extract task title(s)
        task_title = (
            entities.get("task_name") or 
            entities.get("task_title") or 
            entities.get("target_task")
        )
        
        # Check for batch tasks
        task_names = entities.get("task_names", [])
        
        # If no task title(s) were extracted, it's ambiguous
        if not task_title and not task_names:
            return True
        
        # For batch tasks, check if all task names are valid
        if task_names:
            for task_name in task_names:
                if not task_name or self._is_generic_title(task_name):
                    return True
            # All batch task names are valid
            return False
        
        # Check if task title is too generic
        if self._is_generic_title(task_title):
            return True
        
        # Check confidence scores if provided by LLM
        confidence_scores = entities.get("confidence_scores", {})
        
        # If we have confidence scores, use them
        if confidence_scores:
            for slot, threshold in SLOT_THRESHOLDS.items():
                slot_confidence = confidence_scores.get(slot, 1.0)  # Default to high confidence if not provided
                if slot in entities and slot_confidence < threshold:
                    return True
        
        # Fallback: Check for ambiguous patterns in the query
        ambiguous_patterns = [
            "tomorrow morning", "tomorrow afternoon", "tomorrow evening",
            "next week", "this week", "soon", "later", "sometime",
            "when i have time", "before the deadline"
        ]
        
        query_lower = user_query.lower()
        if any(pattern in query_lower for pattern in ambiguous_patterns):
            return True
        
        return False


# Global service instance
_intent_processor = None

def get_intent_processor() -> UnifiedIntentProcessor:
    """Get global IntentProcessor instance"""
    global _intent_processor
    if _intent_processor is None:
        _intent_processor = UnifiedIntentProcessor()
    return _intent_processor