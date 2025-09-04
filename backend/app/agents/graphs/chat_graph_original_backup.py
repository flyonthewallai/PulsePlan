"""
Natural Language Processing Workflow
Implements the intent classification and routing workflow from LANGGRAPH_AGENT_WORKFLOWS.md
"""
from typing import Dict, List, Any
from datetime import datetime
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError


class ChatGraph(BaseWorkflow):
    """
    Natural Language Processing Workflow that:
    1. Classifies user intent from natural language query
    2. Routes to appropriate specialized workflow
    3. Handles unknown intents with clarification
    """
    
    def __init__(self):
        super().__init__(WorkflowType.NATURAL_LANGUAGE)
        
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for natural language workflow"""
        return {
            "input_validator": self.input_validator_node,
            "intent_classifier": self.intent_classifier_node,
            "policy_gate": self.policy_gate_node,
            "rate_limiter": self.rate_limiter_node,
            "calendar_router": self.calendar_router_node,
            "task_router": self.task_router_node,
            "todo_router": self.todo_router_node,
            "briefing_router": self.briefing_router_node,
            "scheduling_router": self.scheduling_router_node,
            "email_router": self.email_router_node,
            "search_router": self.search_router_node,
            "chat_router": self.chat_router_node,
            "clarification_generator": self.clarification_generator_node,
            "result_processor": self.result_processor_node,
            "trace_updater": self.trace_updater_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # Standard workflow path
            ("input_validator", "intent_classifier"),
            ("intent_classifier", self.intent_router, {
                "calendar": "policy_gate",
                "task": "policy_gate",
                "todo": "policy_gate",
                "briefing": "policy_gate",
                "scheduling": "policy_gate",
                "email": "policy_gate",
                "search": "policy_gate",
                "chat": "policy_gate",
                "unknown": "clarification_generator",
                "ambiguous": "clarification_generator"
            }),
            
            # Policy and rate limiting for known intents
            ("policy_gate", "rate_limiter"),
            ("rate_limiter", self.workflow_router, {
                "calendar": "calendar_router",
                "task": "task_router",
                "todo": "todo_router",
                "briefing": "briefing_router",
                "scheduling": "scheduling_router",
                "email": "email_router",
                "search": "search_router",
                "chat": "chat_router"
            }),
            
            # Route to specialized workflows
            ("calendar_router", "result_processor"),
            ("task_router", "result_processor"),
            ("todo_router", "result_processor"),
            ("briefing_router", "result_processor"),
            ("scheduling_router", "result_processor"),
            ("email_router", "result_processor"),
            ("search_router", "result_processor"),
            ("chat_router", "result_processor"),
            
            # Handle unknown intents
            ("clarification_generator", "result_processor"),
            
            # Final processing
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    def intent_classifier_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze user query to determine workflow type with confidence thresholding"""
        import logging
        import time
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        state["current_node"] = "intent_classifier"
        state["visited_nodes"].append("intent_classifier")
        
        user_query = state["input_data"].get("query", "").strip()
        user_id = state.get("user_id", "unknown")
        trace_id = state.get("trace_id", "unknown")
        
        logger.info(
            f"🎯 Intent classification started for query: '{user_query}'",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "query": user_query,
                "query_length": len(user_query),
                "event": "intent_classification_start"
            }
        )
        print(f"🎯 [CLASSIFICATION START] User: {user_id} | Query: '{user_query}' | Length: {len(user_query)}")
        
        if not user_query:
            logger.error(
                "Empty user query provided",
                extra={"user_id": user_id, "trace_id": trace_id, "event": "empty_query_error"}
            )
            raise WorkflowError("Empty user query", {"state": state})
        
        # Always use LLM classification for natural, varied responses
        llm_start = time.time()
        logger.info(
            f"🤖 Starting LLM classification for: '{user_query}'",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "query": user_query,
                "event": "llm_classification_start"
            }
        )
        print(f"🤖 [LLM START] Calling LLM for classification of: '{user_query}'")
        
        classification = self._classify_intent(user_query)
        classification_time = time.time() - start_time
        llm_time = time.time() - llm_start
        
        logger.info(
            f"🤖 LLM classification completed: {classification['intent']} (confidence: {classification['confidence']})",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "intent": classification["intent"],
                "confidence": classification["confidence"],
                "reasoning": classification["reasoning"],
                "classification_time": classification_time,
                "llm_time": llm_time,
                "event": "llm_classification_complete"
            }
        )
        print(f"🤖 [LLM RESULT] Intent: {classification['intent']} | Confidence: {classification['confidence']:.2f} | Reasoning: {classification['reasoning']} | LLM Time: {llm_time:.3f}s")
        
        intent = classification["intent"]
        confidence = classification["confidence"]
        
        # Confidence thresholding for ambiguous cases
        original_intent = intent
        if confidence < 0.4 or classification.get("ambiguous", False):
            # Low confidence - route to clarification
            intent = "ambiguous"
            state["input_data"]["needs_clarification"] = True
            state["input_data"]["clarification_context"] = {
                "possible_intents": [original_intent] + classification.get("alternative_intents", []),
                "reasoning": classification["reasoning"],
                "original_intent": classification["intent"]
            }
            print(f"❓ [LOW CONFIDENCE] Original intent: {original_intent} -> Routing to clarification (confidence: {confidence:.2f})")
        elif 0.4 <= confidence < 0.7:
            # Medium confidence - flag as uncertain but proceed
            state["input_data"]["uncertain_classification"] = True
            print(f"⚠️  [MEDIUM CONFIDENCE] Intent: {intent} (confidence: {confidence:.2f}) - proceeding with uncertainty flag")
        
        # Store comprehensive classification results
        state["input_data"]["classified_intent"] = intent
        state["input_data"]["confidence"] = confidence
        state["input_data"]["classification_details"] = classification
        
        # Generate immediate conversational response and task preview
        immediate_start = time.time()
        logger.info(
            f"💬 Generating immediate response for intent: {intent}",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "intent": intent,
                "confidence": confidence,
                "event": "immediate_response_start"
            }
        )
        print(f"💬 [RESPONSE START] Generating immediate response for intent: {intent}")
        
        immediate_response = self._generate_immediate_response(user_query, intent, classification)
        immediate_time = time.time() - immediate_start
        
        # Store immediate response in state so routers can access actual_title
        state["input_data"]["immediate_response"] = immediate_response
        
        response_preview = immediate_response.get("response", "")[:100] + ("..." if len(immediate_response.get("response", "")) > 100 else "")
        
        logger.info(
            f"💬 Immediate response generated: '{response_preview}'",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "response_type": immediate_response.get("conversation_type"),
                "has_task_preview": bool(immediate_response.get("task_preview")),
                "immediate_response_time": immediate_time,
                "event": "immediate_response_complete"
            }
        )
        print(f"💬 [RESPONSE READY] Type: {immediate_response.get('conversation_type')} | Has task preview: {bool(immediate_response.get('task_preview'))} | Time: {immediate_time:.3f}s")
        print(f"💬 [RESPONSE TEXT] '{response_preview}'")
        
        state["input_data"]["immediate_response"] = immediate_response
        
        # Enhanced metrics with full observability
        from datetime import datetime
        state["metrics"]["intent_classification"] = {
            "intent": intent,
            "confidence": confidence,
            "query_length": len(user_query),
            "reasoning": classification["reasoning"],
            "ambiguous": classification.get("ambiguous", False),
            "alternative_intents": classification.get("alternative_intents", []),
            "needs_clarification": state["input_data"].get("needs_clarification", False),
            "classification_timestamp": datetime.utcnow().isoformat()
        }
        
        # Log detailed classification for audit and training with performance metrics
        total_time = time.time() - start_time
        logger.info(
            f"✅ Intent classification completed: {intent} (confidence: {confidence:.2f})",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "query": user_query,
                "classification": classification,
                "final_intent": intent,
                "confidence": confidence,
                "total_time": total_time,
                "classification_time": classification_time,
                "immediate_response_time": immediate_time,
                "llm_used": True,
                "needs_clarification": state["input_data"].get("needs_clarification", False),
                "has_task_preview": bool(immediate_response.get("task_preview")),
                "response_type": immediate_response.get("conversation_type"),
                "event": "intent_classification_complete"
            }
        )
        
        # Comprehensive routing decision summary
        routing_decision = {
            "query": user_query,
            "final_intent": intent,
            "original_intent": original_intent if 'original_intent' in locals() else intent,
            "confidence": confidence,
            "llm_used": True,
            "needs_clarification": state["input_data"].get("needs_clarification", False),
            "has_task_preview": bool(immediate_response.get("task_preview")),
            "response_type": immediate_response.get("conversation_type"),
            "total_time": total_time
        }
        
        print("="*80)
        print(f"🎯 [CLASSIFICATION SUMMARY]")
        print(f"   Query: '{user_query}'")
        print(f"   Final Intent: {intent} (confidence: {confidence:.2f})")
        if 'original_intent' in locals() and original_intent != intent:
            print(f"   Original Intent: {original_intent} (modified due to low confidence)")
        print(f"   Reasoning: {classification['reasoning']}")
        print(f"   LLM Used: True")
        print(f"   Needs Clarification: {state['input_data'].get('needs_clarification', False)}")
        print(f"   Response Type: {immediate_response.get('conversation_type')}")
        print(f"   Has Task Preview: {bool(immediate_response.get('task_preview'))}")
        print(f"   Total Time: {total_time:.3f}s")
        print(f"   Next Route: {intent}_router" if intent not in ['ambiguous', 'unknown'] else f"   Next Route: clarification_generator")
        print("="*80)
        
        return state
    
    def _generate_task_response(self, query: str, intent: str) -> dict:
        """Generate both task name and acknowledgment response in a single LLM call"""
        from langchain_openai import ChatOpenAI
        import json
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        intent_context = {
            "calendar": "scheduling/calendar task",
            "task": "complex task creation", 
            "todo": "simple todo creation",
            "briefing": "briefing generation",
            "scheduling": "schedule creation",
            "email": "email task",
            "search": "web search"
        }
        
        task_context = intent_context.get(intent, "task")
        
        prompt = f"""
        Generate both a concise task name and a natural acknowledgment response for this user request.
        
        User request: "{query}"
        Task type: {task_context}
        
        CRITICAL: You MUST return a JSON object with exactly these fields:
        - "task_name": concise 4-word max summary for UI display (e.g., "Add Todo Item")
        - "actual_title": REQUIRED - the actual item title to save in database
        - "acknowledgment": natural, enthusiastic response (1 sentence, under 15 words)
        
        IMPORTANT: The "actual_title" field is MANDATORY and must contain the meaningful action/item (what the user actually wants to do):
        - "add milk to my todos" → actual_title: "Buy milk"
        - "add buy groceries to my todo list" → actual_title: "Buy groceries"  
        - "create a task to write report" → actual_title: "Write report"
        - "remind me to call mom" → actual_title: "Call mom"
        - "add walk the dog to my todos" → actual_title: "Walk the dog"
        - "create todo for dentist appointment" → actual_title: "Dentist appointment"

        Examples:
        {{
            "task_name": "Add Todo Item",
            "actual_title": "Buy milk",
            "acknowledgment": "Perfect, I'll add milk to your todos!"
        }}
        {{
            "task_name": "Create Task", 
            "actual_title": "Write project report",
            "acknowledgment": "Got it! I'll create that task for you."
        }}
        {{
            "task_name": "Add Reminder",
            "actual_title": "Call mom",
            "acknowledgment": "I'll set up that reminder to call mom!"
        }}
        {{
            "task_name": "Web Search",
            "actual_title": "study methods",
            "acknowledgment": "Perfect, let me search for study methods!"
        }}
        
        Make the acknowledgment sound enthusiastic and helpful. Don't repeat the exact query - rephrase it naturally.
        Return only valid JSON.
        """
        
        try:
            response = llm.invoke(prompt)
            response_content = response.content.strip()
            
            print(f"🤖 [LLM RESPONSE] Raw response for query '{query}': {response_content}")
            
            result = json.loads(response_content)
            
            # Validate and set defaults
            if not isinstance(result, dict):
                raise ValueError("Response is not a valid JSON object")
            
            actual_title = result.get("actual_title", "").strip()
            if not actual_title:
                print(f"⚠️  [LLM RESPONSE] Empty actual_title, using fallback for query: '{query}'")
                actual_title = query
            
            # Ensure task name is 4 words or less
            task_name = result.get("task_name", "").strip()
            if not task_name:
                task_name = "Process Request"
            words = task_name.split()
            if len(words) > 4:
                task_name = ' '.join(words[:4])
            
            task_response = {
                "task_name": task_name,
                "actual_title": actual_title,
                "acknowledgment": result.get("acknowledgment", "I'll help you with that!").strip()
            }
            
            print(f"✅ [LLM RESPONSE] Parsed response - task_name: '{task_response['task_name']}', actual_title: '{task_response['actual_title']}', acknowledgment: '{task_response['acknowledgment']}'")
            
            return task_response
            
        except Exception as e:
            print(f"❌ [TASK RESPONSE] Failed to parse LLM response: {e}")
            print(f"❌ [TASK RESPONSE] Raw response was: {response_content if 'response_content' in locals() else 'No response'}")
            # Fallback responses if LLM fails
            fallback_names = {
                "calendar": "Schedule Event",
                "task": "Create Task", 
                "briefing": "Generate Briefing",
                "scheduling": "Create Schedule",
                "email": "Send Email",
                "search": "Web Search"
            }
            fallback_responses = {
                "calendar": "Got it! I'll help with that scheduling request.",
                "task": "Perfect! I'll create that task for you.",
                "briefing": "I'll prepare that briefing for you!",
                "scheduling": "Let me create that schedule for you.",
                "email": "I'll help you with that email task.",
                "search": "Perfect, let me search for that information!"
            }
            
            return {
                "task_name": fallback_names.get(intent, "Task"),
                "actual_title": query,  # Fallback to original query
                "acknowledgment": fallback_responses.get(intent, "I'll help you with that!")
            }

    def _generate_immediate_response(self, query: str, intent: str, classification: dict) -> dict:
        """Generate immediate conversational response with task preview for non-chat intents"""
        query_lower = query.lower().strip()
        
        if intent == "chat":
            # All chat queries use LLM for natural, varied responses (no robotic fast paths)
            return {
                "response": "Let me respond to that...",
                "conversation_type": "processing",
                "immediate": True,
                "needs_llm": True,
                "natural_response": True  # Generate natural, varied response
            }
        
        elif intent == "calendar":
            # Immediate response + task preview for calendar operations
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated",
                "immediate": True,
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "calendar",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "cal_1", "name": "calendar_analyzer", "description": "Parse scheduling request", "status": "pending"},
                        {"id": "cal_2", "name": "availability_checker", "description": "Check calendar availability", "status": "pending"},
                        {"id": "cal_3", "name": "event_creator", "description": "Create calendar event", "status": "pending"}
                    ]
                }
            }
        
        elif intent == "task":
            # Immediate response + task preview for complex task operations
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated", 
                "immediate": True,
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "database_task",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "task_1", "name": "task_parser", "description": "Parse task details", "status": "pending"},
                        {"id": "task_2", "name": "dependency_analyzer", "description": "Check task dependencies", "status": "pending"},
                        {"id": "task_3", "name": "scheduling_optimizer", "description": "Optimize task scheduling", "status": "pending"},
                        {"id": "task_4", "name": "task_creator", "description": "Create task in system", "status": "pending"}
                    ]
                }
            }
            
        elif intent == "todo":
            # Immediate response + task preview for simple todo operations
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated", 
                "immediate": True,
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "database_todo",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "todo_1", "name": "todo_parser", "description": "Parse todo details", "status": "pending"},
                        {"id": "todo_2", "name": "priority_analyzer", "description": "Determine todo priority", "status": "pending"},
                        {"id": "todo_3", "name": "todo_creator", "description": "Create todo in system", "status": "pending"}
                    ]
                }
            }
        
        elif intent == "briefing":
            # Immediate response + task preview for briefing
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated",
                "immediate": True, 
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "briefing",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "brief_1", "name": "data_aggregator", "description": "Collect calendar and task data", "status": "pending"},
                        {"id": "brief_2", "name": "content_synthesizer", "description": "Generate briefing content", "status": "pending"},
                        {"id": "brief_3", "name": "formatter", "description": "Format final briefing", "status": "pending"}
                    ]
                }
            }
        
        elif intent == "scheduling":
            # Immediate response + task preview for scheduling
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated",
                "immediate": True, 
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "scheduling",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "sched_1", "name": "task_analyzer", "description": "Analyze tasks and priorities", "status": "pending"},
                        {"id": "sched_2", "name": "time_optimizer", "description": "Find optimal time slots", "status": "pending"},
                        {"id": "sched_3", "name": "schedule_builder", "description": "Build final schedule", "status": "pending"}
                    ]
                }
            }
            
        elif intent == "email":
            # Immediate response + task preview for email
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated",
                "immediate": True, 
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "email",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "email_1", "name": "email_parser", "description": "Parse email request", "status": "pending"},
                        {"id": "email_2", "name": "content_generator", "description": "Generate email content", "status": "pending"},
                        {"id": "email_3", "name": "email_sender", "description": "Send or prepare email", "status": "pending"}
                    ]
                }
            }
            
        elif intent == "search":
            # Immediate response + task preview for web search
            task_response = self._generate_task_response(query, intent)
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated",
                "immediate": True, 
                "actual_title": task_response["actual_title"],  # Include extracted title
                "task_preview": {
                    "task_name": task_response["task_name"],
                    "task_type": "search",
                    "status": "starting",
                    "estimated_tools": [
                        {"id": "search_1", "name": "query_analyzer", "description": "Analyze and optimize search query", "status": "pending"},
                        {"id": "search_2", "name": "web_search", "description": "Search the web for information", "status": "pending"},
                        {"id": "search_3", "name": "result_synthesizer", "description": "Synthesize and format results", "status": "pending"}
                    ]
                }
            }
        
        else:
            # For ambiguous/unknown, provide clarification immediately
            return {
                "response": f"I want to make sure I understand correctly. You said: '{query}' - could you clarify what you'd like me to help with?",
                "conversation_type": "clarification",
                "immediate": True,
                "needs_clarification": True,
                "suggestions": [
                    {"type": "calendar", "example": "Schedule a meeting with John tomorrow"},
                    {"type": "task", "example": "Create a project plan with dependencies"}, 
                    {"type": "todo", "example": "Add buy milk to my todo list"},
                    {"type": "briefing", "example": "Show me my daily agenda"},
                    {"type": "chat", "example": "What can you help me with?"}
                ]
            }
    
    def _classify_intent(self, query: str) -> dict:
        """LLM-based intent classification with confidence and reasoning"""
        from langchain_openai import ChatOpenAI
        import json
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        prompt = f"""
        Classify the following user request into one of these intents. Provide your response as JSON with intent, confidence (0.0-1.0), and reasoning.
        
        IMPORTANT CONTEXT: The system has access to comprehensive information about the user's profile, preferences, and context. If a user asks a question that could be answered from this available information, classify it as "chat" rather than "search".
        
        Intent categories:
        - calendar: scheduling meetings, events, appointments, checking availability
        - task: creating, managing, or updating complex tasks with dependencies, scheduling, or detailed project work
        - todo: creating, managing, or updating simple todos, quick reminders, basic to-do items, shopping lists
        - briefing: requesting summaries, reports, daily briefings, status updates
        - scheduling: creating schedules, time management, organizing weekly/daily plans, optimizing time
        - email: sending emails, composing messages, email management, reading emails, checking inbox, email operations (SECURE: all emails require user approval before sending)
        - search: web search requests for information NOT available in the system context, research queries that require external sources, "search for", "look up", "find information about"
        - chat: greetings (hi, hello, hey), questions about user's own information/profile/preferences, seeking help, general conversation, explanations, casual interactions, questions that can be answered from available context
        - unknown: anything that doesn't clearly fit the above categories
        
        Classification rules:
        - If the user asks about their own information, preferences, or context that the system knows about → classify as "chat"
        - If the user asks for external information not in the system → classify as "search"
        - If the user asks "what can you do?" or similar → classify as "chat"
        - If the user asks about PulsePlan, the app, or the developers → classify as "chat"
        - If the user asks about their schedule, tasks, or personal info → classify as "chat"
        
        Examples:
        - "hi", "hello", "hey" = chat (high confidence)
        - "what can you help me with?" = chat
        - "what are my preferences?" = chat (system has this info)
        - "tell me about myself" = chat (system has user profile)
        - "who made this app?" = chat (system has this info)
        - "what are your capabilities?" = chat (system has this info)
        - "schedule a meeting tomorrow" = calendar
        - "add task to finish project" = task
        - "make my schedule for this week" = scheduling
        - "email John about the meeting" = email
        - "send an email to mom" = email
        - "check my inbox" = email
        - "read my emails" = email
        - "compose an email to my teacher" = email
        - "show me today's summary" = briefing
        - "search for study tips" = search (external info)
        - "look up the weather in Seattle" = search (external info)
        - "find information about machine learning" = search (external info)
        
        User request: "{query}"
        
        Response format:
        {{
            "intent": "category_name",
            "confidence": 0.85,
            "reasoning": "Very brief explanation of why this intent was chosen",
            "ambiguous": false,
            "alternative_intents": ["other_possible_intent"]
        }}
        """
        
        try:
            print(f"🤖 [LLM PROMPT] Sending to LLM:")
            print(f"    Model: gpt-4o-mini")
            print(f"    Temperature: 0")
            print(f"    Query: '{query}'")
            print(f"    Prompt length: {len(prompt)} characters")
            
            resp = llm.invoke(prompt)
            
            # Try to parse JSON response - ensure we handle the response properly
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            print(f"🤖 [LLM RAW RESPONSE] {response_content}")
            
            try:
                result = json.loads(response_content.strip())
                print(f"🤖 [LLM PARSED] Successfully parsed JSON response")
            except json.JSONDecodeError:
                print(f"❌ [LLM PARSE ERROR] Failed to parse JSON response")
                # Fallback: extract just the intent if JSON parsing fails
                content = response_content.strip().lower()
                valid_intents = ["calendar", "task", "todo", "briefing", "scheduling", "email", "search", "chat", "unknown"]
                
                for intent in valid_intents:
                    if intent in content:
                        print(f"🔧 [LLM FALLBACK] Found intent '{intent}' in response text")
                        return {
                            "intent": intent,
                            "confidence": 0.5,
                            "reasoning": "Fallback parsing - JSON response failed",
                            "ambiguous": True,
                            "alternative_intents": [],
                            "raw_response": response_content
                        }
                
                return {
                    "intent": "unknown",
                    "confidence": 0.1,
                    "reasoning": "Could not parse LLM response",
                    "ambiguous": True,
                    "alternative_intents": [],
                    "raw_response": response_content
                }
            
            # Validate and normalize the parsed result
            intent = result.get("intent", "unknown").lower()
            valid_intents = ["calendar", "task", "todo", "briefing", "scheduling", "email", "search", "chat", "unknown"]
            
            if intent not in valid_intents:
                intent = "unknown"
                result["confidence"] = 0.1
                result["reasoning"] = f"Invalid intent '{result.get('intent')}' returned by LLM"
                result["ambiguous"] = True
            
            # Ensure all required fields exist
            classification = {
                "intent": intent,
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "No reasoning provided"),
                "ambiguous": result.get("ambiguous", False),
                "alternative_intents": result.get("alternative_intents", []),
                "raw_response": response_content
            }
            
            # Auto-detect ambiguity based on confidence
            if classification["confidence"] < 0.5:
                classification["ambiguous"] = True
            
            return classification
                
        except Exception as e:
            # Fallback to unknown if LLM fails
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "reasoning": f"LLM classification failed: {str(e)}",
                "ambiguous": True,
                "alternative_intents": [],
                "error": str(e)
            }
    
    def intent_router(self, state: WorkflowState) -> str:
        """Route based on classified intent with ambiguity handling"""
        intent = state["input_data"].get("classified_intent")
        query = state["input_data"].get("query", "")
        
        if intent in ["calendar", "task", "briefing", "scheduling", "email", "search", "chat"]:
            print(f"🚀 [ROUTING] Query: '{query}' -> Intent: {intent} -> Route: {intent}_router")
            return intent
        elif intent == "ambiguous":
            print(f"❓ [ROUTING] Query: '{query}' -> Intent: {intent} -> Route: clarification_generator")
            return "ambiguous"
        else:
            print(f"❓ [ROUTING] Query: '{query}' -> Intent: {intent} -> Route: clarification_generator (unknown)")
            return "unknown"
    
    def workflow_router(self, state: WorkflowState) -> str:
        """Route to appropriate workflow after policy/rate checks"""
        return state["input_data"]["classified_intent"]
    
    async def calendar_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to calendar workflow"""
        state["current_node"] = "calendar_router"
        state["visited_nodes"].append("calendar_router")
        
        query = state["input_data"]["query"]
        workflow_id = state.get("trace_id")
        print(f"📅 [CALENDAR ROUTER] Executing calendar workflow for: '{query}'")
        
        # Emit WebSocket node update
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_node_update(workflow_id, "calendar_router", "executing")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit calendar_router executing: {e}")
        
        # TODO: Execute calendar workflow
        # For now, mock response
        state["output_data"] = {
            "workflow_type": "calendar",
            "message": "Calendar workflow executed",
            "query": query,
            "intent": state["input_data"]["classified_intent"]
        }
        
        # Emit completion event
        try:
            await websocket_manager.emit_node_update(workflow_id, "calendar_router", "completed")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit calendar_router completed: {e}")
        
        print(f"📅 [CALENDAR ROUTER] Calendar workflow completed")
        return state
    
    async def task_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to complex task workflow"""
        state["current_node"] = "task_router"
        state["visited_nodes"].append("task_router")
        
        try:
            # Execute database workflow for tasks
            from ..orchestrator import get_agent_orchestrator
            
            orchestrator = get_agent_orchestrator()
            user_id = state["user_id"]
            query = state["input_data"]["query"]
            
            # Get the actual title from the immediate response (LLM already extracted it)
            immediate_response = state["input_data"].get("immediate_response", {})
            task_title = immediate_response.get("actual_title", query)
            
            print(f"📋 [TASK ROUTER] Query: '{query}' -> Extracted title: '{task_title}'")
            
            # Execute database operation to create task
            result = await orchestrator.execute_database_operation(
                user_id=user_id,
                entity_type="task",
                operation="create",
                data={"title": task_title},
                user_context=state.get("user_context", {})
            )
            
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "task",
                "message": "Complex task created successfully", 
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "result": result.get("result", {})
            }
            
            # Emit task_created WebSocket event
            try:
                from app.core.websocket import websocket_manager
                workflow_id = state.get("trace_id")
                await websocket_manager.emit_task_created(workflow_id, {
                    "type": "task",
                    "title": task_title,
                    "created_item": result.get("result", {}),
                    "success": True,
                    "message": "Complex task created successfully"
                })
            except Exception as e:
                print(f"⚠️ [WEBSOCKET] Failed to emit task_created: {e}")
            
        except Exception as e:
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "task",
                "message": f"Task creation failed: {str(e)}", 
                "query": state["input_data"]["query"],
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def todo_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to simple todo workflow"""
        state["current_node"] = "todo_router"
        state["visited_nodes"].append("todo_router")
        
        try:
            # Execute database workflow for todos
            from ..orchestrator import get_agent_orchestrator
            
            orchestrator = get_agent_orchestrator()
            user_id = state["user_id"]
            query = state["input_data"]["query"]
            
            # Get the actual title from the immediate response (LLM already extracted it)
            immediate_response = state["input_data"].get("immediate_response", {})
            todo_title = immediate_response.get("actual_title", query)
            
            print(f"📝 [TODO ROUTER] Query: '{query}' -> Extracted title: '{todo_title}'")
            
            # Execute database operation to create todo
            result = await orchestrator.execute_database_operation(
                user_id=user_id,
                entity_type="todo",
                operation="create",
                data={"title": todo_title},
                user_context=state.get("user_context", {})
            )
            
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "todo",
                "message": "Simple todo created successfully", 
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "result": result.get("result", {})
            }
            
            # Emit task_created WebSocket event
            try:
                from app.core.websocket import websocket_manager
                workflow_id = state.get("trace_id")
                await websocket_manager.emit_task_created(workflow_id, {
                    "type": "todo",
                    "title": todo_title,
                    "created_item": result.get("result", {}),
                    "success": True,
                    "message": "Simple todo created successfully"
                })
            except Exception as e:
                print(f"⚠️ [WEBSOCKET] Failed to emit task_created: {e}")
            
        except Exception as e:
            state["output_data"] = {
                "workflow_type": "database",
                "entity_type": "todo",
                "message": f"Todo creation failed: {str(e)}", 
                "query": state["input_data"]["query"],
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def briefing_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to briefing workflow"""
        state["current_node"] = "briefing_router"
        state["visited_nodes"].append("briefing_router")
        
        query = state["input_data"]["query"]
        workflow_id = state.get("trace_id")
        print(f"📊 [BRIEFING ROUTER] Executing briefing workflow for: '{query}'")
        
        # Emit WebSocket node update
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_node_update(workflow_id, "briefing_router", "executing")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit briefing_router executing: {e}")
        
        # TODO: Execute briefing workflow
        # For now, mock response
        state["output_data"] = {
            "workflow_type": "briefing",
            "message": "Briefing workflow executed",
            "query": query,
            "intent": state["input_data"]["classified_intent"]
        }
        
        # Emit completion event
        try:
            await websocket_manager.emit_node_update(workflow_id, "briefing_router", "completed")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit briefing_router completed: {e}")
        
        print(f"📊 [BRIEFING ROUTER] Briefing workflow completed")
        return state
    
    async def scheduling_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to scheduling workflow"""
        state["current_node"] = "scheduling_router"
        state["visited_nodes"].append("scheduling_router")
        
        query = state["input_data"]["query"]
        workflow_id = state.get("trace_id")
        print(f"⏰ [SCHEDULING ROUTER] Executing scheduling workflow for: '{query}'")
        
        # Emit WebSocket node update
        try:
            from app.core.websocket import websocket_manager
            await websocket_manager.emit_node_update(workflow_id, "scheduling_router", "executing")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit scheduling_router executing: {e}")
        
        # TODO: Execute scheduling workflow
        # For now, mock response
        state["output_data"] = {
            "workflow_type": "scheduling",
            "message": "Scheduling workflow executed",
            "query": query,
            "intent": state["input_data"]["classified_intent"]
        }
        
        # Emit completion event
        try:
            await websocket_manager.emit_node_update(workflow_id, "scheduling_router", "completed")
        except Exception as e:
            print(f"⚠️ [WEBSOCKET] Failed to emit scheduling_router completed: {e}")
        
        print(f"⏰ [SCHEDULING ROUTER] Scheduling workflow completed")
        return state
    
    async def email_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to dedicated EmailGraph workflow"""
        state["current_node"] = "email_router"
        state["visited_nodes"].append("email_router")
        
        query = state["input_data"]["query"]
        user_id = state.get("user_id", "unknown")
        print(f"📧 [EMAIL ROUTER] Routing to EmailGraph for: '{query}'")
        
        try:
            # Import and execute EmailGraph
            from .email_graph import EmailGraph
            from .base import create_initial_state, WorkflowType
            
            # Create email workflow state
            email_state = create_initial_state(
                user_id=user_id,
                workflow_type=WorkflowType.EMAIL,
                input_data={"query": query},
                user_context=state.get("user_context", {}),
                connected_accounts=state.get("connected_accounts", {}),
                trace_id=state.get("trace_id")  # Preserve original trace_id for WebSocket consistency
            )
            
            # Execute EmailGraph workflow
            email_graph = EmailGraph()
            email_result_state = await email_graph.execute(email_state)
            
            # Extract results from EmailGraph
            if email_result_state.get("output_data"):
                state["output_data"] = email_result_state["output_data"]
                state["output_data"]["intent"] = state["input_data"]["classified_intent"]
                print(f"📧 [EMAIL ROUTER] EmailGraph completed successfully")
            else:
                # Handle case where EmailGraph didn't produce output
                state["output_data"] = {
                    "workflow_type": "email",
                    "message": f"I encountered an issue while processing the email request '{query}'. Please try again.",
                    "query": query,
                    "intent": state["input_data"]["classified_intent"],
                    "error": "EmailGraph did not produce output"
                }
                print(f"❌ [EMAIL ROUTER] EmailGraph did not produce output")
            
        except Exception as e:
            print(f"❌ [EMAIL ROUTER] Exception during EmailGraph execution: {str(e)}")
            state["output_data"] = {
                "workflow_type": "email", 
                "message": f"I encountered an unexpected error while processing the email request '{query}'. Please try again.",
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def search_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to dedicated SearchGraph workflow"""
        state["current_node"] = "search_router"
        state["visited_nodes"].append("search_router")
        
        query = state["input_data"]["query"]
        user_id = state.get("user_id", "unknown")
        print(f"🔍 [SEARCH ROUTER] Routing to SearchGraph for: '{query}'")
        
        try:
            # Import and execute SearchGraph
            from .search_graph import SearchGraph
            from .base import create_initial_state, WorkflowType
            
            # Create search workflow state
            search_state = create_initial_state(
                user_id=user_id,
                workflow_type=WorkflowType.SEARCH,
                input_data={"query": query},
                user_context=state.get("user_context", {}),
                connected_accounts=state.get("connected_accounts", {}),
                trace_id=state.get("trace_id")  # Preserve original trace_id for WebSocket consistency
            )
            
            # Execute SearchGraph workflow
            search_graph = SearchGraph()
            search_result_state = await search_graph.execute(search_state)
            
            # Extract results from SearchGraph
            if search_result_state.get("output_data"):
                state["output_data"] = search_result_state["output_data"]
                state["output_data"]["intent"] = state["input_data"]["classified_intent"]
                print(f"🔍 [SEARCH ROUTER] SearchGraph completed successfully")
            else:
                # Handle case where SearchGraph didn't produce output
                state["output_data"] = {
                    "workflow_type": "search",
                    "message": f"I encountered an issue while processing the search for '{query}'. Please try again.",
                    "search_results": [],
                    "query": query,
                    "intent": state["input_data"]["classified_intent"],
                    "error": "SearchGraph did not produce output"
                }
                print(f"❌ [SEARCH ROUTER] SearchGraph did not produce output")
            
        except Exception as e:
            print(f"❌ [SEARCH ROUTER] Exception during SearchGraph execution: {str(e)}")
            state["output_data"] = {
                "workflow_type": "search", 
                "message": f"I encountered an unexpected error while searching for '{query}'. Please try again.",
                "search_results": [],
                "query": query,
                "intent": state["input_data"]["classified_intent"],
                "error": str(e)
            }
        
        return state
    
    async def chat_router_node(self, state: WorkflowState) -> WorkflowState:
        """Route to LLM-powered chat workflow"""
        state["current_node"] = "chat_router"
        state["visited_nodes"].append("chat_router")
        
        user_query = state["input_data"]["query"]
        
        # Generate response - use lightweight LLM for natural chat
        classification = state["input_data"].get("classification_details", {})
        immediate_response = state["input_data"].get("immediate_response", {})
        
        if immediate_response.get("fast_chat"):
            # Use lightweight LLM prompt for natural but fast responses
            chat_response = self._generate_fast_llm_chat_response(user_query, classification)
        else:
            # Generate full LLM response for complex chat/help queries
            chat_response = self._generate_llm_chat_response(user_query, state.get("user_context", {}))
        
        state["output_data"] = {
            "workflow_type": "chat",
            "message": chat_response["response"],  # Main response message
            "response": chat_response["response"],  # Keep for compatibility
            "conversation_type": chat_response["conversation_type"],
            "helpful_actions": chat_response.get("helpful_actions", []),
            "follow_up_questions": chat_response.get("follow_up_questions", []),
            "query": user_query,
            "intent": state["input_data"]["classified_intent"],
            "tool_calls": [],  # No tool calls for simple chat
            "execution_details": {
                "nodes_visited": state.get("visited_nodes", []),
                "classification": {
                    "intent": state["input_data"]["classified_intent"],
                    "confidence": state["input_data"].get("confidence", 0.0),
                    "reasoning": state["input_data"].get("classification_details", {}).get("reasoning", "")
                },
                "llm_reasoning": chat_response.get("reasoning", "")
            }
        }
        
        return state
    
    def _generate_fast_llm_chat_response(self, query: str, classification: dict) -> dict:
        """Generate natural chat response using a lightweight LLM prompt for speed"""
        from langchain_openai import ChatOpenAI
        import json
        
        # Use faster model and lower temperature for speed while maintaining variety
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=100)
        
        # Determine the greeting type for context
        query_lower = query.lower().strip()
        greeting_type = "general"
        
        if query_lower in ["hi", "hello", "hey"]:
            greeting_type = "simple_greeting"
        elif query_lower in ["how are you", "how's it going", "hows it going"]:
            greeting_type = "personal_greeting"
        elif query_lower in ["good morning", "good afternoon", "good evening"]:
            greeting_type = "time_greeting"
        elif "help" in query_lower or "what can you" in query_lower:
            greeting_type = "help_request"
        
        # Lightweight prompt for natural variety
        prompt = f"""You are Pulse. The user knows you well. Respond naturally to: "{query}"

Guidelines based on type:
- Simple greetings: Be warm and friendly (don't introduce yourself)
- Personal questions: Respond conversationally like you know them
- Time-based greetings: Match their energy and time of day
- Help requests: Be helpful and ready to assist
- Keep it concise (1-2 sentences max)
- Be natural and slightly varied each time
- Never introduce yourself - they know who you are
- Respond like you remember them

Type: {greeting_type}
Respond naturally:"""

        try:
            resp = llm.invoke(prompt)
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            
            # For fast responses, we don't need complex JSON parsing
            response_text = response_content.strip().strip('"')
            
            # Add appropriate helpful actions based on greeting type
            helpful_actions = []
            follow_up = []
            
            if greeting_type == "help_request":
                helpful_actions = [
                    {"action": "calendar", "description": "Schedule meetings", "example_query": "Schedule a meeting tomorrow"},
                    {"action": "task", "description": "Create tasks", "example_query": "Remind me to call mom"},
                    {"action": "briefing", "description": "Get briefings", "example_query": "Show my daily agenda"}
                ]
                follow_up = ["What would you like help with?"]
            elif greeting_type == "personal_greeting":
                follow_up = ["How can I help you today?"]
            else:
                follow_up = ["What can I help you with?"]
            
            return {
                "response": response_text,
                "conversation_type": "greeting",
                "reasoning": f"Fast LLM response for {greeting_type}",
                "helpful_actions": helpful_actions,
                "follow_up_questions": follow_up,
                "fast_llm": True
            }
            
        except Exception as e:
            # Fallback to simple varied responses if LLM fails
            fallback_responses = {
                "simple_greeting": [
                    "Hey there! Ready to tackle the day together?",
                    "Hello! What can we get done today?",
                    "Hi! How can I help you stay on top of things today?"
                ],
                "personal_greeting": [
                    "I'm doing great, thanks for asking! Ready to help you crush your goals today.",
                    "Fantastic! I'm energized and ready to make your day productive.",
                    "I'm doing well! How's your day shaping up so far?"
                ],
                "help_request": [
                    "I'm here and ready! What would you like to work on?",
                    "Happy to help! What's on your agenda today?",
                    "Absolutely! What can we tackle together?"
                ],
                "time_greeting": [
                    "Hope your day is going well! What can I help with?",
                    "Great to hear from you! How can I assist today?",
                    "Nice to connect! What's on your mind?"
                ]
            }
            
            import random
            responses = fallback_responses.get(greeting_type, ["I'm here to help! What can I do for you?"])
            
            return {
                "response": random.choice(responses),
                "conversation_type": "greeting",
                "reasoning": f"Fallback response for {greeting_type}",
                "helpful_actions": [],
                "follow_up_questions": ["How can I assist you?"],
                "fallback": True,
                "error": str(e)
            }
    
    def _generate_fast_chat_response(self, query: str, classification: dict) -> dict:
        """Generate fast pre-built responses for simple queries"""
        query_lower = query.lower().strip()
        
        # Greeting responses
        if classification["reasoning"] == "Simple greeting detected":
            # Different responses based on the specific greeting
            if query_lower in ["how are you", "how's it going", "hows it going"]:
                responses = [
                    "I'm doing great, thanks for asking! I'm ready to help you tackle your day. How are you doing?",
                    "I'm fantastic and energized to help you stay productive! How's your day going so far?",
                    "I'm doing well! Always excited to help with scheduling, tasks, or whatever you need. How about you?",
                    "Great, thank you! I'm here and ready to make your day more organized. What's on your mind?"
                ]
            elif query_lower in ["good morning", "good afternoon", "good evening"]:
                time_responses = {
                    "good morning": [
                        "Good morning! Hope you're having a great start to your day. What can I help you accomplish today?",
                        "Morning! Ready to make today productive? I'm here to help with your schedule, tasks, or anything else.",
                        "Good morning! I'm excited to help you organize your day. What's first on your agenda?"
                    ],
                    "good afternoon": [
                        "Good afternoon! How's your day going? I'm here if you need help with scheduling or tasks.",
                        "Afternoon! Hope you're having a productive day. What can I assist you with?",
                        "Good afternoon! Ready to tackle the rest of your day? I'm here to help."
                    ],
                    "good evening": [
                        "Good evening! Winding down or still have things to organize? I'm here to help.",
                        "Evening! How was your day? I can help you plan for tomorrow if you'd like.",
                        "Good evening! Whether you're planning ahead or wrapping up today, I'm here to assist."
                    ]
                }
                responses = time_responses.get(query_lower, time_responses["good morning"])
            else:
                # General hi/hello responses
                responses = [
                    "Hi there! I'm Pulse, your personal assistant. What can I help you with today?",
                    "Hello! Great to see you. I'm here to help with your scheduling, tasks, or daily planning. What's on your mind?",
                    "Hey! I'm Pulse and I'm ready to help make your day more productive. What would you like to work on?"
                ]
            
            import random
            response = random.choice(responses)
            
            # Lighter helpful actions for casual greetings like "how are you"
            if query_lower in ["how are you", "how's it going", "hows it going"]:
                helpful_actions = []  # Don't overwhelm conversational greetings with actions
                follow_up = ["How can I help you today?"]
            else:
                helpful_actions = [
                    {"action": "calendar", "description": "Schedule something", "example_query": "Schedule a meeting with John tomorrow"},
                    {"action": "task", "description": "Create a task", "example_query": "Remind me to call mom tonight"},
                    {"action": "briefing", "description": "Get daily briefing", "example_query": "What's on my agenda?"}
                ]
                follow_up = ["What would you like to work on today?"]
            
            return {
                "response": response,
                "conversation_type": "greeting",
                "reasoning": "Fast greeting response",
                "helpful_actions": helpful_actions,
                "follow_up_questions": follow_up,
                "fast_path": True
            }
        
        # Thanks responses
        elif classification["reasoning"] == "Gratitude expression detected":
            responses = [
                "You're welcome! I'm always here to help you stay organized and productive.",
                "Happy to help! Let me know if there's anything else you need.",
                "Glad I could assist! Feel free to ask me anything about your schedule, tasks, or daily planning."
            ]
            import random
            response = random.choice(responses)
            
            return {
                "response": response,
                "conversation_type": "acknowledgment",
                "reasoning": "Fast thanks response",
                "helpful_actions": [],
                "follow_up_questions": [],
                "fast_path": True
            }
        
        # Help responses
        elif "help request" in classification["reasoning"].lower():
            response = "I'm Pulse, your AI assistant for productivity! Here's what I can help you with:\n\n• **Calendar**: Schedule meetings, check availability, manage events\n• **Tasks**: Create reminders, set deadlines, track progress\n• **Briefings**: Daily summaries and status updates\n• **Smart Scheduling**: Optimize your time and priorities\n\nJust tell me what you'd like to do in natural language!"
            
            return {
                "response": response,
                "conversation_type": "help",
                "reasoning": "Fast help response",
                "helpful_actions": [
                    {"action": "calendar", "description": "Try scheduling something", "example_query": "Schedule a team meeting for next Monday"},
                    {"action": "task", "description": "Create a task", "example_query": "Add finish project report to my tasks"},
                    {"action": "briefing", "description": "Get a briefing", "example_query": "What's on my agenda today?"}
                ],
                "follow_up_questions": ["What specific area would you like help with?"],
                "fast_path": True
            }
        
        # Fallback to LLM if we can't handle it fast
        return self._generate_llm_chat_response(query, {})
    
    def _generate_llm_chat_response(self, query: str, user_context: dict) -> dict:
        """Generate intelligent chat response using LLM"""
        from langchain_openai import ChatOpenAI
        import json
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)  # Slightly creative for conversation
        
        prompt = f"""
        The user is asking: "{query}"

        You are Pulse. The user knows you well and you remember them.
        
        If this is a greeting, respond naturally and warmly like you know them.
        For questions, provide helpful responses about your capabilities.

        If this is a question about your capabilities (e.g. what can you do?), respond with a detailed list of your capabilities.
        
        Your capabilities:
        - Calendar: Schedule meetings, check availability, manage events
        - Tasks: Create reminders, set deadlines, manage priorities  
        - Briefing: Daily summaries, status reports, progress updates
        - Email: Read emails, compose and send emails (with user approval), manage inbox
        - Intelligent scheduling: Optimize time blocks and priorities

        PulsePlan Info:
        - PulsePlan allows users to create optimized schedules for their tasks and activities. 
        - PulsePlan was developed by Fly on the Wall LLC, founded by Conner Groth, Isaias Perez, and Jake Pechart. Learn more about us at https://flyonthewalldev.com
        
        Guidelines:
        - For greetings: Be warm and familiar (don't introduce yourself)
        - For questions: Be informative and helpful
        - For capabilities: List out all capabilities and be clear about what you can do.
        - Keep responses concise but engaging
        - Respond like you remember them and your past interactions
        - Never introduce yourself - they know who you are
        
        Respond in JSON format:
        {{
            "response": "Natural, conversational response",
            "conversation_type": "greeting|help|explanation|general_chat|feature_question", 
            "reasoning": "Very brief (1 sentence max) explanation of why you responded this way",
            "helpful_actions": [
                {{
                    "action": "calendar|task|briefing|chat",
                    "description": "What they could do next",
                    "example_query": "Example of how to phrase this request"
                }}
            ],
            "follow_up_questions": ["Short, helpful questions"]
        }}
        
        Be natural and familiar.
        """
        
        try:
            resp = llm.invoke(prompt)
            
            # Parse LLM response - ensure we handle the response properly
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            try:
                llm_response = json.loads(response_content.strip())
                llm_response["raw_response"] = response_content
                return llm_response
            except json.JSONDecodeError:
                # Fallback response
                return {
                    "response": f"I'd be happy to help! Regarding '{query}', I can assist you with scheduling, task management, daily briefings, and general productivity questions. What specifically would you like to know more about?",
                    "conversation_type": "general_chat",
                    "reasoning": "JSON parsing failed, using fallback response",
                    "helpful_actions": [
                        {"action": "chat", "description": "Ask me specific questions about PulsePlan features", "example_query": "How do I schedule a meeting?"}
                    ],
                    "follow_up_questions": ["What specific feature would you like to know more about?"],
                    "raw_response": response_content,
                    "fallback_reason": "JSON parsing failed"
                }
                
        except Exception as e:
            # Error fallback
            return {
                "response": f"I'm here to help with '{query}'. I can assist with scheduling, task management, briefings, and productivity questions. What would you like to know?",
                "conversation_type": "general_chat", 
                "reasoning": f"LLM chat generation failed: {str(e)}",
                "helpful_actions": [
                    {"action": "chat", "description": "Ask me about PulsePlan features", "example_query": "What can you help me with?"}
                ],
                "follow_up_questions": ["What specific aspect would you like help with?"],
                "error": str(e)
            }
    
    async def clarification_generator_node(self, state: WorkflowState) -> WorkflowState:
        """Generate LLM-powered clarification for ambiguous or unknown intents"""
        state["current_node"] = "clarification_generator"
        state["visited_nodes"].append("clarification_generator")
        
        user_query = state["input_data"]["query"]
        intent = state["input_data"]["classified_intent"]
        
        if intent == "ambiguous" and state["input_data"].get("needs_clarification"):
            # Handle ambiguous cases with LLM-generated clarification
            clarification_context = state["input_data"]["clarification_context"]
            clarification_response = self._generate_llm_clarification(
                user_query, 
                "ambiguous", 
                clarification_context
            )
        else:
            # Handle completely unknown intents with LLM
            clarification_response = self._generate_llm_clarification(
                user_query, 
                "unknown"
            )
        
        state["output_data"] = clarification_response
        
        # Log clarification request for improvement
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "LLM clarification generated",
            extra={
                "user_id": state["user_id"],
                "query": user_query,
                "clarification_type": clarification_response["clarification_type"],
                "confidence": state["input_data"].get("confidence", 0.0),
                "llm_reasoning": clarification_response.get("llm_reasoning", "No reasoning available")
            }
        )
        
        return state
    
    def _generate_llm_clarification(self, query: str, clarification_type: str, context: dict = None) -> dict:
        """Generate intelligent clarification using LLM"""
        from langchain_openai import ChatOpenAI
        import json
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # Slightly higher temp for creativity
        
        if clarification_type == "ambiguous":
            possible_intents = context.get("possible_intents", [])
            reasoning = context.get("reasoning", "")
            
            prompt = f"""
            The user said: "{query}"
            
            I detected this could be related to multiple intents: {possible_intents}
            My reasoning: {reasoning}
            
            Generate a helpful clarifying question and specific actionable options to help the user clarify what they want to do.
            
            Available workflows:
            - calendar: Schedule meetings, events, check availability
            - task: Create tasks, set reminders, manage deadlines  
            - briefing: Get summaries, daily reports, status updates
            - chat: Ask questions, get help, general conversation
            
            Respond in JSON format:
            {{
                "message": "Friendly clarifying question that acknowledges the ambiguity",
                "explanation": "Brief explanation of why this is ambiguous",
                "options": [
                    {{
                        "action": "calendar",
                        "description": "Specific description of what this would do for their request",
                        "example": "Example of how this would work"
                    }},
                    {{
                        "action": "task", 
                        "description": "Specific description of what this would do for their request",
                        "example": "Example of how this would work"
                    }}
                ],
                "clarifying_questions": ["Specific question to help disambiguate"]
            }}
            """
        else:  # unknown
            prompt = f"""
            The user said: "{query}"
            
            I couldn't determine what they want to do. Generate a helpful response that:
            1. Acknowledges their request
            2. Explains what I can help with
            3. Provides specific options based on what they said
            
            Available workflows:
            - calendar: Schedule meetings, events, check availability
            - task: Create tasks, set reminders, manage deadlines
            - briefing: Get summaries, daily reports, status updates  
            - chat: Ask questions, get help, general conversation
            
            Respond in JSON format:
            {{
                "message": "Helpful message acknowledging their request",
                "explanation": "What I can help with generally",
                "options": [
                    {{
                        "action": "calendar",
                        "description": "How this might relate to their request",
                        "example": "Specific example"
                    }},
                    {{
                        "action": "task",
                        "description": "How this might relate to their request", 
                        "example": "Specific example"
                    }},
                    {{
                        "action": "briefing",
                        "description": "How this might relate to their request",
                        "example": "Specific example"
                    }},
                    {{
                        "action": "chat",
                        "description": "How this might relate to their request",
                        "example": "Specific example"
                    }}
                ],
                "suggestions": ["Specific ways they could rephrase their request"]
            }}
            """
        
        try:
            resp = llm.invoke(prompt)
            
            # Parse LLM response - ensure we handle the response properly
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            try:
                llm_response = json.loads(response_content.strip())
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._fallback_clarification(query, clarification_type, context)
            
            # Structure the response
            clarification_response = {
                "workflow_type": "clarification",
                "clarification_type": clarification_type,
                "original_query": query,
                "message": llm_response.get("message", "I need clarification on what you'd like me to do."),
                "explanation": llm_response.get("explanation", ""),
                "options": llm_response.get("options", []),
                "llm_reasoning": llm_response.get("explanation", ""),
                "raw_llm_response": response_content
            }
            
            # Add type-specific fields
            if clarification_type == "ambiguous":
                clarification_response["possible_intents"] = context.get("possible_intents", []) if context else []
                clarification_response["clarifying_questions"] = llm_response.get("clarifying_questions", [])
            else:
                clarification_response["suggestions"] = llm_response.get("suggestions", [])
            
            return clarification_response
            
        except Exception as e:
            # Fallback to simple clarification if LLM fails
            return self._fallback_clarification(query, clarification_type, context, str(e))
    
    def _fallback_clarification(self, query: str, clarification_type: str, context: dict = None, error: str = None) -> dict:
        """Fallback clarification when LLM fails"""
        if clarification_type == "ambiguous":
            return {
                "workflow_type": "clarification",
                "clarification_type": "ambiguous",
                "original_query": query,
                "message": f"I see a few ways to help with '{query}'. What would you like me to do?",
                "explanation": "This request could be handled in multiple ways.",
                "options": [
                    {"action": "calendar", "description": "Schedule this as a meeting or event", "example": "Add to your calendar"},
                    {"action": "task", "description": "Create this as a task or reminder", "example": "Add to your task list"},
                ],
                "possible_intents": context.get("possible_intents", []) if context else [],
                "clarifying_questions": ["Would you like to schedule this or create a task?"],
                "fallback_reason": f"LLM clarification failed: {error}" if error else "Using fallback clarification"
            }
        else:
            return {
                "workflow_type": "clarification",
                "clarification_type": "unknown", 
                "original_query": query,
                "message": f"I'm not sure what you'd like me to help with regarding: '{query}'",
                "explanation": "I can help you with scheduling, tasks, briefings, or general questions.",
                "options": [
                    {"action": "calendar", "description": "Schedule meetings or events", "example": "Schedule a meeting"},
                    {"action": "task", "description": "Create and manage tasks", "example": "Create a reminder"},
                    {"action": "briefing", "description": "Get daily summaries", "example": "Show my daily briefing"},
                    {"action": "chat", "description": "Ask questions or get help", "example": "How does this work?"}
                ],
                "suggestions": ["Try being more specific about what you want to do"],
                "fallback_reason": f"LLM clarification failed: {error}" if error else "Using fallback clarification"
            }
    
    async def result_processor_node(self, state: WorkflowState) -> WorkflowState:
        """Format and validate outputs with WebSocket emission"""
        state["current_node"] = "result_processor"
        state["visited_nodes"].append("result_processor")
        
        # Ensure output_data exists
        if not state.get("output_data"):
            state["output_data"] = {}
            
        # Add metadata
        state["output_data"]["metadata"] = {
            "workflow_type": state["workflow_type"],
            "execution_time": (datetime.utcnow() - state["execution_start"]).total_seconds(),
            "nodes_visited": len(state["visited_nodes"])
        }
        
        # Emit WebSocket completion event only if this is not a sub-workflow delegation
        # Sub-workflows (email, search) emit their own completion events
        workflow_id = state.get("trace_id")
        visited_nodes = state["visited_nodes"]
        last_visited_node = visited_nodes[-2] if len(visited_nodes) > 1 else None
        
        # Debug logging
        print(f"📡 [CHAT DEBUG] All visited nodes: {visited_nodes}")
        print(f"📡 [CHAT DEBUG] Last visited node: {last_visited_node}")
        
        # Always emit completion - sub-workflows emit their own specific events, but ChatGraph still completes
        if workflow_id:
            try:
                from app.core.websocket import websocket_manager
                
                # Emit WebSocket events directly since we're in an async context
                await websocket_manager.emit_workflow_status(workflow_id, "completed", state.get("output_data"))
                await websocket_manager.emit_node_update(workflow_id, "result_processor", "completed")
                print(f"📡 [WEBSOCKET] Emitted workflow completion for {workflow_id}")
                
            except ImportError:
                print("⚠️ [WEBSOCKET] WebSocket manager not available")
            except Exception as e:
                print(f"❌ [WEBSOCKET] Failed to emit completion: {str(e)}")
        
        return state