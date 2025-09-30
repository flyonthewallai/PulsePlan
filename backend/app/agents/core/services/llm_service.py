"""
Unified LLM Service with Structured Validation and Response Schemas
This service provides optimized, validated LLM interactions with caching and error handling.
"""
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ValidationError
from enum import Enum

from app.core.observability.llm import get_llm_client
from app.config.cache.redis_client import get_redis_client
from app.config.database.supabase import get_supabase

logger = logging.getLogger(__name__)


class ResponseSchema(BaseModel):
    """Base schema for LLM responses"""
    success: bool = Field(description="Whether the operation was successful")
    timestamp: str = Field(description="ISO timestamp of response")

    class Config:
        extra = "allow"


class IntentClassificationResponse(ResponseSchema):
    """Schema for intent classification responses"""
    intent: str = Field(description="Primary classified intent")
    action: str = Field(description="Specific action to take - MUST be one of: create_task, update_task, delete_task, list_tasks, complete_task, schedule_event, block_time, reschedule_day, web_search, daily_briefing, weekly_summary, generate_response, casual_conversation, send_email, read_emails")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities (e.g., target_task, new_title, task_name, event_title, search_query)")
    quantity: Optional[int] = Field(default=None, description="Number of items to retrieve (e.g., '10 most recent emails', '5 tasks'). Null if not specified.")
    suggested_action: str = Field(description="Human-readable description of the action")
    requires_disambiguation: bool = Field(default=False, description="Whether disambiguation is needed")
    alternative_intents: List[str] = Field(default_factory=list, description="Alternative possible intents")
    reasoning: str = Field(description="Brief explanation of classification decision (max 10 words)")


class TaskExtractionResponse(ResponseSchema):
    """Schema for task extraction responses"""
    task_title: str = Field(description="Extracted task title")
    task_description: Optional[str] = Field(None, description="Task description if provided")
    due_date: Optional[str] = Field(None, description="Due date in ISO format if mentioned")
    priority: Optional[str] = Field(default="medium", description="Task priority (low, medium, high, urgent)")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    tags: Optional[List[str]] = Field(default_factory=list, description="Relevant tags")
    category: Optional[str] = Field(default="general", description="Task category")


class ConversationResponse(ResponseSchema):
    """Schema for general conversation responses"""
    message: str = Field(description="Assistant's response message")
    tone: str = Field(default="helpful", description="Response tone")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")
    requires_action: bool = Field(default=False, description="Whether user action is required")


class UserContext(BaseModel):
    """User context data structure"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    timezone: str = "UTC"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    working_hours: Dict[str, Any] = Field(default_factory=dict)
    user_type: Optional[str] = None
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)


class ConversationHistory(BaseModel):
    """Conversation history structure"""
    turns: List[Dict[str, str]] = Field(default_factory=list)
    summary: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class CacheConfig(BaseModel):
    """Cache configuration"""
    enabled: bool = False  # Disabled for fresh responses
    ttl_seconds: int = 0   # No TTL since caching is disabled
    use_redis: bool = False
    use_database: bool = False


class UnifiedLLMService:
    """
    Unified LLM service providing optimized, validated interactions
    """

    def __init__(self, cache_config: Optional[CacheConfig] = None):
        self.cache_config = cache_config or CacheConfig()
        # Disable caching by default for fresh responses
        self.cache_config.enabled = False
        self.llm_client = get_llm_client()

    async def classify_intent_with_context(
        self,
        user_query: str,
        user_context: UserContext,
        conversation_history: ConversationHistory,
        response_schema: Type[IntentClassificationResponse] = IntentClassificationResponse
    ) -> IntentClassificationResponse:
        """
        Classify user intent with full context and structured validation
        """
        operation_id = self._generate_operation_id()

        try:
            logger.info(f"[LLM-TRACE-{operation_id}] Starting intent classification", extra={
                "operation_id": operation_id,
                "user_id": user_context.user_id,
                "query_length": len(user_query),
                "has_history": len(conversation_history.turns) > 0,
                "operation": "intent_classification"
            })

            # Generate cache key
            cache_key = self._generate_cache_key("intent_classification", {
                "query": user_query,
                "user_id": user_context.user_id,
                "context_hash": self._hash_context(user_context, conversation_history)
            })

            # Try cache first
            if self.cache_config.enabled:
                cached_response = await self._get_cached_response(cache_key, response_schema)
                if cached_response:
                    logger.info(f"[LLM-TRACE-{operation_id}] Cache hit - skipping LLM call", extra={
                        "operation_id": operation_id,
                        "cache_key": cache_key[:20] + "...",
                        "cached_intent": cached_response.intent,
                        "cached_confidence": cached_response.confidence
                    })
                    return cached_response

            # Build comprehensive prompt
            system_prompt = await self._build_intent_classification_prompt(user_context)
            user_prompt = self._build_user_prompt_with_history(user_query, conversation_history)

            # Generate schema for LLM
            response_format = self._generate_json_schema(response_schema)

            # Log what we're sending to LLM
            logger.info(f"[LLM-TRACE-{operation_id}] Sending to LLM", extra={
                "operation_id": operation_id,
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "user_query": user_query,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
                "response_schema_fields": list(response_format.get("properties", {}).keys()),
                "cache_key": cache_key
            })

            # Detailed prompt logging (debug level for full content)
            logger.info(f"[LLM-TRACE-{operation_id}] Full system prompt", extra={
                "operation_id": operation_id,
                "system_prompt": system_prompt
            })

            logger.info(f"[LLM-TRACE-{operation_id}] Full user prompt", extra={
                "operation_id": operation_id,
                "user_prompt": user_prompt
            })

            # Call LLM with structured output
            start_time = datetime.utcnow()
            llm_response = await self.llm_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=response_format,
                model="gpt-4o-mini",
                temperature=0.3
            )
            llm_duration = (datetime.utcnow() - start_time).total_seconds()

            # Log what we received from LLM
            logger.info(f"[LLM-TRACE-{operation_id}] Received from LLM", extra={
                "operation_id": operation_id,
                "llm_duration_seconds": llm_duration,
                "response_length": len(llm_response),
                "response_preview": llm_response[:200] + "..." if len(llm_response) > 200 else llm_response
            })

            # Full response logging (debug level)
            logger.info(f"[LLM-TRACE-{operation_id}] Full LLM response", extra={
                "operation_id": operation_id,
                "llm_response": llm_response
            })

            # Validate and parse response
            try:
                validated_response = self._validate_and_parse_response(
                    llm_response, response_schema, user_query
                )

                logger.info(f"[LLM-TRACE-{operation_id}] Response validated successfully", extra={
                    "operation_id": operation_id,
                    "intent": validated_response.intent,
                    "confidence": validated_response.confidence,
                    "action": validated_response.suggested_action,
                    "entities_count": len(validated_response.entities),
                    "validation_success": True
                })

            except Exception as validation_error:
                logger.error(f"[LLM-TRACE-{operation_id}] Response validation failed", extra={
                    "operation_id": operation_id,
                    "validation_error": str(validation_error),
                    "raw_response": llm_response,
                    "validation_success": False
                })
                raise

            # Cache the response
            if self.cache_config.enabled:
                await self._cache_response(cache_key, validated_response)
                logger.debug(f"[LLM-TRACE-{operation_id}] Response cached", extra={
                    "operation_id": operation_id,
                    "cache_key": cache_key
                })

            logger.info(f"[LLM-TRACE-{operation_id}] Intent classification completed", extra={
                "operation_id": operation_id,
                "total_duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "final_intent": validated_response.intent,
                "final_confidence": validated_response.confidence,
                "success": True
            })

            return validated_response

        except Exception as e:
            logger.error(f"[LLM-TRACE-{operation_id}] Intent classification failed", extra={
                "operation_id": operation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_query": user_query,
                "success": False
            })
            # Return fallback response
            return self._create_fallback_intent_response(user_query, str(e))

    async def extract_task_info(
        self,
        user_query: str,
        user_context: UserContext,
        conversation_history: Optional[ConversationHistory] = None,
        response_schema: Type[TaskExtractionResponse] = TaskExtractionResponse
    ) -> TaskExtractionResponse:
        """
        Extract task information from user query with validation
        """
        operation_id = self._generate_operation_id()

        try:
            logger.info(f"[LLM-TRACE-{operation_id}] Starting task extraction", extra={
                "operation_id": operation_id,
                "user_id": user_context.user_id,
                "query_length": len(user_query),
                "operation": "task_extraction"
            })

            cache_key = self._generate_cache_key("task_extraction", {
                "query": user_query,
                "user_id": user_context.user_id
            })

            if self.cache_config.enabled:
                cached_response = await self._get_cached_response(cache_key, response_schema)
                if cached_response:
                    logger.info(f"[LLM-TRACE-{operation_id}] Cache hit - skipping LLM call", extra={
                        "operation_id": operation_id,
                        "cache_key": cache_key[:20] + "...",
                        "cached_task_title": cached_response.task_title
                    })
                    return cached_response

            system_prompt = self._build_task_extraction_prompt(user_context, conversation_history)
            response_format = self._generate_json_schema(response_schema)

            # Log what we're sending to LLM
            logger.info(f"[LLM-TRACE-{operation_id}] Sending to LLM", extra={
                "operation_id": operation_id,
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "user_query": user_query,
                "system_prompt_length": len(system_prompt),
                "response_schema_fields": list(response_format.get("properties", {}).keys())
            })

            logger.debug(f"[LLM-TRACE-{operation_id}] Full prompts", extra={
                "operation_id": operation_id,
                "system_prompt": system_prompt,
                "user_prompt": user_query
            })

            # Enrich user prompt with recent conversation history to resolve references
            enriched_user_prompt = self._build_user_prompt_with_history(
                user_query,
                conversation_history or ConversationHistory()
            )

            start_time = datetime.utcnow()
            llm_response = await self.llm_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=enriched_user_prompt,
                response_format=response_format,
                model="gpt-4o-mini",
                temperature=0.2
            )
            llm_duration = (datetime.utcnow() - start_time).total_seconds()

            # Log what we received from LLM
            logger.info(f"[LLM-TRACE-{operation_id}] Received from LLM", extra={
                "operation_id": operation_id,
                "llm_duration_seconds": llm_duration,
                "response_length": len(llm_response),
                "response_preview": llm_response[:200] + "..." if len(llm_response) > 200 else llm_response
            })

            logger.info(f"[LLM-TRACE-{operation_id}] Full LLM response", extra={
                "operation_id": operation_id,
                "llm_response": llm_response
            })

            validated_response = self._validate_and_parse_response(
                llm_response, response_schema, user_query
            )

            logger.info(f"[LLM-TRACE-{operation_id}] Task extraction completed", extra={
                "operation_id": operation_id,
                "task_title": validated_response.task_title,
                "task_priority": validated_response.priority,
                "has_due_date": bool(validated_response.due_date),
                "tags_count": len(validated_response.tags),
                "success": True
            })

            if self.cache_config.enabled:
                await self._cache_response(cache_key, validated_response)

            return validated_response

        except Exception as e:
            logger.error(f"[LLM-TRACE-{operation_id}] Task extraction failed", extra={
                "operation_id": operation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_query": user_query,
                "success": False
            })
            return self._create_fallback_task_response(user_query, str(e))

    async def complete_clarification_task(
        self,
        user_response: str,
        original_request: Dict[str, Any],
        clarification_context: Dict[str, Any],
        user_context: UserContext
    ) -> TaskExtractionResponse:
        """Complete a task creation from a clarification response using a focused LLM call"""
        operation_id = self._generate_operation_id()
        
        try:
            logger.info(f"🔄 [CLARIFICATION-COMPLETION-{operation_id}] Processing clarification response: '{user_response}'")
            
            # Build focused prompt for task completion
            system_prompt = self._build_clarification_completion_prompt(
                original_request, clarification_context, user_context
            )
            
            user_prompt = f"User's clarification response: {user_response}"
            
            # Make focused LLM call for task extraction
            response_format = self._generate_json_schema(TaskExtractionResponse)
            structured_response = await self.llm_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=response_format,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the structured response
            response = self._validate_and_parse_response(structured_response, TaskExtractionResponse, user_response)
            
            logger.info(f"✅ [CLARIFICATION-COMPLETION-{operation_id}] Task extraction completed: {response.task_title}")
            return response
            
        except Exception as e:
            logger.error(f"❌ [CLARIFICATION-COMPLETION-{operation_id}] Failed to complete clarification: {e}")
            # Fallback to basic task extraction
            return TaskExtractionResponse(
                success=True,
                timestamp=datetime.utcnow().isoformat(),
                task_title=user_response.strip(),
                priority="medium",
                category="general"
            )

    async def generate_conversation_response(
        self,
        user_query: str,
        user_context: UserContext,
        conversation_history: ConversationHistory,
        response_schema: Type[ConversationResponse] = ConversationResponse
    ) -> ConversationResponse:
        """
        Generate conversational response with context and validation
        """
        operation_id = self._generate_operation_id()

        try:
            logger.info(f"[LLM-TRACE-{operation_id}] Starting conversation response", extra={
                "operation_id": operation_id,
                "user_id": user_context.user_id,
                "query_length": len(user_query),
                "history_turns": len(conversation_history.turns),
                "operation": "conversation_response"
            })

            cache_key = self._generate_cache_key("conversation", {
                "query": user_query,
                "user_id": user_context.user_id,
                "context_hash": self._hash_context(user_context, conversation_history)
            })

            if self.cache_config.enabled:
                cached_response = await self._get_cached_response(cache_key, response_schema)
                if cached_response:
                    logger.info(f"[LLM-TRACE-{operation_id}] Cache hit - skipping LLM call", extra={
                        "operation_id": operation_id,
                        "cache_key": cache_key[:20] + "...",
                        "cached_message_length": len(cached_response.message)
                    })
                    return cached_response

            system_prompt = self._build_conversation_prompt(user_context)
            user_prompt = self._build_user_prompt_with_history(user_query, conversation_history)
            response_format = self._generate_json_schema(response_schema)

            # Log what we're sending to LLM
            logger.info(f"[LLM-TRACE-{operation_id}] Sending to LLM", extra={
                "operation_id": operation_id,
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "user_query": user_query,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
                "response_schema_fields": list(response_format.get("properties", {}).keys())
            })

            logger.debug(f"[LLM-TRACE-{operation_id}] Full prompts", extra={
                "operation_id": operation_id,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            })

            start_time = datetime.utcnow()
            llm_response = await self.llm_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=response_format,
                model="gpt-4o-mini",
                temperature=0.7
            )
            llm_duration = (datetime.utcnow() - start_time).total_seconds()

            # Log what we received from LLM
            logger.info(f"[LLM-TRACE-{operation_id}] Received from LLM", extra={
                "operation_id": operation_id,
                "llm_duration_seconds": llm_duration,
                "response_length": len(llm_response),
                "response_preview": llm_response[:200] + "..." if len(llm_response) > 200 else llm_response
            })

            logger.info(f"[LLM-TRACE-{operation_id}] Full LLM response", extra={
                "operation_id": operation_id,
                "llm_response": llm_response
            })

            validated_response = self._validate_and_parse_response(
                llm_response, response_schema, user_query
            )

            logger.info(f"[LLM-TRACE-{operation_id}] Conversation response completed", extra={
                "operation_id": operation_id,
                "message_length": len(validated_response.message),
                "tone": validated_response.tone,
                "follow_up_count": len(validated_response.follow_up_suggestions),
                "requires_action": validated_response.requires_action,
                "success": True
            })

            if self.cache_config.enabled:
                await self._cache_response(cache_key, validated_response)

            return validated_response

        except Exception as e:
            logger.error(f"[LLM-TRACE-{operation_id}] Conversation generation failed", extra={
                "operation_id": operation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_query": user_query,
                "success": False
            })
            return self._create_fallback_conversation_response(user_query, str(e))

    async def _build_intent_classification_prompt(self, user_context: UserContext) -> str:
        """Build system prompt for intent classification"""
        from datetime import datetime
        import pytz
        from ...core.utils.timezone_utils import get_timezone_manager
        
        try:
            # Get user's actual timezone using the timezone service
            timezone_manager = get_timezone_manager()
            user_tz = await timezone_manager.get_user_timezone(user_context.user_id)
            current_time = datetime.now(user_tz)
            current_date_str = current_time.strftime("%A, %B %d, %Y")
            current_time_str = current_time.strftime("%I:%M %p")
            timezone_name = str(user_tz)
        except Exception as e:
            # Fallback to provided timezone if service fails
            logger.warning(f"Failed to get user timezone, using fallback: {e}")
            user_tz = pytz.timezone(user_context.timezone) if user_context.timezone != 'UTC' else pytz.UTC
            current_time = datetime.now(user_tz)
            current_date_str = current_time.strftime("%A, %B %d, %Y")
            current_time_str = current_time.strftime("%I:%M %p")
            timezone_name = user_context.timezone
        
        return f"""You are Pulse, an intelligent AI assistant that helps users manage their academic and professional tasks.

User Context:
- Name: {user_context.name or 'User'}
- Timezone: {timezone_name}
- Current Date: {current_date_str}
- Current Time: {current_time_str}
- User Type: {user_context.user_type or 'general'}
- Working Hours: {json.dumps(user_context.working_hours)}

Your task is to classify the user's intent and determine the specific action to take.

Available intents and their corresponding actions:
- task_management: Creating, updating, deleting, or listing tasks
  * create_task: User wants to create a new task
  * update_task: User wants to modify an existing task
  * delete_task: User wants to remove a task
  * list_tasks: User wants to see their tasks
  * complete_task: User wants to mark a task as done

- calendar: Calendar operations, scheduling, time blocking
  * schedule_event: User wants to create a calendar event
  * block_time: User wants to block time for a task
  * reschedule_day: User wants to reorganize their schedule

- search: Web search requests
  * web_search: User wants to search the web

- briefing: Daily briefings or summaries
  * daily_briefing: User wants a daily summary
  * weekly_summary: User wants a weekly summary

- chat: General conversation, questions, small talk
  * generate_response: User wants a conversational response
  * casual_conversation: User is making small talk

- email: Email-related operations
  * send_email: User wants to send an email
  * read_emails: User wants to check their emails

- canvas: Canvas LMS integration tasks
  * sync_canvas: User wants to sync with Canvas

CRITICAL: The 'action' field MUST be exactly one of the action names listed above (e.g., 'list_tasks', 'create_task', etc.). Do not use natural language descriptions.

When the action relates to existing items (update_task, delete_task, complete_task):
- Use recent conversation context to resolve pronouns like "it", "that one", etc.
- SINGLE ITEM OPERATIONS: Populate entities.target_task with the exact item title to operate on.
- BATCH ITEM OPERATIONS: For multiple items, use entities.target_tasks (array) instead of single target_task.
- If the user is renaming an item, also populate entities.new_title with the new name.
- If multiple items could match or the target cannot be determined, set requires_disambiguation=true and provide a concise suggested_action prompting the user to specify which item.
- UPDATE vs CREATE: 
  * Use create_task when the user explicitly wants to CREATE a new item (keywords: "create", "add", "new", "make a task", "make task", "create a task", "add a task", "finish", "complete", "work on", "do", "handle", "take care of").
  * Use update_task ONLY when modifying existing user-created todos (keywords: "update [existing todo]", "modify [existing todo]", "change [existing todo]", "set [existing todo] due/priority").
  * IMPORTANT: update_task operates on TODOS (user-created items), NOT Canvas assignments/tasks which have immutable due dates.
  * IMPORTANT: If the user says "make a task [X]" or "create a task [X]", always use create_task regardless of what X contains (even if X contains words like "update", "modify", etc.).
- Examples:
  * "delete homework" → target_task: "homework" (deletes user-created todo)
  * "delete them" → target_tasks: ["cook chicken", "linear algebra hw"] (from context)
  * "complete math and science tasks" → target_tasks: ["math", "science"]
  * "delete cook chicken and linear algebra hw" → target_tasks: ["cook chicken", "linear algebra hw"]
  * "update Google OA due tonight at 9pm" → target_task: "Google OA", due_date: "2023-10-05T21:00:00" (updates user-created todo)
  * "modify my study session due today at 9am" → target_task: "study session", due_date: "2023-10-05T09:00:00" (updates user-created todo)
  * "change the todo cook chicken to high priority" → target_task: "cook chicken", priority: "high" (updates user-created todo)
  * "set my workout due Friday" → target_task: "workout", due_date: "2023-10-06T09:00:00" (updates user-created todo)
  * "finish file upload" → create_task with task_name: "finish file upload"
  * "complete the report" → create_task with task_name: "complete the report"
  * "work on presentation" → create_task with task_name: "work on presentation"
  * "make a task -- update beta worklist" → create_task with task_name: "update beta worklist"
  * "create a task called update the database" → create_task with task_name: "update the database"
  * "add a task to modify the settings" → create_task with task_name: "modify the settings"

When the action is web_search:
- Extract the actual search query from the user's message and populate entities.search_query with it.
- Remove phrases like "search the web for", "search for", "look up", "find" from the query.
- Examples:
  * "search the web for tips for studying linear algebra" → search_query: "tips for studying linear algebra"
  * "find information about machine learning" → search_query: "information about machine learning"
  * "look up Python tutorials" → search_query: "Python tutorials"

When the action is create_task:
- Extract task metadata with confidence scores for each field:
  * task_name/task_title/target_task: The task name/title (auto-correct obvious typos)
  * due_date: Due date as ISO timestamp if mentioned. Calculate the actual date/time based on the current date/time provided above and user's timezone. NEVER return past dates or dates more than 2 years in the future. Use null if no due date mentioned.
  * priority: Priority level if mentioned (low, medium, high, urgent)
  * estimated_duration: Duration in minutes if mentioned
  * tags: Relevant tags if mentioned (both predefined and custom tags are supported)
  * description: Additional task description if provided
  * confidence_scores: Object with confidence (0-1) for each extracted field
- SMART DATE PARSING: Calculate actual dates and return as ISO timestamps in user's timezone:
  * Use the Current Date and Current Time provided above for all calculations
  * "tomorrow" → Calculate tomorrow's date + 9am (default time)
  * "Friday at 3pm" → Calculate next Friday + 3pm
  * "next Monday morning" → Calculate next Monday + 9am
  * "in 2 hours" → Add 2 hours to current time
  * "tonight at 9pm" → Today's date + 9pm (only if current time is before 9pm)
  * "January 15th" → Next January 15th + 9am (default time)
  * VALIDATION RULES:
    - NEVER return dates in the past (before current date/time)
    - NEVER return dates more than 2 years in the future
    - If user says "tonight" but it's already past that time, use tomorrow night
    - Default times: morning=9am, afternoon=2pm, evening=6pm, night=8pm
- TAG EXTRACTION: Identify relevant tags from context:
  * Academic: "homework", "study", "exam", "assignment", "project", "research"
  * Work: "meeting", "report", "presentation", "deadline", "client", "email"
  * Personal: "shopping", "cleaning", "exercise", "health", "family", "friends"
  * Urgent: "urgent", "asap", "important", "critical", "priority"
  * Custom: Any specific tags mentioned by user
- BATCH TASK CREATION: Handle multiple tasks in one request:
  * Extract all task names mentioned in the request
  * Use entities.task_names (array) for multiple tasks instead of single task_name
  * Each task can have individual metadata (due_date, priority, etc.)
  * Examples:
    - "add 2 tasks, 1 called linear algebra and the other called Cake" → task_names: ["linear algebra", "Cake"], quantity: 2
    - "create 3 tasks: homework, study, exercise" → task_names: ["homework", "study", "exercise"], quantity: 3
    - "add tasks for math and science" → task_names: ["math", "science"], quantity: 2
- AMBIGUOUS TASK CREATION: When no specific task name is provided:
  * Return task_name: null (not empty string or generic terms)
  * Set requires_disambiguation: true
  * Provide clear suggested_action asking for task name
  * Examples of ambiguous requests: "create a task", "add task", "make a task", "new task", "task creation"
- Be specific about confidence:
  * High confidence (0.8+): Clear, unambiguous values ("homework", "January 25 at 3pm", "high priority")
  * Medium confidence (0.5-0.8): Somewhat clear but may need clarification ("tomorrow morning", "soon", "important")
  * Low confidence (0-0.5): Vague or missing ("it", "later", not mentioned)
- TYPO HANDLING: Auto-correct obvious typos in task names:
  * "tasj" → "task"
  * "homwork" → "homework"
  * "studdy" → "study"
  * "examm" → "exam"
  * "projct" → "project"
- Examples:
  * "create homework due tomorrow morning" → task_name: "homework" (conf: 0.9), due_date: "2023-10-06T09:00:00" (conf: 0.8)
  * "add urgent 2-hour math study" → task_name: "math study" (conf: 0.9), priority: "urgent" (conf: 0.9), estimated_duration: 120 (conf: 0.9)
  * "add 2 tasks, 1 called linear algebra and the other called Cake" → task_names: ["linear algebra", "Cake"], quantity: 2, requires_disambiguation: false
  * "create a tasj" → task_name: null (conf: 0.7, reason: "corrected typo 'tasj'"), requires_disambiguation: true, suggested_action: "What task would you like me to create?"
  * "create a task" → task_name: null, requires_disambiguation: true, suggested_action: "What task would you like me to create?"
  * "add task" → task_name: null, requires_disambiguation: true, suggested_action: "What task would you like me to create?"
  * "make a task" → task_name: null, requires_disambiguation: true, suggested_action: "What task would you like me to create?"

IMPORTANT: Extract quantity information when users specify how many items they want:
- "show me 5 tasks" → quantity: 5
- "get my 10 most recent emails" → quantity: 10  
- "list 3 tasks" → quantity: 3
- "show me all tasks" → quantity: null (no limit)
- "get my tasks" → quantity: null (no limit)

You must always respond with valid JSON matching the required schema. Extract entities (including target_task/new_title when relevant) and quantity carefully and provide brief reasoning for your classification (keep under 10 words).

Be precise with confidence scores:
- 0.9-1.0: Very confident, clear intent
- 0.7-0.9: Confident, some ambiguity
- 0.5-0.7: Moderately confident, multiple possible intents
- 0.3-0.5: Low confidence, requires clarification
- 0.0-0.3: Very unclear, needs disambiguation

IMPORTANT: Keep reasoning very brief - explain the key decision factor in maximum 10 words."""

    def _build_task_extraction_prompt(self, user_context: UserContext) -> str:
        """Build system prompt for task extraction"""
        return f"""You are Pulse, extracting task information from user input.

User Context:
- Name: {user_context.name or 'User'}
- Timezone: {user_context.timezone}
- Working Hours: {json.dumps(user_context.working_hours)}

Extract task details from the user's input. Be specific and accurate:
- task_title: Clear, concise title
- due_date: Only if explicitly mentioned, in ISO format
- priority: Infer from language (urgent words = high, casual = medium)
- estimated_duration: Only if mentioned or can be reasonably inferred
- category: academic, work, personal, health, etc.

Always respond with valid JSON matching the schema."""

    def _build_conversation_prompt(self, user_context: UserContext) -> str:
        """Build system prompt for conversation"""
        user_name = user_context.name or "there"
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

        return f"""You are Pulse, a helpful AI assistant for {user_context.name or 'the user'}.

Current context:
- User: {user_context.name or 'User'}
- Time: {current_time}
- Timezone: {user_context.timezone}

Your capabilities:
- You can help the user with their tasks, calendar, and other tasks.
- You can optimize and time block the user's schedule.
- You can also help the user with their general questions and small talk.
- You can make web searches for the user.
- You can also help the user with their draft emails.
- You can modify events in the user's connected calendar.

App (Refer to as 'our app'):
- Name: PulsePlan
- Creators: Fly on the Wall 
- Website: https://pulseplan.app
- Contact: hello@pulseplan.app
- Pricing: Free + Premium $9.99/month

Be conversational, helpful, and personalized. Use the user's name when appropriate.
Provide actionable follow-up suggestions when relevant.
Keep responses concise but warm and engaging.

Always respond with valid JSON matching the required schema."""

    def _build_clarification_completion_prompt(
        self, 
        original_request: Dict[str, Any], 
        clarification_context: Dict[str, Any], 
        user_context: UserContext
    ) -> str:
        """Build system prompt for completing a task from clarification response"""
        
        original_action = clarification_context.get("action", "create_task")
        clarification_question = clarification_context.get("question", "")
        
        return f"""You are Pulse, completing a task creation from a user's clarification response.

User Context:
- Name: {user_context.name or 'User'}
- Timezone: {user_context.timezone}
- Working Hours: {json.dumps(user_context.working_hours)}

Original Request Context:
- Action: {original_action}
- Clarification Question: "{clarification_question}"

Your task is to extract complete task information from the user's clarification response.

IMPORTANT: The user is responding to a clarification question, so their response should be interpreted as task details.

Extract all relevant task metadata:
- task_title: The main task name/title (required)
- task_description: Additional details if provided
- due_date: Due date in ISO format if mentioned (be smart about relative dates like "tomorrow", "Friday")
- priority: Priority level if mentioned (low, medium, high, urgent)
- estimated_duration: Duration in minutes if mentioned
- tags: Relevant tags if mentioned
- category: Task category (academic, work, personal, health, etc.)

Examples:
- Response: "homework" → task_title: "homework", priority: "medium", category: "academic"
- Response: "Sunday morning cleaning" → task_title: "Sunday morning cleaning", due_date: "next Sunday 09:00", category: "personal"
- Response: "math homework due Friday high priority" → task_title: "math homework", due_date: "Friday 23:59", priority: "high", category: "academic"

Always respond with valid JSON matching the TaskExtractionResponse schema."""

    def _build_user_prompt_with_history(
        self,
        user_query: str,
        conversation_history: ConversationHistory
    ) -> str:
        """Build user prompt including conversation history"""
        prompt_parts = []

        if conversation_history.summary:
            prompt_parts.append(f"Conversation Summary: {conversation_history.summary}")

        if conversation_history.turns:
            prompt_parts.append("Recent conversation:")
            for turn in conversation_history.turns[-5:]:  # Last 5 turns
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
                prompt_parts.append(f"{role.title()}: {content}")

        prompt_parts.append(f"Current message: {user_query}")

        return "\n".join(prompt_parts)

    def _generate_json_schema(self, response_schema: Type[BaseModel]) -> Dict[str, Any]:
        """Generate JSON schema for LLM structured output"""
        schema = response_schema.schema()

        # Simplify schema for LLM consumption
        return {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }

    def _validate_and_parse_response(
        self,
        llm_response: str,
        response_schema: Type[BaseModel],
        original_query: str
    ) -> BaseModel:
        """Validate and parse LLM response"""
        try:
            # Parse JSON
            response_data = json.loads(llm_response)

            # Always override timestamp with current time to prevent LLM from using old dates
            response_data["timestamp"] = datetime.utcnow().isoformat()

            # Add success if not present
            if "success" not in response_data:
                response_data["success"] = True

            # Validate with Pydantic
            validated_response = response_schema(**response_data)

            return validated_response

        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned text instead of JSON, attempting to extract response: {e}")
            # If JSON parsing fails, try to extract a meaningful response from text
            return self._parse_text_response(llm_response, response_schema, original_query)
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise ValueError(f"Response validation failed: {e}")

    def _generate_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate cache key for LLM response"""
        # Create deterministic hash from parameters
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"llm_cache:{operation}:{param_hash}"

    def _hash_context(
        self,
        user_context: UserContext,
        conversation_history: ConversationHistory
    ) -> str:
        """Generate hash of context for caching"""
        context_data = {
            "user_preferences": user_context.preferences,
            "working_hours": user_context.working_hours,
            "recent_turns": conversation_history.turns[-3:] if conversation_history.turns else []
        }
        context_str = json.dumps(context_data, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:8]

    async def _get_cached_response(
        self,
        cache_key: str,
        response_schema: Type[BaseModel]
    ) -> Optional[BaseModel]:
        """Get cached response from Redis or database"""
        try:
            if self.cache_config.use_redis:
                redis_client = await get_redis_client()
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    response_data = json.loads(cached_data)
                    return response_schema(**response_data)

            if self.cache_config.use_database:
                supabase = get_supabase()
                result = supabase.table("llm_cache").select("response").eq("cache_key", cache_key).gte("expires_at", datetime.utcnow().isoformat()).single().execute()
                if result.data and isinstance(result.data, dict):
                    return response_schema(**result.data["response"])

        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")

        return None

    async def _cache_response(self, cache_key: str, response: BaseModel) -> None:
        """Cache response in Redis and database"""
        try:
            response_data = response.dict()
            response_json = json.dumps(response_data)

            if self.cache_config.use_redis:
                redis_client = await get_redis_client()
                await redis_client.setex(cache_key, self.cache_config.ttl_seconds, response_json)

            if self.cache_config.use_database:
                supabase = get_supabase()
                cache_record = {
                    "cache_key": cache_key,
                    "prompt_hash": hashlib.md5(cache_key.encode()).hexdigest(),
                    "response": response_data,
                    "model_name": "gpt-4",
                    "expires_at": (datetime.utcnow() + timedelta(seconds=self.cache_config.ttl_seconds)).isoformat()
                }
                supabase.table("llm_cache").upsert(cache_record).execute()

        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _generate_operation_id(self) -> str:
        """Generate unique operation ID for tracing LLM calls"""
        import uuid
        return str(uuid.uuid4())[:8]

    def _create_fallback_intent_response(self, query: str, error: str) -> IntentClassificationResponse:
        """Create fallback response for intent classification errors"""
        return IntentClassificationResponse(
            success=False,
            timestamp=datetime.utcnow().isoformat(),
            intent="chat",
            confidence=0.1,
            entities={},
            suggested_action="generate_response",
            requires_disambiguation=True,
            alternative_intents=["task_management", "calendar"],
            reasoning=f"Classification error: {error[:50]}"
        )

    def _create_fallback_task_response(self, query: str, error: str) -> TaskExtractionResponse:
        """Create fallback response for task extraction errors"""
        return TaskExtractionResponse(
            success=False,
            timestamp=datetime.utcnow().isoformat(),
            task_title=query[:50] + "..." if len(query) > 50 else query,
            priority="medium",
            category="general"
        )

    def _parse_text_response(
        self,
        text_response: str,
        response_schema: Type[BaseModel],
        original_query: str
    ) -> BaseModel:
        """Parse text response when JSON parsing fails"""
        try:
            # For conversation responses, extract the message from text
            if response_schema == ConversationResponse:
                return ConversationResponse(
                    success=True,
                    timestamp=datetime.utcnow().isoformat(),
                    message=text_response.strip(),
                    tone="friendly",
                    requires_action=False,
                    follow_up_suggestions=[]
                )
            
            # For intent classification, try to extract intent from text
            elif response_schema == IntentClassificationResponse:
                # Simple keyword-based intent detection as fallback
                text_lower = original_query.lower()
                print(f"[DEBUG] Fallback processing query: '{original_query}' -> '{text_lower}'")
                
                if any(word in text_lower for word in ["task", "todo", "create", "add", "schedule"]):
                    intent = "task_management"
                    print(f"[DEBUG] Detected task_management intent")
                elif any(word in text_lower for word in ["calendar", "meeting", "event", "schedule"]):
                    intent = "calendar"
                    print(f"[DEBUG] Detected calendar intent")
                elif any(word in text_lower for word in ["email", "send", "message"]):
                    intent = "email"
                    print(f"[DEBUG] Detected email intent")
                elif any(word in text_lower for word in ["search", "find", "look up", "web search"]):
                    intent = "search"
                    print(f"[DEBUG] Detected search intent")
                else:
                    intent = "chat"
                    print(f"[DEBUG] Detected chat intent")
                
                # Extract entities for search intent
                entities = {}
                if intent == "search":
                    # Extract search query by removing common search phrases
                    search_query = original_query.lower()
                    search_phrases = ["search the web for", "search for", "look up", "find", "web search for"]
                    for phrase in search_phrases:
                        if search_query.startswith(phrase):
                            search_query = search_query[len(phrase):].strip()
                            break
                    entities["search_query"] = search_query
                
                # Determine appropriate action based on intent
                if intent == "search":
                    action = "web_search"
                elif intent == "task_management":
                    # Check if it's a task creation request
                    if any(word in text_lower for word in ["create", "add", "new", "make"]):
                        action = "create_task"
                        # Extract task name if present
                        if "create" in text_lower or "add" in text_lower:
                            # Try to extract task name after "create" or "add"
                            words = text_lower.split()
                            if "create" in words:
                                create_idx = words.index("create")
                                if create_idx + 1 < len(words) and words[create_idx + 1] in ["a", "an", "the"]:
                                    create_idx += 1
                                if create_idx + 1 < len(words) and words[create_idx + 1] == "task":
                                    # Look for task name after "create [a] task"
                                    task_start = create_idx + 2
                                    if task_start < len(words):
                                        task_name = " ".join(words[task_start:])
                                        entities["task_name"] = task_name
                            elif "add" in words:
                                add_idx = words.index("add")
                                if add_idx + 1 < len(words) and words[add_idx + 1] in ["a", "an", "the"]:
                                    add_idx += 1
                                if add_idx + 1 < len(words) and words[add_idx + 1] == "task":
                                    # Look for task name after "add [a] task"
                                    task_start = add_idx + 2
                                    if task_start < len(words):
                                        task_name = " ".join(words[task_start:])
                                        entities["task_name"] = task_name
                    else:
                        action = "list_tasks"
                elif intent == "calendar":
                    action = "schedule_event"
                elif intent == "email":
                    action = "read_emails"
                else:
                    action = "generate_response"
                
                return IntentClassificationResponse(
                    success=True,
                    timestamp=datetime.utcnow().isoformat(),
                    intent=intent,
                    action=action,
                    confidence=0.7,
                    entities=entities,
                    suggested_action=action,
                    requires_disambiguation=False,
                    alternative_intents=[],
                    reasoning="Text response fallback"
                )
            
            # For task extraction, create basic task info
            elif response_schema == TaskExtractionResponse:
                return TaskExtractionResponse(
                    success=True,
                    timestamp=datetime.utcnow().isoformat(),
                    task_title=original_query[:50] + "..." if len(original_query) > 50 else original_query,
                    priority="medium",
                    category="general",
                    due_date=None,
                    estimated_duration=None,
                    description=text_response
                )
            
            # Default fallback
            else:
                raise ValueError(f"Unknown response schema: {response_schema}")
                
        except Exception as e:
            logger.error(f"Failed to parse text response: {e}")
            raise ValueError(f"Failed to parse text response: {e}")

    def _create_fallback_conversation_response(self, query: str, error: str) -> ConversationResponse:
        """Create fallback response for conversation errors"""
        return ConversationResponse(
            success=False,
            timestamp=datetime.utcnow().isoformat(),
            message="I'm sorry, I encountered an issue processing your request. Could you please try rephrasing it?",
            tone="apologetic",
            requires_action=True
        )


# Global service instance
_llm_service = None

def get_llm_service() -> UnifiedLLMService:
    """Get global LLMService instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = UnifiedLLMService()
    return _llm_service